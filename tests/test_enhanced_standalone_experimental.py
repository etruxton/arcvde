#!/usr/bin/env python3
"""
EXPERIMENTAL VERSION - Standalone test script with extensive debug overlays
This version had complex import handling and detailed shooting detection debugging
"""

# Standard library imports
import os
import sys
import random

# Add src directories to path (go up one level from tests/ to project root)
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(project_root, "src"))
sys.path.insert(0, os.path.join(project_root, "src", "game"))
sys.path.insert(0, os.path.join(project_root, "src", "utils"))

# Third-party imports
import cv2
import numpy as np

# Import the trackers directly - EXPERIMENTAL COMPLEX VERSION
try:
    # Try new location first
    from game.cv.finger_gun_detection import EnhancedHandTracker
    from game.cv.finger_gun_detection.enhanced_hand_tracker import FramePreprocessor
    from game.cv.finger_gun_detection.kalman_tracker import HandKalmanTracker
except ImportError:
    # Fallback to old location
    from enhanced_hand_tracker import EnhancedHandTracker, FramePreprocessor
    from kalman_tracker import HandKalmanTracker

from hand_tracker import HandTracker


def draw_debug_info(frame, stats, tracker):
    """Draw debug information on frame - EXPERIMENTAL COMPLEX VERSION"""
    y_offset = 30
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 2

    # Draw problem zone rectangle (full width at bottom)
    problem_x_min = 0
    problem_x_max = 640
    problem_y_min = 480 - 160
    problem_y_max = 480

    overlay = frame.copy()
    zone_color = (255, 100, 100)
    if hasattr(tracker, "last_position_category") and tracker.last_position_category == "problem_zone":
        zone_color = (100, 255, 100)
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

    # Error display
    if "error" in stats:
        cv2.putText(frame, f"ERROR: {stats['error'][:30]}...", (20, y_offset), font, font_scale, (0, 0, 255), thickness)
        y_offset += 25
        return frame  # Skip other displays if there's an error
    
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
        kalman_conf = stats.get('kalman_tracking_confidence', 0)
        kalman_color = (0, 255, 0) if kalman_conf > 0.8 else (255, 255, 0) if kalman_conf > 0.5 else (255, 0, 0)
        cv2.putText(
            frame,
            f"Kalman: {kalman_conf:.2f}",
            (20, y_offset),
            font,
            font_scale,
            kalman_color,
            1,
        )
        y_offset += 25
    
    # Show if region adaptive detection is working - EXPERIMENTAL FEATURE
    if hasattr(tracker, "region_detector") and hasattr(tracker, "last_position_hints"):
        if tracker.last_position_category == "problem_zone" and hasattr(tracker, "last_position_hints"):
            hints = tracker.last_position_hints
            hint_text = ""
            if hints.get("hand_pointing_up"): hint_text += "UP "
            if hints.get("fingers_compressed"): hint_text += "COMP "  
            if hints.get("hand_small"): hint_text += "SMALL "
            if hint_text:
                cv2.putText(frame, f"Hints: {hint_text}", (20, y_offset), font, 0.4, (100, 255, 100), 1)
                y_offset += 20

    # Show active features if using enhanced tracker - EXPERIMENTAL FEATURE
    if hasattr(tracker, "enable_preprocessing"):
        y_offset += 10
        cv2.putText(frame, "Features:", (20, y_offset), font, 0.5, (255, 255, 255), 1)
        y_offset += 18
        
        # Preprocessing
        prep_color = (0, 255, 0) if tracker.enable_preprocessing else (100, 100, 100)
        cv2.putText(frame, f"Preprocessing: {'ON' if tracker.enable_preprocessing else 'OFF'}", 
                   (20, y_offset), font, 0.4, prep_color, 1)
        y_offset += 15
        
        # Angles
        angle_color = (0, 255, 0) if tracker.enable_angles else (100, 100, 100)
        cv2.putText(frame, f"Angles: {'ON' if tracker.enable_angles else 'OFF'}", 
                   (20, y_offset), font, 0.4, angle_color, 1)
        y_offset += 15
        
        # Kalman
        kalman_color = (0, 255, 0) if tracker.enable_kalman else (100, 100, 100)
        cv2.putText(frame, f"Kalman: {'ON' if tracker.enable_kalman else 'OFF'}", 
                   (20, y_offset), font, 0.4, kalman_color, 1)
        y_offset += 20

    # Instructions
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
    print("\n=== Enhanced Hand Tracker Test - EXPERIMENTAL VERSION ===")
    print("This version has complex debug overlays and experimental features")
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

    print("\n=== EXPERIMENTAL VERSION Controls ===")
    print("This version includes experimental shooting debug overlays")
    print("Make a finger gun gesture to test detection")
    print("Flick thumb down to test shooting detection")
    print("\nKeyboard shortcuts:")
    print("  P - Toggle preprocessing")
    print("  A - Toggle angle detection") 
    print("  K - Toggle Kalman filter")
    print("  O - Switch between trackers")
    print("  L - Toggle landmarks")
    print("  Q/ESC - Quit")
    print("\nStarting experimental version...\n")

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
            # Use enhanced tracker - EXPERIMENTAL COMPLEX ERROR HANDLING
            try:
                result = enhanced_tracker.process_frame(frame, debug_mode=True)
                if len(result) == 3:
                    image, results, stats = result
                else:
                    # Fallback for 2-tuple return
                    image, results = result
                    stats = {
                        "preprocessing_ms": getattr(enhanced_tracker, "preprocessing_time", 0),
                        "detection_ms": getattr(enhanced_tracker, "detection_time", 0),
                        "total_ms": 0,
                        "detection_mode": getattr(enhanced_tracker, "detection_mode", "unknown"),
                        "confidence": getattr(enhanced_tracker, "confidence_score", 0),
                        "kalman_active": getattr(enhanced_tracker, "enable_kalman", False),
                        "kalman_tracking_confidence": getattr(enhanced_tracker, "kalman_tracker", None) and 
                                                    getattr(enhanced_tracker.kalman_tracker, "tracking_confidence", 0) or 0,
                    }
            except Exception as e:
                print(f"Enhanced tracker error: {e}")
                # Fallback if enhanced tracker fails
                try:
                    image, results = enhanced_tracker.process_frame(frame)
                    stats = {
                        "preprocessing_ms": getattr(enhanced_tracker, "preprocessing_time", 0),
                        "detection_ms": getattr(enhanced_tracker, "detection_time", 0),
                        "total_ms": 0,
                        "detection_mode": getattr(enhanced_tracker, "detection_mode", "unknown"),
                        "confidence": getattr(enhanced_tracker, "confidence_score", 0),
                        "kalman_active": getattr(enhanced_tracker, "enable_kalman", False),
                    }
                except Exception as e2:
                    print(f"Fallback tracker error: {e2}")
                    image = frame
                    results = None
                    stats = {"error": str(e2)}
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

                        # Check for shooting - EXPERIMENTAL COMPLEX VERSION
                        if thumb_tip and thumb_middle_dist is not None:
                            shoot_detected = current_tracker.detect_shooting_gesture(thumb_tip, thumb_middle_dist)
                            if shoot_detected:
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
                            
                            # EXPERIMENTAL SHOOTING DEBUG INFO - This was the complex version
                            if hasattr(current_tracker, 'previous_thumb_y') and current_tracker.previous_thumb_y is not None:
                                thumb_vel = (thumb_tip.y - current_tracker.previous_thumb_y) if current_tracker.previous_time > 0 else 0
                                
                                # Calculate raw distance for comparison - EXPERIMENTAL
                                raw_dist = thumb_middle_dist  # Default
                                if (current_tracker.enable_kalman and 
                                    hasattr(current_tracker, 'last_raw_landmarks') and 
                                    current_tracker.last_raw_landmarks):
                                    try:
                                        raw_thumb = current_tracker.last_raw_landmarks.landmark[4]  # THUMB_TIP
                                        raw_middle = current_tracker.last_raw_landmarks.landmark[10]  # MIDDLE_PIP
                                        raw_dist = current_tracker.calculate_distance(
                                            (raw_thumb.x, raw_thumb.y), 
                                            (raw_middle.x, raw_middle.y)
                                        )
                                    except:
                                        raw_dist = thumb_middle_dist
                                
                                # EXPERIMENTAL DEBUG OVERLAYS - These were cluttering the display
                                cv2.putText(
                                    image,
                                    f"Thumb Vel: {thumb_vel:.3f}",
                                    (frame_width - 220, frame_height - 100),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.4,
                                    (255, 255, 0),
                                    1,
                                )
                                cv2.putText(
                                    image,
                                    f"Smooth Dist: {thumb_middle_dist:.3f}",
                                    (frame_width - 220, frame_height - 80),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.4,
                                    (255, 255, 0),
                                    1,
                                )
                                cv2.putText(
                                    image,
                                    f"Raw Dist: {raw_dist:.3f}",
                                    (frame_width - 220, frame_height - 60),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.4,
                                    (0, 255, 255),  # Cyan for raw
                                    1,
                                )
                                reset_status = "READY" if current_tracker.thumb_reset else "WAIT"
                                cv2.putText(
                                    image,
                                    f"Status: {reset_status}",
                                    (frame_width - 220, frame_height - 40),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.4,
                                    (0, 255, 0) if current_tracker.thumb_reset else (255, 0, 0),
                                    1,
                                )
                except Exception as e:
                    print(f"Detection error: {e}")
        else:
            # No hand detected
            current_tracker.reset_tracking_state()

        # Draw debug info
        image = draw_debug_info(image, stats, current_tracker)

        # Show tracker type
        tracker_text = "Original Tracker" if use_original else "Enhanced Tracker (EXPERIMENTAL)"
        cv2.putText(
            image,
            tracker_text,
            (frame_width - 300, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 255) if use_original else (0, 255, 255),
            2,
        )

        # Display
        cv2.imshow("Enhanced Hand Tracker Test - EXPERIMENTAL", image)

        # Handle key presses - EXPERIMENTAL COMPLEX VERSION
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:  # 27 is ESC key
            print("Quitting...")
            break
        elif key == ord("p"):
            if hasattr(enhanced_tracker, "enable_preprocessing"):
                enhanced_tracker.enable_preprocessing = not enhanced_tracker.enable_preprocessing
                # Reinitialize preprocessor - EXPERIMENTAL COMPLEX LOGIC
                if enhanced_tracker.enable_preprocessing and not enhanced_tracker.preprocessor:
                    try:
                        from game.cv.finger_gun_detection.enhanced_hand_tracker import FramePreprocessor
                    except ImportError:
                        from enhanced_hand_tracker import FramePreprocessor
                    enhanced_tracker.preprocessor = FramePreprocessor()
                print(f"Preprocessing: {'ON' if enhanced_tracker.enable_preprocessing else 'OFF'}")
        elif key == ord("a"):
            if hasattr(enhanced_tracker, "enable_angles"):
                enhanced_tracker.enable_angles = not enhanced_tracker.enable_angles
                print(f"Angle Detection: {'ON' if enhanced_tracker.enable_angles else 'OFF'}")
        elif key == ord("k"):
            if hasattr(enhanced_tracker, "enable_kalman"):
                enhanced_tracker.enable_kalman = not enhanced_tracker.enable_kalman
                # Reinitialize Kalman tracker - EXPERIMENTAL COMPLEX LOGIC
                if enhanced_tracker.enable_kalman and not enhanced_tracker.kalman_tracker:
                    try:
                        from game.cv.finger_gun_detection.kalman_tracker import HandKalmanTracker
                    except ImportError:
                        from kalman_tracker import HandKalmanTracker
                    enhanced_tracker.kalman_tracker = HandKalmanTracker()
                elif not enhanced_tracker.enable_kalman and enhanced_tracker.kalman_tracker:
                    enhanced_tracker.kalman_tracker.reset()
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
    print("Done with experimental version!")


if __name__ == "__main__":
    main()