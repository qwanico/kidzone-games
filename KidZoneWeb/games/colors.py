import asyncio
from pathlib import Path

import pygame

try:
    from .common.quiz import VoiceQuizGame
    from .common.widgets import draw_speaker_icon
except ImportError:  # standalone `python games/colors.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common.quiz import VoiceQuizGame
    from common.widgets import draw_speaker_icon

BASE_DIR = Path(__file__).parent / "colors_assets"

WIDTH, HEIGHT = 900, 700

CORRECT_COLOR = (90, 200, 110)
WRONG_COLOR = (230, 90, 90)

# Kid-friendly, clearly-saturated swatch RGBs for each color word.
COLOR_RGB = {
    "red": (230, 40, 40),
    "blue": (40, 90, 230),
    "green": (40, 170, 70),
    "yellow": (250, 210, 30),
    "orange": (250, 140, 30),
    "purple": (140, 60, 190),
    "pink": (240, 110, 170),
    "brown": (120, 70, 40),
}


def _draw_check(surface, center, size, color):
    x, y = center
    p1 = (x - size, y)
    p2 = (x - size * 0.25, y + size * 0.7)
    p3 = (x + size, y - size * 0.6)
    pygame.draw.lines(surface, color, False, [p1, p2, p3], width=max(4, int(size * 0.28)))


def _draw_cross(surface, center, size, color):
    x, y = center
    w = max(4, int(size * 0.28))
    pygame.draw.line(surface, color, (x - size, y - size), (x + size, y + size), width=w)
    pygame.draw.line(surface, color, (x - size, y + size), (x + size, y - size), width=w)


class ColorButton:
    """A solid color swatch. The fill IS the answer, so it never changes color
    for hover/correct/wrong (that would hide the very thing being tested).
    Feedback is instead shown with a colored border + check/cross mark, and
    the idle/hover/correct/wrong states drive that border exactly like the
    text-button state machine elsewhere."""

    def __init__(self, rect, value):
        self.rect = pygame.Rect(rect)
        self.value = value
        self.label = str(value)
        self.state = "idle"

    def draw(self, surface, font, mouse_pos):
        rect = self.rect
        pygame.draw.rect(surface, COLOR_RGB[self.value], rect, border_radius=24)

        if self.state == "correct":
            border_color, border_w = CORRECT_COLOR, 8
        elif self.state == "wrong":
            border_color, border_w = WRONG_COLOR, 8
        elif rect.collidepoint(mouse_pos):
            border_color, border_w = (255, 255, 255), 6
        else:
            border_color, border_w = (255, 255, 255), 3
        pygame.draw.rect(surface, border_color, rect, width=border_w, border_radius=24)

        mark_size = rect.height * 0.24
        if self.state == "correct":
            _draw_check(surface, rect.center, mark_size, (255, 255, 255))
        elif self.state == "wrong":
            _draw_cross(surface, rect.center, mark_size, (255, 255, 255))


class Game(VoiceQuizGame):
    TITLE = "Colors"
    SUBTITLE = "Listen, then click the color you hear!"

    VOICE_DIR = BASE_DIR / "voice_cache"
    SOUNDS_DIR = BASE_DIR / "sounds"

    # Layout, palette and feedback timing all match the base defaults.
    # The drifting background circles are the swatch palette, so the menu
    # already shows the colours the game is about.
    BG_SHAPE_COLORS = list(COLOR_RGB.values())

    def load_items(self):
        available = self.available_voices()
        return [c for c in COLOR_RGB if c in available]

    def not_enough_items_message(self):
        return "Need at least 2 colors in voice_cache/"

    def make_button(self, rect, value):
        return ColorButton(rect, value)

    def draw_prompt(self, surface, rect, revealed):
        if revealed:
            pygame.draw.rect(
                surface, COLOR_RGB[self.current], rect.inflate(-16, -16), border_radius=20)
        else:
            draw_speaker_icon(surface, rect.center, self.CARD_SIZE * 0.5, self.SPEAKER_COLOR)


if __name__ == "__main__":
    asyncio.run(Game().run())
