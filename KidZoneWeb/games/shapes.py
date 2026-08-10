import asyncio
import math
import random
from pathlib import Path

import pygame

try:
    from .common.quiz import VoiceQuizGame
    from .common.widgets import AnswerButton, draw_speaker_icon
except ImportError:  # standalone `python games/shapes.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common.quiz import VoiceQuizGame
    from common.widgets import AnswerButton, draw_speaker_icon

BASE_DIR = Path(__file__).parent / "shapes_assets"

WIDTH, HEIGHT = 900, 700

# Soft, low-alpha shapes drifting behind the game - decorative only, drawn
# with the real draw_shape() so they visually echo what's being taught.
DECOR_SHAPES = ["circle", "square", "triangle", "star", "diamond", "heart"]
DECOR_PALETTE = [(190, 225, 220), (150, 210, 200), (210, 235, 230), (130, 195, 185)]


def article(word):
    return "an" if word[:1] in "aeiou" else "a"


def _star_points(cx, cy, outer_r, inner_r, points):
    pts = []
    angle = -math.pi / 2
    step = math.pi / points
    for i in range(points * 2):
        r = outer_r if i % 2 == 0 else inner_r
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        angle += step
    return pts


def _draw_heart(surface, cx, cy, half, color):
    r = half * 0.5
    pygame.draw.circle(surface, color, (int(cx - r), int(cy - r * 0.25)), int(r))
    pygame.draw.circle(surface, color, (int(cx + r), int(cy - r * 0.25)), int(r))
    pts = [
        (cx - half, cy - r * 0.2),
        (cx + half, cy - r * 0.2),
        (cx, cy + half),
    ]
    pygame.draw.polygon(surface, color, pts)


def draw_shape(surface, shape, center, size, color):
    x, y = center
    half = size / 2
    if shape == "circle":
        pygame.draw.circle(surface, color, (int(x), int(y)), int(half))
    elif shape == "square":
        rect = pygame.Rect(0, 0, size, size)
        rect.center = center
        pygame.draw.rect(surface, color, rect, border_radius=int(size * 0.1))
    elif shape == "rectangle":
        w, h = size * 1.3, size * 0.7
        rect = pygame.Rect(0, 0, w, h)
        rect.center = center
        pygame.draw.rect(surface, color, rect, border_radius=int(h * 0.15))
    elif shape == "oval":
        w, h = size * 1.35, size * 0.8
        rect = pygame.Rect(0, 0, w, h)
        rect.center = center
        pygame.draw.ellipse(surface, color, rect)
    elif shape == "triangle":
        pts = [(x, y - half), (x - half, y + half * 0.85), (x + half, y + half * 0.85)]
        pygame.draw.polygon(surface, color, pts)
    elif shape == "diamond":
        pts = [(x, y - half), (x + half * 0.72, y), (x, y + half), (x - half * 0.72, y)]
        pygame.draw.polygon(surface, color, pts)
    elif shape == "star":
        pts = _star_points(x, y, half, half * 0.42, 5)
        pygame.draw.polygon(surface, color, pts)
    elif shape == "heart":
        _draw_heart(surface, x, y, half, color)


class ShapeButton(AnswerButton):
    """Answers are drawn, not named - reading the word would give it away."""

    def draw_face(self, surface, font, mouse_pos):
        draw_shape(surface, self.label, self.rect.center,
                   self.rect.height * 0.62, (255, 255, 255))


class Game(VoiceQuizGame):
    TITLE = "Shapes"
    SUBTITLE = "Listen, then click the shape you hear!"

    VOICE_DIR = BASE_DIR / "voice_cache"
    SOUNDS_DIR = BASE_DIR / "sounds"

    BG_COLOR = (230, 250, 247)
    CARD_BORDER = (180, 225, 218)
    SPEAKER_COLOR = (20, 150, 140)
    BUTTON_COLOR = (20, 150, 140)
    BUTTON_HOVER = (15, 130, 120)
    SCORE_COLOR = (15, 110, 105)
    TITLE_COLOR = (15, 110, 105)

    def load_items(self):
        return sorted(self.available_voices())

    def not_enough_items_message(self):
        return "Need at least 2 shapes in voice_cache/"

    def wrong_message(self, item):
        return f"That's {article(item)} {item}!"

    def make_button(self, rect, value):
        return ShapeButton(rect, value, self.button_palette())

    def draw_prompt(self, surface, rect, revealed):
        if revealed:
            draw_shape(surface, self.current, rect.center,
                       self.CARD_SIZE * 0.62, self.feedback_color)
        else:
            draw_speaker_icon(surface, rect.center, self.CARD_SIZE * 0.5, self.SPEAKER_COLOR)

    def init_background(self):
        self.bg_decorations = [
            {
                "x": random.uniform(40, self.WIDTH - 40),
                "y": random.uniform(40, self.HEIGHT - 40),
                "size": random.randint(18, 34),
                "speed": random.uniform(0.4, 1.0),
                "phase": random.uniform(0, math.tau),
                "shape": random.choice(DECOR_SHAPES),
                "color": random.choice(DECOR_PALETTE),
            }
            for _ in range(9)
        ]

    def draw_background(self, now):
        self.screen.fill(self.BG_COLOR)
        for deco in self.bg_decorations:
            bob = math.sin(now / 900 * deco["speed"] + deco["phase"]) * 16
            size = deco["size"]
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            draw_shape(surf, deco["shape"], (size, size), size * 1.5, (*deco["color"], 90))
            self.screen.blit(surf, (deco["x"] - size, deco["y"] - size + bob))


if __name__ == "__main__":
    asyncio.run(Game().run())
