#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试悬浮窗布局
"""

import sys
import os
from PySide6.QtWidgets import QApplication

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ppt_floating_window import PPTFloatingWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 创建悬浮窗
    window = PPTFloatingWindow()
    window.show()
    
    print("🪟 悬浮窗已显示，请检查布局是否正常")
    print("📋 文稿展示区和'无字幕'按钮应该不重叠")
    
    sys.exit(app.exec()) 