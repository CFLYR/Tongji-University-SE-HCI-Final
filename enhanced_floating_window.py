# -*- coding: utf-8 -*-
"""
增强版PPT悬浮窗 - 集成录像功能
Enhanced PPT Floating Window with Recording Features

功能特性:
1. 原有的PPT控制功能
2. 录像功能（屏幕录制）
3. 麦克风录制开关
4. AI实时字幕显示
5. 悬浮窗内容录制选项
6. 字幕录制选项
7. 录制配置菜单
"""

from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QTextEdit, QCheckBox, QSpinBox,
                             QGroupBox, QFormLayout, QComboBox, QSlider, QMenu,
                             QDialog, QDialogButtonBox, QFrame, QScrollArea)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, pyqtSignal
from PySide6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor
import sys
import os
import json
from datetime import datetime
from typing import Optional

# 导入录像相关模块
from video_recording_assistant import VideoRecordingAssistant, RecordingConfig
from speech_text_manager import SpeechTextManager


class RecordingConfigDialog(QDialog):
    """录制配置对话框"""
    
    def __init__(self, parent=None, config: RecordingConfig = None):
        super().__init__(parent)
        self.config = config or RecordingConfig()
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
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
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
        self.screen_checkbox.setChecked(self.config.enable_screen)
        self.camera_checkbox.setChecked(self.config.enable_camera)
        self.microphone_checkbox.setChecked(self.config.enable_microphone)
        self.ai_subtitles_checkbox.setChecked(self.config.enable_ai_subtitles)
        self.script_correction_checkbox.setChecked(self.config.enable_script_correction)
        
        self.fps_spinbox.setValue(self.config.video_fps)
        
        # 摄像头位置映射
        position_map = {
            "bottom_right": 0, "bottom_left": 1, 
            "top_right": 2, "top_left": 3
        }
        self.camera_position_combo.setCurrentIndex(
            position_map.get(self.config.camera_position, 0)
        )
        
        # 摄像头大小映射
        size_map = {
            (240, 180): 0, (320, 240): 1, (480, 360): 2
        }
        self.camera_size_combo.setCurrentIndex(
            size_map.get(self.config.camera_size, 1)
        )
        
        self.output_dir_label.setText(self.config.output_dir)
    
    def get_config(self) -> RecordingConfig:
        """从UI获取配置"""
        config = RecordingConfig()
        
        config.enable_screen = self.screen_checkbox.isChecked()
        config.enable_camera = self.camera_checkbox.isChecked()
        config.enable_microphone = self.microphone_checkbox.isChecked()
        config.enable_ai_subtitles = self.ai_subtitles_checkbox.isChecked()
        config.enable_script_correction = self.script_correction_checkbox.isChecked()
        
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


