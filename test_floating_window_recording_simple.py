# -*- coding: utf-8 -*-
"""
简单的悬浮窗录制测试
Simple Floating Window Recording Test
"""

import sys
import time
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt

from ppt_floating_window import PPTFloatingWindow
from video_recording_assistant import RecordingConfig

def test_floating_window_recording():
    """测试悬浮窗录制功能"""
    app = QApplication(sys.argv)
    
    # 创建悬浮窗
    floating_window = PPTFloatingWindow()
    floating_window.show()
    floating_window.move(300, 300)
    
    print("=== 悬浮窗录制测试 ===")
    print("1. 悬浮窗已显示在屏幕上")
    print("2. 点击悬浮窗上的配置按钮（⚙️）")
    print("3. 查看'录制悬浮窗内容'选项")
    print("4. 尝试录制并观察输出")
    
    # 测试配置
    config = floating_window.recording_config
    print(f"\n初始配置:")
    print(f"- record_floating_window: {config.record_floating_window}")
    
    # 手动修改配置进行测试
    print(f"\n测试1: 设置不录制悬浮窗")
    config.record_floating_window = False
    floating_window.recording_config = config
    print(f"- record_floating_window: {config.record_floating_window}")
    print("- 预期结果: 悬浮窗应该被遮盖")
    
    print(f"\n测试2: 设置录制悬浮窗")
    config.record_floating_window = True
    floating_window.recording_config = config
    print(f"- record_floating_window: {config.record_floating_window}")
    print("- 预期结果: 悬浮窗应该正常显示")
    
    print(f"\n请手动测试录制功能...")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_floating_window_recording()
