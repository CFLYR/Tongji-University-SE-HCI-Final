# -*- coding: utf-8 -*-
"""
PPT悬浮窗 - 集成录像功能
PPT Floating Window with Recording Features

功能特性:
1. PPT控制功能（开始、上一页、下一页）
2. 录像功能（屏幕录制）
3. 麦克风录制开关
4. AI实时字幕显示
5. 悬浮窗内容录制选项
6. 字幕录制选项
7. 录制配置菜单
8. 手势控制功能集成
"""
import RealTimeVoiceToText as RTVTT
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QTextEdit, QCheckBox, QSpinBox,
                               QGroupBox, QFormLayout, QComboBox, QSlider, QMenu,
                               QDialog, QDialogButtonBox, QFrame, QScrollArea)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
import os
import threading
from PySide6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor
import sys
import os
import json
import threading
from datetime import datetime
from typing import Optional

# 导入录像相关模块
try:
    from video_recording_assistant import VideoRecordingAssistant, RecordingConfig
    from speech_text_manager import SpeechTextManager

    RECORDING_AVAILABLE = True
except ImportError:
    print("⚠️ 录像功能模块未找到，将禁用录像功能")
    RECORDING_AVAILABLE = False

# 导入手势控制模块
try:
    from unified_ppt_gesture_controller import UnifiedPPTGestureController, PPTAction

    GESTURE_AVAILABLE = True
except ImportError:
    print("⚠️ 手势控制模块未找到，将禁用手势控制功能")
    GESTURE_AVAILABLE = False


