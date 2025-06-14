 
"""
PPT内容提取器
PPT Content Extractor

功能特性:
1. 提取PPT文本内容
2. 提取幻灯片标题和内容
3. 支持多种PPT格式
"""

import os
import win32com.client
from typing import List, Dict, Optional
import pythoncom


class PPTContentExtractor:
    """PPT内容提取器"""
    
    def __init__(self):
        self.ppt_app = None
        self.presentation = None
    
    def extract_ppt_content(self, ppt_path: str) -> Dict:
        """
        提取PPT文件的所有文本内容
        
        Args:
            ppt_path: PPT文件路径
            
        Returns:
            包含PPT内容的字典
        """
        if not os.path.exists(ppt_path):
            return {"error": "PPT文件不存在"}
        
        try:
            # 初始化COM
            pythoncom.CoInitialize()
              # 打开PowerPoint应用
            self.ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            # 注意：不能设置 Visible = False，这会导致错误
            # self.ppt_app.Visible = True  # PowerPoint需要可见才能正常工作
            
            # 打开演示文稿
            self.presentation = self.ppt_app.Presentations.Open(ppt_path, ReadOnly=True, WithWindow=False)
            
            # 提取内容
            content = {
                "title": self.presentation.Name,
                "total_slides": self.presentation.Slides.Count,
                "slides": []
            }
            
            # 遍历每一张幻灯片
            for i in range(1, self.presentation.Slides.Count + 1):
                slide = self.presentation.Slides(i)
                slide_content = self._extract_slide_content(slide, i)
                content["slides"].append(slide_content)
            
            # 生成整体内容摘要
            content["full_text"] = self._generate_full_text(content["slides"])
            
            return content
            
        except Exception as e:
            return {"error": f"提取PPT内容失败: {str(e)}"}
        finally:
            self._cleanup()
    
    def _extract_slide_content(self, slide, slide_number: int) -> Dict:
        """
        提取单张幻灯片的内容
        
        Args:
            slide: PowerPoint幻灯片对象
            slide_number: 幻灯片编号
            
        Returns:
            幻灯片内容字典
        """
        slide_content = {
            "slide_number": slide_number,
            "title": "",
            "content": [],
            "text": ""
        }
        
        try:
            # 遍历幻灯片中的所有形状
            for shape in slide.Shapes:
                if shape.HasTextFrame:
                    text_frame = shape.TextFrame
                    if text_frame.HasText:
                        text = text_frame.TextRange.Text.strip()
                        if text:
                            # 判断是否为标题（通常是第一个文本或格式特殊的文本）
                            if not slide_content["title"] and len(text) < 100:
                                slide_content["title"] = text
                            else:
                                slide_content["content"].append(text)
            
            # 合并所有文本
            all_text = []
            if slide_content["title"]:
                all_text.append(slide_content["title"])
            all_text.extend(slide_content["content"])
            slide_content["text"] = "\n".join(all_text)
            
        except Exception as e:
            slide_content["error"] = f"提取幻灯片 {slide_number} 内容失败: {str(e)}"
        
        return slide_content
    
    def _generate_full_text(self, slides: List[Dict]) -> str:
        """
        生成PPT的完整文本内容
        
        Args:
            slides: 幻灯片列表
            
        Returns:
            完整的文本内容
        """
        full_text_parts = []
        
        for slide in slides:
            slide_text = f"=== 幻灯片 {slide['slide_number']} ===\n"
            if slide.get("title"):
                slide_text += f"标题: {slide['title']}\n"
            if slide.get("content"):
                slide_text += "内容:\n"
                for content_item in slide["content"]:
                    slide_text += f"- {content_item}\n"
            slide_text += "\n"
            full_text_parts.append(slide_text)
        
        return "\n".join(full_text_parts)
    def _cleanup(self):
        """清理资源"""
        try:
            if self.presentation:
                self.presentation.Close()
                self.presentation = None
            if self.ppt_app:
                self.ppt_app.Quit()
                self.ppt_app = None
        except:
            pass
        finally:
            try:
                pythoncom.CoUninitialize()
            except:
                pass


def test_ppt_extractor():
    """测试PPT内容提取器"""
    extractor = PPTContentExtractor()
    
    # 查找当前目录下的PPT文件
    ppt_files = [f for f in os.listdir('.') if f.lower().endswith(('.ppt', '.pptx'))]
    
    if ppt_files:
        ppt_path = ppt_files[0]
        print(f"测试提取PPT: {ppt_path}")
        
        content = extractor.extract_ppt_content(ppt_path)
        
        if "error" in content:
            print(f"错误: {content['error']}")
        else:
            print(f"PPT标题: {content['title']}")
            print(f"总幻灯片数: {content['total_slides']}")
            print("\n完整内容:")
            print(content['full_text'])
    else:
        print("当前目录下没有找到PPT文件")


if __name__ == "__main__":
    test_ppt_extractor()
