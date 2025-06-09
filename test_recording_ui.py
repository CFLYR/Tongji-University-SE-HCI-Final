#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPT悬浮窗录像功能测试
Test PPT Floating Window Recording Features
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QLabel
from PySide6.QtCore import Qt
from ppt_floating_window import PPTFloatingWindow, RECORDING_AVAILABLE

class TestMainWindow(QMainWindow):
    """测试主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PPT悬浮窗录像功能测试")
        self.setGeometry(100, 100, 500, 400)
        
        # 悬浮窗实例
        self.floating_window = None
        
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 状态显示
        self.status_label = QLabel(f"录像功能状态: {'可用' if RECORDING_AVAILABLE else '不可用'}")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(self.status_label)
        
        # 控制按钮
        self.show_floating_btn = QPushButton("显示PPT悬浮窗")
        self.show_floating_btn.clicked.connect(self.show_floating_window)
        layout.addWidget(self.show_floating_btn)
        
        self.hide_floating_btn = QPushButton("隐藏PPT悬浮窗")
        self.hide_floating_btn.clicked.connect(self.hide_floating_window)
        layout.addWidget(self.hide_floating_btn)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        # 初始化日志
        self.add_log("PPT悬浮窗录像功能测试已启动")
        if RECORDING_AVAILABLE:
            self.add_log("✅ 录像功能模块可用")
        else:
            self.add_log("❌ 录像功能模块不可用")
    
    def show_floating_window(self):
        """显示悬浮窗"""
        if self.floating_window is None:
            self.floating_window = PPTFloatingWindow()
            # 连接信号
            self.floating_window.recording_started.connect(self.on_recording_started)
            self.floating_window.recording_stopped.connect(self.on_recording_stopped)
            self.floating_window.subtitle_updated.connect(self.on_subtitle_updated)
        
        self.floating_window.show()
        self.add_log("PPT悬浮窗已显示")
    
    def hide_floating_window(self):
        """隐藏悬浮窗"""
        if self.floating_window:
            self.floating_window.hide()
            self.add_log("PPT悬浮窗已隐藏")
    
    def on_recording_started(self):
        """录像开始"""
        self.add_log("🎥 录像已开始")
        self.status_label.setText("录像状态: 正在录制")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; color: red;")
    
    def on_recording_stopped(self, video_path):
        """录像停止"""
        self.add_log(f"🎬 录像已停止，保存到: {video_path}")
        self.status_label.setText(f"录像功能状态: {'可用' if RECORDING_AVAILABLE else '不可用'}")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; color: black;")
    
    def on_subtitle_updated(self, subtitle_text):
        """字幕更新"""
        self.add_log(f"📝 字幕: {subtitle_text}")
    
    def add_log(self, message):
        """添加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.floating_window:
            self.floating_window.close()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("PPT悬浮窗录像测试")
    app.setApplicationVersion("1.0")
    
    window = TestMainWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
