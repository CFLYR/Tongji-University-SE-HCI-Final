# -*- coding: utf-8 -*-
"""
演讲稿文本管理器
Speech Text Manager

功能特性:
1. 演讲稿文本加载和管理
2. 基于输入文本的智能匹配
3. 演讲进度跟踪
4. 自动滚动功能
"""

import json
import re
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher
import cv2 as cv
import numpy as np
from chinese_text_renderer import put_text_auto


@dataclass
class SpeechSegment:
    """演讲片段数据结构"""
    index: int          # 片段索引
    text: str          # 片段文本
    slide_number: int  # 对应的幻灯片页码
    keywords: List[str] # 关键词列表
    is_current: bool = False    # 是否为当前片段
    confidence: float = 0.0     # 匹配置信度


class TextMatcher:
    """文本匹配器"""
    
    def __init__(self):
        self.similarity_threshold = 0.25  # 降低阈值，从0.3改为0.25
        
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        # 简单的字符级相似度
        matcher = SequenceMatcher(None, text1.lower(), text2.lower())
        return matcher.ratio()
    
    def calculate_detailed_similarity(self, text1: str, text2: str) -> Tuple[float, float, float]:
        """计算详细的相似度信息，返回(文本相似度, 关键词匹配度, 综合得分)"""
        # 计算文本相似度
        text_similarity = self.calculate_similarity(text1, text2)
        
        # 计算关键词匹配度
        keywords1 = self.extract_keywords(text1)
        keywords2 = self.extract_keywords(text2)
        keywords_similarity = self.keyword_match_score(keywords1, keywords2)
          # 综合得分 (40% 文本相似度 + 60% 关键词匹配度)
        combined_score = 0.4 * text_similarity + 0.6 * keywords_similarity
        
        return text_similarity, keywords_similarity, combined_score
    
    def extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        # 移除标点符号并分词
        clean_text = re.sub(r'[^\w\s]', '', text)
        
        # 改进的中文分词：更智能的关键词提取
        words = []
        # 首先按空格分词
        space_words = clean_text.split()
        for word in space_words:
            if len(word) > 1:
                words.append(word)
                # 对于长词，添加有意义的子串，而不是所有2字组合
                if len(word) >= 4:  # 只对4字及以上的词进行拆分
                    # 添加2字词（更有意义的组合）
                    for i in range(len(word) - 1):
                        if i + 2 <= len(word):
                            substr = word[i:i+2]
                            # 确保是有意义的中文词组
                            if all('\u4e00' <= char <= '\u9fff' for char in substr):
                                # 避免无意义的组合，如 "迎大", "家参" 等
                                if not (i > 0 and i < len(word) - 2):  # 不要中间的字符组合
                                    words.append(substr)
        
        # 过滤掉常见的停用词
        stop_words = {'的', '是', '在', '和', '与', '以及', '但是', '然而', '因此', 
                     '所以', '这个', '那个', '这些', '那些', '我们', '你们', '他们',
                     '一个', '一些', '很多', '非常', '比较', '更加', '可以', '能够',
                     'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        keywords = [word for word in words if len(word) >= 2 and word.lower() not in stop_words]
        # 去重并保持顺序
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:15]  # 返回前15个关键词
    
    def keyword_match_score(self, input_keywords: List[str], target_keywords: List[str]) -> float:
        """计算关键词匹配分数"""
        if not input_keywords or not target_keywords:
            return 0.0
            
        matches = 0
        for keyword in input_keywords:
            for target_keyword in target_keywords:
                # 降低相似度阈值，从0.8改为0.6，提高匹配率
                if self.calculate_similarity(keyword, target_keyword) > 0.6:
                    matches += 1
                    break
        
        return matches / max(len(input_keywords), len(target_keywords))
    
    def find_best_match(self, input_text: str, segments: List[SpeechSegment]) -> Tuple[int, float]:
        """找到最佳匹配的演讲片段"""
        input_keywords = self.extract_keywords(input_text)
        best_index = -1
        best_score = 0.0
        
        for i, segment in enumerate(segments):
            # 计算文本相似度
            text_similarity = self.calculate_similarity(input_text, segment.text)
            
            # 计算关键词匹配度
            keyword_score = self.keyword_match_score(input_keywords, segment.keywords)
            
            # 综合评分 (文本相似度权重0.4，关键词匹配权重0.6)
            combined_score = text_similarity * 0.4 + keyword_score * 0.6
            
            if combined_score > best_score and combined_score > self.similarity_threshold:
                best_score = combined_score
                best_index = i
        
        return best_index, best_score


