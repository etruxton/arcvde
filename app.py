import cv2
import mediapipe as mp
import math
import numpy as np
import time
import pygame
import random

# Initialize Pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
CAMERA_X = SCREEN_WIDTH - CAMERA_WIDTH - 20
CAMERA_Y = 20

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# Target settings
TARGET_SIZE = 50
TARGET_SPAWN_TIME = 2000  # milliseconds
MAX_TARGETS = 5

# Global variables for slider values (from original code)
thumb_index_threshold = 35
middle_ring_threshold = 8
ring_pinky_threshold = 8
index_wrist_threshold = 10
shoot_velocity_threshold = 0.1
shoot_distance_threshold = 0.1

# Global variables for shooting detection and cooldown
shooting_detected = False
last_shoot_time = 0
cooldown_duration = 0.5
previous_thumb_y = None
previous_time = 0

# Enhanced tracking variables
detection_mode = "standard"  # Can be "standard", "wrist_angle", or "depth"
confidence_score = 0

# Game variables
score = 0
targets = []
last_target_spawn = 0
shoot_pos = None
shoot_animation_time = 0

class Target:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = TARGET_SIZE // 2
        self.hit = False
        self.hit_time = 0
        
    def draw(self, screen):
        if not self.hit:
            # Draw target circles
            pygame.draw.circle(screen, RED, (self.x, self.y), self.radius)
            pygame.draw.circle(screen, WHITE, (self.x, self.y), self.radius - 10)
            pygame.draw.circle(screen, RED, (self.x, self.y), self.radius - 20)
            pygame.draw.circle(screen, WHITE, (self.x, self.y), 5)
        else:
            # Draw hit animation
            if time.time() - self.hit_time < 0.3:
                pygame.draw.circle(screen, YELLOW, (self.x, self.y), self.radius + 10, 3)
                pygame.draw.circle(screen, YELLOW, (self.x, self.y), self.radius + 20, 2)
    
    def check_hit(self, x, y):
        distance = math.sqrt((self.x - x)**2 + (self.y - y)**2)
        if distance <= self.radius:
            self.hit = True
            self.hit_time = time.time()
            return True
        return False

def calculate_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def calculate_3d_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2 + (point1[2] - point2[2])**2)

def get_wrist_angle(hand_landmarks):
    """Calculate the angle of the hand based on wrist and middle finger MCP"""
    wrist = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.WRIST]
    middle_mcp = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.MIDDLE_FINGER_MCP]
    
    # Calculate angle from horizontal
    dx = middle_mcp.x - wrist.x
    dy = middle_mcp.y - wrist.y
    angle = math.atan2(dy, dx) * 180 / math.pi
    
    return angle

def get_palm_normal(hand_landmarks):
    """Calculate palm normal vector using wrist, index MCP, and pinky MCP"""
    wrist = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.WRIST]
    index_mcp = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_MCP]
    pinky_mcp = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.PINKY_MCP]
    
    # Create vectors
    v1 = np.array([index_mcp.x - wrist.x, index_mcp.y - wrist.y, index_mcp.z - wrist.z])
    v2 = np.array([pinky_mcp.x - wrist.x, pinky_mcp.y - wrist.y, pinky_mcp.z - wrist.z])
    
    # Cross product gives normal
    normal = np.cross(v1, v2)
    normal = normal / np.linalg.norm(normal)  # Normalize
    
    return normal

def is_pointing_at_camera(hand_landmarks):
    """Check if hand is pointing toward camera using Z-coordinates"""
    index_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP]
    wrist = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.WRIST]
    
    # If index tip Z is less than wrist Z, finger is pointing at camera
    z_diff = wrist.z - index_tip.z
    return z_diff > 0.05  # Much more sensitive threshold

