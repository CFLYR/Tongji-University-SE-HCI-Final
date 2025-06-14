 
"""
录视频助手 - Video Recording Assistant

功能特性:
1. 录制当前屏幕内容
2. 可选择是否开启前置摄像头
3. 可选择是否录制麦克风
4. 可选择是否开启AI演讲字幕
5. 可选择是否根据导入演讲文稿修正AI字幕
6. 手动修改视频演讲字幕
7. 演讲字幕导出功能
8. 演讲字幕文件读取功能
"""
import RealTimeVoiceToText as RTVTT
import cv2 as cv
import numpy as np
import pyaudio
import wave
import threading
import time
import json
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, asdict
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import speech_recognition as sr
import pyttsx3
from PIL import Image, ImageTk
import mss
import ffmpeg
# 导入现有模块
from speech_text_manager import SpeechTextManager, TextMatcher
from chinese_text_renderer import put_text_auto


@dataclass
class SubtitleSegment:
    """字幕片段数据结构"""
    start_time: float  # 开始时间(秒)
    end_time: float  # 结束时间(秒)
    text: str  # 字幕文本
    corrected_text: str = ""  # 修正后的文本
    confidence: float = 0.0  # 识别置信度
    is_corrected: bool = False  # 是否已修正


@dataclass
class RecordingConfig:
    """录制配置"""
    enable_screen: bool = True  # 录制屏幕
    enable_camera: bool = False  # 录制摄像头
    enable_microphone: bool = True  # 录制麦克风
    enable_ai_subtitles: bool = True  # 开启AI字幕
    enable_script_correction: bool = False  # 开启文稿修正
    record_floating_window: bool = False  # 录制悬浮窗内容
    output_dir: str = "recordings"  # 输出目录
    video_fps: int = 30  # 视频帧率
    audio_sample_rate: int = 44100  # 音频采样率
    camera_position: str = "bottom_right"  # 摄像头位置 
    camera_size: tuple = (320, 240)  # 摄像头大小


class AudioRecorder:
    """音频录制器"""

    def __init__(self, config: RecordingConfig):
        self.config = config
        self.is_recording = False
        self.audio_data = []
        self.audio_thread = None

        # 音频配置
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = config.audio_sample_rate
        self.chunk = 1024

        self.audio = pyaudio.PyAudio()
        self.stream = None

    def start_recording(self):
        """开始录制音频"""
        if self.is_recording:
            return

        self.is_recording = True
        self.audio_data = []

        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )

            self.audio_thread = threading.Thread(target=self._record_audio)
            self.audio_thread.start()
            #print("🎵 开始录制音频")

        except Exception as e:
            # print(
            self.is_recording = False

    def _record_audio(self):
        """录制音频线程"""
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.audio_data.append(data)
            except Exception as e:
                # print(
                break

    def stop_recording(self, output_path: str):
        """停止录制并保存音频"""
        if not self.is_recording:
            return

        self.is_recording = False

        if self.audio_thread:
            self.audio_thread.join()

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        # 保存音频文件
        wf = wave.open(output_path, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.audio_data))
        wf.close()
        #print(f"🎵 音频已保存: {output_path}")

    def cleanup(self):
        """清理资源"""
        if self.stream:
            self.stream.close()
        self.audio.terminate()


