#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
帮助窗口模块
提供应用程序的基本教程和使用说明
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTextEdit, QTabWidget, QWidget, QScrollArea,
                               QFrame, QSizePolicy)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QPixmap
from PySide6.QtSvgWidgets import QSvgWidget

class HelpWindow(QDialog):
    """帮助窗口类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PPT播放助手 - 帮助文档")
        self.setWindowIcon(QIcon("resources/icons/help.svg"))
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)  # 去除标题栏
        self.resize(1000, 700)  # 增加宽度和高度
        self.setMinimumSize(900, 600)  # 增加最小尺寸
        self.setContentsMargins(30, 30, 30, 30)
        
        # 设置窗口居中
        self._center_window()
        
        # 初始化UI
        self.init_ui()
        self.load_styles()
    
    def showEvent(self, event):
        """窗口显示事件，确保窗口居中"""
        super().showEvent(event)
        # 在窗口显示后重新居中，确保位置正确
        self._center_window()
    
    def _center_window(self):
        """将窗口居中显示在屏幕正中间"""
        from PySide6.QtGui import QGuiApplication
        
        # 获取主屏幕的几何信息
        screen = QGuiApplication.primaryScreen().geometry()
        
        # 计算窗口在屏幕中央的位置
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        
        # 设置窗口位置
        self.move(x, y)
        print(f"📍 帮助窗口已居中显示: 位置({x}, {y}), 尺寸({self.width()}, {self.height()})")
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建标题栏
        title_bar = self.create_title_bar()
        layout.addWidget(title_bar)
        
        # 创建主要内容区域
        content_area = self.create_content_area()
        layout.addWidget(content_area, 1)
        
        # 创建底部按钮栏
        button_bar = self.create_button_bar()
        layout.addWidget(button_bar)
    
    def create_title_bar(self):
        """创建标题栏"""
        title_frame = QFrame()
        title_frame.setObjectName("titleFrame")
        title_frame.setFixedHeight(80)  # 增加高度
        
        layout = QHBoxLayout(title_frame)
        layout.setContentsMargins(30, 0, 30, 0)  # 增加左右边距
        layout.setSpacing(20)  # 增加间距
        layout.setAlignment(Qt.AlignLeft)  # 设置主布局左对齐
        
        # 图标
        icon_label = QLabel()
        icon_pixmap = QIcon("resources/icons/help.svg").pixmap(40, 40)  # 增大图标
        icon_label.setPixmap(icon_pixmap)
        icon_label.setFixedSize(40, 40)
        
        # 标题
        title_label = QLabel("帮助文档")
        title_font = QFont()
        title_font.setFamily("Microsoft YaHei")
        title_font.setPointSize(22)  # 增大字体
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #23213A;")  # 设置标题颜色
        title_label.setAlignment(Qt.AlignLeft)  # 左对齐
        
        # 副标题
        subtitle_label = QLabel("PPT播放助手使用指南")
        subtitle_label.setStyleSheet("color: #666; font-size: 14px;")
        subtitle_label.setAlignment(Qt.AlignLeft)  # 左对齐
        
        # 版本信息
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("""
            color: #5B5BF6; 
            font-size: 11px; 
            background: rgba(91, 91, 246, 0.1); 
            padding: 2px 6px; 
            border-radius: 8px;
            font-weight: bold;
            max-height: 20px;
        """)
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: none;
                border-radius: 16px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF4444;
                color: white;
            }
            QPushButton:pressed {
                background-color: #CC3333;
            }
        """)
        close_btn.clicked.connect(self.accept)
        
        # 左侧布局
        left_layout = QHBoxLayout()
        left_layout.setSpacing(15)
        left_layout.setAlignment(Qt.AlignLeft)  # 设置左侧布局左对齐
        left_layout.addWidget(icon_label)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.setAlignment(Qt.AlignLeft)  # 设置布局左对齐
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        left_layout.addLayout(title_layout)
        
        layout.addLayout(left_layout)
        layout.addStretch()
        layout.addWidget(version_label)
        layout.addWidget(close_btn)
        
        return title_frame
    
    def create_content_area(self):
        """创建内容区域"""
        # 创建选项卡控件
        tab_widget = QTabWidget()
        tab_widget.setObjectName("helpTabWidget")
        
        # 添加各个选项卡
        tab_widget.addTab(self.create_quick_start_tab(), "🚀 快速开始")
        tab_widget.addTab(self.create_basic_tutorial_tab(), "📚 基本教程")
        tab_widget.addTab(self.create_gesture_help_tab(), "👋 手势控制")
        tab_widget.addTab(self.create_voice_help_tab(), "🎙️ 语音识别")
        tab_widget.addTab(self.create_ai_help_tab(), "🤖 AI功能")
        tab_widget.addTab(self.create_faq_tab(), "❓ 常见问题")
        
        return tab_widget
    
    def create_quick_start_tab(self):
        """创建快速开始选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 欢迎信息
        welcome_label = QLabel("欢迎使用PPT播放助手！")
        welcome_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #5B5BF6; margin-bottom: 10px;")
        layout.addWidget(welcome_label)
        
        # 快速开始步骤
        steps_text = """
