#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口录像功能补丁文件
"""

def add_recording_quick_button_to_main_window():
    """为主窗口添加录像快捷按钮的补丁代码"""
    
    # 这是添加到主窗口控制按钮区域的代码
    quick_record_button_code = '''
        # 录像快捷按钮
        self.quick_record_btn = QPushButton("录像")
        if os.path.exists("resources/icons/record.svg"):
            self.quick_record_btn.setIcon(QIcon("resources/icons/record.svg"))
        self.quick_record_btn.setIconSize(QSize(16, 16))
        self.quick_record_btn.setMinimumHeight(28)
        self.quick_record_btn.setMaximumWidth(80)
        self.quick_record_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
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
        self.quick_record_btn.clicked.connect(self.toggle_quick_recording)
        self.quick_record_btn.setEnabled(False)  # 初始禁用，需要悬浮窗显示后才能使用
        
        # 添加到布局
        control_layout.addWidget(self.quick_record_btn)
    '''
    
    # 这是快捷录像方法的代码
    toggle_recording_method = '''
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
    '''
    
    return quick_record_button_code, toggle_recording_method

def update_floating_window_connection():
    """更新悬浮窗连接代码"""
    
    connection_update = '''
                # 打开悬浮窗
                if self.floating_window is None:
                    self.floating_window = PPTFloatingWindow()
                    # 连接悬浮窗的录像信号
                    self.floating_window.recording_started.connect(self.on_recording_started)
                    self.floating_window.recording_stopped.connect(self.on_recording_stopped)
                    self.floating_window.subtitle_updated.connect(self.on_subtitle_updated)
                    
                    # 如果有演讲稿管理器，设置到悬浮窗
                    if hasattr(self.controller, 'speech_manager'):
                        self.floating_window.set_speech_manager(self.controller.speech_manager)
                
                self.floating_window.show()
                
                # 启用快捷录像按钮
                if hasattr(self, 'quick_record_btn'):
                    self.quick_record_btn.setEnabled(True)
    '''
    
    return connection_update

if __name__ == "__main__":
    print("主窗口录像功能补丁代码")
    print("=" * 50)
    
    button_code, method_code = add_recording_quick_button_to_main_window()
    connection_code = update_floating_window_connection()
    
    print("1. 录像快捷按钮代码:")
    print(button_code)
    
    print("\n2. 快捷录像方法:")
    print(method_code)
    
    print("\n3. 悬浮窗连接更新:")
    print(connection_code)