class RecordingConfigDialog(QDialog):
    """录制配置对话框"""

    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config or (RecordingConfig() if RECORDING_AVAILABLE else {})
        self.setWindowTitle("录制配置")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.init_ui()
        self.load_config()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 录制选项组
        record_group = QGroupBox("录制选项")
        record_layout = QFormLayout(record_group)

        self.screen_checkbox = QCheckBox("录制屏幕")
        self.camera_checkbox = QCheckBox("录制摄像头")
        self.microphone_checkbox = QCheckBox("录制麦克风")

        record_layout.addRow("屏幕录制:", self.screen_checkbox)
        record_layout.addRow("摄像头录制:", self.camera_checkbox)
        record_layout.addRow("麦克风录制:", self.microphone_checkbox)

        layout.addWidget(record_group)

        # AI字幕选项组
        subtitle_group = QGroupBox("AI字幕选项")
        subtitle_layout = QFormLayout(subtitle_group)
        self.ai_subtitles_checkbox = QCheckBox("启用AI实时字幕")
        self.script_correction_checkbox = QCheckBox("启用文稿修正")
        self.overlay_subtitles_checkbox = QCheckBox("录制时显示字幕")
        self.record_floating_window_checkbox = QCheckBox("录制悬浮窗内容")

        subtitle_layout.addRow("AI字幕:", self.ai_subtitles_checkbox)
        subtitle_layout.addRow("文稿修正:", self.script_correction_checkbox)
        subtitle_layout.addRow("字幕叠加:", self.overlay_subtitles_checkbox)
        subtitle_layout.addRow("悬浮窗录制:", self.record_floating_window_checkbox)

        layout.addWidget(subtitle_group)

        # 视频参数组
        video_group = QGroupBox("视频参数")
        video_layout = QFormLayout(video_group)

        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(15, 60)
        self.fps_spinbox.setValue(30)
        self.fps_spinbox.setSuffix(" FPS")

        self.camera_position_combo = QComboBox()
        self.camera_position_combo.addItems(["右下角", "左下角", "右上角", "左上角"])

        self.camera_size_combo = QComboBox()
        self.camera_size_combo.addItems(["小 (240x180)", "中 (320x240)", "大 (480x360)"])

        video_layout.addRow("视频帧率:", self.fps_spinbox)
        video_layout.addRow("摄像头位置:", self.camera_position_combo)
        video_layout.addRow("摄像头大小:", self.camera_size_combo)

        layout.addWidget(video_group)

        # 输出设置组
        output_group = QGroupBox("输出设置")
        output_layout = QFormLayout(output_group)

        self.output_dir_label = QLabel("recordings/")
        self.output_dir_btn = QPushButton("选择目录...")
        self.output_dir_btn.clicked.connect(self.select_output_dir)

        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_label)
        output_dir_layout.addWidget(self.output_dir_btn)

        output_layout.addRow("输出目录:", output_dir_layout)

        layout.addWidget(output_group)
        # 按钮组
        button_layout = QHBoxLayout()

        # 测试按钮
        test_btn = QPushButton("测试配置")
        test_btn.clicked.connect(self.test_config)
        button_layout.addWidget(test_btn)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)

        layout.addLayout(button_layout)

        # 设置样式
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #165DFF;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #cccccc;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #165DFF;
                border-radius: 3px;
                background-color: #165DFF;
            }
        """)

    def load_config(self):
        """加载配置到UI"""
        if not RECORDING_AVAILABLE:
            return

        self.screen_checkbox.setChecked(getattr(self.config, 'enable_screen', True))
        self.camera_checkbox.setChecked(getattr(self.config, 'enable_camera', False))
        self.microphone_checkbox.setChecked(getattr(self.config, 'enable_microphone', True))
        self.ai_subtitles_checkbox.setChecked(getattr(self.config, 'enable_ai_subtitles', True))
        self.script_correction_checkbox.setChecked(getattr(self.config, 'enable_script_correction', False))
        self.record_floating_window_checkbox.setChecked(getattr(self.config, 'record_floating_window', False))

        self.fps_spinbox.setValue(getattr(self.config, 'video_fps', 30))

        # 摄像头位置映射
        position_map = {
            "bottom_right": 0, "bottom_left": 1,
            "top_right": 2, "top_left": 3
        }
        camera_position = getattr(self.config, 'camera_position', 'bottom_right')
        self.camera_position_combo.setCurrentIndex(
            position_map.get(camera_position, 0)
        )

        # 摄像头大小映射
        size_map = {
            (240, 180): 0, (320, 240): 1, (480, 360): 2
        }
        camera_size = getattr(self.config, 'camera_size', (320, 240))
        self.camera_size_combo.setCurrentIndex(
            size_map.get(camera_size, 1)
        )

        output_dir = getattr(self.config, 'output_dir', 'recordings')
        self.output_dir_label.setText(output_dir)

    def get_config(self):
        """从UI获取配置"""
        if not RECORDING_AVAILABLE:
            return {}

        config = RecordingConfig()

        config.enable_screen = self.screen_checkbox.isChecked()
        config.enable_camera = self.camera_checkbox.isChecked()
        config.enable_microphone = self.microphone_checkbox.isChecked()
        config.enable_ai_subtitles = self.ai_subtitles_checkbox.isChecked()
        config.enable_script_correction = self.script_correction_checkbox.isChecked()
        config.record_floating_window = self.record_floating_window_checkbox.isChecked()

        config.video_fps = self.fps_spinbox.value()

        # 摄像头位置映射
        position_map = ["bottom_right", "bottom_left", "top_right", "top_left"]
        config.camera_position = position_map[self.camera_position_combo.currentIndex()]

        # 摄像头大小映射
        size_map = [(240, 180), (320, 240), (480, 360)]
        config.camera_size = size_map[self.camera_size_combo.currentIndex()]

        config.output_dir = self.output_dir_label.text()

        return config

    def select_output_dir(self):
        """选择输出目录"""
        from PySide6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "选择录制输出目录")
        if dir_path:
            self.output_dir_label.setText(dir_path)

    def test_config(self):
        """测试当前配置"""
        config = self.get_config()
        if config:
            print("🔍 当前录制配置测试:")
            print(f"  - 录制屏幕: {config.enable_screen}")
            print(f"  - 录制摄像头: {config.enable_camera}")
            print(f"  - 录制麦克风: {config.enable_microphone}")
            print(f"  - AI字幕: {config.enable_ai_subtitles}")
            print(f"  - 文稿修正: {config.enable_script_correction}")
            print(f"  - 录制悬浮窗: {config.record_floating_window}")
            print(f"  - 视频帧率: {config.video_fps}")
            print(f"  - 摄像头位置: {config.camera_position}")
            print(f"  - 摄像头大小: {config.camera_size}")
            print(f"  - 输出目录: {config.output_dir}")

            # 特别强调悬浮窗录制选项
            if config.record_floating_window:
                print("✅ 悬浮窗将被录制到视频中")
            else:
                print("🚫 悬浮窗将被遮盖（模糊处理）")


class SubtitleDisplayWidget(QWidget):
    """字幕显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_subtitle = ""
        self.subtitle_history = []
        self.max_history = 5
        self.setFixedHeight(80)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # 当前字幕显示
        self.current_label = QLabel("等待AI字幕...")
        self.current_label.setAlignment(Qt.AlignCenter)
        self.current_label.setWordWrap(True)
        self.current_label.setStyleSheet("""
            QLabel {
                background: rgba(22, 93, 255, 0.1);
                border: 1px solid #165DFF;
                border-radius: 4px;
                padding: 6px;
                font-size: 11px;
                font-weight: bold;
                color: #165DFF;
            }
        """)
        layout.addWidget(self.current_label)

        # 历史字幕显示
        self.history_label = QLabel("")
        self.history_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.history_label.setWordWrap(True)
        self.history_label.setFixedHeight(35)
        self.history_label.setStyleSheet("""
            QLabel {
                background: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 4px;
                font-size: 9px;
                color: #666;
            }
        """)
        layout.addWidget(self.history_label)
    def update_subtitle(self, text: str):
        """更新字幕"""
        if text and text.strip():
            # 如果文本很短或者是临时文本（正在识别中），直接更新当前显示
            if len(text.strip()) <= 2 or not text.endswith(('。', '！', '？', '.', '!', '?')):
                # 临时文本，直接显示
                self.current_label.setText(text)
                self.current_subtitle = text
            else:
                # 完整句子，添加到历史记录
                if text != self.current_subtitle:
                    # 将当前字幕移到历史记录
                    if self.current_subtitle:
                        self.add_to_history(self.current_subtitle)
                    
                    # 更新当前字幕
                    self.current_subtitle = text
                    self.current_label.setText(text)

    def add_to_history(self, text: str):
        """添加到历史记录"""
        self.subtitle_history.append(text)
        if len(self.subtitle_history) > self.max_history:
            self.subtitle_history.pop(0)

        # 更新历史显示
        history_text = " | ".join(self.subtitle_history[-2:])  # 显示最近2条
        self.history_label.setText(history_text)

    def clear_subtitles(self):
        """清除所有字幕"""
        self.current_subtitle = ""
        self.subtitle_history = []
        self.current_label.setText("等待AI字幕...")
        self.history_label.setText("")


