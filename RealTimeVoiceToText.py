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
    if status:
        #print(f"🎤 DEBUG: 音频状态警告: {status}", file=sys.stderr)
        x=1
    # 添加简单的音频活动检测
    volume = np.sqrt(np.mean(indata**2))
    if volume > 0.01:  # 如果有足够的音频信号
        #print(f"🎤 DEBUG: 检测到音频信号，音量: {volume:.4f}")
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
        print(f"🔧 DEBUG: 初始化阿里云语音识别器...")
        print(f"🔧 URL: {self.url}")
        print(f"🔧 APPKEY: {self.appkey}")
        print(f"🔧 TOKEN: {self.token[:20]}...") # 只显示前20个字符
        
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
            print("✅ NlsSpeechTranscriber 创建成功")
            
            self.transcriber.start(aformat="pcm",
                                   enable_intermediate_result=True,
                                   enable_punctuation_prediction=True,
                                   enable_inverse_text_normalization=True)
            print("✅ 阿里云语音识别器启动成功")
        except Exception as e:
            print(f"❌ 初始化阿里云语音识别器失败: {e}")
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
        print(f"🔧 DEBUG: on_start 被调用: {message}")

    def on_result_changed(self, message, *args):
        # 解析JSON消息 - 这是实时更新的文本
        print(f"🔧 DEBUG: on_result_changed 被调用: {message}")
        try:
            data = json.loads(message)
            result = data.get('payload', {}).get('result', '')
            self.current_text = result
            if result:
                print(f"🎤 实时识别中: {result}")
        except json.JSONDecodeError:
            print(f"❌ JSON解析失败: {message}")

    def on_completed(self, message, *args):
        print(f"🔧 DEBUG: on_completed 被调用: {message}")

    def on_error(self, message, *args):
        print(f"❌ 阿里云识别错误: {message}")
        print(f"❌ 错误参数: {args}")

    def on_close(self, *args):
        print(f"🔧 DEBUG: on_close 被调用: {args}")


# 调用阿里云的语音转文字的接口
def recognize_speech(audio_data, recognizer):
    # print(f"🔧 DEBUG: recognize_speech 被调用，音频数据长度: {len(audio_data)}")
    try:
        audio_data = np.concatenate(audio_data)
        audio_bytes = audio_data.tobytes()
        # print(f"🔧 DEBUG: 音频数据转换完成，字节长度: {len(audio_bytes)}")
        recognizer.send_audio(audio_bytes)
        # print(f"✅ 音频数据已发送到阿里云")
    except Exception as e:
        print(f"❌ recognize_speech 失败: {e}")
        import traceback
        traceback.print_exc()


# 开启音频流并处理音频数据
def start_audio_stream(recognizer, mic_device_index=1):
    # print(f"🔧 DEBUG: start_audio_stream 被调用，mic_device_index={mic_device_index}")
    global RUNNING
    with running_lock:
        RUNNING = True  # 设置全局变量RUNNING为True，开启语音识别
        print("✅ 语音识别状态已设为开启")

    def audio_processing():
        print("🔧 DEBUG: audio_processing 线程已启动")
        nonlocal recognizer
        mic_audio_buffer = []
        buffer_count = 0

        while True:
            with running_lock:
                if not RUNNING:
                    print("🛑 语音识别已关闭，退出音频处理循环")
                    break

            # 处理音频队列
            queue_size = audio_queue.qsize()
            # if queue_size > 0:
            #     print(f"🎤 DEBUG: 音频队列中有 {queue_size} 个数据包")
                
            while not audio_queue.empty():
                try:
                    audio_data = audio_queue.get()
                    mic_audio_buffer.append(audio_data)
                    buffer_count += 1
                    # if buffer_count % 20 == 0:  # 每20个包打印一次
                    #     print(f"🎤 DEBUG: 已处理 {buffer_count} 个音频包，当前缓冲区长度: {len(mic_audio_buffer)}")
                except Exception as e:
                    print(f"❌ 处理音频队列时出错: {e}")

            if len(mic_audio_buffer) >= 10:
                # print(f"🎤 DEBUG: 缓冲区已满({len(mic_audio_buffer)})，启动识别线程")
                try:
                    threading.Thread(target=recognize_speech, args=(mic_audio_buffer.copy(), recognizer)).start()
                    mic_audio_buffer = []  # 清空缓冲区
                except Exception as e:
                    print(f"❌ 启动识别线程失败: {e}")

            time.sleep(0.1)

        recognizer.stop_transcription()
        print("🔧 DEBUG: audio_processing 线程已结束")

    # 创建麦克风输入流
    print(f"🎤 DEBUG: 正在创建麦克风输入流，设备索引: {mic_device_index}")
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
        print(f"✅ 麦克风设备 {mic_device_index} 测试成功")
        
        mic_stream = sd.InputStream(
            callback=audio_callback,
            channels=1,
            samplerate=16000,
            dtype='int16',
            device=mic_device_index
        )
        print("✅ 麦克风输入流创建成功")
    except Exception as e:
        print(f"❌ 麦克风输入流创建失败: {e}")
        print("🔧 尝试列出可用设备...")
        list_audio_devices()
        return

    print("🎤 DEBUG: 启动音频流...")
    try:
        with mic_stream:
            print("✅ 麦克风已激活，开始音频处理")
            audio_processing()
    except Exception as e:
        print(f"❌ 音频流运行时出错: {e}")
        import traceback
        traceback.print_exc()


