# -*- coding: utf-8 -*-
"""
测试悬浮窗录制选项功能
Test Floating Window Recording Option
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox, QWidget
from PySide6.QtCore import Qt, QTimer
from ppt_floating_window import PPTFloatingWindow, RecordingConfigDialog
from video_recording_assistant import RecordingConfig

class TestFloatingWindowMask(QWidget):
    def __init__(self):
        super().__init__()
        self.floating_window = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("悬浮窗录制选项测试")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout(self)
        
        # 说明标签
        info_label = QLabel("""
测试步骤：
1. 点击"显示悬浮窗"显示PPT悬浮窗
2. 在悬浮窗中点击配置按钮（⚙️）
3. 取消勾选"录制悬浮窗内容"选项
4. 开始录制并观察输出信息
5. 检查录制的视频中悬浮窗是否被模糊处理
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.show_floating_btn = QPushButton("显示悬浮窗")
        self.show_floating_btn.clicked.connect(self.show_floating_window)
        button_layout.addWidget(self.show_floating_btn)
        
        self.hide_floating_btn = QPushButton("隐藏悬浮窗")
        self.hide_floating_btn.clicked.connect(self.hide_floating_window)
        self.hide_floating_btn.setEnabled(False)
        button_layout.addWidget(self.hide_floating_btn)
        
        self.test_config_btn = QPushButton("测试配置")
        self.test_config_btn.clicked.connect(self.test_config)
        button_layout.addWidget(self.test_config_btn)
        
        layout.addLayout(button_layout)
        
        # 状态显示
        self.status_label = QLabel("等待操作...")
        layout.addWidget(self.status_label)
        
        # 测试结果
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(self.result_label)
        
    def show_floating_window(self):
        """显示悬浮窗"""
        if not self.floating_window:
            self.floating_window = PPTFloatingWindow()
            
        self.floating_window.show()
        self.floating_window.move(200, 200)  # 设置初始位置
        
        self.show_floating_btn.setEnabled(False)
        self.hide_floating_btn.setEnabled(True)
        self.status_label.setText("悬浮窗已显示，请测试录制选项")
        
    def hide_floating_window(self):
        """隐藏悬浮窗"""
        if self.floating_window:
            self.floating_window.hide()
            
        self.show_floating_btn.setEnabled(True)
        self.hide_floating_btn.setEnabled(False)
        self.status_label.setText("悬浮窗已隐藏")
        
    def test_config(self):
        """测试配置功能"""
        if not self.floating_window:
            self.status_label.setText("请先显示悬浮窗")
            return
            
        # 获取当前配置
        config = self.floating_window.recording_config
        if config:
            record_floating = config.record_floating_window
            self.result_label.setText(f"当前配置：录制悬浮窗 = {record_floating}")
            
            # 提示用户测试步骤
            self.status_label.setText("""
请按以下步骤测试：
1. 点击悬浮窗的配置按钮（⚙️）
2. 修改"录制悬浮窗内容"选项
3. 开始录制并观察调试输出
            """)
        else:
            self.result_label.setText("无法获取配置信息")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 检查录制功能是否可用
    try:
        from video_recording_assistant import VideoRecordingAssistant, RecordingConfig
        print("✅ 录制功能模块加载成功")
    except ImportError as e:
        print(f"❌ 录制功能模块加载失败: {e}")
        sys.exit(1)
    
    window = TestFloatingWindowMask()
    window.show()
    
    sys.exit(app.exec())
