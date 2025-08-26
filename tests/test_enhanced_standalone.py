#!/usr/bin/env python3
"""
Standalone test script for enhanced hand tracker
Run this from the project root directory
"""

# Standard library imports
import os
import sys

# Add src directories to path (go up one level from tests/ to project root)
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(project_root, "src"))
sys.path.insert(0, os.path.join(project_root, "src", "game"))
sys.path.insert(0, os.path.join(project_root, "src", "utils"))

# Third-party imports
import cv2
import numpy as np

# Import the trackers directly
try:
    # Try new location first
    from game.cv.finger_gun_detection import EnhancedHandTracker
except ImportError:
    # Fallback to old location
    from enhanced_hand_tracker import EnhancedHandTracker

from hand_tracker import HandTracker


def draw_debug_info(frame, stats, tracker):
    """Draw debug information on frame"""
    y_offset = 30
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 2

    # Draw problem zone rectangle (full width at bottom)
    # Full width, bottom 160 pixels of 640x480
    problem_x_min = 0  # Full width
    problem_x_max = 640  # Full width
    problem_y_min = 480 - 160  # 320 (160 pixels from bottom)
    problem_y_max = 480  # Bottom edge of camera

    # Draw problem zone with transparency
    overlay = frame.copy()

    # Highlight the zone if we're currently in it
    zone_color = (255, 100, 100)  # Red by default
    if hasattr(tracker, "last_position_category") and tracker.last_position_category == "problem_zone":
        zone_color = (100, 255, 100)  # Green when active
        cv2.rectangle(overlay, (problem_x_min, problem_y_min), (problem_x_max, problem_y_max), zone_color, -1)
        frame = cv2.addWeighted(frame, 0.9, overlay, 0.1, 0)
        overlay = frame.copy()

    cv2.rectangle(overlay, (problem_x_min, problem_y_min), (problem_x_max, problem_y_max), zone_color, 2)
    cv2.putText(overlay, "PROBLEM ZONE", (240, problem_y_min + 20), font, 0.5, zone_color, 1)
    frame = cv2.addWeighted(frame, 0.9, overlay, 0.1, 0)

    # Background for text
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (400, 280), (0, 0, 0), -1)
    frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)

    # Performance stats
    if "total_ms" in stats and stats["total_ms"] > 0:
        cv2.putText(frame, f"FPS: {1000/stats['total_ms']:.1f}", (20, y_offset), font, font_scale, (0, 255, 0), thickness)
    y_offset += 25

    if "preprocessing_ms" in stats:
        cv2.putText(
            frame, f"Preprocessing: {stats['preprocessing_ms']:.1f}ms", (20, y_offset), font, font_scale, (255, 255, 255), 1
        )
        y_offset += 25

    if "detection_ms" in stats:
        cv2.putText(frame, f"Detection: {stats['detection_ms']:.1f}ms", (20, y_offset), font, font_scale, (255, 255, 255), 1)
        y_offset += 25

    # Detection info
    mode_color = (0, 255, 0) if tracker.detection_mode != "none" else (0, 0, 255)
    if "region_" in tracker.detection_mode:
        mode_color = (255, 165, 0)  # Orange for region-adaptive
    cv2.putText(frame, f"Mode: {tracker.detection_mode}", (20, y_offset), font, font_scale, mode_color, thickness)
    y_offset += 25

    # Show position category if available
    if hasattr(tracker, "last_position_category"):
        zone_colors = {
            "problem_zone": (100, 255, 100),  # Green
            "edge": (255, 255, 0),  # Yellow
            "normal": (200, 200, 200),  # Gray
        }
        pos_color = zone_colors.get(tracker.last_position_category, (200, 200, 200))
        cv2.putText(frame, f"Zone: {tracker.last_position_category}", (20, y_offset), font, 0.5, pos_color, 1)
        y_offset += 20

    cv2.putText(frame, f"Confidence: {stats.get('confidence', 0):.2f}", (20, y_offset), font, font_scale, (255, 255, 255), 1)
    y_offset += 25

    if stats.get("kalman_active"):
        cv2.putText(
            frame,
            f"Kalman: {stats.get('kalman_tracking_confidence', 0):.2f}",
            (20, y_offset),
            font,
            font_scale,
            (255, 255, 0),
            1,
        )
        y_offset += 25

    # Instructions
    y_offset += 10
    cv2.putText(frame, "Controls:", (20, y_offset), font, 0.5, (255, 255, 255), 1)
    y_offset += 20
    cv2.putText(frame, "P: Toggle preprocessing", (20, y_offset), font, 0.4, (200, 200, 200), 1)
    y_offset += 15
    cv2.putText(frame, "A: Toggle angle detection", (20, y_offset), font, 0.4, (200, 200, 200), 1)
    y_offset += 15
    cv2.putText(frame, "K: Toggle Kalman filter", (20, y_offset), font, 0.4, (200, 200, 200), 1)
    y_offset += 15
    cv2.putText(frame, "O: Toggle original tracker", (20, y_offset), font, 0.4, (200, 200, 200), 1)

    return frame


