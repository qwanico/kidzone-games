import asyncio
import math
import random
from pathlib import Path

import pygame

try:
    from .common import text
    from .common.quiz import VoiceQuizGame, clamp
    from .common.widgets import AnswerButton, draw_speaker_icon
except ImportError:  # standalone `python games/counting.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common import text
    from common.quiz import VoiceQuizGame, clamp
    from common.widgets import AnswerButton, draw_speaker_icon

BASE_DIR = Path(__file__).parent / "counting_assets"

WIDTH, HEIGHT = 900, 700

BUTTON_COLOR = (140, 70, 190)
BUTTON_HOVER = (120, 55, 170)

# Faint drifting numerals behind the game - decorative only.
DECOR_PALETTE = [(210, 190, 230), (190, 165, 220), (225, 205, 240), (170, 140, 205)]

NUMBER_WORDS = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
WORD_TO_INT = {word: i + 1 for i, word in enumerate(NUMBER_WORDS)}


def draw_dots(surface, count, center, box_size, color):
    """Lay `count` dots out as one row up to five, then two rows."""
    cx, cy = center
    cols = min(count, 5)
    rows = 2 if count > 5 else 1
    cell = box_size / 5.2
    dot_r = cell * 0.34
    total_h = rows * cell
    top_y = cy - total_h / 2 + cell / 2

    remaining = count
    for r in range(rows):
        row_count = min(cols, remaining)
        remaining -= row_count
        row_w = row_count * cell
        row_start_x = cx - row_w / 2 + cell / 2
        y = top_y + r * cell
        for c in range(row_count):
            x = row_start_x + c * cell
            pygame.draw.circle(surface, color, (int(x), int(y)), int(dot_r))


class CountButton(AnswerButton):
    """The answer is a quantity, so the button shows dots rather than the
    numeral - counting them is the skill being practised."""

    def draw_face(self, surface, font, mouse_pos):
        draw_dots(surface, WORD_TO_INT[self.label], self.rect.center,
                  self.rect.height * 0.8, (255, 255, 255))


class Game(VoiceQuizGame):
    TITLE = "Counting"
    SUBTITLE = "Listen, then click the group with that many!"

    BUTTON_SQUARE = True

    VOICE_DIR = BASE_DIR / "voice_cache"
    SOUNDS_DIR = BASE_DIR / "sounds"

    BG_COLOR = (247, 240, 255)
    CARD_BORDER = (215, 195, 235)
    SPEAKER_COLOR = (140, 70, 190)
    BUTTON_COLOR = BUTTON_COLOR
    BUTTON_HOVER = BUTTON_HOVER
    SCORE_COLOR = (100, 55, 140)
    TITLE_COLOR = (100, 55, 140)

    def layout_extras(self):
        # Sized off the card rather than fixed, so the numeral still fits
        # when a rotated phone leaves the card a fraction of its height.
        self.font_reveal = text.SysFont("arial", int(self.CARD_SIZE * 0.53), bold=True)
        self.font_decor = text.SysFont("arial", int(clamp(60 * self.SCALE, 30, 66)), bold=True)

    def load_items(self):
        available = self.available_voices()
        return [w for w in NUMBER_WORDS if w in available]

    def not_enough_items_message(self):
        return "Need at least 2 numbers in voice_cache/"

    def wrong_message(self, item):
        return f"That's the number {item}!"

    def make_button(self, rect, value):
        return CountButton(rect, str(value), self.button_palette())

    def draw_prompt(self, surface, rect, revealed):
        if revealed:
            num = self.font_reveal.render(
                str(WORD_TO_INT[self.current]), True, self.feedback_color)
            surface.blit(num, num.get_rect(center=rect.center))
        else:
            draw_speaker_icon(surface, rect.center, self.CARD_SIZE * 0.5, self.SPEAKER_COLOR)

    # Numerals drift instead of the base's circles, so the backdrop is made
    # of the same symbols the game is teaching.
    def init_background(self):
        self.bg_decorations = [
            {
                "x": random.uniform(40, self.WIDTH - 40),
                "y": random.uniform(40, self.HEIGHT - 40),
                "speed": random.uniform(0.4, 1.0),
                "phase": random.uniform(0, math.tau),
                "text": str(random.randint(1, 10)),
                "color": random.choice(DECOR_PALETTE),
            }
            for _ in range(9)
        ]

    def draw_background(self, now):
        self.screen.fill(self.BG_COLOR)
        for deco in self.bg_decorations:
            bob = math.sin(now / 900 * deco["speed"] + deco["phase"]) * 16
            # render_copy: set_alpha would otherwise mutate the shared cache.
            surf = self.font_decor.render_copy(deco["text"], True, deco["color"])
            surf.set_alpha(90)
            self.screen.blit(surf, surf.get_rect(center=(deco["x"], deco["y"] + bob)))


if __name__ == "__main__":
    asyncio.run(Game().run())
