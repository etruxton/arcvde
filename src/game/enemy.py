"""
Enemy system for arcade-style shooting game with doom-like perspective
"""

import pygame
import math
import random
import time
from typing import List, Tuple, Optional
from utils.constants import *

class BloodParticle:
    """A blood particle with physics and 3D perspective"""
    
    def __init__(self, x: float, y: float, vx: float, vy: float, size: int, enemy_z: float = 0.5):
        self.x = x
        self.y = y
        self.vx = vx  # Velocity x
        self.vy = vy  # Velocity y
        self.size = size
        self.original_size = size
        self.lifetime = 3.0  # Seconds
        self.age = 0
        self.gravity = 500  # Pixels per second squared
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
            
            # Apply air resistance
            self.vx *= 0.98
            self.vy *= 0.99
            
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
        color = (
            int(200 * brightness),
            int(20 * brightness),
            int(20 * brightness),
            alpha
        )
        
        if self.splattered:
            # Draw as ellipse when splattered on ground with perspective
            # Make ellipse flatter for distant blood
            ellipse_height = max(2, int(self.size * (0.3 + 0.3 * (1 - self.enemy_z))))
            pygame.draw.ellipse(particle_surface, color,
                              (0, self.size - ellipse_height//2, self.size * 2, ellipse_height))
        else:
            # Draw as circle while flying
            pygame.draw.circle(particle_surface, color,
                             (self.size, self.size), self.size)
        
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
        health_map = {
            "zombie": 30,
            "demon": 50,
            "skull": 1,  # Die in one shot
            "giant": 100
        }
        return health_map.get(self.enemy_type, 30)
    
    def _get_speed(self) -> float:
        """Get movement speed based on enemy type"""
        speed_map = {
            "zombie": 0.15,
            "demon": 0.25,
            "skull": 0.35,
            "giant": 0.10
        }
        return speed_map.get(self.enemy_type, 0.15)
    
    def _get_damage(self) -> int:
        """Get damage based on enemy type"""
        damage_map = {
            "zombie": 10,
            "demon": 20,
            "skull": 15,
            "giant": 30
        }
        return damage_map.get(self.enemy_type, 10)
    
    def _get_score_value(self) -> int:
        """Get score value based on enemy type"""
        score_map = {
            "zombie": 100,
            "demon": 200,
            "skull": 150,
            "giant": 500
        }
        return score_map.get(self.enemy_type, 100)
    
    def _get_color_scheme(self) -> dict:
        """Get color scheme based on enemy type"""
        schemes = {
            "zombie": {
                "body": (60, 80, 60),
                "eyes": (255, 0, 0),
                "detail": (40, 60, 40)
            },
            "demon": {
                "body": (150, 30, 30),
                "eyes": (255, 255, 0),
                "detail": (100, 20, 20)
            },
            "skull": {
                "body": (200, 200, 200),
                "eyes": (0, 255, 255),
                "detail": (150, 150, 150)
            },
            "giant": {
                "body": (80, 40, 120),
                "eyes": (255, 128, 0),
                "detail": (60, 30, 90)
            }
        }
        return schemes.get(self.enemy_type, schemes["zombie"])
    
    def _get_base_size(self) -> int:
        """Get base size based on enemy type"""
        size_map = {
            "zombie": 80,
            "demon": 90,
            "skull": 60,
            "giant": 120
        }
        return size_map.get(self.enemy_type, 80)
    
    def update(self, dt: float, player_health: int) -> Optional[int]:
        """Update enemy state, returns damage if attacking"""
        if not self.alive:
            # Update death animation
            if self.death_animation_progress < 1.0:
                self.death_animation_progress = min(1.0, 
                    (time.time() - self.death_time) / 0.5)
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
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(100, 300) if self.health > 0 else random.uniform(200, 500)
                
                # Scale speed based on distance for perspective
                perspective_scale = 1.0 / (self.z + 0.3)
                speed = speed * perspective_scale * 0.7
                
                particle = BloodParticle(
                    x=hit_pos[0],
                    y=hit_pos[1],
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed - 100,  # Negative for upward burst
                    size=random.randint(3, 8) if self.health > 0 else random.randint(4, 10),
                    enemy_z=self.z  # Pass enemy's distance for perspective
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
        """Draw zombie enemy"""
        # Body
        body_rect = pygame.Rect(x - size//3, y - size//2, size*2//3, size)
        pygame.draw.rect(screen, body_color, body_rect)
        pygame.draw.rect(screen, self.color_scheme["detail"], body_rect, 2)
        
        # Head
        head_size = size // 3
        pygame.draw.circle(screen, body_color, (x, y - size//2 - head_size//2), head_size)
        
        # Eyes (glowing red)
        eye_size = max(2, size // 15)
        eye_y = y - size//2 - head_size//2
        pygame.draw.circle(screen, self.color_scheme["eyes"], (x - head_size//3, eye_y), eye_size)
        pygame.draw.circle(screen, self.color_scheme["eyes"], (x + head_size//3, eye_y), eye_size)
        
        # Arms (outstretched)
        arm_angle = math.sin(self.animation_time) * 0.2
        pygame.draw.line(screen, body_color, 
                        (x - size//3, y - size//4),
                        (x - size//2 - size//4 * math.cos(arm_angle), 
                         y - size//4 + size//4 * math.sin(arm_angle)), 
                        max(2, size//20))
        pygame.draw.line(screen, body_color,
                        (x + size//3, y - size//4),
                        (x + size//2 + size//4 * math.cos(-arm_angle),
                         y - size//4 + size//4 * math.sin(-arm_angle)),
                        max(2, size//20))
    
    def _draw_demon(self, screen: pygame.Surface, x: int, y: int, size: int, body_color: tuple):
        """Draw demon enemy"""
        # Body (triangular/demonic shape)
        body_points = [
            (x, y - size//2),
            (x - size//2, y + size//3),
            (x + size//2, y + size//3)
        ]
        pygame.draw.polygon(screen, body_color, body_points)
        pygame.draw.polygon(screen, self.color_scheme["detail"], body_points, 2)
        
        # Horns
        horn_size = size // 4
        pygame.draw.polygon(screen, (200, 50, 50), [
            (x - size//4, y - size//2),
            (x - size//3, y - size//2 - horn_size),
            (x - size//5, y - size//2)
        ])
        pygame.draw.polygon(screen, (200, 50, 50), [
            (x + size//4, y - size//2),
            (x + size//3, y - size//2 - horn_size),
            (x + size//5, y - size//2)
        ])
        
        # Eyes (glowing yellow)
        eye_size = max(3, size // 12)
        pygame.draw.circle(screen, self.color_scheme["eyes"], (x - size//5, y - size//3), eye_size)
        pygame.draw.circle(screen, self.color_scheme["eyes"], (x + size//5, y - size//3), eye_size)
        
        # Wings (simplified)
        wing_spread = math.sin(self.animation_time * 2) * 0.3
        pygame.draw.arc(screen, body_color,
                       pygame.Rect(x - size, y - size//2, size, size//2),
                       -math.pi/4 + wing_spread, math.pi/4 + wing_spread, max(2, size//25))
        pygame.draw.arc(screen, body_color,
                       pygame.Rect(x, y - size//2, size, size//2),
                       3*math.pi/4 - wing_spread, 5*math.pi/4 - wing_spread, max(2, size//25))
    
    def _draw_skull(self, screen: pygame.Surface, x: int, y: int, size: int, body_color: tuple):
        """Draw floating skull enemy"""
        # Floating animation
        float_offset = math.sin(self.animation_time * 3) * size * 0.1
        y = int(y + float_offset)
        
        # Skull
        skull_size = size // 2
        pygame.draw.circle(screen, body_color, (x, y), skull_size)
        pygame.draw.circle(screen, self.color_scheme["detail"], (x, y), skull_size, 2)
        
        # Eye sockets (glowing)
        eye_size = max(4, skull_size // 4)
        pygame.draw.circle(screen, BLACK, (x - skull_size//3, y - skull_size//4), eye_size)
        pygame.draw.circle(screen, self.color_scheme["eyes"], 
                          (x - skull_size//3, y - skull_size//4), eye_size//2)
        pygame.draw.circle(screen, BLACK, (x + skull_size//3, y - skull_size//4), eye_size)
        pygame.draw.circle(screen, self.color_scheme["eyes"],
                          (x + skull_size//3, y - skull_size//4), eye_size//2)
        
        # Jaw
        jaw_points = [
            (x - skull_size//2, y + skull_size//4),
            (x, y + skull_size//2),
            (x + skull_size//2, y + skull_size//4)
        ]
        pygame.draw.polygon(screen, body_color, jaw_points)
        
        # Teeth
        for i in range(-2, 3):
            tooth_x = x + i * (skull_size // 5)
            pygame.draw.line(screen, self.color_scheme["detail"],
                           (tooth_x, y + skull_size//4),
                           (tooth_x, y + skull_size//3),
                           max(1, size//30))
    
    def _draw_giant(self, screen: pygame.Surface, x: int, y: int, size: int, body_color: tuple):
        """Draw giant enemy"""
        # Massive body
        body_width = size
        body_height = int(size * 1.5)
        body_rect = pygame.Rect(x - body_width//2, y - body_height//2, body_width, body_height)
        pygame.draw.rect(screen, body_color, body_rect, border_radius=size//8)
        pygame.draw.rect(screen, self.color_scheme["detail"], body_rect, 3, border_radius=size//8)
        
        # Head
        head_size = size // 2
        pygame.draw.circle(screen, body_color, (x, y - body_height//2 - head_size//3), head_size)
        
        # Glowing eyes
        eye_size = max(4, size // 10)
        eye_y = y - body_height//2 - head_size//3
        pygame.draw.circle(screen, self.color_scheme["eyes"], (x - head_size//3, eye_y), eye_size)
        pygame.draw.circle(screen, self.color_scheme["eyes"], (x + head_size//3, eye_y), eye_size)
        
        # Massive arms
        arm_width = max(4, size // 10)
        pygame.draw.line(screen, body_color,
                        (x - body_width//2, y - body_height//4),
                        (x - body_width, y + body_height//4),
                        arm_width)
        pygame.draw.line(screen, body_color,
                        (x + body_width//2, y - body_height//4),
                        (x + body_width, y + body_height//4),
                        arm_width)
        
        # Spikes on shoulders
        spike_size = size // 6
        for spike_x in [x - body_width//2, x + body_width//2]:
            pygame.draw.polygon(screen, self.color_scheme["detail"], [
                (spike_x, y - body_height//2),
                (spike_x - spike_size//2, y - body_height//2 - spike_size),
                (spike_x + spike_size//2, y - body_height//2 - spike_size)
            ])
    
    def _draw_health_bar(self, screen: pygame.Surface, x: int, y: int, width: int):
        """Draw health bar above enemy"""
        bar_height = 4
        bar_width = width
        
        # Background
        pygame.draw.rect(screen, (50, 50, 50), 
                        (x - bar_width//2, y, bar_width, bar_height))
        
        # Health
        health_percent = self.health / self.max_health
        health_color = (255, 0, 0) if health_percent < 0.3 else (255, 255, 0) if health_percent < 0.6 else (0, 255, 0)
        pygame.draw.rect(screen, health_color,
                        (x - bar_width//2, y, int(bar_width * health_percent), bar_height))
    
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
            hitbox_y = y - size//2 - size//3
        elif self.enemy_type == "demon":
            # Demon: triangular body from (y-size/2) with horns above
            hitbox_width = int(size * 1.0)
            hitbox_height = int(size * 1.2)  # Include horns
            hitbox_y = y - int(size * 0.75)  # Start from horn tips
        elif self.enemy_type == "skull":
            # Skull: circular head centered at y
            hitbox_width = int(size)
            hitbox_height = int(size)
            hitbox_y = y - size//2
        elif self.enemy_type == "giant":
            # Giant: massive body from (y-body_height/2) with head above
            body_height = int(size * 1.5)
            head_size = size // 2
            hitbox_width = int(size)
            hitbox_height = body_height + head_size//2
            hitbox_y = y - body_height//2 - head_size//2
        else:
            # Default fallback
            hitbox_width = int(size * 0.9)
            hitbox_height = int(size * 1.3)
            hitbox_y = y - int(size * 0.8)
        
        return pygame.Rect(x - hitbox_width//2, hitbox_y, hitbox_width, hitbox_height)


class EnemyManager:
    """Manages enemy spawning and waves"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        self.enemies: List[Enemy] = []
        self.wave_number = 1
        self.enemies_spawned_this_wave = 0
        self.enemies_per_wave = 5
        self.time_between_spawns = 3.0
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
        if (self.enemies_spawned_this_wave >= self.enemies_per_wave and 
            len(self.enemies) == 0 and not self.wave_complete):
            self.wave_complete = True
            self.wave_complete_time = current_time
        
        # Start next wave after delay
        if self.wave_complete and current_time - self.wave_complete_time > 3.0:
            self.start_next_wave()
        
        # Spawn new enemies
        if (not self.wave_complete and 
            self.enemies_spawned_this_wave < self.enemies_per_wave and
            current_time - self.last_spawn_time > self.time_between_spawns):
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
        if self.wave_number >= 7 and random.random() < 0.2:
            enemy_types.append("giant")
        
        enemy_type = random.choice(enemy_types)
        
        enemy = Enemy(spawn_x, spawn_z, enemy_type)
        
        # Apply difficulty scaling
        enemy.health = int(enemy.health * self.difficulty_multiplier)
        enemy.max_health = enemy.health
        enemy.speed *= (1 + (self.wave_number - 1) * 0.1)
        
        self.enemies.append(enemy)
        self.enemies_spawned_this_wave += 1
    
    def start_next_wave(self):
        """Start the next wave"""
        self.wave_number += 1
        self.wave_complete = False
        self.enemies_spawned_this_wave = 0
        self.enemies_per_wave = 5 + self.wave_number * 2
        self.time_between_spawns = max(1.0, 3.0 - self.wave_number * 0.2)
        self.difficulty_multiplier = 1.0 + (self.wave_number - 1) * 0.15
    
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