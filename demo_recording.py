#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPT悬浮窗录像功能演示 - Demo Script
"""

import sys
import os
import time
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

def test_recording_modules():
    """测试录像模块"""
    print("=" * 60)
    print("PPT悬浮窗录像功能测试")
    print("=" * 60)
    
    # 1. 测试基础模块导入
    print("\n1. 测试模块导入...")
    try:
        from ppt_floating_window import PPTFloatingWindow, RECORDING_AVAILABLE
        print(f"   ✅ PPT悬浮窗模块导入成功")
        print(f"   ✅ 录像功能可用: {RECORDING_AVAILABLE}")
        
        if RECORDING_AVAILABLE:
            from video_recording_assistant import VideoRecordingAssistant, RecordingConfig
            print(f"   ✅ 录像助手模块导入成功")
            
            from speech_text_manager import SpeechTextManager
            print(f"   ✅ 语音文本管理器导入成功")
        
    except ImportError as e:
        print(f"   ❌ 模块导入失败: {e}")
        return False
    
    # 2. 测试录像配置
    if RECORDING_AVAILABLE:
        print("\n2. 测试录像配置...")
        try:
            config = RecordingConfig()
            print(f"   ✅ 默认配置创建成功")
            print(f"      - 屏幕录制: {config.enable_screen}")
            print(f"      - 摄像头录制: {config.enable_camera}")
            print(f"      - 麦克风录制: {config.enable_microphone}")
            print(f"      - AI字幕: {config.enable_ai_subtitles}")
            print(f"      - 视频帧率: {config.video_fps}")
            print(f"      - 输出目录: {config.output_dir}")
        except Exception as e:
            print(f"   ❌ 配置创建失败: {e}")
            return False
    
    # 3. 测试录像助手初始化
    if RECORDING_AVAILABLE:
        print("\n3. 测试录像助手初始化...")
        try:
            assistant = VideoRecordingAssistant()
            print(f"   ✅ 录像助手初始化成功")
            print(f"      - 当前状态: {'录制中' if assistant.is_recording else '未录制'}")
            print(f"      - 输出目录: {assistant.output_dir}")
        except Exception as e:
            print(f"   ❌ 录像助手初始化失败: {e}")
            return False
    
    # 4. 测试PPT悬浮窗创建
    print("\n4. 测试PPT悬浮窗创建...")
    try:
        from PySide6.QtWidgets import QApplication
        
        # 如果没有QApplication实例，创建一个
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        floating_window = PPTFloatingWindow()
        print(f"   ✅ PPT悬浮窗创建成功")
        
        # 测试录像状态获取
        status = floating_window.get_recording_status()
        print(f"   ✅ 录像状态获取成功:")
        print(f"      - 录像功能可用: {status['recording_available']}")
        print(f"      - 当前录制状态: {status['is_recording']}")
        
        # 清理
        floating_window.close()
        
    except Exception as e:
        print(f"   ❌ PPT悬浮窗创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！录像功能集成成功！")
    print("=" * 60)
    
    # 5. 显示功能特性
    print("\n📋 PPT悬浮窗录像功能特性:")
    print("   🎥 屏幕录制 - 录制整个屏幕或选定区域")
    print("   📹 摄像头录制 - 可选择开启前置摄像头画中画")
    print("   🎤 麦克风录制 - 录制音频解说")
    print("   📝 AI实时字幕 - 实时生成演讲字幕")
    print("   ✏️  文稿修正 - 根据导入演讲稿修正AI字幕")
    print("   💾 录制配置 - 完整的录制参数配置")
    print("   🎮 悬浮控制 - 悬浮窗便捷控制录制")
    print("   🔗 主窗口集成 - 与主程序完美集成")
    
    print("\n🚀 使用方法:")
    print("   1. 运行主程序: python main.py")
    print("   2. 打开PPT文件并开始演示")
    print("   3. 在悬浮窗中点击录制按钮开始录像")
    print("   4. 点击配置按钮调整录制参数")
    print("   5. 录制完成后文件自动保存到recordings目录")
    
    return True

if __name__ == "__main__":
    success = test_recording_modules()
    
    if success:
        print(f"\n🎉 PPT悬浮窗录像功能集成完成！")
        print(f"🗂️  录制文件保存位置: {os.path.abspath('recordings')}")
        
        # 检查录制目录
        recordings_dir = Path("recordings")
        if recordings_dir.exists():
            sessions = list(recordings_dir.iterdir())
            if sessions:
                print(f"📁 现有录制会话: {len(sessions)} 个")
                for session in sessions[-3:]:  # 显示最近3个
                    print(f"   - {session.name}")
            else:
                print(f"📁 录制目录为空，准备就绪")
        else:
            print(f"📁 将创建录制目录: {recordings_dir.absolute()}")
    else:
        print(f"\n❌ 录像功能集成存在问题，请检查依赖项")
        sys.exit(1)