<h3 style="color: #5B5BF6; margin-bottom: 30px;">🎯 三步快速开始：</h3>

<h4 style="color: #23213A; margin: 25px 0 20px 0;">步骤 1：打开PPT文件</h4>
<p style="margin: 12px 0; line-height: 2.0;">• 点击中央的"打开PPT文件"按钮</p>
<p style="margin: 12px 0; line-height: 2.0;">• 选择您要演示的PowerPoint文件（.ppt 或 .pptx）</p>
<p style="margin: 12px 0; line-height: 2.0;">• 系统会自动显示第一张幻灯片的预览</p>

<h4 style="color: #23213A; margin: 25px 0 20px 0;">步骤 2：配置控制方式</h4>
<p style="margin: 12px 0; line-height: 2.0;">• <strong>手势控制：</strong>勾选"启用手势识别"，可用手势控制幻灯片切换</p>
<p style="margin: 12px 0; line-height: 2.0;">• <strong>语音控制：</strong>勾选"启用语音识别"，可用语音命令控制</p>
<p style="margin: 12px 0; line-height: 2.0;">• <strong>AI字幕：</strong>启用语音识别后，可开启"显示AI字幕"功能</p>

<h4 style="color: #23213A; margin: 25px 0 20px 0;">步骤 3：开始演示</h4>
<p style="margin: 12px 0; line-height: 2.0;">• 点击"开始播放"按钮启动演示</p>
<p style="margin: 12px 0; line-height: 2.0;">• 悬浮窗会自动显示，提供便捷的控制界面</p>
<p style="margin: 12px 0; line-height: 2.0;">• 使用配置好的手势或语音命令控制演示</p>

