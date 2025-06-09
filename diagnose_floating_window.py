# -*- coding: utf-8 -*-
"""
诊断悬浮窗录制选项问题
Diagnose floating window recording option issue
"""

from video_recording_assistant import RecordingConfig

def test_logic():
    """测试录制逻辑"""
    print("=== 悬浮窗录制选项逻辑测试 ===")
    
    # 测试案例1：不录制悬浮窗
    config1 = RecordingConfig()
    config1.record_floating_window = False
    floating_window_exists = True
    
    should_mask = not config1.record_floating_window and floating_window_exists
    print(f"案例1 - 不录制悬浮窗:")
    print(f"  record_floating_window = {config1.record_floating_window}")
    print(f"  floating_window_exists = {floating_window_exists}")
    print(f"  should_mask = {should_mask}")
    print(f"  结果: {'悬浮窗将被遮盖' if should_mask else '悬浮窗将被录制'}")
    print()
    
    # 测试案例2：录制悬浮窗
    config2 = RecordingConfig()
    config2.record_floating_window = True
    
    should_mask = not config2.record_floating_window and floating_window_exists
    print(f"案例2 - 录制悬浮窗:")
    print(f"  record_floating_window = {config2.record_floating_window}")
    print(f"  floating_window_exists = {floating_window_exists}")
    print(f"  should_mask = {should_mask}")
    print(f"  结果: {'悬浮窗将被遮盖' if should_mask else '悬浮窗将被录制'}")
    print()
    
    # 测试案例3：没有悬浮窗
    config3 = RecordingConfig()
    config3.record_floating_window = False
    floating_window_exists = False
    
    should_mask = not config3.record_floating_window and floating_window_exists
    print(f"案例3 - 不录制悬浮窗但没有悬浮窗:")
    print(f"  record_floating_window = {config3.record_floating_window}")
    print(f"  floating_window_exists = {floating_window_exists}")
    print(f"  should_mask = {should_mask}")
    print(f"  结果: {'悬浮窗将被遮盖' if should_mask else '悬浮窗将被录制'}")
    print()

def test_default_config():
    """测试默认配置"""
    print("=== 默认配置测试 ===")
    config = RecordingConfig()
    print(f"默认 record_floating_window = {config.record_floating_window}")
    print("这意味着默认情况下悬浮窗将被遮盖（不录制）")
    print()

if __name__ == "__main__":
    test_logic()
    test_default_config()
    
    print("=== 问题分析 ===")
    print("如果用户报告'无论是否勾选都会录制悬浮窗'，可能的原因：")
    print("1. 配置没有正确传递到VideoRecorder")
    print("2. 悬浮窗对象传递有问题")
    print("3. 坐标计算错误导致遮盖失败")
    print("4. 遮盖效果不明显（只是模糊而非完全隐藏）")
    print()
    print("建议检查：")
    print("- 启用调试信息观察实际配置值")
    print("- 检查悬浮窗坐标是否正确获取")
    print("- 确认遮盖区域是否正确应用")
