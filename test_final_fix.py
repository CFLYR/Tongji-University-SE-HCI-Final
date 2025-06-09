#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试脚本 - 验证悬浮窗录制功能修复
"""

import sys
import os
import time
from unittest.mock import Mock

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from video_recording_assistant import RecordingConfig, VideoRecorder

def test_configuration_passing():
    """测试配置传递是否正确"""
    print("🧪 测试配置传递...")
    
    # 创建配置：不录制悬浮窗
    config = RecordingConfig()
    config.record_floating_window = False
    config.mask_mode = "black"
    
    # 创建模拟的悬浮窗对象
    mock_floating_window = Mock()
    mock_floating_window.geometry.return_value = Mock()
    mock_floating_window.geometry().x.return_value = 100
    mock_floating_window.geometry().y.return_value = 50
    mock_floating_window.geometry().width.return_value = 300
    mock_floating_window.geometry().height.return_value = 200
    
    # 创建VideoRecorder
    video_recorder = VideoRecorder(config, mock_floating_window)
    
    print(f"✅ 配置测试结果:")
    print(f"   - 原始配置 record_floating_window: {config.record_floating_window}")
    print(f"   - VideoRecorder配置 record_floating_window: {video_recorder.config.record_floating_window}")
    print(f"   - VideoRecorder悬浮窗对象: {video_recorder.floating_window is not None}")
    print(f"   - mask_mode: {video_recorder.config.mask_mode}")
    
    # 测试遮盖逻辑
    import numpy as np
    import cv2 as cv
    
    # 创建测试帧
    test_frame = np.ones((600, 800, 3), dtype=np.uint8) * 128  # 灰色背景
    
    print(f"\n🧪 测试遮盖逻辑...")
    
    # 测试情况1：不录制悬浮窗
    video_recorder.config.record_floating_window = False
    should_mask = not video_recorder.config.record_floating_window and video_recorder.floating_window
    print(f"   - 不录制悬浮窗时应该遮盖: {should_mask}")
    
    if should_mask:
        masked_frame = video_recorder._mask_floating_window(test_frame.copy())
        # 检查遮盖区域是否变黑
        x, y, w, h = 100, 50, 300, 200
        mask_region = masked_frame[y:y+h, x:x+w]
        is_masked = np.all(mask_region == 0)  # 黑色遮盖
        print(f"   - 遮盖效果检测: {'✅ 成功' if is_masked else '❌ 失败'}")
    
    # 测试情况2：录制悬浮窗
    video_recorder.config.record_floating_window = True
    should_not_mask = not (not video_recorder.config.record_floating_window and video_recorder.floating_window)
    print(f"   - 录制悬浮窗时不应该遮盖: {should_not_mask}")
    
    print(f"\n✅ 配置传递测试完成")

def test_debug_output():
    """测试调试输出"""
    print("\n🧪 测试调试输出...")
    
    config = RecordingConfig()
    config.record_floating_window = False
    
    mock_floating_window = Mock()
    mock_floating_window.geometry.return_value = Mock()
    mock_floating_window.geometry().x.return_value = 100
    mock_floating_window.geometry().y.return_value = 50
    mock_floating_window.geometry().width.return_value = 300
    mock_floating_window.geometry().height.return_value = 200
    
    video_recorder = VideoRecorder(config, mock_floating_window)
    
    # 模拟_capture_frame_threaded中的调试输出
    print(f"🔍 DEBUG 模拟输出:")
    print(f"🔍 DEBUG: record_floating_window = {video_recorder.config.record_floating_window}, floating_window = {video_recorder.floating_window is not None}")
    
    if not video_recorder.config.record_floating_window and video_recorder.floating_window:
        print("🔧 正在遮盖悬浮窗区域...")
    elif video_recorder.config.record_floating_window:
        print("📹 正在录制悬浮窗区域...")
    else:
        print("ℹ️ 无悬浮窗需要处理")

if __name__ == "__main__":
    print("🎯 悬浮窗录制修复最终测试")
    print("=" * 50)
    
    test_configuration_passing()
    test_debug_output()
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！如果看到✅标记说明修复生效")