class SubtitleDisplayWidget(QWidget):
    """字幕显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_subtitle = ""
        self.subtitle_history = []
        self.max_history = 5
        self.setFixedHeight(120)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 当前字幕显示
        self.current_label = QLabel("等待AI字幕...")
        self.current_label.setAlignment(Qt.AlignCenter)
        self.current_label.setWordWrap(True)
        self.current_label.setStyleSheet("""
            QLabel {
                background: rgba(22, 93, 255, 0.1);
                border: 1px solid #165DFF;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
                color: #165DFF;
            }
        """)
        layout.addWidget(self.current_label)
        
        # 历史字幕显示（滚动区域）
        self.history_area = QScrollArea()
        self.history_area.setFixedHeight(60)
        self.history_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.history_widget = QWidget()
        self.history_layout = QHBoxLayout(self.history_widget)
        self.history_layout.setSpacing(5)
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        
        self.history_area.setWidget(self.history_widget)
        self.history_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: #f8f8f8;
            }
        """)
        
        layout.addWidget(self.history_area)
    
    def update_subtitle(self, text: str):
        """更新字幕"""
        if text and text != self.current_subtitle:
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
        self.update_history_display()
    
    def update_history_display(self):
        """更新历史显示"""
        # 清除现有历史标签
        for i in reversed(range(self.history_layout.count())):
            child = self.history_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
        
        # 添加历史标签
        for text in self.subtitle_history[-3:]:  # 只显示最近3条
            label = QLabel(text)
            label.setFixedHeight(20)
            label.setStyleSheet("""
                QLabel {
                    background: #e8e8e8;
                    border-radius: 3px;
                    padding: 2px 6px;
                    font-size: 10px;
                    color: #666;
                }
            """)
            label.setWordWrap(False)
            self.history_layout.addWidget(label)
        
        # 滚动到最右边
        self.history_area.horizontalScrollBar().setValue(
            self.history_area.horizontalScrollBar().maximum()
        )
    
    def clear_subtitles(self):
        """清除所有字幕"""
        self.current_subtitle = ""
        self.subtitle_history = []
        self.current_label.setText("等待AI字幕...")
        self.update_history_display()


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
        layout.setContentsMargins(8, 4, 8, 4)
        
        # 录制状态指示器
        self.status_indicator = QLabel("●")
        self.status_indicator.setFixedSize(12, 12)
        self.status_indicator.setStyleSheet("color: #888; font-size: 16px;")
        
        # 录制时间显示
        self.duration_label = QLabel("00:00:00")
        self.duration_label.setStyleSheet("""
            QLabel {
                font-family: 'Courier New', monospace;
                font-size: 11px;
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
        self.status_indicator.setStyleSheet("color: #ff4444; font-size: 16px;")
        self.timer.start(1000)  # 每秒更新
    
    def stop_recording(self):
        """停止录制"""
        self.is_recording = False
        self.status_indicator.setStyleSheet("color: #888; font-size: 16px;")
        self.timer.stop()
    
    def update_duration(self):
        """更新录制时长"""
        if self.is_recording:
            self.recording_duration += 1
            hours = self.recording_duration // 3600
            minutes = (self.recording_duration % 3600) // 60
            seconds = self.recording_duration % 60
            self.duration_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")


class EnhancedPPTFloatingWindow(QWidget):
    """增强版PPT悬浮窗"""
    
    # 定义信号
    recording_started = Signal()
    recording_stopped = Signal(str)  # 录制文件路径
    subtitle_updated = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        # 窗口属性
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(380, 280)
        
        # 录制相关
        self.recording_assistant = VideoRecordingAssistant()
        self.speech_manager = None
        self.recording_config = RecordingConfig()
        
        # 拖拽相关
        self._drag_active = False
        self._drag_pos = None
        
        self.init_ui()
        self.load_styles()
        
        # 字幕更新定时器
        self.subtitle_timer = QTimer()
        self.subtitle_timer.timeout.connect(self.update_subtitle_display)
    
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
                font-size: 14px;
                font-weight: bold;
                color: #333;
            }
        """)
        
        # 录制状态显示
        self.recording_status = RecordingStatusWidget()
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background: none;
                color: #888;
                font-size: 16px;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                color: #D32F2F;
                background: rgba(211, 47, 47, 0.1);
            }
        """)
        close_btn.clicked.connect(self.close)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.recording_status)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        main_layout.addLayout(title_layout)
        
        # PPT控制按钮区
        ppt_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("开始")
        self.btn_prev = QPushButton("上一页")
        self.btn_next = QPushButton("下一页")
        
        for btn in [self.btn_start, self.btn_prev, self.btn_next]:
            btn.setFixedHeight(32)
            btn.setStyleSheet("""
                QPushButton {
                    background: #165DFF;
                    color: white;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 0 12px;
                    border: none;
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
        
        # 录制控制按钮区
        record_layout = QHBoxLayout()
        
        self.btn_record = QPushButton("开始录制")
        self.btn_record.setFixedHeight(32)
        self.btn_record.setStyleSheet("""
            QPushButton {
                background: #52C41A;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 12px;
                border: none;
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
        self.btn_config.setFixedSize(32, 32)
        self.btn_config.setStyleSheet("""
            QPushButton {
                background: #8C8C8C;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                border: none;
                font-size: 14px;
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
                font-size: 13px;
                color: #222;
                background: #F5F5F5;
                border-radius: 6px;
                padding: 8px;
                border: 1px solid #E0E0E0;
            }
        """)
        self.text_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.text_label.setWordWrap(True)
        self.text_label.setMinimumHeight(60)
        main_layout.addWidget(self.text_label)
        
        # AI字幕显示区
        self.subtitle_display = SubtitleDisplayWidget()
        main_layout.addWidget(self.subtitle_display)
    
    def load_styles(self):
        """加载样式"""
        self.setStyleSheet("""
            EnhancedPPTFloatingWindow {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 12px;
                border: 1px solid #CCCCCC;
            }
        """)
    
    def set_speech_manager(self, speech_manager: SpeechTextManager):
        """设置演讲稿管理器"""
        self.speech_manager = speech_manager
        self.recording_assistant.set_speech_manager(speech_manager)
    
    def set_script_text(self, text: str):
        """设置文稿文本"""
        self.text_label.setText(text)
    
    def toggle_recording(self):
        """切换录制状态"""
        if not self.recording_assistant.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """开始录制"""
        # 更新录制配置
        self.recording_assistant.config = self.recording_config
        
        if self.recording_assistant.start_recording():
            self.btn_record.setText("停止录制")
            self.btn_record.setStyleSheet("""
                QPushButton {
                    background: #FF4D4F;
                    color: white;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 0 12px;
                    border: none;
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
    
    def stop_recording(self):
        """停止录制"""
        self.recording_assistant.stop_recording()
        
        self.btn_record.setText("开始录制")
        self.btn_record.setStyleSheet("""
            QPushButton {
                background: #52C41A;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 12px;
                border: none;
            }
            QPushButton:hover {
                background: #73D13D;
            }
            QPushButton:pressed {
                background: #389E0D;
            }
        """)
        
        self.recording_status.stop_recording()
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
        if self.recording_assistant.is_recording:
            subtitles = self.recording_assistant.get_current_subtitles()
            if subtitles:
                latest_subtitle = subtitles[-1]
                text = (latest_subtitle.corrected_text 
                       if latest_subtitle.is_corrected 
                       else latest_subtitle.text)
                
                self.subtitle_display.update_subtitle(text)
                self.subtitle_updated.emit(text)
    
    def show_config_dialog(self):
        """显示配置对话框"""
        dialog = RecordingConfigDialog(self, self.recording_config)
        if dialog.exec() == QDialog.Accepted:
            self.recording_config = dialog.get_config()
            print("📝 录制配置已更新")
    
    def get_recording_status(self):
        """获取录制状态"""
        return {
            "is_recording": self.recording_assistant.is_recording,
            "session_id": self.recording_assistant.current_session_id,
            "config": self.recording_config.__dict__
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
        if self.recording_assistant.is_recording:
            self.stop_recording()
        
        # 清理字幕显示
        self.subtitle_display.clear_subtitles()
        
        event.accept()


def main():
    """测试主函数"""
    app = QApplication(sys.argv)
    
    # 创建增强版悬浮窗
    window = EnhancedPPTFloatingWindow()
    
    # 连接信号（测试用）
    window.recording_started.connect(lambda: print("录制开始信号"))
    window.recording_stopped.connect(lambda path: print(f"录制停止信号: {path}"))
    window.subtitle_updated.connect(lambda text: print(f"字幕更新: {text}"))
    
    # 设置测试文本
    window.set_script_text("这是一个测试演讲稿。\n您可以看到PPT控制和录像功能都已集成到悬浮窗中。")
    
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
