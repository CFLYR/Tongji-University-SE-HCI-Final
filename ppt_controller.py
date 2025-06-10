# -*- coding: utf-8 -*-
"""
PowerPoint控制模块
PowerPoint Control Module

提供跨平台的PowerPoint控制功能，支持多种PPT软件
"""

import os
import pyautogui as pt
import subprocess
import time
import platform
from typing import Optional, List
from pathlib import Path

# Windows窗口激活相关导入
try:
    import win32gui
    import win32con
    import win32process

    WINDOWS_API_AVAILABLE = True
except ImportError:
    WINDOWS_API_AVAILABLE = False
    print("⚠️ Windows API不可用，将使用备用的窗口激活方法")


class PPTController:
    """PowerPoint控制器类"""

    def __init__(self):
        self.is_presentation_active = False
        self.current_ppt_path = None
        self.ppt_process = None
        self.laser_mode = False  # 激光指示器模式状态

        # 禁用pyautogui的安全检查以提高性能
        pt.FAILSAFE = False
        pt.PAUSE = 0.1

    def open_powerpoint_file(self, file_path: str) -> bool:
        """
        打开PowerPoint文件
        
        Args:
            file_path: PPT文件路径
            
        Returns:
            是否成功打开
        """
        try:
            if not os.path.exists(file_path):
                print(f"文件不存在: {file_path}")
                return False

            # 根据操作系统选择打开方式
            system = platform.system()

            if system == "Windows":
                # Windows系统
                self.ppt_process = os.startfile(file_path)
                time.sleep(3)  # 等待PowerPoint启动

                # 尝试进入演示模式
                time.sleep(2)
                pt.press('f5')  # F5键进入幻灯片放映模式

            elif system == "Darwin":  # macOS
                subprocess.run(['open', file_path])
                time.sleep(3)
                # macOS的Keynote或PowerPoint快捷键
                pt.hotkey('cmd', 'shift', 'return')

            elif system == "Linux":
                subprocess.run(['xdg-open', file_path])
                time.sleep(3)
                pt.press('f5')

            self.current_ppt_path = file_path
            self.is_presentation_active = True
            print(f"成功打开PPT: {file_path}")
            return True

        except Exception as e:
            print(f"打开PPT失败: {e}")
            return False

    def next_slide(self):
        """下一张幻灯片"""
        if self.is_presentation_active:
            try:
                pt.press('right')  # 或者使用 'space', 'pagedown'
                print("执行：下一张幻灯片")
            except Exception as e:
                print(f"下一张幻灯片失败: {e}")

    def previous_slide(self):
        """上一张幻灯片"""
        if self.is_presentation_active:
            try:
                pt.press('left')  # 或者使用 'backspace', 'pageup'
                print("执行：上一张幻灯片")
            except Exception as e:
                print(f"上一张幻灯片失败: {e}")

    def play_pause(self):
        """播放/暂停"""
        if self.is_presentation_active:
            try:
                pt.press('space')
                print("执行：播放/暂停")
            except Exception as e:
                print(f"播放/暂停失败: {e}")

    def exit_presentation(self):
        """退出演示"""
        if self.is_presentation_active:
            try:
                pt.press('esc')
                self.is_presentation_active = False
                print("执行：退出演示")
            except Exception as e:
                print(f"退出演示失败: {e}")

    def fullscreen_toggle(self):
        """切换全屏"""
        if self.is_presentation_active:
            try:
                pt.press('f5')  # 或者 F11
                print("执行：切换全屏")
            except Exception as e:
                print(f"切换全屏失败: {e}")

    def jump_to_slide(self, slide_number: int):
        """跳转到指定幻灯片"""
        if self.is_presentation_active:
            try:
                # 输入幻灯片编号
                pt.typewrite(str(slide_number))
                pt.press('enter')
                print(f"执行：跳转到第{slide_number}张幻灯片")
            except Exception as e:
                print(f"跳转幻灯片失败: {e}")

    def black_screen(self):
        """黑屏/恢复"""
        if self.is_presentation_active:
            try:
                pt.press('b')  # 按B键黑屏/恢复
                print("执行：黑屏切换")
            except Exception as e:
                print(f"黑屏切换失败: {e}")

    def white_screen(self):
        """白屏/恢复"""
        if self.is_presentation_active:
            try:
                pt.press('w')  # 按W键白屏/恢复
                print("执行：白屏切换")
            except Exception as e:
                print(f"白屏切换失败: {e}")

    def laser_pointer_mode(self):
        """激光指示器模式"""
        if self.is_presentation_active:
            try:
                pt.hotkey('ctrl', 'l')  # Ctrl+L激活激光指示器
                self.laser_mode = not self.laser_mode  # 切换激光指示器状态
                status = "开启" if self.laser_mode else "关闭"
                print(f"执行：激光指示器模式 ({status})")
            except Exception as e:
                print(f"激光指示器模式失败: {e}")

    def pen_mode(self):
        """画笔模式"""
        if self.is_presentation_active:
            try:
                pt.hotkey('ctrl', 'p')  # Ctrl+P激活画笔
                print("执行：画笔模式")
            except Exception as e:
                print(f"画笔模式失败: {e}")

    def eraser_mode(self):
        """橡皮擦模式"""
        if self.is_presentation_active:
            try:
                pt.hotkey('ctrl', 'e')  # Ctrl+E激活橡皮擦
                print("执行：橡皮擦模式")
            except Exception as e:
                print(f"橡皮擦模式失败: {e}")

    def zoom_in(self):
        """放大"""
        if self.is_presentation_active:
            try:
                pt.press('equal')  # 等号键放大 (或 Ctrl+=)
                print("执行：放大")
            except Exception as e:
                print(f"放大失败: {e}")

    def zoom_out(self):
        """缩小"""
        if self.is_presentation_active:
            try:
                pt.press('minus')  # 减号键缩小 (或 Ctrl+-)
                print("执行：缩小")
            except Exception as e:
                print(f"缩小失败: {e}")

    def get_ppt_files(self, directory: str = None) -> List[str]:
        """
        获取目录中的PPT文件列表
        
        Args:
            directory: 搜索目录，默认为当前目录
            
        Returns:
            PPT文件路径列表
        """
        if directory is None:
            directory = os.getcwd()

        ppt_extensions = ['.ppt', '.pptx', '.pps', '.ppsx']
        ppt_files = []

        try:
            for file in os.listdir(directory):
                if any(file.lower().endswith(ext) for ext in ppt_extensions):
                    ppt_files.append(os.path.join(directory, file))
        except Exception as e:
            print(f"搜索PPT文件失败: {e}")

        return ppt_files

    def auto_select_ppt(self) -> Optional[str]:
        """
        自动选择PPT文件（选择第一个找到的PPT文件）
        
        Returns:
            选中的PPT文件路径，如果没有找到则返回None
        """
        ppt_files = self.get_ppt_files()

        if ppt_files:
            selected_file = ppt_files[0]
            print(f"自动选择PPT文件: {selected_file}")
            return selected_file
        else:
            print("当前目录下没有找到PPT文件")
            return None

    def execute_action(self, action):
        """
        执行PPT操作
        
        Args:
            action: PPTAction枚举值或字符串
        """
        # 处理枚举或字符串
        if hasattr(action, 'value'):
            action_str = action.value
        else:
            action_str = str(action)

        try:  # 映射操作到具体方法
            action_map = {
                "next_slide": self.next_slide,
                "prev_slide": self.previous_slide,
                "play_pause": self.play_pause,
                "exit_presentation": self.exit_presentation,
                "fullscreen_toggle": self.fullscreen_toggle,
                "draw_mode": self.pen_mode,
                "erase_mode": self.eraser_mode,
                "zoom_in": self.zoom_in,
                "zoom_out": self.zoom_out,
                "menu_toggle": self.black_screen,  # 映射到黑屏功能
                "jump_to_page": lambda: None  # 占位符，需要参数
            }

            if action_str in action_map:
                action_map[action_str]()
                print(f" 成功执行PPT操作: {action_str}")
            else:
                print(f" 未知的PPT操作: {action_str}")

        except Exception as e:
            print(f" 执行PPT操作失败 ({action_str}): {e}")

    def is_active(self) -> bool:
        """检查演示是否处于活动状态"""
        return self.is_presentation_active

    def get_status(self) -> dict:
        """获取控制器状态"""
        return {
            "is_active": self.is_presentation_active,
            "current_file": self.current_ppt_path,
            "process": self.ppt_process is not None
        }


# 全局PPT控制器实例
_ppt_controller = None


def get_ppt_controller() -> PPTController:
    """获取全局PPT控制器实例"""
    global _ppt_controller
    if _ppt_controller is None:
        _ppt_controller = PPTController()
    return _ppt_controller


if __name__ == "__main__":
    # 测试PPT控制器
    controller = PPTController()

    # 自动选择PPT文件
    ppt_file = controller.auto_select_ppt()

    if ppt_file:
        # 打开PPT
        if controller.open_powerpoint_file(ppt_file):
            print("PPT控制器测试开始...")
            time.sleep(3)

            # 测试基本控制
            print("测试下一张幻灯片...")
            controller.next_slide()
            time.sleep(2)

            print("测试上一张幻灯片...")
            controller.previous_slide()
            time.sleep(2)

            print("PPT控制器测试完成")
        else:
            print("无法打开PPT文件")
    else:
        print("没有找到PPT文件进行测试")
