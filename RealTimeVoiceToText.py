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
TOKEN = "51e5f05a6fe84b6f835bfc301aa78369"  # 实际Token，这是临时的免费的，可能需要每24小时换一个
APPKEY = "eb0qKUAXtcStGTtw"  # 实际Appkey

# 记录音频数据的队列
audio_queue = queue.Queue()

# 控制语音识别的开启和关闭
RUNNING: bool = False
running_lock = threading.Lock()  # 用于保护RUNNING变量的锁
page_lock = threading.Lock()  # 翻页锁

output_lock = threading.Lock()


# 从麦克风输入音频的回调函数 向音频队列中添加数据
def audio_callback(indata, frames, time, status):
    if status:
        ## print(
        x=1
    # 添加简单的音频活动检测
    volume = np.sqrt(np.mean(indata**2))
    if volume > 0.01:  # 如果有足够的音频信号
        ## print(
        x=1
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
        # print(
        # print(
        # print(
        # print( # 只显示前20个字符
        
        try:
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
            # print(
            
            self.transcriber.start(aformat="pcm",
                                   enable_intermediate_result=True,
                                   enable_punctuation_prediction=True,
                                   enable_inverse_text_normalization=True)
            # print(
        except Exception as e:
            # print(
            import traceback
            traceback.print_exc()

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
            
            print(f"\n🔧 DEBUG: on_sentence_end 收到完整句子: '{result}'")
            # print(
            # print(
            
            # 当一段连续不中断的话结束 阿里云的sdk会自动调用该函数 在这里调用PPT换页的逻辑
            with page_lock:                # 检查下一页关键词
                matched_next_keywords = [kw for kw in self.next_page_keywords if kw in result]
                # print(
                if matched_next_keywords:
                    # print(
                    
                    # 直接发送按键，同时激活PPT窗口
                    try:
                        import pyautogui as pt
                        import time
                        
                        # 激活PPT窗口的简单方法：先切换窗口，再发送按键
                        pt.FAILSAFE = False
                        pt.PAUSE = 0.1
                        
                        # 使用Alt+Tab切换到PPT窗口
                        pt.hotkey('alt', 'tab')
                        time.sleep(0.2)  # 等待窗口切换
                        
                        # 发送右箭头键（下一页）
                        pt.press('right')
                        # print(
                    except Exception as e:
                        # print(
                        # 备用方案：尝试使用PPT控制器
                        try:
                            get_ppt_controller().next_slide()
                        except Exception as e2:
                            print("执行下一页操作时出错:", e2)

                    print(f"📄 已执行下一页操作")
                                
                elif self.prev_page_keyword in result:
                    # print(
                    
                    # 直接发送按键，不依赖PPT控制器状态
                    try:
                        import pyautogui as pt
                        pt.FAILSAFE = False
                        pt.PAUSE = 0.1
                        pt.press('left')  # 发送左箭头键（上一页）
                        # print(
                    except Exception as e:
                        # print(
                        # 备用方案：尝试使用PPT控制器
                        try:
                            get_ppt_controller().previous_slide()
                        except Exception as e2:
                            print("执行上一页操作时出错:", e2)

                    print(f"📄 已执行上一页操作")
                else:
                    # print(
                    # print(
                    self.detect_page_jump_command(result)
                    
            with output_lock:
                print(f"\n[完整句子] {result}")
        except json.JSONDecodeError:
            # print(
            pass
        
    def on_start(self, message, *args):
        print("开始识别")

    def on_result_changed(self, message, *args):
        # 解析JSON消息 - 这是实时更新的文本
        # print(
        try:
            data = json.loads(message)
            result = data.get('payload', {}).get('result', '')
            self.current_text = result
            if result:
                print("实时识别结果:", result)
        except json.JSONDecodeError:
            print("解析实时识别结果时出错:", e)

    def on_completed(self, message, *args):
        print("识别完成")

    def on_error(self, message, *args):
        # print(
        print("识别出错:", message)

    def on_close(self, *args):
        print("识别关闭")