def main():
    print("\n=== Enhanced Hand Tracker Test ===")
    print("Initializing trackers...")

    # Initialize trackers
    try:
        enhanced_tracker = EnhancedHandTracker(enable_preprocessing=True, enable_angles=True, enable_kalman=True)
        print("✓ Enhanced tracker initialized")
    except Exception as e:
        print(f"Error initializing enhanced tracker: {e}")
        return

    try:
        original_tracker = HandTracker()
        print("✓ Original tracker initialized")
    except Exception as e:
        print(f"Error initializing original tracker: {e}")
        original_tracker = None

    # Open camera
    print("Opening camera...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    print("✓ Camera opened")

    # Settings
    use_original = False
    show_landmarks = True

    print("\n=== Controls ===")
    print("Make a finger gun gesture to test detection")
    print("Flick thumb down to test shooting detection")
    print("\nKeyboard shortcuts:")
    print("  P - Toggle preprocessing")
    print("  A - Toggle angle detection")
    print("  K - Toggle Kalman filter")
    print("  O - Switch between trackers")
    print("  L - Toggle landmarks")
    print("  Q/ESC - Quit")
    print("\nStarting...\n")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error reading frame")
            break

        # Flip for mirror effect
        frame = cv2.flip(frame, 1)
        frame_height, frame_width = frame.shape[:2]

        # Choose tracker
        if use_original and original_tracker:
            # Use original tracker
            image, results = original_tracker.process_frame(frame)
            stats = {
                "preprocessing_ms": 0,
                "detection_ms": 0,
                "total_ms": 0,
                "detection_mode": original_tracker.detection_mode,
                "confidence": original_tracker.confidence_score,
            }
            current_tracker = original_tracker
        else:
            # Use enhanced tracker (with debug_mode=True to show preprocessed images)
            try:
                image, results, stats = enhanced_tracker.process_frame(frame, debug_mode=True)
            except:
                # Fallback if enhanced tracker returns only 2 values or doesn't support debug_mode
                try:
                    image, results = enhanced_tracker.process_frame(frame)
                except:
                    image, results, stats = enhanced_tracker.process_frame(frame, False)
                stats = {
                    "preprocessing_ms": getattr(enhanced_tracker, "preprocessing_time", 0),
                    "detection_ms": getattr(enhanced_tracker, "detection_time", 0),
                    "total_ms": 0,
                    "detection_mode": enhanced_tracker.detection_mode,
                    "confidence": enhanced_tracker.confidence_score,
                    "kalman_active": enhanced_tracker.enable_kalman,
                }
            current_tracker = enhanced_tracker

        # Process hand landmarks
        if results and hasattr(results, "multi_hand_landmarks") and results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks if enabled
                if show_landmarks:
                    current_tracker.draw_landmarks(image, hand_landmarks)

                # Detect finger gun
                try:
                    detection_result = current_tracker.detect_finger_gun(hand_landmarks, frame_width, frame_height)

                    # Unpack result (handle different return formats)
                    if len(detection_result) == 6:
                        is_gun, index_coords, thumb_tip, middle_pip, thumb_middle_dist, confidence = detection_result
                    else:
                        is_gun = detection_result[0]
                        index_coords = detection_result[1] if len(detection_result) > 1 else None
                        thumb_tip = detection_result[2] if len(detection_result) > 2 else None
                        middle_pip = detection_result[3] if len(detection_result) > 3 else None
                        thumb_middle_dist = detection_result[4] if len(detection_result) > 4 else None
                        confidence = detection_result[5] if len(detection_result) > 5 else 0

                    if is_gun and index_coords:
                        # Draw finger gun indicator
                        cv2.circle(image, index_coords, 15, (0, 255, 0), 3)
                        cv2.putText(
                            image,
                            "FINGER GUN",
                            (index_coords[0] - 50, index_coords[1] - 20),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0),
                            2,
                        )

                        # Check for shooting
                        if thumb_tip and thumb_middle_dist is not None:
                            if current_tracker.detect_shooting_gesture(thumb_tip, thumb_middle_dist):
                                # Flash screen for shooting
                                cv2.rectangle(image, (0, 0), (frame_width, frame_height), (0, 0, 255), 10)
                                cv2.putText(
                                    image,
                                    "BANG!",
                                    (frame_width // 2 - 50, frame_height // 2),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    2,
                                    (0, 0, 255),
                                    4,
                                )
                except Exception as e:
                    print(f"Detection error: {e}")
        else:
            # No hand detected
            current_tracker.reset_tracking_state()

        # Draw debug info
        image = draw_debug_info(image, stats, current_tracker)

        # Show tracker type
        tracker_text = "Original Tracker" if use_original else "Enhanced Tracker"
        cv2.putText(
            image,
            tracker_text,
            (frame_width - 200, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 255) if use_original else (0, 255, 255),
            2,
        )

        # Display
        cv2.imshow("Enhanced Hand Tracker Test", image)

        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:  # 27 is ESC key
            print("Quitting...")
            break
        elif key == ord("p"):
            if hasattr(enhanced_tracker, "enable_preprocessing"):
                enhanced_tracker.enable_preprocessing = not enhanced_tracker.enable_preprocessing
                print(f"Preprocessing: {'ON' if enhanced_tracker.enable_preprocessing else 'OFF'}")
        elif key == ord("a"):
            if hasattr(enhanced_tracker, "enable_angles"):
                enhanced_tracker.enable_angles = not enhanced_tracker.enable_angles
                print(f"Angle Detection: {'ON' if enhanced_tracker.enable_angles else 'OFF'}")
        elif key == ord("k"):
            if hasattr(enhanced_tracker, "enable_kalman"):
                enhanced_tracker.enable_kalman = not enhanced_tracker.enable_kalman
                print(f"Kalman Filter: {'ON' if enhanced_tracker.enable_kalman else 'OFF'}")
        elif key == ord("o"):
            if original_tracker:
                use_original = not use_original
                print(f"Using: {'Original' if use_original else 'Enhanced'} Tracker")
        elif key == ord("l"):
            show_landmarks = not show_landmarks
            print(f"Landmarks: {'ON' if show_landmarks else 'OFF'}")

    cap.release()
    cv2.destroyAllWindows()
    print("Done!")


if __name__ == "__main__":
    main()
