 
"""
文稿管理器 - 负责处理演讲文稿的导入、显示和关键词管理
Script Manager - Handles script import, display and keyword management
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QScrollArea, QWidget, QFrame, QTextEdit,
                               QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, Signal, QDateTime
from PySide6.QtGui import QFont
import os
import json


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
                min-width: 320px;
                min-height: 160px;
            }
            QMessageBox QLabel {
                color: #23213A;
                font-size: 14px;
                font-weight: 500;
                background-color: transparent;
                text-align: center;
                qproperty-alignment: AlignCenter;
                padding: 15px 20px 10px 20px;
                margin: 5px 0px;
            }
            QMessageBox QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
                padding: 8px 20px;
                min-width: 80px;
                min-height: 32px;
                margin: 5px;
                box-shadow: 0 2px 8px rgba(35,33,58,0.06);
            }
            QMessageBox QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
        """)
        
        return msg_box.exec()
    
    @staticmethod
    def information(parent, title, text):
        """显示信息消息"""
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Information)
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
                min-width: 320px;
                min-height: 160px;
            }
            QMessageBox QLabel {
                color: #23213A;
                font-size: 14px;
                font-weight: 500;
                background-color: transparent;
                text-align: center;
                qproperty-alignment: AlignCenter;
                padding: 15px 20px 10px 20px;
                margin: 5px 0px;
            }
            QMessageBox QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
                padding: 8px 20px;
                min-width: 80px;
                min-height: 32px;
                margin: 5px;
                box-shadow: 0 2px 8px rgba(35,33,58,0.06);
            }
            QMessageBox QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
        """)
        
        return msg_box.exec()


class ScriptLineWidget(QWidget):
    """单行文稿显示组件"""
    line_selected = Signal(str)  # 发射选中的文本行
    
    def __init__(self, line_number, text, parent=None):
        super().__init__(parent)
        self.line_number = line_number
        self.text = text.strip()
        self.is_added = False  # 是否已添加到关键词序列
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)
        
        # 行号标签
        self.line_label = QLabel(f"{self.line_number:02d}")
        self.line_label.setStyleSheet("""
            QLabel {
                background-color: #E8F4FD;
                color: #1976D2;
                border-radius: 12px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 11px;
                min-width: 24px;
            }
        """)
        self.line_label.setAlignment(Qt.AlignCenter)
        self.line_label.setFixedSize(40, 24)
        
        # 文本内容标签
        self.content_label = QLabel(self.text)
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 13px;
                padding: 4px;
                background-color: transparent;
            }
        """)
        
        # 添加按钮
        self.add_btn = QPushButton("添加")
        self.add_btn.setFixedSize(60, 28)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color:#332E4D;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5A5187;
            }
            QPushButton:pressed {
                background-color:  #EADFED;
            }
            QPushButton:disabled {
                background-color:  #EADFED;
                color: #999;
            }
        """)
        self.add_btn.clicked.connect(self.on_add_clicked)
        
        layout.addWidget(self.line_label)
        layout.addWidget(self.content_label, 1)
        layout.addWidget(self.add_btn)
        
        # 设置整体样式
        self.setStyleSheet("""
            ScriptLineWidget {
                background-color: white;
                border: 1px solid #E8E8E8;
                border-radius: 6px;
                margin: 2px;
            }
            ScriptLineWidget:hover {
                border-color: #1890FF;
                background-color: #F0F9FF;
            }
        """)
    
    def on_add_clicked(self):
        """添加按钮点击事件"""
        if not self.is_added:
            self.mark_as_added()
            self.line_selected.emit(self.text)
    
    def mark_as_added(self):
        """标记为已添加"""
        self.is_added = True
        self.add_btn.setText("已添加")
        self.add_btn.setEnabled(False)
        self.setStyleSheet("""
            ScriptLineWidget {
                background-color: #F6FFED;
                border: 1px solid #B7EB8F;
                border-radius: 6px;
                margin: 2px;
            }
        """)
        self.line_label.setStyleSheet("""
            QLabel {
                background-color: #E0E0E0;
                color: #424242;
                border-radius: 12px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 11px;
                min-width: 24px;
            }
        """)
    
    def can_add(self):
        """检查是否可以添加"""
        return not self.is_added and len(self.text.strip()) > 0


class ScriptImportDialog(QDialog):
    """文稿导入对话框"""
    keywords_updated = Signal(list)  # 发射更新后的关键词列表
    
    def __init__(self, parent=None, current_keywords=None):
        super().__init__(parent)
        self.current_keywords = current_keywords or []
        self.script_lines = []  # 存储文稿行
        self.init_ui()
        self.setWindowTitle("演讲文稿导入")
        self.setFixedSize(800, 600)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # 设置与主窗口一致的背景样式，添加无边框圆角
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
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题区域
        title_layout = QHBoxLayout()
        title_label = QLabel("📄 演讲文稿导入")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #23213A;
                padding: 8px 0;
                background-color: transparent;
            }
        """)
        
        # 导入按钮
        self.import_btn = QPushButton("📁 选择文稿文件")
        self.import_btn.setFixedSize(120, 36)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 12px;
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
        self.import_btn.clicked.connect(self.import_script_file)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.import_btn)
        layout.addLayout(title_layout)
        
        # 说明文本
        info_label = QLabel("选择.txt格式的演讲文稿文件，每行内容将作为一个可选的关键词项目显示。")
        info_label.setStyleSheet("""
            QLabel {
                color: #8B8BA7;
                font-size: 12px;
                padding: 8px 16px;
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E3E6F5;
                border-left: 3px solid #5B5BF6;
                box-shadow: 0 1px 4px rgba(35,33,58,0.03);
            }
        """)
        layout.addWidget(info_label)
        
        # 文稿显示区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid #E3E6F5;
                border-radius: 12px;
                background-color: #FFFFFF;
                box-shadow: 0 2px 8px rgba(35,33,58,0.06);
            }
        """)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(6)
        
        # 默认提示
        self.empty_label = QLabel("请选择一个文稿文件开始导入...")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("""
            QLabel {
                color: #8B8BA7;
                font-size: 14px;
                padding: 40px;
                background-color: transparent;
            }
        """)
        self.content_layout.addWidget(self.empty_label)
        
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)
        
        # 状态信息
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #8B8BA7;
                font-size: 11px;
                padding: 4px 8px;
                background-color: transparent;
            }
        """)
        layout.addWidget(self.status_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 应用按钮
        self.apply_btn = QPushButton("应用更改")
        self.apply_btn.setFixedSize(100, 36)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 12px;
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
        self.apply_btn.clicked.connect(self.apply_changes)
        
        # 关闭按钮
        self.close_btn = QPushButton("关闭")
        self.close_btn.setFixedSize(80, 36)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #E3E6F5;
                color: #8B8BA7;
                border: none;
                border-radius: 12px;
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
        self.close_btn.clicked.connect(self.close)
        
        button_layout.addStretch()
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)
    
    def import_script_file(self):
        """导入文稿文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择演讲文稿文件",
            "",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.load_script_content(content)
                self.status_label.setText(f"√ 已导入文稿: {os.path.basename(file_path)}")
                
            except Exception as e:
                CustomMessageBox.warning(self, "导入错误", f"无法读取文件:\n{str(e)}")
                self.status_label.setText("❌ 文件导入失败")
    
    def load_script_content(self, content):
        """加载文稿内容"""
        # 清空现有内容
        self.clear_content()
        
        # 按行分割内容
        lines = content.strip().split('\n')
        valid_lines = [line.strip() for line in lines if line.strip()]
        
        if not valid_lines:
            self.empty_label.setText("文稿文件为空或格式不正确")
            self.content_layout.addWidget(self.empty_label)
            return
        
        # 创建行组件
        self.script_lines = []
        for i, line in enumerate(valid_lines, 1):
            line_widget = ScriptLineWidget(i, line)
            line_widget.line_selected.connect(self.on_line_selected)
            
            # 检查是否已经在关键词列表中
            if line in self.current_keywords:
                line_widget.mark_as_added()
            
            self.script_lines.append(line_widget)
            self.content_layout.addWidget(line_widget)
        
        self.content_layout.addStretch()
        self.status_label.setText(f"共导入 {len(valid_lines)} 行文稿内容")
    
    def clear_content(self):
        """清空内容区域"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def on_line_selected(self, text):
        """行被选中时的处理"""
        if text not in self.current_keywords:
            self.current_keywords.append(text)
            self.status_label.setText(f"✅ 已添加关键词: {text[:30]}{'...' if len(text) > 30 else ''}")
            
    def apply_changes(self):
        """应用更改"""
        # 保存导入的文稿到文件
        self.save_imported_script()
        
        self.keywords_updated.emit(self.current_keywords)
        self.status_label.setText(f"✅ 已应用更改，当前关键词总数: {len(self.current_keywords)}")
        CustomMessageBox.information(self, "应用成功", f"关键词列表已更新\n当前共有 {len(self.current_keywords)} 个关键词")
    
    def save_imported_script(self):
        """保存导入的文稿数据"""
        if not self.script_lines:
            return
        
        script_data = {
            "title": "导入的演讲文稿",
            "import_time": QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"),
            "total_lines": len(self.script_lines),
            "lines": []
        }
        
        for widget in self.script_lines:
            line_data = {
                "line_number": widget.line_number,
                "text": widget.text,
                "is_added_to_keywords": widget.is_added,
                "character_count": len(widget.text)
            }
            script_data["lines"].append(line_data)
        
        try:
            import json
            script_file_path = "imported_script.json"
            with open(script_file_path, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, ensure_ascii=False, indent=2)
            
            print(f"📄 文稿已保存到: {script_file_path}")
            self.status_label.setText(f"✅ 文稿已保存，共 {len(self.script_lines)} 行")
            
        except Exception as e:
            # print(
            self.status_label.setText("⚠️ 文稿保存失败")