# 调用阿里云的语音转文字的接口
def recognize_speech(audio_data, recognizer):
    # # print(
    try:
        audio_data = np.concatenate(audio_data)
        audio_bytes = audio_data.tobytes()
        # # print(
        recognizer.send_audio(audio_bytes)
        # # print(
    except Exception as e:
        print("识别出错:", e)
        import traceback
        traceback.print_exc()


# 开启音频流并处理音频数据
def start_audio_stream(recognizer, mic_device_index=1):
    # # print(
    global RUNNING
    with running_lock:
        RUNNING = True  # 设置全局变量RUNNING为True，开启语音识别
        # print(

    def audio_processing():
        # print(
        nonlocal recognizer
        mic_audio_buffer = []
        buffer_count = 0

        while True:
            with running_lock:
                if not RUNNING:
                    # print(
                    break

            # 处理音频队列
            queue_size = audio_queue.qsize()
            # if queue_size > 0:
            #     # print(
                
            while not audio_queue.empty():
                try:
                    audio_data = audio_queue.get()
                    mic_audio_buffer.append(audio_data)
                    buffer_count += 1
                    # if buffer_count % 20 == 0:  # 每20个包打印一次
                    #     # print(
                except Exception as e:
                    print("处理音频队列时出错:", e)

            if len(mic_audio_buffer) >= 10:
                # # print(
                try:
                    threading.Thread(target=recognize_speech, args=(mic_audio_buffer.copy(), recognizer)).start()
                    mic_audio_buffer = []  # 清空缓冲区
                except Exception as e:
                    print("处理音频缓冲区时出错:", e)

            time.sleep(0.1)

        recognizer.stop_transcription()
        # print(

    # 创建麦克风输入流
    # print(
    try:
        # 测试设备是否可用
        test_stream = sd.InputStream(
            callback=None,
            channels=1,
            samplerate=16000,
            dtype='int16',
            device=mic_device_index
        )
        test_stream.close()
        # print(
        
        mic_stream = sd.InputStream(
            callback=audio_callback,
            channels=1,
            samplerate=16000,
            dtype='int16',
            device=mic_device_index
        )
        # print(
    except Exception as e:
        # print(
        # print(
        list_audio_devices()
        return

    # print(
    try:
        with mic_stream:
            # print(
            audio_processing()
    except Exception as e:
        # print(
        import traceback
        traceback.print_exc()


def toggle_audio_stream(enabled: bool):
    # print(
    print(f"切换语音识别状态: {'开启' if enabled else '关闭'}")
    global RUNNING
    with running_lock:
        old_running = RUNNING
        RUNNING = enabled
        # print(
    
    # if enabled:
    #     # print(
    #     # print(


_RTVTT_recognizer = None
_audio_stream_thread = None  # 新增：音频流线程


def get_RTVTT_recognizer():
    global _RTVTT_recognizer
    if _RTVTT_recognizer is None:
        _RTVTT_recognizer = RealTimeSpeechRecognizer()
    return _RTVTT_recognizer


def is_voice_recognition_running():
    """检查语音识别是否正在运行"""
    global RUNNING, _audio_stream_thread
    with running_lock:
        # 检查全局状态和线程状态
        thread_alive = _audio_stream_thread and _audio_stream_thread.is_alive()
        return RUNNING and thread_alive


def list_audio_devices():
    """列出可用的音频设备"""
    # print(
    try:
        devices = sd.query_devices()
        # for i, device in enumerate(devices):
        #     if device['max_input_channels'] > 0:  # 只显示输入设备
        #         print(f"  设备 {i}: {device['name']} (输入通道: {device['max_input_channels']})")
        # print(
    except Exception as e:
        print("列出音频设备时出错:", e)


