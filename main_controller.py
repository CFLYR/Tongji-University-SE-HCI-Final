from PySide6.QtCore import QObject, Signal
from ppt_controller import PPTController, get_ppt_controller
from handTrackingModule import handDetector
import time
import json
import os
from unified_ppt_gesture_controller import UnifiedPPTGestureController
import RealTimeVoiceToText as RTVTT
import threading
import speech_text_manager
from PySide6.QtCore import QObject, Signal


class MainController(QObject):
    # 定义信号
    ppt_file_opened = Signal(str)
    presentation_started = Signal()
    presentation_stopped = Signal()
    slide_changed = Signal(int)
    gesture_detection_started = Signal()
    gesture_detection_stopped = Signal()
    gesture_detected = Signal(str, float)
    fps_updated = Signal(float)
    config_changed = Signal(str)
    gesture_enabled = Signal(str, bool)
    system_status_changed = Signal(str)
    error_occurred = Signal(str)
    status_changed = Signal(str)
    # 添加语音识别信号
    voice_recognition_started = Signal()
    voice_recognition_stopped = Signal()

    def __init__(self):
        super().__init__()
        # 初始化控制器
        self.ppt_controller = get_ppt_controller()
        self.gesture_detector = handDetector()
        self.gesture_controller = UnifiedPPTGestureController()
        self.running = False
        self.start_time = 0
        self.frame_count = 0
        self.last_fps_update = 0
        self.current_fps = 0

        # 主窗口引用
        self.main_window = None

        # 手势配置
        self.gesture_configs = {
            "next_slide": {"gesture_type": "swipe_right", "enabled": True},
            "prev_slide": {"gesture_type": "swipe_left", "enabled": True},
            "play_pause": {"gesture_type": "palm_up", "enabled": True},
            "exit_presentation": {"gesture_type": "fist", "enabled": True}
        }

        # 加载配置
        self.load_configs()

        # 初始化语音识别器
        self.audio_thread = None
        self.voice_recognizer = RTVTT.get_RTVTT_recognizer()

        # 初始化演讲稿管理器
        self.speech_manager = speech_text_manager.SpeechTextManager()

    def set_main_window(self, main_window):
        """设置主窗口引用"""
        self.main_window = main_window
        print("✅ 主控制器已设置主窗口引用")

    def start_system(self) -> bool:
        """启动系统"""
        try:
            self.running = True
            self.start_time = time.time()
            self.frame_count = 0
            self.system_status_changed.emit("系统已启动")
            return True
        except Exception as e:
            self.error_occurred.emit(f"启动系统失败: {str(e)}")
            return False

    def stop_system(self):
        """停止系统"""
        try:
            self.running = False
            if self.ppt_controller.is_active():
                self.ppt_controller.exit_presentation()
            self.system_status_changed.emit("系统已停止")
        except Exception as e:
            self.error_occurred.emit(f"停止系统失败: {str(e)}")

    def open_ppt_file(self, file_path: str) -> bool:
        """打开PPT文件"""
        try:
            if self.ppt_controller.open_powerpoint_file(file_path):
                self.ppt_file_opened.emit(file_path)
                return True
            return False
        except Exception as e:
            self.error_occurred.emit(f"打开PPT文件失败: {str(e)}")
            return False

    def start_presentation(self, file_path: str) -> bool:
        """开始PPT演示"""
        try:
            if self.ppt_controller.open_powerpoint_file(file_path):
                self.presentation_started.emit()
                return True
            return False
        except Exception as e:
            self.error_occurred.emit(f"开始演示失败: {str(e)}")
            return False

    def stop_presentation(self):
        """停止PPT演示"""
        try:
            self.ppt_controller.exit_presentation()
            self.presentation_stopped.emit()
        except Exception as e:
            self.error_occurred.emit(f"停止演示失败: {str(e)}")

    def next_slide(self):
        """下一张幻灯片"""
        try:
            self.ppt_controller.next_slide()
        except Exception as e:
            self.error_occurred.emit(f"切换幻灯片失败: {str(e)}")

    def previous_slide(self):
        """上一张幻灯片"""
        try:
            self.ppt_controller.previous_slide()
        except Exception as e:
            self.error_occurred.emit(f"切换幻灯片失败: {str(e)}")

    def jump_to_slide(self, slide_number: int):
        """跳转到指定幻灯片"""
        try:
            self.ppt_controller.jump_to_slide(slide_number)
        except Exception as e:
            self.error_occurred.emit(f"跳转幻灯片失败: {str(e)}")

    def start_gesture_detection(self) -> bool:
        """开始手势检测"""
        try:
            self.gesture_detection_started.emit()
            return True
        except Exception as e:
            self.error_occurred.emit(f"启动手势检测失败: {str(e)}")
            return False

    def stop_gesture_detection(self):
        """停止手势检测"""
        try:
            self.gesture_detection_stopped.emit()
        except Exception as e:
            self.error_occurred.emit(f"停止手势检测失败: {str(e)}")

    def set_detection_interval(self, interval: float):
        """设置检测间隔"""
        try:
            # 更新检测间隔
            pass
        except Exception as e:
            self.error_occurred.emit(f"设置检测间隔失败: {str(e)}")

    def update_gesture_config(self, gesture_name: str, config: dict) -> bool:
        """更新手势配置"""
        try:
            if gesture_name in self.gesture_configs:
                self.gesture_configs[gesture_name].update(config)
                self.config_changed.emit(gesture_name)
                return True
            return False
        except Exception as e:
            self.error_occurred.emit(f"更新手势配置失败: {str(e)}")
            return False

    def get_system_status(self) -> dict:
        """获取系统状态"""
        return {
            "running": self.running,
            "fps": self.current_fps,
            "frame_count": self.frame_count,
            "runtime": time.time() - self.start_time if self.running else 0
        }

    def get_current_slide(self) -> int:
        """获取当前幻灯片编号"""
        try:
            if self.ppt_controller.is_active():
                return self.ppt_controller.get_status().get("current_slide", 1)
            return 1
        except Exception as e:
            self.error_occurred.emit(f"获取当前幻灯片失败: {str(e)}")
            return 1

    def load_configs(self):
        """加载配置"""
        try:
            if os.path.exists("gesture_config.json"):
                with open("gesture_config.json", "r", encoding="utf-8") as f:
                    self.gesture_configs = json.load(f)
        except Exception as e:
            self.error_occurred.emit(f"加载配置失败: {str(e)}")

    def save_configs(self) -> bool:
        """保存配置"""
        try:
            with open("gesture_config.json", "w", encoding="utf-8") as f:
                json.dump(self.gesture_configs, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            self.error_occurred.emit(f"保存配置失败: {str(e)}")
            return False

    def update_fps(self, fps: float):
        """更新FPS"""
        self.current_fps = fps
        self.fps_updated.emit(fps)

    def process_frame(self, frame):
        """处理视频帧"""
        if not self.running:
            return frame

        try:
            # 更新帧计数
            self.frame_count += 1

            # 更新FPS
            current_time = time.time()
            if current_time - self.last_fps_update >= 1.0:
                self.update_fps(self.frame_count / (current_time - self.start_time))
                self.frame_count = 0
                self.last_fps_update = current_time

            # 处理手势检测
            frame = self.gesture_detector.findHands(frame)
            lmList = self.gesture_detector.findPosition(frame)

            if len(lmList) != 0:
                # 检测手势并执行相应操作
                self.process_gesture(lmList)

            return frame

        except Exception as e:
            self.error_occurred.emit(f"处理视频帧失败: {str(e)}")
            return frame

    def process_gesture(self, lmList):
        """处理检测到的手势"""
        try:
            # 获取手指状态
            fingers = self.gesture_detector.fingersUp(lmList)

            # 根据手指状态判断手势
            if sum(fingers) == 5:  # 所有手指都张开
                self.gesture_detected.emit("palm_up", 1.0)
            elif sum(fingers) == 0:  # 所有手指都闭合
                self.gesture_detected.emit("fist", 1.0)
            # 可以添加更多手势判断逻辑

        except Exception as e:
            self.error_occurred.emit(f"处理手势失败: {str(e)}")

    def toggle_gesture_detection(self, enabled: bool):
        """切换手势检测状态"""
        try:
            # 使用 UnifiedPPTGestureController 的 running 属性来控制手势检测
            self.gesture_controller.running = enabled
            if enabled:
                self.gesture_detection_started.emit()
            else:
                self.gesture_detection_stopped.emit() 
        except Exception as e:
            self.error_occurred.emit(f"切换手势检测失败: {str(e)}")

    def toggle_voice_recognition(self, enabled: bool, next_page_keywords: list):
        """切换语音识别状态"""
        try:
            if enabled:
                # 启动实时语音识别
                print("🔧 DEBUG: 主控制器启动语音识别")
                success = RTVTT.start_real_time_voice_recognition(mic_device_index=None)
                if success:
                    self.voice_recognizer.next_page_keywords = next_page_keywords
                    self.voice_recognition_started.emit()
                    print("✅ 主控制器：语音识别启动成功")
                else:
                    print("❌ 主控制器：语音识别启动失败")
                    self.error_occurred.emit("语音识别启动失败")
            else:
                # 停止实时语音识别
                print("🔧 DEBUG: 主控制器停止语音识别")
                RTVTT.stop_real_time_voice_recognition()
                self.voice_recognition_stopped.emit()
                print("✅ 主控制器：语音识别停止成功")
        except Exception as e:
            self.error_occurred.emit(f"切换语音识别状态失败: {str(e)}")
            print(f"❌ 主控制器切换语音识别状态失败: {e}")
            import traceback
            traceback.print_exc()

    def update_gesture_mapping(self, gesture: str, action: str):
        """更新手势映射 - 已移至主窗口处理"""
        try:
            # 手势映射更新逻辑已移至主窗口的update_gesture_mapping方法
            # 这里只需要发出配置更改信号
            self.config_changed.emit(f"{action}->{gesture}")
        except Exception as e:
            self.error_occurred.emit(f"更新手势映射失败: {str(e)}")

    def update_detection_interval(self, interval: int):
        """更新检测间隔"""
        try:
            # 由于 UnifiedPPTGestureController 没有 update_detection_interval 方法
            # 我们可以设置命令冷却时间来控制检测间隔
            if hasattr(self.gesture_controller, 'command_cooldown_duration'):
                self.gesture_controller.command_cooldown_duration = float(interval / 1000.0)  # 转换为秒
                self.config_changed.emit("detection_interval")
            else:
                self.error_occurred.emit("无法更新检测间隔：控制器不支持此功能")
        except Exception as e:
            self.error_occurred.emit(f"更新检测间隔失败: {str(e)}")

    def get_ppt_status(self) -> dict:
        """获取PPT状态"""
        return self.ppt_controller.get_status()

    def is_presentation_active(self) -> bool:
        """检查演示是否处于活动状态"""
        return self.ppt_controller.is_active()
