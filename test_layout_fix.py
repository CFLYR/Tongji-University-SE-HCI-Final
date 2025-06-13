#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试悬浮窗布局修复功能
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ppt_floating_window import PPTFloatingWindow

def test_layout():
    """测试布局修复"""
    app = QApplication(sys.argv)
    
    # 创建悬浮窗
    floating_window = PPTFloatingWindow()
    floating_window.show()
    
    print("🪟 悬浮窗已显示")
    print("📋 请检查初始状态下是否有组件重叠")
    print("⏰ 100ms后将自动修复布局...")
    
    # 3秒后自动退出
    QTimer.singleShot(3000, app.quit)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_layout() 