from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QStackedWidget, QFileDialog,
                               QSpinBox, QComboBox, QGroupBox, QFormLayout, QSpacerItem,
                               QSizePolicy, QCheckBox, QDialog,QTextEdit,QDialogButtonBox)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QIcon, QPixmap, QImage
from PySide6.QtCore import QSize
from PySide6.QtSvgWidgets import QSvgWidget
from main_controller import MainController
from ppt_floating_window import PPTFloatingWindow
from keyword_manager import KeywordManagerDialog
from script_manager import ScriptImportDialog, ScriptManager
from ppt_content_extractor import PPTContentExtractor
from ppt_ai_advisor import PPTAIAdvisor
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
        self.setMinimumSize(1200, 800)        # 初始化主控制器
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
        self.imported_script_lines = []  # 导入的文稿行列表        # 创建主窗口部件
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
            
            # 启用AI优化建议按钮
            self.ai_chat_btn.setEnabled(True)
            print(f"✅ AI优化建议按钮已启用，PPT路径: {file_path}")
            
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
                        self.floating_window.set_speech_manager(self.controller.speech_manager)                    # 同步当前字幕显示状态到悬浮窗
                    if hasattr(self, 'subtitle_checkbox') and self.subtitle_checkbox.isChecked():
                        print("🔄 同步字幕显示状态到悬浮窗")
                        self.floating_window.set_subtitle_display_enabled(True)
                    
                    # 同步语音识别功能状态和关键词到悬浮窗
                    if hasattr(self, 'voice_checkbox') and self.voice_checkbox.isChecked():
                        print("🔄 同步语音识别功能状态到悬浮窗")
                        if hasattr(self.floating_window, 'set_voice_recognition_enabled'):
                            self.floating_window.set_voice_recognition_enabled(True)
                        if hasattr(self.floating_window, 'set_voice_keywords'):
                            self.floating_window.set_voice_keywords(self.voice_keywords)
                            print(f"📝 已将关键词同步到悬浮窗: {self.voice_keywords}")

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
                    print(f"📝 已将关键词传递到悬浮窗: {self.voice_keywords}")

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
                    # 获取文稿的第一行作为预览
                    first_line = self.script_manager.get_line_by_number(1)
                    if first_line:
                        self.floating_window.set_script_text(f"📄 文稿已导入\n{first_line[:50]}...")
                    else:
                        self.floating_window.set_script_text("📄 文稿已导入，可以开始演示")
                    
                    print("✅ 文稿已同步到悬浮窗")
            
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
        self.ai_chat_btn.setEnabled(True)  # 启用AI按钮
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
        self.recording_status_label.hide()  # 初始隐藏        status_layout.addWidget(self.gesture_status_label)
        status_layout.addWidget(self.voice_status_label)
        status_layout.addWidget(self.recording_status_label)
        layout.addWidget(status_group)

        # AI对话优化建议
        ai_group = QGroupBox("")
        ai_layout = QVBoxLayout(ai_group)
        ai_layout.setSpacing(10)
        ai_layout.setContentsMargins(0, 0, 0, 0)
        
        # 顶部自定义标题栏
        ai_title_layout = QHBoxLayout()
        ai_title_layout.setSpacing(4)
        ai_svg_widget = QSvgWidget("resources/icons/info.svg")  # 使用合适的图标
        ai_svg_widget.setFixedSize(20, 20)
        ai_title_label = QLabel("AI优化建议")
        ai_title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-left: 1px;color: #1a1a1a")
        ai_title_layout.addWidget(ai_svg_widget)
        ai_title_layout.addWidget(ai_title_label)
        ai_title_layout.addStretch()
        
        ai_layout.addLayout(ai_title_layout)
        ai_layout.addSpacing(10)
        
        # AI对话按钮
        self.ai_chat_btn = QPushButton("💬 获取PPT优化建议")
        self.ai_chat_btn.setFixedHeight(35)
        self.ai_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #165DFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #4080FF;
            }
            QPushButton:pressed {
                background-color: #0E4BC7;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #888888;
            }
        """)
        self.ai_chat_btn.setEnabled(False)  # 初始禁用，需要打开PPT后才能使用
        self.ai_chat_btn.clicked.connect(self.request_ai_advice)
        ai_layout.addWidget(self.ai_chat_btn)
        
        # AI输出框
        self.ai_output_text = QTextEdit()
        self.ai_output_text.setFixedHeight(150)
        self.ai_output_text.setPlaceholderText("AI优化建议将在这里显示...\n\n请先打开PPT文件，然后点击上方按钮获取优化建议。")
        self.ai_output_text.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 2px solid #E1E5E9;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                line-height: 1.4;
                color: #2C3E50;
            }
            QTextEdit:focus {
                border-color: #165DFF;
            }
        """)
        self.ai_output_text.setReadOnly(True)
        ai_layout.addWidget(self.ai_output_text)
        
        layout.addWidget(ai_group)

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
        
        # 文稿跟随复选框
        self.script_follow_checkbox = QCheckBox("启用文稿跟随")
        self.script_follow_checkbox.setStyleSheet("QCheckBox {}")
        self.script_follow_checkbox.setEnabled(False)  # 默认禁用，需要先启用语音识别
        self.script_follow_checkbox.toggled.connect(self.toggle_script_follow)
        
        voice_layout.addWidget(self.script_follow_checkbox, alignment=Qt.AlignLeft)
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

    def toggle_script_follow(self, enabled: bool):
        """切换文稿跟随状态"""
        print(f"🔧 DEBUG: toggle_script_follow 被调用, enabled={enabled}")
        print(f"🔧 DEBUG: 语音识别状态: {self.voice_checkbox.isChecked()}")
        
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
                self.update_status("文稿跟随已启用，将根据语音识别结果跟随文稿进度")
                print(f"✅ 文稿跟随已启用，共 {len(self.imported_script_lines)} 行文稿")
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
            
            print(f"📝 第{i+1}行: '{script_line[:30]}...' -> 置信度: {confidence:.3f}")
            
            if confidence > max_confidence:
                max_confidence = confidence
                best_match_position = i
        
        # 如果找不到好的匹配，尝试在整个文稿中搜索
        if max_confidence < 0.3:
            print("🔄 在当前位置附近未找到匹配，扩大搜索范围...")
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
            print(f"✅ 匹配成功! 第{best_match_position+1}行, 置信度: {max_confidence:.3f}")
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
            print(f"📺 悬浮窗文稿显示已更新到第{self.current_script_position + 1}行")

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
                print(f"✅ AI输出文本已更新")
        except Exception as e:
            print(f"❌ 更新AI输出文本失败: {e}")

    def _reset_ai_button_direct(self):
        """直接在主线程中重置AI按钮状态"""
        try:
            if hasattr(self, 'ai_chat_btn'):
                self.ai_chat_btn.setEnabled(True)
                self.ai_chat_btn.setText("💬 获取PPT优化建议")
                print(f"✅ AI按钮状态已重置")
        except Exception as e:
            print(f"❌ 重置AI按钮失败: {e}")

    def _update_status_direct(self, message: str, is_error: bool = False):
        """直接在主线程中更新状态"""
        try:
            self.update_status(message, is_error)
            print(f"✅ 状态已更新: {message}")
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
            print("🤖 开始处理AI请求...")
            
            # 获取PPT路径
            ppt_path = self.controller.ppt_controller.current_ppt_path
            
            # 提取PPT内容
            print("📄 提取PPT内容...")
            content_result = self.ppt_extractor.extract_ppt_content(ppt_path)
            
            if "error" in content_result:
                error_msg = f"❌ 提取PPT内容失败：{content_result['error']}"
                print(error_msg)
                # 使用信号发送更新
                self.ai_output_updated.emit(error_msg)
                self.ai_button_reset.emit()
                return
            
            # 调用AI分析
            print("🤖 调用AI分析...")
            ppt_text = content_result.get("full_text", "")
            advice = self.ai_advisor.get_ppt_optimization_advice(ppt_text, "detailed")
            
            # 格式化输出
            formatted_advice = self._format_ai_advice(advice, len(content_result.get("slides", [])))
            
            print("✅ AI分析成功完成")
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
        print(f"🔍 DEBUG: 当前PPT路径: {self.controller.ppt_controller.current_ppt_path}")
        print(f"🔍 DEBUG: AI按钮是否启用: {self.ai_chat_btn.isEnabled()}")
        
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