class RecordingStatusWidget(QWidget):
    """录制状态显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_recording = False
        self.recording_duration = 0
        self.init_ui()

        # 录制时间更新定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_duration)

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        # 录制状态指示器
        self.status_indicator = QLabel("●")
        self.status_indicator.setFixedSize(10, 10)
        self.status_indicator.setStyleSheet("color: #888; font-size: 12px;")

        # 录制时间显示
        self.duration_label = QLabel("00:00:00")
        self.duration_label.setStyleSheet("""
            QLabel {
                font-family: 'Courier New', monospace;
                font-size: 10px;
                font-weight: bold;
                color: #333;
            }
        """)

        layout.addWidget(self.status_indicator)
        layout.addWidget(self.duration_label)
        layout.addStretch()

    def start_recording(self):
        """开始录制"""
        self.is_recording = True
        self.recording_duration = 0
        self.status_indicator.setStyleSheet("color: #ff4444; font-size: 12px;")
        self.timer.start(1000)  # 每秒更新

    def stop_recording(self):
        """停止录制"""
        self.is_recording = False
        self.status_indicator.setStyleSheet("color: #888; font-size: 12px;")
        self.timer.stop()

    def update_duration(self):
        """更新录制时长"""
        if self.is_recording:
            self.recording_duration += 1
            hours = self.recording_duration // 3600
            minutes = (self.recording_duration % 3600) // 60
            seconds = self.recording_duration % 60
            self.duration_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")


class PPTFloatingWindow(QWidget):
    """PPT悬浮窗 - 集成录像功能"""
    # 定义信号
    recording_started = Signal()
    recording_stopped = Signal(str)  # 录制文件路径
    subtitle_updated = Signal(str)

    def __init__(self):
        super().__init__()

        # 窗口属性
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(340, 260)

        # 录制相关
        if RECORDING_AVAILABLE:
            self.recording_assistant = VideoRecordingAssistant()
            self.recording_config = RecordingConfig()
        else:
            self.recording_assistant = None
            self.recording_config = None

        # 手势控制相关
        if GESTURE_AVAILABLE:
            self.gesture_controller = UnifiedPPTGestureController()
            self.gesture_thread = None
            self.is_gesture_active = False
        else:
            self.gesture_controller = None
            self.is_gesture_active = False

        # 主控制器引用，用于检查手势识别状态
        self.main_controller = None

        # 拖拽相关
        self._drag_active = False
        self._drag_pos = None
        # 最小化状态
        self._is_minimized = False
        self._normal_size = (340, 260)
        self._minimized_size = (80, 40)  # 增大最小化尺寸以完全显示按钮
        self.init_ui()

        # 设置按钮拖拽处理
        self.setup_button_drag_handling()        # 字幕更新定时器
        if RECORDING_AVAILABLE:
            self.subtitle_timer = QTimer()
            self.subtitle_timer.timeout.connect(self.update_subtitle_display)

        # 语音识别字幕更新定时器
        self.voice_subtitle_timer = QTimer()
        self.voice_subtitle_timer.timeout.connect(self.update_voice_subtitle_display)

        # 演讲稿管理器
        self.speech_manager = None
        # 演讲稿滚动显示器
        self.speech_scroll_displayer = None

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # 顶部标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("PPT控制台")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #333;
            }
        """)

        # 录制状态显示
        self.recording_status = RecordingStatusWidget()  # 最小化按钮（原关闭按钮）
        self.minimize_btn = QPushButton("—")
        self.minimize_btn.setFixedSize(24, 24)  # 增大按钮尺寸
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background: #E0E0E0;
                color: #333;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #CCCCCC;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: #FF9800;
                color: white;
                border: 1px solid #FF9800;
            }
            QPushButton:pressed {
                background: #F57C00;
            }
        """)
        self.minimize_btn.clicked.connect(self.toggle_minimize)

        title_layout.addWidget(title_label)
        title_layout.addWidget(self.recording_status)
        title_layout.addStretch()
        title_layout.addWidget(self.minimize_btn)
        main_layout.addLayout(title_layout)

        # PPT控制按钮区
        ppt_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("开始语音")
        self.btn_prev = QPushButton("上一页")
        self.btn_next = QPushButton("下一页")

        for btn in [self.btn_start, self.btn_prev, self.btn_next]:
            btn.setFixedHeight(28)
            btn.setStyleSheet("""
                QPushButton {
                    background: #165DFF;
                    color: white;
                    border-radius: 5px;
                    font-weight: bold;
                    padding: 0 8px;
                    border: none;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #466BB0;
                }
                QPushButton:pressed {
                    background: #0F4FDD;
                }
            """)        
        ppt_layout.addWidget(self.btn_start)
        ppt_layout.addWidget(self.btn_prev)
        ppt_layout.addWidget(self.btn_next)
        main_layout.addLayout(ppt_layout)
        # 连接PPT控制按钮事件
        self.btn_start.clicked.connect(self.toggle_voice_recognition)  # 开始/停止语音识别

        # 连接上一页和下一页按钮
        self.btn_prev.clicked.connect(self.previous_slide)
        self.btn_next.clicked.connect(self.next_slide)

        # 录制控制按钮区
        if RECORDING_AVAILABLE:
            record_layout = QHBoxLayout()

            self.btn_record = QPushButton("开始录制")
            self.btn_record.setFixedHeight(28)
            self.btn_record.setStyleSheet("""
                QPushButton {
                    background: #52C41A;
                    color: white;
                    border-radius: 5px;
                    font-weight: bold;
                    padding: 0 8px;
                    border: none;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #73D13D;
                }
                QPushButton:pressed {
                    background: #389E0D;
                }
            """)
            self.btn_record.clicked.connect(self.toggle_recording)
            self.btn_config = QPushButton("⚙️")
            self.btn_config.setFixedSize(28, 28)
            self.btn_config.setStyleSheet("""
                QPushButton {
                    background: #8C8C8C;
                    color: white;
                    border-radius: 5px;
                    font-weight: bold;
                    border: none;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #A6A6A6;
                }
            """)
            self.btn_config.clicked.connect(self.show_config_dialog)

            record_layout.addWidget(self.btn_record, 1)
            record_layout.addWidget(self.btn_config)
            main_layout.addLayout(record_layout)

        # 文稿展示区
        self.text_label = QLabel("文稿展示区")
        self.text_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #222;
                background: #F5F5F5;
                border-radius: 5px;
                padding: 6px;
                border: 1px solid #E0E0E0;
            }
        """)        
        self.text_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.text_label.setWordWrap(True)
        self.text_label.setMinimumHeight(50)
        main_layout.addWidget(self.text_label)

        # AI字幕显示区（语音识别字幕显示）
        self.subtitle_display = SubtitleDisplayWidget()
        main_layout.addWidget(self.subtitle_display)

        # 设置整体样式
        self.setStyleSheet("""
            PPTFloatingWindow {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 10px;
                border: 1px solid #CCCCCC;
            }        """) 
    def toggle_voice_recognition(self):
        # 启动语音识别
        if self.main_controller.audio_thread is None or not self.main_controller.audio_thread.is_alive():
            self.main_controller.audio_thread = threading.Thread(target=RTVTT.start_audio_stream,
                                                                 args=(self.main_controller.voice_recognizer,))
            self.main_controller.audio_thread.start()
            
            # 启动语音字幕更新定时器
            if hasattr(self, 'voice_subtitle_timer'):
                self.voice_subtitle_timer.start(500)  # 每500ms更新一次字幕
            
            # 更新按钮文本
            self.btn_start.setText("停止语音")
            print("语音识别开启✅")
        # 停止语音识别
        elif self.main_controller.audio_thread and self.main_controller.audio_thread.is_alive():
            RTVTT.toggle_audio_stream(False)
            
            # 停止语音字幕更新定时器
            if hasattr(self, 'voice_subtitle_timer'):
                self.voice_subtitle_timer.stop()
            
            # 更新按钮文本
            self.btn_start.setText("开始语音")
            print("语音识别停止❌")

    def set_speech_manager(self, speech_manager):
        """设置演讲稿管理器"""
        self.speech_manager = speech_manager
        if RECORDING_AVAILABLE and self.recording_assistant:
            self.recording_assistant.set_speech_manager(speech_manager)

    def set_main_controller(self, main_controller):
        """设置主控制器引用"""
        self.main_controller = main_controller

    def set_script_text(self, text: str):
        """设置文稿文本"""
        self.text_label.setText(text)

    def toggle_recording(self):
        """切换录制状态"""
        if not RECORDING_AVAILABLE:
            print("❌ 录像功能不可用")
            return

        if not self.recording_assistant.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """开始录制"""
        if not RECORDING_AVAILABLE:
            return

        # 更新录制配置
        self.recording_assistant.config = self.recording_config

        # 调试信息
        print(f"🔍 DEBUG: 录制配置 - record_floating_window = {self.recording_config.record_floating_window}")

        # 传递悬浮窗对象到录制助手，用于悬浮窗区域排除
        if self.recording_assistant.start_recording(floating_window=self):
            self.btn_record.setText("停止录制")
            self.btn_record.setStyleSheet("""
                QPushButton {
                    background: #FF4D4F;
                    color: white;
                    border-radius: 5px;
                    font-weight: bold;
                    padding: 0 8px;
                    border: none;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #FF7875;
                }
                QPushButton:pressed {
                    background: #D9363E;
                }
            """)

            self.recording_status.start_recording()

            # 如果启用AI字幕，开始字幕更新
            if self.recording_config.enable_ai_subtitles:
                self.subtitle_timer.start(1000)

            self.recording_started.emit()
            print("🎬 录制已开始")
        else:
            print("❌ 录制启动失败")

    def stop_recording(self):
        """停止录制"""
        if not RECORDING_AVAILABLE:
            return

        self.recording_assistant.stop_recording()

        self.btn_record.setText("开始录制")
        self.btn_record.setStyleSheet("""
            QPushButton {
                background: #52C41A;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                padding: 0 8px;
                border: none;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #73D13D;
            }
            QPushButton:pressed {
                background: #389E0D;
            }
        """)

        self.recording_status.stop_recording()
        if hasattr(self, 'subtitle_timer'):
            self.subtitle_timer.stop()

        # 获取录制文件路径
        if self.recording_assistant.current_session_id:
            session_dir = os.path.join(
                self.recording_assistant.output_dir,
                self.recording_assistant.current_session_id
            )
            self.recording_stopped.emit(session_dir)     
        print("🎬 录制已停止")

    def update_subtitle_display(self):
        """更新字幕显示"""
        if not RECORDING_AVAILABLE or not self.recording_assistant.is_recording:
            return

        subtitles = self.recording_assistant.get_current_subtitles()
        if subtitles:
            latest_subtitle = subtitles[-1]
            text = (latest_subtitle.corrected_text
                    if latest_subtitle.is_corrected
                    else latest_subtitle.text)
            if hasattr(self, 'subtitle_display'):
                self.subtitle_display.update_subtitle(text)
            self.subtitle_updated.emit(text)
            
    def update_voice_subtitle_display(self):
        """更新语音识别字幕显示"""
        if not self.main_controller or not self.main_controller.voice_recognizer:
            return
        
        try:
            # 获取实时语音文本
            current_text = self.main_controller.voice_recognizer.get_current_text()
            last_complete_sentence = self.main_controller.voice_recognizer.get_last_complete_sentence()
            
            # 优先显示当前正在识别的文本，如果没有则显示最后完成的句子
            display_text = ""
            if current_text and current_text.strip():
                display_text = f"🎤 {current_text}"  # 正在识别的文本加上麦克风图标
            elif last_complete_sentence and last_complete_sentence.strip():
                display_text = f"✅ {last_complete_sentence}"  # 完成的句子加上对勾图标
            
            if display_text and hasattr(self, 'subtitle_display'):
                self.subtitle_display.update_subtitle(display_text)
        except Exception as e:
            print(f"❌ 更新语音字幕失败: {e}")

    def show_config_dialog(self):
        """显示配置对话框"""
        if not RECORDING_AVAILABLE:
            print("❌ 录像功能不可用")
            return

        dialog = RecordingConfigDialog(self, self.recording_config)
        if dialog.exec() == QDialog.Accepted:
            self.recording_config = dialog.get_config()
            print("📝 录制配置已更新")

    def previous_slide(self):
        """上一张幻灯片"""
        print("🔙 执行：上一张幻灯片")
        try:
            # 先尝试激活PPT窗口
            self._activate_ppt_window()

            # 直接发送按键，不依赖控制器状态
            import pyautogui as pt
            pt.FAILSAFE = False
            pt.PAUSE = 0.1
            pt.press('left')  # 发送左箭头键（上一页）
            print("✅ 成功发送按键：left 箭头（上一页）")

        except Exception as e:
            print(f"❌ 上一张幻灯片失败: {e}")
            import traceback
            traceback.print_exc()

    def next_slide(self):
        """下一张幻灯片"""
        print("🔜 执行：下一张幻灯片")
        try:
            # 先尝试激活PPT窗口
            self._activate_ppt_window()

            # 直接发送按键，不依赖控制器状态
            import pyautogui as pt
            pt.FAILSAFE = False
            pt.PAUSE = 0.1
            pt.press('right')  # 发送右箭头键（下一页）
            print("✅ 成功发送按键：right 箭头（下一页）")

        except Exception as e:
            print(f"❌ 下一张幻灯片失败: {e}")
            import traceback
            traceback.print_exc()

    def _activate_ppt_window(self):
        """激活PPT窗口"""
        try:
            # 首先尝试通过Windows API激活PPT窗口
            try:
                import win32gui
                import win32con
                import time

                def enum_windows_callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        window_text = win32gui.GetWindowText(hwnd)
                        class_name = win32gui.GetClassName(hwnd)
                        # 检查是否是PowerPoint窗口
                        if ('PowerPoint' in window_text or
                                'PP' in class_name or
                                'POWERPNT' in class_name.upper() or
                                '幻灯片放映' in window_text or
                                'Slide Show' in window_text):
                            windows.append(hwnd)
                    return True

                windows = []
                win32gui.EnumWindows(enum_windows_callback, windows)

                if windows:
                    # 激活找到的第一个PowerPoint窗口
                    hwnd = windows[0]
                    win32gui.SetForegroundWindow(hwnd)
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    time.sleep(0.2)  # 等待窗口激活
                    print("✅ PPT窗口已激活")
                    return True
                else:
                    print("⚠️ 未找到PPT窗口")

            except ImportError:
                print("⚠️ Windows API不可用，使用备用方法")

            # 备用方法：使用Alt+Tab切换窗口
            import pyautogui as pt
            import time
            pt.hotkey('alt', 'tab')
            time.sleep(0.2)
            print("🔄 尝试切换到PPT窗口")
            return True

        except Exception as e:
            print(f"❌ 激活PPT窗口失败: {e}")
            return False

    def toggle_gesture_control(self):
        """切换手势控制状态"""
        if not GESTURE_AVAILABLE:
            print("❌ 手势控制功能不可用")
            return
        if self.is_gesture_active:
            self.stop_gesture_control()
        else:
            self.start_gesture_control()

    def start_gesture_control(self):
        """启动手势控制"""
        if not GESTURE_AVAILABLE or self.is_gesture_active:
            return

        # 检查主窗口的手势识别状态
        if self.main_controller and hasattr(self.main_controller, 'gesture_controller'):
            if not getattr(self.main_controller.gesture_controller, 'running', False):
                print("❌ 手势识别未在主窗口启用，请先在主窗口勾选'启用手势识别'")
                return

        try:
            # 首先检查并设置PPT演示状态
            self._setup_ppt_presentation_state()

            # 更新按钮状态
            self.btn_start.setText("停止")
            self.btn_start.setStyleSheet("""
                QPushButton {
                    background: #FF4D4F;
                    color: white;
                    border-radius: 5px;
                    font-weight: bold;
                    padding: 0 8px;
                    border: none;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #FF7875;
                }
                QPushButton:pressed {
                    background: #D9363E;
                }
            """)
            # 启动手势控制线程
            self.gesture_thread = threading.Thread(target=self._run_gesture_control, daemon=True)
            self.is_gesture_active = True
            self.gesture_thread.start()

            print("🖐️ 手势控制已启动")

        except Exception as e:
            print(f"❌ 启动手势控制失败: {e}")
            self.is_gesture_active = False

    def _setup_ppt_presentation_state(self):
        """设置PPT演示状态"""
        if not self.gesture_controller:
            return

        try:
            # 只设置PPT控制器状态，不自动打开PPT文件
            ppt_controller = self.gesture_controller.ppt_controller

            # 直接设置为活跃状态，允许按钮控制
            ppt_controller.is_presentation_active = True
            print("✅ PPT控制状态已设置为活跃，按钮控制可用")
            print("📢 提示：请确保PPT已在演示模式（按F5进入），然后可以使用手势和按钮控制")

        except Exception as e:
            print(f"⚠️ 设置PPT状态时出错: {e}")
            # 即使出错，也允许尝试控制
            if self.gesture_controller:
                self.gesture_controller.ppt_controller.is_presentation_active = True

    def stop_gesture_control(self):
        """停止手势控制"""
        if not GESTURE_AVAILABLE or not self.is_gesture_active:
            return

        try:
            # 停止手势控制
            self.is_gesture_active = False
            if self.gesture_controller:
                self.gesture_controller.running = False

            # 更新按钮状态
            self.btn_start.setText("开始")
            self.btn_start.setStyleSheet("""
                QPushButton {
                    background: #165DFF;
                    color: white;
                    border-radius: 5px;
                    font-weight: bold;
                    padding: 0 8px;
                    border: none;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #466BB0;
                }
                QPushButton:pressed {
                    background: #0F4FDD;
                }
            """)

            # 等待线程结束
            if self.gesture_thread and self.gesture_thread.is_alive():
                self.gesture_thread.join(timeout=1.0)

            print("🛑 手势控制已停止")

        except Exception as e:
            print(f"❌ 停止手势控制失败: {e}")

    def _run_gesture_control(self):
        """在后台线程中运行手势控制"""
        try:
            if self.gesture_controller:
                # 重置手势控制器状态
                self.gesture_controller.running = True
                # 运行手势控制（这会阻塞直到停止）
                self.gesture_controller.run()
        except Exception as e:
            print(f"❌ 手势控制运行出错: {e}")
        finally:
            # 确保状态正确重置
            self.is_gesture_active = False

    def get_recording_status(self):
        """获取录制状态"""
        if not RECORDING_AVAILABLE:
            return {
                "is_recording": self.recording_assistant.is_recording,
                "session_id": self.recording_assistant.current_session_id,
                "recording_available": True,
                "config": self.recording_config.__dict__ if self.recording_config else {}
            }

    def mousePressEvent(self, event):
        """鼠标按下事件 - 用于拖拽"""
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 用于拖拽"""
        if self._drag_active and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 结束拖拽"""
        self._drag_active = False
        
    def closeEvent(self, event):
        """关闭事件"""
        # 如果正在录制，先停止录制
        if RECORDING_AVAILABLE and self.recording_assistant and self.recording_assistant.is_recording:
            self.stop_recording()

        # 如果手势控制正在运行，先停止手势控制
        if GESTURE_AVAILABLE and self.is_gesture_active:
            self.stop_gesture_control()

        # 停止语音识别
        if hasattr(self, 'voice_subtitle_timer'):
            self.voice_subtitle_timer.stop()
        
        # 停止语音识别
        if self.main_controller and self.main_controller.audio_thread and self.main_controller.audio_thread.is_alive():
            RTVTT.toggle_audio_stream(False)

        # 清理字幕显示
        if hasattr(self, 'subtitle_display'):
            self.subtitle_display.clear_subtitles()

        event.accept()

    def toggle_minimize(self):
        """切换最小化状态"""
        if self._is_minimized:
            self.restore_window()
        else:
            self.minimize_window()

    def minimize_window(self):
        """最小化窗口"""
        self._is_minimized = True

        # 保存当前尺寸
        self._normal_size = (self.width(), self.height())

        # 设置为最小化尺寸
        self.setFixedSize(*self._minimized_size)

        # 隐藏除了最小化按钮外的所有内容
        for child in self.findChildren(QWidget):
            if child != self.minimize_btn:
                child.hide()
        # 更改最小化按钮的样式和文本，使其成为恢复按钮
        self.minimize_btn.setText("展开")
        self.minimize_btn.setFixedSize(70, 30)  # 调整为更合适的小按钮大小
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                font-size: 11px;
                border: none;
                border-radius: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #66BB6A;
            }
            QPushButton:pressed {
                background: #388E3C;
            }
        """)
        # 创建一个简单的布局来显示小按钮
        if hasattr(self, 'minimized_layout'):
            # 清理之前的布局
            while self.minimized_layout.count():
                self.minimized_layout.takeAt(0)
        else:
            self.minimized_layout = QVBoxLayout()

        self.minimized_layout.addWidget(self.minimize_btn)
        self.minimized_layout.setContentsMargins(5, 5, 5, 5)  # 增加边距确保按钮完全显示
        self.minimized_layout.setAlignment(Qt.AlignCenter)  # 居中对齐

        # 设置新的布局
        if self.layout():
            # 清理当前布局
            QWidget().setLayout(self.layout())
        self.setLayout(self.minimized_layout)

        print("📦 悬浮窗已最小化")

    def restore_window(self):
        """恢复窗口"""
        self._is_minimized = False

        # 恢复原始尺寸
        self.setFixedSize(*self._normal_size)
        # 恢复最小化按钮的原始样式
        self.minimize_btn.setText("—")
        self.minimize_btn.setFixedSize(24, 24)
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background: #E0E0E0;
                color: #333;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #CCCCCC;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: #FF9800;
                color: white;
                border: 1px solid #FF9800;
            }
            QPushButton:pressed {
                background: #F57C00;
            }
        """)

        # 重新初始化UI
        if self.layout():
            QWidget().setLayout(self.layout())

        self.init_ui()

        # 显示所有子控件
        for child in self.findChildren(QWidget):
            child.show()

        print("📂 悬浮窗已恢复")

    def setup_button_drag_handling(self):
        """为最小化按钮设置拖拽事件处理"""
        # 为按钮添加鼠标事件过滤器，使其在最小化状态下可以拖拽
        self.minimize_btn.mousePressEvent = self.button_mouse_press_event
        self.minimize_btn.mouseMoveEvent = self.button_mouse_move_event
        self.minimize_btn.mouseReleaseEvent = self.button_mouse_release_event

    def button_mouse_press_event(self, event):
        """按钮的鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            if self._is_minimized:
                # 在最小化状态下，记录拖拽信息
                self._drag_active = True
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self._button_drag_start = True
                event.accept()
            else:
                # 正常状态下，按钮不处理拖拽
                QPushButton.mousePressEvent(self.minimize_btn, event)

    def button_mouse_move_event(self, event):
        """按钮的鼠标移动事件"""
        if self._is_minimized and self._drag_active and event.buttons() & Qt.LeftButton:
            # 在最小化状态下移动窗口
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            QPushButton.mouseMoveEvent(self.minimize_btn, event)

    def button_mouse_release_event(self, event):
        """按钮的鼠标释放事件"""
        if self._is_minimized and hasattr(self, '_button_drag_start') and self._button_drag_start:
            # 如果是拖拽结束，不触发按钮点击
            self._drag_active = False
            self._button_drag_start = False
            event.accept()
        else:
            # 正常的按钮点击
            self._drag_active = False
            QPushButton.mouseReleaseEvent(self.minimize_btn, event)


class DraggableMinimizedWidget(QWidget):
    """可拖拽的最小化控件"""

    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.setFixedSize(80, 40)
        self.setStyleSheet("""
            QWidget {
                background: rgba(76, 175, 80, 0.9);
                border: 2px solid #4CAF50;
                border-radius: 20px;
            }
        """)

        # 拖拽相关
        self._drag_active = False
        self._drag_pos = None

        # 设置布局和按钮
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 拖拽区域（左侧）
        drag_area = QLabel("⋮⋮")
        drag_area.setFixedSize(15, 30)
        drag_area.setAlignment(Qt.AlignCenter)
        drag_area.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 10px;
                font-weight: bold;
                background: transparent;
            }
        """)

        # 展开按钮（右侧）
        self.expand_btn = QPushButton("展开")
        self.expand_btn.setFixedSize(50, 30)
        self.expand_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                font-size: 10px;
                border: none;
                border-radius: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #66BB6A;
            }
            QPushButton:pressed {
                background: #388E3C;
            }
        """)
        self.expand_btn.clicked.connect(self.parent_window.restore_window)

        layout.addWidget(drag_area)
        layout.addWidget(self.expand_btn)

        # 设置窗口属性
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def mousePressEvent(self, event):
        """鼠标按下事件 - 用于拖拽"""
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 用于拖拽"""
        if self._drag_active and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 结束拖拽"""
        self._drag_active = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PPTFloatingWindow()
    win.show()
    sys.exit(app.exec())
