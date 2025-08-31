"""
Blinky Bird game screen for the ARCVDE game collection.
Integrates blink detection with Flappy Bird-style gameplay.
"""

# Standard library imports
import time
from typing import Optional

# Third-party imports
import cv2
import numpy as np
import pygame

# Local application imports
from game.blinky_bird import BlinkyBirdGame, GameState
from game.cv.blink_detection import BlinkDetector
from screens.base_screen import BaseScreen
from utils.camera_manager import CameraManager
from utils.constants import (
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    CAMERA_X,
    CAMERA_Y,
    GAME_STATE_MENU,
    GREEN,
    LIGHT_GRAY,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    UI_ACCENT,
    UI_TEXT,
    VAPORWAVE_CYAN,
    VAPORWAVE_MINT,
    VAPORWAVE_PINK,
    WHITE,
)


class BlinkyBirdScreen(BaseScreen):
    """
    Screen for playing Blinky Bird - a blink-controlled Flappy Bird clone.

    Features:
    - Integration with camera-based blink detection
    - Automatic calibration for glasses support
    - Real-time gameplay with physics and obstacles
    - Score tracking and high score persistence
    - Seamless integration with ARCVDE UI system
    """

    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        super().__init__(screen, camera_manager)

        # Initialize fonts
        self.title_font = pygame.font.Font(None, 72)
        self.large_font = pygame.font.Font(None, 48)
        self.medium_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Initialize game and blink detector
        self.game = BlinkyBirdGame(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.blink_detector = BlinkDetector(calibration_time=2.0, sensitivity=1.0)

        # UI state
        self.show_debug_info = False
        self.calibration_start_time = None
        self.last_blink_feedback_time = 0
        self.blink_feedback_duration = 0.5
        self.last_blink_type = "None"
        self.paused = False

        # Camera preview settings
        self.preview_width = CAMERA_WIDTH
        self.preview_height = CAMERA_HEIGHT
        self.preview_x = CAMERA_X
        self.preview_y = CAMERA_Y

        # Performance tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle pygame events."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return GAME_STATE_MENU
            elif event.key == pygame.K_p:
                # Toggle pause
                self.paused = not self.paused
            elif event.key == pygame.K_d:
                self.show_debug_info = not self.show_debug_info
            elif event.key == pygame.K_r:
                # Reset game for testing
                self.game.reset_game()
                self.paused = False  # Unpause when resetting
            elif event.key == pygame.K_c:
                # Recalibrate blink detector
                self.blink_detector.recalibrate()
            elif event.key == pygame.K_SPACE:
                if self.paused:
                    # Unpause with spacebar
                    self.paused = False
                else:
                    # Manual flap for testing
                    if self.game.state == GameState.PLAYING:
                        self.game.bird.flap()
                    elif self.game.state == GameState.READY:
                        self.game.start_game()
                    elif self.game.state == GameState.GAME_OVER:
                        self.game.reset_game()

        return None

    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update game logic and blink detection."""
        # Handle calibration state first
        detector_status = self.blink_detector.get_status()

        # Set game state based on calibration status
        if not detector_status["calibrated"]:
            # Still calibrating - force game into calibrating state
            if self.game.state != GameState.CALIBRATING:
                self.game.state = GameState.CALIBRATING

            if self.calibration_start_time is None:
                self.calibration_start_time = time.time()
        else:
            # Calibration complete
            if self.calibration_start_time is not None:
                self.calibration_start_time = None
                # Move to ready state if we were calibrating
                if self.game.state == GameState.CALIBRATING:
                    self.game.state = GameState.READY
                    self.game.ready_time = time.time()

        # Process camera frame for blink detection
        if hasattr(self, "current_frame") and self.current_frame is not None:
            blink_detected, blink_type = self.blink_detector.process_frame(self.current_frame)

            # Get fresh detector status after processing (calibration might have just completed!)
            fresh_detector_status = self.blink_detector.get_status()

            # Only handle actual blinks if calibrated and not paused
            if fresh_detector_status["calibrated"] and blink_detected and blink_type == "Blink" and not self.paused:
                self.last_blink_feedback_time = time.time()
                self.last_blink_type = blink_type

                # Handle blinks in game
                self.game.handle_blink(blink_type)

        # Update game state (skip if paused)
        if not self.paused:
            self.game.update(dt)

        # Update FPS counter
        self.fps_counter += 1
        current_time_sec = time.time()
        if current_time_sec - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter / (current_time_sec - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = current_time_sec

        return None

    def draw(self) -> None:
        """Draw the complete Blinky Bird screen."""
        # Get camera frame for processing and display
        ret, frame = self.camera_manager.read_frame()
        self.current_frame = frame if ret else None

        # Clear screen with game background
        self.screen.fill((135, 206, 235))  # Sky blue background

        # Draw game world
        self.game.draw(self.screen)

        # Draw UI overlays based on game state
        game_info = self.game.get_game_info()
        detector_status = self.blink_detector.get_status()

        if self.game.state == GameState.WAITING_FOR_CALIBRATION:
            self._draw_waiting_screen()
        elif self.game.state == GameState.CALIBRATING or not detector_status["calibrated"]:
            self._draw_calibration_screen(detector_status)
        elif self.game.state == GameState.READY:
            self._draw_ready_screen(game_info)
        elif self.game.state == GameState.PLAYING:
            self._draw_playing_ui(game_info)
        elif self.game.state == GameState.GAME_OVER:
            self._draw_game_over_screen(game_info)

        # Draw camera preview
        self._draw_camera_preview()

        # Draw blink feedback
        self._draw_blink_feedback()

        # Draw debug info if enabled
        if self.show_debug_info:
            self._draw_debug_info(game_info, detector_status)

        # Draw pause screen overlay if paused
        if self.paused and self.game.state == GameState.PLAYING:
            self._draw_pause_screen()

        # Draw controls at bottom (always visible except during pause)
        if not self.paused:
            self._draw_controls()

    def _draw_waiting_screen(self):
        """Draw initial waiting screen."""
        title = self.title_font.render("BLINKY BIRD", True, VAPORWAVE_CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(title, title_rect)

        subtitle = self.large_font.render("Blink-Controlled Flappy Bird", True, UI_TEXT)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(subtitle, subtitle_rect)

        instruction = self.medium_font.render("Position yourself in front of the camera", True, WHITE)
        instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(instruction, instruction_rect)

        instruction2 = self.medium_font.render("Look directly at the camera to begin calibration", True, WHITE)
        instruction2_rect = instruction2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(instruction2, instruction2_rect)

    def _draw_calibration_screen(self, detector_status: dict):
        """Draw calibration progress screen."""
        title = self.large_font.render("CALIBRATING BLINK DETECTION", True, VAPORWAVE_PINK)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        self.screen.blit(title, title_rect)

        progress = detector_status.get("calibration_progress", 0)
        progress_text = self.medium_font.render(f"Progress: {progress:.0%}", True, UI_TEXT)
        progress_rect = progress_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(progress_text, progress_rect)

        # Progress bar
        bar_width = 300
        bar_height = 20
        bar_x = SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = SCREEN_HEIGHT // 2 + 10

        # Background bar
        pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))

        # Progress bar
        if progress > 0:
            progress_width = int(bar_width * progress)
            pygame.draw.rect(self.screen, VAPORWAVE_CYAN, (bar_x, bar_y, progress_width, bar_height))

        # Bar outline
        pygame.draw.rect(self.screen, UI_TEXT, (bar_x, bar_y, bar_width, bar_height), 2)

        instruction = self.medium_font.render("Keep both eyes open and look at the camera", True, WHITE)
        instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(instruction, instruction_rect)

        if detector_status.get("glasses_mode", False):
            glasses_text = self.small_font.render("Glasses detected - adaptive thresholds enabled", True, VAPORWAVE_MINT)
            glasses_rect = glasses_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 90))
            self.screen.blit(glasses_text, glasses_rect)

    def _draw_ready_screen(self, game_info: dict):
        """Draw ready to play screen."""
        title = self.large_font.render("READY TO PLAY!", True, VAPORWAVE_CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        instruction = self.medium_font.render("Blink to start flying!", True, UI_TEXT)
        instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(instruction, instruction_rect)

        # Show high score if available
        if self.game.high_score > 0:
            high_score_text = self.medium_font.render(f"High Score: {self.game.high_score}", True, UI_ACCENT)
            high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
            self.screen.blit(high_score_text, high_score_rect)

        # Controls help
        controls = [
            "Controls:",
            "• Blink = Flap wings",
            "• ESC = Return to menu",
            "• D = Toggle debug info",
            "• C = Recalibrate blink detection",
        ]

        start_y = SCREEN_HEIGHT - 200
        for i, control_text in enumerate(controls):
            color = UI_ACCENT if i == 0 else WHITE
            font = self.small_font if i > 0 else self.medium_font
            text = font.render(control_text, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 25))
            self.screen.blit(text, text_rect)

    def _draw_playing_ui(self, game_info: dict):
        """Draw UI during active gameplay."""
        # Score display
        score_text = self.large_font.render(f"Score: {self.game.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(score_text, score_rect)

        # High score (smaller)
        if self.game.high_score > self.game.score:
            high_score_text = self.medium_font.render(f"Best: {self.game.high_score}", True, UI_ACCENT)
            high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH // 2, 90))
            self.screen.blit(high_score_text, high_score_rect)

    def _draw_game_over_screen(self, game_info: dict):
        """Draw game over screen with score and restart option."""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Game Over text
        game_over_text = self.title_font.render("GAME OVER", True, VAPORWAVE_PINK)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(game_over_text, game_over_rect)

        # Final score
        score_text = self.large_font.render(f"Final Score: {self.game.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(score_text, score_rect)

        # High score
        if self.game.score >= self.game.high_score:
            high_score_text = self.medium_font.render("NEW HIGH SCORE!", True, GREEN)
        else:
            high_score_text = self.medium_font.render(f"Best: {self.game.high_score}", True, UI_ACCENT)

        high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(high_score_text, high_score_rect)

        # Restart instruction
        restart_text = self.medium_font.render("Blink to play again", True, VAPORWAVE_CYAN)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(restart_text, restart_rect)

        # Return to menu
        menu_text = self.small_font.render("ESC - Return to Menu", True, WHITE)
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        self.screen.blit(menu_text, menu_rect)

    def _draw_camera_preview(self):
        """Draw camera preview with blink detection visualization."""
        if hasattr(self, "current_frame") and self.current_frame is not None:
            # Create a copy of the frame for drawing overlays
            frame_with_overlay = self.current_frame.copy()

            # Add eye detection overlay
            self._draw_eye_overlay_on_frame(frame_with_overlay)

            # Convert frame to pygame surface using camera_manager method
            frame_surface = self.camera_manager.frame_to_pygame_surface(
                frame_with_overlay, (self.preview_width, self.preview_height)
            )

            # Draw preview border
            pygame.draw.rect(
                self.screen,
                (50, 50, 50),
                (self.preview_x - 2, self.preview_y - 2, self.preview_width + 4, self.preview_height + 4),
            )

            # Draw preview
            self.screen.blit(frame_surface, (self.preview_x, self.preview_y))

            # No label above camera preview for cleaner look

    def _draw_eye_overlay_on_frame(self, frame: np.ndarray):
        """Draw eye detection overlay on the camera frame."""
        # Convert frame to RGB for MediaPipe processing
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False

        # Process with MediaPipe Face Mesh
        results = self.blink_detector.face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            h, w = frame.shape[:2]

            # Draw eye landmarks and bounding boxes
            self._draw_eye_landmarks(frame, face_landmarks, w, h)

            # Add eye state text
            self._draw_eye_state_text(frame, face_landmarks, w, h)

    def _draw_eye_landmarks(self, frame: np.ndarray, face_landmarks, w: int, h: int):
        """Draw eye landmark points and bounding boxes on frame."""
        # Get eye states for coloring
        detector_status = self.blink_detector.get_status()

        # Define colors
        open_color = (0, 255, 0)  # Green for open eyes
        closed_color = (0, 0, 255)  # Red for closed eyes

        # Draw left eye landmarks
        left_eye_indices = self.blink_detector.LEFT_EYE_KEY
        left_closed = False

        if detector_status["calibrated"]:
            # Calculate current EAR to determine if eye is closed
            left_eye_points = []
            for idx in left_eye_indices:
                landmark = face_landmarks.landmark[idx]
                left_eye_points.append((landmark.x, landmark.y))

            left_ear = self.blink_detector.calculate_ear(left_eye_points)
            left_closed = left_ear < detector_status.get("adaptive_threshold_left", 0.25)

        # Draw left eye landmarks
        left_color = closed_color if left_closed else open_color
        for idx in left_eye_indices:
            landmark = face_landmarks.landmark[idx]
            x, y = int(landmark.x * w), int(landmark.y * h)
            cv2.circle(frame, (x, y), 2, left_color, -1)

        # Draw left eye bounding box
        if left_eye_indices:
            left_points = [
                (int(face_landmarks.landmark[idx].x * w), int(face_landmarks.landmark[idx].y * h)) for idx in left_eye_indices
            ]
            left_rect = cv2.boundingRect(np.array(left_points))
            cv2.rectangle(frame, left_rect, left_color, 2)

        # Draw right eye landmarks
        right_eye_indices = self.blink_detector.RIGHT_EYE_KEY
        right_closed = False

        if detector_status["calibrated"]:
            right_eye_points = []
            for idx in right_eye_indices:
                landmark = face_landmarks.landmark[idx]
                right_eye_points.append((landmark.x, landmark.y))

            right_ear = self.blink_detector.calculate_ear(right_eye_points)
            right_closed = right_ear < detector_status.get("adaptive_threshold_right", 0.25)

        # Draw right eye landmarks
        right_color = closed_color if right_closed else open_color
        for idx in right_eye_indices:
            landmark = face_landmarks.landmark[idx]
            x, y = int(landmark.x * w), int(landmark.y * h)
            cv2.circle(frame, (x, y), 2, right_color, -1)

        # Draw right eye bounding box
        if right_eye_indices:
            right_points = [
                (int(face_landmarks.landmark[idx].x * w), int(face_landmarks.landmark[idx].y * h)) for idx in right_eye_indices
            ]
            right_rect = cv2.boundingRect(np.array(right_points))
            cv2.rectangle(frame, right_rect, right_color, 2)

    def _draw_eye_state_text(self, frame: np.ndarray, face_landmarks, w: int, h: int):
        """Draw eye state text on the frame."""
        detector_status = self.blink_detector.get_status()

        if detector_status["calibrated"]:
            # Draw L and R labels for eyes
            left_center = np.mean(
                [
                    (face_landmarks.landmark[idx].x * w, face_landmarks.landmark[idx].y * h)
                    for idx in self.blink_detector.LEFT_EYE_KEY
                ],
                axis=0,
            )
            right_center = np.mean(
                [
                    (face_landmarks.landmark[idx].x * w, face_landmarks.landmark[idx].y * h)
                    for idx in self.blink_detector.RIGHT_EYE_KEY
                ],
                axis=0,
            )

            # Draw labels
            cv2.putText(
                frame,
                "L",
                (int(left_center[0]) - 10, int(left_center[1]) - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                "R",
                (int(right_center[0]) - 10, int(right_center[1]) - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            # Draw glasses indicator if detected
            if detector_status.get("glasses_mode", False):
                cv2.putText(frame, "GLASSES", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        else:
            # Show calibration status
            progress = detector_status.get("calibration_progress", 0)
            cv2.putText(frame, f"CALIBRATING {progress:.0%}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

    def _draw_blink_feedback(self):
        """Draw visual feedback when blinks are detected."""
        current_time = time.time()
        if current_time - self.last_blink_feedback_time < self.blink_feedback_duration:
            # Flash effect
            alpha = int(255 * (1 - (current_time - self.last_blink_feedback_time) / self.blink_feedback_duration))

            # Green color for successful blinks
            color = GREEN

            # Create flash surface
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surface.set_alpha(alpha // 4)  # Subtle flash
            flash_surface.fill(color)
            self.screen.blit(flash_surface, (0, 0))

            # Blink indicator text
            blink_text = self.large_font.render("BLINK!", True, color)
            blink_rect = blink_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
            self.screen.blit(blink_text, blink_rect)

    def _draw_debug_info(self, game_info: dict, detector_status: dict):
        """Draw debug information overlay."""
        debug_y = 250
        debug_texts = [
            f"FPS: {self.current_fps:.1f}",
            f"Game State: {game_info['state'].value}",
            f"Bird Y: {game_info.get('bird_y', 0):.1f}",
            f"Bird Velocity: {game_info.get('bird_velocity', 0):.1f}",
            f"Blink Count: {detector_status.get('blink_count', 0)}",
            f"Calibrated: {detector_status.get('calibrated', False)}",
            f"Glasses Mode: {detector_status.get('glasses_mode', False)}",
        ]

        # Next pipe info
        if "next_pipe" in game_info:
            pipe_info = game_info["next_pipe"]
            debug_texts.extend(
                [
                    f"Next Pipe X: {pipe_info['x']:.1f}",
                    f"Gap Center: {pipe_info['gap_center']:.1f}",
                ]
            )

        # Difficulty info
        difficulty = self.game.get_difficulty_info()
        debug_texts.extend(
            [
                f"Difficulty Level: {difficulty['difficulty_level']}",
                f"Gap Size: {difficulty['gap_size']}",
                f"Pipe Speed: {difficulty['pipe_speed']:.1f}",
            ]
        )

        # Draw debug background
        debug_bg = pygame.Surface((250, len(debug_texts) * 20 + 10))
        debug_bg.set_alpha(180)
        debug_bg.fill((0, 0, 0))
        self.screen.blit(debug_bg, (10, debug_y - 5))

        # Draw debug texts
        for i, text in enumerate(debug_texts):
            debug_surface = self.small_font.render(text, True, WHITE)
            self.screen.blit(debug_surface, (15, debug_y + i * 20))

    def _draw_controls(self):
        """Draw controls at the bottom of the screen like capybara hunt."""
        controls_text = self.small_font.render("ESC: Menu | P: Pause | R: Restart | C: Recalibrate", True, LIGHT_GRAY)
        controls_rect = controls_text.get_rect()
        controls_rect.centerx = SCREEN_WIDTH // 2
        controls_rect.y = SCREEN_HEIGHT - 30
        self.screen.blit(controls_text, controls_rect)

    def _draw_pause_screen(self):
        """Draw pause screen overlay."""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Pause title
        pause_text = self.title_font.render("PAUSED", True, VAPORWAVE_CYAN)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(pause_text, pause_rect)

        # Controls
        controls = ["P/SPACE - Resume", "R - Restart", "ESC - Return to Menu", "C - Recalibrate Blink Detection"]

        y_start = SCREEN_HEIGHT // 2 - 50
        for i, control in enumerate(controls):
            control_text = self.medium_font.render(control, True, UI_ACCENT)
            control_rect = control_text.get_rect(center=(SCREEN_WIDTH // 2, y_start + i * 40))
            self.screen.blit(control_text, control_rect)

    def reset_game(self):
        """Reset the game to initial state."""
        self.game.reset_game()
        self.blink_detector.reset_counters()
        self.blink_detector.reset_tracking()  # Clear any stuck tracking state!
        self.calibration_start_time = None
        self.paused = False
