#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("开始测试录制模块导入...")

try:
    from video_recording_assistant import VideoRecordingAssistant, RecordingConfig
    print("✅ video_recording_assistant 导入成功")
except ImportError as e:
    print(f"❌ video_recording_assistant 导入失败: {e}")

try:
    from speech_text_manager import SpeechTextManager
    print("✅ speech_text_manager 导入成功")
except ImportError as e:
    print(f"❌ speech_text_manager 导入失败: {e}")

# 测试其他可能缺失的依赖
missing_packages = []

try:
    import mss
    print("✅ mss 模块可用")
except ImportError:
    print("❌ mss 模块缺失")
    missing_packages.append("mss")

try:
    import cv2
    print("✅ opencv-python 模块可用")
except ImportError:
    print("❌ opencv-python 模块缺失")
    missing_packages.append("opencv-python")

try:
    import pyaudio
    print("✅ pyaudio 模块可用")
except ImportError:
    print("❌ pyaudio 模块缺失")
    missing_packages.append("pyaudio")

try:
    import ffmpeg
    print("✅ ffmpeg-python 模块可用")
except ImportError:
    print("❌ ffmpeg-python 模块缺失")
    missing_packages.append("ffmpeg-python")

if missing_packages:
    print(f"\n需要安装的缺失包: {', '.join(missing_packages)}")
    print("请运行以下命令安装:")
    for pkg in missing_packages:
        print(f"  pip install {pkg}")
else:
    print("\n✅ 所有录制相关模块都可用!") 