from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QStackedWidget, QFileDialog,
                             QSpinBox, QComboBox, QGroupBox, QFormLayout, QSpacerItem,
                             QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("大学生Presentation助手")
        self.setMinimumSize(900, 650)
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建左侧控制面板
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)  # 1是拉伸因子

        # 创建中间控制面板
        center_panel = self.create_center_panel()
        main_layout.addWidget(center_panel, 3)  # 1是拉伸因子
        
        # 创建右侧设置面板
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 1)  # 1是拉伸因子
        
        # 连接信号
        self.connect_signals()
        
        # 设置样式
        self.load_styles()
    
    def connect_signals(self):
        # 连接文件选择按钮的点击信号
        self.open_ppt_btn.clicked.connect(self.select_ppt_file)
    
    def select_ppt_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择PPT文件",
            "",
            "PowerPoint Files (*.ppt *.pptx)"
        )
        if file_path:
            self.file_path_label.setText(file_path)
            self.start_btn.setEnabled(True)
            self.status_label.setText("PPT文件已选择")
    
    def create_center_panel(self):
        panel = QGroupBox()
        panel.setObjectName("centerPanel")
        panel.setStyleSheet("#centerPanel { background-color: white; }")  
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        self.center_title = QLabel("PPT演示内容")
        self.center_title.setAlignment(Qt.AlignCenter)
        self.center_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.center_title)

        # 提示
        self.center_tip = QLabel("请导入或选择一个PPT文件开始播放")
        self.center_tip.setAlignment(Qt.AlignCenter)
        self.center_tip.setStyleSheet("color: #888; font-size: 16px;")
        layout.addWidget(self.center_tip)

        # 打开PPT按钮
        self.open_ppt_btn = QPushButton("打开PPT文件")
        self.open_ppt_btn.setIcon(QIcon("resources/icons/file.png"))
        self.open_ppt_btn.setFixedWidth(180)
        self.open_ppt_btn.setFixedHeight(40)
        layout.addWidget(self.open_ppt_btn, alignment=Qt.AlignCenter)

        layout.addStretch()

        # 幻灯片预览区
        preview_group = QGroupBox()
        preview_group.setTitle("")
        preview_layout = QHBoxLayout(preview_group)
        preview_layout.setSpacing(15)
        preview_layout.setContentsMargins(0, 20, 0, 0)
        self.slide_previews = []
        for i in range(1, 6):
            btn = QPushButton(str(i))
            btn.setFixedSize(80, 80)
            btn.setStyleSheet("font-size: 18px; background-color: #F5F5F5; border: 2px solid #5C8EDC; border-radius: 10px;")
            self.slide_previews.append(btn)
            preview_layout.addWidget(btn)
        layout.addWidget(preview_group)
       
        return panel

    def create_right_panel(self):
        panel = QGroupBox()
        panel.setObjectName("rightPanel")
        panel.setStyleSheet("#rightPanel { background-color: white; }")  
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 30, 20, 20)

        # 演示信息
        info_group = QGroupBox("演示信息")
        info_layout = QVBoxLayout(info_group)
        self.slide_count_label = QLabel("幻灯片总数: 25")
        self.current_page_label = QLabel("当前页码: 1/25")
        self.duration_label = QLabel("演示时长: 03:45")
        self.remain_label = QLabel("剩余时间: 12:15")
        info_layout.addWidget(self.slide_count_label)
        info_layout.addWidget(self.current_page_label)
        info_layout.addWidget(self.duration_label)
        info_layout.addWidget(self.remain_label)
        layout.addWidget(info_group)

        # 操作记录
        record_group = QGroupBox("操作记录")
        record_layout = QVBoxLayout(record_group)
        self.record_list = QVBoxLayout()
        # 示例记录
        for icon, text in [
            ("resources/icons/play.png", "开始播放/放映演示"),
            ("resources/icons/next.png", "切换到第2页"),
            ("resources/icons/gesture.png", "手势识别: 下一页  14:23:45")]:
            h = QHBoxLayout()
            lbl_icon = QLabel()
            lbl_icon.setPixmap(QIcon(icon).pixmap(18, 18))
            lbl_text = QLabel(text)
            h.addWidget(lbl_icon)
            h.addWidget(lbl_text)
            h.addStretch()
            self.record_list.addLayout(h)
        record_layout.addLayout(self.record_list)
        layout.addWidget(record_group)

        # 状态提示
        status_group = QGroupBox("状态提示")
        status_layout = QVBoxLayout(status_group)
        self.gesture_status_label = QLabel("✔ 手势识别已启用\n正在检测手势...")
        self.gesture_status_label.setStyleSheet("background-color: #E8F5E9; color: #388E3C; border-radius: 6px; padding: 8px;")
        self.voice_status_label = QLabel("语音识别已启用\n等待语音指令...")
        self.voice_status_label.setStyleSheet("background-color: #E3F2FD; color: #1976D2; border-radius: 6px; padding: 8px;")
        status_layout.addWidget(self.gesture_status_label)
        status_layout.addWidget(self.voice_status_label)
        layout.addWidget(status_group)

        layout.addStretch()
        return panel

    def create_left_panel(self):
        panel = QGroupBox("PPT控制")
        panel.setObjectName("leftPanel")
        panel.setStyleSheet("#leftPanel { background-color: white; }")
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 30, 20, 20)
      
        # 播放控制
        control_group = QGroupBox("播放控制")
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(15)

        self.prev_btn = QPushButton("上一页")
        self.prev_btn.setIcon(QIcon("resources/icons/prev.png"))
        self.prev_btn.setMinimumHeight(28)
        self.prev_btn.setMaximumWidth(100)
        self.prev_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.prev_btn.setStyleSheet("margin-left:0px;margin-right:0px;")

        self.start_btn = QPushButton("播放")
        self.start_btn.setIcon(QIcon("resources/icons/play.png"))
        self.start_btn.setMinimumHeight(28)
        self.start_btn.setMaximumWidth(100)
        self.start_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.start_btn.setStyleSheet("margin-left:0px;margin-right:0px;")

        self.next_btn = QPushButton("下一页")
        self.next_btn.setIcon(QIcon("resources/icons/next.png"))
        self.next_btn.setMinimumHeight(28)
        self.next_btn.setMaximumWidth(100)
        self.next_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.next_btn.setStyleSheet("margin-left:0px;margin-right:0px;")

        control_layout.addWidget(self.prev_btn)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.next_btn)
        layout.addWidget(control_group)
        
        # 手势控制
        gesture_group = QGroupBox("手势控制")
        gesture_layout = QVBoxLayout(gesture_group)
        gesture_layout.setSpacing(10)
        #gesture_layout.setContentsMargins(0, 0, 0, 0)  # 设置手势控制分组的左右边距
        
        # 手势功能映射
        mapping_group = QGroupBox("")
        mapping_layout = QFormLayout(mapping_group)
        mapping_layout.setSpacing(10)
        
        self.gesture_mappings = {}
        gestures = ["向左滑动", "向右滑动", "向上滑动", "向下滑动", "握拳", "张开手掌","自定义手势","无"]
        actions = ["上一页", "下一页", "开始播放", "结束播放", "暂停", "继续"]
        
        for action, gesture in zip(actions, gestures):
            label = QLabel(f"{action}:")
            label.setStyleSheet("color: #222; font-size: 14px;")
            combo = QComboBox()
            combo.addItems(gestures)
            combo.setCurrentText(gesture)
            self.gesture_mappings[action] = combo
            mapping_layout.addRow(label, combo)
        
        gesture_layout.addWidget(mapping_group)

        # 检测间隔设置
        interval_group = QGroupBox("检测设置")
        interval_layout = QFormLayout(interval_group)
        interval_layout.setSpacing(10)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 10)
        self.interval_spin.setValue(3)
        self.interval_spin.setSuffix(" 秒")
        interval_layout.addRow("检测间隔:", self.interval_spin)
        gesture_layout.addWidget(interval_group)

        self.gesture_btn = QPushButton("开启手势检测")
        self.gesture_btn.setCheckable(True)
        self.gesture_btn.setIcon(QIcon("resources/icons/gesture.png"))
        self.gesture_btn.setMinimumHeight(40)
        self.gesture_btn.setMaximumWidth(220)
        self.gesture_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.gesture_btn.setStyleSheet("margin-left:0px;margin-right:0px;")

        gesture_layout.addWidget(self.gesture_btn, alignment=Qt.AlignHCenter)
        layout.addWidget(gesture_group)
        
         # 语音识别
        voice_group = QGroupBox("语音识别")
        voice_layout = QVBoxLayout(voice_group)
        self.voice_label = QLabel("语音识别已启用\n等待语音指令...")
        self.voice_label.setStyleSheet("background-color: #F5F5F5; padding: 10px; border-radius: 5px;")
        voice_layout.addWidget(self.voice_label)

        self.voice_btn = QPushButton("开启语音识别")
        self.voice_btn.setCheckable(True)
        self.voice_btn.setIcon(QIcon("resources/icons/gesture.png"))
        self.voice_btn.setMinimumHeight(28)
        self.voice_btn.setMaximumWidth(220)
        self.gesture_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.gesture_btn.setStyleSheet("margin-left:0px;margin-right:0px;")

        voice_layout.addWidget(self.voice_btn, alignment=Qt.AlignHCenter)
        layout.addWidget(voice_group)
        
        # 添加弹性空间
        layout.addStretch()
        return panel
    
    
    def load_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F5F5;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                margin-top: 15px;
                padding: 15px;
                background-color: #F5F5F5;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #5C8EDC;
            }
            QPushButton {
                background-color: #5C8EDC;
                color: white;
                border: none;
                padding: 6px 12px;
                margin: 8px;
                border-radius: 8px;
                font-size: 14px;
                min-height: 16px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #466BB0;
            }
            QPushButton:hover {
                background-color: #466BB0;
            }
            QPushButton:pressed {
                background-color: #395A96;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
            QLabel {
                font-size: 14px;
                color: #424242;
                padding: 2px;
                font-weight: 500;
            }
            QSpinBox, QComboBox {
                padding: 2px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                min-height: 25px;
                background-color: white;
                selection-background-color: #5C8EDC;
                selection-color: white;
            }
            QSpinBox:hover, QComboBox:hover {
                border-color: #5C8EDC;
            }
            QSpinBox:focus, QComboBox:focus {
                border-color: #466BB0;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: url(resources/icons/down-arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #5C8EDC;
                border-radius: 6px;
                background-color: white;
                selection-background-color: #5C8EDC;
                selection-color: white;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                background-color: #5C8EDC;
                border-radius: 3px;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #466BB0;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 8px;
                height: 8px;
                background-color: white;
            }
        """) 