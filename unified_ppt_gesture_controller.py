# -*- coding: utf-8 -*-
"""
统一PPT手势识别播放器
Unified PPT Gesture Recognition Controller

功能特性:
1. 基础播放控制 (上一页/下一页/暂停/退出)
2. 高级交互功能 (激光指示器/画笔/缩放)
3. 自定义手势配置
4. 多种手势识别算法
5. 实时反馈和状态显示
6. 支持多种PPT软件
"""

import cv2 as cv
import numpy as np
import time
import math
import json
import os
import pyautogui as pt
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Callable
import handTrackingModule as hmt
from chinese_text_renderer import put_chinese_text, ChineseTextRenderer, put_text_auto
from ppt_controller import PPTController, get_ppt_controller


class GestureType(Enum):
    """手势类型枚举"""
    STATIC = "static"  # 静态手势 (手指形状)
    DYNAMIC = "dynamic"  # 动态手势 (运动轨迹)
    DUAL_HAND = "dual_hand"  # 双手手势
    CONTINUOUS = "continuous"  # 持续手势


class PPTAction(Enum):
    """PPT操作枚举"""
    NEXT_SLIDE = "next_slide"
    PREV_SLIDE = "prev_slide"
    PLAY_PAUSE = "play_pause"
    EXIT_PRESENTATION = "exit_presentation"
    FULLSCREEN_TOGGLE = "fullscreen_toggle"
    LASER_POINTER = "laser_pointer"
    DRAW_MODE = "draw_mode"
    ERASE_MODE = "erase_mode"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    JUMP_TO_PAGE = "jump_to_page"
    MENU_TOGGLE = "menu_toggle"


@dataclass
class GestureConfig:
    """手势配置数据类"""
    name: str
    gesture_type: GestureType
    action: PPTAction
    finger_pattern: List[int] = None  # 静态手势的手指模式 [拇指,食指,中指,无名指,小指]
    motion_pattern: str = None  # 动态手势的运动模式
    confidence_threshold: float = 0.8  # 识别置信度阈值
    hold_duration: float = 0.0  # 持续时间要求 (秒)
    enabled: bool = True  # 是否启用
    custom: bool = False  # 是否为自定义手势


