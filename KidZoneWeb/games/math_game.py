import asyncio
import math
import random
from pathlib import Path

import pygame

try:
    from .common import text
    from .common.quiz import VoiceQuizGame, clamp
    from .common.widgets import AnswerButton, draw_speaker_icon
except ImportError:  # standalone `python games/math_game.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common import text
    from common.quiz import VoiceQuizGame, clamp
    from common.widgets import AnswerButton, draw_speaker_icon

BASE_DIR = Path(__file__).parent / "math_game_assets"
ASSETS_DIR = BASE_DIR / "assets"

WIDTH, HEIGHT = 900, 700
FRUIT_SIZE = 30

TEXT_COLOR = (50, 50, 60)
GLOW_COLOR = (255, 210, 90)

def fruit_grid_positions(count, area_rect, icon_size):
    """Lay `count` icons out in rows of five, centred in `area_rect`."""
    gap = 6
    remaining = count
    rows = math.ceil(count / 5)
    total_h = rows * icon_size + (rows - 1) * gap
    start_y = area_rect.centery - total_h / 2
    positions = []
    for row in range(rows):
        row_count = min(5, remaining)
        remaining -= row_count
        row_w = row_count * icon_size + (row_count - 1) * gap
        start_x = area_rect.centerx - row_w / 2
        y = start_y + row * (icon_size + gap)
        for col in range(row_count):
            positions.append((start_x + col * (icon_size + gap), y))
    return positions

class FruitButton(AnswerButton):
    """Shows the numeral *and* that many apples, so a child who cannot yet
    read numerals can still count their way to the answer."""

    def __init__(self, rect, value, palette, fruit_icon, number_font):
        super().__init__(rect, value, palette)
        self.fruit_icon = fruit_icon
        self.number_font = number_font

    def draw(self, surface, font, mouse_pos):
        # A hovered button lifts and bobs; the base frame is drawn against
        # that shifted rect, so the whole button moves together.
        real_rect = self.rect
        if real_rect.collidepoint(mouse_pos) and self.state == "idle":
            bounce = math.sin(pygame.time.get_ticks() / 140) * 4
            self.rect = real_rect.inflate(6, 6).move(0, int(bounce))
        try:
            super().draw(surface, font, mouse_pos)
        finally:
            self.rect = real_rect

    def draw_face(self, surface, font, mouse_pos):
        number = self.number_font.render(str(self.label), True, (255, 255, 255))
        number_rect = number.get_rect(midtop=(self.rect.centerx, self.rect.top + 8))
        surface.blit(number, number_rect)

        icon_area = self.rect.copy()
        icon_area.top = number_rect.bottom + 4
        icon_area.height = max(icon_area.bottom - icon_area.top - 8,
                               self.fruit_icon.get_height())
        for x, y in fruit_grid_positions(self.label, icon_area,
                                         self.fruit_icon.get_width()):
            surface.blit(self.fruit_icon, (x, y))