<div style="background: linear-gradient(135deg, #f0f8ff 0%, #e8f4fd 100%); padding: 20px; border-radius: 12px; margin-top: 30px; border: 1px solid rgba(91, 91, 246, 0.1);">
<h4 style="color: #5B5BF6; margin-bottom: 15px;">💡 小贴士：</h4>
<p style="margin: 12px 0; line-height: 2.0;">• 首次使用建议先在"基本教程"中了解详细功能</p>
<p style="margin: 12px 0; line-height: 2.0;">• 可以在演示过程中随时调整设置</p>
<p style="margin: 12px 0; line-height: 2.0;">• 悬浮窗支持拖拽移动，不会遮挡演示内容</p>
</div>
        """
        
        text_edit = QTextEdit()
        text_edit.setHtml(steps_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        return widget
    
    def create_basic_tutorial_tab(self):
        """创建基本教程选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        tutorial_text = """
<h2 style="color: #5B5BF6; margin-bottom: 30px;">📚 基本教程</h2>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">🎮 播放控制</h3>
<p style="margin: 12px 0; line-height: 2.0;"><strong>开始/暂停演示：</strong></p>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">点击"开始播放"按钮启动PPT演示</li>
<li style="margin: 8px 0; line-height: 2.0;">演示开始后，按钮变为"暂停"，可随时暂停演示</li>
<li style="margin: 8px 0; line-height: 2.0;">悬浮窗提供"开始"、"上一页"、"下一页"、"结束演示"按钮</li>
</ul>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">👋 手势控制设置</h3>
<p style="margin: 12px 0; line-height: 2.0;"><strong>启用手势识别：</strong></p>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">勾选左侧面板中的"启用手势识别"复选框</li>
<li style="margin: 8px 0; line-height: 2.0;">可以自定义手势映射：上一页、下一页、开始播放、结束播放等</li>
<li style="margin: 8px 0; line-height: 2.0;">支持的手势类型：向左滑动、向右滑动、握拳、张开手掌、OK手势等</li>
<li style="margin: 8px 0; line-height: 2.0;">可调整检测间隔（50-1000ms），默认200ms</li>
</ul>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">🎙️ 语音识别设置</h3>
<p style="margin: 12px 0; line-height: 2.0;"><strong>启用语音识别：</strong></p>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">勾选"启用语音识别"复选框</li>
<li style="margin: 8px 0; line-height: 2.0;">点击"设置关键词"按钮自定义语音命令</li>
<li style="margin: 8px 0; line-height: 2.0;">点击"导入文稿"可导入演讲稿，启用文稿跟随功能</li>
<li style="margin: 8px 0; line-height: 2.0;">启用"显示AI字幕"可实时显示语音识别结果</li>
<li style="margin: 8px 0; line-height: 2.0;">启用"启用文稿跟随"可根据语音自动跟踪演讲进度</li>
</ul>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">🤖 AI功能</h3>
<p style="margin: 12px 0; line-height: 2.0;"><strong>AI优化建议：</strong></p>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">打开PPT文件后，"获取PPT优化建议"按钮会被启用</li>
<li style="margin: 8px 0; line-height: 2.0;">点击按钮，AI会分析您的PPT内容并提供优化建议</li>
<li style="margin: 8px 0; line-height: 2.0;">建议包括内容结构、视觉设计、演讲技巧等方面</li>
</ul>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">📱 悬浮窗功能</h3>
<p style="margin: 12px 0; line-height: 2.0;"><strong>悬浮窗控制：</strong></p>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">演示开始后自动显示悬浮窗</li>
<li style="margin: 8px 0; line-height: 2.0;">悬浮窗包含：播放控制、文稿显示、字幕显示、录制功能</li>
<li style="margin: 8px 0; line-height: 2.0;">可以拖拽移动悬浮窗位置</li>
<li style="margin: 8px 0; line-height: 2.0;">支持最小化，不影响演示效果</li>
<li style="margin: 8px 0; line-height: 2.0;">集成录制功能，可录制演示过程</li>
</ul>

<div style="background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%); padding: 20px; border-radius: 12px; margin-top: 30px; border: 1px solid rgba(40, 167, 69, 0.3);">
<h3 style="color: #155724; margin-bottom: 15px;">📊 状态监控</h3>
<p style="margin: 12px 0; line-height: 2.0;"><strong>实时状态显示：</strong></p>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">右侧面板显示演示信息：幻灯片总数、当前页码、演示时长</li>
<li style="margin: 8px 0; line-height: 2.0;">状态提示区域显示系统状态、手势状态、语音状态</li>
<li style="margin: 8px 0; line-height: 2.0;">错误信息会及时显示在状态区域</li>
</ul>
</div>
        """
        
        text_edit = QTextEdit()
        text_edit.setHtml(tutorial_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        return widget
    
    def create_gesture_help_tab(self):
        """创建手势控制帮助选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        gesture_text = """
<h2 style="color: #5B5BF6; margin-bottom: 30px;">👋 手势控制详解</h2>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">🎯 支持的手势类型</h3>

<div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #6c757d;">
<h4 style="color: #495057; margin-bottom: 15px;">动态手势（滑动类）</h4>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;"><strong>向左滑动：</strong>默认映射为"上一页"</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>向右滑动：</strong>默认映射为"下一页"</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>向上滑动：</strong>可自定义映射</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>向下滑动：</strong>可自定义映射</li>
</ul>
</div>

<div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #2196f3;">
<h4 style="color: #1565c0; margin-bottom: 15px;">静态手势（手型类）</h4>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;"><strong>握拳：</strong>五指收拢成拳头状</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>张开手掌：</strong>五指完全张开</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>OK手势：</strong>拇指和食指形成圆圈</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>食指：</strong>仅伸出食指，其他手指收拢</li>
</ul>
</div>

<div style="background: linear-gradient(135deg, #ffeef0 0%, #fce4ec 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #e91e63;">
<h4 style="color: #c2185b; margin-bottom: 15px;">特殊手势</h4>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;"><strong>双手手势：</strong>默认映射为"结束播放"，需要同时使用双手</li>
</ul>
</div>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">⚙️ 手势设置</h3>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;"><strong>自定义映射：</strong>在左侧面板的手势控制区域，可以为每个动作选择对应的手势</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>检测间隔：</strong>调整手势检测的频率，较低的值响应更快但可能误触发</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>禁用手势：</strong>将手势设置为"无"可以禁用特定动作的手势控制</li>
</ul>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">💡 使用技巧</h3>
<div style="background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%); padding: 20px; border-radius: 12px; border-left: 4px solid #4caf50;">
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">确保摄像头能清楚看到您的手部</li>
<li style="margin: 8px 0; line-height: 2.0;">手势动作要清晰明确，避免模糊不清</li>
<li style="margin: 8px 0; line-height: 2.0;">滑动手势需要有明显的方向性移动</li>
<li style="margin: 8px 0; line-height: 2.0;">静态手势需要保持1-2秒钟让系统识别</li>
<li style="margin: 8px 0; line-height: 2.0;">避免在强光或背光环境下使用</li>
<li style="margin: 8px 0; line-height: 2.0;">建议在演示前先测试手势识别效果</li>
</ul>
</div>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">🔧 故障排除</h3>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;"><strong>手势无响应：</strong>检查摄像头是否正常工作，确保手势在摄像头视野内</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>误触发：</strong>增加检测间隔时间，或调整手势映射</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>识别不准确：</strong>改善光照条件，确保手势动作标准</li>
</ul>
        """
        
        text_edit = QTextEdit()
        text_edit.setHtml(gesture_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        return widget
    
    def create_voice_help_tab(self):
        """创建语音识别帮助选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        voice_text = """
<h2 style="color: #5B5BF6; margin-bottom: 30px;">🎙️ 语音识别功能详解</h2>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">🎯 基本功能</h3>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;"><strong>语音命令控制：</strong>通过说出预设的关键词来控制PPT播放</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>AI字幕显示：</strong>实时将语音转换为文字显示</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>文稿跟随：</strong>根据语音内容自动跟踪演讲进度</li>
</ul>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">⚙️ 设置步骤</h3>

<div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #6c757d;">
<h4 style="color: #495057; margin-bottom: 15px;">1. 启用语音识别</h4>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">勾选左侧面板中的"启用语音识别"复选框</li>
<li style="margin: 8px 0; line-height: 2.0;">系统会自动检测麦克风设备</li>
<li style="margin: 8px 0; line-height: 2.0;">确保麦克风权限已授予应用程序</li>
</ul>
</div>

<div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #2196f3;">
<h4 style="color: #1565c0; margin-bottom: 15px;">2. 设置关键词</h4>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">点击"设置关键词"按钮打开关键词管理器</li>
<li style="margin: 8px 0; line-height: 2.0;">可以添加、编辑、删除语音命令关键词</li>
<li style="margin: 8px 0; line-height: 2.0;">默认关键词包括："下一页"、"上一页"、"开始"、"结束"等</li>
<li style="margin: 8px 0; line-height: 2.0;">支持自定义关键词，建议使用简短明确的词语</li>
</ul>
</div>

<div style="background: linear-gradient(135deg, #ffeef0 0%, #fce4ec 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #e91e63;">
<h4 style="color: #c2185b; margin-bottom: 15px;">3. 导入演讲文稿</h4>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">点击"导入文稿"按钮</li>
<li style="margin: 8px 0; line-height: 2.0;">可以输入或粘贴演讲稿内容</li>
<li style="margin: 8px 0; line-height: 2.0;">系统会自动从文稿中提取关键词</li>
<li style="margin: 8px 0; line-height: 2.0;">启用文稿跟随功能后，可根据语音自动定位演讲进度</li>
</ul>
</div>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">🔧 高级功能</h3>

<div style="background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #4caf50;">
<h4 style="color: #2e7d32; margin-bottom: 15px;">AI字幕显示</h4>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">启用语音识别后，可勾选"显示AI字幕"</li>
<li style="margin: 8px 0; line-height: 2.0;">悬浮窗会实时显示语音识别结果</li>
<li style="margin: 8px 0; line-height: 2.0;">支持中文和英文语音识别</li>
<li style="margin: 8px 0; line-height: 2.0;">字幕会显示在悬浮窗的专用区域</li>
</ul>
</div>

<div style="background: linear-gradient(135deg, #fff3e0 0%, #ffcc02 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #ff9800;">
<h4 style="color: #e65100; margin-bottom: 15px;">文稿跟随</h4>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">需要先导入演讲文稿</li>
<li style="margin: 8px 0; line-height: 2.0;">启用"启用文稿跟随"功能</li>
<li style="margin: 8px 0; line-height: 2.0;">系统会将语音识别结果与文稿内容进行匹配</li>
<li style="margin: 8px 0; line-height: 2.0;">悬浮窗会高亮显示当前演讲位置</li>
<li style="margin: 8px 0; line-height: 2.0;">帮助演讲者掌握演讲进度</li>
</ul>
</div>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">💡 使用技巧</h3>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">确保麦克风距离适中（20-50cm）</li>
<li style="margin: 8px 0; line-height: 2.0;">说话清晰，语速适中</li>
<li style="margin: 8px 0; line-height: 2.0;">避免在嘈杂环境中使用</li>
<li style="margin: 8px 0; line-height: 2.0;">关键词要发音准确</li>
<li style="margin: 8px 0; line-height: 2.0;">可以在演示前测试语音识别效果</li>
</ul>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">🔧 故障排除</h3>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;"><strong>无法识别语音：</strong>检查麦克风设备和权限设置</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>识别不准确：</strong>改善环境噪音，调整麦克风位置</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>关键词无响应：</strong>检查关键词设置，确保发音准确</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>文稿跟随不准确：</strong>检查导入的文稿内容是否与实际演讲一致</li>
</ul>
        """
        
        text_edit = QTextEdit()
        text_edit.setHtml(voice_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        return widget
    
    def create_ai_help_tab(self):
        """创建AI功能帮助选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        ai_text = """
<h2 style="color: #5B5BF6; margin-bottom: 30px;">🤖 AI功能详解</h2>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">🎯 AI优化建议</h3>
<p style="margin: 12px 0; line-height: 2.0;">AI优化建议功能可以分析您的PPT内容，并提供专业的优化建议。</p>

<div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #6c757d;">
<h4 style="color: #495057; margin-bottom: 15px;">功能特点</h4>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;"><strong>内容分析：</strong>AI会分析PPT的文字内容、结构布局</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>多维度建议：</strong>包括内容结构、视觉设计、演讲技巧等</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>个性化建议：</strong>根据PPT的具体内容提供针对性建议</li>
<li style="margin: 8px 0; line-height: 2.0;"><strong>实时分析：</strong>修改PPT后可重新获取最新建议</li>
</ul>
</div>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">📋 使用步骤</h3>

<div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #2196f3;">
<h4 style="color: #1565c0; margin-bottom: 15px;">1. 打开PPT文件</h4>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">首先需要打开一个PPT文件</li>
<li style="margin: 8px 0; line-height: 2.0;">系统会自动提取PPT内容</li>
<li style="margin: 8px 0; line-height: 2.0;">"获取PPT优化建议"按钮会被启用</li>
</ul>
</div>

<div style="background: linear-gradient(135deg, #ffeef0 0%, #fce4ec 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #e91e63;">
<h4 style="color: #c2185b; margin-bottom: 15px;">2. 获取AI建议</h4>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">点击"💬 获取PPT优化建议"按钮</li>
<li style="margin: 8px 0; line-height: 2.0;">AI会开始分析PPT内容（可能需要几秒钟）</li>
<li style="margin: 8px 0; line-height: 2.0;">分析完成后，建议会显示在右侧的文本区域</li>
</ul>
</div>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">📊 建议内容类型</h3>

<div style="background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #4caf50;">
<h4 style="color: #2e7d32; margin-bottom: 15px;">内容结构建议</h4>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">幻灯片逻辑结构优化</li>
<li style="margin: 8px 0; line-height: 2.0;">内容层次和重点突出</li>
<li style="margin: 8px 0; line-height: 2.0;">信息密度和可读性</li>
<li style="margin: 8px 0; line-height: 2.0;">标题和小标题优化</li>
</ul>
</div>

<div style="background: linear-gradient(135deg, #fff3e0 0%, #ffcc02 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #ff9800;">
<h4 style="color: #e65100; margin-bottom: 15px;">视觉设计建议</h4>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">色彩搭配和主题一致性</li>
<li style="margin: 8px 0; line-height: 2.0;">字体选择和大小建议</li>
<li style="margin: 8px 0; line-height: 2.0;">图片和图表使用建议</li>
<li style="margin: 8px 0; line-height: 2.0;">布局和空白空间优化</li>
</ul>
</div>

<div style="background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #9c27b0;">
<h4 style="color: #7b1fa2; margin-bottom: 15px;">演讲技巧建议</h4>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">演讲节奏和时间控制</li>
<li style="margin: 8px 0; line-height: 2.0;">互动环节设计</li>
<li style="margin: 8px 0; line-height: 2.0;">重点内容强调方式</li>
<li style="margin: 8px 0; line-height: 2.0;">听众参与度提升</li>
</ul>
</div>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">💡 使用技巧</h3>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">建议在PPT制作的不同阶段多次使用AI分析</li>
<li style="margin: 8px 0; line-height: 2.0;">可以根据建议逐步优化PPT内容</li>
<li style="margin: 8px 0; line-height: 2.0;">结合具体的演讲场景和听众特点应用建议</li>
<li style="margin: 8px 0; line-height: 2.0;">AI建议仅供参考，最终决策还需结合实际情况</li>
</ul>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">🔧 注意事项</h3>
<div style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); padding: 20px; border-radius: 12px; border-left: 4px solid #f39c12;">
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">需要网络连接才能使用AI功能</li>
<li style="margin: 8px 0; line-height: 2.0;">分析时间取决于PPT内容的复杂程度</li>
<li style="margin: 8px 0; line-height: 2.0;">建议在网络状况良好时使用</li>
<li style="margin: 8px 0; line-height: 2.0;">如果分析失败，可以稍后重试</li>
</ul>
</div>

<h3 style="color: #23213A; margin: 25px 0 20px 0;">🚀 未来功能</h3>
<p style="margin: 12px 0; line-height: 2.0;">我们正在开发更多AI功能：</p>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">AI演讲稿生成</li>
<li style="margin: 8px 0; line-height: 2.0;">智能幻灯片排版</li>
<li style="margin: 8px 0; line-height: 2.0;">演讲效果评估</li>
<li style="margin: 8px 0; line-height: 2.0;">个性化学习建议</li>
</ul>
        """
        
        text_edit = QTextEdit()
        text_edit.setHtml(ai_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        return widget
    
    def create_faq_tab(self):
        """创建常见问题选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        faq_text = """
<h2 style="color: #5B5BF6; margin-bottom: 30px;">❓ 常见问题解答</h2>

<div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #6c757d;">
<h4 style="color: #495057; margin-bottom: 15px;">Q: 为什么手势识别不工作？</h4>
<p style="margin: 12px 0; line-height: 2.0;"><strong>A:</strong> 请检查以下几点：</p>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">确保摄像头正常工作且未被其他应用占用</li>
<li style="margin: 8px 0; line-height: 2.0;">检查摄像头权限是否已授予应用程序</li>
<li style="margin: 8px 0; line-height: 2.0;">确保手势在摄像头视野范围内</li>
<li style="margin: 8px 0; line-height: 2.0;">改善光照条件，避免背光或强光</li>
<li style="margin: 8px 0; line-height: 2.0;">确保已勾选"启用手势识别"复选框</li>
</ul>
</div>

<div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #2196f3;">
<h4 style="color: #1565c0; margin-bottom: 15px;">Q: 语音识别无法正常工作？</h4>
<p style="margin: 12px 0; line-height: 2.0;"><strong>A:</strong> 请尝试以下解决方案：</p>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">检查麦克风设备是否正常连接</li>
<li style="margin: 8px 0; line-height: 2.0;">确认麦克风权限已授予应用程序</li>
<li style="margin: 8px 0; line-height: 2.0;">检查系统音量设置和麦克风音量</li>
<li style="margin: 8px 0; line-height: 2.0;">尝试在安静环境中使用</li>
<li style="margin: 8px 0; line-height: 2.0;">确保已勾选"启用语音识别"复选框</li>
</ul>
</div>

<div style="background: linear-gradient(135deg, #ffeef0 0%, #fce4ec 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #e91e63;">
<h4 style="color: #c2185b; margin-bottom: 15px;">Q: PPT文件无法打开？</h4>
<p style="margin: 12px 0; line-height: 2.0;"><strong>A:</strong> 可能的原因和解决方法：</p>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">确保文件格式为.ppt或.pptx</li>
<li style="margin: 8px 0; line-height: 2.0;">检查文件是否损坏或被加密</li>
<li style="margin: 8px 0; line-height: 2.0;">确保系统已安装Microsoft PowerPoint</li>
<li style="margin: 8px 0; line-height: 2.0;">尝试用PowerPoint先打开文件确认无误</li>
<li style="margin: 8px 0; line-height: 2.0;">检查文件路径中是否包含特殊字符</li>
</ul>
</div>

<div style="background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #4caf50;">
<h4 style="color: #2e7d32; margin-bottom: 15px;">Q: 悬浮窗显示异常？</h4>
<p style="margin: 12px 0; line-height: 2.0;"><strong>A:</strong> 请尝试以下操作：</p>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">重新启动演示（停止后再开始）</li>
<li style="margin: 8px 0; line-height: 2.0;">检查屏幕分辨率和缩放设置</li>
<li style="margin: 8px 0; line-height: 2.0;">尝试拖拽悬浮窗到合适位置</li>
<li style="margin: 8px 0; line-height: 2.0;">如果悬浮窗消失，可以重新开始演示</li>
</ul>
</div>

<div style="background: linear-gradient(135deg, #fff3e0 0%, #ffcc02 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #ff9800;">
<h4 style="color: #e65100; margin-bottom: 15px;">Q: AI功能无法使用？</h4>
<p style="margin: 12px 0; line-height: 2.0;"><strong>A:</strong> 请检查：</p>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">确保网络连接正常</li>
<li style="margin: 8px 0; line-height: 2.0;">检查是否已打开PPT文件</li>
<li style="margin: 8px 0; line-height: 2.0;">如果分析失败，请稍后重试</li>
<li style="margin: 8px 0; line-height: 2.0;">确保PPT内容不为空</li>
</ul>
</div>

<div style="background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #9c27b0;">
<h4 style="color: #7b1fa2; margin-bottom: 15px;">Q: 录制功能无法使用？</h4>
<p style="margin: 12px 0; line-height: 2.0;"><strong>A:</strong> 录制功能需要：</p>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">确保已开始PPT演示</li>
<li style="margin: 8px 0; line-height: 2.0;">检查系统录制权限</li>
<li style="margin: 8px 0; line-height: 2.0;">确保有足够的磁盘空间</li>
<li style="margin: 8px 0; line-height: 2.0;">在悬浮窗中点击录制按钮</li>
</ul>
</div>

<div style="background: linear-gradient(135deg, #e0f2f1 0%, #b2dfdb 100%); padding: 20px; border-radius: 12px; margin: 15px 0; border-left: 4px solid #009688;">
<h4 style="color: #00695c; margin-bottom: 15px;">Q: 如何获得更好的使用体验？</h4>
<p style="margin: 12px 0; line-height: 2.0;"><strong>A:</strong> 建议：</p>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0;">在演示前先测试所有功能</li>
<li style="margin: 8px 0; line-height: 2.0;">确保硬件设备（摄像头、麦克风）工作正常</li>
<li style="margin: 8px 0; line-height: 2.0;">选择合适的环境（光线充足、噪音较少）</li>
<li style="margin: 8px 0; line-height: 2.0;">熟悉手势和语音命令</li>
<li style="margin: 8px 0; line-height: 2.0;">准备备用的控制方式（鼠标、键盘）</li>
</ul>
</div>

<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 16px; margin-top: 30px; color: white; box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);">
<h3 style="color: white; margin-bottom: 20px; font-size: 18px;">🆘 技术支持</h3>
<p style="margin: 12px 0; line-height: 2.0; opacity: 0.95;">如果以上解答无法解决您的问题，请联系技术支持：</p>
<ul style="margin: 15px 0; padding-left: 20px;">
<li style="margin: 8px 0; line-height: 2.0; opacity: 0.95;"><strong>邮箱：</strong> support@pptassistant.com</li>
<li style="margin: 8px 0; line-height: 1.8; opacity: 0.95;"><strong>QQ群：</strong> 123456789</li>
<li style="margin: 8px 0; line-height: 1.8; opacity: 0.95;"><strong>微信群：</strong> 扫描二维码加入用户群</li>
</ul>
<p style="margin: 12px 0; line-height: 1.8; opacity: 0.9; font-size: 13px;">请在反馈问题时提供详细的错误信息和操作步骤，以便我们更好地为您服务。</p>
</div>
        """
        
        text_edit = QTextEdit()
        text_edit.setHtml(faq_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        return widget
    
    def create_button_bar(self):
        """创建底部按钮栏"""
        button_frame = QFrame()
        button_frame.setObjectName("buttonFrame")
        button_frame.setFixedHeight(70)  # 增加高度
        
        layout = QHBoxLayout(button_frame)
        layout.setContentsMargins(30, 15, 30, 15)  # 增加边距
        layout.setSpacing(15)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setFixedSize(100, 40)  # 增大按钮
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        return button_frame
    
    def load_styles(self):
        """加载样式表"""
        self.setStyleSheet("""
            QDialog {
                background-color: #F6F8FB;
                border-radius: 16px;
            }
            
            #titleFrame {
                background-color: #F6F8FB;
                border-radius: 16px 16px 0 0;
                border: none;
            }
            
            #buttonFrame {
                background-color: #F6F8FB;
                border-radius: 0 0 16px 16px;
                border: none;
            }
            
            #helpTabWidget {
                background-color: #FFFFFF;
                border: none;
                border-radius: 12px;
                margin: 10px 25px 25px 25px;
            }
            
            #helpTabWidget::pane {
                border: none;
                border-radius: 12px;
                background-color: #FFFFFF;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            }
            
            #helpTabWidget::tab-bar {
                alignment: left;
            }
            
            #helpTabWidget QTabBar::tab {
                background-color: transparent;
                color: #666;
                padding: 14px 18px;
                margin-right: 6px;
                margin-top: 10px;
                margin-bottom: 4px;
                border-radius: 10px;
                min-width: 95px;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.2s ease;
            }
            
            #helpTabWidget QTabBar::tab:selected {
                background-color: #5B5BF6;
                color: white;
                box-shadow: 0 2px 8px rgba(91, 91, 246, 0.3);
            }
            
            #helpTabWidget QTabBar::tab:hover:!selected {
                background-color: rgba(91, 91, 246, 0.1);
                color: #5B5BF6;
            }
            
            QTextEdit {
                background-color: #FFFFFF;
                border: none;
                border-radius: 12px;
                padding: 25px;
                font-size: 14px;
                line-height: 1.8;
                color: #23213A;
                selection-background-color: rgba(91, 91, 246, 0.2);
            }
            
            QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                padding: 14px 28px;
                box-shadow: 0 3px 12px rgba(91, 91, 246, 0.25);
                transition: all 0.2s ease;
            }
            
            QPushButton:hover {
                background-color: #4A4AE5;
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(91, 91, 246, 0.35);
            }
            
            QPushButton:pressed {
                background-color: #3939D4;
                transform: translateY(0px);
                box-shadow: 0 2px 4px rgba(91, 91, 246, 0.2);
            }
            
            QLabel {
                color: #23213A;
            }
        """) 