class VideoRecorder:
    """视频录制器"""

    def __init__(self, config: RecordingConfig, floating_window=None):
        self.config = config
        self.floating_window = floating_window  # 悬浮窗对象，用于获取窗口位置
        self.is_recording = False
        self.screen_capture = None
        self.camera_capture = None
        self.video_writer = None
        self.recording_thread = None
        self.start_time = None

    def initialize_captures(self):
        """初始化捕获设备"""
        # 初始化屏幕捕获
        if self.config.enable_screen:
            try:
                self.screen_capture = mss.mss()
                self.monitor = self.screen_capture.monitors[1]  # 主显示器
                # print(
            except Exception as e:
                # print(
                self.config.enable_screen = False

        # 初始化摄像头
        if self.config.enable_camera:
            try:
                self.camera_capture = cv.VideoCapture(0)
                if not self.camera_capture.isOpened():
                    # print(
                    self.config.enable_camera = False
                else:
                    self.camera_capture.set(cv.CAP_PROP_FRAME_WIDTH, self.config.camera_size[0])
                    self.camera_capture.set(cv.CAP_PROP_FRAME_HEIGHT, self.config.camera_size[1])
                    # print(
            except Exception as e:
                # print(
                self.config.enable_camera = False

    def start_recording(self, output_path: str):
        """开始录制视频"""
        if self.is_recording:
            return

        self.initialize_captures()

        # 获取屏幕尺寸
        if self.config.enable_screen:
            screen_width = self.monitor["width"]
            screen_height = self.monitor["height"]
        else:
            screen_width, screen_height = 1920, 1080  # 默认尺寸

        # 初始化视频写入器
        fourcc = cv.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv.VideoWriter(
            output_path,
            fourcc,
            self.config.video_fps,
            (screen_width, screen_height)
        )

        if not self.video_writer.isOpened():
            # print(
            return

        self.is_recording = True
        self.start_time = time.time()

        self.recording_thread = threading.Thread(target=self._record_video)
        self.recording_thread.start()
        # print(

    def _record_video(self):
        """录制视频线程"""
        # 在录制线程中重新初始化mss实例以避免线程安全问题
        if self.config.enable_screen:
            thread_screen_capture = mss.mss()
            thread_monitor = thread_screen_capture.monitors[1]
        else:
            thread_screen_capture = None
            thread_monitor = None

        while self.is_recording:
            try:
                frame = self._capture_frame_threaded(thread_screen_capture, thread_monitor)
                if frame is not None:
                    self.video_writer.write(frame)
                time.sleep(1.0 / self.config.video_fps)
            except Exception as e:
                # print(
                break

        # 清理线程本地的screen capture
        if thread_screen_capture:
            thread_screen_capture.close()

    def _capture_frame(self):
        """捕获一帧画面"""
        frame = None

        # 捕获屏幕
        if self.config.enable_screen:
            try:
                screenshot = self.screen_capture.grab(self.monitor)
                frame = np.array(screenshot)
                frame = cv.cvtColor(frame, cv.COLOR_BGRA2BGR)
            except Exception as e:
                # print(
                # 创建黑色画面作为备用
                frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

        # 添加摄像头画面
        if self.config.enable_camera and self.camera_capture:
            ret, camera_frame = self.camera_capture.read()
            if ret:
                frame = self._overlay_camera(frame, camera_frame)

        return frame

    def _capture_frame_threaded(self, thread_screen_capture, thread_monitor):
        """线程安全的帧捕获方法"""
        frame = None

        # 捕获屏幕
        if self.config.enable_screen and thread_screen_capture:
            try:
                screenshot = thread_screen_capture.grab(thread_monitor)
                frame = np.array(screenshot)
                frame = cv.cvtColor(frame, cv.COLOR_BGRA2BGR)

                # 如果不录制悬浮窗内容，需要遮盖悬浮窗区域
                if not self.config.record_floating_window and self.floating_window:
                    frame = self._mask_floating_window(frame)

            except Exception as e:
                # print(
                # 创建黑色画面作为备用
                frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
                cv.putText(frame, "Screen Capture Error", (50, 100),
                           cv.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)

        # 添加摄像头画面
        if self.config.enable_camera and self.camera_capture:
            ret, camera_frame = self.camera_capture.read()
            if ret:
                frame = self._overlay_camera(frame, camera_frame)
            

        return frame

    def _overlay_camera(self, screen_frame, camera_frame):
        """在屏幕画面上叠加摄像头画面"""
        if screen_frame is None:
            return camera_frame

        h, w = screen_frame.shape[:2]
        cam_h, cam_w = self.config.camera_size

        # 调整摄像头画面大小
        camera_resized = cv.resize(camera_frame, (cam_w, cam_h))

        # 根据配置位置放置摄像头画面
        if self.config.camera_position == "bottom_right":
            x, y = w - cam_w - 20, h - cam_h - 20
        elif self.config.camera_position == "bottom_left":
            x, y = 20, h - cam_h - 20
        elif self.config.camera_position == "top_right":
            x, y = w - cam_w - 20, 20
        elif self.config.camera_position == "top_left":
            x, y = 20, 20
        else:
            x, y = w - cam_w - 20, h - cam_h - 20  # 默认右下角
        # 叠加摄像头画面
        screen_frame[y:y + cam_h, x:x + cam_w] = camera_resized
        return screen_frame

    def _mask_floating_window(self, frame):

        """遮盖悬浮窗区域"""
        if not self.floating_window:
            return frame
        
        return frame

    def stop_recording(self):
        """停止录制视频"""
        if not self.is_recording:
            return

        self.is_recording = False

        if self.recording_thread:
            self.recording_thread.join()

        if self.video_writer:
            self.video_writer.release()

        if self.camera_capture:
            self.camera_capture.release()

        # print(

    def get_recording_duration(self):
        """获取录制时长"""
        if self.start_time:
            return time.time() - self.start_time
        return 0


