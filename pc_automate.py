import cv2
import mediapipe as mp
import pyautogui
import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc
import math

# Setup camera and screen
cap = cv2.VideoCapture(0)
screen_width, screen_height = pyautogui.size()

# MediaPipe hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Volume control setup
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
vol_range = volume.GetVolumeRange()
min_vol, max_vol = vol_range[0], vol_range[1]

while True:
    success, frame = cap.read()
    if not success:
        break

    # Flip and convert image
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process hands
    results = hands.process(rgb_frame)
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Get coordinates of thumb tip and index tip
            lm_list = hand_landmarks.landmark
            thumb = lm_list[mp_hands.HandLandmark.THUMB_TIP]
            index = lm_list[mp_hands.HandLandmark.INDEX_FINGER_TIP]

            x1, y1 = int(thumb.x * w), int(thumb.y * h)
            x2, y2 = int(index.x * w), int(index.y * h)

            # Draw line and circle between tips
            cv2.circle(frame, (x1, y1), 8, (255, 0, 0), -1)
            cv2.circle(frame, (x2, y2), 8, (255, 0, 0), -1)
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

            # Calculate distance between thumb and index finger
            length = math.hypot(x2 - x1, y2 - y1)

            # Volume control: pinch fingers to adjust
            vol = np.interp(length, [20, 150], [min_vol, max_vol])
            volume.SetMasterVolumeLevel(vol, None)

            # Brightness control: use middle finger height
            middle = lm_list[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
            middle_y = int(middle.y * h)
            brightness = np.interp(middle_y, [h, 0], [0, 100])
            sbc.set_brightness(int(brightness))

            # Mouse movement: move index finger
            pyautogui.moveTo(index.x * screen_width, index.y * screen_height)

    cv2.imshow("Gesture Control", frame)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

