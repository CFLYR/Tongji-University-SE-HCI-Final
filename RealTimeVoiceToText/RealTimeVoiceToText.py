import time
import queue
import sounddevice as sd
import numpy as np
import nls
import sys
import threading
import json

# 阿里云配置信息
URL = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
TOKEN = "1fb2d383df2f48e5b7440dc55516139d"  # 实际Token，这是临时的免费的，可能需要每24小时换一个
APPKEY = "Th4Q3N8Q2BRXGhNg"  # 实际Appkey

# 记录音频数据的队列
audio_queue = queue.Queue()

# 创建锁对象确保输出不混乱
output_lock = threading.Lock()


# 打印可用音频设备
def list_audio_devices():
    """列出所有可用的音频设备并返回设备列表"""
    print("\n可用音频设备列表:")
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        print(f"{i}: {dev['name']} (输入通道: {dev['max_input_channels']}, 输出通道: {dev['max_output_channels']})")

    return devices


# 让用户选择设备
def select_device(device_type):
    """让用户选择设备并返回设备索引"""
    devices = list_audio_devices()

    while True:
        try:
            index = int(input(f"\n请输入{device_type}的设备索引: "))
            if 0 <= index < len(devices):
                # 验证设备是否有输入通道
                if devices[index]['max_input_channels'] > 0:
                    return index
                else:
                    print(f"设备 {index} 没有输入通道，请选择其他设备")
            else:
                print("索引超出范围，请重新输入")
        except ValueError:
            print("请输入有效的数字索引")


# 从麦克风输入音频的回调函数
def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(indata.copy())


class RealTimeSpeechRecognizer:
    def __init__(self, url, token, appkey):
        self.url = url
        self.token = token
        self.appkey = appkey
        self.transcriber = None
        self.current_text = ""  # 存储当前识别的文本
        self.last_complete_sentence = ""  # 存储最后完成的句子
        self.__initialize_transcriber()

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
            with output_lock:
                print(f"\n[开始] {result}")
        except json.JSONDecodeError:
            print(f"解析错误: {message}")

    def on_sentence_end(self, message, *args):
        # 解析JSON消息
        try:
            data = json.loads(message)
            result = data.get('payload', {}).get('result', '')
            self.current_text = ""
            self.last_complete_sentence = result
            with output_lock:
                print(f"\n[完整句子] {result}")
        except json.JSONDecodeError:
            print(f"解析错误: {message}")

    def on_start(self, message, *args):
        with output_lock:
            print(f"识别开始: {message}")

    def on_result_changed(self, message, *args):
        # 解析JSON消息 - 这是实时更新的文本
        try:
            data = json.loads(message)
            result = data.get('payload', {}).get('result', '')
            self.current_text = result
            # 使用回车符覆盖上一行实现实时更新效果
            with output_lock:
                print(f"\r实时识别: {result}", end="", flush=True)
        except json.JSONDecodeError:
            print(f"解析错误: {message}")

    def on_completed(self, message, *args):
        with output_lock:
            print(f"\n识别完成: {message}")

    def on_error(self, message, *args):
        with output_lock:
            print(f"\n错误: {message}")

    def on_close(self, *args):
        with output_lock:
            print(f"\n连接关闭: {args}")


# 调用阿里云的语音转文字的接口
def recognize_speech(audio_data, recognizer):
    audio_data = np.concatenate(audio_data)
    recognizer.send_audio(audio_data.tobytes())


# 实时显示识别结果的线程函数
def display_results(recognizer):
    """实时显示识别结果的线程"""
    try:
        while True:
            # 获取当前识别文本
            current_text = recognizer.get_current_text()

            # 使用锁确保输出不混乱
            with output_lock:
                # 清空当前行
                print("\r" + " " * 100, end="", flush=True)
                # 显示实时结果
                if current_text:
                    print(f"\r{current_text}", end="", flush=True)

            time.sleep(0.1)
    except KeyboardInterrupt:
        pass


# 开启音频流并处理音频数据
def start_audio_stream(mic_device_index, recognizer):
    # 创建麦克风输入流
    mic_stream = sd.InputStream(
        callback=audio_callback,
        channels=1,
        samplerate=16000,
        dtype='int16',
        device=mic_device_index
    )

    with mic_stream:
        print("\n录音中... 按 Ctrl+C 停止")
        print(f"麦克风设备: {sd.query_devices(mic_device_index)['name']}")

        # 启动结果显示线程
        display_thread = threading.Thread(target=display_results, args=(recognizer,))
        display_thread.daemon = True
        display_thread.start()

        mic_audio_buffer = []

        try:
            while True:
                # 收集麦克风音频数据
                while not audio_queue.empty():
                    mic_audio_buffer.append(audio_queue.get())

                # 当收集到足够数据时发送识别请求
                if len(mic_audio_buffer) >= 10:
                    threading.Thread(target=recognize_speech, args=(mic_audio_buffer.copy(), recognizer)).start()
                    mic_audio_buffer = []  # 清空缓冲区

                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n停止录音...")
            recognizer.stop_transcription()
            print("转录服务已停止")


if __name__ == "__main__":
    # 解除以下注释选择音频输入设备
    # print("=" * 50)
    # print("麦克风实时语音转文字程序")
    # print("=" * 50)
    # print("说明:")
    # print("- 实时识别文本会在同一行更新")
    # print("- 完整的句子会以[完整句子]标记在新行显示")
    # print("=" * 50)
    # # 让用户选择麦克风设备
    # print("\n请选择麦克风设备:")
    # mic_device_index = select_device("麦克风")

    # 默认麦克风
    mic_device_index = 1

    # 初始化语音识别器
    recognizer = RealTimeSpeechRecognizer(URL, TOKEN, APPKEY)
    # 启动音频流
    start_audio_stream(mic_device_index, recognizer)
