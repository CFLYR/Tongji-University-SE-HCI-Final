from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QStackedWidget, QFileDialog,
                               QSpinBox, QComboBox, QGroupBox, QFormLayout, QSpacerItem,
                               QSizePolicy, QCheckBox, QDialog,QTextEdit,QDialogButtonBox,
                               QFrame, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QIcon, QPixmap, QImage, QColor
from PySide6.QtCore import QSize
from PySide6.QtSvgWidgets import QSvgWidget
from main_controller import MainController
from ppt_floating_window import PPTFloatingWindow
from keyword_manager import KeywordManagerDialog
from script_manager import ScriptImportDialog, ScriptManager
from ppt_content_extractor import PPTContentExtractor
from ppt_ai_advisor import PPTAIAdvisor
from help_window import HelpWindow
import cv2
import numpy as np
import win32com.client
import os
import threading
import traceback

class MainWindow(QMainWindow):
    # 在类级别定义信号
    ai_output_updated = Signal(str)
    ai_button_reset = Signal()
    status_updated = Signal(str, bool)
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("大学生Presentation助手")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMinimumSize(1300, 850)
        
        # 设置初始窗口位置为屏幕中间
        self._center_window()        # 初始化主控制器
        self.controller = MainController()
        self.controller.set_main_window(self)  # 设置主窗口引用
          # 初始化语音关键词列表
        self.voice_keywords = ["下一页"]        # 初始化文稿管理器
        self.script_manager = ScriptManager()
        
        # 初始化PPT内容提取器和AI顾问
        self.ppt_extractor = PPTContentExtractor()
        self.ai_advisor = PPTAIAdvisor()
        self.current_ppt_content = None  # 当前PPT的内容
        
        # 文稿跟随状态
        self.script_follow_enabled = False
        self.current_script_position = 0  # 当前演讲到的位置（行号，从0开始）
        self.imported_script_lines = []  # 导入的文稿行列表
        
        # 存储当前PPT信息
        self.current_ppt_slide_count = 0        # 创建主窗口部件
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
    
    def _center_window(self):
        """将窗口居中显示"""
        from PySide6.QtGui import QGuiApplication
        
        # 获取屏幕几何信息
        screen = QGuiApplication.primaryScreen().geometry()
        
        # 设置初始窗口大小
        window_width = 1400
        window_height = 900
        self.resize(window_width, window_height)
        
        # 计算居中位置
        x = (screen.width() - window_width) // 2
        y = (screen.height() - window_height) // 2
        
        # 设置窗口位置
        self.move(x, y)
        

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
        
        self.ai_output_updated.connect(self._update_ai_output_direct)
        self.ai_button_reset.connect(self._reset_ai_button_direct)
        self.status_updated.connect(self._update_status_direct)
        

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

        self.update_status("PPT预览加载完成", False)
        pixmap = QPixmap(img_path)
        self.slide_image_label.setPixmap(pixmap)
        # 显示文件名
        ppt_path = self.file_path_label.text()
        ppt_filename = os.path.basename(ppt_path)
        self.slide_filename_label.setText(f"PPT文件名：{ppt_filename}")
        self.slide_filename_label.show()
        
        # 恢复按钮状态（虽然按钮已隐藏，但为了保持状态一致性）
        self.open_ppt_btn.setText("   打开PPT文件")
        self.open_ppt_btn.setEnabled(True)

    def select_ppt_file(self):
        """选择PPT文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择PPT文件",
            "",
            "PowerPoint Files (*.ppt *.pptx);;All Files (*.*)"
        )
        if file_path:
            # 更新按钮文本为加载中状态
            self.open_ppt_btn.setText("   正在加载中...")
            self.open_ppt_btn.setEnabled(False)
            
            # 强制刷新UI
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            
            self.update_status("正在加载PPT预览...")
            self.file_path_label.setText(file_path)
            self.controller.ppt_controller.current_ppt_path = file_path
    
            # 使用QTimer延迟执行，确保UI更新
            QTimer.singleShot(100, lambda: self._load_ppt_preview(file_path))
    
    def _load_ppt_preview(self, file_path):
        """在后台加载PPT预览"""
        try:
            img_path = self.export_first_slide_as_image(file_path)
            self.show_ppt_first_slide_preview(img_path)
            
            # 获取并更新PPT信息
            self._update_ppt_info_from_file(file_path)
            
            # 启用AI优化建议按钮
            self.ai_chat_btn.setEnabled(True)
            ##print(f"✅ AI优化建议按钮已启用，PPT路径: {file_path}")
            
        except Exception as e:
            # 如果加载失败，恢复按钮状态
            self.open_ppt_btn.setText("   打开PPT文件")
            self.open_ppt_btn.setEnabled(True)
            self.open_ppt_btn.show()  # 确保按钮重新显示
            self.handle_error(f"加载PPT预览失败: {str(e)}")
            
    def _update_ppt_info_from_file(self, file_path):
        """从PPT文件获取并更新演示信息"""
        try:
            from pptx import Presentation
            import os
            
            # 使用python-pptx库读取PPT文件信息
            prs = Presentation(file_path)
            slide_count = len(prs.slides)
            
            # 获取文件名
            file_name = os.path.basename(file_path)
            
            # 存储幻灯片总数
            self.current_ppt_slide_count = slide_count
            
            # 更新演示信息显示
            self.slide_count_value.setText(str(slide_count))
            self.current_page_value.setText("1/{}".format(slide_count))
            self.duration_value.setText("00:00:00")  # 重置演示时长
            
            # 更新状态
            self.update_status(f"已加载PPT文件：{file_name}")
            #print(f"✅ PPT信息已更新：{file_name}，共{slide_count}张幻灯片")
            
        except Exception as e:
            print(f"❌ 获取PPT信息失败: {str(e)}")
            # 如果获取信息失败，设置默认值
            self.slide_count_value.setText("0")
            self.current_page_value.setText("0/0")
            self.duration_value.setText("00:00:00")
            
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
                return
            
            # 检查是否至少勾选了一项功能（手势识别或语音识别）
            gesture_enabled = hasattr(self, 'gesture_checkbox') and self.gesture_checkbox.isChecked()
            voice_enabled = hasattr(self, 'voice_checkbox') and self.voice_checkbox.isChecked()
            
            if not gesture_enabled and not voice_enabled:
                self.update_status("请至少勾选一项功能", is_error=True)
                return
                
            # 开始播放
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
                            # 让悬浮窗加载完整的文稿内容
                            if hasattr(self.floating_window, 'load_imported_script'):
                                success = self.floating_window.load_imported_script()
                                # if success:
                                #     #print("✅ 已将完整文稿加载到悬浮窗")
                                # else:
                                #     # 如果悬浮窗加载失败，使用预览文本
                                #     first_line = self.script_manager.get_line_by_number(1)
                                #     if first_line:
                                #         self.floating_window.set_script_text(f"📄 演讲文稿已加载\n{first_line[:50]}...")
                            else:
                                # 如果悬浮窗没有load_imported_script方法，使用预览文本
                                first_line = self.script_manager.get_line_by_number(1)
                                if first_line:
                                    self.floating_window.set_script_text(f"📄 演讲文稿已加载\n{first_line[:50]}...")
                        else:
                            self.floating_window.set_script_text("📄 文稿展示区\n请先导入演讲文稿")
                    
                    # 如果有演讲稿管理器，设置到悬浮窗
                    if hasattr(self.controller, 'speech_manager'):
                        self.floating_window.set_speech_manager(self.controller.speech_manager)                    # 同步当前字幕显示状态到悬浮窗
                    if hasattr(self, 'subtitle_checkbox') and self.subtitle_checkbox.isChecked():
                        #print("🔄 同步字幕显示状态到悬浮窗")
                        self.floating_window.set_subtitle_display_enabled(True)
                    
                    # 同步语音识别功能状态和关键词到悬浮窗
                    if hasattr(self, 'voice_checkbox') and self.voice_checkbox.isChecked():
                        #print("🔄 同步语音识别功能状态到悬浮窗")
                        if hasattr(self.floating_window, 'set_voice_recognition_enabled'):
                            self.floating_window.set_voice_recognition_enabled(True)
                        if hasattr(self.floating_window, 'set_voice_keywords'):
                            self.floating_window.set_voice_keywords(self.voice_keywords)
                            print(f" 已将关键词同步到悬浮窗: {self.voice_keywords}")

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
        """切换语音识别功能可用状态（不直接启动语音识别）"""
        print(f"🎙️ 设置语音识别功能可用状态: {enabled}")
        
        # 更新状态显示
        self.update_status(f"语音识别功能已{'启用' if enabled else '禁用'}")
        
        # 控制字幕复选框和文稿跟随复选框的可用性
        self.subtitle_checkbox.setEnabled(enabled)
        self.script_follow_checkbox.setEnabled(enabled)
        
        if not enabled:
            # 禁用语音识别功能时，也禁用字幕显示和文稿跟随
            self.subtitle_checkbox.blockSignals(True)
            self.subtitle_checkbox.setChecked(False)
            self.subtitle_checkbox.blockSignals(False)
            
            self.script_follow_checkbox.blockSignals(True)
            self.script_follow_checkbox.setChecked(False)
            self.script_follow_checkbox.blockSignals(False)
            
            # 如果悬浮窗存在，停止语音识别并禁用功能
            if hasattr(self, 'floating_window') and self.floating_window:
                if hasattr(self.floating_window, 'stop_voice_recognition'):
                    self.floating_window.stop_voice_recognition()
                if hasattr(self.floating_window, 'set_voice_recognition_enabled'):
                    self.floating_window.set_voice_recognition_enabled(False)
        else:
            # 启用语音识别功能时，传递状态和关键词到悬浮窗
            if hasattr(self, 'floating_window') and self.floating_window:
                # 设置语音识别功能可用状态
                if hasattr(self.floating_window, 'set_voice_recognition_enabled'):
                    self.floating_window.set_voice_recognition_enabled(True)
                
                # 传递关键词到悬浮窗
                if hasattr(self.floating_window, 'set_voice_keywords'):
                    self.floating_window.set_voice_keywords(self.voice_keywords)
                    print(f" 已将关键词传递到悬浮窗: {self.voice_keywords}")

    def show_keyword_settings(self):
        """显示关键词设置对话框"""
        dialog = KeywordManagerDialog(self, self.voice_keywords)
        
        def on_keywords_updated(keywords):
            self.voice_keywords = keywords
            self.update_status(f"关键词已更新，共 {len(keywords)} 个")
            print(f" 语音关键词已更新: {keywords}")
        
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
            
            # 尝试加载已导入的文稿到文稿管理器
            success = self.script_manager.load_imported_script()
            if success:
                # 更新文稿跟随相关变量
                self.imported_script_lines = self.script_manager.get_lines()
                if self.script_follow_enabled:
                    self.current_script_position = 0  # 重置位置
                    self.update_script_display()
                
                # 如果悬浮窗存在，更新悬浮窗中的文稿显示
                if hasattr(self, 'floating_window') and self.floating_window:
                    # 让悬浮窗加载完整的文稿内容
                    if hasattr(self.floating_window, 'load_imported_script'):
                        success = self.floating_window.load_imported_script()
                        # if success:
                        #     #print("✅ 完整文稿已同步到悬浮窗")
                        # else:
                        #     # 如果加载失败，使用预览文本
                        #     first_line = self.script_manager.get_line_by_number(1)
                        #     if first_line:
                        #         self.floating_window.set_script_text(f"📄 文稿已导入\n{first_line[:50]}...")
                        #     else:
                        #         self.floating_window.set_script_text("📄 文稿已导入，可以开始演示")
                    else:
                        # 如果悬浮窗没有load_imported_script方法，使用预览文本
                        first_line = self.script_manager.get_line_by_number(1)
                        if first_line:
                            self.floating_window.set_script_text(f"📄 文稿已导入\n{first_line[:50]}...")
                        else:
                            self.floating_window.set_script_text("📄 文稿已导入，可以开始演示")
            
            self.update_status(f"文稿导入完成，关键词已更新，共 {len(keywords)} 个")
            print(f"📄 从文稿导入的关键词已更新: {keywords}")
        
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
                    # 让悬浮窗加载完整的文稿内容
                    if hasattr(self.floating_window, 'load_imported_script'):
                        success = self.floating_window.load_imported_script()
                        # if success:
                        #     #print("✅ 完整文稿已同步到悬浮窗")
                        # else:
                        #     # 如果加载失败，使用预览文本
                        #     first_line = self.script_manager.get_line_by_number(1)
                        #     if first_line:
                        #         self.floating_window.set_script_text(f"📄 文稿已导入\n{first_line[:50]}...")
                        #     else:
                        #         self.floating_window.set_script_text("📄 文稿已导入，可以开始演示")
                    else:
                        # 如果悬浮窗没有load_imported_script方法，使用预览文本
                        first_line = self.script_manager.get_line_by_number(1)
                        if first_line:
                            self.floating_window.set_script_text(f"📄 文稿已导入\n{first_line[:50]}...")
                        else:
                            self.floating_window.set_script_text("📄 文稿已导入，可以开始演示")
            
            self.update_status(f"文稿导入完成，关键词已更新，共 {len(keywords)} 个")
            print(f"📄 从文稿导入的关键词已更新: {keywords}")
        
        dialog.keywords_updated.connect(on_keywords_updated)
        dialog.exec()

    def show_help_window(self):
        """显示帮助窗口"""
        try:
            help_window = HelpWindow(self)
            help_window.exec()
            print("📖 帮助窗口已显示")
        except Exception as e:
            self.update_status(f"显示帮助窗口失败: {str(e)}", is_error=True)
            print(f"❌ 显示帮助窗口失败: {e}")


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
        self.duration_value.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    # 信号处理函数    
    def on_ppt_file_opened(self, file_path: str):
        """PPT文件打开处理"""
        self.file_path_label.setText(file_path)
        self.start_btn.setEnabled(True)
        self.ai_chat_btn.setEnabled(True)  # 启用AI按钮
        self.update_status("PPT文件已选择")

    def on_presentation_started(self):
        """演示开始处理"""
        self.start_btn.setText("暂停")
        self.update_status("正在播放PPT...")
        
        # 重置当前页码为1
        if hasattr(self, 'current_ppt_slide_count') and self.current_ppt_slide_count > 0:
            self.current_page_value.setText(f"1/{self.current_ppt_slide_count}")
        else:
            self.current_page_value.setText("1")

    def on_presentation_stopped(self):
        """演示停止处理"""
        self.start_btn.setText("播放")
        self.update_status("演示已停止")
        
        # 重置演示时长
        self.duration_value.setText("00:00:00")

    def on_slide_changed(self, slide_number: int):
        """幻灯片切换处理"""
        # 使用存储的幻灯片总数
        if hasattr(self, 'current_ppt_slide_count') and self.current_ppt_slide_count > 0:
            total_slides = self.current_ppt_slide_count
            self.current_page_value.setText(f"{slide_number}/{total_slides}")
            # 同步信息到悬浮窗
            if (hasattr(self, 'floating_window') and self.floating_window and 
                hasattr(self.floating_window, 'update_slide_info')):
                self.floating_window.update_slide_info(slide_number, total_slides)
        else:
            # 如果没有幻灯片总数信息，只显示当前页码
            self.current_page_value.setText(f"{slide_number}")
            if (hasattr(self, 'floating_window') and self.floating_window and 
                hasattr(self.floating_window, 'update_slide_info')):
                self.floating_window.update_slide_info(slide_number, 1)

    def on_gesture_detection_started(self):
        """手势检测开始处理"""
        self.gesture_status_label.setText("✔ 手势识别已启用")

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

        print(f"字幕更新: {subtitle_text}")

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
        icon_label.setPixmap(QIcon("resources/icons/diannao.svg").pixmap(24, 24))
        icon_label.setFixedSize(28, 28)
        icon_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title_label = QLabel("Presentation助手")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #5B5BF6;")
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

        # # 右侧：按钮
        # btn_open = QPushButton()
        # btn_open.setObjectName("windowControlButton")
        # btn_open.setIcon(QIcon("resources/icons/ppt.svg"))
        # btn_open.setFixedHeight(28)
        # btn_open.setCursor(Qt.PointingHandCursor)

        # btn_setting = QPushButton()
        # btn_setting.setObjectName("windowControlButton")
        # btn_setting.setIcon(QIcon("resources/icons/tiaojie.svg"))
        # btn_setting.setFixedHeight(28)
        # btn_setting.setCursor(Qt.PointingHandCursor)

        btn_help = QPushButton()
        btn_help.setObjectName("windowControlButton")
        btn_help.setIcon(QIcon("resources/icons/help.svg"))
        btn_help.setFixedHeight(28)
        btn_help.setCursor(Qt.PointingHandCursor)
        btn_help.clicked.connect(self.show_help_window)

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
        # right_layout.addWidget(btn_open)
        # right_layout.addWidget(btn_setting)
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
        panel.setStyleSheet("""
            #centerPanel {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 180, 0, 30)

        # 标题
        self.center_title = QLabel("PPT演示内容预览")
        self.center_title.setAlignment(Qt.AlignCenter)
        self.center_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1A3A8F; font-family: 'Inter', 'Microsoft YaHei', Arial, sans-serif;")
        layout.addWidget(self.center_title)

        # 提示
        self.center_tip = QLabel("请导入或选择一个PPT文件开始播放")
        self.center_tip.setAlignment(Qt.AlignCenter)
        self.center_tip.setStyleSheet("color: #9E9E9E; font-size: 16px; font-family: 'Inter', 'Microsoft YaHei', Arial, sans-serif;")
        layout.addWidget(self.center_tip)

        # 文件路径显示
        self.file_path_label = QLabel("")
        self.file_path_label.setAlignment(Qt.AlignCenter)
        self.file_path_label.setStyleSheet("color: #9E9E9E; font-size: 14px; font-family: 'Inter', 'Microsoft YaHei', Arial, sans-serif;")
        layout.addWidget(self.file_path_label)

        # 打开PPT按钮
        self.open_ppt_btn = QPushButton("   打开PPT文件")
        self.open_ppt_btn.setIcon(QIcon("resources/icons/ppt.svg"))
        self.open_ppt_btn.setIconSize(QSize(24, 24))
        self.open_ppt_btn.setFixedWidth(220)
        self.open_ppt_btn.setFixedHeight(50)
        
        # 设置按钮字体
        from PySide6.QtGui import QFont
        button_font = QFont()
        button_font.setFamily("Microsoft YaHei")  # 微软雅黑
        button_font.setPointSize(14)  # 字体大小
        button_font.setBold(True)  # 粗体
        self.open_ppt_btn.setFont(button_font)
        
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
        self.slide_filename_label.setStyleSheet("color: #9E9E9E; font-size: 15px; font-family: 'Inter', 'Microsoft YaHei', Arial, sans-serif; margin-top: 8px;")
        self.slide_filename_label.hide()
        layout.addWidget(self.slide_filename_label)
        layout.addStretch()

        panel.setMinimumWidth(460)

        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.slide_image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        return panel

    def create_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)  # 减少卡片间距
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建各个卡片 - 为AI优化建议分配更多空间
        layout.addWidget(self.create_card_widget(self.create_info_content()), 0)  # 不拉伸
        layout.addWidget(self.create_card_widget(self.create_status_content()), 0)  # 不拉伸
        layout.addWidget(self.create_card_widget(self.create_ai_content()), 1)  # 拉伸因子为1，占用剩余空间
        
        return panel

    def create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(18)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.create_card_widget(self.create_play_control_content()))
        layout.addWidget(self.create_card_widget(self.create_gesture_control_content()))
        layout.addWidget(self.create_card_widget(self.create_voice_control_content()))
        layout.addStretch()
        return panel

    def create_card_widget(self, content_widget):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #fff;
                border-radius: 14px;
                border: none;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 25))
        card.setGraphicsEffect(shadow)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(content_widget)
        # 设置卡片的尺寸策略，允许垂直方向拉伸
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        return card

    def create_play_control_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)
        # 标题区
        title_layout = QHBoxLayout()
        icon = QSvgWidget("resources/icons/播放.svg")
        icon.setFixedSize(20, 20)
        title = QLabel("播放控制")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #23213A;")
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        # 内容区
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        self.start_btn = QPushButton("开始播放")
        self.start_btn.setIcon(QIcon("resources/icons/运行.svg"))
        self.start_btn.setIconSize(QSize(16, 16))
        self.start_btn.setFixedHeight(32)
        self.start_btn.setMinimumWidth(120)
        self.start_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 0px 16px;
            }
            QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
            QPushButton:pressed {
                background-color: #E3E6F5;
            }
        """)
        btn_layout.addWidget(self.start_btn)
        layout.addLayout(btn_layout)
        return widget

    def create_gesture_control_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)
        # 标题区
        title_layout = QHBoxLayout()
        icon = QSvgWidget("resources/icons/gesture.svg")
        icon.setFixedSize(20, 20)
        title = QLabel("手势控制")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #23213A;")
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        # 内容区
        mapping_group = QGroupBox("")
        mapping_group.setStyleSheet("QGroupBox { margin-top: 8px; padding: 12px; border: none; background-color: transparent; }")
        mapping_layout = QFormLayout(mapping_group)
        mapping_layout.setSpacing(12)
        mapping_layout.setContentsMargins(0, 0, 0, 0)
        self.gesture_mappings = {}
        gestures = ["向左滑动", "向右滑动", "向上滑动", "向下滑动", "握拳", "张开手掌", "OK手势", "食指", "双手手势", "无"]
        actions = ["上一页", "下一页", "开始播放", "结束播放", "暂停", "继续"]
        default_gestures = self.get_default_gesture_settings()
        for i, action in enumerate(actions):
            label = QLabel(f"{action}:")
            label.setStyleSheet("color: #666; font-size: 13px;")
            label.setFixedWidth(65)
            combo = QComboBox()
            combo.addItems(gestures)
            combo.setFixedHeight(28)
            combo.setEditable(True)
            combo.lineEdit().setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
            combo.lineEdit().setReadOnly(True)
            combo.setStyleSheet("QComboBox { text-align: center; font-size: 13px; }")
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            combo.setMinimumContentsLength(6)
            default_gesture = default_gestures.get(action, gestures[i] if i < len(gestures) else "无")
            combo.setCurrentText(default_gesture)
            self.gesture_mappings[action] = combo
            row_layout = QHBoxLayout()
            row_layout.setAlignment(Qt.AlignVCenter)
            row_layout.addWidget(label)
            row_layout.addWidget(combo)
            mapping_layout.addRow(row_layout)
        layout.addWidget(mapping_group)
        # 检测间隔
        interval_group = QWidget()
        interval_layout = QHBoxLayout(interval_group)
        interval_layout.setSpacing(12)
        interval_layout.setContentsMargins(0, 0, 0, 0)
        
        interval_label = QLabel("检测间隔:")
        interval_label.setStyleSheet("color: #666; font-size: 13px;")
        interval_label.setFixedWidth(65)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(50, 1000)
        self.interval_spin.setSingleStep(100)
        self.interval_spin.setValue(200)
        self.interval_spin.setSuffix(" ms")
        self.interval_spin.setFixedHeight(28)
        self.interval_spin.setStyleSheet("""
            QSpinBox {
                background-color: white;
                border: 1px solid #E3E6F5;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
                color: #23213A;
            }
            QSpinBox:focus {
                border-color: #5B5BF6;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                background: transparent;
                width: 16px;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 8px;
                height: 8px;
            }
        """)
        
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spin)
        interval_layout.addStretch()
        layout.addWidget(interval_group)
        # 手势检测checkbox
        gesture_switch_layout = QHBoxLayout()
        gesture_switch_layout.setContentsMargins(0, 0, 0, 0)
        gesture_label = QLabel("启用手势识别")
        gesture_label.setStyleSheet("font-size: 14px; color: #23213A;")
        self.gesture_checkbox = QCheckBox()
        #self.gesture_checkbox.setObjectName("switchCheckBox")
        gesture_switch_layout.addWidget(gesture_label)
        gesture_switch_layout.addStretch()
        gesture_switch_layout.addWidget(self.gesture_checkbox)
        layout.addLayout(gesture_switch_layout)
        return widget

    def create_voice_control_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)
        # 标题区
        title_layout = QHBoxLayout()
        icon = QSvgWidget("resources/icons/voice.svg")
        icon.setFixedSize(20, 20)
        title = QLabel("语音识别")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #23213A;")
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        # 内容区（复用原有语音识别内容）
        self.voice_label = QLabel("语音识别已启用\n等待语音指令...")
        self.voice_label.setStyleSheet("background-color: #F8F9FA; padding: 12px; border-radius: 8px; font-size: 13px; color: #666; line-height: 1.4;")
        layout.addWidget(self.voice_label)
        # 启用语音识别开关
        voice_switch_layout = QHBoxLayout()
        voice_switch_layout.setContentsMargins(0, 0, 0, 0)
        voice_label = QLabel("启用语音识别")
        voice_label.setStyleSheet("font-size: 14px; color: #23213A;")
        self.voice_checkbox = QCheckBox()
        #self.voice_checkbox.setObjectName("switchCheckBox")
        voice_switch_layout.addWidget(voice_label)
        voice_switch_layout.addStretch()
        voice_switch_layout.addWidget(self.voice_checkbox)
        layout.addLayout(voice_switch_layout)
        keyword_layout = QHBoxLayout()
        keyword_layout.setContentsMargins(0, 4, 0, 4)
        keyword_layout.setSpacing(10)
        self.keyword_settings_btn = QPushButton("设置关键词")
        self.keyword_settings_btn.setFixedHeight(30)
        self.keyword_settings_btn.setMinimumWidth(85)
        self.keyword_settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                padding: 0px 12px;
            }
            QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
            QPushButton:pressed {
                background-color: #E3E6F5;
            }
            QPushButton:disabled {
                background-color: #E3E6F5;
                color: #8B8BA7;
            }
        """)
        self.keyword_settings_btn.clicked.connect(self.show_keyword_settings)
        self.script_import_btn = QPushButton("导入文稿")
        self.script_import_btn.setFixedHeight(30)
        self.script_import_btn.setMinimumWidth(85)
        self.script_import_btn.setStyleSheet("""
            QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                padding: 0px 12px;
            }
            QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
            QPushButton:pressed {
                background-color: #E3E6F5;
            }
            QPushButton:disabled {
                background-color: #E3E6F5;
                color: #8B8BA7;
            }
        """)
        self.script_import_btn.clicked.connect(self.show_script_import_dialog)
        keyword_layout.addWidget(self.keyword_settings_btn)
        keyword_layout.addWidget(self.script_import_btn)
        layout.addLayout(keyword_layout)
        # 显示AI字幕开关
        subtitle_switch_layout = QHBoxLayout()
        subtitle_switch_layout.setContentsMargins(0, 0, 0, 0)
        subtitle_label = QLabel("显示AI字幕")
        subtitle_label.setStyleSheet("font-size: 14px; color: #23213A;")
        self.subtitle_checkbox = QCheckBox()
        #self.subtitle_checkbox.setObjectName("switchCheckBox")
        self.subtitle_checkbox.setEnabled(False)
        subtitle_switch_layout.addWidget(subtitle_label)
        subtitle_switch_layout.addStretch()
        subtitle_switch_layout.addWidget(self.subtitle_checkbox)
        layout.addLayout(subtitle_switch_layout)
        # 启用文稿跟随开关
        script_switch_layout = QHBoxLayout()
        script_switch_layout.setContentsMargins(0, 0, 0, 0)
        script_label = QLabel("启用文稿跟随")
        script_label.setStyleSheet("font-size: 14px; color: #23213A;")
        self.script_follow_checkbox = QCheckBox()
        #self.script_follow_checkbox.setObjectName("switchCheckBox")
        self.script_follow_checkbox.setEnabled(False)
        self.script_follow_checkbox.toggled.connect(self.toggle_script_follow)
        script_switch_layout.addWidget(script_label)
        script_switch_layout.addStretch()
        script_switch_layout.addWidget(self.script_follow_checkbox)
        layout.addLayout(script_switch_layout)
        return widget

    def create_info_content(self):
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)  # 固定高度
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题区
        title_layout = QHBoxLayout()
        icon = QSvgWidget("resources/icons/info.svg")
        icon.setFixedSize(20, 20)
        title = QLabel("演示信息")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #23213A;")
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 内容区域
        info_widget = QWidget()
        info_widget.setObjectName("infoWidget")
        info_widget.setStyleSheet("#infoWidget { background-color: white; border-radius: 8px; padding: 16px; }")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建标签
        self.slide_count_label = QLabel("幻灯片总数:")
        self.slide_count_value = QLabel("0")
        self.current_page_label = QLabel("当前页码:")
        self.current_page_value = QLabel("0/0")
        self.duration_label = QLabel("演示时长:")
        self.duration_value = QLabel("00:00:00")
        
        # 设置标签样式
        label_style = "color: #888; font-size: 13px; font-weight: normal;"
        value_style = "color: #222; font-size: 14px; font-weight: bold;"
        
        for label in [self.slide_count_label, self.current_page_label, self.duration_label]:
            label.setStyleSheet(label_style)
        for value in [self.slide_count_value, self.current_page_value, self.duration_value]:
            value.setStyleSheet(value_style)
        
        # 第一行：幻灯片总数和当前页码
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(0)
        
        # 左半部分：幻灯片总数
        left_layout = QVBoxLayout()
        left_layout.setSpacing(2)
        left_layout.addWidget(self.slide_count_label)
        left_layout.addWidget(self.slide_count_value)
        
        # 右半部分：当前页码
        right_layout = QVBoxLayout()
        right_layout.setSpacing(2)
        right_layout.addWidget(self.current_page_label)
        right_layout.addWidget(self.current_page_value)
        
        row1_layout.addLayout(left_layout)
        row1_layout.addStretch()
        row1_layout.addLayout(right_layout)
        
        # 第二行：演示时长
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(0)
        
        duration_layout = QVBoxLayout()
        duration_layout.setSpacing(2)
        duration_layout.addWidget(self.duration_label)
        duration_layout.addWidget(self.duration_value)
        
        row2_layout.addLayout(duration_layout)
        row2_layout.addStretch()
        
        info_layout.addLayout(row1_layout)
        info_layout.addLayout(row2_layout)
        
        layout.addWidget(info_widget)
        return widget



    def create_status_content(self):
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)  # 固定高度
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题区
        title_layout = QHBoxLayout()
        icon = QSvgWidget("resources/icons/status.svg")
        icon.setFixedSize(20, 20)
        title = QLabel("状态提示")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #23213A;")
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 内容区域 - 系统状态
        self.status_label = QLabel("系统就绪")
        self.status_label.setStyleSheet("background-color: #E8F5E9; color: #388E3C; border-radius: 6px; padding: 8px; font-size: 14px;")
        layout.addWidget(self.status_label)
        
        # 手势状态
        self.gesture_status_label = QLabel("")
        self.gesture_status_label.setStyleSheet(
            "background-color: #E8F5E9; color: #388E3C; border-radius: 6px; padding: 8px; font-size: 14px;")
        layout.addWidget(self.gesture_status_label)
        
        # 语音状态
        self.voice_status_label = QLabel("")
        self.voice_status_label.setStyleSheet(
            "background-color: #E3F2FD; color: #1976D2; border-radius: 6px; padding: 8px; font-size: 14px;")
        layout.addWidget(self.voice_status_label)
        
        # 录像状态指示器
        self.recording_status_label = QLabel("")
        self.recording_status_label.setStyleSheet(
            "background-color: #FFF3E0; color: #F57C00; border-radius: 6px; padding: 8px; font-size: 14px;")
        self.recording_status_label.hide()  # 初始隐藏
        layout.addWidget(self.recording_status_label)
        
        return widget

    def create_ai_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题区
        title_layout = QHBoxLayout()
        icon = QSvgWidget("resources/icons/ai.svg") 
        icon.setFixedSize(20, 20)
        title = QLabel("AI优化建议")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #23213A;")
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # AI按钮
        self.ai_chat_btn = QPushButton("💬 获取PPT优化建议")
        self.ai_chat_btn.setFixedHeight(35)
        self.ai_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #5B5BF6;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
            QPushButton:pressed {
                background-color: #E3E6F5;
            }
            QPushButton:disabled {
                background-color: #E3E6F5;
                color: #8B8BA7;
            }
        """)
        self.ai_chat_btn.setEnabled(False)  # 初始禁用，需要打开PPT后才能使用
        self.ai_chat_btn.clicked.connect(self.request_ai_advice)
        layout.addWidget(self.ai_chat_btn)
        
        # AI输出文本框 - 使用弹性布局，允许随窗口大小变化
        self.ai_output_text = QTextEdit()
        self.ai_output_text.setMinimumHeight(150)
        self.ai_output_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ai_output_text.setPlaceholderText("AI优化建议将在这里显示...\n\n请先打开PPT文件，然后点击上方按钮获取优化建议。")
        self.ai_output_text.setStyleSheet("""
            QTextEdit {
                background-color: #F6F8FB;
                border: 2px solid #E3E6F5;
                border-radius: 12px;
                padding: 12px;
                font-size: 12px;
                line-height: 1.4;
                color: #23213A;
            }
            QTextEdit:focus {
                border-color: #5B5BF6;
            }
        """)
        self.ai_output_text.setReadOnly(True)
        layout.addWidget(self.ai_output_text, 1)  # 设置拉伸因子为1，使其占用剩余空间
        
        return widget

    def update_ppt_info(self):
        """更新PPT信息显示"""
        if self.controller.ppt_controller.is_active():
            # 更新幻灯片信息
            self.slide_count_value.setText(f"{self.controller.ppt_controller.get_status()['total_slides']}")
            self.current_page_value.setText(f"{self.controller.ppt_controller.get_status()['current_slide']}")

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
                background-color: #F6F8FB;
            }
            QWidget {
                color: #23213A;
            }
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                border: none;
                margin-top: 0px;
                padding: 15px;
                border-radius: 12px;
                background-color: #FFFFFF;
                color: #23213A;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #23213A;
            }
            #previewGroup {
                background-color: #FFFFFF !important;
                border-radius: 10px;
                color: #23213A;
            }
            #previewGroup:title {
                color: #23213A;
            }
            QPushButton {
                background-color: #5B5BF6;
                color: #fff;
                border: none;
                border-radius: 12px;
            }
            QPushButton#windowControlButton {
                background: none;
                border-radius: 10px;
            }
            QPushButton:checked {
                background-color: #CFC3F9;
            }
            QPushButton:hover {
                background-color: #CFC3F9;
                color: #23213A;
            }
            QPushButton:pressed {
                background-color: #E3E6F5;
            }
            QPushButton:disabled {
                background-color: #E3E6F5;
                color: #8B8BA7;
            }
            QLabel {
                color: #23213A;
            }
            QLabel#previewimage {
                background: #FFFFFF;
                border-radius: 12px;
            }
            QSpinBox, QComboBox, QTextEdit, QLineEdit {
                border: 2px solid #E3E6F5;
                border-radius: 12px;
                background-color: #F6F8FB;
                selection-background-color: #CFC3F9;
                selection-color: #23213A;
                color: #23213A;
            }
            QSpinBox:hover, QComboBox:hover, QTextEdit:hover, QLineEdit:hover {
                border-color: #CFC3F9;
            }
            QSpinBox:focus, QComboBox:focus, QTextEdit:focus, QLineEdit:focus {
                border-color: #5B5BF6;
            }
            QComboBox::drop-down {
                border: none;
                background: #F6F8FB;
                border-radius: 6px;
                width: 20px;
                margin: 2px;
            }
            QComboBox::drop-down:hover {
                background: #E3E6F5;
            }
            QComboBox::down-arrow {
                image: url(resources/icons/downarrow.svg);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #CFC3F9;
                border-radius: 12px;
                background-color: #FFFFFF;
                selection-background-color: #CFC3F9;
                selection-color: #23213A;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                background: #F6F8FB;
                border-radius: 6px;
                width: 16px;
                margin: 1px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #E3E6F5;
            }
            QSpinBox::up-arrow {
                image: url(resources/icons/uparrow.svg);
                width: 12px;
                height: 12px;
            }
            QSpinBox::down-arrow {
                image: url(resources/icons/downarrow.svg);
                width: 12px;
                height: 12px;
            }
            QCheckBox {
                margin-left: 10px;
                margin-right: 10px;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
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
             QCheckBox::indicator:disabled {
                 border: 2px solid #ccc;
                 background: #D3D3D3;
                 border-radius: 4px;
             }               
           
            QTextEdit {
                background-color: #F6F8FB;
                border: 2px solid #E3E6F5;
                border-radius: 12px;
                color: #23213A;
            }
            QTextEdit:focus {
                border-color: #5B5BF6;
            }
            #topBar {
                background-color: #FFFFFF;
                border-radius: 0 0 12px 12px;
                color: #23213A;
            }
            #leftPanel {
                background-color: #FFFFFF;
                border-radius: 12px;
            }
            .QLabel[status="success"] {
                background-color: #E3F9F1;
                color: #5B5BF6;
                border-radius: 10px;
            }
            .QLabel[status="error"] {
                background-color: #FFF0F3;
                color: #CFC3F9;
                border-radius: 10px;
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
        #print(f"🔧 DEBUG: toggle_subtitle_display 被调用, enabled={enabled}")
        #print(f"🔧 DEBUG: 语音识别状态: {self.voice_checkbox.isChecked()}")
        #print(f"🔧 DEBUG: 悬浮窗存在: {hasattr(self, 'floating_window') and self.floating_window is not None}")
        
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
            #print(f"📡 DEBUG: 正在通知悬浮窗更新字幕状态: {enabled}")
            self.floating_window.set_subtitle_display_enabled(enabled)
        # else:
        #     #print("⚠️ DEBUG: 悬浮窗不存在，无法设置字幕状态")

        status_text = "字幕显示已开启" if enabled else "字幕显示已关闭"
        self.update_status(status_text)
        #print(f"✅ DEBUG: 字幕显示状态更新完成: {status_text}")

    def toggle_script_follow(self, enabled: bool):
        """切换文稿跟随状态"""
        #print(f"🔧 DEBUG: toggle_script_follow 被调用, enabled={enabled}")
        #print(f"🔧 DEBUG: 语音识别状态: {self.voice_checkbox.isChecked()}")
        
        if enabled and not self.voice_checkbox.isChecked():
            # 如果语音识别未开启，不允许开启文稿跟随
            self.script_follow_checkbox.blockSignals(True)
            self.script_follow_checkbox.setChecked(False)
            self.script_follow_checkbox.blockSignals(False)
            self.update_status("请先启用语音识别才能使用文稿跟随", is_error=True)
            print("❌ DEBUG: 语音识别未开启，拒绝启用文稿跟随")
            return
        
        self.script_follow_enabled = enabled
        
        if enabled:
            # 加载导入的文稿
            if self.script_manager.load_imported_script():
                self.imported_script_lines = self.script_manager.get_lines()
                self.current_script_position = 0  # 重置到开始位置
                self.update_script_display()
                self.update_status("文稿跟随已启用")

                #print(f"✅ 文稿跟随已启用，共 {len(self.imported_script_lines)} 行文稿")
            else:
                # 如果没有导入文稿，禁用文稿跟随
                self.script_follow_checkbox.blockSignals(True)
                self.script_follow_checkbox.setChecked(False)
                self.script_follow_checkbox.blockSignals(False)
                self.script_follow_enabled = False
                self.update_status("请先导入演讲文稿才能使用文稿跟随功能", is_error=True)
                print("❌ 没有导入文稿，无法启用文稿跟随")
        else:
            self.update_status("文稿跟随已关闭")
            print("❌ 文稿跟随已关闭")

    def match_speech_to_script(self, recognized_text: str):
        """将识别的语音与文稿进行匹配"""
        if not self.script_follow_enabled or not self.imported_script_lines:
            return False, -1, 0.0
        
        # 清理识别文本
        cleaned_text = recognized_text.strip()
        if len(cleaned_text) < 3:  # 太短的文本不进行匹配
            return False, -1, 0.0
        
        print(f"🔍 正在匹配语音文本: '{cleaned_text}'")
        
        # 从当前位置开始向后搜索匹配
        max_confidence = 0.0
        best_match_position = -1
        
        # 搜索范围：当前位置往后的5行内
        search_start = self.current_script_position
        search_end = min(len(self.imported_script_lines), self.current_script_position + 5)
        
        for i in range(search_start, search_end):
            script_line = self.imported_script_lines[i]
            confidence = self.calculate_text_similarity(cleaned_text, script_line)
            
            print(f" 第{i+1}行: '{script_line[:30]}...' -> 置信度: {confidence:.3f}")
            
            if confidence > max_confidence:
                max_confidence = confidence
                best_match_position = i
        
        # 如果找不到好的匹配，尝试在整个文稿中搜索
        if max_confidence < 0.3:
            #print("🔄 在当前位置附近未找到匹配，扩大搜索范围...")
            for i in range(len(self.imported_script_lines)):
                if i >= search_start and i < search_end:
                    continue  # 跳过已经搜索过的
                
                script_line = self.imported_script_lines[i]
                confidence = self.calculate_text_similarity(cleaned_text, script_line)
                
                if confidence > max_confidence:
                    max_confidence = confidence
                    best_match_position = i
        
        # 判断是否匹配成功（置信度阈值设为0.4）
        match_threshold = 0.4
        is_match = max_confidence >= match_threshold
        
        if is_match:
            #print(f"✅ 匹配成功! 第{best_match_position+1}行, 置信度: {max_confidence:.3f}")
            return True, best_match_position, max_confidence
        else:
            print(f"❌ 匹配失败, 最高置信度: {max_confidence:.3f} < {match_threshold}")
            return False, -1, max_confidence

    def calculate_text_similarity(self, text1: str, text2: str):
        """计算两个文本的相似度"""
        # 简单的相似度算法：基于公共子字符串
        text1 = text1.replace(" ", "").replace("，", "").replace("。", "").replace("！", "").replace("？", "")
        text2 = text2.replace(" ", "").replace("，", "").replace("。", "").replace("！", "").replace("？", "")
        
        if not text1 or not text2:
            return 0.0
        
        # 计算最长公共子序列
        def lcs_length(s1, s2):
            m, n = len(s1), len(s2)
            dp = [[0] * (n + 1) for _ in range(m + 1)]
            
            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    if s1[i-1] == s2[j-1]:
                        dp[i][j] = dp[i-1][j-1] + 1
                    else:
                        dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            
            return dp[m][n]
        
        lcs_len = lcs_length(text1, text2)
        max_len = max(len(text1), len(text2))
        similarity = lcs_len / max_len if max_len > 0 else 0.0
        
        # 额外加分：如果text1是text2的子串或vice versa
        if text1 in text2 or text2 in text1:
            similarity += 0.2
        
        return min(similarity, 1.0)

    def update_script_display(self):
        """更新悬浮窗中的文稿显示"""
        if not hasattr(self, 'floating_window') or not self.floating_window:
            return
        
        if not self.imported_script_lines or self.current_script_position < 0:
            return
        
        # 显示当前位置和接下来的两行（总共三行）
        display_lines = []
        for i in range(3):
            line_index = self.current_script_position + i
            if line_index < len(self.imported_script_lines):
                line_text = self.imported_script_lines[line_index]
                line_number = line_index + 1
                
                # 当前行用特殊标记
                if i == 0:
                    display_lines.append(f"▶ {line_number:02d}. {line_text}")
                else:
                    display_lines.append(f"  {line_number:02d}. {line_text}")
        
        if display_lines:
            script_text = f"📄 演讲文稿跟随 (第{self.current_script_position + 1}行)\n\n" + "\n".join(display_lines)
            self.floating_window.set_script_text(script_text)
            #print(f"📺 悬浮窗文稿显示已更新到第{self.current_script_position + 1}行")

    def process_complete_sentence(self, sentence: str):
        """处理完整的识别句子，进行文稿匹配"""
        if not self.script_follow_enabled:
            return
        
        print(f"🎯 处理完整句子: '{sentence}'")
        
        # 进行文稿匹配
        is_match, position, confidence = self.match_speech_to_script(sentence)
        
        if is_match and position >= 0:
            # 更新当前位置
            old_position = self.current_script_position
            self.current_script_position = position
            
            # 更新悬浮窗显示
            self.update_script_display()
            
                       
            # 显示匹配状态
            status_msg = f"文稿跟随: 第{old_position + 1}行 → 第{position + 1}行 (置信度: {confidence:.2f})"
            self.update_status(status_msg)
            
            print(f"📍 文稿位置更新: {old_position + 1} → {position + 1}")
        else:
            print(f"🔍 未找到匹配的文稿位置 (置信度: {confidence:.2f})")

    def request_ai_advice(self):
        """请求AI优化建议"""
        # 检查是否有打开的PPT
        if not self.controller.ppt_controller.current_ppt_path:
            self.ai_output_text.setText("❌ 请先打开一个PPT文件，然后再请求AI优化建议。")
            self.update_status("请先打开PPT文件", is_error=True)
            return
        
        # 显示加载状态
        self.ai_output_text.setText("🤖 AI正在分析您的PPT内容，请稍候...\n\n这可能需要几秒钟时间。")
        self.ai_chat_btn.setEnabled(False)
        self.ai_chat_btn.setText("🔄 分析中...")
        
        # 在新线程中处理AI请求，避免阻塞UI
        ai_thread = threading.Thread(target=self._process_ai_request, daemon=True)
        ai_thread.start()
    
    def _process_ai_request(self):
        """在后台线程中处理AI请求"""
        try:
            ppt_path = self.controller.ppt_controller.current_ppt_path
            
            # 提取PPT内容
            self.update_status("正在提取PPT内容...")
            content_result = self.ppt_extractor.extract_ppt_content(ppt_path)
            
            if "error" in content_result:
                self._update_ai_output_on_main_thread(f"❌ 提取PPT内容失败：{content_result['error']}")
                return
            
            # 保存当前PPT内容
            self.current_ppt_content = content_result
              # 请求AI建议
            self.update_status("正在获取AI优化建议...")
            ppt_text = content_result.get("full_text", "")
            advice = self.ai_advisor.get_ppt_optimization_advice(ppt_text, "detailed")
            
            # 格式化输出
            formatted_advice = self._format_ai_advice(advice, len(content_result.get("slides", [])))
                  # 在主线程中更新UI
            self._update_ai_output_on_main_thread(formatted_advice)
            self._update_status_on_main_thread("AI优化建议获取完成！")
            
        except Exception as e:
            error_msg = f"❌ 获取AI建议时发生错误：\n{str(e)}\n\n请检查网络连接或稍后重试。"
            self._update_ai_output_on_main_thread(error_msg)
            self._update_status_on_main_thread("获取AI建议失败", is_error=True)
        finally:
            # 恢复按钮状态
            self._reset_ai_button_on_main_thread()

    def _update_ai_output_direct(self, text: str):
        """直接在主线程中更新AI输出文本"""
        try:
            if hasattr(self, 'ai_output_text'):
                self.ai_output_text.setText(text)
                ##print(f"✅ AI输出文本已更新")
        except Exception as e:
            print(f"❌ 更新AI输出文本失败: {e}")

    def _reset_ai_button_direct(self):
        """直接在主线程中重置AI按钮状态"""
        try:
            if hasattr(self, 'ai_chat_btn'):
                self.ai_chat_btn.setEnabled(True)
                self.ai_chat_btn.setText("💬 获取PPT优化建议")
                ##print(f"✅ AI按钮状态已重置")
        except Exception as e:
            print(f"❌ 重置AI按钮失败: {e}")

    def _update_status_direct(self, message: str, is_error: bool = False):
        """直接在主线程中更新状态"""
        try:
            self.update_status(message, is_error)
            #print(f"✅ 状态已更新: {message}")
        except Exception as e:
            print(f"❌ 更新状态失败: {e}")

    def _format_ai_advice(self, advice: str, slide_count: int) -> str:
        """格式化AI建议输出"""
        from datetime import datetime
        
        header = f"🤖 AI优化建议 (共{slide_count}张幻灯片)\n"
        header += "=" * 40 + "\n\n"
        
        # 添加时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header += f"📅 分析时间: {timestamp}\n\n"
        
        # 主要建议内容
        main_content = advice + "\n\n"
        
        # 添加使用提示
        footer = "💡 使用提示:\n"
        footer += "• 点击按钮可重新获取建议\n"
        footer += "• 修改PPT后可获取新的优化建议\n"
        footer += "• 建议结合具体演讲场景进行调整"
        
        return header + main_content + footer

    def _process_ai_request(self):
        """在后台线程中处理AI请求"""
        try:
            #print("🤖 开始处理AI请求...")
            
            # 获取PPT路径
            ppt_path = self.controller.ppt_controller.current_ppt_path
            
            # 提取PPT内容
            #print("📄 提取PPT内容...")
            content_result = self.ppt_extractor.extract_ppt_content(ppt_path)
            
            if "error" in content_result:
                error_msg = f"❌ 提取PPT内容失败：{content_result['error']}"
                print(error_msg)
                # 使用信号发送更新
                self.ai_output_updated.emit(error_msg)
                self.ai_button_reset.emit()
                return
            
            # 调用AI分析
            #print("🤖 调用AI分析...")
            ppt_text = content_result.get("full_text", "")
            advice = self.ai_advisor.get_ppt_optimization_advice(ppt_text, "detailed")
            
            # 格式化输出
            formatted_advice = self._format_ai_advice(advice, len(content_result.get("slides", [])))
            
            #print("✅ AI分析成功完成")
            self.status_updated.emit("AI优化建议获取完成！", False)
            
            # 使用信号发送更新
            self.ai_output_updated.emit(formatted_advice)
            self.ai_button_reset.emit()
            
        except Exception as e:
            error_msg = f"❌ 处理AI请求时发生错误：{str(e)}"
            print(error_msg)
            print(f"❌ 详细错误信息: {traceback.format_exc()}")
            
            # 使用信号发送更新
            self.ai_output_updated.emit(error_msg)
            self.status_updated.emit("获取AI建议失败", True)
            self.ai_button_reset.emit()

    def request_ai_advice(self):
        """请求AI优化建议"""
        # 添加调试信息
        #print(f"🔍 DEBUG: 当前PPT路径: {self.controller.ppt_controller.current_ppt_path}")
        #print(f"🔍 DEBUG: AI按钮是否启用: {self.ai_chat_btn.isEnabled()}")
        
        # 检查是否有打开的PPT
        if not self.controller.ppt_controller.current_ppt_path:
            self.ai_output_text.setText("❌ 请先打开一个PPT文件，然后再请求AI优化建议。")
            self.update_status("请先打开PPT文件", is_error=True)
            return
        
        # 禁用按钮，防止重复点击
        self.ai_chat_btn.setEnabled(False)
        self.ai_chat_btn.setText("AI分析中... ⏳")
        
        # 显示加载信息
        self.ai_output_text.setText("🤖 AI正在分析您的PPT内容，请稍候...\n\n这可能需要几秒钟时间。")
        self.update_status("AI正在分析PPT内容...")
        
        # 在后台线程中处理AI请求
        threading.Thread(target=self._process_ai_request, daemon=True).start()            
        # 使用信号发送更新
        self.ai_output_updated.emit(error_msg)
        self.status_updated.emit("获取AI建议失败", True)
        self.ai_button_reset.emit()

    def request_ai_advice(self):
        """请求AI优化建议"""
        # 添加调试信息
        #print(f"🔍 DEBUG: 当前PPT路径: {self.controller.ppt_controller.current_ppt_path}")
        #print(f"🔍 DEBUG: AI按钮是否启用: {self.ai_chat_btn.isEnabled()}")
        
        # 检查是否有打开的PPT
        if not self.controller.ppt_controller.current_ppt_path:
            self.ai_output_text.setText("❌ 请先打开一个PPT文件，然后再请求AI优化建议。")
            self.update_status("请先打开PPT文件", is_error=True)
            return
        
        # 禁用按钮，防止重复点击
        self.ai_chat_btn.setEnabled(False)
        self.ai_chat_btn.setText("AI分析中... ⏳")
        
        # 显示加载信息
        self.ai_output_text.setText("🤖 AI正在分析您的PPT内容，请稍候...\n\n这可能需要几秒钟时间。")
        self.update_status("AI正在分析PPT内容...")
        
        # 在后台线程中处理AI请求
        threading.Thread(target=self._process_ai_request, daemon=True).start()
