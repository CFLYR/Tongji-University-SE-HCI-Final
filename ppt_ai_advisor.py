# -*- coding: utf-8 -*-
"""
PPT AI优化顾问
PPT AI Optimization Advisor

基于星火大模型的PPT内容优化建议系统
"""

import openai
from typing import Dict, List, Optional


class PPTAIAdvisor:
    """PPT AI优化顾问"""
    
    def __init__(self):
        # 星火大模型API配置
        self.api_key = "bqSRpqYFHOtxuGQqrZlq:uVzHvoEQYEqgVuLgchct"
        self.base_url = "https://spark-api-open.xf-yun.com/v1"
        
        # 初始化OpenAI客户端
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # PPT优化提示词模板
        self.optimization_prompt = """你是一位专业的演示文稿优化专家，具有丰富的PPT设计和演讲经验。
请基于以下PPT内容，从以下几个维度提供具体的优化建议：

1. **内容结构**: 分析逻辑结构是否清晰，内容组织是否合理
2. **语言表达**: 评估文字表达是否简洁有力，是否适合演示
3. **视觉设计**: 建议幻灯片的视觉呈现和排版优化
4. **演讲技巧**: 提供演讲时的注意事项和技巧
5. **互动效果**: 建议如何增强与观众的互动

请提供具体、可操作的建议，避免空泛的建议。每个建议都要说明原因和预期效果。

PPT内容如下：
{ppt_content}

请以结构化的方式提供优化建议："""
        
        # 简短建议提示词
        self.quick_advice_prompt = """作为PPT优化专家，请对以下演示文稿提供3-5条最重要的优化建议，每条建议控制在50字以内：

{ppt_content}

请直接列出建议，格式如下：
1. [具体建议]
2. [具体建议]
3. [具体建议]"""

    def get_ppt_optimization_advice(self, ppt_content: str, advice_type: str = "detailed") -> str:
        """
        获取PPT优化建议
        
        Args:
            ppt_content: PPT文本内容
            advice_type: 建议类型 ("detailed" 或 "quick")
            
        Returns:
            AI生成的优化建议
        """
        if not ppt_content or not ppt_content.strip():
            return "请先打开一个PPT文件，然后再请求优化建议。"
        
        try:
            # 选择合适的提示词
            if advice_type == "quick":
                prompt = self.quick_advice_prompt.format(ppt_content=ppt_content)
                max_tokens = 300
            else:
                prompt = self.optimization_prompt.format(ppt_content=ppt_content)
                max_tokens = 800
            
            # 构建消息
            messages = [
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            # 调用API
            response = self.client.chat.completions.create(
                model="lite",  # 使用星火Spark-lite模型
                messages=messages,
                temperature=0.7,  # 适中的创造性
                max_tokens=max_tokens,
            )
            
            # 获取回复内容
            advice = response.choices[0].message.content
            
            return advice
            
        except Exception as e:
            return f"获取AI建议时发生错误：{str(e)}\n\n请检查网络连接或稍后重试。"
    
    def analyze_ppt_structure(self, slides_content: List[Dict]) -> str:
        """
        分析PPT结构并提供建议
        
        Args:
            slides_content: 幻灯片内容列表
            
        Returns:
            结构分析建议
        """
        if not slides_content:
            return "没有可分析的幻灯片内容。"
        
        # 构建结构化的内容描述
        structure_info = f"该PPT共有 {len(slides_content)} 张幻灯片，具体内容如下：\n\n"
        
        for slide in slides_content:
            structure_info += f"第{slide['slide_number']}张: "
            if slide.get('title'):
                structure_info += f"《{slide['title']}》"
            else:
                structure_info += "无标题"
            
            if slide.get('content'):
                content_preview = ' '.join(slide['content'])[:100]
                if len(content_preview) >= 100:
                    content_preview += "..."
                structure_info += f" - {content_preview}"
            
            structure_info += "\n"
        
        # 获取结构优化建议
        structure_prompt = f"""作为演示文稿结构优化专家，请分析以下PPT的结构合理性：

{structure_info}

请从以下角度分析：
1. 幻灯片数量是否合适
2. 内容分布是否均衡
3. 逻辑顺序是否清晰
4. 是否缺少关键环节（开场、总结等）

请提供具体的结构优化建议："""
        
        try:
            messages = [{"role": "user", "content": structure_prompt}]
            
            response = self.client.chat.completions.create(
                model="lite",
                messages=messages,
                temperature=0.6,
                max_tokens=500,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"分析PPT结构时发生错误：{str(e)}"
    
    def get_presentation_tips(self, ppt_content: str) -> str:
        """
        获取演讲技巧建议
        
        Args:
            ppt_content: PPT内容
            
        Returns:
            演讲技巧建议
        """
        tips_prompt = f"""基于以下PPT内容，请提供具体的演讲技巧和注意事项：

{ppt_content[:1000]}...

请从以下方面提供建议：
1. 开场白建议
2. 重点内容的强调方法
3. 与观众互动的时机
4. 结尾总结技巧
5. 常见问题的应对

请提供实用、具体的演讲技巧："""
        
        try:
            messages = [{"role": "user", "content": tips_prompt}]
            
            response = self.client.chat.completions.create(
                model="lite",
                messages=messages,
                temperature=0.8,
                max_tokens=600,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"获取演讲技巧时发生错误：{str(e)}"


def test_ai_advisor():
    """测试AI顾问功能"""
    advisor = PPTAIAdvisor()
    
    # 测试内容
    test_content = """
    === 幻灯片 1 ===
    标题: 项目介绍
    内容:
    - 欢迎大家参加今天的演示
    - 本项目旨在解决PPT演示中的交互问题
    
    === 幻灯片 2 ===
    标题: 技术方案
    内容:
    - 使用手势识别技术
    - 集成语音识别功能
    - 实时字幕显示
    """
    
    print("=== 测试AI优化建议 ===")
    advice = advisor.get_ppt_optimization_advice(test_content, "quick")
    print(advice)
    
    print("\n=== 测试演讲技巧建议 ===")
    tips = advisor.get_presentation_tips(test_content)
    print(tips)


if __name__ == "__main__":
    test_ai_advisor()
