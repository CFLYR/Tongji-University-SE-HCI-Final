"""
中文文本渲染器
用于在OpenCV图像上正确显示中文字符
"""

import cv2 as cv
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os


class ChineseTextRenderer:
    """中文文本渲染器类"""
    
    def __init__(self):
        self.font_path = self._get_chinese_font()
        self.font_cache = {}
        
    def _get_chinese_font(self):
        """获取中文字体路径"""
        # Windows系统中文字体路径
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
            "C:/Windows/Fonts/simhei.ttf",    # 黑体
            "C:/Windows/Fonts/simsun.ttc",    # 宋体
            "C:/Windows/Fonts/simkai.ttf",    # 楷体
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                return font_path
                
        # 如果找不到系统字体，返回None使用默认字体
        return None
    
    def _get_font(self, size):
        """获取指定大小的字体对象"""
        if size not in self.font_cache:
            try:
                if self.font_path:
                    self.font_cache[size] = ImageFont.truetype(self.font_path, size)
                else:
                    # 使用默认字体
                    self.font_cache[size] = ImageFont.load_default()
            except:
                # 如果加载失败，使用默认字体
                self.font_cache[size] = ImageFont.load_default()
        
        return self.font_cache[size]
    
    def put_text(self, img, text, position, font_size=20, color=(255, 255, 255)):
        """
        在图像上绘制中文文本
        
        Args:
            img: OpenCV图像
            text: 要显示的文本
            position: 文本位置 (x, y)
            font_size: 字体大小
            color: 文本颜色 (B, G, R)
        
        Returns:
            修改后的图像
        """
        # 将OpenCV图像转换为PIL图像
        img_pil = Image.fromarray(cv.cvtColor(img, cv.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        # 获取字体
        font = self._get_font(font_size)
        
        # 绘制文本 (PIL使用RGB格式)
        color_rgb = (color[2], color[1], color[0])  # BGR to RGB
        draw.text(position, text, font=font, fill=color_rgb)
        
        # 转换回OpenCV格式
        img_cv = cv.cvtColor(np.array(img_pil), cv.COLOR_RGB2BGR)
        return img_cv


# 全局渲染器实例
_renderer = None

def get_renderer():
    """获取全局渲染器实例"""
    global _renderer
    if _renderer is None:
        _renderer = ChineseTextRenderer()
    return _renderer


def put_chinese_text(img, text, position, font_size=20, color=(255, 255, 255)):
    """
    便捷函数：在图像上绘制中文文本
    
    Args:
        img: OpenCV图像
        text: 要显示的文本
        position: 文本位置 (x, y)
        font_size: 字体大小
        color: 文本颜色 (B, G, R)
    
    Returns:
        修改后的图像
    """
    renderer = get_renderer()
    return renderer.put_text(img, text, position, font_size, color)


def put_text_auto(img, text, position, font_size=20, color=(255, 255, 255)):
    """
    自动选择渲染方式的文本绘制函数
    如果文本包含中文字符，使用中文渲染器；否则使用OpenCV原生方法
    
    Args:
        img: OpenCV图像
        text: 要显示的文本
        position: 文本位置 (x, y)  
        font_size: 字体大小
        color: 文本颜色 (B, G, R)
    
    Returns:
        修改后的图像
    """
    # 检查是否包含中文字符
    def contains_chinese(text):
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False
    
    if contains_chinese(str(text)):
        # 包含中文，使用中文渲染器
        return put_chinese_text(img, str(text), position, font_size, color)
    else:
        # 纯英文/数字，使用OpenCV原生方法
        cv.putText(img, str(text), position, cv.FONT_HERSHEY_SIMPLEX, 
                   font_size/30.0, color, 2)  # 调整字体大小比例
        return img


# 兼容性函数，保持与原代码的兼容性
def render_chinese_text(img, text, position, font_size=20, color=(255, 255, 255)):
    """兼容性函数"""
    return put_chinese_text(img, text, position, font_size, color)