import time
import queue
import sounddevice as sd
import numpy as np
import nls
import sys
import threading
import json
from ppt_controller import get_ppt_controller
import re

# 阿里云配置信息
URL = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
TOKEN = "d47f354604834d0e846aeff5d332a951"  # 实际Token，这是临时的免费的，可能需要每24小时换一个
APPKEY = "Th4Q3N8Q2BRXGhNg"  # 实际Appkey

# 记录音频数据的队列
audio_queue = queue.Queue()

# 控制语音识别的开启和关闭
RUNNING: bool = False
running_lock = threading.Lock()  # 用于保护RUNNING变量的锁
page_lock = threading.Lock()  # 翻页锁

output_lock = threading.Lock()


# 从麦克风输入音频的回调函数 向音频队列中添加数据
def audio_callback(indata, frames, time, status):
    # if status:
    #     print(status, file=sys.stderr)
    audio_queue.put(indata.copy())


class RealTimeSpeechRecognizer:
    def __init__(self, url=URL, token=TOKEN, appkey=APPKEY):
        self.url = url
        self.token = token
        self.appkey = appkey
        self.transcriber = None
        self.current_text = ""  # 存储当前识别的文本
        self.last_complete_sentence = ""  # 存储最后完成的句子
        self.__initialize_transcriber()

        # 换页关键词
        self.next_page_keywords = []
        self.prev_page_keyword = "上一页"

    def __initialize_transcriber(self):
        self.transcriber = nls.NlsSpeechTranscriber(
            url=self.url,
            token=self.token,
            appkey=self.appkey,
            on_sentence_begin=self.on_sentence_begin,
            on_sentence_end=self.on_sentence_end,
            on_start=self.on_start,
            on_result_changed=self.on_result_changed,
            on_completed=self.on_completed,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.transcriber.start(aformat="pcm",
                               enable_intermediate_result=True,
                               enable_punctuation_prediction=True,
                               enable_inverse_text_normalization=True)

    def send_audio(self, audio_data):
        if self.transcriber:
            self.transcriber.send_audio(audio_data)

    def stop_transcription(self):
        if self.transcriber:
            self.transcriber.stop()

    def get_current_text(self):
        """获取当前识别的文本"""
        return self.current_text

    def get_last_complete_sentence(self):
        """获取最后完成的句子"""
        return self.last_complete_sentence

    def on_sentence_begin(self, message, *args):
        # 解析JSON消息
        try:
            data = json.loads(message)
            result = data.get('payload', {}).get('result', '')
            self.current_text = result
            # with output_lock:
            #     print(f"\n[开始] {result}")
        except json.JSONDecodeError:
            # print(f"解析错误: {message}")
            pass

    def detect_page_jump_command(self, text):
        """
        使用正则表达式检测跳转页面指令
        支持中英文混合表达，如：
          "跳转到第5页"
          "go to page 10"
          "翻到第3页"
          "jump to page 15"
        """
        # 统一转换为小写（不区分大小写）
        normalized_text = text.lower()
        # 定义跳转页面的正则表达式模式
        # 中文模式：匹配 "跳转[到/至]第X页" 或 "翻到第X页"
        chinese_pattern = r'(?:跳转|翻|转到|切换)[到至]?第?(\d+)[页张]'
        # 英文模式：匹配 "go to page X" 或 "jump to page X"
        english_pattern = r'(?:go|jump|switch)\s*to\s*page\s*(\d+)'
        # 组合中英文模式
        combined_pattern = f"({chinese_pattern})|({english_pattern})"
        # 在文本中搜索匹配
        match = re.search(combined_pattern, normalized_text)
        if match:
            # 提取页码数字（优先取中文匹配，如果没有则取英文匹配）
            page_num = match.group(1) or match.group(3)
            if page_num:
                try:
                    page_num = int(page_num)
                    # 执行跳转操作
                    get_ppt_controller().jump_to_slide(page_num)
                except ValueError:
                    # print(f"提取的页码无效: {page_num}")
                    pass

    def on_sentence_end(self, message, *args):
        # 解析JSON消息
        try:
            data = json.loads(message)
            result = data.get('payload', {}).get('result', '')
            self.current_text = ""
            self.last_complete_sentence = result  # 一句完整的不中断的话
            # 当一段连续不中断的话结束 阿里云的sdk会自动调用该函数 在这里调用PPT换页的逻辑
            with page_lock:
                next_page_keyword = [kw for kw in self.next_page_keywords if kw in result]
                if next_page_keyword:
                    get_ppt_controller().next_slide()
                elif self.prev_page_keyword in result:
                    get_ppt_controller().previous_slide()
                # else:
                #     self.detect_page_jump_command(result)
            with output_lock:
                print(f"\n[完整句子] {result}")
        except json.JSONDecodeError:
            # print(f"解析错误: {message}")
            pass

    def on_start(self, message, *args):
        pass

    def on_result_changed(self, message, *args):
        # 解析JSON消息 - 这是实时更新的文本
        try:
            data = json.loads(message)
            result = data.get('payload', {}).get('result', '')
            self.current_text = result
        except json.JSONDecodeError:
            pass

    def on_completed(self, message, *args):
        pass

    def on_error(self, message, *args):
        pass

    def on_close(self, *args):
        pass


# 调用阿里云的语音转文字的接口
def recognize_speech(audio_data, recognizer):
    audio_data = np.concatenate(audio_data)
    recognizer.send_audio(audio_data.tobytes())


# 开启音频流并处理音频数据
def start_audio_stream(recognizer, mic_device_index=1):
    global RUNNING
    with running_lock:
        RUNNING = True  # 设置全局变量RUNNING为True，开启语音识别
        print("语音识别已开启")

    def audio_processing():
        nonlocal recognizer
        mic_audio_buffer = []

        while True:
            with running_lock:
                if not RUNNING:
                    print("语音识别已关闭")
                    break

            while not audio_queue.empty():
                mic_audio_buffer.append(audio_queue.get())

            if len(mic_audio_buffer) >= 10:
                threading.Thread(target=recognize_speech, args=(mic_audio_buffer.copy(), recognizer)).start()
                mic_audio_buffer = []  # 清空缓冲区

            time.sleep(0.1)

        recognizer.stop_transcription()

    # 创建麦克风输入流
    mic_stream = sd.InputStream(
        callback=audio_callback,
        channels=1,
        samplerate=16000,
        dtype='int16',
        device=mic_device_index
    )

    with mic_stream:
        audio_processing()


def toggle_audio_stream(enabled: bool):
    global RUNNING
    with running_lock:
        RUNNING = enabled


_RTVTT_recognizer = None


def get_RTVTT_recognizer() -> RealTimeSpeechRecognizer():
    global _RTVTT_recognizer
    if _RTVTT_recognizer is None:
        _RTVTT_recognizer = RealTimeSpeechRecognizer()
    return _RTVTT_recognizer


if __name__ == "__main__":
    # 默认麦克风
    mic_device_index = 1

    # 初始化语音识别器
    recognizer = RealTimeSpeechRecognizer(URL, TOKEN, APPKEY)
    # 开启音频流并处理音频数据
    start_audio_stream(recognizer, mic_device_index)
