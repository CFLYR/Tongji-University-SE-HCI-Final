# -*- coding: utf-8 -*-
"""
语音关键词管理窗口
Voice Keyword Manager Window

功能特性:
1. 美观的关键词设置界面
2. 列表显示关键词
3. 新增、编辑、删除关键词
4. 保证至少保留一个关键词
5. 不受Windows主题控制的固定样式
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QListWidget, QListWidgetItem, QLabel, QLineEdit,
                               QWidget, QFrame, QMessageBox, QInputDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
import json
import os


class CustomInputDialog(QDialog):
    """自定义输入对话框，不受Windows主题影响"""
    
    def __init__(self, parent=None, title="输入", label="请输入:", text=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(420, 180)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # 设置与主窗口一致的样式
        self.setStyleSheet("""
            QDialog {
                background-color: #F6F8FB;
                color: #23213A;
                font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif;
                border-radius: 16px;
                border: 2px solid #E3E6F5;
            }
            QLabel {
                color: #23213A;
                font-size: 12px;
                background-color: transparent;
            }
            QLineEdit {
                background-color: #FFFFFF;
                color: #23213A;
                border: 2px solid #E3E6F5;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                selection-background-color: #CFC3F9;
                selection-color: #23213A;
                box-shadow: 0 1px 4px rgba(35,33,58,0.03);
            }
            QLineEdit:focus {
                border-color: #5B5BF6;
            }
            QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 14px;
                min-width: 70px;
                box-shadow: 0 2px 8px rgba(35,33,58,0.06);
            }
            QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
            QPushButton:pressed {
                background-color: #E3E6F5;
            }
            QPushButton#cancelBtn {
                background-color: #E3E6F5;
                color: #8B8BA7;
            }
            QPushButton#cancelBtn:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
        """)
        
        self.init_ui(label, text)
        self.result_text = ""
        
        # 确保窗口尺寸生效
        self.setFixedSize(420, 180)
        self.resize(420, 180)
    
    def init_ui(self, label_text, default_text):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标签
        label = QLabel(label_text)
        layout.addWidget(label)
        
        # 输入框
        self.line_edit = QLineEdit(default_text)
        self.line_edit.setMinimumHeight(40)
        self.line_edit.selectAll()
        layout.addWidget(self.line_edit)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.setFixedSize(75, 32)
        cancel_btn.clicked.connect(self.reject)
        
        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(75, 32)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        layout.addLayout(button_layout)
        
        # 设置焦点
        self.line_edit.setFocus()
        
        # 设置窗口大小策略
        layout.setSizeConstraint(QVBoxLayout.SetFixedSize)
    
    def get_text(self):
        return self.line_edit.text().strip()
    
    @staticmethod
    def getText(parent=None, title="输入", label="请输入:", text=""):
        """静态方法，模仿QInputDialog.getText的接口"""
        dialog = CustomInputDialog(parent, title, label, text)
        if dialog.exec() == QDialog.Accepted:
            return dialog.get_text(), True
        return "", False


class CustomMessageBox:
    """自定义消息框，不受Windows主题影响"""
    
    @staticmethod
    def warning(parent, title, text):
        """显示警告消息"""
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        # 设置无边框窗口
        msg_box.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # 设置与主窗口一致的样式
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #F6F8FB;
                color: #23213A;
                font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif;
                border-radius: 16px;
                border: 2px solid #E3E6F5;
                min-width: 300px;
                min-height: 150px;
            }
            QMessageBox QLabel {
                color: #23213A;
                font-size: 12px;
                background-color: transparent;
                padding: 10px;
            }
            QMessageBox QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 14px;
                min-width: 70px;
                box-shadow: 0 2px 8px rgba(35,33,58,0.06);
            }
            QMessageBox QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
        """)
        
        return msg_box.exec()
    
    @staticmethod
    def question(parent, title, text, buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.No):
        """显示询问消息"""
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(buttons)
        msg_box.setDefaultButton(default_button)
        
        # 设置无边框窗口
        msg_box.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # 强制设置固定尺寸
        msg_box.setFixedSize(380, 200)
        
        # 设置与主窗口一致的样式
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #F6F8FB;
                color: #23213A;
                font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif;
                border-radius: 16px;
                border: 2px solid #E3E6F5;
                min-width: 380px;
                min-height: 200px;
            }
            QMessageBox QLabel {
                color: #23213A;
                font-size: 15px;
                font-weight: 500;
                background-color: transparent;
                text-align: center;
                qproperty-alignment: AlignCenter;
                padding: 30px 25px 25px 25px;
                margin: 10px 5px;
            }
            QMessageBox QLabel#qt_msgbox_label {
                color: #23213A;
                font-size: 15px;
                font-weight: 500;
                background-color: transparent;
                text-align: center;
                qproperty-alignment: AlignCenter;
                padding: 30px 25px 25px 25px;
                margin: 10px 5px;
            }
            QMessageBox .QLabel {
                font-size: 15px;
                padding: 30px 25px 25px 25px;
                margin: 10px 5px;
            }
            QMessageBox QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
                padding: 10px 20px;
                min-width: 85px;
                min-height: 36px;
                margin: 8px 10px;
                box-shadow: 0 2px 8px rgba(35,33,58,0.06);
            }
            QMessageBox QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
            QMessageBox QPushButton[text="Yes"] {
                background-color: #F56565;
                margin-right: 10px;
            }
            QMessageBox QPushButton[text="Yes"]:hover {
                background-color: #E53E3E;
                color: white;
            }
            QMessageBox QPushButton[text="No"] {
                background-color: #E3E6F5;
                color: #8B8BA7;
                margin-left: 10px;
            }
            QMessageBox QPushButton[text="No"]:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
            QMessageBox QDialogButtonBox {
                alignment: center;
                margin: 20px 15px 20px 15px;
            }
        """)
        
        return msg_box.exec()


class KeywordListWidget(QListWidget):
    """自定义的关键词列表控件"""
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                border-radius: 0px;
                padding: 0px;
                font-size: 12px;
                selection-background-color: transparent;
                selection-color: #23213A;
                outline: none;
                margin: 0px;
            }
            QListWidget::item {
                padding: 0px;
                border: none;
                border-radius: 0px;
                margin: 0px;    
                background-color: transparent;
            }
            QListWidget::item:hover {
                background-color: transparent;
                border-color: transparent;
            }
            QListWidget::item:selected {
                background-color: transparent;
                border-color: transparent;
                color: #23213A;
            }
        """)


