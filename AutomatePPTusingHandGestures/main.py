import os
import cv2 as cv
import handTrackingModule as hmt
import pyautogui as pt
import time

def rescaleFrame(frame, scale = 0.75):
    width = int(frame.shape[1] * scale)
    height = int(frame.shape[0] * scale)
    dimension = (width, height)
    return cv.resize(frame, dimension, interpolation=cv.INTER_AREA)

pprs = os.startfile('C:/Users/liuyo/Documents/GitHub/Tongji-University-SE-HCI-Final/AutomatePPTusingHandGestures/test.pptx')
pt._handlePause(1)
pt.press('f5')


pTime = 0
cTime = 0
cap = cv.VideoCapture(0)
detector = hmt.handDetector()
count = 0
curr = 0
pre = 0

while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPosition(img)
    rescaledFrame = rescaleFrame(img, scale=1.25)

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime

    # cv.putText(img, str(int(fps)), (10, 70), cv.FONT_HERSHEY_PLAIN, 3, (255, 0, 22), 2)
    # cv.imshow('Video', rescaledFrame)

    if len(lmList) != 0:
        MiddleTip = lmList[12]
        curr = MiddleTip[1]
        pre = MiddleTip[2]
        # The Below Method Only Works For Left Hand
        if curr < 200:
            pt.press('space')
        if pre < 200:
            pt.press('left')


        print(lmList[16])


cap.relese()
cv.DestroyAllWindows()
cv.waitKey(0)
