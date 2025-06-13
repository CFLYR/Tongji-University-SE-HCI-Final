#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试悬浮窗滚动功能
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ppt_floating_window import PPTFloatingWindow

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("测试悬浮窗滚动功能")
        self.setGeometry(100, 100, 300, 200)
        
        layout = QVBoxLayout()
        
        # 创建悬浮窗
        self.floating_window = PPTFloatingWindow()
        
        # 测试按钮
        test_btn = QPushButton("测试滚动功能")
        test_btn.clicked.connect(self.test_scroll)
        layout.addWidget(test_btn)
        
        # 显示悬浮窗按钮
        show_btn = QPushButton("显示悬浮窗")
        show_btn.clicked.connect(self.show_floating_window)
        layout.addWidget(show_btn)
        
        # 滚动到第10行按钮
        scroll_btn = QPushButton("滚动到第10行")
        scroll_btn.clicked.connect(self.scroll_to_line_10)
        layout.addWidget(scroll_btn)
        
        # 测试长文本按钮
        long_text_btn = QPushButton("测试长文本")
        long_text_btn.clicked.connect(self.test_long_text)
        layout.addWidget(long_text_btn)
        
        # 重置文本按钮
        reset_btn = QPushButton("重置文本")
        reset_btn.clicked.connect(self.reset_text)
        layout.addWidget(reset_btn)
        
        # 测试初始布局按钮
        layout_btn = QPushButton("修复布局")
        layout_btn.clicked.connect(self.fix_layout)
        layout.addWidget(layout_btn)
        
        self.setLayout(layout)
    
    def test_scroll(self):
        """测试滚动功能"""
        self.floating_window.test_scroll_functionality()
    
    def show_floating_window(self):
        """显示悬浮窗"""
        self.floating_window.show()
        self.floating_window.raise_()
    
    def scroll_to_line_10(self):
        """滚动到第10行"""
        self.floating_window.scroll_to_line(10)
    
    def test_long_text(self):
        """测试长文本滚动"""
        long_text = "📄 长文本滚动测试\n" + "=" * 50 + "\n\n"
        for i in range(1, 51):  # 生成50行测试文本
            long_text += f"{i:02d}. 这是第{i}行长文本内容，用于测试滚动功能是否能正确处理大量文本内容。这行文本比较长，可以测试自动换行功能。\n"
        
        self.floating_window.set_script_text(long_text)
        print("📜 长文本已加载，请测试滚动功能")
    
    def reset_text(self):
        """重置为默认文本"""
        self.floating_window.set_script_text("📄 文稿展示区\n请导入演讲文稿或点击测试按钮")
    
    def fix_layout(self):
        """手动修复布局"""
        if hasattr(self.floating_window, '_fix_initial_layout'):
            self.floating_window._fix_initial_layout()
        print("🔧 手动修复布局完成")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec()) 