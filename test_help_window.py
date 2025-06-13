#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试帮助窗口功能
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QVBoxLayout, QPushButton, QWidget, QLabel
from PySide6.QtCore import Qt
from help_window import HelpWindow

class TestHelpWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化测试界面"""
        self.setWindowTitle("测试帮助窗口")
        self.setGeometry(200, 200, 300, 200)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("帮助窗口功能测试")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # 测试按钮
        test_btn = QPushButton("显示帮助窗口")
        test_btn.setFixedHeight(40)
        test_btn.clicked.connect(self.show_help)
        layout.addWidget(test_btn)
        
        # 状态显示
        self.status_label = QLabel("点击按钮测试帮助窗口功能")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("padding: 10px; background: #f0f0f0; border-radius: 5px; margin: 10px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def show_help(self):
        """显示帮助窗口"""
        try:
            help_window = HelpWindow(self)
            help_window.exec()
            self.status_label.setText("✅ 帮助窗口显示成功")
            print("📖 帮助窗口测试成功")
        except Exception as e:
            self.status_label.setText(f"❌ 帮助窗口显示失败: {str(e)}")
            print(f"❌ 帮助窗口测试失败: {e}")

def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyleSheet("""
        QWidget {
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
        }
        QPushButton {
            background: #5B5BF6;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background: #CFC3F9;
            color: #23213A;
        }
        QPushButton:pressed {
            background: #E3E6F5;
        }
    """)
    
    test_window = TestHelpWindow()
    test_window.show()
    
    print("🚀 帮助窗口测试程序已启动")
    print("📋 测试步骤：")
    print("   1. 点击'显示帮助窗口'按钮")
    print("   2. 检查帮助窗口是否正常显示")
    print("   3. 测试各个选项卡的内容")
    print("   4. 测试窗口的关闭功能")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 