def start_real_time_voice_recognition(mic_device_index=None):
    """启动完整的实时语音识别（包括音频流）"""
    # print(
    
    # 如果没有指定设备，使用默认设备
    if mic_device_index is None:
        try:
            mic_device_index = sd.default.device[0]
            # print(
        except:
            mic_device_index = 0
            # print(
    
    # 列出可用设备以供调试
    list_audio_devices()
    
    global _audio_stream_thread, RUNNING
    
    # 检查是否已经在运行
    if _audio_stream_thread and _audio_stream_thread.is_alive():
        # print(
        return True
    
    try:
        # 获取识别器并强制重新初始化transcriber
        recognizer = get_RTVTT_recognizer()
        
        # 重要：强制重新初始化transcriber，确保每次启动都是全新的
        # print(
        recognizer._RealTimeSpeechRecognizer__initialize_transcriber()
        # print(
        
        # 【新增】启动前清空识别内容，确保重新开始
        recognizer.last_complete_sentence = ""
        recognizer.current_text = ""
        # print(
        # print(
        
        # 启动音频流线程
        # print(
        _audio_stream_thread = threading.Thread(
            target=start_audio_stream,
            args=(recognizer, mic_device_index),
            daemon=True
        )
        _audio_stream_thread.start()
        
        # 等待一小段时间确保线程启动
        time.sleep(0.5)
        
        if _audio_stream_thread.is_alive():
            # print(
            # print(
            # print(
            return True
        else:
            # print(
            return False
            
    except Exception as e:
        # print(
        import traceback
        traceback.print_exc()
        return False


def stop_real_time_voice_recognition():
    """停止实时语音识别"""
    # print(
    global _audio_stream_thread, RUNNING, _RTVTT_recognizer
    
    # 先停止transcriber
    if _RTVTT_recognizer and _RTVTT_recognizer.transcriber:
        try:
            # print(
            _RTVTT_recognizer.transcriber.stop()
            # print(
        except Exception as e:
            print("停止transcriber时出错:", e)

    # 停止音频流
    with running_lock:
        RUNNING = False
        # print(
    
    # 等待线程结束
    if _audio_stream_thread and _audio_stream_thread.is_alive():
        print("⏳ 等待音频流线程结束...")
        _audio_stream_thread.join(timeout=3.0)
        # if _audio_stream_thread.is_alive():
        #     # print(
        # else:
        #     # print(
    
    _audio_stream_thread = None
    
    # 重要：清空和重置识别器，准备下次使用
    if _RTVTT_recognizer is not None:
        # print(
        _RTVTT_recognizer.last_complete_sentence = ""
        _RTVTT_recognizer.current_text = ""
        _RTVTT_recognizer.transcriber = None  # 清空transcriber，强制下次重新初始化
        # print(
    
    # print(

def set_voice_keywords(next_page_keywords: list, prev_page_keyword: str = "上一页"):
    """设置语音识别的关键词"""
    global _RTVTT_recognizer
    
    # print(
    # print(
    # print(
    
    # 获取或创建识别器
    recognizer = get_RTVTT_recognizer()
    
    # 设置关键词
    recognizer.next_page_keywords = next_page_keywords.copy() if next_page_keywords else []
    recognizer.prev_page_keyword = prev_page_keyword
    
    # print(
    print(f"   - 下一页关键词: {recognizer.next_page_keywords}")
    print(f"   - 上一页关键词: '{recognizer.prev_page_keyword}'")

def get_voice_keywords():
    """获取当前设置的语音关键词"""
    global _RTVTT_recognizer
    
    if _RTVTT_recognizer is None:
        return [], "上一页"
    
    return _RTVTT_recognizer.next_page_keywords.copy(), _RTVTT_recognizer.prev_page_keyword

if __name__ == "__main__":
    # 默认麦克风
    mic_device_index = 1

    # 初始化语音识别器
    recognizer = RealTimeSpeechRecognizer(URL, TOKEN, APPKEY)
    # 开启音频流并处理音频数据
    start_audio_stream(recognizer, mic_device_index)