class Game(VoiceQuizGame):
    TITLE = "Math"
    SUBTITLE = "Listen, then click the right answer!"

    BUTTON_H_RATIO = 0.21    # taller: the button holds a numeral above its apples

    VOICE_DIR = BASE_DIR / "voice_cache"
    SOUNDS_DIR = BASE_DIR / "sounds"

    BG_COLOR = (245, 250, 215)
    CARD_BORDER = (210, 225, 165)
    SPEAKER_COLOR = (120, 180, 40)
    BUTTON_COLOR = (120, 180, 40)
    BUTTON_HOVER = (100, 160, 30)
    SCORE_COLOR = (90, 130, 30)
    TITLE_COLOR = (90, 130, 30)

    BG_SHAPE_COUNT = 10
    BG_SHAPE_RADIUS = (10, 22)
    BG_SHAPE_ALPHA = 55
    BG_SHAPE_BOB = 14

    def setup(self):
        self.current_sum = 0
        self.shake_until = 0
        self.shake_seed = 0.0

    def layout_extras(self):
        self.font_equation = text.SysFont("arial", int(self.CARD_SIZE * 0.25), bold=True)
        self.font_number = text.SysFont("arial", int(self.BUTTON_H * 0.2), bold=True)
        # Five apples plus their gaps have to fit across a button, and the
        # button is a fraction of the screen - so the icon is sized from it
        # rather than fixed at 30px. Rescaled here, never per frame.
        icon = int(clamp(min(FRUIT_SIZE * self.SCALE, (self.BUTTON_W - 6 * 6) / 5), 10, 44))
        self._raw_fruit = getattr(self, "_raw_fruit", None) or \
            pygame.image.load(str(ASSETS_DIR / "apple.png")).convert_alpha()
        self.fruit_icon = pygame.transform.smoothscale(self._raw_fruit, (icon, icon))

    def load_items(self):
        available = self.available_voices()
        return [
            (a, b)
            for a in range(1, 6) for b in range(1, 6)
            if f"{a}_plus_{b}" in available
        ]

    def not_enough_items_message(self):
        return "Need at least 2 problems in voice_cache/"

    def voice_name(self, item):
        a, b = item
        return f"{a}_plus_{b}"

    def wrong_message(self, item):
        a, b = item
        return f"{a} + {b} = {self.current_sum}!"

    # Buttons hold sums, not the (a, b) problem being asked.
    def correct_value(self):
        return self.current_sum

    def choose_round_items(self):
        choices = [p for p in self.items if p != self.last_item] or self.items
        self.current = random.choice(choices)
        self.last_item = self.current

        a, b = self.current
        self.current_sum = a + b
        # Distractors sit near the answer, so the choice is a real comparison
        # rather than "pick the plausible-looking number".
        lo, hi = max(2, self.current_sum - 3), min(10, self.current_sum + 3)
        wrong = random.sample(
            [n for n in range(lo, hi + 1) if n != self.current_sum],
            self.CHOICES - 1,
        )
        self.last_wrong = wrong[0]

        shown = [self.current_sum] + wrong
        random.shuffle(shown)
        return shown

    def make_button(self, rect, value):
        return FruitButton(rect, value, self.button_palette(),
                           self.fruit_icon, self.font_number)

    def answer(self, button, value):
        super().answer(button, value)
        if value != self.current_sum:
            self.shake_until = pygame.time.get_ticks() + 400
            self.shake_seed = random.uniform(0, 100)

    def draw_card(self, mouse_pos):
        now = pygame.time.get_ticks()
        rect = self.card_rect.copy()
        if now < self.shake_until:
            t = (self.shake_until - now) / 400.0
            rect.x += int(math.sin((now + self.shake_seed) / 25) * 10 * t)

        # While the question is still open the card breathes, which is what
        # draws a child's eye back to it after they stop listening.
        if not self.revealed:
            pulse = (math.sin(now / 260) + 1) / 2
            glow_rect = rect.inflate(int(10 + pulse * 10), int(10 + pulse * 10))
            glow = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow, (*GLOW_COLOR, int(60 + pulse * 60)),
                             glow.get_rect(), border_radius=32)
            self.screen.blit(glow, glow_rect.topleft)

        border = self.BUTTON_HOVER if rect.collidepoint(mouse_pos) else self.CARD_BORDER
        pygame.draw.rect(self.screen, self.CARD_COLOR, rect, border_radius=28)
        pygame.draw.rect(self.screen, border, rect, width=3, border_radius=28)
        self.draw_prompt(self.screen, rect,
                         self.revealed and now < self.feedback_until)

    def draw_prompt(self, surface, rect, revealed):
        a, b = self.current
        if revealed:
            equation, color = f"{a} + {b} = {self.current_sum}", self.feedback_color
        else:
            equation, color = f"{a} + {b} = ?", TEXT_COLOR

        eq = self.font_equation.render(equation, True, color)
        surface.blit(eq, eq.get_rect(center=(rect.centerx, rect.centery - 45)))

        now = pygame.time.get_ticks()
        pulse = (math.sin(now / 200) + 1) / 2 if not revealed else 0.0
        draw_speaker_icon(surface, (rect.centerx, rect.centery + 90),
                          self.CARD_SIZE * 0.28, self.SPEAKER_COLOR, pulse=pulse)

if __name__ == "__main__":
    asyncio.run(Game().run())