class KeywordItemWidget(QWidget):
    """关键词列表项控件"""
    
    edit_requested = Signal(str, str)  # 原关键词, 新关键词
    delete_requested = Signal(str)     # 关键词
    
    def __init__(self, keyword):
        super().__init__()
        self.keyword = keyword
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        # 设置整个控件的最小高度和背景色
        self.setMinimumHeight(50)
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid #E3E6F5;
                box-shadow: 0 1px 4px rgba(35,33,58,0.03);
            }
            QWidget:hover {
                border-color: #5B5BF6;
                background-color: #F6F8FB;
            }
        """)
        
        # 关键词文本
        self.keyword_label = QLabel(self.keyword)
        self.keyword_label.setStyleSheet("""
            QLabel {
                color: #23213A;
                font-size: 13px;
                font-weight: 600;
                padding: 6px 10px;
                background-color: transparent;
                border: none;
                min-height: 16px;
            }
        """)
        self.keyword_label.setMinimumWidth(140)
        
        # 编辑按钮
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.setFixedSize(65, 30)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
                min-height: 26px;
                box-shadow: 0 2px 8px rgba(35,33,58,0.06);
            }
            QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
            QPushButton:pressed {
                background-color: #E3E6F5;
            }
        """)
        self.edit_btn.clicked.connect(self.edit_keyword)
        
        # 删除按钮
        self.delete_btn = QPushButton("删除")
        self.delete_btn.setFixedSize(65, 30)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F56565;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
                min-height: 26px;
                box-shadow: 0 2px 8px rgba(35,33,58,0.06);
            }
            QPushButton:hover {
                background-color: #E53E3E;
                color: white;
            }
            QPushButton:pressed {
                background-color: #C53030;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_keyword)
        
        layout.addWidget(self.keyword_label)
        layout.addStretch()
        layout.addWidget(self.edit_btn)
        layout.addWidget(self.delete_btn)
        
    def edit_keyword(self):
        """编辑关键词"""
        text, ok = CustomInputDialog.getText(
            self, 
            "编辑关键词", 
            "请输入新的关键词:",
            self.keyword
        )
        if ok and text.strip():
            self.edit_requested.emit(self.keyword, text.strip())
    
    def delete_keyword(self):
        """删除关键词"""
        self.delete_requested.emit(self.keyword)


class KeywordManagerDialog(QDialog):
    """语音关键词管理对话框"""
    
    keywords_changed = Signal(list)  # 关键词列表改变信号
    
    def __init__(self, parent=None, initial_keywords=None):
        super().__init__(parent)
        self.keywords = initial_keywords or ["下一页"]  # 默认关键词
        self.init_ui()
        self.load_keywords()
        
        # 设置窗口属性
        self.setWindowTitle("语音翻页关键词设置")
        self.setFixedSize(420, 480)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # 应用与主窗口一致的样式
        self.setStyleSheet("""
            QDialog {
                background-color: #F6F8FB;
                color: #23213A;
                font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif;
                border-radius: 16px;
                border: 2px solid #E3E6F5;
            }
        """)
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)
        
        # 标题
        title_label = QLabel("语音翻页关键词管理")
        title_label.setStyleSheet("""
            QLabel {
                color: #23213A;
                font-size: 16px;
                font-weight: bold;
                padding: 6px 0px;
                background-color: transparent;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        
        # 说明文本
        desc_label = QLabel("设置语音识别触发翻页的关键词，至少需要保留一个关键词")
        desc_label.setStyleSheet("""
            QLabel {
                color: #8B8BA7;
                font-size: 11px;
                padding: 6px 12px;
                background-color: transparent;
                border-radius: 0px;
                border: none;
                box-shadow: 0 1px 4px rgba(35,33,58,0.03);
            }
        """)
        desc_label.setWordWrap(True)
        
        # 新增按钮
        self.add_btn = QPushButton("+ 新增关键词")
        self.add_btn.setFixedHeight(38)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 14px;
                box-shadow: 0 2px 8px rgba(35,33,58,0.06);
            }
            QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
            QPushButton:pressed {
                background-color: #E3E6F5;
            }
        """)
        self.add_btn.clicked.connect(self.add_keyword)
        
        # 关键词列表容器
        list_container = QFrame()
        list_container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 2px solid #E3E6F5;
                border-radius: 10px;
                padding: 8px;
                box-shadow: 0 2px 8px rgba(35,33,58,0.06);
            }
        """)
        
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(12, 12, 12, 12)
        
        # 列表标题
        list_title = QLabel("当前关键词列表")
        list_title.setStyleSheet("""
            QLabel {
                color: #23213A;
                font-size: 13px;
                font-weight: bold;
                padding: 6px 0px;
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }
        """)
        
        # 关键词列表
        self.keyword_list = KeywordListWidget()
        self.keyword_list.setMinimumHeight(280)
        
        list_layout.addWidget(list_title)
        list_layout.addWidget(self.keyword_list)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedSize(90, 34)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #E3E6F5;
                color: #8B8BA7;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
                box-shadow: 0 2px 8px rgba(35,33,58,0.06);
            }
            QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
            QPushButton:pressed {
                background-color: #F6F8FB;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.confirm_btn = QPushButton("确定")
        self.confirm_btn.setFixedSize(90, 34)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
                box-shadow: 0 2px 8px rgba(35,33,58,0.06);
            }
            QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
            QPushButton:pressed {
                background-color: #E3E6F5;
            }
        """)
        self.confirm_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.confirm_btn)
        
        # 添加到主布局
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addWidget(self.add_btn)
        layout.addWidget(list_container)
        layout.addLayout(button_layout)
    
    def load_keywords(self):
        """加载关键词到列表"""
        self.keyword_list.clear()
        
        print(f"🔄 加载关键词列表: {self.keywords}")  # 调试信息
        
        for keyword in self.keywords:
            item = QListWidgetItem()
            widget = KeywordItemWidget(keyword)
            widget.edit_requested.connect(self.edit_keyword)
            widget.delete_requested.connect(self.delete_keyword)
            
            # 设置足够的高度来显示按钮
            widget.setMinimumHeight(56)
            item.setSizeHint(widget.sizeHint())
            
            self.keyword_list.addItem(item)
            self.keyword_list.setItemWidget(item, widget)
            
        print(f"✅ 已加载 {len(self.keywords)} 个关键词到列表")
            
    def add_keyword(self):
        """添加新关键词"""
        text, ok = CustomInputDialog.getText(
            self, 
            "新增关键词", 
            "请输入新的关键词:"
        )
        if ok and text.strip():
            keyword = text.strip()
            if keyword not in self.keywords:
                self.keywords.append(keyword)
                self.load_keywords()
                print(f"✅ 成功添加关键词: {keyword}")
            else:
                CustomMessageBox.warning(self, "提示", "该关键词已存在！")

    def edit_keyword(self, old_keyword, new_keyword):
        """编辑关键词"""
        if new_keyword not in self.keywords:
            index = self.keywords.index(old_keyword)
            self.keywords[index] = new_keyword
            self.load_keywords()
            print(f"✅ 成功编辑关键词: {old_keyword} -> {new_keyword}")
        else:
            CustomMessageBox.warning(self, "提示", "该关键词已存在！")
    
    def delete_keyword(self, keyword):
        """删除关键词"""
        if len(self.keywords) <= 1:
            CustomMessageBox.warning(self, "提示", "至少需要保留一个关键词！")
            return
        
        reply = CustomMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除关键词 '{keyword}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.keywords.remove(keyword)
            self.load_keywords()
            print(f"✅ 成功删除关键词: {keyword}")
    
    def get_keywords(self):
        """获取当前关键词列表"""
        return self.keywords.copy()
    
    def accept(self):
        """确定按钮处理"""
        self.keywords_changed.emit(self.keywords)
        super().accept()


def test_keyword_manager():
    """测试关键词管理器"""
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 测试关键词
    initial_keywords = ["下一页", "下一张", "继续", "next"]
    
    dialog = KeywordManagerDialog(initial_keywords=initial_keywords)
    
    def on_keywords_changed(keywords):
        print(f"关键词已更新: {keywords}")
    
    dialog.keywords_changed.connect(on_keywords_changed)
    
    if dialog.exec() == QDialog.Accepted:
        print(f"最终关键词: {dialog.get_keywords()}")
    else:
        print("用户取消了操作")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    test_keyword_manager()