class SpeechTextManager:
    """演讲稿管理器"""
    
    def __init__(self, config_file: str = "speech_config.json"):
        self.config_file = config_file
        self.segments: List[SpeechSegment] = []
        self.current_index = 0
        self.matcher = TextMatcher()
        self.auto_scroll_enabled = True
        self.display_context_lines = 3  # 显示上下文行数
        
        # 加载演讲稿配置
        self.load_speech_config()
    
    def load_speech_config(self):
        """加载演讲稿配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.load_speech_from_data(data)
                print(f"✅ 演讲稿配置已从 {self.config_file} 加载")
            except Exception as e:
                print(f"❌ 加载演讲稿配置失败: {e}")
                self.create_default_speech()
        else:
            print("📝 未找到演讲稿配置文件，创建默认配置")
            self.create_default_speech()
    
    def create_default_speech(self):
        """创建默认演讲稿"""
        default_data = {
            "title": "演示演讲稿",
            "total_slides": 5,
            "segments": [
                {
                    "text": "欢迎大家参加今天的演讲。我是主讲人，今天将为大家介绍我们的项目成果。",
                    "slide_number": 1,
                    "keywords": ["欢迎", "演讲", "主讲人", "项目", "成果"]
                },
                {
                    "text": "首先让我们看看项目的背景和目标。这个项目旨在解决现有技术的不足。",
                    "slide_number": 2,
                    "keywords": ["背景", "目标", "项目", "技术", "不足"]
                },
                {
                    "text": "接下来介绍我们的技术方案。我们采用了创新的方法来实现这个功能。",
                    "slide_number": 3,
                    "keywords": ["技术", "方案", "创新", "方法", "功能"]
                },
                {
                    "text": "现在展示我们的实验结果。从数据可以看出，我们的方案效果显著。",
                    "slide_number": 4,
                    "keywords": ["实验", "结果", "数据", "方案", "效果"]
                },
                {
                    "text": "总结一下，我们的项目取得了预期的成果。感谢大家的聆听！",
                    "slide_number": 5,
                    "keywords": ["总结", "项目", "成果", "感谢", "聆听"]
                }
            ]
        }
        
        self.load_speech_from_data(default_data)
        self.save_speech_config(default_data)
    
    def load_speech_from_data(self, data: Dict):
        """从数据字典加载演讲稿"""
        self.segments = []
        for i, segment_data in enumerate(data.get("segments", [])):
            segment = SpeechSegment(
                index=i,
                text=segment_data["text"],
                slide_number=segment_data.get("slide_number", i + 1),
                keywords=segment_data.get("keywords", [])
            )
            # 如果没有预定义关键词，自动提取
            if not segment.keywords:
                segment.keywords = self.matcher.extract_keywords(segment.text)
            
            self.segments.append(segment)
          # 设置第一个片段为当前片段
        if self.segments:
            self.segments[0].is_current = True
    
    def save_speech_config(self, data: Dict):
        """保存演讲稿配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ 演讲稿配置已保存到 {self.config_file}")
        except Exception as e:
            print(f"❌ 保存演讲稿配置失败: {e}")
    
    def match_input_text(self, input_text: str) -> tuple:
        """根据输入文本匹配演讲稿位置，返回(匹配成功, 片段文本, 置信度)"""
        if not input_text.strip():
            return False, "", 0.0
        
        print(f"🔍 匹配输入文本: {input_text}")
        
        # 找到最佳匹配
        best_index, confidence = self.matcher.find_best_match(input_text, self.segments)
        
        if best_index >= 0:
            # 更新当前位置
            old_index = self.current_index
            self.current_index = best_index
            
            # 更新当前状态
            for i, segment in enumerate(self.segments):
                segment.is_current = (i == best_index)
                segment.confidence = confidence if i == best_index else 0.0
            
            print(f"✅ 匹配成功! 片段 {best_index + 1}, 置信度: {confidence:.2f}")
            print(f"📍 当前内容: {self.segments[best_index].text[:50]}...")
            
            # 返回匹配结果：找到匹配、片段文本、置信度
            return True, self.segments[best_index].text, confidence
                
        else:
            print(f"❌ 未找到匹配的演讲内容 (输入: {input_text[:30]}...)")
        
        # 返回未匹配结果
        return False, "", 0.0
    
    def get_current_slide_number(self) -> int:
        """获取当前应该显示的幻灯片页码"""
        if 0 <= self.current_index < len(self.segments):
            return self.segments[self.current_index].slide_number
        return 1
    
    def get_progress_info(self) -> Dict:
        """获取演讲进度信息"""
        total_segments = len(self.segments)
        current_segment = self.current_index + 1
        progress_percent = (current_segment / total_segments) * 100 if total_segments > 0 else 0
        
        return {
            "current_segment": current_segment,
            "total_segments": total_segments,
            "progress_percent": progress_percent,
            "current_slide": self.get_current_slide_number(),
            "current_text": self.segments[self.current_index].text if self.segments else "",
            "confidence": self.segments[self.current_index].confidence if self.segments else 0.0
        }
    
    def get_display_segments(self) -> List[SpeechSegment]:
        """获取用于显示的演讲片段（包含上下文）"""
        if not self.segments:
            return []
        
        start = max(0, self.current_index - self.display_context_lines)
        end = min(len(self.segments), self.current_index + self.display_context_lines + 1)
        
        return self.segments[start:end]
    
    def manually_navigate(self, direction: str) -> bool:
        """手动导航演讲稿"""
        old_index = self.current_index
        
        if direction == "next" and self.current_index < len(self.segments) - 1:
            self.current_index += 1
        elif direction == "prev" and self.current_index > 0:
            self.current_index -= 1
        elif direction == "first":
            self.current_index = 0
        elif direction == "last":
            self.current_index = len(self.segments) - 1
        else:
            return False
        
        # 更新当前状态
        for i, segment in enumerate(self.segments):
            segment.is_current = (i == self.current_index)
            segment.confidence = 0.0  # 手动导航时清除置信度
        
        return old_index != self.current_index
    
    def toggle_auto_scroll(self):
        """切换自动滚动状态"""
        self.auto_scroll_enabled = not self.auto_scroll_enabled
        status = "开启" if self.auto_scroll_enabled else "关闭"
        print(f"🔄 自动滚动已{status}")
        return self.auto_scroll_enabled


