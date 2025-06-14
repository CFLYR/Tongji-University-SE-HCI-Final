 
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
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QPoint
import os
import threading
from PySide6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor
import sys
import os
import json
import threading
import traceback
from datetime import datetime
from typing import Optional

# 导入录像相关模块
try:
    from video_recording_assistant import VideoRecordingAssistant, RecordingConfig
    from speech_text_manager import SpeechTextManager

    RECORDING_AVAILABLE = True
except ImportError:
    # print(
    RECORDING_AVAILABLE = False

# 导入手势控制模块
try:
    from unified_ppt_gesture_controller import UnifiedPPTGestureController, PPTAction

    GESTURE_AVAILABLE = True
except ImportError:
    # print(
    GESTURE_AVAILABLE = False


class RecordingConfigDialog(QDialog):
    """录制配置对话框"""

    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config or (RecordingConfig() if RECORDING_AVAILABLE else {})
        self.setWindowTitle("录制配置")
        self.setFixedSize(450, 550)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.init_ui()
        self.load_config()

    def init_ui(self):
        # 创建主容器
        main_widget = QWidget(self)
        main_widget.setStyleSheet("""
            QWidget {
                background-color: #F6F8FB;
                border-radius: 16px;
                border: 2px solid #E3E6F5;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_widget)
        
        content_layout = QVBoxLayout(main_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(25, 25, 25, 25)

        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("🎥 录制配置")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #23213A;
                padding: 8px 0;
                background-color: transparent;
            }
        """)
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8B8BA7;
                border: none;
                border-radius: 16px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E3E6F5;
                color: #23213A;
            }
            QPushButton:pressed {
                background-color: #CFC3F9;
            }
        """)
        close_btn.clicked.connect(self.reject)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        content_layout.addLayout(title_layout)

        # 视频参数组
        video_group = QGroupBox("📹 视频参数")
        video_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #23213A;
                border: 2px solid #E3E6F5;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 15px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #5B5BF6;
                font-weight: bold;
            }        """)
        video_layout = QFormLayout(video_group)

        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(15, 60)
        self.fps_spinbox.setValue(30)
        self.fps_spinbox.setSuffix(" FPS")
        self.fps_spinbox.setFixedHeight(36)

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "1920x1080 (1080p)", 
            "1280x720 (720p)", 
            "1600x900 (900p)",
            "2560x1440 (1440p)",
            "3840x2160 (4K)"
        ])
        self.resolution_combo.setFixedHeight(36)
        self.resolution_combo.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                border: 2px solid #E3E6F5;
                border-radius: 8px;
                padding: 8px 12px;
                color: #000000;
                font-size: 12px;
                font-weight: 500;
            }
            QComboBox:hover {
                border-color: #5B5BF6;
                background-color: #F8F9FF;
            }
            QComboBox:focus {
                border-color: #5B5BF6;
                outline: none;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #E3E6F5;
                border-left-style: solid;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background-color: #F6F8FB;
            }
            QComboBox::down-arrow {
                image: url(resources/icons/downarrow.svg);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #E3E6F5;
                border-radius: 8px;
                background-color: #FFFFFF;
                selection-background-color: #CFC3F9;
                selection-color: #000000;
                color: #000000;
                outline: none;
            }
        """)

        # 设置布局间距
        video_layout.setVerticalSpacing(18)
        video_layout.setHorizontalSpacing(15)
          # 创建带样式的标签
        fps_label = QLabel("视频帧率")
        fps_label.setStyleSheet("""
            QLabel {
                color: #23213A;
                font-size: 11px;
                font-weight: 600;
                padding: 2px 0;
                letter-spacing: 0.5px;
                margin-bottom: 2px;
            }
        """)
        
        resolution_label = QLabel("录制分辨率")
        resolution_label.setStyleSheet("""
            QLabel {
                color: #23213A;
                font-size: 11px;
                font-weight: 600;
                padding: 2px 0;
                letter-spacing: 0.5px;
                margin-bottom: 2px;
            }
        """)

        video_layout.addRow(fps_label, self.fps_spinbox)
        video_layout.addRow(resolution_label, self.resolution_combo)

        content_layout.addWidget(video_group)

        # 输出设置组
        output_group = QGroupBox("📁 输出设置")
        output_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #23213A;
                border: 2px solid #E3E6F5;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 15px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #5B5BF6;
                font-weight: bold;
            }
        """)
        output_layout = QFormLayout(output_group)

        self.output_dir_label = QLabel("recordings/")
        self.output_dir_label.setStyleSheet("""
            QLabel {
                background-color: #F6F8FB;
                border: 2px solid #E3E6F5;
                border-radius: 8px;
                padding: 8px 12px;
                color: #23213A;
                font-size: 12px;
            }
        """)
        
        self.output_dir_btn = QPushButton("选择目录...")
        self.output_dir_btn.setFixedHeight(36)
        self.output_dir_btn.setStyleSheet("""
            QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
            QPushButton:pressed {
                background-color: #E3E6F5;
            }
        """)
        self.output_dir_btn.clicked.connect(self.select_output_dir)

        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_label, 1)
        output_dir_layout.addWidget(self.output_dir_btn, 0)

        # 设置布局间距
        output_layout.setVerticalSpacing(18)
        output_layout.setHorizontalSpacing(15)
        
        # 创建带样式的标签
        output_label = QLabel("输出目录")
        output_label.setStyleSheet("""
            QLabel {
                color: #23213A;
                font-size: 11px;
                font-weight: 600;
                padding: 2px 0;
                letter-spacing: 0.5px;
                margin-bottom: 2px;
            }
        """)

        output_layout.addRow(output_label, output_dir_layout)

        content_layout.addWidget(output_group)
        
        # 添加弹性空间
        content_layout.addStretch()
        
        # 按钮组
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(100, 40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #E3E6F5;
                color: #8B8BA7;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
            QPushButton:pressed {
                background-color: #F6F8FB;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(100, 40)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
            QPushButton:pressed {
                background-color: #E3E6F5;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        content_layout.addLayout(button_layout)

        # 设置全局样式
        self.setStyleSheet("""
            QLabel {
                color: #23213A;
                font-size: 13px;
                font-weight: 500;
                font-family: "Microsoft YaHei", Arial, sans-serif;
            }
            QSpinBox, QComboBox {
                border: 2px solid #E3E6F5;
                border-radius: 8px;
                background-color: #FFFFFF;
                color: #23213A;
                padding: 6px 12px;
                font-size: 12px;
                selection-background-color: #CFC3F9;
                selection-color: #23213A;
            }
            QSpinBox:hover, QComboBox:hover {
                border-color: #CFC3F9;
            }
            QSpinBox:focus, QComboBox:focus {
                border-color: #5B5BF6;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                background: #F6F8FB;
                border-radius: 6px;
                width: 16px;
                margin: 1px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #E3E6F5;
            }
            QSpinBox::up-arrow {
                image: url(resources/icons/uparrow.svg);
                width: 12px;
                height: 12px;
            }
            QSpinBox::down-arrow {
                image: url(resources/icons/downarrow.svg);
                width: 12px;
                height: 12px;
            }
            QComboBox::drop-down {
                border: none;
                background: #F6F8FB;
                border-radius: 6px;
                width: 20px;
                margin: 2px;
            }
            QComboBox::drop-down:hover {
                background: #E3E6F5;
            }
            QComboBox::down-arrow {
                image: url(resources/icons/downarrow.svg);
                width: 12px;
                height: 12px;
            }

            QComboBox QAbstractItemView {
                border: 2px solid #E3E6F5;
                border-radius: 8px;
                background-color: #FFFFFF;
                selection-background-color: #CFC3F9;
                selection-color: #23213A;
                outline: none;
            }        """)
        
    def load_config(self):
        """加载配置到UI"""
        if not RECORDING_AVAILABLE:
            return

        self.fps_spinbox.setValue(getattr(self.config, 'video_fps', 30))

        # 录制分辨率映射
        resolution_map = {
            "1920x1080": 0, "1280x720": 1, "1600x900": 2,
            "2560x1440": 3, "3840x2160": 4
        }
        recording_resolution = getattr(self.config, 'recording_resolution', '1920x1080')
        self.resolution_combo.setCurrentIndex(
            resolution_map.get(recording_resolution, 0)
        )

        output_dir = getattr(self.config, 'output_dir', 'recordings')
        self.output_dir_label.setText(output_dir)
        
    def get_config(self):
        """从UI获取配置"""
        if not RECORDING_AVAILABLE:
            return {}

        config = RecordingConfig()

        # 保持默认值，仅更新视频参数和输出设置
        config.video_fps = self.fps_spinbox.value()

        # 录制分辨率映射
        resolution_map = ["1920x1080", "1280x720", "1600x900", "2560x1440", "3840x2160"]
        config.recording_resolution = resolution_map[self.resolution_combo.currentIndex()]

        config.output_dir = self.output_dir_label.text()

        return config
    
    def select_output_dir(self):
        """选择输出目录"""
        from PySide6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "选择录制输出目录")
        if dir_path:
            self.output_dir_label.setText(dir_path)


class SubtitleDisplayWidget(QWidget):
    """字幕显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_subtitle = ""
        self.subtitle_history = []
        self.max_history = 5
        self.setFixedHeight(78)  # 调整总高度以匹配内部组件
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)  # 减少内部间距

        # 当前字幕显示
        self.current_label = QLabel("无字幕")
        self.current_label.setAlignment(Qt.AlignCenter)
        self.current_label.setWordWrap(True)
        self.current_label.setFixedHeight(40)  # 设置固定高度
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
        layout.addWidget(self.current_label)        # 历史字幕显示
        self.history_label = QLabel("")
        self.history_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.history_label.setWordWrap(False)  # 禁用自动换行
        self.history_label.setFixedHeight(30)  # 减少高度
        self.history_label.setStyleSheet("""
            QLabel {
                background: #FFFFFF;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 4px;
                font-size: 9px;
                color: #666;
            }
        """)
        layout.addWidget(self.history_label)
        
        # 确保布局大小固定
        self.setMinimumHeight(78)
        self.setMaximumHeight(78)

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

        # 更新历史显示 - 对长句子进行截断处理
        recent_history = self.subtitle_history[-2:]  # 显示最近2条
        
        # 截断过长的句子并添加省略号
        max_length_per_item = 15  # 每条历史记录最大字符数
        truncated_history = []
        for item in recent_history:
            # 移除可能的表情符号前缀（如🎤、✅等）
            clean_item = item
            if len(item) > 0 and ord(item[0]) > 127:  # 检测是否以非ASCII字符开头（如表情符号）
                # 查找第一个空格后的内容
                space_index = item.find(' ')
                if space_index > 0 and space_index < len(item) - 1:
                    clean_item = item[space_index + 1:]
            
            # 截断并添加省略号
            if len(clean_item) > max_length_per_item:
                truncated_item = clean_item[:max_length_per_item] + "..."
            else:
                truncated_item = clean_item
            truncated_history.append(truncated_item)
        
        history_text = " | ".join(truncated_history)
        self.history_label.setText(history_text)

    def clear_subtitles(self):
        """清除所有字幕"""
        self.current_subtitle = ""
        self.subtitle_history = []
        self.current_label.setText("无字幕")
        self.history_label.setText("")


class RecordingStatusWidget(QWidget):
    """录制状态显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_recording = False
        self.recording_duration = 0
        
        # 演示计时相关
        self.is_presentation_timing = False
        self.presentation_duration = 0
        
        self.init_ui()

        # 录制时间更新定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_duration)
        
        # 演示计时定时器
        self.presentation_timer = QTimer()
        self.presentation_timer.timeout.connect(self.update_presentation_duration)

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
    
    def start_presentation_timing(self):
        """开始演示计时"""
        self.is_presentation_timing = True
        self.presentation_duration = 0
        self.status_indicator.setStyleSheet("color: #52C41A; font-size: 12px;")  # 绿色表示演示进行中
        self.presentation_timer.start(1000)  # 每秒更新
        # print(

    def stop_presentation_timing(self):
        """停止演示计时"""
        self.is_presentation_timing = False
        self.status_indicator.setStyleSheet("color: #888; font-size: 12px;")  # 恢复灰色
        self.presentation_timer.stop()
        # print(

    def update_presentation_duration(self):
        """更新演示时长"""
        if self.is_presentation_timing:
            self.presentation_duration += 1
            hours = self.presentation_duration // 3600
            minutes = (self.presentation_duration % 3600) // 60
            seconds = self.presentation_duration % 60
            self.duration_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def reset_presentation_timing(self):
        """重置演示计时"""
        self.presentation_duration = 0
        self.duration_label.setText("00:00:00")
        # print(


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
        self.setFixedSize(340, 340)  # 再增加20px高度确保足够空间
        
        # 设置初始位置到屏幕右下方
        self._set_initial_position()

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
        self._drag_start_pos = None
        self._button_drag_start = False  
        
        # 最小化状态
        self._is_minimized = False
        self._normal_size = (340, 260)
        self._minimized_size = (80, 40)  
        self.init_ui()

        # 设置按钮拖拽处理
        self.setup_button_drag_handling()        # 字幕更新定时器
        if RECORDING_AVAILABLE:
            self.subtitle_timer = QTimer()
            self.subtitle_timer.timeout.connect(self.update_subtitle_display)        # 语音识别字幕更新定时器
        self.voice_subtitle_timer = QTimer()
        self.voice_subtitle_timer.timeout.connect(self.update_voice_subtitle_display)

        # 字幕显示控制（默认关闭，由主窗口控制）
        self.subtitle_display_enabled = False

        # 演讲稿管理器
        self.speech_manager = None
        # 演讲稿滚动显示器
        self.speech_scroll_displayer = None
        
        # 主窗口状态检查定时器 - 用于检测复选框状态变化
        self.checkbox_state_timer = QTimer()
        self.checkbox_state_timer.timeout.connect(self.check_main_window_checkbox_state)
        
        # 记录上次的复选框状态，避免重复更新
        self.last_voice_enabled = False
        self.last_gesture_enabled = False
        
        # 标记是否已经点击过开始按钮（用于控制自动状态更新）
        self.has_started_once = False
          # 延迟启动定时器，确保UI完全初始化
        QTimer.singleShot(2000, self.start_state_monitoring)
        
        # 延迟布局修复，确保所有组件都已正确初始化
        QTimer.singleShot(100, self._delayed_layout_fix)
    
    def _set_initial_position(self):
        """设置窗口初始位置到屏幕右下方"""
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        window_width = 340
        window_height = 340  # 与setFixedSize保持一致
        margin = 20  # 距离屏幕边缘的边距
        
        # 计算右下角位置
        x = (screen.width() - window_width) // 2
        y = (screen.height() - window_height) // 2
        
        self.move(x, y)

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)  # 减少组件间距

        # 顶部标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("PPT控制台")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #333;
            }
        """)        # 录制状态显示
        self.recording_status = RecordingStatusWidget() 

        #最小化按钮
        self.minimize_btn = QPushButton("—")
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
        self.minimize_btn.clicked.connect(self.toggle_minimize)
        
        # 关闭按钮
        # self.close_btn = QPushButton("×")
        # self.close_btn.setFixedSize(24, 24)
        # self.close_btn.setStyleSheet("""
        #     QPushButton {
        #         background: #E0E0E0;
        #         color: #333;
        #         font-size: 16px;
        #         font-weight: bold;
        #         border: 1px solid #CCCCCC;
        #         border-radius: 12px;
        #     }
        #     QPushButton:hover {
        #         background: #FF4444;
        #         color: white;
        #         border: 1px solid #FF4444;
        #     }
        #     QPushButton:pressed {
        #         background: #CC0000;
        #     }
        # """)
        # self.close_btn.clicked.connect(self.close)

        title_layout.addWidget(title_label)
        title_layout.addWidget(self.recording_status)
        title_layout.addStretch()
        title_layout.addWidget(self.minimize_btn)
        #title_layout.addWidget(self.close_btn)
        main_layout.addLayout(title_layout)        # PPT控制按钮区
        ppt_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("开始")
        self.btn_prev = QPushButton("上一页")
        self.btn_next = QPushButton("下一页")
        self.btn_end_presentation = QPushButton("结束演示")

        for btn in [self.btn_start, self.btn_prev, self.btn_next]:
            btn.setFixedHeight(28)
            btn.setStyleSheet("""
                QPushButton {
                    background: #5B5BF6;
                    color: white;
                    border-radius: 8px;
                    font-weight: bold;
                    padding: 0 12px;
                    border: none;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #CFC3F9;
                    color: #23213A;
                }
                QPushButton:pressed {
                    background: #E3E6F5;
                }
            """)
        
        # 红色"结束演示"按钮的独特样式
        self.btn_end_presentation.setFixedHeight(28)
        self.btn_end_presentation.setStyleSheet("""
            QPushButton {
                background: #FF4D4F;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                padding: 0 12px;
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
        ppt_layout.addWidget(self.btn_start)
        ppt_layout.addWidget(self.btn_prev)
        ppt_layout.addWidget(self.btn_next)
        ppt_layout.addWidget(self.btn_end_presentation)
        main_layout.addLayout(ppt_layout)        # 连接PPT控制按钮事件
        
        self.btn_start.clicked.connect(self.toggle_start_functions)  # 统一控制函数

        # 连接上一页和下一页按钮
        self.btn_prev.clicked.connect(self.previous_slide)
        self.btn_next.clicked.connect(self.next_slide)
        
        # 连接结束演示按钮
        self.btn_end_presentation.clicked.connect(self.end_presentation)

        # 录制控制按钮区
        if RECORDING_AVAILABLE:
            record_layout = QHBoxLayout()

            self.btn_record = QPushButton("开始录制")
            self.btn_record.setFixedHeight(28)
            self.btn_record.setStyleSheet("""
                QPushButton {
                    background: #5B5BF6;
                    color: white;
                    border-radius: 8px;
                    font-weight: bold;
                    padding: 0 12px;
                    border: none;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #CFC3F9;
                    color: #23213A;
                }
                QPushButton:pressed {
                    background: #E3E6F5;
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
            main_layout.addLayout(record_layout)        # 文稿展示区（带滚动功能）
        self.script_scroll_area = QScrollArea()
        self.script_scroll_area.setFixedHeight(100)  # 减少高度避免重叠
        self.script_scroll_area.setWidgetResizable(True)
        self.script_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.script_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
          # 文稿内容标签
        self.text_label = QLabel("文稿展示区")
        self.text_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #222;
                background: transparent;
                border-radius: 5px;
                padding: 8px;
                border: none;
            }
        """)        
        self.text_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.text_label.setWordWrap(True)        # 设置合适的高度和尺寸约束
        self.text_label.setFixedHeight(80)  # 减少高度
        self.text_label.setMinimumWidth(300)  # 确保宽度足够
        self.text_label.setMaximumWidth(320)  # 限制最大宽度
        
        # 设置滚动区域样式
        self.script_scroll_area.setStyleSheet("""
            QScrollArea {
                background: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 5px;
            }
            QScrollBar:vertical {
                background: #F0F0F0;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #C0C0C0;
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #A0A0A0;
            }
            QScrollBar::handle:vertical:pressed {
                background: #808080;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
          # 将文稿标签放入滚动区域
        self.script_scroll_area.setWidget(self.text_label)
        main_layout.addWidget(self.script_scroll_area)
          # 添加分隔间距，确保滚动区域和字幕区域不重叠
        main_layout.addSpacing(4)  # 减少间距，确保不会导致溢出

        # AI字幕显示区（语音识别字幕显示）
        self.subtitle_display = SubtitleDisplayWidget()
        main_layout.addWidget(self.subtitle_display)
        
        # 添加弹性空间，确保底部对齐
        main_layout.addStretch(0)
        
        # 设置整体样式
        self.setStyleSheet("""
            PPTFloatingWindow {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 10px;
                border: 1px solid #CCCCCC;
            }
        """)
          # 立即修复初始布局，确保组件不重叠
        self._fix_initial_layout()
        
        # 强制更新布局
        self.updateGeometry()
        self.update()
        
        # 强制重新计算布局
        self.layout().update()
        self.layout().activate()
    
    def _fix_initial_layout(self):
        """修复初始布局，确保组件不重叠"""
        try:
            # 确保文稿标签有正确的初始高度
            self.text_label.setFixedHeight(80)
            
            # 确保滚动区域有正确的高度
            self.script_scroll_area.setFixedHeight(100)
            
            # 确保字幕显示区域有正确的高度和初始文本
            self.subtitle_display.setFixedHeight(78)
            self.subtitle_display.current_label.setText("无字幕")
            
            # print(
            
        except Exception as e:
            print(f"修复初始布局时出错: {e}")

    def _delayed_layout_fix(self):
        """延迟布局修复，在UI完全初始化后执行"""
        try:
            # 强制重新计算所有组件尺寸
            self.text_label.adjustSize()
            self.script_scroll_area.setWidget(self.text_label)
            
            # 确保字幕显示区域正确显示
            self.subtitle_display.setFixedHeight(78)
            self.subtitle_display.current_label.setText("无字幕")
            self.subtitle_display.history_label.setText("")
            
            # 强制重新布局
            self.layout().activate()
            self.layout().update()
            
            # 强制重绘
            self.repaint()
            
            # print(
            
        except Exception as e:
            print(f"修复初始布局时出错: {e}")

    def toggle_start_functions(self):
        """统一控制函数：根据当前运行状态和主窗口复选框状态决定切换功能"""
        # print(
        
        # 标记用户已经点击过开始按钮
        self.has_started_once = True
        
        if not self.main_controller:
            # print(
            return
        
        # 检查当前运行状态
        voice_running = RTVTT.is_voice_recognition_running()
        gesture_running = self.is_gesture_active
        
        # print(
        
        # 如果有任何功能正在运行，先停止所有功能
        if voice_running or gesture_running:
            # print(
            if voice_running:
                self.stop_voice_recognition()
            if gesture_running:
                self.stop_gesture_control()
            
            # 停止演示计时
            if hasattr(self, 'recording_status'):
                self.recording_status.stop_presentation_timing()
            
            # 停止功能后，重新检查状态并更新按钮
            voice_still_running = RTVTT.is_voice_recognition_running()
            gesture_still_running = self.is_gesture_active
            
            # 更新按钮状态
            if not voice_still_running and not gesture_still_running:
                # 如果没有功能在运行，恢复默认状态
                self.btn_start.setText("开始")
                self.btn_start.setStyleSheet("""
                    QPushButton {
                        background: #5B5BF6;
                        color: white;
                        border-radius: 8px;
                        font-weight: bold;
                        padding: 0 12px;
                        border: none;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background: #CFC3F9;
                        color: #23213A;
                    }
                    QPushButton:pressed {
                        background: #E3E6F5;
                    }
                """)
                # print(
            else:
                print("停止功能后仍有功能在运行，可能是状态更新延迟")
            return
        
        # 如果没有功能运行，根据主窗口复选框状态启动相应功能
        # print(
        
        # 尝试获取主窗口实例
        main_window = None
        try:
            # 从应用程序中查找主窗口
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                for widget in app.allWidgets():
                    if hasattr(widget, 'voice_checkbox') and hasattr(widget, 'gesture_checkbox'):
                        main_window = widget
                        break
            
            if not main_window:
                # print(
                self.start_voice_recognition()
                self._update_button_state("voice")
                return
                
        except Exception as e:
            # print(
            self.start_voice_recognition()
            self._update_button_state("voice")
            return
        
        # 检查复选框状态
        voice_enabled = main_window.voice_checkbox.isChecked() if hasattr(main_window, 'voice_checkbox') else False
        gesture_enabled = main_window.gesture_checkbox.isChecked() if hasattr(main_window, 'gesture_checkbox') else False
        
        # print(
        
        # 开始演示计时
        if hasattr(self, 'recording_status'):
            self.recording_status.start_presentation_timing()
        
        # 根据复选框状态启动相应功能
        if voice_enabled and gesture_enabled:
            # print(
            self.start_voice_recognition()
            self.start_gesture_control()
            self._update_button_state("both")
            
        elif voice_enabled:
            # print(
            self.start_voice_recognition()
            self._update_button_state("voice")
            
        elif gesture_enabled:
            # print(
            self.start_gesture_control()
            self._update_button_state("gesture")
            
        else:
            # print(
            self._update_button_state("none")
            # print(
    
    def _update_button_state(self, mode):
        """根据模式更新按钮状态"""
        if mode == "both":
            self.btn_start.setText("停止全部")
            self.btn_start.setStyleSheet("""
                QPushButton {
                    background: #FF4D4F;
                    color: white;
                    border-radius: 8px;
                    font-weight: bold;
                    padding: 0 12px;
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
        elif mode == "voice":
            self.btn_start.setText("停止语音")
            self.btn_start.setStyleSheet("""
                QPushButton {
                    background: #FF4D4F;
                    color: white;
                    border-radius: 8px;
                    font-weight: bold;
                    padding: 0 12px;
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
        elif mode == "gesture":
            self.btn_start.setText("停止手势")
            self.btn_start.setStyleSheet("""
                QPushButton {
                    background: #FF4D4F;
                    color: white;
                    border-radius: 8px;
                    font-weight: bold;
                    padding: 0 12px;
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
        else:  # mode == "none"
            self.btn_start.setText("无功能已启用")
            self._set_disabled_button_style()  
    def start_voice_recognition(self):
        """启动语音识别"""
        # print(
        
        # 检查语音识别功能是否被主窗口启用
        if not getattr(self, 'voice_recognition_enabled', False):
            
            # print(
            return
        
        try:
            if not self.main_controller:
                # print(
                return
            
            # 【新增】清空字幕显示，防止显示旧内容
            if hasattr(self, 'subtitle_display'):
                self.subtitle_display.clear_subtitles()
                # print(
            
            # 使用传递过来的关键词启动语音识别
            keywords = getattr(self, 'voice_keywords', ["下一页"])
            # print(
            
            # 【关键修复】直接设置关键词到语音识别器，然后启动
            import RealTimeVoiceToText as RTVTT
            RTVTT.set_voice_keywords(keywords, "上一页")
            # print(
            
            # 通过主控制器启动语音识别，传递关键词
            self.main_controller.toggle_voice_recognition(True, keywords)
              # 启动语音字幕更新定时器（只有在字幕显示启用时才启动）
            if hasattr(self, 'voice_subtitle_timer'):
                if self.subtitle_display_enabled:
                    self.voice_subtitle_timer.start(500)  # 每500ms更新一次字幕
                else:
                    print("语音字幕更新定时器未启用")
            else:
                print("语音字幕更新定时器未初始化")
            
            # print(
            
        except Exception as e:
            # print(
            import traceback
            traceback.print_exc()
    def stop_voice_recognition(self):
        """停止语音识别"""
        # print(      
        try:
            if not self.main_controller:
                # print(
                return
            
            # 通过主控制器停止语音识别
            # print(
            self.main_controller.toggle_voice_recognition(False, [])
            
            # 停止字幕更新定时器
            if hasattr(self, 'voice_subtitle_timer'):
                self.voice_subtitle_timer.stop()
                # print(
            
            # print(
            
        except Exception as e:
            # print(
            import traceback
            traceback.print_exc()

    def toggle_voice_recognition(self):
        """切换语音识别状态（保持兼容性）"""
        # print(        # 检查语音识别是否在运行
        if not RTVTT.is_voice_recognition_running():
            self.start_voice_recognition()
            # 更新按钮文本（仅在兼容模式下）
            print("语音识别开启✅")
        # 停止语音识别
        else:
            self.stop_voice_recognition()
            # 更新按钮文本（仅在兼容模式下）
            print("语音识别停止❌")

    def set_speech_manager(self, speech_manager):
        """设置演讲稿管理器"""
        self.speech_manager = speech_manager
        if RECORDING_AVAILABLE and self.recording_assistant:
            self.recording_assistant.set_speech_manager(speech_manager) 
    
    def set_main_controller(self, main_controller):
        """设置主控制器引用"""
        self.main_controller = main_controller
    
    def update_slide_info(self, current_slide: int, total_slides: int):
        """更新幻灯片信息"""
        try:
            # 这里可以添加在悬浮窗中显示幻灯片信息的逻辑
            # 目前主要用于内部跟踪
            self.current_slide = current_slide
            self.total_slides = total_slides
            # print(
        except Exception as e:
            print(f"更新悬浮窗幻灯片信息失败: {e}")

    def set_script_text(self, text: str):
        """设置文稿文本（支持滚动显示）"""
        self.text_label.setText(text)
        
        # 根据文本内容调整标签高度，确保能触发滚动
        line_count = text.count('\n') + 1
        # 每行约18像素高度，加上边距
        estimated_height = max(100, line_count * 18 + 40)
        
        # 设置标签的固定高度而不是最小高度，确保滚动正常工作
        self.text_label.setFixedHeight(estimated_height)
        
        # 强制更新滚动区域
        if hasattr(self, 'script_scroll_area'):
            self.script_scroll_area.updateGeometry()
        
        # 滚动到顶部
        if hasattr(self, 'script_scroll_area'):
            self.script_scroll_area.verticalScrollBar().setValue(0)
            # print(
    
    def scroll_to_line(self, line_number: int):
        """滚动到指定行号"""
        if hasattr(self, 'script_scroll_area') and line_number > 0:
            # 估算行高（约18像素）
            line_height = 18
            target_position = (line_number - 1) * line_height
            
            # 获取滚动条的最大值，确保不超出范围
            max_value = self.script_scroll_area.verticalScrollBar().maximum()
            target_position = min(target_position, max_value)
            
            # 滚动到目标位置
            self.script_scroll_area.verticalScrollBar().setValue(target_position)
            # print(
    
    def highlight_script_line(self, line_number: int, text: str):
        """高亮显示匹配的文稿行"""
        try:
            current_text = self.text_label.text()
            lines = current_text.split('\n')
            
            # 查找包含指定行号的行
            for i, line in enumerate(lines):
                if line.startswith(f"{line_number:02d}."):
                    # 高亮该行（使用HTML格式）
                    highlighted_line = f"<span style='background-color: #FFE066; font-weight: bold;'>{line}</span>"
                    lines[i] = highlighted_line
                    break
            
            # 更新文本显示
            highlighted_text = '\n'.join(lines)
            self.text_label.setText(highlighted_text)
            
            # 滚动到该行
            self.scroll_to_line(line_number)
            
            # print(
            
        except Exception as e:
            print(f"高亮显示文稿行时出错: {e}")

    def test_scroll_functionality(self):
        """测试滚动功能（用于调试）"""
        test_text = "📄 测试文稿滚动功能\n" + "=" * 30 + "\n\n"
        for i in range(1, 21):  # 生成20行测试文本
            test_text += f"{i:02d}. 这是第{i}行测试文稿内容，用于验证滚动功能是否正常工作。\n"
        
        self.set_script_text(test_text)
        # print(
    
    def load_imported_script(self):
        """加载导入的文稿并显示（支持滚动显示更多内容）"""
        try:
            import json
            script_file_path = "imported_script.json"
            
            if not os.path.exists(script_file_path):
                self.text_label.setText("📄 文稿展示区\n暂无导入的文稿")
                return False
            
            with open(script_file_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            
            # 显示文稿信息
            title = script_data.get("title", "导入的演讲文稿")
            total_lines = script_data.get("total_lines", 0)
            import_time = script_data.get("import_time", "未知时间")
            lines = script_data.get("lines", [])
            
            # 构建显示文本 - 显示更多内容以利用滚动功能
            display_text = f"📄 {title}\n"
            display_text += f"导入时间: {import_time}\n"
            display_text += f"共 {total_lines} 行\n"
            display_text += "=" * 30 + "\n\n"
            
            # 显示所有文稿内容，让用户可以滚动查看
            for line_data in lines:
                line_text = line_data.get("text", "")
                line_number = line_data.get("line_number", 0)
                # 不再截断文本，显示完整内容
                display_text += f"{line_number:02d}. {line_text}\n"
            
            # 设置文本并调整标签高度以适应内容
            self.text_label.setText(display_text)
            
            # 计算所需高度（每行大约18像素，加上边距）
            total_display_lines = display_text.count('\n') + 1
            estimated_height = max(100, total_display_lines * 18 + 40)
            
            # 设置标签的固定高度而不是最小高度，确保滚动正常工作
            self.text_label.setFixedHeight(estimated_height)
            
            # 强制更新滚动区域
            if hasattr(self, 'script_scroll_area'):
                self.script_scroll_area.updateGeometry()
            
            # print(
            
            # print(
            return True
            
        except Exception as e:
            # print(
            self.text_label.setText("📄 文稿展示区\n文稿加载失败")
            return False

    def toggle_recording(self):
        """切换录制状态"""
        if not RECORDING_AVAILABLE:
            # print(
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
        # print(

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
            # print(
        else:
            print("录制助手启动失败，请检查配置或权限。")

    def stop_recording(self):
        """停止录制"""
        if not RECORDING_AVAILABLE:
            return

        self.recording_assistant.stop_recording()

        self.btn_record.setText("开始录制")
        self.btn_record.setStyleSheet("""
            QPushButton {
                background: #5B5BF6;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                padding: 0 12px;
                border: none;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #CFC3F9;
                color: #23213A;
            }
            QPushButton:pressed {
                background: #E3E6F5;
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
        # print(

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
        # 检查字幕显示是否启用
        if not self.subtitle_display_enabled:
            return
            
        if not self.main_controller or not self.main_controller.voice_recognizer:
            return
        
        try:
            # 获取实时语音文本
            current_text = self.main_controller.voice_recognizer.get_current_text()
            last_complete_sentence = self.main_controller.voice_recognizer.get_last_complete_sentence()
            
            # 详细调试信息输出
            if current_text and current_text.strip():
                #print(f"当前识别文本: {current_text}")
                x=1

            if last_complete_sentence and last_complete_sentence.strip():
                # print(
                
                # 通知主窗口进行文稿匹配（如果有主窗口引用）
                if hasattr(self.main_controller, 'main_window'):
                    try:
                        self.main_controller.main_window.process_complete_sentence(last_complete_sentence)
                    except Exception as e:
                        print(f"处理完成句子时出错: {e}")

            # 优先显示当前正在识别的文本，如果没有则显示最后完成的句子
            display_text = ""
            if current_text and current_text.strip():
                display_text = f"🎤 {current_text}"  # 正在识别的文本加上麦克风图标
                # print(
            elif last_complete_sentence and last_complete_sentence.strip():
                display_text = f"✅ {last_complete_sentence}"  # 完成的句子加上对勾图标
                # print(
            
            if display_text and hasattr(self, 'subtitle_display'):
                self.subtitle_display.update_subtitle(display_text)
                # 发射字幕更新信号到主窗口
                self.subtitle_updated.emit(display_text)
                # print(
            else:
                # 没有字幕内容时的调试信息
                if not current_text and not last_complete_sentence:
                    pass  # 不输出过多的空白信息
                else:
                    print(f"当前识别文本: {current_text}")

        except Exception as e:
            # print(
            import traceback
            traceback.print_exc()

    def show_config_dialog(self):
        """显示配置对话框"""
        if not RECORDING_AVAILABLE:
            # print(
            return

        dialog = RecordingConfigDialog(self, self.recording_config)
        if dialog.exec() == QDialog.Accepted:
            self.recording_config = dialog.get_config()
            # print(

    def previous_slide(self):
        """上一张幻灯片"""
        # print(
        try:
            # 先尝试激活PPT窗口
            self._activate_ppt_window()

            # 直接发送按键，不依赖控制器状态
            import pyautogui as pt
            pt.FAILSAFE = False
            pt.PAUSE = 0.1
            pt.press('left')  # 发送左箭头键（上一页）
            # print(

        except Exception as e:
            # print(
            import traceback
            traceback.print_exc()

    def next_slide(self):
        """下一张幻灯片"""
        # print(
        try:
            # 先尝试激活PPT窗口
            self._activate_ppt_window()

            # 直接发送按键，不依赖控制器状态
            import pyautogui as pt
            pt.FAILSAFE = False
            pt.PAUSE = 0.1
            pt.press('right')  # 发送右箭头键（下一页）
            # print(

        except Exception as e:
            # print(
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
                    # print(
                    return True
                else:
                    print("未找到PowerPoint窗口")

            except ImportError:
                print("未找到win32gui模块，无法激活PPT窗口")

            # 备用方法：使用Alt+Tab切换窗口
            import pyautogui as pt
            import time
            pt.hotkey('alt', 'tab')
            time.sleep(0.2)
            # print(
            return True

        except Exception as e:
            # print(
            return False

    def toggle_gesture_control(self):
        """切换手势控制状态"""
        if not GESTURE_AVAILABLE:
            # print(
            return
        if self.is_gesture_active:
            self.stop_gesture_control()
        else:
            self.start_gesture_control()
            
    def start_gesture_control(self):
        """启动手势控制（仅核心功能）"""
        if not GESTURE_AVAILABLE or self.is_gesture_active:
            return

        # 检查主窗口的手势识别状态
        if self.main_controller and hasattr(self.main_controller, 'gesture_controller'):
            if not getattr(self.main_controller.gesture_controller, 'running', False):
                # print(
                return

        try:
            # 首先检查并设置PPT演示状态
            self._setup_ppt_presentation_state()

            # 启动手势控制线程
            self.gesture_thread = threading.Thread(target=self._run_gesture_control, daemon=True)
            self.is_gesture_active = True
            self.gesture_thread.start()

            # print(

        except Exception as e:
            # print(
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
            # print(
            #print("📢 提示：请确保PPT已在演示模式（按F5进入），然后可以使用手势和按钮控制")

        except Exception as e:
            # print(
            # 即使出错，也允许尝试控制
            if self.gesture_controller:
                self.gesture_controller.ppt_controller.is_presentation_active = True
                
    def stop_gesture_control(self):
        """停止手势控制（仅核心功能）"""
        if not GESTURE_AVAILABLE:
            # print(
            return
            
        if not self.is_gesture_active:
            # print(
            return

        try:
            # print(
            
            # 停止手势控制
            self.is_gesture_active = False
            if self.gesture_controller:
                self.gesture_controller.running = False
                # print(

            # 等待线程结束
            if self.gesture_thread and self.gesture_thread.is_alive():
                #print("⏳ 等待手势控制线程结束...")
                self.gesture_thread.join(timeout=2.0)  # 增加超时时间
                # if self.gesture_thread.is_alive():
                #     #print("⏳ 手势控制线程未能在规定时间内结束")
                # else:
                #     #print("✅ 手势控制线程已结束")

            # 清理线程引用
            self.gesture_thread = None
            # print(

            # print(

        except Exception as e:
            # print(
            # 即使出错，也要确保状态正确
            self.is_gesture_active = False
            if self.gesture_controller:
                self.gesture_controller.running = False

    def _run_gesture_control(self):
        """在后台线程中运行手势控制"""
        try:
            if self.gesture_controller:
                # 重置手势控制器状态
                self.gesture_controller.running = True
                # 运行手势控制（这会阻塞直到停止）
                self.gesture_controller.run()
        except Exception as e:
            print("手势控制运行时出错:", e)
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
        """鼠标按下事件 - 用于拖拽，但要避免干扰滚动区域"""
        if event.button() == Qt.LeftButton:
            # 检查点击位置是否在滚动区域内
            if hasattr(self, 'script_scroll_area'):
                scroll_area_rect = self.script_scroll_area.geometry()
                click_pos = event.position().toPoint()
                
                # 如果点击在滚动区域内，不启动拖拽
                if scroll_area_rect.contains(click_pos):
                    event.ignore()  # 让滚动区域处理这个事件
                    return
            
            # 如果不在滚动区域内，启动拖拽
            self._drag_active = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 用于拖拽"""
        if self._drag_active and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            event.ignore()  # 让子控件处理移动事件

    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 结束拖拽"""
        if self._drag_active:
            self._drag_active = False
            event.accept()
        else:
            event.ignore()  # 让子控件处理释放事件
        
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
        
        # 停止复选框状态检查定时器
        if hasattr(self, 'checkbox_state_timer'):
            self.checkbox_state_timer.stop()
        
        # 停止语音识别
        if self.main_controller and self.main_controller.audio_thread and self.main_controller.audio_thread.is_alive():
            RTVTT.toggle_audio_stream(False)

        # 停止演示计时
        if hasattr(self, 'recording_status'):
            self.recording_status.stop_presentation_timing()

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
        # 重置所有拖拽相关状态
        self._drag_active = False
        self._button_drag_start = False
        self._drag_pos = None
        self._drag_start_pos = None
        
        self._is_minimized = True
        
        # 保存当前尺寸和所有状态信息
        self._normal_size = (self.width(), self.height())
        
        # 保存当前所有控件的状态
        self._saved_widgets = []
        self._saved_layout = self.layout()
        
        # 收集除最小化按钮外的所有子控件
        for child in self.findChildren(QWidget):
            if child != self.minimize_btn:
                self._saved_widgets.append(child)
        
        # 设置为最小化尺寸
        self.setFixedSize(*self._minimized_size)
        
        # 隐藏除了最小化按钮外的所有内容
        for widget in self._saved_widgets:
            widget.hide()
        
        # 更改最小化按钮的样式和文本，使其成为恢复按钮
        self.minimize_btn.setText("展开")
        self.minimize_btn.setFixedSize(70, 30)  # 调整为更合适的小按钮大小
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background: #5B5BF6;
                color: white;
                font-size: 11px;
                border: none;
                border-radius: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7B7BF8;
            }
            QPushButton:pressed {
                background: #3B3BF4;
            }
        """)
        
        # 创建最小化布局
        self._minimized_layout = QVBoxLayout()
        self._minimized_layout.addWidget(self.minimize_btn)
        self._minimized_layout.setContentsMargins(5, 5, 5, 5)
        self._minimized_layout.setAlignment(Qt.AlignCenter)
        
        # 临时移除当前布局并设置新的最小化布局
        if self._saved_layout:
            # 保存布局但不删除它
            temp_widget = QWidget()
            temp_widget.setLayout(self._saved_layout)
            self._saved_layout_widget = temp_widget
        
        self.setLayout(self._minimized_layout)
        
        # 重新连接按钮的点击事件
        try:
            self.minimize_btn.clicked.disconnect()
        except:
            pass
        self.minimize_btn.clicked.connect(self.toggle_minimize)
        
        # 重新设置按钮的事件处理器
        self.minimize_btn.mousePressEvent = self.button_mouse_press_event
        self.minimize_btn.mouseMoveEvent = self.button_mouse_move_event
        self.minimize_btn.mouseReleaseEvent = self.button_mouse_release_event
        
        # print(
        
    def restore_window(self):
        """恢复窗口"""
        # print(
        # 重置所有拖拽相关状态
        self._drag_active = False
        self._button_drag_start = False
        self._drag_pos = None
        self._drag_start_pos = None
        
        self._is_minimized = False
        
        # 恢复原始尺寸
        self.setFixedSize(*self._normal_size)
        
        # 先恢复最小化按钮的原始样式（在清理布局之前）
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
        
        # 重新连接按钮的点击事件
        try:
            self.minimize_btn.clicked.disconnect()
        except:
            pass
        self.minimize_btn.clicked.connect(self.toggle_minimize)
        
        # 恢复按钮的默认事件处理器
        self.minimize_btn.mousePressEvent = lambda e: QPushButton.mousePressEvent(self.minimize_btn, e)
        self.minimize_btn.mouseMoveEvent = lambda e: QPushButton.mouseMoveEvent(self.minimize_btn, e)
        self.minimize_btn.mouseReleaseEvent = lambda e: QPushButton.mouseReleaseEvent(self.minimize_btn, e)
        
        # 在清理布局之前，先将恢复后的按钮添加到原始布局中
        if hasattr(self, '_saved_layout_widget') and self._saved_layout_widget:
            original_layout = self._saved_layout_widget.layout()
            if original_layout:
                # 找到title_layout并将按钮重新添加
                title_layout_item = original_layout.itemAt(0) if original_layout.count() > 0 else None
                if title_layout_item and title_layout_item.layout():
                    title_layout = title_layout_item.layout()
                    
                    # 先从当前布局中移除按钮（避免重复添加）
                    if self.layout():
                        current_layout = self.layout()
                        for i in range(current_layout.count()):
                            item = current_layout.itemAt(i)
                            if item and item.widget() == self.minimize_btn:
                                current_layout.removeWidget(self.minimize_btn)
                                break
                    
                    # 将按钮添加到原始title_layout的末尾
                    title_layout.addWidget(self.minimize_btn)
                    # print(
        
        # 清理当前最小化布局
        if self.layout():
            QWidget().setLayout(self.layout())
        
        # 恢复保存的原始布局
        if hasattr(self, '_saved_layout_widget') and self._saved_layout_widget:
            original_layout = self._saved_layout_widget.layout()
            if original_layout:
                # 从临时widget中取回布局
                self._saved_layout_widget.setLayout(QVBoxLayout())  # 设置一个空布局给临时widget
                self.setLayout(original_layout)  # 将原始布局设置回主窗口
            
            # 清理临时widget
            self._saved_layout_widget.deleteLater()
            self._saved_layout_widget = None
        
        # 显示所有保存的控件
        if hasattr(self, '_saved_widgets'):
            for widget in self._saved_widgets:
                if widget and not widget.isVisible():
                    widget.show()
                    widget.setVisible(True)
            # 清理保存的控件列表
            self._saved_widgets = []
        
        # 确保最小化按钮可见
        self.minimize_btn.show()
        self.minimize_btn.setVisible(True)
        
        # print(
        
        # 强制更新布局和显示
        self.updateGeometry()
        self.update()
        
        # print(

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
                # 在最小化状态下，记录拖拽起始位置
                self._drag_active = False  # 初始状态为未拖动
                self._button_drag_start = True
                
                # 获取当前鼠标的全局位置
                global_pos = event.globalPosition().toPoint()
                
                # 使用更可靠的窗口位置获取方法
                # 优先使用geometry()，如果不可靠则使用保存的位置
                try:
                    current_window_pos = self.pos()
                    # 检查位置是否合理（不应该有异常大的跳跃）
                    if hasattr(self, '_pre_minimize_pos'):
                        distance = (current_window_pos - self._pre_minimize_pos).manhattanLength()
                        if distance > 200:  # 如果距离过大，可能是位置不准确
                            # print(
                            # 使用相对于pre_minimize_pos的合理位置
                            current_window_pos = self._pre_minimize_pos
                except:
                    current_window_pos = self.pos()
                
                # 计算鼠标相对于窗口左上角的偏移量
                self._drag_pos = global_pos - current_window_pos
                self._drag_start_pos = global_pos
                
                # print(
                
                # 验证偏移量是否合理（偏移量不应该超过窗口尺寸太多）
                if abs(self._drag_pos.x()) > 100 or abs(self._drag_pos.y()) > 100:
                    # print(
                    # 使用按钮中心作为默认偏移
                    self._drag_pos = QPoint(35, 15)  # 按钮大小的一半
                
                event.accept()
            else:
                # 正常状态下，按钮不处理拖拽
                QPushButton.mousePressEvent(self.minimize_btn, event)

    def button_mouse_move_event(self, event):
        """按钮的鼠标移动事件"""
        if self._is_minimized and self._button_drag_start and event.buttons() & Qt.LeftButton:
            current_global_pos = event.globalPosition().toPoint()
            move_distance = (current_global_pos - self._drag_start_pos).manhattanLength()
            
            # 如果移动距离超过阈值（8像素），则启用拖动
            if move_distance > 8:
                if not self._drag_active:
                    self._drag_active = True
                    # print(
            
            # 一旦开始拖动，就持续移动窗口，保持鼠标和窗口的相对位置
            if self._drag_active:
                # 计算新的窗口位置：当前鼠标位置 - 初始记录的偏移量
                new_window_pos = current_global_pos - self._drag_pos
                self.move(new_window_pos)
                # # print(
            event.accept()
        else:
            QPushButton.mouseMoveEvent(self.minimize_btn, event)

    def button_mouse_release_event(self, event):
        """按钮的鼠标释放事件"""
        if self._is_minimized and event.button() == Qt.LeftButton:
            if self._drag_active:
                # 拖动结束，不触发点击
                # print(
                self._drag_active = False
                self._button_drag_start = False
                event.accept()
            else:
                # 未拖动，触发按钮点击
                # print(
                self._button_drag_start = False
                self.minimize_btn.click()  # 直接模拟点击
                event.accept()
        else:
            QPushButton.mouseReleaseEvent(self.minimize_btn, event)

    def set_subtitle_display_enabled(self, enabled: bool):
        """设置字幕显示开关"""
        # print(
        self.subtitle_display_enabled = enabled
        
        if enabled:
            # 启用字幕显示
            # print(
            if hasattr(self, 'voice_subtitle_timer'):
                # 检查语音识别是否正在运行
                voice_running = RTVTT.is_voice_recognition_running() if RTVTT else False
                # print(
                
                if voice_running:
                    self.voice_subtitle_timer.start(500)
                    # print(
                # else:
                #     # print(
                #     # print(
            # print(
        else:
            # 禁用字幕显示
            # print(
            if hasattr(self, 'voice_subtitle_timer'):
                self.voice_subtitle_timer.stop()
                # print(
            # 清空字幕显示
            if hasattr(self, 'subtitle_display'):
                self.subtitle_display.clear_subtitles()
                # print(
            # print(

    def set_voice_recognition_enabled(self, enabled: bool):
        """设置语音识别功能可用状态"""
        self.voice_recognition_enabled = enabled
        # print(
        
        # 如果禁用了语音识别功能，停止当前的语音识别
        if not enabled:
            self.stop_voice_recognition()
    
    def set_voice_keywords(self, keywords: list):
        """设置语音识别关键词"""
        self.voice_keywords = keywords
        # print(
    
    def get_voice_recognition_status(self):
        """获取语音识别状态"""
        return {
            'enabled': getattr(self, 'voice_recognition_enabled', False),
            'keywords': getattr(self, 'voice_keywords', []),
            'running': RTVTT.is_voice_recognition_running() if RTVTT else False
        }
    
    def start_state_monitoring(self):
        """启动状态监控"""
        # print(
        # 初始化记录当前复选框状态，但不改变按钮显示
        self.update_last_checkbox_state()
        # 启动定时器
        self.checkbox_state_timer.start(2000)  # 每2秒检查一次
    
    def update_last_checkbox_state(self):
        """更新记录的复选框状态，但不改变按钮显示"""
        try:
            # 获取主窗口实例
            main_window = self.get_main_window()
            if main_window:
                # 获取当前复选框状态并记录
                self.last_voice_enabled = main_window.voice_checkbox.isChecked() if hasattr(main_window, 'voice_checkbox') else False
                self.last_gesture_enabled = main_window.gesture_checkbox.isChecked() if hasattr(main_window, 'gesture_checkbox') else False
                # print(
        except Exception as e:
            print("获取主窗口复选框状态失败:", e)
    
    def get_main_window(self):
        """获取主窗口实例"""
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                for widget in app.allWidgets():
                    if hasattr(widget, 'voice_checkbox') and hasattr(widget, 'gesture_checkbox'):
                        return widget
            return None
        except Exception as e:
            return None

    def check_main_window_checkbox_state(self):
        """检查主窗口复选框状态变化，自动更新悬浮窗按钮"""
        try:
            # 如果有功能正在运行，不需要检查复选框状态
            voice_running = RTVTT.is_voice_recognition_running()
            gesture_running = self.is_gesture_active
            
            if voice_running or gesture_running:
                return  # 有功能在运行时不检查
            
            # 获取主窗口实例
            main_window = self.get_main_window()
            if not main_window:
                return
            
            # 获取当前复选框状态
            current_voice_enabled = main_window.voice_checkbox.isChecked() if hasattr(main_window, 'voice_checkbox') else False
            current_gesture_enabled = main_window.gesture_checkbox.isChecked() if hasattr(main_window, 'gesture_checkbox') else False
            
            # 检查状态是否发生变化
            state_changed = (current_voice_enabled != self.last_voice_enabled or 
                           current_gesture_enabled != self.last_gesture_enabled)
            
            # 只有在用户点击过开始按钮后，才根据复选框状态自动更新按钮
            if state_changed and self.has_started_once:
                # print(
                print(f"   语音识别: {self.last_voice_enabled} → {current_voice_enabled}")
                print(f"   手势识别: {self.last_gesture_enabled} → {current_gesture_enabled}")
                
                # 更新记录的状态
                self.last_voice_enabled = current_voice_enabled
                self.last_gesture_enabled = current_gesture_enabled
                
                # 根据新状态更新按钮显示
                if current_voice_enabled and current_gesture_enabled:
                    # 两个功能都启用
                    self.btn_start.setText("开始")
                    self._set_start_button_style()
                    # print(
                    
                elif current_voice_enabled:
                    # 只启用语音识别
                    self.btn_start.setText("开始")
                    self._set_start_button_style()
                    # print(
                    
                elif current_gesture_enabled:
                    # 只启用手势识别
                    self.btn_start.setText("开始")
                    self._set_start_button_style()
                    # print(
                    
                else:
                    # 没有功能启用
                    self.btn_start.setText("无功能已启用")
                    self._set_disabled_button_style()
                    # print(
            elif state_changed:
                # 只更新记录的状态，不改变按钮显示
                self.last_voice_enabled = current_voice_enabled
                self.last_gesture_enabled = current_gesture_enabled
                    
        except Exception as e:
            # 静默处理错误，避免过多日志输出
            pass
    
    def _set_start_button_style(self):
        """设置开始按钮样式（主题色）"""
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: #5B5BF6;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                padding: 0 12px;
                border: none;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #CFC3F9;
                color: #23213A;
            }
            QPushButton:pressed {
                background: #E3E6F5;
            }
        """)
    
    def _set_disabled_button_style(self):
        """设置禁用状态按钮样式（灰色）"""
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: #8B8BA7;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                padding: 0 12px;
                border: none;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #A6A6A6;
            }
            QPushButton:pressed {
                background: #737373;
            }
        """)

    def end_presentation(self):
        """结束演示 - 完整的演示结束流程"""
        # print(
        
        try:
            # 1. 停止所有活跃的控制功能（语音控制、手势控制）
            # print(
              # 停止语音识别 - 使用完整的停止流程
            # print(
            
            # 首先停止悬浮窗的语音识别功能
            if hasattr(self, 'stop_voice_recognition'):
                self.stop_voice_recognition()
                # print(
            
            # 确保通过主控制器停止语音识别（双重保险）
            if self.main_controller:
                try:
                    # 检查语音识别是否正在运行
                    if RTVTT.is_voice_recognition_running():
                        # print(
                        self.main_controller.toggle_voice_recognition(False, [])
                        # print(
                    # else:
                    #     # print(
                except Exception as e:
                    print("停止语音识别时出错:", e)
            # 最后直接调用RTVTT停止方法（最终保险）
            try:
                if RTVTT.is_voice_recognition_running():
                    # print(
                    RTVTT.stop_real_time_voice_recognition()
                    # print(
            except Exception as e:
                print("停止实时语音识别时出错:", e)

            # print(
            
            # 停止手势控制
            if GESTURE_AVAILABLE and self.is_gesture_active:
                self.stop_gesture_control()
                # print(
            
            # 停止录制（如果正在进行）
            if RECORDING_AVAILABLE and self.recording_assistant and self.recording_assistant.is_recording:
                self.stop_recording()
                # print(
            
            # 停止演示计时
            if hasattr(self, 'recording_status'):
                self.recording_status.stop_presentation_timing()
                # print(
              # 2. 完全关闭PPT应用程序和窗口
            # print(
            if self.main_controller:
                # 使用新的完全关闭PPT功能
                if hasattr(self.main_controller.ppt_controller, 'close_powerpoint_application'):
                    success = self.main_controller.ppt_controller.close_powerpoint_application()
                    # if success:
                    #     # print(
                    # else:
                    #     # print(
                    #     self.main_controller.stop_presentation()
                    #     # print(
                else:
                    # 如果没有新方法，使用原来的方法
                    self.main_controller.stop_presentation()
                    # print(
            
            # 3. 重置主窗口的start_btn状态为"开始播放"
            # print(
            try:
                # 从应用程序中查找主窗口
                from PySide6.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    for widget in app.allWidgets():
                        if hasattr(widget, 'start_btn') and hasattr(widget, 'controller'):
                            # 找到主窗口
                            main_window = widget
                            main_window.start_btn.setText("开始播放")
                            main_window.update_status("演示已结束")
                            # print(
                            break
                    # else:
                    #     # print(
                # else:
                #     # print(
            except Exception as e:
                print("结束演示时出错:", e)

            # 4. 重置悬浮窗状态，确保下次加载时显示"开始"
            # print(
            self.has_started_once = False
            self.btn_start.setText("开始")
            self._set_start_button_style()
            # print(
            
            # 5. 关闭悬浮窗
            # print(
            self.close()
            # print(
            
            # print(
            
        except Exception as e:
            # print(
            traceback.print_exc()
            # 即使出错，也要尝试关闭窗口
            self.close()


class DraggableMinimizedWidget(QWidget):
    """可拖拽的最小化控件"""

    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.setFixedSize(80, 40)
        self.setStyleSheet("""
            QWidget {
                background: rgba(91, 91, 246, 0.9);
                border: 2px solid #5B5BF6;
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
                background: #5B5BF6;
                color: white;
                font-size: 10px;
                border: none;
                border-radius: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7B7BF8;
            }
            QPushButton:pressed {
                background: #3B3BF4;
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
