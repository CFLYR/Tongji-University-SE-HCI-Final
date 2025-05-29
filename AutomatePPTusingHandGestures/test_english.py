"""
Gesture Recognition Debug Tool (English Version)
Based on MediaPipe for gesture detection and analysis
Supports recognition of various common gestures with real-time display
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
        self.tipIds = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky finger tips
        
    def get_fingers_up(self, lmList):
        """Detect which fingers are up"""
        fingers = []
        
        if len(lmList) == 0:
            return fingers
            
        # Thumb (special handling due to different orientation)
        if lmList[self.tipIds[0]][1] > lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)
            
        # Other four fingers
        for id in range(1, 5):
            if lmList[self.tipIds[id]][2] < lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
                
        return fingers
    
    def get_distance(self, p1, p2, lmList):
        """Calculate distance between two points"""
        if len(lmList) == 0:
            return 0
        x1, y1 = lmList[p1][1], lmList[p1][2]
        x2, y2 = lmList[p2][1], lmList[p2][2]
        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return distance
    
    def detect_gesture(self, lmList):
        """Detect specific gestures"""
        if len(lmList) == 0:
            return ["No Gesture"]
            
        fingers = self.get_fingers_up(lmList)
        total_fingers = fingers.count(1)
        
        # Define various gestures
        gestures = []
        
        # Number gestures
        if total_fingers == 0:
            gestures.append("Fist")
        elif total_fingers == 1:
            if fingers[1] == 1:  # Only index finger
                gestures.append("Point/Num1")
            elif fingers[0] == 1:  # Only thumb
                gestures.append("ThumbUp/Num1")
        elif total_fingers == 2:
            if fingers[1] == 1 and fingers[2] == 1:  # Index and middle
                gestures.append("V-Sign/Num2")
            elif fingers[0] == 1 and fingers[1] == 1:  # Thumb and index
                # Check for OK gesture (thumb and index form circle)
                distance = self.get_distance(4, 8, lmList)
                if distance < 40:  # Close distance, might be OK gesture
                    gestures.append("OK-Sign")
                else:
                    gestures.append("Num2")
        elif total_fingers == 3:
            if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1:
                gestures.append("Num3")
            elif fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1:
                gestures.append("Num3")
        elif total_fingers == 4:
            if fingers[0] == 0:  # Thumb folded
                gestures.append("Num4")
            else:
                gestures.append("Num4(ThumbOut)")
        elif total_fingers == 5:
            gestures.append("OpenHand/Num5/Stop")
            
        # Special gesture detection
        # L gesture (thumb and index perpendicular)
        if fingers[0] == 1 and fingers[1] == 1 and total_fingers == 2:
            thumb_tip = lmList[4]
            index_tip = lmList[8]
            thumb_ip = lmList[3]
            index_pip = lmList[6]
            
            # Calculate angle to determine L shape
            angle = self.calculate_angle(thumb_ip, thumb_tip, index_tip)
            if 70 < angle < 110:  # Close to 90 degrees
                gestures.append("L-Sign")
        
        # Rock gesture (index and pinky extended)
        if fingers[1] == 1 and fingers[4] == 1 and fingers[2] == 0 and fingers[3] == 0:
            gestures.append("Rock-Sign")
            
        # Position-related gestures
        hand_center = lmList[9]  # Hand center
        if hand_center[1] < 200:  # Hand on left
            gestures.append("Position: Left")
        elif hand_center[1] > 440:  # Hand on right
            gestures.append("Position: Right")
        else:
            gestures.append("Position: Center")
            
        if hand_center[2] < 200:  # Hand on top
            gestures.append("Position: Top")
        elif hand_center[2] > 360:  # Hand on bottom
            gestures.append("Position: Bottom")
        else:
            gestures.append("Position: Middle")
            
        return gestures if gestures else ["Unknown Gesture"]
    
    def calculate_angle(self, p1, p2, p3):
        """Calculate angle formed by three points"""
        x1, y1 = p1[1], p1[2]
        x2, y2 = p2[1], p2[2]
        x3, y3 = p3[1], p3[2]
        
        angle = math.degrees(math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2))
        return abs(angle)


def main():
    """Main function - Run gesture recognition debug tool"""
    print("=" * 60)
    print("Gesture Recognition Debug Tool Started")
    print("Supported gesture types:")
    print("- Number gestures: 0-5")
    print("- Special gestures: Fist, ThumbUp, OK, V-Sign, L-Sign, Rock-Sign, etc.")
    print("- Position detection: Left/Right/Top/Bottom positions")
    print("Press 'q' to exit")
    print("=" * 60)
    
    cap = cv.VideoCapture(0)
    gesture_detector = GestureDetector()
    
    # Performance monitoring
    pTime = 0
    frame_count = 0
    
    while True:
        success, img = cap.read()
        if not success:
            print("Cannot read from camera")
            break
            
        # Flip image to make it mirror-like
        img = cv.flip(img, 1)
        
        # Detect hands
        img = gesture_detector.detector.findHands(img)
        lmList = gesture_detector.detector.findPosition(img, draw=False)
        
        # FPS calculation
        cTime = time.time()
        fps = 1 / (cTime - pTime) if cTime != pTime else 0
        pTime = cTime
        frame_count += 1
        
        # Detect gestures
        if len(lmList) != 0:
            gestures = gesture_detector.detect_gesture(lmList)
            fingers = gesture_detector.get_fingers_up(lmList)
            
            # Display information on image (English only)
            cv.putText(img, f"FPS: {int(fps)}", (10, 30), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv.putText(img, f"Fingers: {fingers}", (10, 60), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            
            cv.putText(img, f"Count: {fingers.count(1)}", (10, 90), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            
            # Display detected gestures (max 3 shown)
            for i, gesture in enumerate(gestures[:3]):
                cv.putText(img, f"Gesture{i+1}: {gesture}", (10, 120 + i*30), 
                          cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # Terminal output detailed information
            if frame_count % 30 == 0:  # Output every 30 frames to avoid spam
                print(f"\nFrame: {frame_count} | FPS: {int(fps)}")
                print(f"Finger Status: {fingers} (1=up, 0=down)")
                print(f"Fingers Up Count: {fingers.count(1)}")
                print("Detected Gestures:")
                for i, gesture in enumerate(gestures, 1):
                    print(f"  {i}. {gesture}")
                    
                # Display key point coordinates (optional)
                print(f"Thumb Tip Position: ({lmList[4][1]}, {lmList[4][2]})")
                print(f"Index Tip Position: ({lmList[8][1]}, {lmList[8][2]})")
                print(f"Hand Center Position: ({lmList[9][1]}, {lmList[9][2]})")
        else:
            cv.putText(img, f"FPS: {int(fps)}", (10, 30), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv.putText(img, "No Hand Detected", (10, 60), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Display image
        cv.imshow('Gesture Recognition Debug Tool', img)
        
        # Check exit key
        key = cv.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # 'q' key or ESC key to exit
            break
    
    # Clean up resources
    cap.release()
    cv.destroyAllWindows()
    print("\nGesture Recognition Debug Tool Exited")
    print(f"Total frames processed: {frame_count}")


if __name__ == '__main__':
    main()