def toggle_audio_stream(enabled: bool):
    print(f"🔧 DEBUG: toggle_audio_stream 被调用，enabled={enabled}")
    print(f"切换语音识别状态: {'开启' if enabled else '关闭'}")
    global RUNNING
    with running_lock:
        old_running = RUNNING
        RUNNING = enabled
        print(f"🔧 DEBUG: RUNNING 状态从 {old_running} 变更为 {RUNNING}")
    
    if enabled:
        print("❌ WARNING: toggle_audio_stream(True) 只设置了状态，但没有启动音频流！")
        print("💡 提示: 需要调用 start_audio_stream() 来实际启动音频流和麦克风")


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
    print("🎤 DEBUG: 可用的音频设备:")
    try:
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:  # 只显示输入设备
                print(f"  设备 {i}: {device['name']} (输入通道: {device['max_input_channels']})")
        print(f"🎤 DEBUG: 默认输入设备: {sd.default.device[0]}")
    except Exception as e:
        print(f"❌ 查询音频设备失败: {e}")


def start_real_time_voice_recognition(mic_device_index=None):
    """启动完整的实时语音识别（包括音频流）"""
    print(f"🔧 DEBUG: start_real_time_voice_recognition 被调用，mic_device_index={mic_device_index}")
    
    # 如果没有指定设备，使用默认设备
    if mic_device_index is None:
        try:
            mic_device_index = sd.default.device[0]
            print(f"🎤 使用默认麦克风设备: {mic_device_index}")
        except:
            mic_device_index = 0
            print(f"🎤 使用设备 0 作为默认设备")
    
    # 列出可用设备以供调试
    list_audio_devices()
    
    global _audio_stream_thread, RUNNING
    
    # 检查是否已经在运行
    if _audio_stream_thread and _audio_stream_thread.is_alive():
        print("⚠️ 语音识别已在运行中")
        return True
    
    try:
        # 获取识别器并强制重新初始化transcriber
        recognizer = get_RTVTT_recognizer()
        
        # 重要：强制重新初始化transcriber，确保每次启动都是全新的
        print("🔧 强制重新初始化阿里云transcriber...")
        recognizer._RealTimeSpeechRecognizer__initialize_transcriber()
        print("✅ 阿里云transcriber重新初始化完成")
        
        # 【新增】启动前清空识别内容，确保重新开始
        recognizer.last_complete_sentence = ""
        recognizer.current_text = ""
        print("🧹 识别器内容已清空，确保重新开始")
        print("✅ 语音识别器已准备就绪")
        
        # 启动音频流线程
        print("🚀 正在启动音频流线程...")
        _audio_stream_thread = threading.Thread(
            target=start_audio_stream,
            args=(recognizer, mic_device_index),
            daemon=True
        )
        _audio_stream_thread.start()
        
        # 等待一小段时间确保线程启动
        time.sleep(0.5)
        
        if _audio_stream_thread.is_alive():
            print("✅ 实时语音识别完全启动成功！")
            print(f"🎤 麦克风设备索引: {mic_device_index}")
            print(f"🔧 RUNNING状态: {RUNNING}")
            return True
        else:
            print("❌ 音频流线程启动失败")
            return False
            
    except Exception as e:
        print(f"❌ 启动实时语音识别失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def stop_real_time_voice_recognition():
    """停止实时语音识别"""
    print("🔧 DEBUG: stop_real_time_voice_recognition 被调用")
    global _audio_stream_thread, RUNNING, _RTVTT_recognizer
    
    # 先停止transcriber
    if _RTVTT_recognizer and _RTVTT_recognizer.transcriber:
        try:
            print("🔧 正在停止阿里云transcriber...")
            _RTVTT_recognizer.transcriber.stop()
            print("✅ 阿里云transcriber已停止")
        except Exception as e:
            print(f"⚠️ 停止transcriber时出错: {e}")
    
    # 停止音频流
    with running_lock:
        RUNNING = False
        print(f"🔧 DEBUG: RUNNING 设置为 False")
    
    # 等待线程结束
    if _audio_stream_thread and _audio_stream_thread.is_alive():
        print("⏳ 等待音频流线程结束...")
        _audio_stream_thread.join(timeout=3.0)
        if _audio_stream_thread.is_alive():
            print("⚠️ 音频流线程未能正常结束")
        else:
            print("✅ 音频流线程已结束")
    
    _audio_stream_thread = None
    
    # 重要：清空和重置识别器，准备下次使用
    if _RTVTT_recognizer is not None:
        print("🔧 正在重置语音识别器...")
        _RTVTT_recognizer.last_complete_sentence = ""
        _RTVTT_recognizer.current_text = ""
        _RTVTT_recognizer.transcriber = None  # 清空transcriber，强制下次重新初始化
        print("✅ 语音识别器已重置")
    
    print("✅ 实时语音识别已完全停止")

if __name__ == "__main__":
    # 默认麦克风
    mic_device_index = 1

    # 初始化语音识别器
    recognizer = RealTimeSpeechRecognizer(URL, TOKEN, APPKEY)
    # 开启音频流并处理音频数据
    start_audio_stream(recognizer, mic_device_index)