class UnifiedGestureDetector:
    """统一手势识别器"""

    def __init__(self):
        self.detector = hmt.handDetector()
        self.tipIds = [4, 8, 12, 16, 20]  # 手指尖端ID

        # 手势历史记录 (用于动态手势和持续手势)
        self.gesture_history = []
        self.position_history = []
        self.last_gesture_time = {}

        # 双手检测
        self.left_hand_landmarks = None
        self.right_hand_landmarks = None

    def detect_static_gesture(self, lmList: List[List[int]]) -> Dict[str, float]:
        """检测静态手势 - 返回各种手势的置信度"""
        if len(lmList) == 0:
            return {}

        fingers = self.get_fingers_up(lmList)
        total_fingers = sum(fingers)

        gestures = {}

        # 基础数字手势
        if total_fingers == 0:
            gestures["fist"] = 1.0
        elif total_fingers == 1:
            if fingers[1] == 1:  # 食指
                gestures["point"] = 1.0
            elif fingers[0] == 1:  # 拇指
                gestures["thumb_up"] = 1.0
        elif total_fingers == 2:
            if fingers[1] == 1 and fingers[2] == 1:
                gestures["peace"] = 1.0
            elif fingers[0] == 1 and fingers[1] == 1:
                # 检查OK手势
                distance = self.get_distance(4, 8, lmList)
                if distance < 40:
                    gestures["ok"] = 0.9
                else:
                    gestures["two"] = 0.8
        elif total_fingers == 3:
            gestures["three"] = 1.0
        elif total_fingers == 4:
            gestures["four"] = 1.0
        elif total_fingers == 5:
            gestures["open_hand"] = 1.0

        # 特殊手势
        if fingers[1] == 1 and fingers[4] == 1 and sum(fingers[2:4]) == 0:
            gestures["rock"] = 0.9

        return gestures

    def detect_dynamic_gesture(self, lmList: List[List[int]]) -> Dict[str, float]:
        """检测动态手势 - 基于运动轨迹"""
        if len(lmList) == 0:
            return {}

        # 记录手掌中心位置
        hand_center = lmList[9]  # 手掌中心
        self.position_history.append([hand_center[1], hand_center[2], time.time()])

        # 保持最近30帧的历史
        if len(self.position_history) > 30:
            self.position_history = self.position_history[-30:]

        gestures = {}

        if len(self.position_history) >= 10:
            # 分析运动模式
            recent_positions = self.position_history[-10:]

            # 计算总体运动方向
            start_pos = recent_positions[0]
            end_pos = recent_positions[-1]
            dx = end_pos[0] - start_pos[0]
            dy = end_pos[1] - start_pos[1]
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > 50:  # 有明显移动
                # 水平移动
                if abs(dx) > abs(dy) * 2:
                    if dx > 0:
                        gestures["swipe_right"] = min(distance / 100, 1.0)
                    else:
                        gestures["swipe_left"] = min(distance / 100, 1.0)
                # 垂直移动
                elif abs(dy) > abs(dx) * 2:
                    if dy > 0:
                        gestures["swipe_down"] = min(distance / 100, 1.0)
                    else:
                        gestures["swipe_up"] = min(distance / 100, 1.0)

                # 检测圆形运动
                if self.is_circular_motion(recent_positions):
                    gestures["circle"] = 0.8

        return gestures

    def detect_dual_hand_gesture(self, left_landmarks, right_landmarks) -> Dict[str, float]:
        """检测双手手势"""
        gestures = {}

        if left_landmarks is not None and right_landmarks is not None:
            # 计算双手距离
            left_center = left_landmarks[9]
            right_center = right_landmarks[9]

            distance = self.get_distance_between_points(
                left_center[1], left_center[2],
                right_center[1], right_center[2]
            )

            # 双手张开/合拢
            if distance > 200:
                gestures["hands_spread"] = min(distance / 300, 1.0)
            elif distance < 100:
                gestures["hands_together"] = 1.0 - (distance / 100)

            # 双手拳头
            left_fingers = self.get_fingers_up(left_landmarks)
            right_fingers = self.get_fingers_up(right_landmarks)

            if sum(left_fingers) == 0 and sum(right_fingers) == 0:
                gestures["double_fist"] = 1.0

        return gestures

    def get_fingers_up(self, lmList: List[List[int]]) -> List[int]:
        """检测竖起的手指"""
        fingers = []

        if len(lmList) == 0:
            return fingers

        # 拇指
        if lmList[self.tipIds[0]][1] > lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # 其他四根手指
        for id in range(1, 5):
            if lmList[self.tipIds[id]][2] < lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def get_distance(self, p1: int, p2: int, lmList: List[List[int]]) -> float:
        """计算两点间距离"""
        if len(lmList) == 0:
            return 0
        x1, y1 = lmList[p1][1], lmList[p1][2]
        x2, y2 = lmList[p2][1], lmList[p2][2]
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def get_distance_between_points(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """计算任意两点间距离"""
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def is_circular_motion(self, positions: List[List]) -> bool:
        """检测是否为圆形运动"""
        if len(positions) < 8:
            return False

        # 简单的圆形检测算法
        center_x = sum(pos[0] for pos in positions) / len(positions)
        center_y = sum(pos[1] for pos in positions) / len(positions)

        # 计算每个点到中心的距离变化
        distances = []
        for pos in positions:
            dist = math.sqrt((pos[0] - center_x) ** 2 + (pos[1] - center_y) ** 2)
            distances.append(dist)

        # 如果距离变化不大，可能是圆形
        avg_dist = sum(distances) / len(distances)
        variance = sum((d - avg_dist) ** 2 for d in distances) / len(distances)

        return variance < (avg_dist * 0.3) ** 2  # 距离变化小于30%


class UnifiedPPTGestureController:
    """统一PPT手势识别播放器主类"""

    def __init__(self, config_file: str = "gesture_config.json"):
        self.gesture_detector = UnifiedGestureDetector()
        self.ppt_controller = PPTController()
        self.config_file = config_file

        # 初始化中文文本渲染器
        self.chinese_renderer = ChineseTextRenderer()

        # 加载手势配置
        self.gesture_configs = self.load_gesture_configs()

        # 状态变量
        self.running = True
        self.show_help = False
        self.calibration_mode = False

        # 性能监控
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()

        # 激光指示器相关
        self.laser_point = None
        self.draw_trail = []

        # 命令执行冷却控制
        self.command_cooldown_duration = 2.0  # 执行命令后冷却2秒
        self.last_command_execution_time = 0

        # 尝试自动初始化PPT
        self.auto_initialize_ppt()

    def auto_initialize_ppt(self):
        """自动初始化PPT演示"""
        try:
            print(" 正在搜索PPT文件...")
            ppt_file = self.ppt_controller.auto_select_ppt()

            if ppt_file:
                print(f" 找到PPT文件: {os.path.basename(ppt_file)}")
                user_input = input("是否要自动打开PPT演示？(y/n): ").lower().strip()

                if user_input in ['y', 'yes', '是', '']:
                    if self.ppt_controller.open_powerpoint_file(ppt_file):
                        print(" PPT演示已启动，可以开始手势控制")
                    else:
                        print(" PPT启动失败，将只显示手势检测")
                else:
                    print(" 跳过PPT自动启动，手动启动PPT后可使用手势控制")
            else:
                print(" 当前目录未找到PPT文件")
                print(" 提示：将PPT文件放在程序目录下，或手动打开PPT后使用手势控制")

        except Exception as e:
            print(f" PPT初始化过程中出现错误: {e}")
            print(" 继续运行程序，可手动打开PPT使用手势控制")

    def load_gesture_configs(self) -> Dict[str, GestureConfig]:
        """加载手势配置"""
        default_configs = {
            "next_slide": GestureConfig(
                name="下一页",
                gesture_type=GestureType.DYNAMIC,
                action=PPTAction.NEXT_SLIDE,
                motion_pattern="swipe_right",
                confidence_threshold=0.7
            ),
            "prev_slide": GestureConfig(
                name="上一页",
                gesture_type=GestureType.DYNAMIC,
                action=PPTAction.PREV_SLIDE,
                motion_pattern="swipe_left",
                confidence_threshold=0.7
            ),
            "pause": GestureConfig(
                name="暂停/播放",
                gesture_type=GestureType.STATIC,
                action=PPTAction.PLAY_PAUSE,
                finger_pattern=[0, 0, 0, 0, 0],  # 拳头
                confidence_threshold=0.9,
                enabled=False  # 禁用暂停/播放手势
            ),
            "exit": GestureConfig(
                name="退出",
                gesture_type=GestureType.DUAL_HAND,
                action=PPTAction.EXIT_PRESENTATION,
                confidence_threshold=0.8,
                hold_duration=2.0
            ),
            "laser": GestureConfig(
                name="激光指示器",
                gesture_type=GestureType.STATIC,
                action=PPTAction.LASER_POINTER,
                finger_pattern=[0, 1, 0, 0, 0],  # 食指
                confidence_threshold=0.8
            ),
            "fullscreen": GestureConfig(
                name="全屏切换",
                gesture_type=GestureType.STATIC,
                action=PPTAction.FULLSCREEN_TOGGLE,
                finger_pattern=[1, 1, 1, 1, 1],  # 张开手掌
                confidence_threshold=0.9,
                hold_duration=1.0,
                enabled=False  # 禁用全屏切换手势
            )
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    configs = {}
                    for key, value in data.items():
                        # 处理枚举类型转换
                        if 'gesture_type' in value and isinstance(value['gesture_type'], str):
                            value['gesture_type'] = GestureType(value['gesture_type'])
                        if 'action' in value and isinstance(value['action'], str):
                            value['action'] = PPTAction(value['action'])
                        configs[key] = GestureConfig(**value)
                    return configs
            except Exception as e:
                print(f"配置文件加载失败，使用默认配置: {e}")

        return default_configs

    def save_gesture_configs(self):
        """保存手势配置到文件"""
        try:
            configs_dict = {}
            for key, config in self.gesture_configs.items():
                # 转换为可序列化的字典
                config_dict = asdict(config)
                # 处理枚举类型
                if hasattr(config_dict['gesture_type'], 'value'):
                    config_dict['gesture_type'] = config_dict['gesture_type'].value
                if hasattr(config_dict['action'], 'value'):
                    config_dict['action'] = config_dict['action'].value
                configs_dict[key] = config_dict
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(configs_dict, f, ensure_ascii=False, indent=2)
            print(f" 配置已保存到: {self.config_file}")
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")

    def process_frame(self, img):
        """处理视频帧"""
        # 翻转图像 (镜像效果)
        img = cv.flip(img, 1)

        # 检测手部
        img = self.gesture_detector.detector.findHands(img)
        lmList = self.gesture_detector.detector.findPosition(img, draw=False)

        # 识别手势
        detected_gestures = {}
        current_time = time.time()

        if len(lmList) != 0:
            # 静态手势检测
            static_gestures = self.gesture_detector.detect_static_gesture(lmList)
            detected_gestures.update(static_gestures)

            # 动态手势检测
            dynamic_gestures = self.gesture_detector.detect_dynamic_gesture(lmList)
            detected_gestures.update(dynamic_gestures)

            # 激光指示器功能 (实时更新，不受冷却限制)
            if self.ppt_controller.laser_mode:
                index_tip = lmList[8]  # 食指尖
                self.laser_point = (index_tip[1], index_tip[2])

        # 双手手势检测 (需要更复杂的实现)
        # dual_gestures = self.gesture_detector.detect_dual_hand_gesture(left_lm, right_lm)
        # detected_gestures.update(dual_gestures)

        # 检查命令执行冷却状态
        current_time = time.time()
        in_cooldown = (current_time - self.last_command_execution_time) < self.command_cooldown_duration

        # 实时进行手势检测（不受冷却影响）
        if detected_gestures:
            self.match_and_execute_gestures(detected_gestures, current_time, in_cooldown)

        # 绘制界面元素
        self.draw_ui(img, detected_gestures, lmList)

        return img

    def match_and_execute_gestures(self, detected_gestures: Dict[str, float], current_time: float, in_cooldown: bool):
        """匹配检测到的手势并执行相应操作"""

        # 如果在冷却期内，不执行任何命令，只进行手势检测显示
        if in_cooldown:
            return

        for config_key, config in self.gesture_configs.items():
            if not config.enabled:
                continue

            matched = False
            confidence = 0.0

            # 根据手势类型进行匹配
            if config.gesture_type == GestureType.STATIC:
                # 静态手势匹配
                for gesture_name, gesture_confidence in detected_gestures.items():
                    if self.matches_static_pattern(gesture_name, config):
                        confidence = gesture_confidence
                        matched = True
                        break

            elif config.gesture_type == GestureType.DYNAMIC:
                # 动态手势匹配
                if config.motion_pattern in detected_gestures:
                    confidence = detected_gestures[config.motion_pattern]
                    matched = True

            # 检查置信度阈值
            if matched and confidence >= config.confidence_threshold:
                # 检查持续时间要求
                if config.hold_duration > 0:
                    if config_key not in self.gesture_detector.last_gesture_time:
                        self.gesture_detector.last_gesture_time[config_key] = current_time
                    elif current_time - self.gesture_detector.last_gesture_time[config_key] >= config.hold_duration:
                        self.ppt_controller.execute_action(config.action)
                        self.gesture_detector.last_gesture_time[config_key] = current_time
                        # 记录命令执行时间，开始冷却
                        self.last_command_execution_time = current_time
                        print(f" 执行命令: {config.name}, 冷却{self.command_cooldown_duration}秒")
                else:
                    # 防止重复触发
                    if config_key not in self.gesture_detector.last_gesture_time or \
                            current_time - self.gesture_detector.last_gesture_time[config_key] > 1.0:
                        self.ppt_controller.execute_action(config.action)
                        self.gesture_detector.last_gesture_time[config_key] = current_time
                        # 记录命令执行时间，开始冷却
                        self.last_command_execution_time = current_time
                        print(f" 执行命令: {config.name}, 冷却{self.command_cooldown_duration}秒")
            else:
                # 重置持续时间计时器
                if config_key in self.gesture_detector.last_gesture_time:
                    del self.gesture_detector.last_gesture_time[config_key]

    def matches_static_pattern(self, gesture_name: str, config: GestureConfig) -> bool:
        """检查静态手势是否匹配配置模式"""
        # 简化的匹配逻辑，实际可以更复杂
        pattern_map = {
            "fist": [0, 0, 0, 0, 0],
            "point": [0, 1, 0, 0, 0],
            "thumb_up": [1, 0, 0, 0, 0],
            "peace": [0, 1, 1, 0, 0],
            "ok": [1, 1, 0, 0, 0],
            "three": [0, 1, 1, 1, 0],
            "four": [0, 1, 1, 1, 1],
            "open_hand": [1, 1, 1, 1, 1]
        }

        if gesture_name in pattern_map and config.finger_pattern:
            return pattern_map[gesture_name] == config.finger_pattern
        return False

    def draw_ui(self, img, detected_gestures: Dict[str, float], lmList):
        """绘制用户界面"""
        h, w, c = img.shape

        # 绘制FPS
        cv.putText(img, f"FPS: {int(self.fps)}", (10, 30),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 绘制PPT状态信息
        ppt_status = "演示中" if self.ppt_controller.is_presentation_active else "待机"
        status_text = f"PPT状态: {ppt_status}"
        img = put_text_auto(img, status_text, (10, 60), 18, (0, 255, 255))

        # 绘制当前PPT文件信息
        if self.ppt_controller.current_ppt_path:
            ppt_name = os.path.basename(self.ppt_controller.current_ppt_path)
            ppt_info = f"文件: {ppt_name}"
            img = put_text_auto(img, ppt_info, (10, 90), 18, (255, 255, 255))

        # 绘制命令冷却状态信息
        current_time = time.time()
        time_since_execution = current_time - self.last_command_execution_time
        cooldown_remaining = max(0, self.command_cooldown_duration - time_since_execution)

        if cooldown_remaining > 0:
            cooldown_text = f"命令冷却中: {cooldown_remaining:.1f}秒 (冷却时长: {self.command_cooldown_duration}秒)"
            color = (0, 165, 255)  # 橙色表示冷却中
        else:
            cooldown_text = f"可执行命令 (冷却时长: {self.command_cooldown_duration}秒)"
            color = (0, 255, 0)  # 绿色表示可执行

        img = put_text_auto(img, cooldown_text, (10, 120), 16, color)

        # 绘制检测到的手势
        y_offset = 150
        for gesture_name, confidence in detected_gestures.items():
            if confidence > 0.5:  # 只显示高置信度的手势
                text = f"{gesture_name}: {confidence:.2f}"
                cv.putText(img, text, (10, y_offset),
                           cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                y_offset += 25

        # 绘制激光指示器
        if self.laser_point and self.ppt_controller.is_presentation_active:
            cv.circle(img, self.laser_point, 10, (0, 0, 255), -1)
            cv.circle(img, self.laser_point, 15, (255, 255, 255), 2)

        # 绘制手部关键点 (如果需要)
        if len(lmList) != 0 and self.calibration_mode:
            for lm in lmList:
                cv.circle(img, (lm[1], lm[2]), 5, (255, 0, 255), -1)

        # 绘制帮助信息
        if self.show_help:
            self.draw_help_overlay(img)

    def draw_help_overlay(self, img):
        """绘制帮助覆盖层"""
        h, w = img.shape[:2]
        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        overlay[:] = (0, 0, 0)  # 黑色背景

        help_text = [
            "手势控制帮助:",
            "右滑 - 下一页",
            "左滑 - 上一页",
            "食指 - 激光指示器",
            "双拳(长按) - 退出",
            "",
            "系统特性:",
            "✓ 实时手势检测",
            "✓ 命令执行后冷却防误触",
            "",
            "按键控制:",
            "H - 显示/隐藏帮助",
            "C - 校准模式",
            "S - 保存配置",
            "+ - 增加冷却时间",
            "- - 减少冷却时间",
            "Q/ESC - 退出程序"
        ]

        y = 50
        for text in help_text:
            overlay = put_text_auto(overlay, text, (50, y), 21, (255, 255, 255))
            y += 35

        # 半透明效果
        cv.addWeighted(img, 0.3, overlay, 0.7, 0, img)

    def run(self):
        """运行主程序"""
        print(" 统一PPT手势识别播放器启动")
        print(" 支持的手势:")
        for key, config in self.gesture_configs.items():
            if config.enabled:  # 只显示启用的手势
                print(f"  - {config.name}: {config.gesture_type.value}")
        print(" 按 'H' 显示帮助，按 'Q' 退出")
        print("=" * 60)

        cap = cv.VideoCapture(0)
        pTime = 0

        # 设置摄像头参数
        cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv.CAP_PROP_FPS, 30)

        while self.running:
            success, img = cap.read()
            if not success:
                print(" 无法读取摄像头")
                break

            # 处理当前帧
            img = self.process_frame(img)

            # 计算FPS
            cTime = time.time()
            if cTime != pTime:
                self.fps = 1 / (cTime - pTime)
            pTime = cTime
            self.frame_count += 1

            # 显示图像
            cv.imshow('统一PPT手势识别播放器', img)

            # 处理按键
            key = cv.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # Q或ESC退出
                self.running = False
            elif key == ord('h'):  # H显示/隐藏帮助
                self.show_help = not self.show_help
            elif key == ord('c'):  # C校准模式
                self.calibration_mode = not self.calibration_mode
                print(f"校准模式: {'开启' if self.calibration_mode else '关闭'}")
            elif key == ord('s'):  # S保存配置
                self.save_gesture_configs()
            elif key == ord('+') or key == ord('='):  # +键增加冷却时间
                self.command_cooldown_duration = min(5.0, self.command_cooldown_duration + 0.5)
                print(f"命令冷却时间增加到: {self.command_cooldown_duration}秒")
            elif key == ord('-'):  # -键减少冷却时间
                self.command_cooldown_duration = max(0.5, self.command_cooldown_duration - 0.5)
                print(f"命令冷却时间减少到: {self.command_cooldown_duration}秒")

        # 清理资源
        cap.release()
        cv.destroyAllWindows()

        # 显示统计信息
        total_time = time.time() - self.start_time
        avg_fps = self.frame_count / total_time if total_time > 0 else 0
        print(f"\n程序运行统计:")
        print(f"   总运行时间: {total_time:.1f}秒")
        print(f"   处理帧数: {self.frame_count}")
        print(f"   平均FPS: {avg_fps:.1f}")
        print("统一PPT手势识别播放器已退出")


def main():
    """主函数"""
    try:
        controller = UnifiedPPTGestureController()
        controller.run()
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        print(f" 程序运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
