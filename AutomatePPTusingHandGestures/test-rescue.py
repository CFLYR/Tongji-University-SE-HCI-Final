# -*- coding: utf-8 -*-
"""
演讲补救功能测试脚本
当检测到用户输入语言与预定文稿不匹配度超过40%时，调用AI进行补救
"""

import openai
import difflib
import re

# OpenAI API配置
OPENAI_API_KEY = "bqSRpqYFHOtxuGQqrZlq:uVzHvoEQYEqgVuLgchct"
client = openai.OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://spark-api-open.xf-yun.com/v1",  # 星火大模型API
)

class SpeechRescueSystem:
    def __init__(self, script_content):
        """
        初始化演讲补救系统
        
        Args:
            script_content (str): 预定的演讲稿内容
        """
        self.script_content = script_content
        self.script_sentences = self.split_into_sentences(script_content)
        self.current_position = 0  # 当前演讲位置
        
    def split_into_sentences(self, text):
        """将文本分割成句子"""
        # 使用正则表达式分割句子，支持中英文标点
        sentences = re.split(r'[。！？.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def calculate_similarity(self, text1, text2):
        """
        计算两个文本的相似度
        
        Args:
            text1 (str): 第一个文本
            text2 (str): 第二个文本
            
        Returns:
            float: 相似度分数 (0-1)
        """
        # 使用difflib计算序列相似度
        matcher = difflib.SequenceMatcher(None, text1.lower(), text2.lower())
        return matcher.ratio()
    
    def find_best_match_position(self, user_input):
        """
        在演讲稿中找到最匹配的位置
        
        Args:
            user_input (str): 用户输入的文本
            
        Returns:
            tuple: (最佳匹配位置索引, 最高相似度)
        """
        best_score = 0
        best_position = 0
        
        for i, sentence in enumerate(self.script_sentences):
            similarity = self.calculate_similarity(user_input, sentence)
            if similarity > best_score:
                best_score = similarity
                best_position = i
                
        return best_position, best_score
    
    def check_speech_accuracy(self, user_input):
        """
        检查用户输入与演讲稿的匹配度
        
        Args:
            user_input (str): 用户输入的文本
            
        Returns:
            dict: 检查结果
        """
        # 找到最佳匹配位置
        best_position, similarity = self.find_best_match_position(user_input)
        
        # 计算不匹配度
        mismatch_rate = 1 - similarity
        
        result = {
            'user_input': user_input,
            'expected_sentence': self.script_sentences[best_position] if best_position < len(self.script_sentences) else "",
            'similarity': similarity,
            'mismatch_rate': mismatch_rate,
            'position': best_position,
            'needs_rescue': mismatch_rate > 0.4  # 40%不匹配阈值
        }
        
        return result
    
    def generate_rescue_content(self, check_result):
        """
        调用AI生成补救内容
        
        Args:
            check_result (dict): 检查结果
            
        Returns:
            str: AI生成的补救内容
        """
        if not check_result['needs_rescue']:
            return "演讲内容匹配良好，无需补救。"
        
        # 获取前一句和后一句作为上下文
        position = check_result['position']
        prev_sentence = self.script_sentences[position - 1] if position > 0 else ""
        current_sentence = check_result['expected_sentence']
        next_sentence = self.script_sentences[position + 1] if position + 1 < len(self.script_sentences) else ""
        
        # 构建提示词
        prompt = f"""
你是一个演讲辅助AI助手。用户在演讲过程中出现了偏差，需要你帮助进行补救。

演讲稿原文上下文：
前一句：{prev_sentence}
当前应该说的句子：{current_sentence}
下一句：{next_sentence}

用户实际说的内容：{check_result['user_input']}

请生成一个自然的补救过渡句，帮助用户从当前说错的内容平滑过渡到演讲稿的正确内容。补救内容应该：
1. 承认或巧妙地处理用户说错的部分
2. 自然地引导到正确的演讲内容
3. 保持演讲的流畅性和逻辑性
4. 语言简洁明了，不超过50字

请直接输出补救过渡句，不需要其他说明：
"""

        try:
            response = client.chat.completions.create(
                model="lite",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            rescue_content = response.choices[0].message.content.strip()
            return rescue_content
            
        except Exception as e:
            return f"AI补救生成失败：{str(e)}"
    
    def process_user_input(self, user_input):
        """
        处理用户输入的完整流程
        
        Args:
            user_input (str): 用户输入的文本
            
        Returns:
            dict: 处理结果
        """
        # 检查语音准确性
        check_result = self.check_speech_accuracy(user_input)
        
        # 如果需要补救，生成补救内容
        rescue_content = ""
        if check_result['needs_rescue']:
            rescue_content = self.generate_rescue_content(check_result)
        
        return {
            'check_result': check_result,
            'rescue_content': rescue_content
        }

def test_speech_rescue():
    """测试演讲补救功能"""
    
    # 预定义的演讲稿
    script = """
    大家好，我是李明，今天很高兴能在这里和大家分享我的研究成果。
    人工智能技术在近年来得到了快速发展，特别是在自然语言处理领域。
    我们的研究团队致力于开发更智能的对话系统，以提升用户体验。
    通过深度学习算法，我们实现了更准确的语义理解和情感分析。
    这项技术可以广泛应用于客服、教育、医疗等多个领域。
    接下来，我将详细介绍我们的技术方案和实验结果。
    感谢大家的聆听，欢迎在后面的环节提出问题和建议。
    """
    
    # 初始化补救系统
    rescue_system = SpeechRescueSystem(script)
    
    # 测试用例
    test_cases = [
        "大家好，我叫王小明，今天来介绍一下我的项目",  # 与第一句相似但有偏差
        "AI技术发展很快，尤其在图像识别方面",  # 与第二句部分匹配
        "我们团队在做聊天机器人的研究",  # 与第三句相关但表达不同
        "深度学习让我们的模型更加精准",  # 与第四句相似
        "这个技术能用在很多地方",  # 与第五句意思相近但简化
        "感谢大家的聆听，欢迎在后面的环节提出问题和建议",  # 完全匹配的内容
        "人工智能技术在近年来得到了快速发展"  # 完全匹配的内容
    ]
    
    print("=" * 60)
    print("演讲补救系统测试")
    print("=" * 60)
    
    for i, user_input in enumerate(test_cases, 1):
        print(f"\n测试案例 {i}:")
        print(f"用户输入: {user_input}")
        
        # 处理用户输入
        result = rescue_system.process_user_input(user_input)
        check_result = result['check_result']
        
        print(f"最匹配的原稿句子: {check_result['expected_sentence']}")
        print(f"相似度: {check_result['similarity']:.2f}")
        print(f"不匹配率: {check_result['mismatch_rate']:.2f}")
        print(f"是否需要补救: {'是' if check_result['needs_rescue'] else '否'}")
        
        if check_result['needs_rescue']:
            print("⚠️  警告：检测到演讲内容偏差！")
            print(f"AI补救建议: {result['rescue_content']}")
        else:
            print("✅ 演讲内容正常，继续进行。")
        
        print("-" * 60)

if __name__ == "__main__":
    try:
        print("开始运行演讲补救系统测试...")
        test_speech_rescue()
        print("测试完成！")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
