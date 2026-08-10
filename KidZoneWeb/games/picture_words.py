import asyncio
from pathlib import Path

import pygame

try:
    from .common.quiz import VoiceQuizGame
    from .common.widgets import AnswerButton
except ImportError:  # standalone `python games/picture_words.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common.quiz import VoiceQuizGame
    from common.widgets import AnswerButton

BASE_DIR = Path(__file__).parent / "picture_words_assets"
ASSETS_DIR = BASE_DIR / "assets"

WIDTH, HEIGHT = 900, 700
PICTURE_SIZE = 360


def to_display_name(stem: str) -> str:
    return stem.replace("_", " ").title()


class Game(VoiceQuizGame):
    TITLE = "Picture Words"
    SUBTITLE = "Pick the word that matches the picture!"

    VOICE_DIR = BASE_DIR / "voice_cache"
    SOUNDS_DIR = BASE_DIR / "sounds"

    CARD_SIZE = 360
    CARD_TOP = 60
    BUTTON_W, BUTTON_H = 320, 90
    BUTTON_GAP = 40
    BUTTON_Y = HEIGHT - 160
    SCORE_POS = (100, 32)
    FEEDBACK_OFFSET = 40
    FEEDBACK_MS = 1400

    CARD_BORDER = (210, 200, 170)
    BUTTON_COLOR = (90, 160, 230)
    BUTTON_HOVER = (70, 140, 210)
    SCORE_COLOR = (120, 90, 40)
    TITLE_COLOR = (120, 90, 40)
    MILESTONE_COLOR = (210, 130, 40)

    # Warm drifting bokeh glows: the base's bubbles without the highlight
    # ring, larger and slower.
    BACKGROUND = "bubbles"
    BG_TOP_COLOR = (255, 248, 222)
    BG_BOTTOM_COLOR = (250, 232, 190)
    BUBBLE_COLORS = [
        (255, 235, 180, 90),
        (255, 210, 150, 70),
        (255, 255, 255, 60),
    ]
    BUBBLE_COUNT = 12
    BUBBLE_RADIUS = (14, 34)
    BUBBLE_SPEED = (8, 22)
    BUBBLE_DRIFT = 8
    BUBBLE_RING = False

    PARTICLES = "confetti"
    CONFETTI_COLORS = [
        (255, 200, 90),
        (240, 150, 90),
        (255, 255, 255),
        (110, 196, 255),
        (140, 200, 140),
    ]

    def setup(self):
        self.picture_surface = None

    def load_items(self):
        """A playable item needs both halves - a picture and a clip naming
        it - so anything with only one is skipped rather than crashing mid
        round."""
        self.pictures = {}
        available = self.available_voices()
        for img_path in sorted(ASSETS_DIR.glob("*.png")):
            name = img_path.stem
            if not name.endswith("-pygbag") and name in available:
                self.pictures[name] = img_path
        return sorted(self.pictures)

    def not_enough_items_message(self):
        return "Need at least 2 picture/word pairs in assets/"

    def wrong_message(self, item):
        return f"That's {to_display_name(item)}!"

    def make_button(self, rect, value):
        return AnswerButton(rect, to_display_name(value), self.button_palette())

    def on_new_round(self):
        self.picture_surface = self.load_picture(self.current)

    def load_picture(self, name):
        img = pygame.image.load(str(self.pictures[name])).convert_alpha()
        w, h = img.get_size()
        scale = PICTURE_SIZE / max(w, h)
        return pygame.transform.smoothscale(
            img, (max(1, int(w * scale)), max(1, int(h * scale))))

    def draw_prompt(self, surface, rect, revealed):
        # The picture is the question and stays up through the answer.
        if self.picture_surface is not None:
            surface.blit(self.picture_surface,
                         self.picture_surface.get_rect(center=rect.center))


if __name__ == "__main__":
    asyncio.run(Game().run())
