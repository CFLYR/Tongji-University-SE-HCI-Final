#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试悬浮窗文稿显示功能
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLabel
from PyQt6.QtCore import Qt
from ppt_floating_window import PPTFloatingWindow

class TestScriptDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.floating_window = None
        self.init_ui()
        self.create_test_script()
        
    def init_ui(self):
        """初始化测试界面"""
        self.setWindowTitle("测试悬浮窗文稿显示")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("悬浮窗文稿显示测试")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.show_floating_btn = QPushButton("显示悬浮窗")
        self.show_floating_btn.clicked.connect(self.show_floating_window)
        button_layout.addWidget(self.show_floating_btn)
        
        self.load_script_btn = QPushButton("加载测试文稿")
        self.load_script_btn.clicked.connect(self.load_test_script)
        button_layout.addWidget(self.load_script_btn)
        
        self.test_scroll_btn = QPushButton("测试滚动功能")
        self.test_scroll_btn.clicked.connect(self.test_scroll_function)
        button_layout.addWidget(self.test_scroll_btn)
        
        layout.addLayout(button_layout)
        
        # 状态显示
        self.status_label = QLabel("点击按钮开始测试...")
        self.status_label.setStyleSheet("padding: 10px; background: #f0f0f0; border-radius: 5px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def create_test_script(self):
        """创建测试文稿文件"""
        test_script = {
            "title": "测试演讲文稿",
            "import_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_lines": 15,
            "lines": []
        }
        
        # 生成测试文稿内容
        test_lines = [
            "欢迎大家参加今天的演讲，我是主讲人。",
            "今天我们要讨论的主题是人工智能与课堂互动。",
            "首先，让我们来了解一下人工智能的基本概念。",
            "人工智能是计算机科学的一个分支，致力于创建智能机器。",
            "在教育领域，AI技术正在改变传统的教学方式。",
            "智能教学系统可以根据学生的学习进度调整内容。",
            "语音识别技术让师生互动变得更加自然流畅。",
            "手势识别为课堂演示提供了新的交互方式。",
            "通过数据分析，我们可以更好地了解学习效果。",
            "个性化学习路径帮助每个学生发挥最大潜力。",
            "AI助教可以24小时为学生提供学习支持。",
            "虚拟现实技术让抽象概念变得具体可感。",
            "未来的教育将是人机协作的新模式。",
            "让我们一起拥抱教育技术的美好未来。",
            "感谢大家的聆听，欢迎提问和讨论。"
        ]
        
        for i, line_text in enumerate(test_lines, 1):
            test_script["lines"].append({
                "line_number": i,
                "text": line_text
            })
        
        # 保存到文件
        with open("imported_script.json", 'w', encoding='utf-8') as f:
            json.dump(test_script, f, ensure_ascii=False, indent=2)
        
        print("✅ 测试文稿已创建")
        
    def show_floating_window(self):
        """显示悬浮窗"""
        if not self.floating_window:
            self.floating_window = PPTFloatingWindow()
            
        self.floating_window.show()
        self.status_label.setText("✅ 悬浮窗已显示")
        print("📱 悬浮窗已显示")
        
    def load_test_script(self):
        """加载测试文稿到悬浮窗"""
        if not self.floating_window:
            self.show_floating_window()
            
        # 调用悬浮窗的load_imported_script方法
        if hasattr(self.floating_window, 'load_imported_script'):
            success = self.floating_window.load_imported_script()
            if success:
                self.status_label.setText("✅ 测试文稿已加载到悬浮窗，请检查文稿显示区")
                print("📄 测试文稿已成功加载到悬浮窗")
            else:
                self.status_label.setText("❌ 文稿加载失败")
                print("❌ 文稿加载失败")
        else:
            self.status_label.setText("❌ 悬浮窗不支持load_imported_script方法")
            print("❌ 悬浮窗不支持load_imported_script方法")
            
    def test_scroll_function(self):
        """测试滚动功能"""
        if not self.floating_window:
            self.show_floating_window()
            
        # 先加载文稿
        self.load_test_script()
        
        # 测试滚动到不同位置
        if hasattr(self.floating_window, 'scroll_to_line'):
            # 滚动到第5行
            self.floating_window.scroll_to_line(5)
            self.status_label.setText("✅ 已滚动到第5行，请检查悬浮窗")
            print("📜 已滚动到第5行")
        else:
            self.status_label.setText("❌ 悬浮窗不支持滚动功能")
            print("❌ 悬浮窗不支持滚动功能")

def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyleSheet("""
        QWidget {
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
        }
        QPushButton {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 12px;
        }
        QPushButton:hover {
            background: #45a049;
        }
        QPushButton:pressed {
            background: #3d8b40;
        }
    """)
    
    test_window = TestScriptDisplay()
    test_window.show()
    
    print("🚀 测试程序已启动")
    print("📋 测试步骤：")
    print("   1. 点击'显示悬浮窗'按钮")
    print("   2. 点击'加载测试文稿'按钮")
    print("   3. 检查悬浮窗是否显示完整文稿内容")
    print("   4. 点击'测试滚动功能'按钮")
    print("   5. 检查悬浮窗文稿区域是否可以滚动")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 