class SpeechScrollDisplay:
    """演讲稿滚动显示器"""
    
    def __init__(self, speech_manager: SpeechTextManager):
        self.speech_manager = speech_manager
        self.display_window_name = "演讲稿滚动显示"
        self.window_width = 800
        self.window_height = 600
        self.font_size = 24
        self.line_height = 40
        self.margin = 20
        
    def create_display_image(self) -> np.ndarray:
        """创建显示图像"""
        img = np.zeros((self.window_height, self.window_width, 3), dtype=np.uint8)
        img[:] = (40, 40, 40)  # 深灰色背景
        
        # 获取要显示的片段
        segments = self.speech_manager.get_display_segments()
        if not segments:
            return img
        
        y_offset = self.margin
        
        # 显示标题
        progress_info = self.speech_manager.get_progress_info()
        title = f"演讲稿进度: {progress_info['current_segment']}/{progress_info['total_segments']} ({progress_info['progress_percent']:.1f}%)"
        
        img = put_text_auto(img, title, (self.margin, y_offset), 
                          font_size=self.font_size-4, color=(255, 255, 255))
        y_offset += self.line_height
        
        # 显示置信度
        if progress_info['confidence'] > 0:
            confidence_text = f"匹配置信度: {progress_info['confidence']:.2f}"
            img = put_text_auto(img, confidence_text, (self.margin, y_offset), 
                              font_size=self.font_size-6, color=(0, 255, 0))
            y_offset += self.line_height // 2
        
        # 分隔线
        cv.line(img, (self.margin, y_offset), (self.window_width - self.margin, y_offset), 
                (100, 100, 100), 2)
        y_offset += 20
        
        # 显示演讲片段
        for segment in segments:
            if y_offset > self.window_height - self.line_height * 2:
                break
                
            # 片段标题
            title_text = f"片段 {segment.index + 1} (幻灯片 {segment.slide_number})"
            color = (0, 255, 255) if segment.is_current else (150, 150, 150)
            
            img = put_text_auto(img, title_text, (self.margin, y_offset), 
                              font_size=self.font_size-6, color=color)
            y_offset += self.line_height // 2
            
            # 片段内容
            content_color = (255, 255, 255) if segment.is_current else (180, 180, 180)
            font_size = self.font_size if segment.is_current else self.font_size - 2
            
            # 分行显示长文本
            max_chars_per_line = 25
            lines = []
            current_line = ""
            for char in segment.text:
                if len(current_line) >= max_chars_per_line and char in '，。！？；':
                    lines.append(current_line + char)
                    current_line = ""
                else:
                    current_line += char
            if current_line:
                lines.append(current_line)
            
            for line in lines:
                if y_offset > self.window_height - self.line_height:
                    break
                img = put_text_auto(img, line, (self.margin + 20, y_offset), 
                                  font_size=font_size, color=content_color)
                y_offset += self.line_height
            
            y_offset += 10  # 片段间隙
            
        return img
    
    def show_display(self):
        """显示滚动窗口"""
        cv.namedWindow(self.display_window_name, cv.WINDOW_NORMAL)
        cv.resizeWindow(self.display_window_name, self.window_width, self.window_height)
        
        while True:
            img = self.create_display_image()
            cv.imshow(self.display_window_name, img)
            
            key = cv.waitKey(100) & 0xFF
            if key == ord('q') or key == 27:  # 'q' 或 ESC 退出
                break
            elif key == ord('n'):  # 下一个片段
                self.speech_manager.manually_navigate("next")
            elif key == ord('p'):  # 上一个片段
                self.speech_manager.manually_navigate("prev")
            elif key == ord('a'):  # 切换自动滚动
                self.speech_manager.toggle_auto_scroll()
        
        cv.destroyWindow(self.display_window_name)


def test_speech_text_manager():
    """测试演讲稿管理器"""
    print("=== 演讲稿文本管理器测试 ===")
    
    # 创建管理器
    manager = SpeechTextManager()
    
    # 测试文本匹配
    test_inputs = [
        "欢迎大家参加今天的演讲",
        "项目的背景和目标",
        "技术方案和创新方法", 
        "实验结果数据分析",
        "项目总结感谢聆听"
    ]
    
    for input_text in test_inputs:
        print(f"\n测试输入: {input_text}")
        result = manager.match_input_text(input_text)
        progress = manager.get_progress_info()
        print(f"匹配结果: {result}")
        print(f"当前位置: 片段{progress['current_segment']}, 幻灯片{progress['current_slide']}")
        print("---")


if __name__ == "__main__":
    test_speech_text_manager()
