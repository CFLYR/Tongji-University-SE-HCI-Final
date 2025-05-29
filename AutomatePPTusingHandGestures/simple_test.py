"""
简化版手势调试工具
快速测试基本手势识别功能
"""

import cv2 as cv
import handTrackingModule as hmt
import time

def detect_basic_gestures(fingers):
    """检测基本手势"""
    total = fingers.count(1)
    
    gesture_map = {
        0: "拳头 ✊",
        1: "一个手指 ☝️" if fingers[1] == 1 else "拇指 👍",
        2: "两个手指 ✌️" if fingers[1] == 1 and fingers[2] == 1 else "其他双指",
        3: "三个手指 🤟",
        4: "四个手指 🖐️",
        5: "张开手掌 ✋"
    }
    
    return gesture_map.get(total, "未知手势")

def main():
    print("🚀 简化版手势调试工具启动...")
    print("支持检测: 拳头、1-5个手指的基本手势")
    print("按 'q' 退出\n")
    
    cap = cv.VideoCapture(0)
    detector = hmt.handDetector()
    
    while True:
        success, img = cap.read()
        if not success:
            break
            
        img = cv.flip(img, 1)  # 镜像翻转
        img = detector.findHands(img)
        lmList = detector.findPosition(img, draw=False)
        
        if len(lmList) != 0:
            fingers = detector.fingersUp(lmList)
            gesture = detect_basic_gestures(fingers)
            finger_count = fingers.count(1)
            
            # 显示信息
            cv.putText(img, f"手指: {fingers}", (10, 50), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            cv.putText(img, f"数量: {finger_count}", (10, 100), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv.putText(img, f"手势: {gesture}", (10, 150), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            # 控制台输出
            print(f"手指状态: {fingers} | 数量: {finger_count} | 手势: {gesture}")
        else:
            cv.putText(img, "未检测到手", (10, 50), 
                      cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        cv.imshow("手势调试", img)
        
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv.destroyAllWindows()
    print("调试工具已退出")

if __name__ == "__main__":
    main()
