import asyncio
from pathlib import Path

try:
    from .common import text
    from .common.audio import available_voices
    from .common.quiz import VoiceQuizGame
    from .common.widgets import draw_speaker_icon
except ImportError:  # standalone `python games/letters.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common import text
    from common.audio import available_voices
    from common.quiz import VoiceQuizGame
    from common.widgets import draw_speaker_icon

BASE_DIR = Path(__file__).parent / "letters_assets"

WIDTH, HEIGHT = 900, 700


class Game(VoiceQuizGame):
    TITLE = "Letters"
    SUBTITLE = "Listen, then click the letter you hear!"

    VOICE_DIR = BASE_DIR / "voice_cache"
    SOUNDS_DIR = BASE_DIR / "sounds"

    CARD_SIZE = 360
    CARD_TOP = 60
    BUTTON_W, BUTTON_H = 320, 90
    BUTTON_GAP = 40
    BUTTON_Y = HEIGHT - 160
    SCORE_POS = (100, 32)
    FEEDBACK_OFFSET = 40

    CARD_BORDER = (230, 200, 210)
    SPEAKER_COLOR = (220, 110, 150)
    BUTTON_COLOR = (220, 110, 150)
    BUTTON_HOVER = (200, 90, 130)
    SCORE_COLOR = (150, 70, 100)
    TITLE_COLOR = (150, 70, 100)
    MILESTONE_COLOR = (215, 130, 60)

    BACKGROUND = "bubbles"
    BG_TOP_COLOR = (255, 246, 249)
    BG_BOTTOM_COLOR = (250, 224, 233)
    BUBBLE_COLORS = [
        (255, 255, 255, 95),
        (240, 170, 200, 80),
        (220, 180, 235, 80),
    ]
    PARTICLES = "confetti"
    CONFETTI_COLORS = [
        (240, 130, 170),
        (200, 140, 230),
        (255, 200, 90),
        (255, 255, 255),
        (150, 200, 255),
    ]

    def setup(self):
        self.font_reveal = text.SysFont("arial", 160, bold=True)

    def load_items(self):
        return available_voices(self.VOICE_DIR)

    def not_enough_items_message(self):
        return "Need at least 2 letters in voice_cache/"

    def wrong_message(self, item):
        return f"That letter is {item}"

    def draw_prompt(self, surface, rect, revealed):
        if revealed:
            letter = self.font_reveal.render(self.current, True, self.feedback_color)
            surface.blit(letter, letter.get_rect(center=rect.center))
        else:
            draw_speaker_icon(surface, rect.center, self.CARD_SIZE * 0.5, self.SPEAKER_COLOR)


if __name__ == "__main__":
    asyncio.run(Game().run())