def enhanced_finger_gun_detection(hand_landmarks, frame_width, frame_height):
    """Enhanced detection with multiple methods"""
    global detection_mode, confidence_score
    
    if hand_landmarks is None:
        return False, None, None, None, None, 0
    
    # Get all necessary landmarks
    thumb_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.RING_FINGER_TIP]
    pinky_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.PINKY_TIP]
    wrist = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.WRIST]
    middle_pip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.MIDDLE_FINGER_PIP]
    ring_pip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.RING_FINGER_PIP]
    pinky_pip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.PINKY_PIP]
    index_mcp = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_MCP]
    
    # Method 1: Standard detection (original method)
    thumb_index_dist = calculate_distance((thumb_tip.x, thumb_tip.y), (index_tip.x, index_tip.y))
    middle_ring_dist = calculate_distance((middle_tip.x, middle_tip.y), (ring_tip.x, ring_tip.y))
    ring_pinky_dist = calculate_distance((ring_tip.x, ring_tip.y), (pinky_tip.x, pinky_tip.y))
    index_wrist_dist = calculate_distance((index_tip.x, index_tip.y), (wrist.x, wrist.y))
    thumb_middle_dist = calculate_distance((thumb_tip.x, thumb_tip.y), (middle_pip.x, middle_pip.y))
    
    scaled_thumb_index = thumb_index_threshold / 100.0
    scaled_middle_ring = middle_ring_threshold / 100.0
    scaled_ring_pinky = ring_pinky_threshold / 100.0
    scaled_index_wrist = index_wrist_threshold / 100.0
    
    standard_checks = {
        'thumb_near_index': thumb_index_dist < scaled_thumb_index,
        'middle_ring_close': middle_ring_dist < scaled_middle_ring,
        'ring_pinky_close': ring_pinky_dist < scaled_ring_pinky,
        'index_extended': index_wrist_dist > scaled_index_wrist
    }
    
    standard_score = sum(standard_checks.values()) / len(standard_checks)
    
    # Method 2: Wrist angle detection
    wrist_angle = get_wrist_angle(hand_landmarks)
    pointing_forward = is_pointing_at_camera(hand_landmarks)
    
    # Method 3: Enhanced finger curl detection using 3D coordinates
    # Check if middle, ring, and pinky are curled (closer to palm in Z)
    middle_curl = middle_tip.z > middle_pip.z  # Curled if tip is behind PIP
    ring_curl = ring_tip.z > ring_pip.z
    pinky_curl = pinky_tip.z > pinky_pip.z
    
    # Method 4: Index finger extension check using MCP-TIP angle
    index_vector = np.array([index_tip.x - index_mcp.x, index_tip.y - index_mcp.y])
    index_length = np.linalg.norm(index_vector)
    index_extended_alt = index_length > 0.15  # Alternative extension check
    
    # Combine detection methods with cascading logic
    if standard_score >= 0.75:  # Standard method works well
        detection_mode = "standard"
        confidence_score = standard_score
        is_gun = all(standard_checks.values())
    elif standard_score >= 0.5:  # Partial standard detection, try to help with depth
        if pointing_forward and index_extended_alt:
            detection_mode = "depth"
            confidence_score = 0.7
            is_gun = True
        elif abs(wrist_angle) < 60 and index_extended_alt:
            detection_mode = "wrist_angle"
            confidence_score = 0.6
            is_gun = middle_ring_dist < scaled_middle_ring * 2.0
        else:
            detection_mode = "none"
            confidence_score = standard_score
            is_gun = False
    elif pointing_forward and index_extended_alt and (middle_curl or ring_curl or pinky_curl):
        # Hand detected, try depth mode even without partial standard detection
        detection_mode = "depth"
        confidence_score = 0.6
        is_gun = True
    elif index_extended_alt and (middle_curl or ring_curl or pinky_curl):
        # Fallback to wrist angle mode
        detection_mode = "wrist_angle"
        confidence_score = 0.5
        is_gun = True
    else:
        detection_mode = "none"
        confidence_score = 0
        is_gun = False
    
    if is_gun:
        index_coords = (int(index_tip.x * frame_width), int(index_tip.y * frame_height))
        return True, index_coords, thumb_tip, middle_pip, thumb_middle_dist, confidence_score
    else:
        return False, None, None, None, None, confidence_score

def spawn_target():
    # Avoid spawning in camera area
    x = random.randint(TARGET_SIZE, SCREEN_WIDTH - TARGET_SIZE - CAMERA_WIDTH - 40)
    y = random.randint(TARGET_SIZE, SCREEN_HEIGHT - TARGET_SIZE)
    return Target(x, y)

