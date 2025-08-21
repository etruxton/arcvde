"""
Loading screen with animated logo and progress indicators
"""

import pygame
import math
from typing import Optional
from utils.constants import *

class LoadingScreen:
    """Loading screen with animated logo and loading effects"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        
        # Load assets
        self.logo = pygame.image.load("assets/arCVde-2.png")
        
        # Scale logo to fit nicely on screen
        logo_width = min(600, SCREEN_WIDTH * 0.6)
        logo_height = int(logo_width * (self.logo.get_height() / self.logo.get_width()))
        self.logo = pygame.transform.scale(self.logo, (logo_width, logo_height))
        
        # Animation state
        self.animation_time = 0
        self.fade_alpha = 0
        self.logo_scale = 0.5
        self.progress = 0
        self.loading_dots = 0
        self.spin_angle = 0
        
        # Loading phases
        self.phase = "fade_in"  # fade_in -> logo_grow -> loading -> complete
        self.phase_start_time = 0
        
        # External loading status
        self.external_loading_complete = False
        
        # Create font
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Particle system for sparkles
        self.particles = []
        
    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update loading screen animations"""
        self.animation_time += dt
        
        # Update phase timing
        if self.phase == "fade_in":
            if self.animation_time < 1.0:
                self.fade_alpha = int(255 * self.animation_time)
            else:
                self.phase = "logo_grow"
                self.phase_start_time = self.animation_time
                self.fade_alpha = 255
        
        elif self.phase == "logo_grow":
            grow_time = self.animation_time - self.phase_start_time
            if grow_time < 1.5:
                # Smooth scaling with easing
                t = grow_time / 1.5
                eased_t = 1 - (1 - t) ** 3  # Cubic ease out
                self.logo_scale = 0.5 + 0.5 * eased_t
            else:
                self.phase = "loading"
                self.phase_start_time = self.animation_time
                self.logo_scale = 1.0
        
        elif self.phase == "loading":
            loading_time = self.animation_time - self.phase_start_time
            
            # Progress based on actual loading status
            if not self.external_loading_complete:
                # Show progress while loading (up to 90%)
                base_progress = min(90, (loading_time / 3.0) * 90)
                self.progress = base_progress
            else:
                # Complete the progress bar quickly once loading is done
                self.progress = min(100, 90 + (loading_time - 3.0) * 100)
                if self.progress >= 100:
                    self.phase = "complete"
                    self.phase_start_time = self.animation_time
        
        elif self.phase == "complete":
            complete_time = self.animation_time - self.phase_start_time
            if complete_time > 0.5:  # Wait a bit before transitioning
                return GAME_STATE_MENU
        
        # Update spinning logo
        self.spin_angle += dt * 180  # 180 degrees per second
        
        # Update loading dots animation
        self.loading_dots = int((self.animation_time * 2) % 4)
        
        # Update particles
        self._update_particles(dt)
        
        # Add new particles occasionally
        if self.phase == "loading" and len(self.particles) < 20 and self.animation_time % 0.1 < dt:
            self._add_particle()
        
        return None
    
    def set_loading_complete(self, complete: bool):
        """Set external loading completion status"""
        self.external_loading_complete = complete
    
    def _update_particles(self, dt: float):
        """Update particle positions and remove expired ones"""
        for particle in self.particles[:]:  # Copy list to iterate safely
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['life'] -= dt
            particle['alpha'] = max(0, min(255, particle['life'] * 255))
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def _add_particle(self):
        """Add a new sparkle particle"""
        import random
        
        # Create particles around the logo area
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2 - 50
        
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(100, 200)
        
        particle = {
            'x': center_x + math.cos(angle) * distance,
            'y': center_y + math.sin(angle) * distance,
            'vx': random.uniform(-50, 50),
            'vy': random.uniform(-50, 50),
            'life': random.uniform(1.0, 2.0),
            'alpha': 255,
            'color': random.choice([UI_ACCENT, WHITE, YELLOW])
        }
        self.particles.append(particle)
    
    def draw(self):
        """Draw the loading screen"""
        # Clear screen with dark background
        self.screen.fill(UI_BACKGROUND)
        
        # Create a subtle gradient background
        self._draw_gradient_background()
        
        if self.phase == "fade_in" or self.fade_alpha > 0:
            # Main logo
            logo_rect = self.logo.get_rect()
            
            # Apply scaling
            scaled_logo = pygame.transform.scale(
                self.logo, 
                (int(logo_rect.width * self.logo_scale), 
                 int(logo_rect.height * self.logo_scale))
            )
            
            # Create surface with alpha for fading
            logo_surface = scaled_logo.copy()
            logo_surface.set_alpha(self.fade_alpha)
            
            # Center the logo
            scaled_rect = scaled_logo.get_rect()
            scaled_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
            
            # Add pulsing effect when loading
            if self.phase == "loading":
                pulse = math.sin(self.animation_time * 4) * 0.05 + 1.0
                pulse_logo = pygame.transform.scale(
                    scaled_logo,
                    (int(scaled_rect.width * pulse), int(scaled_rect.height * pulse))
                )
                pulse_rect = pulse_logo.get_rect(center=scaled_rect.center)
                self.screen.blit(pulse_logo, pulse_rect)
            else:
                self.screen.blit(logo_surface, scaled_rect)
        
        # Draw particles
        self._draw_particles()
        
        # Loading progress and text
        if self.phase == "loading" or self.phase == "complete":
            self._draw_loading_elements()
    
    def _draw_gradient_background(self):
        """Draw a subtle gradient background"""
        for y in range(SCREEN_HEIGHT):
            # Calculate gradient color
            factor = y / SCREEN_HEIGHT
            r = int(UI_BACKGROUND[0] + (40 - UI_BACKGROUND[0]) * factor)
            g = int(UI_BACKGROUND[1] + (40 - UI_BACKGROUND[1]) * factor)
            b = int(UI_BACKGROUND[2] + (60 - UI_BACKGROUND[2]) * factor)
            
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    def _draw_particles(self):
        """Draw sparkle particles"""
        for particle in self.particles:
            if particle['alpha'] > 0:
                # Create a surface for the particle with alpha
                particle_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
                color_with_alpha = (*particle['color'], int(particle['alpha']))
                pygame.draw.circle(particle_surface, color_with_alpha, (2, 2), 2)
                
                self.screen.blit(particle_surface, (particle['x'] - 2, particle['y'] - 2))
    
    def _draw_loading_elements(self):
        """Draw loading progress bar and text"""
        # Loading text with animated dots
        dots = "." * self.loading_dots
        if not self.external_loading_complete:
            if self.progress < 30:
                loading_text = self.font.render(f"Initializing camera{dots}", True, WHITE)
            elif self.progress < 70:
                loading_text = self.font.render(f"Loading game assets{dots}", True, WHITE)
            else:
                loading_text = self.font.render(f"Preparing game{dots}", True, WHITE)
        else:
            loading_text = self.font.render("Ready!", True, GREEN)
        
        text_rect = loading_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
        self.screen.blit(loading_text, text_rect)
        
        # Progress bar
        bar_width = 400
        bar_height = 8
        bar_x = (SCREEN_WIDTH - bar_width) // 2
        bar_y = SCREEN_HEIGHT // 2 + 180
        
        # Background bar
        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
        
        # Progress fill with gradient effect
        if self.progress > 0:
            fill_width = int(bar_width * (self.progress / 100))
            
            # Create gradient fill
            for x in range(fill_width):
                progress_factor = x / fill_width if fill_width > 0 else 0
                r = int(UI_ACCENT[0] * (1 - progress_factor * 0.3))
                g = int(UI_ACCENT[1] * (1 - progress_factor * 0.2))
                b = int(UI_ACCENT[2])
                
                pygame.draw.line(self.screen, (r, g, b), 
                               (bar_x + x, bar_y), (bar_x + x, bar_y + bar_height))
        
        # Progress percentage
        if self.progress > 0:
            progress_text = self.small_font.render(f"{int(self.progress)}%", True, WHITE)
            progress_rect = progress_text.get_rect(center=(SCREEN_WIDTH // 2, bar_y + 25))
            self.screen.blit(progress_text, progress_rect)
    
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events (skip loading on click)"""
        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            # Skip to menu if user presses any key or clicks
            return GAME_STATE_MENU
        return None