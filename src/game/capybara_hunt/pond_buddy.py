# Standard library imports
import math
import random
from typing import Optional

# Third-party imports
import pygame

WHITE = (255, 255, 255)


class PondBuddy:
    """
    Pond buddy character that reacts to game events with moods and speech.
    Provides visual feedback and commentary during the capybara hunt game.
    """

    def __init__(self, x: int, y: int):
        """Initialize the pond buddy at given position"""
        self.x = x
        self.y = y
        self.mood = "neutral"
        self.mood_timer = 0.0
        self.mood_duration = 2.0
        self.mood_priority = 0
        self.bob_offset = 0.0
        self.bob_time = 0.0
        self.last_hit_streak = 0
        self.last_miss_streak = 0
        self.animation_frame = 0
        self.animation_timer = 0.0
        self.sprite: Optional[pygame.Surface] = None
        self.speech_text = ""
        self.speech_timer = 0.0
        self.speech_index = 0
        self.snarky_index = 0
        self.encouraging_index = 0

        self._load_sprite()

    def _load_sprite(self):
        """Load the pond buddy sprite"""
        try:
            self.sprite = pygame.image.load("assets/pond_buddy.png").convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (100, 100))
        except Exception as e:
            print(f"Could not load pond buddy sprite: {e}")
            self.sprite = None

    def set_mood(self, mood: str, duration: float = 2.0, priority: int = 1):
        """Set the pond buddy's mood with priority system
        Priority levels:
        0 = neutral/default (lowest)
        1 = normal reactions (happy, sad, worried, etc.)
        2 = special reactions (excited, laughing, disappointed)
        3 = round completion reactions (celebration, relieved, proud)
        """
        if priority >= self.mood_priority or self.mood_timer <= 0:
            self.mood = mood
            self.mood_timer = duration
            self.mood_priority = priority
            self.animation_frame = 0
            if mood == "laughing":
                self._set_speech(duration, "snarky")

    def _set_speech(self, duration: float, speech_type: str = "snarky"):
        """Set speech text for the pond buddy"""
        if speech_type == "snarky":
            speech_options = [
                "Haha! Try again!",
                "Oops! That was close!",
                "Nice aim... NOT!",
                "Maybe try glasses?",
                "Balloons: 1, You: 0",
                "Better luck next time!",
                "That was... interesting!",
                "So close, yet so far!",
                "Swing and a miss!",
                "Whoosh! Right past it!",
            ]
            # Cycle through different speeches each time
            self.speech_text = speech_options[self.snarky_index]
            self.snarky_index = (self.snarky_index + 1) % len(speech_options)
        else:  # encouraging
            speech_options = [
                "Nice shot!",
                "Great aim!",
                "You're getting good!",
                "Balloon defeated!",
                "Balloons: 0, You: 1!",
                "Keep it up!",
                "Bullseye!",
                "Viva la Capybara!",
                "You're on fire!",
                "Cap-tastic!",
            ]
            self.speech_text = speech_options[self.encouraging_index]
            self.encouraging_index = (self.encouraging_index + 1) % len(speech_options)

        self.speech_timer = duration

    def update(self, dt: float):
        """Update pond buddy animations and mood"""
        # Update mood timer
        if self.mood_timer > 0:
            self.mood_timer -= dt
            if self.mood_timer <= 0:
                self.mood = "neutral"
                self.mood_priority = 0
                self.last_hit_streak = 0
                self.last_miss_streak = 0

        # Update speech timer
        if self.speech_timer > 0:
            self.speech_timer -= dt
            if self.speech_timer <= 0:
                self.speech_text = ""

        # Random idle reactions when neutral
        if self.mood == "neutral" and random.random() < 0.01:
            idle_moods = ["surprised", "happy"]
            self.set_mood(random.choice(idle_moods), random.uniform(0.5, 1.5))

        # Bobbing animation
        self.bob_time += dt
        self.bob_offset = math.sin(self.bob_time * 2) * 3

        # Animation frame update for expressions
        self.animation_timer += dt
        if self.animation_timer > 0.2:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 2

    def on_capybara_hit(self):
        """Called when player successfully hits a capybara"""
        self.last_hit_streak += 1
        self.last_miss_streak = 0

        # 1/5 chance to give encouraging speech for any balloon hit
        if random.random() < 1 / 5:
            self.set_mood("laughing", 2.5)
            self._set_speech(2.5, "encouraging")
        elif self.last_hit_streak >= 5:
            self.set_mood("celebration", 3.5, 2)
        elif self.last_hit_streak >= 3:
            self.set_mood("excited", 3.0, 2)
        elif self.last_hit_streak == 1:
            self.set_mood("happy", 1.5, 1)

    def on_capybara_miss(self):
        """Called when player shoots capybara instead of balloon"""
        self.last_miss_streak += 1
        self.last_hit_streak = 0

        # 1/3 chance to laugh with snarky speech on any miss
        if random.random() < 1 / 3:
            self.set_mood("laughing", 2.5)
        elif self.last_miss_streak >= 3:
            self.set_mood("disappointed", 2.0, 2)
        else:
            self.set_mood("sad", 1.5, 1)

    def on_capybara_escape(self):
        """Called when a capybara escapes (flies away)"""
        self.set_mood("worried", 1.5, 1)

    def draw(self, screen: pygame.Surface):
        """Draw the pond buddy"""
        x = self.x
        y = self.y + self.bob_offset
        mood = self.mood

        # Draw the pond buddy sprite if loaded
        if self.sprite:
            sprite_rect = self.sprite.get_rect()
            sprite_rect.center = (int(x), int(y))
            screen.blit(self.sprite, sprite_rect)

            # Draw facial expressions on top of the sprite
            face_x = x + 2
            face_y = y - 20

            self._draw_expressions(screen, mood, face_x, face_y)
        else:
            # Fallback if no sprite is loaded - draw simple circle buddy
            body_color = (101, 67, 33)  # Brown
            pygame.draw.circle(screen, body_color, (int(x), int(y)), 25)
            pygame.draw.circle(screen, (139, 90, 43), (int(x), int(y)), 25, 3)  # Border
            # Simple neutral face
            pygame.draw.circle(screen, (0, 0, 0), (int(x - 8), int(y - 5)), 3)
            pygame.draw.circle(screen, (0, 0, 0), (int(x + 8), int(y - 5)), 3)

        # Draw speech bubble if buddy is talking
        self._draw_speech_bubble(screen)

    def _draw_expressions(self, screen: pygame.Surface, mood: str, face_x: float, face_y: float):
        """Draw facial expressions based on mood"""
        eye_color = (0, 0, 0)

        if mood == "neutral":
            # Normal eyes - farther apart (scaled for larger sprite)
            pygame.draw.circle(screen, eye_color, (int(face_x - 15), int(face_y)), 5)
            pygame.draw.circle(screen, eye_color, (int(face_x + 15), int(face_y)), 5)

        elif mood == "happy":
            # Happy eyes (curved) - draw multiple passes to fill gaps
            left_eye_rect = (int(face_x - 20), int(face_y - 3), 12, 12)
            right_eye_rect = (int(face_x + 8), int(face_y - 3), 12, 12)
            pygame.draw.arc(screen, eye_color, left_eye_rect, 0, math.pi, 3)
            pygame.draw.arc(
                screen,
                eye_color,
                (left_eye_rect[0], left_eye_rect[1] + 1, left_eye_rect[2], left_eye_rect[3]),
                0,
                math.pi,
                3,
            )
            pygame.draw.arc(screen, eye_color, right_eye_rect, 0, math.pi, 3)
            pygame.draw.arc(
                screen,
                eye_color,
                (right_eye_rect[0], right_eye_rect[1] + 1, right_eye_rect[2], right_eye_rect[3]),
                0,
                math.pi,
                3,
            )
            # Smile (upward curve) - draw multiple passes to fill gaps
            rect = (int(face_x - 14), int(face_y + 7), 28, 16)
            pygame.draw.arc(screen, eye_color, rect, math.pi, 2 * math.pi, 2)
            # Draw again with slight offset to fill gaps
            pygame.draw.arc(screen, eye_color, (rect[0], rect[1] - 1, rect[2], rect[3]), math.pi, 2 * math.pi, 2)

        elif mood == "sad":
            # Sad eyes (small) - scaled up
            pygame.draw.circle(screen, eye_color, (int(face_x - 15), int(face_y)), 3)
            pygame.draw.circle(screen, eye_color, (int(face_x + 15), int(face_y)), 3)
            # Frown (downward curve) - draw multiple passes to fill gaps
            rect = (int(face_x - 14), int(face_y + 18), 28, 14)
            pygame.draw.arc(screen, eye_color, rect, 0, math.pi, 3)
            # Draw again with slight offset to fill gaps
            pygame.draw.arc(screen, eye_color, (rect[0], rect[1] + 1, rect[2], rect[3]), 0, math.pi, 3)

        elif mood == "excited":
            # Star eyes
            frame = self.animation_frame
            if frame == 0:
                # Wide eyes - scaled up
                pygame.draw.circle(screen, eye_color, (int(face_x - 15), int(face_y)), 6)
                pygame.draw.circle(screen, eye_color, (int(face_x + 15), int(face_y)), 6)
                pygame.draw.circle(screen, WHITE, (int(face_x - 13), int(face_y - 2)), 3)
                pygame.draw.circle(screen, WHITE, (int(face_x + 17), int(face_y - 2)), 3)
            else:
                # Sparkle effect - scaled up
                pygame.draw.circle(screen, (255, 215, 0), (int(face_x - 15), int(face_y)), 5)
                pygame.draw.circle(screen, (255, 215, 0), (int(face_x + 15), int(face_y)), 5)
            # Big smile - draw multiple passes to fill gaps
            rect = (int(face_x - 18), int(face_y + 7), 36, 20)
            pygame.draw.arc(screen, eye_color, rect, math.pi, 2 * math.pi, 2)
            # Draw again with slight offset to fill gaps
            pygame.draw.arc(screen, eye_color, (rect[0], rect[1] - 1, rect[2], rect[3]), math.pi, 2 * math.pi, 2)

        elif mood == "laughing":
            # Closed eyes (laughing) - draw multiple passes to fill gaps
            left_eye_rect = (int(face_x - 20), int(face_y), 12, 6)
            right_eye_rect = (int(face_x + 8), int(face_y), 12, 6)
            pygame.draw.arc(screen, eye_color, left_eye_rect, math.pi, 2 * math.pi, 2)
            pygame.draw.arc(
                screen,
                eye_color,
                (left_eye_rect[0], left_eye_rect[1] - 1, left_eye_rect[2], left_eye_rect[3]),
                math.pi,
                2 * math.pi,
                2,
            )
            pygame.draw.arc(screen, eye_color, right_eye_rect, math.pi, 2 * math.pi, 2)
            pygame.draw.arc(
                screen,
                eye_color,
                (right_eye_rect[0], right_eye_rect[1] - 1, right_eye_rect[2], right_eye_rect[3]),
                math.pi,
                2 * math.pi,
                2,
            )
            # Wide open mouth - lowered (laughing mouth isn't a smile)
            if self.animation_frame == 0:
                pygame.draw.ellipse(screen, eye_color, (int(face_x - 10), int(face_y + 14), 20, 14))
                pygame.draw.ellipse(screen, (255, 192, 203), (int(face_x - 7), int(face_y + 16), 14, 9))
            else:
                # Draw multiple passes to fill gaps
                rect = (int(face_x - 14), int(face_y + 7), 28, 16)
                pygame.draw.arc(screen, eye_color, rect, math.pi, 2 * math.pi, 2)
                pygame.draw.arc(screen, eye_color, (rect[0], rect[1] - 1, rect[2], rect[3]), math.pi, 2 * math.pi, 2)

        elif mood == "surprised":
            # Wide eyes - scaled up
            pygame.draw.circle(screen, WHITE, (int(face_x - 15), int(face_y)), 8)
            pygame.draw.circle(screen, WHITE, (int(face_x + 15), int(face_y)), 8)
            pygame.draw.circle(screen, eye_color, (int(face_x - 15), int(face_y)), 5)
            pygame.draw.circle(screen, eye_color, (int(face_x + 15), int(face_y)), 5)
            # O mouth - filled black circle - lowered
            pygame.draw.circle(screen, eye_color, (int(face_x), int(face_y + 16)), 7)

        elif mood == "celebration":
            # Jumping animation
            jump_offset = abs(math.sin(self.animation_timer * 10)) * 5
            face_y -= jump_offset
            # Star eyes - scaled up
            for eye_x in [-15, 15]:
                cx = int(face_x + eye_x)
                cy = int(face_y)
                # Draw star shape - scaled up
                pygame.draw.line(screen, (255, 215, 0), (cx - 5, cy), (cx + 5, cy), 3)
                pygame.draw.line(screen, (255, 215, 0), (cx, cy - 5), (cx, cy + 5), 3)
                pygame.draw.line(screen, (255, 215, 0), (cx - 4, cy - 4), (cx + 4, cy + 4), 2)
                pygame.draw.line(screen, (255, 215, 0), (cx - 4, cy + 4), (cx + 4, cy - 4), 2)
            # Huge smile - draw multiple passes to fill gaps
            rect = (int(face_x - 20), int(face_y + 5), 40, 24)
            pygame.draw.arc(screen, eye_color, rect, math.pi, 2 * math.pi, 3)
            # Draw again with slight offset to fill gaps
            pygame.draw.arc(screen, eye_color, (rect[0], rect[1] - 1, rect[2], rect[3]), math.pi, 2 * math.pi, 3)
            # Party hat (triangle on top of head) - scaled up
            hat_color = (255, 20, 147) if self.animation_frame == 0 else (16, 231, 245)
            pygame.draw.polygon(
                screen,
                hat_color,
                [
                    (int(face_x), int(face_y - 40)),
                    (int(face_x - 14), int(face_y - 20)),
                    (int(face_x + 14), int(face_y - 20)),
                ],
            )

        elif mood == "relieved":
            # Half-closed eyes (relief) - draw multiple passes to fill gaps
            left_eye_rect = (int(face_x - 18), int(face_y - 2), 10, 8)
            right_eye_rect = (int(face_x + 8), int(face_y - 2), 10, 8)
            pygame.draw.arc(screen, eye_color, left_eye_rect, math.pi, 2 * math.pi, 3)
            pygame.draw.arc(
                screen,
                eye_color,
                (left_eye_rect[0], left_eye_rect[1] - 1, left_eye_rect[2], left_eye_rect[3]),
                math.pi,
                2 * math.pi,
                3,
            )
            pygame.draw.arc(screen, eye_color, right_eye_rect, math.pi, 2 * math.pi, 3)
            pygame.draw.arc(
                screen,
                eye_color,
                (right_eye_rect[0], right_eye_rect[1] - 1, right_eye_rect[2], right_eye_rect[3]),
                math.pi,
                2 * math.pi,
                3,
            )
            # Slight smile - draw multiple passes to fill gaps
            rect = (int(face_x - 14), int(face_y + 7), 28, 16)
            pygame.draw.arc(screen, eye_color, rect, math.pi, 2 * math.pi, 2)
            pygame.draw.arc(screen, eye_color, (rect[0], rect[1] - 1, rect[2], rect[3]), math.pi, 2 * math.pi, 2)
            # Sweat drop - teardrop shape (rounded cone)
            sweat_color = (100, 180, 255)  # Bright blue
            drop_x = int(face_x + 28)
            drop_y = int(face_y - 14)

            # Draw teardrop shape - combination of circle bottom and triangle top
            # Bottom circle (the rounded part)
            pygame.draw.circle(screen, sweat_color, (drop_x, drop_y), 6)

            # Top triangle/cone that connects smoothly to circle
            # Draw multiple triangles to create smooth transition
            for i in range(6):
                width = 6 - i  # Gradually narrow from circle width to point
                y_offset = i * 2
                pygame.draw.polygon(
                    screen,
                    sweat_color,
                    [
                        (drop_x, drop_y - 6 - y_offset - 2),  # Top point (gets higher)
                        (drop_x - width, drop_y - y_offset),  # Left base
                        (drop_x + width, drop_y - y_offset),  # Right base
                    ],
                )

            # Add white highlight for glossy effect
            pygame.draw.circle(screen, WHITE, (drop_x - 2, drop_y - 2), 2)
            pygame.draw.circle(screen, (200, 230, 255), (drop_x - 1, drop_y - 4), 1)

        elif mood == "proud":
            # Confident eyes - scaled up
            pygame.draw.circle(screen, eye_color, (int(face_x - 15), int(face_y)), 5)
            pygame.draw.circle(screen, eye_color, (int(face_x + 15), int(face_y)), 5)
            pygame.draw.circle(screen, WHITE, (int(face_x - 13), int(face_y - 2)), 2)
            pygame.draw.circle(screen, WHITE, (int(face_x + 17), int(face_y - 2)), 2)
            # Smug smile - draw multiple passes to fill gaps
            rect = (int(face_x - 14), int(face_y + 7), 28, 14)
            pygame.draw.arc(screen, eye_color, rect, math.pi * 1.2, math.pi * 1.8, 3)
            pygame.draw.arc(screen, eye_color, (rect[0], rect[1] - 1, rect[2], rect[3]), math.pi * 1.2, math.pi * 1.8, 3)
            # Raised eyebrow effect - draw multiple passes to fill gaps
            left_brow_rect = (int(face_x - 20), int(face_y - 7), 14, 7)
            right_brow_rect = (int(face_x + 6), int(face_y - 7), 14, 7)
            pygame.draw.arc(screen, eye_color, left_brow_rect, 0, math.pi, 2)
            pygame.draw.arc(
                screen,
                eye_color,
                (left_brow_rect[0], left_brow_rect[1] + 1, left_brow_rect[2], left_brow_rect[3]),
                0,
                math.pi,
                3,
            )
            pygame.draw.arc(screen, eye_color, right_brow_rect, 0, math.pi, 2)
            pygame.draw.arc(
                screen,
                eye_color,
                (right_brow_rect[0], right_brow_rect[1] + 1, right_brow_rect[2], right_brow_rect[3]),
                0,
                math.pi,
                3,
            )

        elif mood == "disappointed":
            # Sad droopy eyes - draw multiple passes to fill gaps
            left_eye_rect = (int(face_x - 18), int(face_y + 2), 10, 7)
            right_eye_rect = (int(face_x + 8), int(face_y + 2), 10, 7)
            pygame.draw.arc(screen, eye_color, left_eye_rect, 0, math.pi, 3)
            pygame.draw.arc(
                screen,
                eye_color,
                (left_eye_rect[0], left_eye_rect[1] + 1, left_eye_rect[2], left_eye_rect[3]),
                0,
                math.pi,
                3,
            )
            pygame.draw.arc(screen, eye_color, right_eye_rect, 0, math.pi, 3)
            pygame.draw.arc(
                screen,
                eye_color,
                (right_eye_rect[0], right_eye_rect[1] + 1, right_eye_rect[2], right_eye_rect[3]),
                0,
                math.pi,
                3,
            )
            # Frown - draw multiple passes to fill gaps
            rect = (int(face_x - 14), int(face_y + 18), 28, 14)
            pygame.draw.arc(screen, eye_color, rect, 0, math.pi, 3)
            pygame.draw.arc(screen, eye_color, (rect[0], rect[1] + 1, rect[2], rect[3]), 0, math.pi, 3)
            # Tear drop animation - scaled up
            if self.animation_frame == 0:
                pygame.draw.circle(screen, (135, 206, 250), (int(face_x - 20), int(face_y + 5)), 3)
            else:
                pygame.draw.circle(screen, (135, 206, 250), (int(face_x - 20), int(face_y + 10)), 3)

        elif mood == "worried":
            # Worried expression - raised eyebrows and wavy mouth
            # Wide concerned eyes
            pygame.draw.circle(screen, eye_color, (int(face_x - 15), int(face_y)), 5)
            pygame.draw.circle(screen, eye_color, (int(face_x + 15), int(face_y)), 5)
            pygame.draw.circle(screen, WHITE, (int(face_x - 13), int(face_y - 1)), 2)
            pygame.draw.circle(screen, WHITE, (int(face_x + 17), int(face_y - 1)), 2)

            # Raised worried eyebrows (tilted)
            left_brow_rect = (int(face_x - 18), int(face_y - 8), 12, 6)
            right_brow_rect = (int(face_x + 6), int(face_y - 8), 12, 6)
            pygame.draw.arc(screen, eye_color, left_brow_rect, math.pi * 0.2, math.pi * 0.8, 3)
            pygame.draw.arc(screen, eye_color, right_brow_rect, math.pi * 0.2, math.pi * 0.8, 3)

            # Wavy worried mouth - lowered
            pygame.draw.line(screen, eye_color, (int(face_x - 10), int(face_y + 18)), (int(face_x - 5), int(face_y + 16)), 3)
            pygame.draw.line(screen, eye_color, (int(face_x - 5), int(face_y + 16)), (int(face_x), int(face_y + 18)), 3)
            pygame.draw.line(screen, eye_color, (int(face_x), int(face_y + 18)), (int(face_x + 5), int(face_y + 16)), 3)
            pygame.draw.line(screen, eye_color, (int(face_x + 5), int(face_y + 16)), (int(face_x + 10), int(face_y + 18)), 3)

    def _draw_speech_bubble(self, screen: pygame.Surface):
        """Draw speech bubble above pond buddy"""
        if not self.speech_text or self.speech_timer <= 0:
            return

        bubble_x = self.x + 50  # Offset to the right so it doesn't overlap
        bubble_y = self.y - 50  # Above the buddy, slightly lower to merge with triangle

        # Render the text
        font = pygame.font.Font(None, 24)
        text_surface = font.render(self.speech_text, True, (0, 0, 0))
        text_rect = text_surface.get_rect()

        # Bubble dimensions
        padding = 10
        bubble_width = text_rect.width + padding * 2
        bubble_height = text_rect.height + padding * 2

        # Draw bubble background (white with black border)
        bubble_rect = pygame.Rect(bubble_x - bubble_width // 2, bubble_y - bubble_height, bubble_width, bubble_height)
        pygame.draw.rect(screen, (255, 255, 255), bubble_rect)
        pygame.draw.rect(screen, (0, 0, 0), bubble_rect, 2)

        # Draw bubble tail pointing to pond buddy
        tail_tip_x = self.x + 30
        tail_tip_y = self.y - 20
        tail_base_x = bubble_x - 10
        tail_base_y = bubble_y

        # Triangle for speech bubble tail
        tail_points = [(tail_tip_x, tail_tip_y), (tail_base_x - 8, tail_base_y), (tail_base_x + 8, tail_base_y)]
        pygame.draw.polygon(screen, (255, 255, 255), tail_points)
        pygame.draw.polygon(screen, (0, 0, 0), tail_points, 2)

        # Draw text centered in bubble
        text_x = bubble_x - text_rect.width // 2
        text_y = bubble_y - bubble_height + padding
        screen.blit(text_surface, (text_x, text_y))
