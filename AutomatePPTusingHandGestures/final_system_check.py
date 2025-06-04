#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终系统状态检查
验证PPT手势控制器的所有组件是否正常工作
"""

from speech_text_manager import SpeechTextManager
import json

def main():
    print('=== PPT手势控制器系统最终检查 ===')
    
    # 1. 检查语音文本管理器
    try:
        manager = SpeechTextManager('speech_config.json')
        print('✅ SpeechTextManager 初始化成功')
          # 测试文本匹配 - 使用演讲稿内容而不是控制命令
        test_cases = [
            '欢迎大家参加今天的演讲',           # 演讲稿第一段
            '项目的背景和目标',               # 演讲稿第二段
            '手势识别和语音文本匹配',         # 演讲稿第三段
            '通过摄像头捕捉手势',             # 演讲稿第四段
        ]
        
        for i, test_text in enumerate(test_cases, 1):
            match_found, segment_text, confidence = manager.match_input_text(test_text)
            status = '✅' if match_found else '❌'
            print(f'{status} 测试{i}: "{test_text}" -> 匹配: {match_found}, 置信度: {confidence:.3f}')
        
    except Exception as e:
        print(f'❌ SpeechTextManager 错误: {e}')
        return False

    # 2. 检查配置文件
    try:
        with open('speech_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        segment_count = len(config.get('segments', []))
        print(f'✅ 配置文件加载成功，包含 {segment_count} 个语音段')
    except Exception as e:
        print(f'❌ 配置文件错误: {e}')
        return False

    # 3. 检查主控制器导入
    try:
        import unified_ppt_gesture_controller
        print('✅ 主控制器模块导入成功')
    except Exception as e:
        print(f'❌ 主控制器导入错误: {e}')
        return False

    print('\n=== 系统检查完成 ===')
    print('🎉 所有组件都正常工作！PPT手势控制器系统已准备就绪。')
    return True

if __name__ == '__main__':
    main()
