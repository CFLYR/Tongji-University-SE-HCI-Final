from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QStackedWidget, QFileDialog,
                               QSpinBox, QComboBox, QGroupBox, QFormLayout, QSpacerItem,
                               QSizePolicy, QCheckBox, QDialog,QTextEdit,QDialogButtonBox)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QPixmap, QImage
from PySide6.QtCore import QSize
from PySide6.QtSvgWidgets import QSvgWidget
from main_controller import MainController
from ppt_floating_window import PPTFloatingWindow
from keyword_manager import KeywordManagerDialog
from script_manager import ScriptImportDialog, ScriptManager
import cv2
import numpy as np
import win32com.client
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("大学生Presentation助手")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMinimumSize(1200, 800)

        # 初始化主控制器
        self.controller = MainController()
          # 初始化语音关键词列表
        self.voice_keywords = ["下一页"]
        
        # 初始化文稿管理器
        self.script_manager = ScriptManager()

        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部栏
        top_bar = self.create_top_bar()
        main_layout.addWidget(top_bar)

        # 创建主布局
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 0, 20, 0)
        content_layout.setStretch(0, 1)
        content_layout.setStretch(1, 3)
        content_layout.setStretch(2, 1)
        # 创建左侧控制面板
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, 1)

        # 创建中间控制面板
        center_panel = self.create_center_panel()
        content_layout.addWidget(center_panel, 3)

        # 创建右侧设置面板
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, 1)

        main_layout.addLayout(content_layout)
        # 连接信号
        self.connect_signals()

        # 设置样式
        self.load_styles()

        # 创建状态更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # 每秒更新一次状态

        # 启动系统
        self.controller.start_system()

        self.floating_window = None  # 悬浮窗实例

    def connect_signals(self):
        # 连接控制器信号
        self.controller.ppt_file_opened.connect(self.on_ppt_file_opened)
        self.controller.presentation_started.connect(self.on_presentation_started)
        self.controller.presentation_stopped.connect(self.on_presentation_stopped)
        self.controller.slide_changed.connect(self.on_slide_changed)
        self.controller.gesture_detection_started.connect(self.on_gesture_detection_started)
        self.controller.gesture_detection_stopped.connect(self.on_gesture_detection_stopped)
        self.controller.gesture_detected.connect(self.on_gesture_detected)
        # self.controller.fps_updated.connect(self.on_fps_updated)
        self.controller.config_changed.connect(self.on_config_changed)
        self.controller.gesture_enabled.connect(self.on_gesture_enabled)
        self.controller.system_status_changed.connect(self.on_system_status_changed)
        self.controller.error_occurred.connect(self.on_error_occurred)
        # 连接语音控制ppt的信号
        self.controller.voice_recognition_started.connect(self.on_voice_recognition_started)
        self.controller.voice_recognition_stopped.connect(self.on_voice_recognition_stopped)

        # 连接UI控件信号
        self.open_ppt_btn.clicked.connect(self.select_ppt_file)
        self.start_btn.clicked.connect(self.toggle_presentation)
        self.gesture_checkbox.stateChanged.connect(self.toggle_gesture_detection)
        self.voice_checkbox.stateChanged.connect(self.toggle_voice_recognition)
        self.subtitle_checkbox.stateChanged.connect(self.toggle_subtitle_display)
        self.interval_spin.valueChanged.connect(self.update_detection_interval)

        # 连接手势映射下拉框
        for action, combo in self.gesture_mappings.items():
            combo.currentTextChanged.connect(
                lambda text, a=action: self.update_gesture_mapping(a, text)
            )

    def export_first_slide_as_image(self, ppt_path, output_dir="slide_previews"):
        # 生成绝对路径
        ppt_path = os.path.abspath(ppt_path)
        output_dir = os.path.join(os.path.dirname(ppt_path), "slide_previews")
        os.makedirs(output_dir, exist_ok=True)
        img_path = os.path.join(output_dir, "first_slide.png")
        img_path = os.path.abspath(img_path)  # 关键：必须是绝对路径
        print("PPT路径：", ppt_path)
        print("导出图片路径：", img_path)
        ppt_app = win32com.client.Dispatch("PowerPoint.Application")
        print("PowerPoint COM Name:", ppt_app.Name)
        ppt_app.Visible = 1
        try:
            presentation = ppt_app.Presentations.Open(ppt_path, WithWindow=False)
            slide = presentation.Slides(1)
            slide.Export(img_path, "PNG")
            presentation.Close()
            ppt_app.Quit()
            return img_path
        except Exception as e:
            ppt_app.Quit()
            print("导出PPT缩略图失败：", e)
            raise

    def show_ppt_first_slide_preview(self, img_path):
        self.slide_image_label.show()
        # self.center_title.hide()
        self.center_tip.hide()
        self.file_path_label.hide()
        self.open_ppt_btn.hide()

        self.update_status("", True)
        pixmap = QPixmap(img_path)
        self.slide_image_label.setPixmap(pixmap)
        # 显示文件名
        ppt_path = self.file_path_label.text()
        ppt_filename = os.path.basename(ppt_path)
        self.slide_filename_label.setText(f"PPT文件名：{ppt_filename}")
        self.slide_filename_label.show()

    def select_ppt_file(self):
        """选择PPT文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择PPT文件",
            "",
            "PowerPoint Files (*.ppt *.pptx);;All Files (*.*)"
        )
        if file_path:
            self.update_status(f"已打开PPT文件: {file_path}")
            self.file_path_label.setText(file_path)
            self.controller.ppt_controller.current_ppt_path = file_path

            img_path = self.export_first_slide_as_image(file_path)
            self.show_ppt_first_slide_preview(img_path)

    def toggle_max_restore(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def toggle_presentation(self):
        """切换演示状态"""
        # 根据按钮文本判断当前状态
        if self.start_btn.text() == "开始播放":
            # 检查是否已选择PPT文件
            if not self.controller.ppt_controller.current_ppt_path:
                self.handle_error("请先选择PPT文件")
                return  # 开始播放
            if self.controller.start_presentation(self.controller.ppt_controller.current_ppt_path):
                self.start_btn.setText("暂停")
                self.update_status("正在播放PPT...")  # 打开悬浮窗
                if self.floating_window is None:
                    self.floating_window = PPTFloatingWindow()
                    # 连接悬浮窗的录像信号
                    self.floating_window.recording_started.connect(self.on_recording_started)
                    self.floating_window.recording_stopped.connect(self.on_recording_stopped)
                    self.floating_window.subtitle_updated.connect(self.on_subtitle_updated)                    # 传递主控制器引用到悬浮窗，用于检查手势识别状态
                    self.floating_window.set_main_controller(self.controller)
                    
                    # 传递文稿管理器到悬浮窗
                    if hasattr(self, 'script_manager') and self.script_manager:
                        # 尝试加载已导入的文稿
                        if self.script_manager.load_imported_script():
                            # 获取文稿预览文本
                            first_line = self.script_manager.get_line_by_number(1)
                            if first_line:
                                self.floating_window.set_script_text(f"📄 演讲文稿已加载\n{first_line[:50]}...")
                            print("✅ 已将导入的文稿加载到悬浮窗")
                        else:
                            self.floating_window.set_script_text("📄 文稿展示区\n请先导入演讲文稿")
                    
                    # 如果有演讲稿管理器，设置到悬浮窗
                    if hasattr(self.controller, 'speech_manager'):
                        self.floating_window.set_speech_manager(self.controller.speech_manager)

                    # 同步当前字幕显示状态到悬浮窗
                    if hasattr(self, 'subtitle_checkbox') and self.subtitle_checkbox.isChecked():
                        print("🔄 同步字幕显示状态到悬浮窗")
                        self.floating_window.set_subtitle_display_enabled(True)

                self.floating_window.show()
        else:
            self.controller.stop_presentation()
            self.start_btn.setText("开始播放")
            self.update_status("演示已停止")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            top_bar = self.findChild(QWidget, "topBar")
            if top_bar and top_bar.geometry().contains(event.pos()):
                self._drag_active = True
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
            else:
                self._drag_active = False

    def mouseMoveEvent(self, event):
        if hasattr(self, "_drag_active") and self._drag_active and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        self._drag_active = False

    def toggle_gesture_detection(self, enabled: bool):
        """切换手势检测状态"""
        self.controller.toggle_gesture_detection(enabled)
        status = "开启" if enabled else "关闭"
        self.update_status(f"手势检测已{status}")

    def toggle_voice_recognition(self, enabled: bool):
        """切换语音识别状态"""
        # 直接使用已保存的关键词，不再弹出设置对话框
        if enabled:
            # 启动语音识别，使用当前保存的关键词
            self.controller.toggle_voice_recognition(True, self.voice_keywords)
        else:
            # 停止语音识别
            self.controller.toggle_voice_recognition(False, [])

        # 更新状态显示
        self.update_status(f"语音识别已{'开启' if enabled else '关闭'}")        # 控制字幕复选框的可用性
        self.subtitle_checkbox.setEnabled(enabled)
        if not enabled:
            # 禁用语音识别时，也禁用字幕显示
            self.subtitle_checkbox.blockSignals(True)
            self.subtitle_checkbox.setChecked(False)
            self.subtitle_checkbox.blockSignals(False)

    def show_keyword_settings(self):
        """显示关键词设置对话框"""
        dialog = KeywordManagerDialog(self, self.voice_keywords)
        
        def on_keywords_updated(keywords):
            self.voice_keywords = keywords
            self.update_status(f"关键词已更新，共 {len(keywords)} 个")
            print(f"📝 语音关键词已更新: {keywords}")
        
        dialog.keywords_changed.connect(on_keywords_updated)
        dialog.exec() 
        
    def update_detection_interval(self, interval: int):
        """更新检测间隔"""
        self.controller.update_detection_interval(interval)
        self.update_status(f"已更新检测间隔: {interval}ms")
    
    def show_keyword_settings(self):
        """显示关键词设置对话框"""
        dialog = KeywordManagerDialog(self, self.voice_keywords)
        
        def on_keywords_updated(keywords):
            self.voice_keywords = keywords
            self.update_status(f"关键词已更新，共 {len(keywords)} 个")
            print(f"📝 语音关键词已更新: {keywords}")
        
        dialog.keywords_changed.connect(on_keywords_updated)
        dialog.exec()
    
    def show_script_import_dialog(self):
        """显示文稿导入对话框"""
        dialog = ScriptImportDialog(self, self.voice_keywords)
        
        def on_keywords_updated(keywords):
            self.voice_keywords = keywords
            
            # 尝试加载已导入的文稿到文稿管理器
            success = self.script_manager.load_imported_script()
            if success:
                # 如果悬浮窗存在，更新悬浮窗中的文稿显示
                if hasattr(self, 'floating_window') and self.floating_window:
                    # 获取文稿的第一行作为预览
                    first_line = self.script_manager.get_line_by_number(1)
                    if first_line:
                        self.floating_window.set_script_text(f"📄 文稿已导入\n{first_line[:50]}...")
                    else:
                        self.floating_window.set_script_text("📄 文稿已导入，可以开始演示")
                    
                    print("✅ 文稿已同步到悬浮窗")
            
            self.update_status(f"文稿导入完成，关键词已更新，共 {len(keywords)} 个")
            print(f"📄 从文稿导入的关键词已更新: {keywords}")
        
        dialog.keywords_updated.connect(on_keywords_updated)
        dialog.exec()

    def update_gesture_mapping(self, action: str, gesture: str):
        """更新手势映射"""
        try:
            # 创建前端到后端的映射
            action_mapping = {
                "上一页": "prev_slide",
                "下一页": "next_slide",
                "开始播放": "fullscreen",
                "结束播放": "exit",
                "暂停": "pause",
                "继续": "pause"
            }
            gesture_mapping = {
                "向左滑动": "swipe_left",
                "向右滑动": "swipe_right",
                "向上滑动": "swipe_up",
                "向下滑动": "swipe_down",
                "握拳": "fist",
                "张开手掌": "open_hand",
                "OK手势": "ok",
                "食指": "point",
                "双手手势": "dual_hand",
                "无": "none"
            }

            backend_action = action_mapping.get(action, action)
            backend_gesture = gesture_mapping.get(gesture, gesture)

            # 更新后端配置
            if hasattr(self.controller, 'gesture_controller') and hasattr(self.controller.gesture_controller,
                                                                          'gesture_configs'):
                configs = self.controller.gesture_controller.gesture_configs

                # 找到对应的配置并更新
                if backend_action in configs:
                    config = configs[backend_action]
                    # 根据手势类型更新配置
                    if backend_gesture == "none":
                        config.enabled = False
                    else:
                        config.enabled = True
                        if config.gesture_type.value == "dynamic":
                            config.motion_pattern = backend_gesture
                        elif config.gesture_type.value == "static":
                            # 设置手指模式
                            finger_patterns = {
                                "fist": [0, 0, 0, 0, 0],
                                "open_hand": [1, 1, 1, 1, 1],
                                "ok": [1, 1, 0, 0, 0],  # OK手势的手指模式
                                "point": [0, 1, 0, 0, 0],  # 食指的手指模式
                            }
                            if backend_gesture in finger_patterns:
                                config.finger_pattern = finger_patterns[backend_gesture]
                        elif config.gesture_type.value == "dual_hand":
                            # 双手手势不需要设置finger_pattern
                            pass

                    # 保存配置
                    self.controller.gesture_controller.save_gesture_configs()
                    self.update_status(f"已更新手势映射: {action} -> {gesture}")
                else:
                    self.update_status(f"未找到手势配置: {backend_action}", True)
            else:
                self.update_status("手势控制器未初始化", True)

        except Exception as e:
            self.update_status(f"更新手势映射失败: {str(e)}", True)

    def update_status(self, message: str = None, is_error: bool = False):
        """更新状态显示"""
        if message is not None:
            if is_error:
                self.status_label.setStyleSheet(
                    "background-color: #FFEBEE; color: #D32F2F; border-radius: 6px; padding: 8px;")
            else:
                self.status_label.setStyleSheet(
                    "background-color: #E8F5E9; color: #388E3C; border-radius: 6px; padding: 8px;")
            self.status_label.setText(message)

        # 更新运行时间
        status = self.controller.get_system_status()
        runtime = int(status['runtime'])
        hours = runtime // 3600
        minutes = (runtime % 3600) // 60
        seconds = runtime % 60
        self.duration_label.setText(f"演示时长: {hours:02d}:{minutes:02d}:{seconds:02d}")

    # 信号处理函数
    def on_ppt_file_opened(self, file_path: str):
        """PPT文件打开处理"""
        self.file_path_label.setText(file_path)
        self.start_btn.setEnabled(True)
        self.update_status("PPT文件已选择")

    def on_presentation_started(self):
        """演示开始处理"""
        self.start_btn.setText("暂停")
        self.update_status("正在播放PPT...")

    def on_presentation_stopped(self):
        """演示停止处理"""
        self.start_btn.setText("播放")
        self.update_status("演示已停止")

    def on_slide_changed(self, slide_number: int):
        """幻灯片切换处理"""
        self.current_page_label.setText(f"当前页码: {slide_number}")

    def on_gesture_detection_started(self):
        """手势检测开始处理"""
        self.gesture_status_label.setText("✔ 手势识别已启用\n正在检测手势...")

    def on_gesture_detection_stopped(self):
        """手势检测停止处理"""
        self.gesture_status_label.setText("✘ 手势识别已禁用")

    def on_gesture_detected(self, gesture_name: str, confidence: float):
        """手势检测处理"""
        # 可以在这里添加手势检测的视觉反馈
        pass

    def on_voice_recognition_started(self):
        """状态提示 语音识别已启用"""
        self.voice_status_label.setText("✔ 语音识别已启用\n等待语音指令...")

    def on_voice_recognition_stopped(self):
        """状态提示 语音识别已关闭"""
        self.voice_status_label.setText("✘ 手势识别已关闭")

    def on_voice_recognized(self):
        """"""
        pass

    def on_config_changed(self, config_name: str):
        """配置更改处理"""
        if config_name == "all":
            # 更新所有配置显示
            pass
        else:
            # 更新特定配置显示
            pass

    def on_gesture_enabled(self, gesture_name: str, enabled: bool):
        """手势启用状态更改处理"""
        # 更新手势启用状态显示
        pass

    def on_system_status_changed(self, status: str):
        """系统状态更改处理"""
        self.update_status(status)

    def on_error_occurred(self, error: str):
        """错误处理"""
        self.handle_error(error)

    def on_recording_started(self):
        """录像开始处理"""
        self.update_status("录像已开始", is_error=False)
        # 显示录像状态指示器
        self.recording_status_label.setText("🎥 正在录制")
        self.recording_status_label.setStyleSheet(
            "background-color: #FFEBEE; color: #D32F2F; border-radius: 6px; padding: 8px;")
        self.recording_status_label.show()
        print("🎥 录像已开始")

    def on_recording_stopped(self, video_path: str):
        """录像停止处理"""
        self.update_status(f"录像已停止，文件保存到: {video_path}", is_error=False)
        # 隐藏录像状态指示器
        self.recording_status_label.hide()
        print(f"🎬 录像已停止，保存到: {video_path}")

    def on_subtitle_updated(self, subtitle_text: str):
        """字幕更新处理"""
        # 可以在这里显示字幕或发送给演讲稿管理器进行文稿修正
        if hasattr(self.controller, 'speech_manager') and self.controller.speech_manager:
            # 发送给演讲稿管理器进行处理
            self.controller.speech_manager.process_real_time_text(subtitle_text)

        # 更新录像状态显示包含字幕信息
        if hasattr(self, 'recording_status_label') and self.recording_status_label.isVisible():
            # 截取字幕前20个字符用于显示
            subtitle_preview = subtitle_text[:20] + "..." if len(subtitle_text) > 20 else subtitle_text
            self.recording_status_label.setText(f"🎥 录制中 📝 {subtitle_preview}")

        print(f"📝 字幕更新: {subtitle_text}")

    def toggle_quick_recording(self):
        """快捷录像功能"""
        if not hasattr(self, 'floating_window') or self.floating_window is None:
            self.update_status("请先开始PPT演示以显示悬浮窗", is_error=True)
            return

        # 获取录像状态
        recording_status = self.floating_window.get_recording_status()

        if not recording_status.get('recording_available', False):
            self.update_status("录像功能不可用", is_error=True)
            return

        if recording_status.get('is_recording', False):
            # 停止录像
            self.floating_window.stop_recording()
            self.quick_record_btn.setText("录像")
            self.quick_record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF4444;
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                    margin-left: 5px;
                    margin-right: 0px;
                }
                QPushButton:hover {
                    background-color: #FF6666;
                }
                QPushButton:pressed {
                    background-color: #CC3333;
                }
            """)
        else:
            # 开始录像
            self.floating_window.start_recording()
            self.quick_record_btn.setText("停止")
            self.quick_record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                    margin-left: 5px;
                    margin-right: 0px;
                }
                QPushButton:hover {
                    background-color: #66BB6A;
                }
                QPushButton:pressed {
                    background-color: #388E3C;
                }
            """)

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        try:
            # 停止所有控制器
            if self.controller.ppt_controller.is_active():
                self.controller.exit_presentation()
            if hasattr(self.controller, 'gesture_controller') and hasattr(self.controller.gesture_controller,
                                                                          'running'):
                self.controller.gesture_controller.running = False
            event.accept()
        except Exception as e:
            self.handle_error(f"关闭时发生错误: {str(e)}")
            event.accept()

    def create_top_bar(self):
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)

        top_bar.setObjectName("topBar")
        top_bar.setStyleSheet("#topBar { background-color: white; }")

        top_layout.setContentsMargins(20, 0, 20, 0)
        top_layout.setSpacing(20)
        top_layout.setAlignment(Qt.AlignVCenter)

        # 左侧：应用图标+标题
        icon_label = QLabel()
        icon_label.setPixmap(QIcon("resources/icons/monitor.svg").pixmap(24, 24))
        icon_label.setFixedSize(28, 28)
        icon_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title_label = QLabel("PPT播放助手")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #165DFF;")
        title_label.setFixedHeight(28)

        left_layout = QHBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setAlignment(Qt.AlignVCenter)
        left_layout.addWidget(icon_label)
        left_layout.addWidget(title_label)
        # left_layout.addStretch()

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setFixedHeight(40)
        top_layout.addWidget(left_widget, 1)

        # 右侧：按钮
        btn_open = QPushButton()
        btn_open.setObjectName("windowControlButton")
        btn_open.setIcon(QIcon("resources/icons/ppt.svg"))
        btn_open.setFixedHeight(28)
        btn_open.setCursor(Qt.PointingHandCursor)

        btn_setting = QPushButton()
        btn_setting.setObjectName("windowControlButton")
        btn_setting.setIcon(QIcon("resources/icons/tiaojie.svg"))
        btn_setting.setFixedHeight(28)
        btn_setting.setCursor(Qt.PointingHandCursor)

        btn_help = QPushButton()
        btn_help.setObjectName("windowControlButton")
        btn_help.setIcon(QIcon("resources/icons/help.svg"))
        btn_help.setFixedHeight(28)
        btn_help.setCursor(Qt.PointingHandCursor)

        btn_min = QPushButton()
        btn_min.setObjectName("windowControlButton")
        btn_min.setIcon(QIcon("resources/icons/minimize.svg"))
        btn_min.setFixedSize(28, 28)
        btn_min.clicked.connect(self.showMinimized)

        btn_max = QPushButton()
        btn_max.setObjectName("windowControlButton")
        btn_max.setIcon(QIcon("resources/icons/maximize.svg"))
        btn_max.setFixedSize(28, 28)
        btn_max.clicked.connect(self.toggle_max_restore)

        btn_close = QPushButton()
        btn_close.setObjectName("windowControlButton")
        btn_close.setIcon(QIcon("resources/icons/close.svg"))
        btn_close.setFixedSize(28, 28)
        btn_close.clicked.connect(self.close)

        right_layout = QHBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        right_layout.setAlignment(Qt.AlignVCenter)

        right_layout.addStretch()
        right_layout.addWidget(btn_open)
        right_layout.addWidget(btn_setting)
        right_layout.addWidget(btn_help)
        right_layout.addWidget(btn_min)
        right_layout.addWidget(btn_max)
        right_layout.addWidget(btn_close)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        right_widget.setFixedHeight(40)
        top_layout.addWidget(right_widget, 0)

        return top_bar

    def create_center_panel(self):
        panel = QGroupBox()
        panel.setObjectName("centerPanel")
        panel.setStyleSheet("#centerPanel { background-color: #FCFCFC; }")

        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 170, 0, 30)

        # 标题
        self.center_title = QLabel("PPT演示内容预览")
        self.center_title.setAlignment(Qt.AlignCenter)
        self.center_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.center_title)

        # 提示
        self.center_tip = QLabel("请导入或选择一个PPT文件开始播放")
        self.center_tip.setAlignment(Qt.AlignCenter)
        self.center_tip.setStyleSheet("color: #888; font-size: 16px;")
        layout.addWidget(self.center_tip)

        # 文件路径显示
        self.file_path_label = QLabel("")
        self.file_path_label.setAlignment(Qt.AlignCenter)
        self.file_path_label.setStyleSheet("color: #666; font-size: 14px;")
        layout.addWidget(self.file_path_label)

        # 打开PPT按钮
        self.open_ppt_btn = QPushButton("   打开PPT文件")
        self.open_ppt_btn.setIcon(QIcon("resources/icons/ppt.svg"))
        self.open_ppt_btn.setIconSize(QSize(20, 20))
        self.open_ppt_btn.setFixedWidth(180)
        self.open_ppt_btn.setFixedHeight(40)
        layout.addWidget(self.open_ppt_btn, alignment=Qt.AlignCenter)

        self.slide_image_label = QLabel()
        self.slide_image_label.setObjectName("previewimage")
        self.slide_image_label.setStyleSheet("#previewimage { background-color: white; }")
        self.slide_image_label.setAlignment(Qt.AlignCenter)
        self.slide_image_label.setMinimumSize(427, 240)
        self.slide_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.slide_image_label.setScaledContents(True)
        # elf.slide_image_label.hide()
        layout.addWidget(self.slide_image_label, stretch=1)
        self.slide_filename_label = QLabel("")
        self.slide_filename_label.setAlignment(Qt.AlignCenter)
        self.slide_filename_label.setStyleSheet("color: #1976D2; font-size: 15px; font-weight: bold; margin-top: 8px;")
        self.slide_filename_label.hide()
        layout.addWidget(self.slide_filename_label)
        layout.addStretch()

        # # 幻灯片预览区
        # preview_group = QGroupBox("幻灯片预览")
        # preview_group.setObjectName("previewGroup")
        # preview_group.setStyleSheet("#previewGroup { background-color: white; }")
        # preview_layout = QHBoxLayout(preview_group)
        # preview_layout.setSpacing(5)
        # preview_layout.setContentsMargins(0, 10, 0, 0)
        # self.slide_previews = []
        # for i in range(1, 6):
        #     btn = QPushButton(str(i))
        #     btn.setStyleSheet("font-size: 14px; background-color: #F5F5F5; border-radius: 10px;border: none;color :#757575")
        #     btn.setMinimumHeight(80)
        #     btn.setMinimumWidth(100)
        #     btn.setMaximumHeight(150)
        #     btn.setMaximumWidth(150)
        #     self.slide_previews.append(btn)
        #     preview_layout.addWidget(btn)
        # layout.addWidget(preview_group)

        panel.setMinimumWidth(460)

        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.slide_image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        return panel

    def create_right_panel(self):
        panel = QGroupBox()
        panel.setObjectName("rightPanel")
        panel.setStyleSheet("#rightPanel { background-color: white; }")
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # 演示信息

        info_group = QGroupBox("")
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(0)
        info_layout.setContentsMargins(0, 0, 0, 0)

        info_title_layout = QHBoxLayout()
        info_title_layout.setSpacing(4)
        info_svg_widget = QSvgWidget("resources/icons/info.svg")
        info_svg_widget.setFixedSize(20, 20)
        info_title_label = QLabel("演示信息")
        info_title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-left: 1px;color: #1a1a1a")
        info_title_layout.addWidget(info_svg_widget)
        info_title_layout.addWidget(info_title_label)

        info_layout.addLayout(info_title_layout)
        info_layout.addSpacing(15)
        info_layout.addStretch()

        info_widget = QWidget()
        info_widget.setObjectName("infoWidget")
        info_widget.setStyleSheet("#infoWidget { background-color: #F5F5F5; }")
        info_widget_layout = QVBoxLayout(info_widget)
        info_widget_layout.setSpacing(0)
        info_widget_layout.setContentsMargins(0, 0, 0, 0)
        self.slide_count_label = QLabel("幻灯片总数: 25")
        self.current_page_label = QLabel("当前页码: 1/25")
        self.duration_label = QLabel("演示时长: 03:45")
        self.remain_label = QLabel("剩余时间: 12:15")
        info_widget_layout.addWidget(self.slide_count_label)
        info_widget_layout.addWidget(self.current_page_label)
        info_widget_layout.addWidget(self.duration_label)
        info_widget_layout.addWidget(self.remain_label)
        info_layout.addWidget(info_widget)
        layout.addWidget(info_group)

        # 操作记录
        record_group = QGroupBox("")
        record_layout = QVBoxLayout(record_group)
        record_layout.setSpacing(0)
        record_layout.setContentsMargins(0, 0, 0, 0)
        self.record_list = QVBoxLayout()

        # 顶部自定义标题栏
        record_title_layout = QHBoxLayout()
        record_title_layout.setSpacing(4)
        record_svg_widget = QSvgWidget("resources/icons/record-2.svg")
        record_svg_widget.setFixedSize(20, 20)
        record_title_label = QLabel("操作记录")
        record_title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-left: 1px;color: #1a1a1a")
        record_title_layout.addWidget(record_svg_widget)
        record_title_layout.addWidget(record_title_label)
        record_title_layout.addStretch()

        record_layout.addLayout(record_title_layout)
        record_layout.addSpacing(15)

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
        status_group = QGroupBox("")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(0)
        status_layout.setContentsMargins(0, 0, 0, 0)
        # 顶部自定义标题栏
        status_title_layout = QHBoxLayout()
        status_title_layout.setSpacing(4)
        status_svg_widget = QSvgWidget("resources/icons/status.svg")
        status_svg_widget.setFixedSize(20, 20)
        status_title_label = QLabel("状态提示")
        status_title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-left: 1px;color: #1a1a1a")
        status_title_layout.addWidget(status_svg_widget)
        status_title_layout.addWidget(status_title_label)
        status_layout.addLayout(status_title_layout)
        status_layout.addSpacing(15)
        status_layout.addStretch()  # 添加系统状态标签
        self.status_label = QLabel("系统就绪")
        self.status_label.setStyleSheet("background-color: #E8F5E9; color: #388E3C; border-radius: 6px; padding: 8px;")
        status_layout.addWidget(self.status_label)

        self.gesture_status_label = QLabel("")
        self.gesture_status_label.setStyleSheet(
            "background-color: #E8F5E9; color: #388E3C; border-radius: 6px; padding: 8px;")
        self.voice_status_label = QLabel("")
        self.voice_status_label.setStyleSheet(
            "background-color: #E3F2FD; color: #1976D2; border-radius: 6px; padding: 8px;")

        # 录像状态指示器
        self.recording_status_label = QLabel("")
        self.recording_status_label.setStyleSheet(
            "background-color: #FFF3E0; color: #F57C00; border-radius: 6px; padding: 8px;")
        self.recording_status_label.hide()  # 初始隐藏

        status_layout.addWidget(self.gesture_status_label)
        status_layout.addWidget(self.voice_status_label)
        status_layout.addWidget(self.recording_status_label)
        layout.addWidget(status_group)

        layout.addStretch()
        return panel

    def create_left_panel(self):
        panel = QGroupBox("")
        panel.setObjectName("leftPanel")
        panel.setStyleSheet("#leftPanel { background-color: white; }")
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # 播放控制
        control_group = QGroupBox("")
        main_vlayout = QVBoxLayout(control_group)
        main_vlayout.setSpacing(0)
        main_vlayout.setContentsMargins(0, 0, 0, 0)
        # 顶部自定义标题栏
        control_title_layout = QHBoxLayout()
        control_title_layout.setSpacing(4)
        control_svg_widget = QSvgWidget("resources/icons/设置.svg")
        control_svg_widget.setFixedSize(20, 20)
        control_title_label = QLabel("播放控制")
        control_title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-left: 1px;color: #1a1a1a")
        control_title_layout.addWidget(control_svg_widget)
        control_title_layout.addWidget(control_title_label)
        control_title_layout.addStretch()

        main_vlayout.addLayout(control_title_layout)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)

        self.start_btn = QPushButton("开始播放")
        self.start_btn.setIcon(QIcon("resources/icons/运行.svg"))
        self.start_btn.setIconSize(QSize(80, 20))
        self.start_btn.setMinimumHeight(28)
        self.start_btn.setMaximumWidth(100)
        self.start_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.start_btn.setStyleSheet("margin-left:0px;margin-right:0px;")

        control_layout.addWidget(self.start_btn)

        main_vlayout.addLayout(control_layout)
        layout.addWidget(control_group)

        # 手势控制
        gesture_group = QGroupBox("")
        gesture_layout = QVBoxLayout(gesture_group)
        gesture_layout.setSpacing(10)
        gesture_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部自定义标题栏
        gesture_title_layout = QHBoxLayout()
        gesture_title_layout.setSpacing(4)
        gesture_svg_widget = QSvgWidget("resources/icons/gesture.svg")
        gesture_svg_widget.setFixedSize(20, 20)
        gesture_title_label = QLabel("手势控制")
        gesture_title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-left: 1px;color: #1a1a1a")
        gesture_title_layout.addWidget(gesture_svg_widget)
        gesture_title_layout.addWidget(gesture_title_label)
        gesture_title_layout.addStretch()

        gesture_layout.addLayout(gesture_title_layout)

        # 手势功能映射
        mapping_group = QGroupBox("")
        mapping_group.setStyleSheet(
            "QGroupBox { margin-top: 10px; padding-top: 10px; border: none; ;background-color: #F5F5F5;}")
        mapping_layout = QFormLayout(mapping_group)
        mapping_layout.setSpacing(10)
        mapping_layout.setContentsMargins(0, 0, 0, 0)

        self.gesture_mappings = {}
        # 只包含后端实际支持的手势选项
        gestures = [
            "向左滑动",  # swipe_left - 后端支持
            "向右滑动",  # swipe_right - 后端支持
            "向上滑动",  # swipe_up - 后端支持
            "向下滑动",  # swipe_down - 后端支持
            "握拳",  # fist (静态手势) - 后端支持
            "张开手掌",  # open_hand (静态手势) - 后端支持
            "OK手势",  # ok (静态手势) - 后端支持
            "食指",  # point (静态手势) - 后端支持
            "双手手势",  # dual_hand - 后端支持
            "无"  # 禁用该功能
        ]
        actions = ["上一页", "下一页", "开始播放", "结束播放", "暂停", "继续"]

        # 从后端配置读取默认设置
        default_gestures = self.get_default_gesture_settings()

        for i, action in enumerate(actions):
            label = QLabel(f"{action}:")
            label.setStyleSheet("color: #222; font-size: 14px;")
            combo = QComboBox()
            combo.addItems(gestures)

            # 设置默认值
            default_gesture = default_gestures.get(action, gestures[i] if i < len(gestures) else "无")
            combo.setCurrentText(default_gesture)

            self.gesture_mappings[action] = combo
            mapping_layout.addRow(label, combo)

        gesture_layout.addWidget(mapping_group)

        # 检测间隔设置
        interval_group = QWidget()
        interval_layout = QFormLayout(interval_group)
        interval_layout.setSpacing(10)
        interval_layout.setContentsMargins(0, 0, 0, 0)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(50, 1000)
        self.interval_spin.setSingleStep(100)
        self.interval_spin.setValue(200)
        self.interval_spin.setSuffix(" ms")
        interval_layout.addRow("检测间隔:", self.interval_spin)
        gesture_layout.addWidget(interval_group)

        # 手势检测按钮
        self.gesture_checkbox = QCheckBox("启用手势识别")
        self.gesture_checkbox.setStyleSheet("QCheckBox {}")

        gesture_layout.addWidget(self.gesture_checkbox, alignment=Qt.AlignLeft)
        layout.addWidget(gesture_group)

        # 语音识别
        voice_group = QGroupBox("")
        voice_layout = QVBoxLayout(voice_group)
        voice_layout.setSpacing(10)
        voice_layout.setContentsMargins(0, 0, 0, 0)
        # 顶部自定义标题栏
        voice_title_layout = QHBoxLayout()
        voice_title_layout.setSpacing(4)
        voice_svg_widget = QSvgWidget("resources/icons/voice.svg")
        voice_svg_widget.setFixedSize(20, 20)
        voice_title_label = QLabel("语音识别")
        voice_title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-left: 1px;color: #1a1a1a")
        voice_title_layout.addWidget(voice_svg_widget)
        voice_title_layout.addWidget(voice_title_label)
        voice_title_layout.addStretch()

        voice_layout.addLayout(voice_title_layout)

        self.voice_label = QLabel("语音识别已启用\n等待语音指令...")
        self.voice_label.setStyleSheet("background-color: #F5F5F5; padding: 10px; border-radius: 5px;")
        voice_layout.addWidget(self.voice_label)

        voice_layout.addStretch()        # 语音识别按钮
        self.voice_checkbox = QCheckBox("启用语音识别")
        self.voice_checkbox.setStyleSheet("QCheckBox {}")

        voice_layout.addWidget(self.voice_checkbox, alignment=Qt.AlignLeft)
          # 关键词设置按钮
        keyword_layout = QHBoxLayout()
        keyword_layout.setContentsMargins(0, 5, 0, 5)
        keyword_layout.setSpacing(8)
        
        self.keyword_settings_btn = QPushButton("设置关键词")
        self.keyword_settings_btn.setFixedHeight(32)
        self.keyword_settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 12px;
                margin: 2px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:pressed {
                background-color: #d35400;
            }
        """)
        self.keyword_settings_btn.clicked.connect(self.show_keyword_settings)
        
        # 文稿导入按钮
        self.script_import_btn = QPushButton("导入文稿")
        self.script_import_btn.setFixedHeight(32)
        self.script_import_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 12px;
                margin: 2px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        self.script_import_btn.clicked.connect(self.show_script_import_dialog)
        
        keyword_layout.addWidget(self.keyword_settings_btn)
        keyword_layout.addWidget(self.script_import_btn)
        keyword_layout.addStretch()
        voice_layout.addLayout(keyword_layout)
        
        # 字幕显示按钮
        self.subtitle_checkbox = QCheckBox("显示AI字幕")
        self.subtitle_checkbox.setStyleSheet("QCheckBox {}")
        self.subtitle_checkbox.setEnabled(False)  # 默认禁用，需要先启用语音识别
        
        voice_layout.addWidget(self.subtitle_checkbox, alignment=Qt.AlignLeft)
        layout.addWidget(voice_group)

        # 添加弹性空间
        layout.addStretch()
        return panel

    # def update_video(self):
    #     """更新视频显示"""
    #     ret, frame = self.cap.read()
    #     if ret:
    #         # 处理帧
    #         frame = self.controller.process_frame(frame)

    #         # 转换颜色空间
    #         frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    #         # 转换为QImage
    #         h, w, ch = frame.shape
    #         bytes_per_line = ch * w
    #         qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

    #         # 更新预览标签
    #         self.preview_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
    #             self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
    #         ))

    def update_ppt_info(self):
        """更新PPT信息显示"""
        if self.controller.ppt_controller.is_active():
            # 更新幻灯片信息
            self.slide_count_label.setText(f"幻灯片总数: {self.controller.ppt_controller.get_status()['total_slides']}")
            self.current_page_label.setText(f"当前页码: {self.controller.ppt_controller.get_status()['current_slide']}")

            # 更新预览按钮状态
            for i, btn in enumerate(self.slide_previews):
                if i < len(self.slide_previews):
                    btn.setEnabled(True)
                    btn.clicked.connect(lambda x, idx=i + 1: self.jump_to_slide(idx))

    def jump_to_slide(self, slide_number: int):
        """跳转到指定幻灯片"""
        try:
            self.controller.jump_to_slide(slide_number)
            self.update_status(f"已跳转到第 {slide_number} 页")
        except Exception as e:
            self.handle_error(f"跳转失败: {str(e)}")

    def handle_error(self, error_message: str):
        """处理错误"""
        self.update_status(error_message, True)
        print(f"错误: {error_message}")

    def update_ppt_info(self):
        """更新PPT信息显示"""
        if self.controller.ppt_controller.is_active():
            # 更新幻灯片信息
            self.slide_count_label.setText(f"幻灯片总数: {self.controller.ppt_controller.get_status()['total_slides']}")
            self.current_page_label.setText(f"当前页码: {self.controller.ppt_controller.get_status()['current_slide']}")

            # 更新预览按钮状态
            for i, btn in enumerate(self.slide_previews):
                if i < len(self.slide_previews):
                    btn.setEnabled(True)
                    btn.clicked.connect(lambda x, idx=i + 1: self.jump_to_slide(idx))

    def jump_to_slide(self, slide_number: int):
        """跳转到指定幻灯片"""
        try:
            self.controller.jump_to_slide(slide_number)
            self.update_status(f"已跳转到第 {slide_number} 页")
        except Exception as e:
            self.handle_error(f"跳转失败: {str(e)}")

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        try:
            # 停止所有控制器
            if self.controller.ppt_controller.is_active():
                self.controller.exit_presentation()
            if hasattr(self.controller, 'gesture_controller') and hasattr(self.controller.gesture_controller,
                                                                          'running'):
                self.controller.gesture_controller.running = False
            event.accept()
        except Exception as e:
            self.handle_error(f"关闭时发生错误: {str(e)}")
            event.accept()

    def load_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F5F5;
            }

            QWidget {
                color: #333333;  
            }
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                margin-top: 15px;
                padding: 15px;
                background-color:white;
                color: #1a1a1a;  
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #1a1a1a;
            }
            #previewGroup { 
                background-color: white !important;
                border-radius: 10px;
                color: #333;
            }
            #previewGroup:title {
                color: #333;
            }
            
            QPushButton {
                background-color: #165DFF;
                color: white;
                border: none;
                padding: 6px 12px;
                margin: 8px;
                border-radius: 8px;
                font-size: 14px;
                min-height: 50px;
                font-weight: bold;
        
            }
            QPushButton#windowControlButton {
                background: none;
                border-radius: 4px;
                padding: 0px;
                margin: 0px;
                min-height: 28px;
                min-width: 28px;
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
            QLabel#previewimage {
                background: white;
                border-radius: 4px;
                padding: 0px;
                margin: 0px;    
                min-height: 240px;
                min-width: 427px;
            }
            QSpinBox, QComboBox {
                padding: 2px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                min-height: 16px;
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
            }
            QSpinBox::up-arrow {
                image: url(resources/icons/up.svg);
            }
            QSpinBox::down-arrow {
                image: url(resources/icons/down.svg);
            }
            QCheckBox {
                margin-left: 5px;
                margin-right: 5px;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #aaa;
                background: #F5F5F5;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                image: url(resources/icons/check.svg);
                border: 2px solid #FAB81A;
                background: #FAB81A;
                border-radius: 4px;
            }
                           
        """)

    def get_default_gesture_settings(self):
        """从后端配置获取默认手势设置"""
        try:
            # 创建后端到前端的映射
            backend_to_frontend_action = {
                "prev_slide": "上一页",
                "next_slide": "下一页",
                "fullscreen": "开始播放",
                "exit": "结束播放",
                "pause": "暂停"
            }
            backend_to_frontend_gesture = {
                "swipe_left": "向左滑动",
                "swipe_right": "向右滑动",
                "swipe_up": "向上滑动",
                "swipe_down": "向下滑动",
                "fist": "握拳",
                "open_hand": "张开手掌",
                "ok": "OK手势",
                "point": "食指",
                "dual_hand": "双手手势"
            }

            default_settings = {}

            # 如果有手势控制器，从配置中读取
            if hasattr(self.controller, 'gesture_controller') and hasattr(self.controller.gesture_controller,
                                                                          'gesture_configs'):
                configs = self.controller.gesture_controller.gesture_configs

                for backend_action, config in configs.items():
                    frontend_action = backend_to_frontend_action.get(backend_action)
                    if frontend_action:
                        if config.enabled:
                            if config.gesture_type.value == "dynamic" and config.motion_pattern:
                                frontend_gesture = backend_to_frontend_gesture.get(config.motion_pattern, "自定义手势")
                                default_settings[frontend_action] = frontend_gesture
                            elif config.gesture_type.value == "static" and config.finger_pattern:
                                # 根据手指模式确定手势
                                if config.finger_pattern == [0, 0, 0, 0, 0]:
                                    default_settings[frontend_action] = "握拳"
                                elif config.finger_pattern == [1, 1, 1, 1, 1]:
                                    default_settings[frontend_action] = "张开手掌"
                                elif config.finger_pattern == [1, 1, 0, 0, 0]:
                                    default_settings[frontend_action] = "OK手势"
                                elif config.finger_pattern == [0, 1, 0, 0, 0]:
                                    default_settings[frontend_action] = "食指"
                                else:
                                    default_settings[frontend_action] = "无"
                            elif config.gesture_type.value == "dual_hand":
                                default_settings[frontend_action] = "双手手势"
                            else:
                                default_settings[frontend_action] = "无"
                        else:
                            default_settings[frontend_action] = "无"
            # 确保所有前端动作都有默认值
            all_actions = ["上一页", "下一页", "开始播放", "结束播放", "暂停", "继续"]
            for action in all_actions:
                if action not in default_settings:
                    default_settings[action] = "无"

            # 根据实际的gesture_config.json，默认启用的是：
            # next_slide (下一页): swipe_right
            # prev_slide (上一页): swipe_left
            # exit (退出): dual_hand
            # if not any(v != "无" for v in default_settings.values()):
            default_settings = {
                "上一页": "向左滑动",  # prev_slide enabled=true
                "下一页": "向右滑动",  # next_slide enabled=true
                "开始播放": "无",  # fullscreen enabled=false
                "结束播放": "双手手势",  # exit enabled=true, dual_hand
                "暂停": "无",  # pause enabled=false                "继续": "无"             # 没有对应的后端配置
            }

            return default_settings

        except Exception as e:
            print(f"获取默认手势设置失败: {e}")
            # 返回实际的默认配置：根据gesture_config.json
            return {
                "上一页": "向左滑动",  # prev_slide enabled=true
                "下一页": "向右滑动",  # next_slide enabled=true
                "开始播放": "无",  # fullscreen enabled=false
                "结束播放": "双手手势",  # exit enabled=true, dual_hand
                "暂停": "无",  # pause enabled=false
                "继续": "无"  # 没有对应的后端配置
            }

    def toggle_subtitle_display(self, enabled: bool):
        """切换字幕显示状态"""
        print(f"🔧 DEBUG: toggle_subtitle_display 被调用, enabled={enabled}")
        print(f"🔧 DEBUG: 语音识别状态: {self.voice_checkbox.isChecked()}")
        print(f"🔧 DEBUG: 悬浮窗存在: {hasattr(self, 'floating_window') and self.floating_window is not None}")
        
        if enabled and not self.voice_checkbox.isChecked():
            # 如果语音识别未开启，不允许开启字幕
            self.subtitle_checkbox.blockSignals(True)
            self.subtitle_checkbox.setChecked(False)
            self.subtitle_checkbox.blockSignals(False)
            self.update_status("请先启用语音识别才能显示字幕", is_error=True)
            print("❌ DEBUG: 语音识别未开启，拒绝启用字幕")
            return

        # 通知悬浮窗更新字幕显示状态
        if hasattr(self, 'floating_window') and self.floating_window is not None:
            print(f"📡 DEBUG: 正在通知悬浮窗更新字幕状态: {enabled}")
            self.floating_window.set_subtitle_display_enabled(enabled)
        else:
            print("⚠️ DEBUG: 悬浮窗不存在，无法设置字幕状态")

        status_text = "字幕显示已开启" if enabled else "字幕显示已关闭"
        self.update_status(status_text)
        print(f"✅ DEBUG: 字幕显示状态更新完成: {status_text}")