class SpeechRecognizer:
    """语音识别器"""

    def __init__(self, config: RecordingConfig):
        self.config = config
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_recognizing = False
        self.recognition_thread = None
        self.subtitles = []
        self.speech_manager = None
        self.text_matcher = TextMatcher()
        self.RTVTT_recognizer = RTVTT.RealTimeSpeechRecognizer()

        # 调整识别器参数
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)

    def set_speech_manager(self, speech_manager: SpeechTextManager):
        """设置演讲稿管理器"""
        self.speech_manager = speech_manager

    def start_recognition(self):
        """开始语音识别"""
        if self.is_recognizing:
            return

        self.is_recognizing = True
        self.subtitles = []
        self.recognition_thread = threading.Thread(target=self._recognize_speech)
        self.recognition_thread.start()
        # print(

    def _recognize_speech(self):
        """语音识别线程"""
        start_time = time.time()

        while self.is_recognizing:
            try:
                with self.microphone as source:
                    # 监听音频
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)

                try:
                    # 识别语音（使用Google语音识别）
                    # text = self.recognizer.recognize_google(audio, language='zh-CN')
                    # 实时语音识别使用阿里云
                    self.RTVTT_recognizer = RTVTT.get_RTVTT_recognizer()
                    # RTVTT.start_audio_stream(self.RTVTT_recognizer)
                    text = self.RTVTT_recognizer.last_complete_sentence

                    current_time = time.time() - start_time

                    # 创建字幕片段
                    subtitle = SubtitleSegment(
                        start_time=current_time - 5,  # 估算开始时间
                        end_time=current_time,
                        text=text,
                        confidence=0.8  # 默认置信度
                    )

                    # 如果启用文稿修正，尝试匹配并修正
                    if self.config.enable_script_correction and self.speech_manager:
                        self._correct_subtitle_with_script(subtitle)

                    self.subtitles.append(subtitle)
                    # print(

                except sr.UnknownValueError:
                    pass  # 无法识别的音频

            except sr.WaitTimeoutError:
                pass  # 超时，继续下一次监听
            except Exception as e:
                # print(
                time.sleep(1)

    def _correct_subtitle_with_script(self, subtitle: SubtitleSegment):
        """使用演讲稿修正字幕"""
        if not self.speech_manager:
            return

        # 尝试匹配演讲稿
        match_found, script_text, confidence = self.speech_manager.match_input_text(subtitle.text)

        if match_found and confidence > 0.3:  # 如果匹配度较高
            subtitle.corrected_text = script_text
            subtitle.is_corrected = True
            subtitle.confidence = confidence
            # print(

    def stop_recognition(self):
        """停止语音识别"""
        if not self.is_recognizing:
            return

        self.is_recognizing = False
        if self.recognition_thread:
            self.recognition_thread.join()

        # print(

    def get_subtitles(self) -> List[SubtitleSegment]:
        """获取字幕列表"""
        return self.subtitles.copy()

    def export_subtitles(self, output_path: str, format_type: str = "srt"):
        """导出字幕文件"""
        if not self.subtitles:
            return

        if format_type.lower() == "srt":
            self._export_srt(output_path)
        elif format_type.lower() == "json":
            self._export_json(output_path)
        else:
            self._export_txt(output_path)

    def _export_srt(self, output_path: str):
        """导出SRT格式字幕"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, subtitle in enumerate(self.subtitles, 1):
                start_time = self._format_srt_time(subtitle.start_time)
                end_time = self._format_srt_time(subtitle.end_time)
                text = subtitle.corrected_text if subtitle.is_corrected else subtitle.text

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")

    def _format_srt_time(self, seconds: float) -> str:
        """格式化SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def _export_json(self, output_path: str):
        """导出JSON格式字幕"""
        data = {
            "subtitles": [asdict(subtitle) for subtitle in self.subtitles],
            "export_time": datetime.now().isoformat()
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _export_txt(self, output_path: str):
        """导出纯文本格式字幕"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for subtitle in self.subtitles:
                text = subtitle.corrected_text if subtitle.is_corrected else subtitle.text
                f.write(f"[{subtitle.start_time:.1f}s - {subtitle.end_time:.1f}s] {text}\n")

    def load_subtitles(self, file_path: str):
        """加载字幕文件"""
        if file_path.endswith('.json'):
            self._load_json_subtitles(file_path)
        elif file_path.endswith('.srt'):
            self._load_srt_subtitles(file_path)
        else:
            self._load_txt_subtitles(file_path)

    def _load_json_subtitles(self, file_path: str):
        """加载JSON格式字幕"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.subtitles = []
        for subtitle_data in data.get("subtitles", []):
            subtitle = SubtitleSegment(**subtitle_data)
            self.subtitles.append(subtitle)

    def _load_srt_subtitles(self, file_path: str):
        """加载SRT格式字幕"""
        # 简化的SRT解析，实际项目中可能需要更强大的解析器
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 这里可以实现更复杂的SRT解析逻辑
        print("SRT格式加载功能需要进一步实现")

    def _load_txt_subtitles(self, file_path: str):
        """加载文本格式字幕"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        self.subtitles = []
        for i, line in enumerate(lines):
            line = line.strip()
            if line:
                # 简单解析，实际可能需要更复杂的逻辑
                subtitle = SubtitleSegment(
                    start_time=i * 5,
                    end_time=(i + 1) * 5,
                    text=line
                )
                self.subtitles.append(subtitle)


class VideoRecordingAssistant:
    """录视频助手主类""" 
    
    def __init__(self):
        self.config = RecordingConfig()
        self.audio_recorder = None
        self.video_recorder = None
        self.speech_recognizer = None
        self.speech_manager = None

        self.is_recording = False
        self.output_dir = self.config.output_dir
        self.current_session_id = None

        # 注意：不在初始化时创建输出目录，而是在真正开始录制时创建

    def set_speech_manager(self, speech_manager: SpeechTextManager):
        """设置演讲稿管理器"""
        self.speech_manager = speech_manager
        if self.speech_recognizer:
            self.speech_recognizer.set_speech_manager(speech_manager)

    def update_config(self, **kwargs):
        """更新录制配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        # print(

    def start_recording(self, floating_window=None):
        """开始录制
        
        Args:
            floating_window: 可选的悬浮窗对象，用于在录制时排除悬浮窗区域
        """
        if self.is_recording:
            # print(
            return False

        # 生成会话ID
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(self.output_dir, self.current_session_id)
        os.makedirs(session_dir, exist_ok=True)

        # print(

        try:
            # 初始化录制器
            if self.config.enable_microphone:
                self.audio_recorder = AudioRecorder(self.config)
                self.audio_recorder.start_recording()

            # 创建视频录制器时传递悬浮窗对象
            self.video_recorder = VideoRecorder(self.config, floating_window)
            video_path = os.path.join(session_dir, f"video_{self.current_session_id}.mp4")
            self.video_recorder.start_recording(video_path)

            if self.config.enable_ai_subtitles:
                self.speech_recognizer = SpeechRecognizer(self.config)
                if self.speech_manager:
                    self.speech_recognizer.set_speech_manager(self.speech_manager)
                self.speech_recognizer.start_recognition()

            self.is_recording = True
            # print(
            return True

        except Exception as e:
            # print(
            self.stop_recording()
            return False

    def stop_recording(self):
        """停止录制"""
        if not self.is_recording:
            return

        # print(

        try:
            # 停止音频录制
            if self.audio_recorder:
                session_dir = os.path.join(self.output_dir, self.current_session_id)
                audio_path = os.path.join(session_dir, f"audio_{self.current_session_id}.wav")
                self.audio_recorder.stop_recording(audio_path)
                self.audio_recorder.cleanup()

            # 停止视频录制
            if self.video_recorder:
                self.video_recorder.stop_recording()

            # 停止语音识别
            if self.speech_recognizer:
                self.speech_recognizer.stop_recognition()

                # 导出字幕
                session_dir = os.path.join(self.output_dir, self.current_session_id)
                subtitle_path = os.path.join(session_dir, f"subtitles_{self.current_session_id}.json")
                self.speech_recognizer.export_subtitles(subtitle_path, "json")

                # 也导出SRT格式
                srt_path = os.path.join(session_dir, f"subtitles_{self.current_session_id}.srt")
                self.speech_recognizer.export_subtitles(srt_path, "srt")

            self.is_recording = False
            # print(

            # 尝试合并音视频
            self._merge_audio_video()

        except Exception as e:
            print(f"停止录制时出错: {e}")

    def _merge_audio_video(self):
        """合并音频和视频文件"""
        if not self.current_session_id:
            return

        try:
            session_dir = os.path.join(self.output_dir, self.current_session_id)
            video_path = os.path.join(session_dir, f"video_{self.current_session_id}.mp4")
            audio_path = os.path.join(session_dir, f"audio_{self.current_session_id}.wav")
            output_path = os.path.join(session_dir, f"final_{self.current_session_id}.mp4")

            if os.path.exists(video_path) and os.path.exists(audio_path):
                # 使用ffmpeg合并音视频
                input_video = ffmpeg.input(video_path)
                input_audio = ffmpeg.input(audio_path)

                out = ffmpeg.output(
                    input_video, input_audio,
                    output_path,
                    vcodec='copy',
                    acodec='aac'
                )
                ffmpeg.run(out, overwrite_output=True, quiet=True)

                # print(

        except Exception as e:
            print(f"合并音视频时出错: {e}")

    def get_recording_status(self) -> Dict:
        """获取录制状态"""
        status = {
            "is_recording": self.is_recording,
            "session_id": self.current_session_id,
            "duration": 0,
            "config": asdict(self.config)
        }

        if self.video_recorder and self.is_recording:
            status["duration"] = self.video_recorder.get_recording_duration()

        return status

    def get_current_subtitles(self) -> List[SubtitleSegment]:
        """获取当前字幕"""
        if self.speech_recognizer:
            return self.speech_recognizer.get_subtitles()
        return []

    def edit_subtitle(self, index: int, new_text: str):
        """编辑字幕"""
        if self.speech_recognizer and 0 <= index < len(self.speech_recognizer.subtitles):
            self.speech_recognizer.subtitles[index].text = new_text
            self.speech_recognizer.subtitles[index].is_corrected = True
            # print(

    def export_subtitles(self, output_path: str, format_type: str = "srt"):
        """导出字幕"""
        if self.speech_recognizer:
            self.speech_recognizer.export_subtitles(output_path, format_type)

    def load_subtitles(self, file_path: str):
        """加载字幕文件"""
        if not self.speech_recognizer:
            self.speech_recognizer = SpeechRecognizer(self.config)
        self.speech_recognizer.load_subtitles(file_path)


def test_video_recording_assistant():
    """测试录视频助手"""
    print("=== 录视频助手测试 ===")

    # 创建助手实例
    assistant = VideoRecordingAssistant()

    # 配置录制参数
    assistant.update_config(
        enable_screen=True,
        enable_camera=False,  # 测试时关闭摄像头
        enable_microphone=True,
        enable_ai_subtitles=True,
        enable_script_correction=False
    )

    print("配置完成，按Enter开始录制...")
    input()

    # 开始录制
    if assistant.start_recording():
        print("录制中... 按Enter停止录制")
        input()

        # 停止录制
        assistant.stop_recording()

        # 显示状态
        status = assistant.get_recording_status()
        print(f"录制状态: {status}")

        # 显示字幕
        subtitles = assistant.get_current_subtitles()
        print(f"生成了 {len(subtitles)} 条字幕")
        for i, subtitle in enumerate(subtitles):
            print(f"{i + 1}. [{subtitle.start_time:.1f}s-{subtitle.end_time:.1f}s] {subtitle.text}")


if __name__ == "__main__":
    test_video_recording_assistant()
