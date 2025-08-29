"""
Enemy system for arcade-style shooting game with doom-like perspective
"""

# Standard library imports
import math
import random
import time
from typing import List, Optional, Tuple

# Third-party imports
import pygame

# Local application imports
from utils.constants import BLACK, SCREEN_HEIGHT


class BloodParticle:
    """A blood particle with physics and 3D perspective"""

    def __init__(self, x: float, y: float, vx: float, vy: float, size: int, enemy_z: float = 0.5):
        self.x = x
        self.y = y
        self.vx = vx  # Velocity x
        self.vy = vy  # Velocity y
        self.size = size
        self.original_size = size
        self.lifetime = 2.5  # Seconds - moderate lifetime
        self.age = 0
        self.gravity = 1500  # Pixels per second squared - fast but not too fast
        self.splattered = False

        # 3D perspective properties
        self.enemy_z = enemy_z  # Distance of enemy when shot (0=close, 1=far)
        # Calculate ground level based on perspective
        horizon_y = SCREEN_HEIGHT * 0.4
        # Ground gets lower on screen as distance increases
        self.ground_y = horizon_y + (SCREEN_HEIGHT - horizon_y) * (1.0 - enemy_z * 0.7)

        # Scale particle size based on distance
        perspective_scale = 1.0 / (enemy_z + 0.3)
        self.size = int(self.size * perspective_scale * 0.7)  # Make blood smaller for perspective
        self.original_size = self.size

    def update(self, dt: float):
        """Update particle physics"""
        self.age += dt
        self.lifetime -= dt

        if not self.splattered:
            # Apply velocity
            self.x += self.vx * dt
            self.y += self.vy * dt

            # Apply gravity (less gravity for distant particles for perspective illusion)
            gravity_scale = 0.5 + 0.5 * (1 - self.enemy_z)  # Less gravity when far
            self.vy += self.gravity * gravity_scale * dt

            # Apply air resistance (balanced for good spread with fast fall)
            self.vx *= 0.96  # Moderate horizontal resistance
            self.vy *= 0.98  # Less resistance vertically for faster fall

            # Check if hit ground at the correct perspective depth
            if self.y > self.ground_y:
                self.splattered = True
                self.y = self.ground_y + random.randint(-3, 3)
                # Increase size when splattering (less increase for distant blood)
                size_increase = 1.3 + 0.3 * (1 - self.enemy_z)
                self.size = int(self.original_size * size_increase)

    def draw(self, screen: pygame.Surface):
        """Draw the blood particle"""
        # Calculate alpha based on lifetime
        alpha = max(0, int(255 * (self.lifetime / 3.0)))
        if alpha <= 0:
            return

        # Create surface for alpha blending
        particle_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)

        # Color gets darker over time
        brightness = max(0.3, 1.0 - self.age / 3.0)
        color = (int(200 * brightness), int(20 * brightness), int(20 * brightness), alpha)

        if self.splattered:
            # Draw as ellipse when splattered on ground with perspective
            # Make ellipse flatter for distant blood
            ellipse_height = max(2, int(self.size * (0.3 + 0.3 * (1 - self.enemy_z))))
            pygame.draw.ellipse(particle_surface, color, (0, self.size - ellipse_height // 2, self.size * 2, ellipse_height))
        else:
            # Draw as circle while flying
            pygame.draw.circle(particle_surface, color, (self.size, self.size), self.size)

        screen.blit(particle_surface, (int(self.x - self.size), int(self.y - self.size)))


class Enemy:
    """Base enemy class with 3D-like perspective rendering"""

    def __init__(self, x: float, z: float, enemy_type: str = "zombie"):
        # Position in 3D space
        self.x = x  # Horizontal position (-1 to 1)
        self.y = 0  # Vertical position (0 = ground level)
        self.z = z  # Distance from player (0 = close, 1 = far)

        # Enemy properties
        self.enemy_type = enemy_type
        self.health = self._get_initial_health()
        self.max_health = self.health
        self.speed = self._get_speed()
        self.damage = self._get_damage()
        self.score_value = self._get_score_value()

        # State
        self.alive = True
        self.attacking = False
        self.hit_flash_time = 0
        self.death_time = 0
        self.last_attack_time = 0
        self.attack_cooldown = 2.0

        # Animation
        self.animation_time = random.random() * math.pi * 2
        self.walk_cycle = 0
        self.death_animation_progress = 0

        # Visual properties
        self.color_scheme = self._get_color_scheme()
        self.base_size = self._get_base_size()

        # Blood effects with physics
        self.blood_particles = []  # List of blood particle objects with physics

    def _get_initial_health(self) -> int:
        """Get initial health based on enemy type"""
        health_map = {"zombie": 30, "demon": 50, "skull": 1, "giant": 100}  # Die in one shot
        return health_map.get(self.enemy_type, 30)

    def _get_speed(self) -> float:
        """Get movement speed based on enemy type"""
        speed_map = {"zombie": 0.15, "demon": 0.18, "skull": 0.35, "giant": 0.10}  # Reduced from 0.25 for better balance
        return speed_map.get(self.enemy_type, 0.15)

    def _get_damage(self) -> int:
        """Get damage based on enemy type"""
        damage_map = {"zombie": 10, "demon": 20, "skull": 15, "giant": 30}
        return damage_map.get(self.enemy_type, 10)

    def _get_score_value(self) -> int:
        """Get score value based on enemy type"""
        score_map = {"zombie": 100, "demon": 200, "skull": 150, "giant": 500}
        return score_map.get(self.enemy_type, 100)

    def _get_color_scheme(self) -> dict:
        """Get color scheme based on enemy type"""
        schemes = {
            "zombie": {"body": (60, 80, 60), "eyes": (255, 0, 0), "detail": (40, 60, 40)},
            "demon": {"body": (150, 30, 30), "eyes": (255, 255, 0), "detail": (100, 20, 20)},
            "skull": {"body": (200, 200, 200), "eyes": (0, 255, 255), "detail": (150, 150, 150)},
            "giant": {"body": (80, 40, 120), "eyes": (255, 128, 0), "detail": (60, 30, 90)},
        }
        return schemes.get(self.enemy_type, schemes["zombie"])

    def _get_base_size(self) -> int:
        """Get base size based on enemy type"""
        size_map = {"zombie": 80, "demon": 90, "skull": 60, "giant": 120}
        return size_map.get(self.enemy_type, 80)

    def update(self, dt: float, player_health: int) -> Optional[int]:
        """Update enemy state, returns damage if attacking"""
        if not self.alive:
            # Update death animation
            if self.death_animation_progress < 1.0:
                self.death_animation_progress = min(1.0, (time.time() - self.death_time) / 0.5)
            return None

        # Update animation
        self.animation_time += dt * 2
        self.walk_cycle += dt * 4

        # Move towards player
        if self.z > 0.15:  # Stop a bit further away to stay visible
            self.z -= self.speed * dt

            # Slight side-to-side movement for variety
            if self.enemy_type != "giant":
                self.x += math.sin(self.animation_time) * 0.02 * dt
                # Much stricter clamping to keep enemies on screen
                # Adjust based on distance (closer enemies need tighter bounds)
                max_x = 0.8 - (0.3 * (1 - self.z))
                self.x = max(-max_x, min(max_x, self.x))
        else:
            # At player, can attack
            self.z = 0.15  # Keep enemy visible and shootable
            # Keep close enemies well within screen bounds
            self.x = max(-0.5, min(0.5, self.x))
            current_time = time.time()
            if current_time - self.last_attack_time > self.attack_cooldown:
                self.attacking = True
                self.last_attack_time = current_time
                return self.damage

        # Update hit flash
        if self.hit_flash_time > 0:
            self.hit_flash_time -= dt

        return None

    def take_damage(self, damage: int, knockback: bool = False, hit_pos: Tuple[int, int] = None) -> bool:
        """Take damage, returns True if killed"""
        if not self.alive:
            return False

        self.health -= damage
        self.hit_flash_time = 0.2

        # Create blood splatter at hit position with physics
        if hit_pos:
            # Add multiple blood particles that explode outward
            num_particles = random.randint(3, 6) if self.health > 0 else random.randint(8, 15)
            for _ in range(num_particles):
                # Create particle with velocity exploding outward
                angle = random.uniform(0, math.pi * 2)  # Full 360 degree spread
                # Balanced speeds - not too far, not too close
                if self.health > 0:
                    speed = random.uniform(200, 400)  # Normal hit
                else:
                    speed = random.uniform(300, 600)  # Death - more dramatic but not excessive

                # Scale speed based on distance for perspective
                perspective_scale = 1.0 / (self.z + 0.3)
                speed = speed * perspective_scale * 0.7

                # Balanced horizontal/vertical movement
                vx_multiplier = 0.85  # Good horizontal spread
                vy_offset = -150  # Moderate upward burst

                particle = BloodParticle(
                    x=hit_pos[0],
                    y=hit_pos[1],
                    vx=math.cos(angle) * speed * vx_multiplier,
                    vy=math.sin(angle) * speed * 0.7 + vy_offset,  # Slightly reduced vertical component
                    size=random.randint(3, 8) if self.health > 0 else random.randint(4, 10),
                    enemy_z=self.z,  # Pass enemy's distance for perspective
                )
                self.blood_particles.append(particle)

        # Apply knockback effect
        if knockback and self.z < 0.5:
            self.z = min(0.5, self.z + 0.1)

        if self.health <= 0:
            self.alive = False
            self.death_time = time.time()
            return True

        return False

    def get_screen_position(self, screen_width: int, screen_height: int) -> Tuple[int, int]:
        """Convert 3D position to 2D screen coordinates with perspective"""
        # Perspective projection - clamp minimum z to keep enemy visible
        z_clamped = max(0.1, self.z)
        perspective_scale = 1.0 / (z_clamped + 0.3)

        # Horizon at 40% from top
        horizon_y = screen_height * 0.4

        # Calculate screen position
        screen_x = screen_width // 2 + (self.x * screen_width * 0.4 * perspective_scale)
        screen_y = horizon_y + (self.y + 0.5) * screen_height * 0.4 * perspective_scale

        return int(screen_x), int(screen_y)

    def get_size(self) -> int:
        """Get current size based on distance (perspective)"""
        # Clamp minimum z to keep enemy at reasonable size
        z_clamped = max(0.1, self.z)
        perspective_scale = 1.0 / (z_clamped + 0.3)
        # Also clamp maximum size when very close
        return min(int(self.base_size * 2.5), int(self.base_size * perspective_scale))

    def update_and_draw_blood(self, screen: pygame.Surface, dt: float):
        """Update and draw blood particles with physics"""
        remaining_particles = []
        for particle in self.blood_particles:
            particle.update(dt)
            if particle.lifetime > 0:
                particle.draw(screen)
                remaining_particles.append(particle)
        self.blood_particles = remaining_particles

    def draw(self, screen: pygame.Surface, screen_width: int, screen_height: int, debug_hitbox: bool = False):
        """Draw enemy with perspective and animations"""
        # Blood particles are now drawn separately with physics update

        if self.death_animation_progress >= 1.0:
            return  # Fully dead, don't draw enemy (but blood remains)

        x, y = self.get_screen_position(screen_width, screen_height)
        size = self.get_size()

        # Apply death animation (fall down)
        if not self.alive:
            y += int(size * self.death_animation_progress)
            size = int(size * (1 - self.death_animation_progress * 0.5))

        # Hit flash effect
        if self.hit_flash_time > 0:
            body_color = (255, 255, 255)
        else:
            body_color = self.color_scheme["body"]

        # Walking animation
        walk_offset = math.sin(self.walk_cycle) * size * 0.05 if self.alive else 0

        if self.enemy_type == "zombie":
            self._draw_zombie(screen, x, int(y + walk_offset), size, body_color)
        elif self.enemy_type == "demon":
            self._draw_demon(screen, x, int(y + walk_offset), size, body_color)
        elif self.enemy_type == "skull":
            self._draw_skull(screen, x, int(y + walk_offset), size, body_color)
        elif self.enemy_type == "giant":
            self._draw_giant(screen, x, int(y + walk_offset), size, body_color)

        # Draw health bar if damaged and alive (but not for skulls since they die in 1 hit)
        if self.alive and self.health < self.max_health and self.enemy_type != "skull":
            # Position health bar well above the enemy's head
            health_bar_y = y - size - 20 if self.enemy_type != "skull" else y - size // 2 - 30
            self._draw_health_bar(screen, x, health_bar_y, size)

        # Debug: Draw hitbox
        if debug_hitbox and self.alive:
            hitbox = self.get_hitbox(screen_width, screen_height)
            pygame.draw.rect(screen, (255, 0, 255), hitbox, 2)

    def _draw_zombie(self, screen: pygame.Surface, x: int, y: int, size: int, body_color: tuple):
        """Draw detailed zombie enemy with rotting features"""
        # Tattered clothing body
        body_rect = pygame.Rect(x - size // 3, y - size // 2, size * 2 // 3, size)
        pygame.draw.rect(screen, body_color, body_rect)

        # Torn clothing details
        for i in range(3):
            tear_y = y - size // 2 + random.randint(size // 4, size * 3 // 4)
            tear_x = x - size // 3 + random.randint(0, size * 2 // 3)
            pygame.draw.polygon(
                screen,
                (30, 40, 30),
                [(tear_x, tear_y), (tear_x - size // 15, tear_y + size // 10), (tear_x + size // 15, tear_y + size // 10)],
            )

        # Ribs showing through (lowered)
        for i in range(-1, 2):
            rib_y = y - size // 8 + i * (size // 8)  # Lowered from y - size//4
            pygame.draw.arc(
                screen,
                (200, 200, 180),
                pygame.Rect(x - size // 4, rib_y, size // 2, size // 8),
                0,
                math.pi,
                max(1, size // 30),
            )

        # Head with skull features
        head_size = size // 3
        pygame.draw.circle(screen, body_color, (x, y - size // 2 - head_size // 2), head_size)

        # Hollow eye sockets with pulsing red eyes
        eye_y = y - size // 2 - head_size // 2
        for eye_x in [x - head_size // 3, x + head_size // 3]:
            # Dark socket
            pygame.draw.circle(screen, (20, 20, 20), (eye_x, eye_y), max(3, size // 12))
            # Pulsing red glow (slower pulse)
            pulse = (math.sin(self.animation_time * 2) + 1) / 2  # 0 to 1 pulse, slower
            glow_size = max(2, size // 20) + int(pulse * size // 15)
            pygame.draw.circle(screen, self.color_scheme["eyes"], (eye_x, eye_y), glow_size)
            # Inner bright glow that also pulses
            pygame.draw.circle(screen, (255, 100 + int(pulse * 100), 100), (eye_x, eye_y), max(1, glow_size // 2))
        mouth_y = y - size // 2 - head_size // 4 + head_size // 3
        # Teeth
        for i in range(-2, 3):
            tooth_x = x + i * (head_size // 6)
            tooth_size = random.randint(size // 30, size // 20)
            pygame.draw.polygon(
                screen,
                (255, 255, 230),
                [(tooth_x, mouth_y), (tooth_x - 2, mouth_y + tooth_size), (tooth_x + 2, mouth_y + tooth_size)],
            )

        # Arms with exposed bone
        arm_angle = math.sin(self.animation_time) * 0.2
        for arm_side, direction in [(-1, 1), (1, -1)]:
            arm_start_x = x + arm_side * size // 3
            arm_end_x = x + arm_side * (size // 2 + size // 4 * math.cos(direction * arm_angle))
            arm_end_y = y - size // 4 + size // 4 * math.sin(direction * arm_angle)

            # Arm flesh
            pygame.draw.line(screen, body_color, (arm_start_x, y - size // 4), (arm_end_x, arm_end_y), max(3, size // 15))
            # Exposed bone
            pygame.draw.line(
                screen,
                (230, 230, 210),
                (arm_start_x, y - size // 4),
                ((arm_start_x + arm_end_x) // 2, (y - size // 4 + arm_end_y) // 2),
                max(1, size // 30),
            )

            # Clawed fingers
            for finger in range(3):
                finger_angle = direction * arm_angle + (finger - 1) * 0.2
                finger_x = arm_end_x + math.cos(finger_angle) * size // 15
                finger_y = arm_end_y + math.sin(finger_angle) * size // 15
                pygame.draw.line(screen, (50, 50, 40), (arm_end_x, arm_end_y), (finger_x, finger_y), max(1, size // 40))

        # Dripping decay effect
        if random.random() < 0.3:
            drip_x = x + random.randint(-size // 3, size // 3)
            drip_y = y + size // 2
            pygame.draw.circle(screen, (100, 120, 80), (drip_x, drip_y), max(1, size // 30))

    def _draw_demon(self, screen: pygame.Surface, x: int, y: int, size: int, body_color: tuple):
        """Draw terrifying demon with bat wings and flames"""
        # Muscular body with scales
        body_points = [(x, y - size // 2), (x - size // 2, y + size // 3), (x + size // 2, y + size // 3)]
        pygame.draw.polygon(screen, body_color, body_points)

        # Scale texture (properly positioned within triangle body)
        # Triangle body spans from (x, y - size//2) at top to base at (y + size//3)
        # Width varies with height - narrower at top, wider at bottom
        for j in range(3):  # Rows of scales
            # Calculate Y position and width at this height
            scale_y = y - size // 3 + j * (size // 4)
            # Calculate triangle width at this Y position
            # Triangle is narrowest at top (y - size//2) and widest at bottom (y + size//3)
            height_ratio = (scale_y - (y - size // 2)) / (size * 5 / 6)  # 0 at top, 1 at bottom
            triangle_half_width = size // 2 * max(0.2, height_ratio)  # Min width to avoid scales at tip

            # Place scales within the triangle width at this height
            num_scales = 2 if j == 0 else 3  # Fewer scales at top
            for i in range(num_scales):
                if num_scales == 2:
                    scale_x = x - triangle_half_width // 2 + i * triangle_half_width
                else:
                    scale_x = x - triangle_half_width + i * triangle_half_width

                # Only draw if within reasonable bounds
                if abs(scale_x - x) <= triangle_half_width:
                    pygame.draw.arc(
                        screen, (100, 20, 20), pygame.Rect(scale_x - size // 16, scale_y, size // 8, size // 8), 0, math.pi, 1
                    )

        # Twisted horns with ridges
        horn_size = size // 3
        for horn_side in [-1, 1]:
            # Main horn
            horn_points = [
                (x + horn_side * size // 4, y - size // 2),
                (x + horn_side * size // 3, y - size // 2 - horn_size),
                (x + horn_side * size // 3 + horn_side * size // 8, y - size // 2 - horn_size + size // 8),
                (x + horn_side * size // 5, y - size // 2),
            ]
            pygame.draw.polygon(screen, (150, 30, 30), horn_points)
            # Horn ridges
            for ridge in range(3):
                ridge_y = y - size // 2 - (ridge * horn_size // 3)
                pygame.draw.line(
                    screen,
                    (100, 20, 20),
                    (x + horn_side * size // 4, ridge_y),
                    (x + horn_side * size // 3, ridge_y - horn_size // 6),
                    max(1, size // 40),
                )

        # Burning eyes with fire effect
        eye_size = max(4, size // 10)
        for eye_x in [x - size // 5, x + size // 5]:
            # Fire aura around eyes
            for flame in range(3):
                flame_size = eye_size + flame * 2
                # flame_alpha = 100 - flame * 30
                flame_color = (255, 200 - flame * 50, 0)
                pygame.draw.circle(screen, flame_color, (eye_x, y - size // 3), flame_size, 1)
            # Main eye
            pygame.draw.circle(screen, self.color_scheme["eyes"], (eye_x, y - size // 3), eye_size)
            # Vertical slit pupil that moves side to side (looking around)
            look_offset = math.sin(self.animation_time * 2) * eye_size // 3
            pygame.draw.line(
                screen,
                (0, 0, 0),
                (eye_x + look_offset, y - size // 3 - eye_size + 2),
                (eye_x + look_offset, y - size // 3 + eye_size - 2),
                2,
            )

        # Large fangs (removed black mouth line)
        mouth_y = y - size // 5
        for fang_x in [x - size // 5, x + size // 5]:
            pygame.draw.polygon(
                screen,
                (255, 255, 200),
                [(fang_x, mouth_y), (fang_x - size // 20, mouth_y + size // 8), (fang_x + size // 20, mouth_y + size // 8)],
            )

        # Detailed bat wings
        # wing_spread = math.sin(self.animation_time * 2) * 0.3
        for wing_side in [-1, 1]:
            # Wing membrane
            wing_points = [
                (x + wing_side * size // 3, y - size // 3),
                (x + wing_side * size, y - size // 2 + math.sin(self.animation_time * 2) * size // 10),
                (x + wing_side * (size + size // 3), y),
                (x + wing_side * size, y + size // 4),
                (x + wing_side * size // 2, y),
            ]
            pygame.draw.polygon(screen, (80, 20, 20), wing_points)
            # Wing bones
            for bone in range(3):
                bone_end_x = x + wing_side * (size + bone * size // 6)
                bone_end_y = y - size // 3 + bone * size // 4
                pygame.draw.line(
                    screen,
                    (60, 15, 15),
                    (x + wing_side * size // 3, y - size // 3),
                    (bone_end_x, bone_end_y),
                    max(1, size // 30),
                )

        # Flaming aura effect
        if random.random() < 0.5:
            for _ in range(3):
                flame_x = x + random.randint(-size // 2, size // 2)
                flame_y = y + size // 3 + random.randint(0, size // 6)
                flame_size = random.randint(2, 4)
                pygame.draw.circle(screen, (255, random.randint(100, 200), 0), (flame_x, flame_y), flame_size)

    def _draw_skull(self, screen: pygame.Surface, x: int, y: int, size: int, body_color: tuple):
        """Draw ghostly floating skull with ethereal effects"""
        # Floating animation with rotation
        float_offset = math.sin(self.animation_time * 3) * size * 0.1
        # rotation = math.sin(self.animation_time * 2) * 0.1
        y = int(y + float_offset)

        # Ethereal aura (ghostly trail)
        for trail in range(3):
            trail_alpha = 30 - trail * 10
            trail_y = y - trail * 3
            trail_size = size // 2 + trail * 3
            aura_surface = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura_surface, (150, 150, 255, trail_alpha), (trail_size, trail_size), trail_size)
            screen.blit(aura_surface, (x - trail_size, trail_y - trail_size))

        # Cracked skull
        skull_size = size // 2
        pygame.draw.circle(screen, body_color, (x, y), skull_size)

        # Skull cracks
        for crack in range(2):
            crack_start_x = x + random.randint(-skull_size // 2, skull_size // 2)
            crack_start_y = y - skull_size // 2
            crack_end_x = crack_start_x + random.randint(-skull_size // 3, skull_size // 3)
            crack_end_y = y + random.randint(0, skull_size // 2)
            pygame.draw.line(screen, (180, 180, 180), (crack_start_x, crack_start_y), (crack_end_x, crack_end_y), 1)

        # Deep eye sockets with swirling energy
        eye_size = max(5, skull_size // 3)
        for eye_x in [x - skull_size // 3, x + skull_size // 3]:
            # Dark socket
            pygame.draw.circle(screen, BLACK, (eye_x, y - skull_size // 4), eye_size)
            # Swirling ghostly energy
            for swirl in range(3):
                swirl_angle = self.animation_time * 4 + swirl * 2
                swirl_x = eye_x + math.cos(swirl_angle) * eye_size // 2
                swirl_y = y - skull_size // 4 + math.sin(swirl_angle) * eye_size // 2
                pygame.draw.circle(screen, self.color_scheme["eyes"], (int(swirl_x), int(swirl_y)), max(2, eye_size // 4))
            # Central glow
            pygame.draw.circle(screen, (100, 255, 255), (eye_x, y - skull_size // 4), max(1, eye_size // 6))

        # Nasal cavity
        nose_points = [
            (x, y - skull_size // 8),
            (x - skull_size // 8, y + skull_size // 8),
            (x + skull_size // 8, y + skull_size // 8),
        ]
        pygame.draw.polygon(screen, BLACK, nose_points)

        # Broken jaw with missing teeth
        jaw_points = [
            (x - skull_size // 2, y + skull_size // 4),
            (x - skull_size // 4, y + skull_size // 2),
            (x + skull_size // 4, y + skull_size // 2),
            (x + skull_size // 2, y + skull_size // 4),
        ]
        pygame.draw.polygon(screen, body_color, jaw_points)

        # Uneven teeth (some missing)
        teeth_positions = [-2, -1, 1, 2]  # Missing center tooth
        for i in teeth_positions:
            if random.random() < 0.8:  # 20% chance tooth is missing
                tooth_x = x + i * (skull_size // 5)
                tooth_height = random.randint(skull_size // 10, skull_size // 6)
                pygame.draw.polygon(
                    screen,
                    (255, 255, 230),
                    [
                        (tooth_x - 2, y + skull_size // 4),
                        (tooth_x, y + skull_size // 4 + tooth_height),
                        (tooth_x + 2, y + skull_size // 4),
                    ],
                )

        # Ectoplasmic wisps
        for wisp in range(2):
            wisp_angle = self.animation_time * 3 + wisp * math.pi
            wisp_x = x + math.cos(wisp_angle) * skull_size
            wisp_y = y + math.sin(wisp_angle) * skull_size // 2
            wisp_size = random.randint(3, 6)
            pygame.draw.circle(screen, (200, 200, 255), (int(wisp_x), int(wisp_y)), wisp_size, 1)

    def _draw_giant(self, screen: pygame.Surface, x: int, y: int, size: int, body_color: tuple):
        """Draw massive armored giant with battle scars"""
        # Massive armored body
        body_width = size
        body_height = int(size * 1.5)
        body_rect = pygame.Rect(x - body_width // 2, y - body_height // 2, body_width, body_height)
        pygame.draw.rect(screen, body_color, body_rect, border_radius=size // 8)

        # Armor plates
        for plate_y in range(3):
            plate_rect = pygame.Rect(
                x - body_width // 3, y - body_height // 2 + plate_y * body_height // 3, body_width * 2 // 3, body_height // 4
            )
            pygame.draw.rect(screen, (60, 30, 90), plate_rect, border_radius=size // 16)
            pygame.draw.rect(screen, (40, 20, 60), plate_rect, 2, border_radius=size // 16)
            # Battle damage on armor
            for _ in range(2):
                scratch_x = plate_rect.x + random.randint(0, plate_rect.width)
                scratch_y = plate_rect.y + random.randint(0, plate_rect.height)
                pygame.draw.line(
                    screen, (30, 15, 45), (scratch_x, scratch_y), (scratch_x + size // 10, scratch_y + size // 15), 1
                )

        # Scarred head with war paint
        head_size = size // 2
        head_y = y - body_height // 2 - head_size // 3
        pygame.draw.circle(screen, body_color, (x, head_y), head_size)

        # War paint stripes
        for stripe in range(3):
            stripe_y = head_y - head_size // 3 + stripe * head_size // 3
            pygame.draw.line(
                screen, (180, 0, 0), (x - head_size // 2, stripe_y), (x + head_size // 2, stripe_y), max(2, size // 30)
            )

        # Battle scar across face
        pygame.draw.line(
            screen,
            (150, 100, 100),
            (x - head_size // 3, head_y - head_size // 4),
            (x + head_size // 4, head_y + head_size // 3),
            max(2, size // 25),
        )

        # Glowing angry eyes with pulsing yellow
        base_eye_size = max(5, size // 8)
        eye_y = head_y
        # Pulsing effect for yellow center (slower)
        pulse = (math.sin(self.animation_time * 1.5) + 1) / 2  # 0 to 1, slower pulse

        for eye_x in [x - head_size // 3, x + head_size // 3]:
            # Outer glow
            for glow in range(3):
                glow_size = base_eye_size + glow * 2
                # glow_alpha = 80 - glow * 25
                pygame.draw.circle(screen, (255, 128, 0), (eye_x, eye_y), glow_size, 1)
            # Main eye
            pygame.draw.circle(screen, self.color_scheme["eyes"], (eye_x, eye_y), base_eye_size)
            # Pulsing yellow pupil (grows and shrinks)
            pupil_size = max(2, int(base_eye_size // 3 + pulse * base_eye_size // 3))
            pygame.draw.circle(screen, (255, 255, 0), (eye_x, eye_y), pupil_size)

        # Roaring mouth with tusks
        mouth_y = head_y + head_size // 3
        mouth_rect = pygame.Rect(x - head_size // 2, mouth_y - head_size // 6, head_size, head_size // 3)
        pygame.draw.ellipse(screen, (20, 20, 20), mouth_rect)
        # Tusks (starting inside mouth)
        for tusk_x in [x - head_size // 3, x + head_size // 3]:
            pygame.draw.polygon(
                screen,
                (255, 255, 200),
                [
                    (tusk_x, mouth_y + size // 20),  # Start inside mouth
                    (tusk_x - size // 15, mouth_y - size // 15),  # End point slightly lower
                    (tusk_x + size // 15, mouth_y - size // 15),
                ],
            )

        # Massive spiked arms
        arm_width = max(6, size // 8)
        for arm_side in [-1, 1]:
            arm_start_x = x + arm_side * body_width // 2
            arm_end_x = x + arm_side * body_width
            arm_end_y = y + body_height // 4

            # Main arm
            pygame.draw.line(screen, body_color, (arm_start_x, y - body_height // 4), (arm_end_x, arm_end_y), arm_width)

            # Arm spikes
            for spike in range(2):
                spike_pos = 0.3 + spike * 0.3
                spike_x = arm_start_x + (arm_end_x - arm_start_x) * spike_pos
                spike_y = y - body_height // 4 + (arm_end_y - (y - body_height // 4)) * spike_pos
                pygame.draw.polygon(
                    screen,
                    (100, 50, 150),
                    [
                        (spike_x, spike_y),
                        (spike_x + arm_side * size // 10, spike_y - size // 8),
                        (spike_x + arm_side * size // 15, spike_y + size // 20),
                    ],
                )

            # Clawed hand
            for claw in range(3):
                claw_angle = arm_side * 0.3 + (claw - 1) * 0.2
                claw_x = arm_end_x + math.cos(claw_angle) * size // 8
                claw_y = arm_end_y + math.sin(claw_angle) * size // 8
                pygame.draw.line(screen, (200, 200, 200), (arm_end_x, arm_end_y), (claw_x, claw_y), max(2, size // 30))

        # Shoulder spikes (positioned at body edges)
        spike_size = size // 4
        spike_positions = [
            (x - body_width // 2, -1),  # Left spike at body edge
            (x + body_width // 2, 1),  # Right spike at body edge
        ]
        for spike_base_x, side in spike_positions:
            # Multiple spikes
            for spike_num in range(2):
                spike_offset = spike_num * size // 8
                spike_x = spike_base_x + spike_offset * side
                pygame.draw.polygon(
                    screen,
                    (120, 60, 180),
                    [
                        (spike_x, y - body_height // 2),
                        (spike_x - spike_size // 3, y - body_height // 2 - spike_size),
                        (spike_x + spike_size // 3, y - body_height // 2 - spike_size),
                    ],
                )
                # Spike highlight
                pygame.draw.line(
                    screen,
                    (150, 80, 200),
                    (spike_x, y - body_height // 2),
                    (spike_x, y - body_height // 2 - spike_size),
                    max(1, size // 40),
                )

        # Ground crack effect under giant
        if random.random() < 0.3:
            crack_y = y + body_height // 2
            for crack in range(2):
                crack_x = x + random.randint(-body_width // 2, body_width // 2)
                pygame.draw.line(
                    screen,
                    (50, 50, 50),
                    (crack_x, crack_y),
                    (crack_x + random.randint(-size // 4, size // 4), crack_y + size // 6),
                    max(1, size // 30),
                )

        # New special effect: Electric sparks on random body parts
        if random.random() < 0.4:
            # Choose random start and end points on the giant's body
            # Possible positions: shoulders, arms, chest, head
            body_positions = [
                (x - body_width // 2, y - body_height // 2),  # Left shoulder
                (x + body_width // 2, y - body_height // 2),  # Right shoulder
                (x - body_width // 2, y),  # Left side
                (x + body_width // 2, y),  # Right side
                (x, y - body_height // 2),  # Top center
                (x, y + body_height // 2),  # Bottom center
                (x - body_width, y + body_height // 4),  # Left arm end
                (x + body_width, y + body_height // 4),  # Right arm end
            ]

            # Pick two random positions
            start_pos = random.choice(body_positions)
            end_pos = random.choice([p for p in body_positions if p != start_pos])

            spark_start_x, spark_start_y = start_pos
            spark_end_x, spark_end_y = end_pos

            # Create jagged lightning path
            points = [(spark_start_x, spark_start_y)]
            for i in range(2 + random.randint(0, 2)):  # Variable number of segments
                progress = (i + 1) / (3.0)
                mid_x = spark_start_x + (spark_end_x - spark_start_x) * progress
                mid_y = spark_start_y + (spark_end_y - spark_start_y) * progress
                # Add random offset for jaggedness
                mid_x += random.randint(-size // 15, size // 15)
                mid_y += random.randint(-size // 15, size // 15)
                points.append((mid_x, mid_y))
            points.append((spark_end_x, spark_end_y))

            # Draw lightning
            for i in range(len(points) - 1):
                pygame.draw.line(screen, (200, 150, 255), points[i], points[i + 1], max(2, size // 40))
                pygame.draw.line(screen, (255, 255, 255), points[i], points[i + 1], max(1, size // 60))

    def _draw_health_bar(self, screen: pygame.Surface, x: int, y: int, width: int):
        """Draw health bar above enemy"""
        bar_height = 4
        bar_width = width

        # Background
        pygame.draw.rect(screen, (50, 50, 50), (x - bar_width // 2, y, bar_width, bar_height))

        # Health
        health_percent = self.health / self.max_health
        health_color = (255, 0, 0) if health_percent < 0.3 else (255, 255, 0) if health_percent < 0.6 else (0, 255, 0)
        pygame.draw.rect(screen, health_color, (x - bar_width // 2, y, int(bar_width * health_percent), bar_height))

    def get_hitbox(self, screen_width: int, screen_height: int) -> pygame.Rect:
        """Get hitbox for collision detection"""
        x, y = self.get_screen_position(screen_width, screen_height)
        size = self.get_size()

        # Adjust hitbox based on enemy type since they have different shapes
        if self.enemy_type == "zombie":
            # Zombie: body rect is from (y-size/2) to (y+size/2), head is at (y-size/2-head_size/2)
            # Head size is size/3, so head top is at y - size/2 - size/3
            hitbox_width = int(size * 0.75)
            hitbox_height = int(size * 1.33)  # Body (size) + head (size/3)
            # Start from top of head
            hitbox_y = y - size // 2 - size // 3
        elif self.enemy_type == "demon":
            # Demon: triangular body from (y-size/2) with horns above
            hitbox_width = int(size * 1.0)
            hitbox_height = int(size * 1.2)  # Include horns
            hitbox_y = y - int(size * 0.75)  # Start from horn tips
        elif self.enemy_type == "skull":
            # Skull: circular head centered at y
            hitbox_width = int(size)
            hitbox_height = int(size)
            hitbox_y = y - size // 2
        elif self.enemy_type == "giant":
            # Giant: massive body from (y-body_height/2) with head above
            body_height = int(size * 1.5)
            head_size = size // 2
            hitbox_width = int(size)
            hitbox_height = body_height + head_size // 2
            hitbox_y = y - body_height // 2 - head_size // 2
        else:
            # Default fallback
            hitbox_width = int(size * 0.9)
            hitbox_height = int(size * 1.3)
            hitbox_y = y - int(size * 0.8)

        return pygame.Rect(x - hitbox_width // 2, hitbox_y, hitbox_width, hitbox_height)


class EnemyManager:
    """Manages enemy spawning and waves"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.enemies: List[Enemy] = []
        self.wave_number = 1
        self.enemies_spawned_this_wave = 0
        self.enemies_per_wave = 5
        self.time_between_spawns = 2.5
        self.last_spawn_time = 0
        self.wave_complete = False
        self.wave_complete_time = 0

        # Difficulty scaling
        self.difficulty_multiplier = 1.0

        # Player stats
        self.total_kills = 0
        self.current_combo = 0
        self.combo_timer = 0
        self.max_combo_time = 2.0

    def update(self, dt: float, current_time: float) -> Tuple[int, int]:
        """Update all enemies, returns (damage_to_player, enemies_killed)"""
        total_damage = 0
        enemies_killed = 0

        # Update combo timer
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.current_combo = 0

        # Update enemies
        for enemy in self.enemies[:]:
            damage = enemy.update(dt, 100)  # TODO: pass actual player health
            if damage:
                total_damage += damage

            # Remove dead enemies after animation but keep their blood
            if not enemy.alive and enemy.death_animation_progress >= 1.0:
                # Keep blood particles alive even after enemy is removed
                if enemy.blood_particles:
                    # Transfer blood particles to a persistent list if needed
                    pass  # Blood particles stay with enemy for now

                # Only remove enemy if blood is also done
                if not enemy.blood_particles or all(p.lifetime <= 0 for p in enemy.blood_particles):
                    self.enemies.remove(enemy)
                    enemies_killed += 1

        # Check wave completion
        if self.enemies_spawned_this_wave >= self.enemies_per_wave and len(self.enemies) == 0 and not self.wave_complete:
            self.wave_complete = True
            self.wave_complete_time = current_time

        # Start next wave after delay
        if self.wave_complete and current_time - self.wave_complete_time > 3.0:
            self.start_next_wave()

        # Spawn new enemies
        if (
            not self.wave_complete
            and self.enemies_spawned_this_wave < self.enemies_per_wave
            and current_time - self.last_spawn_time > self.time_between_spawns
        ):
            self.spawn_enemy()
            self.last_spawn_time = current_time

        return total_damage, enemies_killed

    def spawn_enemy(self):
        """Spawn a new enemy"""
        # Random spawn position but keep within screen bounds
        # Reduced range to ensure enemies stay visible
        spawn_x = random.choice([-0.6, -0.3, 0, 0.3, 0.6])
        spawn_z = 1.0  # Start far away

        # Choose enemy type based on wave
        enemy_types = ["zombie"]
        if self.wave_number >= 3:
            enemy_types.append("skull")
        if self.wave_number >= 5:
            enemy_types.append("demon")
        if self.wave_number >= 7:
            # Stage 4 - more giants and mixed enemy types
            enemy_types.extend(["demon", "skull"])  # More variety
            if random.random() < 0.2:  # 20% chance of giants
                enemy_types.append("giant")

        enemy_type = random.choice(enemy_types)

        enemy = Enemy(spawn_x, spawn_z, enemy_type)

        # Apply difficulty scaling (reduced scaling for better balance)
        enemy.health = int(enemy.health * self.difficulty_multiplier)
        enemy.max_health = enemy.health
        enemy.speed *= 1 + (self.wave_number - 1) * 0.05  # Reduced from 0.1 to 0.05

        self.enemies.append(enemy)
        self.enemies_spawned_this_wave += 1

    def start_next_wave(self):
        """Start the next wave"""
        self.wave_number += 1
        self.wave_complete = False
        self.enemies_spawned_this_wave = 0
        self.enemies_per_wave = 5 + self.wave_number * 2
        self.time_between_spawns = max(1.5, 3.0 - self.wave_number * 0.15)  # Slower spawn rate
        self.difficulty_multiplier = 1.0 + (self.wave_number - 1) * 0.10  # Reduced from 0.15

    def check_hit(self, x: int, y: int, damage: int = 10) -> Tuple[int, bool]:
        """Check if shot hit an enemy, returns (score_gained, killed)"""
        # Sort enemies by z (closest first) for proper hit detection
        sorted_enemies = sorted(self.enemies, key=lambda e: e.z)

        for enemy in sorted_enemies:
            if enemy.alive:
                hitbox = enemy.get_hitbox(self.screen_width, self.screen_height)
                if hitbox.collidepoint(x, y):
                    # Apply knockback if enemy is very close
                    apply_knockback = enemy.z < 0.25
                    # Pass hit position for blood effects
                    killed = enemy.take_damage(damage, knockback=apply_knockback, hit_pos=(x, y))
                    if killed:
                        # Increment combo and kills HERE when enemy is actually killed
                        self.total_kills += 1
                        self.current_combo += 1
                        self.combo_timer = self.max_combo_time

                        # Calculate score with combo multiplier
                        base_score = enemy.score_value
                        combo_bonus = min(self.current_combo - 1, 10) * 10  # -1 because we just incremented
                        return base_score + combo_bonus, True
                    return 10, False  # Hit but not killed

        return 0, False

    def draw(self, screen: pygame.Surface, debug_hitbox: bool = False, dt: float = 0.016):
        """Draw all enemies with proper depth sorting"""
        # Sort enemies by z (far to near) for proper rendering
        sorted_enemies = sorted(self.enemies, key=lambda e: e.z, reverse=True)

        # Draw blood particles behind enemies
        for enemy in self.enemies:
            enemy.update_and_draw_blood(screen, dt)

        # Draw enemies on top of blood
        for enemy in sorted_enemies:
            enemy.draw(screen, self.screen_width, self.screen_height, debug_hitbox)

    def get_closest_enemy_distance(self) -> float:
        """Get distance of closest enemy"""
        if not self.enemies:
            return 1.0

        alive_enemies = [enemy.z for enemy in self.enemies if enemy.alive]
        if not alive_enemies:
            return 1.0

        return min(alive_enemies)

    def clear_all_enemies(self):
        """Clear all enemies"""
        self.enemies.clear()
        self.wave_number = 1
        self.enemies_spawned_this_wave = 0
        self.wave_complete = False
        self.total_kills = 0
        self.current_combo = 0
        self.combo_timer = 0
