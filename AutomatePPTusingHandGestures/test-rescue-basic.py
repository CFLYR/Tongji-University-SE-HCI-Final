# -*- coding: utf-8 -*-
"""
简化版演讲补救功能测试脚本
"""

import difflib
import re

def calculate_similarity(text1, text2):
    """计算两个文本的相似度"""
    matcher = difflib.SequenceMatcher(None, text1.lower(), text2.lower())
    return matcher.ratio()

def test_basic_functionality():
    """测试基本的文本匹配功能"""
    
    # 预定义的演讲稿
    script_sentences = [
        "大家好，我是李明，今天很高兴能在这里和大家分享我的研究成果。",
        "人工智能技术在近年来得到了快速发展，特别是在自然语言处理领域。",
        "我们的研究团队致力于开发更智能的对话系统，以提升用户体验。",
        "通过深度学习算法，我们实现了更准确的语义理解和情感分析。",
        "这项技术可以广泛应用于客服、教育、医疗等多个领域。"
    ]
    
    # 测试用例
    test_cases = [
        "大家好，我叫王小明，今天来介绍一下我的项目",
        "AI技术发展很快，尤其在图像识别方面", 
        "我们团队在做聊天机器人的研究",
        "深度学习让我们的模型更加精准",
        "这个技术能用在很多地方",
        "完全不相关的内容，比如今天天气很好",
        "人工智能技术在近年来得到了快速发展"
    ]
    
    print("=" * 60)
    print("演讲补救系统基础测试")
    print("=" * 60)
    
    for i, user_input in enumerate(test_cases, 1):
        print(f"\n测试案例 {i}:")
        print(f"用户输入: {user_input}")
        
        # 找到最佳匹配
        best_score = 0
        best_match = ""
        best_index = 0
        
        for j, sentence in enumerate(script_sentences):
            similarity = calculate_similarity(user_input, sentence)
            if similarity > best_score:
                best_score = similarity
                best_match = sentence
                best_index = j
        
        mismatch_rate = 1 - best_score
        needs_rescue = mismatch_rate > 0.4
        
        print(f"最匹配的原稿句子: {best_match}")
        print(f"相似度: {best_score:.2f}")
        print(f"不匹配率: {mismatch_rate:.2f}")
        print(f"是否需要补救: {'是' if needs_rescue else '否'}")
        
        if needs_rescue:
            print("⚠️  警告：检测到演讲内容偏差超过40%！")
            print("建议：调用AI进行补救措施")
        else:
            print("✅ 演讲内容匹配良好，继续进行。")
        
        print("-" * 60)

if __name__ == "__main__":
    try:
        print("开始运行演讲补救系统基础测试...")
        test_basic_functionality()
        print("\n基础测试完成！")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
