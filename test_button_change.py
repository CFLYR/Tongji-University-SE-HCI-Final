#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    print("🔍 测试说明:")
    print("1. 点击'打开PPT文件'按钮")
    print("2. 选择一个PPT文件")
    print("3. 观察按钮文本是否变为'正在加载中...'")
    print("4. 加载完成后按钮应该隐藏，显示PPT预览")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 