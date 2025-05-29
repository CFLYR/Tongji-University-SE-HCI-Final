"""
手势识别调试工具 (修复版)
基于MediaPipe的手势检测和分析，所有显示文本使用英文以避免字体问题
"""

import cv2 as cv
import mediapipe as mp
import numpy as np
import time
import math
from handTrackingModule import handDetector


class GestureDetector:
    def __init__(self):
        self.detector = handDetector()
        self.tipIds = [4, 8, 12, 16, 20]  # 拇指、食指、中指、无名指、小指的指尖ID
        
    def get_fingers_up(self, lmList):
        """检测哪些手指是竖起的"""
        fingers = []
        
        if len(lmList) == 0:
            return fingers
            
        # 拇指 (特殊处理，因为拇指的方向不同)
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
    
    def get_distance(self, p1, p2, lmList):
        """计算两点之间的距离"""
        if len(lmList) == 0:
            return 0
        x1, y1 = lmList[p1][1], lmList[p1][2]
        x2, y2 = lmList[p2][1], lmList[p2][2]
        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return distance
    
    def detect_gesture(self, lmList):
        """检测具体的手势 - 返回英文名称避免显示问题"""
        if len(lmList) == 0:
            return ["No Gesture"]
            
        fingers = self.get_fingers_up(lmList)
        total_fingers = fingers.count(1)
        
        # 定义各种手势 - 使用英文避免显示问题
        gestures = []
        
        # 数字手势
        if total_fingers == 0:
            gestures.append("Fist")
        elif total_fingers == 1:
            if fingers[1] == 1:  # 只有食指
                gestures.append("Point/Num1")
            elif fingers[0] == 1:  # 只有拇指
                gestures.append("ThumbUp/Num1")
        elif total_fingers == 2:
            if fingers[1] == 1 and fingers[2] == 1:  # 食指和中指
                gestures.append("V-Sign/Num2")
            elif fingers[0] == 1 and fingers[1] == 1:  # 拇指和食指
                # 检查是否是OK手势
                distance = self.get_distance(4, 8, lmList)
                if distance < 40:
                    gestures.append("OK-Sign")
                else:
                    gestures.append("Num2")
        elif total_fingers == 3:
            if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1:
                gestures.append("Num3")
            elif fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1:
                gestures.append("Num3")
        elif total_fingers == 4:
            if fingers[0] == 0:  # 拇指收起
                gestures.append("Num4")
            else:
                gestures.append("Num4(ThumbOut)")
        elif total_fingers == 5:
            gestures.append("OpenHand/Num5/Stop")
            
        # 特殊手势检测
        # L手势
        if fingers[0] == 1 and fingers[1] == 1 and total_fingers == 2:
            thumb_tip = lmList[4]
            index_tip = lmList[8]
            thumb_ip = lmList[3]
            index_pip = lmList[6]
            
            angle = self.calculate_angle(thumb_ip, thumb_tip, index_tip)
            if 70 < angle < 110:
                gestures.append("L-Sign")
        
        # 摇滚手势
        if fingers[1] == 1 and fingers[4] == 1 and fingers[2] == 0 and fingers[3] == 0:
            gestures.append("Rock-Sign")
            
        # 位置相关的手势
        hand_center = lmList[9]
        if hand_center[1] < 200:
            gestures.append("Position: Left")
        elif hand_center[1] > 440:
            gestures.append("Position: Right")
        else:
            gestures.append("Position: Center")
            
        if hand_center[2] < 200:
            gestures.append("Position: Top")
        elif hand_center[2] > 360:
            gestures.append("Position: Bottom")
        else:
            gestures.append("Position: Middle")
            
        return gestures if gestures else ["Unknown Gesture"]
    
    def calculate_angle(self, p1, p2, p3):
        """计算三点构成的角度"""
        x1, y1 = p1[1], p1[2]
        x2, y2 = p2[1], p2[2]
        x3, y3 = p3[1], p3[2]
        
        angle = math.degrees(math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2))
        return abs(angle)


def main():
    """主函数 - 运行手势识别调试工具"""
    print("=" * 60)
    print("手势识别调试工具启动 (显示使用英文避免乱码)")
    print("支持的手势类型:")
    print("- 数字手势: 0-5")
    print("- 特殊手势: 拳头、点赞、OK、V手势、L手势、摇滚手势等")
    print("- 位置检测: 左右上下位置")
    print("按 'q' 键退出")
    print("=" * 60)
    
    cap = cv.VideoCapture(0)
    gesture_detector = GestureDetector()
    
    # 性能监控
    pTime = 0
    frame_count = 0
    
    while True:
        success, img = cap.read()
        if not success:
            print("无法读取摄像头")
            break
            
        # 翻转图像，使其像镜子一样
        img = cv.flip(img, 1)
        
        # 检测手部
        img = gesture_detector.detector.findHands(img)
        lmList = gesture_detector.detector.findPosition(img, draw=False)
        
        # FPS计算
        cTime = time.time()
        fps = 1 / (cTime - pTime) if cTime != pTime else 0
        pTime = cTime
        frame_count += 1
        
        # 检测手势
        if len(lmList) != 0:
            gestures = gesture_detector.detect_gesture(lmList)
            fingers = gesture_detector.get_fingers_up(lmList)
            
            # 在图像上显示信息 (全部使用英文)
            cv.putText(img, f"FPS: {int(fps)}", (10, 30), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv.putText(img, f"Fingers: {fingers}", (10, 60), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            
            cv.putText(img, f"Count: {fingers.count(1)}", (10, 90), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            
            # 显示检测到的手势 (最多显示3个)
            for i, gesture in enumerate(gestures[:3]):
                cv.putText(img, f"Gesture{i+1}: {gesture}", (10, 120 + i*30), 
                          cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # 在终端输出详细信息 (中文注释，方便理解)
            if frame_count % 30 == 0:  # 每30帧输出一次，避免刷屏
                print(f"\n帧数: {frame_count} | FPS: {int(fps)}")
                print(f"手指状态: {fingers} (1=伸出, 0=收起)")
                print(f"竖起手指数: {fingers.count(1)}")
                print("检测到的手势:")
                for i, gesture in enumerate(gestures, 1):
                    print(f"  {i}. {gesture}")
                    
                # 显示关键点坐标
                print(f"拇指尖位置: ({lmList[4][1]}, {lmList[4][2]})")
                print(f"食指尖位置: ({lmList[8][1]}, {lmList[8][2]})")
                print(f"手掌中心位置: ({lmList[9][1]}, {lmList[9][2]})")
        else:
            cv.putText(img, f"FPS: {int(fps)}", (10, 30), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv.putText(img, "No Hand Detected", (10, 60), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # 显示图像
        cv.imshow('Gesture Recognition Debug Tool', img)
        
        # 检查退出键
        key = cv.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # 'q'键或ESC键退出
            break
    
    # 清理资源
    cap.release()
    cv.destroyAllWindows()
    print("\n手势识别调试工具已退出")
    print(f"总共处理了 {frame_count} 帧")


if __name__ == '__main__':
    main()