def main():
    global shooting_detected, last_shoot_time, previous_thumb_y, previous_time
    global score, targets, last_target_spawn, shoot_pos, shoot_animation_time
    
    # Initialize MediaPipe with enhanced settings
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        min_detection_confidence=0.7, 
        min_tracking_confidence=0.6, 
        max_num_hands=1,
        model_complexity=1  # Higher complexity for better tracking
    )
    mp_drawing = mp.solutions.drawing_utils
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    
    # Initialize Pygame screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("arcvde")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    big_font = pygame.font.Font(None, 72)
    
    running = True
    
    while running:
        current_time = pygame.time.get_ticks()
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Read camera frame
        ret, frame = cap.read()
        if not ret:
            continue
        
        frame = cv2.flip(frame, 1)
        
        # Process hand tracking
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = hands.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Track hand and detect shooting
        index_finger_pos = None
        shoot_detected = False
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # Use enhanced detection
                is_gun, index_tip_coords, thumb_tip, middle_mcp, thumb_middle_dist, conf = enhanced_finger_gun_detection(
                    hand_landmarks, frame_width, frame_height
                )
                
                if is_gun and index_tip_coords:
                    # Map finger position to game screen
                    game_x = int((index_tip_coords[0] / frame_width) * SCREEN_WIDTH)
                    game_y = int((index_tip_coords[1] / frame_height) * SCREEN_HEIGHT)
                    index_finger_pos = (game_x, game_y)
                    
                    # Draw crosshair on camera feed with detection mode indicator
                    color = (0, 255, 0) if detection_mode == "standard" else (255, 255, 0) if detection_mode == "depth" else (0, 255, 255)
                    cv2.circle(image, index_tip_coords, 10, color, -1)
                    cv2.putText(image, f"Mode: {detection_mode}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    cv2.putText(image, f"Conf: {conf:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    
                    # Detect shooting gesture
                    current_thumb_y = thumb_tip.y
                    if previous_thumb_y is not None:
                        delta_time = time.time() - previous_time
                        if delta_time != 0:
                            thumb_velocity = (current_thumb_y - previous_thumb_y) / delta_time
                        else:
                            thumb_velocity = 0
                        
                        # More lenient shooting detection for different modes
                        velocity_threshold = shoot_velocity_threshold * (1.5 if detection_mode != "standard" else 1.0)
                        distance_threshold = shoot_distance_threshold * (1.5 if detection_mode != "standard" else 1.0)
                        
                        if thumb_velocity > velocity_threshold and thumb_middle_dist < distance_threshold:
                            if not shooting_detected and time.time() - last_shoot_time > cooldown_duration:
                                shoot_detected = True
                                shoot_pos = index_finger_pos
                                shoot_animation_time = current_time
                                shooting_detected = True
                                last_shoot_time = time.time()
                                cv2.putText(image, "SHOOT!", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        else:
                            shooting_detected = False
                    
                    previous_thumb_y = current_thumb_y
                    previous_time = time.time()
                else:
                    shooting_detected = False
                    previous_thumb_y = None
                    previous_time = 0
        else:
            shooting_detected = False
            previous_thumb_y = None
            previous_time = 0
        
        # Spawn targets
        if current_time - last_target_spawn > TARGET_SPAWN_TIME and len(targets) < MAX_TARGETS:
            targets.append(spawn_target())
            last_target_spawn = current_time
        
        # Check for hits
        if shoot_detected and shoot_pos:
            for target in targets:
                if not target.hit and target.check_hit(shoot_pos[0], shoot_pos[1]):
                    score += 10
                    break
        
        # Remove hit targets after animation
        targets = [t for t in targets if not t.hit or time.time() - t.hit_time < 0.3]
        
        # Clear screen
        screen.fill(BLACK)
        
        # Draw game elements
        for target in targets:
            target.draw(screen)
        
        # Draw crosshair if aiming
        if index_finger_pos:
            # Color based on detection mode
            crosshair_color = GREEN if detection_mode == "standard" else YELLOW if detection_mode == "depth" else PURPLE
            pygame.draw.circle(screen, crosshair_color, index_finger_pos, 20, 2)
            pygame.draw.line(screen, crosshair_color, (index_finger_pos[0] - 30, index_finger_pos[1]), 
                           (index_finger_pos[0] + 30, index_finger_pos[1]), 2)
            pygame.draw.line(screen, crosshair_color, (index_finger_pos[0], index_finger_pos[1] - 30), 
                           (index_finger_pos[0], index_finger_pos[1] + 30), 2)
        
        # Draw shooting animation
        if current_time - shoot_animation_time < 200 and shoot_pos:
            pygame.draw.circle(screen, YELLOW, shoot_pos, 40, 3)
            pygame.draw.circle(screen, WHITE, shoot_pos, 30, 2)
        
        # Draw score
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        # Draw detection mode indicator
        if detection_mode != "none":
            mode_color = GREEN if detection_mode == "standard" else YELLOW if detection_mode == "depth" else PURPLE
            mode_text = small_font.render(f"Detection: {detection_mode.title()}", True, mode_color)
            screen.blit(mode_text, (10, 50))
        
        # Draw instructions
        inst_text = font.render("Make finger gun to aim, flick thumb down to shoot!", True, WHITE)
        screen.blit(inst_text, (10, SCREEN_HEIGHT - 40))
        
        # Prepare camera frame for pygame
        resized_frame = cv2.resize(image, (CAMERA_WIDTH, CAMERA_HEIGHT))
        frame_surface = pygame.surfarray.make_surface(cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB).swapaxes(0, 1))
        
        # Draw camera feed border
        pygame.draw.rect(screen, WHITE, (CAMERA_X - 2, CAMERA_Y - 2, CAMERA_WIDTH + 4, CAMERA_HEIGHT + 4), 2)
        screen.blit(frame_surface, (CAMERA_X, CAMERA_Y))
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()

if __name__ == "__main__":
    main()