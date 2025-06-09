#!/usr/bin/env python3
"""
测试悬浮窗录制功能的脚本
Test script for floating window recording functionality
"""
import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from video_recording_assistant import RecordingConfig, VideoRecordingAssistant
from ppt_floating_window import PPTFloatingWindow

def test_floating_window_recording():
    """测试悬浮窗录制功能"""
    app = QApplication(sys.argv)
    
    # 创建悬浮窗
    floating_window = PPTFloatingWindow()
    floating_window.show()
    
    # 创建录制配置（禁用悬浮窗录制）
    config = RecordingConfig()
    config.record_floating_window = False  # 关键：不录制悬浮窗
    config.output_path = "test_recording_no_floating_window.mp4"
    config.fps = 10  # 降低帧率以便测试
    config.duration = 5  # 录制5秒
    
    # 创建录制助手
    recording_assistant = VideoRecordingAssistant()
    recording_assistant.config = config
    
    print("开始测试录制（不包含悬浮窗）...")
    print(f"悬浮窗位置: {floating_window.geometry()}")
    print(f"录制配置 - record_floating_window: {config.record_floating_window}")
    
    # 启动录制（传递悬浮窗对象）
    success = recording_assistant.start_recording(floating_window=floating_window)
    
    if success:
        print("录制已启动，5秒后自动停止...")
        
        # 使用QTimer延迟停止录制
        def stop_recording():
            recording_assistant.stop_recording()
            print("录制已停止")
            print(f"输出文件: {config.output_path}")
            app.quit()
        
        timer = QTimer()
        timer.singleShot(5000, stop_recording)  # 5秒后停止录制
        
        app.exec()
    else:
        print("录制启动失败")
        app.quit()

if __name__ == "__main__":
    test_floating_window_recording()
