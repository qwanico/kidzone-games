import asyncio
import json
from pathlib import Path

import pygame

try:
    from .common.audio import available_voices
    from .common.quiz import VoiceQuizGame
    from .common.widgets import AnswerButton
except ImportError:  # standalone `python games/feelings.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common.audio import available_voices
    from common.quiz import VoiceQuizGame
    from common.widgets import AnswerButton

BASE_DIR = Path(__file__).parent / "feelings_assets"
ANIM_DIR = BASE_DIR / "anim_frames"

WIDTH, HEIGHT = 900, 700


def to_display_name(word: str) -> str:
    return word.capitalize()


class FrameAnimation:
    """Plays a pre-extracted sequence of PNG frames (see anim_frames/manifest.json)."""

    def __init__(self, frame_specs):
        self.frames = [
            (pygame.image.load(str(ANIM_DIR / spec["file"])).convert_alpha(), spec["duration"])
            for spec in frame_specs
        ]
        self.index = 0
        self.timer = 0

    def reset(self):
        self.index = 0
        self.timer = 0

    def update(self, dt_ms):
        if len(self.frames) <= 1:
            return
        self.timer += dt_ms
        _, duration = self.frames[self.index]
        while self.timer >= duration:
            self.timer -= duration
            self.index = (self.index + 1) % len(self.frames)
            _, duration = self.frames[self.index]

    def current(self):
        return self.frames[self.index][0]


class Game(VoiceQuizGame):
    TITLE = "Feelings"
    SUBTITLE = "Watch the face, then click the feeling you hear!"

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

    CARD_BORDER = (200, 220, 195)
    BUTTON_COLOR = (100, 175, 130)
    BUTTON_HOVER = (80, 155, 110)
    SCORE_COLOR = (70, 120, 90)
    TITLE_COLOR = (70, 120, 90)
    MILESTONE_COLOR = (225, 165, 40)

    BACKGROUND = "bubbles"
    BG_TOP_COLOR = (247, 253, 240)
    BG_BOTTOM_COLOR = (221, 241, 216)
    BUBBLE_COLORS = [
        (255, 255, 255, 90),
        (255, 241, 181, 70),
        (200, 235, 210, 95),
    ]
    PARTICLES = "confetti"
    CONFETTI_COLORS = [
        (255, 209, 102),
        (144, 224, 167),
        (110, 196, 255),
        (255, 255, 255),
        (198, 161, 255),
    ]

    def setup(self):
        manifest = json.loads((ANIM_DIR / "manifest.json").read_text())
        self.animations = {name: FrameAnimation(manifest[name]) for name in self.items}

    def load_items(self):
        return available_voices(self.VOICE_DIR)

    def not_enough_items_message(self):
        return "Need at least 2 feelings in voice_cache/"

    def wrong_message(self, item):
        return f"That's {to_display_name(item)}!"

    def make_button(self, rect, value):
        return AnswerButton(rect, to_display_name(value), self.button_palette())

    def on_new_round(self):
        self.animations[self.current].reset()

    def update(self, dt_ms):
        super().update(dt_ms)
        self.animations[self.current].update(dt_ms)

    def draw_prompt(self, surface, rect, revealed):
        # The animated face is the prompt itself and plays throughout, so
        # there is no speaker glyph and nothing extra to reveal.
        frame = self.animations[self.current].current()
        surface.blit(frame, frame.get_rect(center=rect.center))


if __name__ == "__main__":
    asyncio.run(Game().run())
