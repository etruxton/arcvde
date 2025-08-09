"""
Camera management utilities
"""

import cv2
import pygame
import numpy as np
from typing import List, Optional, Tuple

class CameraManager:
    """Manages camera operations and device detection"""
    
    def __init__(self):
        self.current_camera = None
        self.camera_id = 0
        self.available_cameras = []
        self.frame_width = 640
        self.frame_height = 480
        self._scan_cameras()
    
    def _scan_cameras(self) -> None:
        """Scan for available cameras"""
        self.available_cameras = []
        
        # Test up to 10 camera indices
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    self.available_cameras.append(i)
                cap.release()
            else:
                # If we can't open the camera, we've likely reached the end
                if i > 2:  # Allow for some gaps in low indices
                    break
        
        if not self.available_cameras:
            self.available_cameras = [0]  # Fallback
    
    def get_available_cameras(self) -> List[int]:
        """Get list of available camera IDs"""
        return self.available_cameras.copy()
    
    def initialize_camera(self, camera_id: int = 0) -> bool:
        """Initialize camera with given ID"""
        if self.current_camera:
            self.current_camera.release()
        
        self.current_camera = cv2.VideoCapture(camera_id)
        
        if not self.current_camera.isOpened():
            return False
        
        # Set camera properties
        self.current_camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.current_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        
        # Update actual dimensions
        self.frame_width = int(self.current_camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.current_camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.camera_id = camera_id
        return True
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read a frame from the current camera"""
        if not self.current_camera:
            return False, None
        
        ret, frame = self.current_camera.read()
        if ret:
            frame = cv2.flip(frame, 1)  # Mirror the image
        
        return ret, frame
    
    def frame_to_pygame_surface(self, frame: np.ndarray, size: Tuple[int, int]) -> pygame.Surface:
        """Convert OpenCV frame to pygame surface"""
        if frame is None:
            # Create a black surface if no frame
            surface = pygame.Surface(size)
            surface.fill((0, 0, 0))
            return surface
        
        # Resize frame
        resized_frame = cv2.resize(frame, size)
        
        # Convert BGR to RGB and create pygame surface
        rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
        surface = pygame.surfarray.make_surface(rgb_frame.swapaxes(0, 1))
        
        return surface
    
    def switch_camera(self, camera_id: int) -> bool:
        """Switch to a different camera"""
        if camera_id in self.available_cameras:
            return self.initialize_camera(camera_id)
        return False
    
    def get_camera_info(self) -> dict:
        """Get current camera information"""
        return {
            'current_id': self.camera_id,
            'available_cameras': self.available_cameras,
            'resolution': (self.frame_width, self.frame_height),
            'is_open': self.current_camera.isOpened() if self.current_camera else False
        }
    
    def release(self) -> None:
        """Release camera resources"""
        if self.current_camera:
            self.current_camera.release()
            self.current_camera = None