class ScriptManager:
    """文稿管理器主类"""
    
    def __init__(self):
        self.script_content = ""
        self.script_lines = []
        self.script_data = None  # 存储完整的文稿数据
    
    def load_script_from_file(self, file_path):
        """从文件加载文稿"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.script_content = f.read()
            
            self.script_lines = [line.strip() for line in self.script_content.split('\n') if line.strip()]
            return True
        except Exception as e:
            print(f"加载文稿失败: {e}")
            return False
    
    def load_imported_script(self, script_file_path="imported_script.json"):
        """加载已导入的文稿数据"""
        try:
            if not os.path.exists(script_file_path):
                print(f"文稿文件不存在: {script_file_path}")
                return False
            
            with open(script_file_path, 'r', encoding='utf-8') as f:
                self.script_data = json.load(f)
            
            # 提取文本行
            self.script_lines = [line_data["text"] for line_data in self.script_data.get("lines", [])]
            self.script_content = "\n".join(self.script_lines)
            
            # print(
            # print(
            return True
            
        except Exception as e:
            # print(
            return False
    
    def get_lines(self):
        """获取文稿行列表"""
        return self.script_lines
    
    def get_content(self):
        """获取完整文稿内容"""
        return self.script_content
    
    def get_script_data(self):
        """获取完整的文稿数据（包含元数据）"""
        return self.script_data
    
    def get_line_by_number(self, line_number):
        """根据行号获取文本行"""
        if 1 <= line_number <= len(self.script_lines):
            return self.script_lines[line_number - 1]
        return None
    
    def search_lines_by_keyword(self, keyword):
        """根据关键词搜索文本行"""
        matching_lines = []
        for i, line in enumerate(self.script_lines, 1):
            if keyword.lower() in line.lower():
                matching_lines.append({
                    "line_number": i,
                    "text": line,
                    "keyword": keyword
                })
        return matching_lines
