import asyncio
import random
from pathlib import Path

import pygame

try:
    from .common import fx
    from .common import text
    from .common.audio import available_voices
    from .common.quiz import VoiceQuizGame
    from .common.widgets import draw_speaker_icon
except ImportError:  # standalone `python games/sight_words.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common import fx
    from common import text
    from common.audio import available_voices
    from common.quiz import VoiceQuizGame
    from common.widgets import draw_speaker_icon

BASE_DIR = Path(__file__).parent / "sight_words_assets"

WIDTH, HEIGHT = 900, 700

CLOUD_COLOR = (255, 255, 255)

class Game(VoiceQuizGame):
    TITLE = "Sight Words"
    SUBTITLE = "Listen, then click the word you hear!"

    VOICE_DIR = BASE_DIR / "voice_cache"
    SOUNDS_DIR = BASE_DIR / "sounds"

    CARD_BORDER = (190, 210, 230)
    SPEAKER_COLOR = (90, 160, 230)
    BUTTON_COLOR = (90, 160, 230)
    BUTTON_HOVER = (70, 140, 210)
    SCORE_COLOR = (60, 90, 130)
    TITLE_COLOR = (60, 90, 130)
    MILESTONE_COLOR = (230, 160, 40)

    BG_TOP_COLOR = (200, 232, 253)
    BG_BOTTOM_COLOR = (235, 248, 255)
    PARTICLES = "confetti"
    CONFETTI_COLORS = [
        (255, 220, 90),
        (110, 196, 255),
        (255, 255, 255),
        (140, 220, 180),
        (255, 160, 190),
    ]

    def layout_extras(self):
        # Words are long, so this is a much smaller fraction than the
        # single-glyph games use.
        self.font_reveal = text.SysFont("arial", int(self.CARD_SIZE * 0.25), bold=True)

    def load_items(self):
        return available_voices(self.VOICE_DIR)

    def not_enough_items_message(self):
        return "Need at least 2 sight words in voice_cache/"

    def wrong_message(self, item):
        return f"That word is {item}"

    def draw_prompt(self, surface, rect, revealed):
        if revealed:
            word = self.font_reveal.render(self.current, True, self.feedback_color)
            surface.blit(word, word.get_rect(center=rect.center))
        else:
            draw_speaker_icon(surface, rect.center, self.CARD_SIZE * 0.5, self.SPEAKER_COLOR)

    # Clear sky with slow drifting clouds, rather than the base's rising
    # bubbles - reading words wants a calm, uncluttered backdrop.
    def init_background(self):
        self.bg_surface = fx.build_gradient(
            self.WIDTH, self.HEIGHT, self.BG_TOP_COLOR, self.BG_BOTTOM_COLOR)
        self.clouds = [self._make_cloud(initial=True) for _ in range(5)]

    def _make_cloud(self, initial=False):
        return {
            "x": random.uniform(0, self.WIDTH) if initial else -220,
            "y": random.uniform(30, 230),
            "speed": random.uniform(10, 24),
            "scale": random.uniform(0.7, 1.3),
        }

    def update_background(self, dt_ms):
        dt = dt_ms / 1000
        for c in self.clouds:
            c["x"] += c["speed"] * dt
            if c["x"] > self.WIDTH + 200:
                c.update(self._make_cloud())

    def draw_background(self, now):
        self.screen.blit(self.bg_surface, (0, 0))
        for c in self.clouds:
            x, y, scale = c["x"], c["y"], c["scale"]
            for dx, dy, r in ((-40, 6, 26), (0, -8, 34), (38, 4, 28), (68, 8, 20)):
                pygame.draw.circle(
                    self.screen, CLOUD_COLOR,
                    (int(x + dx * scale), int(y + dy * scale)), int(r * scale))

if __name__ == "__main__":
    asyncio.run(Game().run())
