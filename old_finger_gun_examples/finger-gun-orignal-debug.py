import cv2
import mediapipe as mp
import math
import numpy as np
import time

# Global variables for slider values
thumb_index_threshold = 35
middle_ring_threshold = 8
ring_pinky_threshold = 8
index_wrist_threshold = 10
shoot_velocity_threshold = 0.1  # Adjust for sensitivity (positive for downward movement)
shoot_distance_threshold = 0.1  # Adjust distance threshold

# Global variables for shooting detection and cooldown
shooting_detected = False
last_shoot_time = 0
cooldown_duration = 0.5  # 0.5 seconds cooldown
previous_thumb_y = None
previous_time = 0

def create_trackbars():
    cv2.namedWindow("Threshold Controls")
    cv2.createTrackbar("Thumb-Index", "Threshold Controls", thumb_index_threshold, 100, lambda x: None)
    cv2.createTrackbar("Middle-Ring", "Threshold Controls", middle_ring_threshold, 100, lambda x: None)
    cv2.createTrackbar("Ring-Pinky", "Threshold Controls", ring_pinky_threshold, 100, lambda x: None)
    cv2.createTrackbar("Index-Wrist", "Threshold Controls", index_wrist_threshold, 100, lambda x: None)
    cv2.createTrackbar("Shoot Velocity Threshold", "Threshold Controls", int(shoot_velocity_threshold * 1000), 100, lambda x: None)
    cv2.createTrackbar("Shoot Distance Threshold", "Threshold Controls", int(shoot_distance_threshold * 1000), 100, lambda x: None)

def get_trackbar_values():
    global thumb_index_threshold, middle_ring_threshold, ring_pinky_threshold, index_wrist_threshold, shoot_velocity_threshold, shoot_distance_threshold
    thumb_index_threshold = cv2.getTrackbarPos("Thumb-Index", "Threshold Controls")
    middle_ring_threshold = cv2.getTrackbarPos("Middle-Ring", "Threshold Controls")
    ring_pinky_threshold = cv2.getTrackbarPos("Ring-Pinky", "Threshold Controls")
    index_wrist_threshold = cv2.getTrackbarPos("Index-Wrist", "Threshold Controls")
    shoot_velocity_threshold = cv2.getTrackbarPos("Shoot Velocity Threshold", "Threshold Controls") / 1000.0
    shoot_distance_threshold = cv2.getTrackbarPos("Shoot Distance Threshold", "Threshold Controls") / 1000.0

def calculate_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def is_finger_gun(hand_landmarks):
    if hand_landmarks is None:
        return False, None

    thumb_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.RING_FINGER_TIP]
    pinky_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.PINKY_TIP]
    wrist = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.WRIST]
    middle_pip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.MIDDLE_FINGER_PIP] 

    thumb_index_dist = calculate_distance((thumb_tip.x, thumb_tip.y), (index_tip.x, index_tip.y))
    middle_ring_dist = calculate_distance((middle_tip.x, middle_tip.y), (ring_tip.x, ring_tip.y))
    ring_pinky_dist = calculate_distance((ring_tip.x, ring_tip.y), (pinky_tip.x, pinky_tip.y))
    index_wrist_dist = calculate_distance((index_tip.x, index_tip.y), (wrist.x, wrist.y))
    thumb_middle_dist = calculate_distance((thumb_tip.x, thumb_tip.y), (middle_pip.x, middle_pip.y)) 

    get_trackbar_values()
    scaled_thumb_index = thumb_index_threshold / 100.0
    scaled_middle_ring = middle_ring_threshold / 100.0
    scaled_ring_pinky = ring_pinky_threshold / 100.0
    scaled_index_wrist = index_wrist_threshold / 100.0

    is_thumb_near_index = thumb_index_dist < scaled_thumb_index
    is_middle_ring_close = middle_ring_dist < scaled_middle_ring
    is_ring_pinky_close = ring_pinky_dist < scaled_ring_pinky
    is_index_extended = index_wrist_dist > scaled_index_wrist

    if is_thumb_near_index and is_middle_ring_close and is_ring_pinky_close and is_index_extended:
        return True, (int(index_tip.x * frame_width), int(index_tip.y * frame_height)), thumb_tip, middle_pip, thumb_middle_dist #changed this line
    else:
        return False, None, None, None, None

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.6, max_num_hands=1)
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

frame_width = int(cap.get(3))
frame_height = int(cap.get(4))

create_trackbars()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)

    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    results = hands.process(image)
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            is_gun, index_tip_coords, thumb_tip, middle_mcp, thumb_middle_dist = is_finger_gun(hand_landmarks)
            if is_gun:
                cv2.putText(image, "Finger Gun!", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                if index_tip_coords:
                    cv2.circle(image, index_tip_coords, 10, (0, 0, 255), -1)

                    # Highlight thumb tip and middle MCP
                    thumb_tip_x, thumb_tip_y = int(thumb_tip.x * frame_width), int(thumb_tip.y * frame_height)
                    middle_mcp_x, middle_mcp_y = int(middle_mcp.x * frame_width), int(middle_mcp.y * frame_height)
                    cv2.circle(image, (thumb_tip_x, thumb_tip_y), 5, (0, 255, 0), -1)  # Highlight thumb tip
                    cv2.circle(image, (middle_mcp_x, middle_mcp_y), 5, (0, 255, 0), -1)  # Highlight middle MCP

                current_time = time.time()
                current_thumb_y = thumb_tip.y #Added this line.
                if previous_thumb_y is not None:
                    delta_time = current_time - previous_time
                    if delta_time != 0:
                        thumb_velocity = (current_thumb_y - previous_thumb_y) / delta_time
                    else:
                        thumb_velocity = 0

                    if thumb_velocity > shoot_velocity_threshold and thumb_middle_dist < shoot_distance_threshold:
                        if not shooting_detected and current_time - last_shoot_time > cooldown_duration:
                            cv2.putText(image, "Shoot!", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            print(f"Shoot! {thumb_velocity} > {shoot_velocity_threshold} and {thumb_middle_dist} < {shoot_distance_threshold}")
                            shooting_detected = True
                            last_shoot_time = current_time
                    else:
                        shooting_detected = False

                previous_thumb_y = current_thumb_y
                previous_time = current_time

            else:
                shooting_detected = False
                previous_thumb_y = None
                previous_time = 0

    else:
        shooting_detected = False
        previous_thumb_y = None
        previous_time = 0

    cv2.imshow('Hand Tracking', image)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()