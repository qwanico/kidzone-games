import asyncio
import math
import random
from pathlib import Path

import pygame

try:
    import platform
except ImportError:
    platform = None

try:
    from .common import fx
    from .common.audio import VoicePlayer
    from .common.widgets import draw_home_icon, draw_speaker_icon
    from .common import display
    from .common import text
except ImportError:  # standalone `python games/counting.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common import fx
    from common.audio import VoicePlayer
    from common.widgets import draw_home_icon, draw_speaker_icon
    from common import display
    from common import text

BASE_DIR = Path(__file__).parent / "counting_assets"
VOICE_DIR = BASE_DIR / "voice_cache"
SOUNDS_DIR = BASE_DIR / "sounds"

WIDTH, HEIGHT = 900, 700
CARD_SIZE = 300
BUTTON_SIZE = 200
BUTTON_GAP = 60
BUTTON_Y = 450
FEEDBACK_MS = 1600

BG_COLOR = (247, 240, 255)
CARD_COLOR = (255, 255, 255)
CARD_BORDER = (215, 195, 235)
SPEAKER_COLOR = (140, 70, 190)
BUTTON_COLOR = (140, 70, 190)
BUTTON_HOVER = (120, 55, 170)
CORRECT_COLOR = (90, 200, 110)
WRONG_COLOR = (230, 90, 90)
TEXT_COLOR = (50, 50, 60)
SCORE_COLOR = (100, 55, 140)
OVERLAY_COLOR = (30, 30, 40, 190)
TITLE_COLOR = (100, 55, 140)
MILESTONE_GOLD = (215, 150, 20)

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"

# Faint drifting numerals + dot clusters behind the game - decorative only.
DECOR_PALETTE = [(210, 190, 230), (190, 165, 220), (225, 205, 240), (170, 140, 205)]

CONFETTI_COLORS = [
    (255, 99, 132), (255, 205, 86), (75, 192, 192),
    (54, 162, 235), (153, 102, 255), (255, 159, 64),
]


NUMBER_WORDS = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
WORD_TO_INT = {word: i + 1 for i, word in enumerate(NUMBER_WORDS)}


WORD_TO_INT = {word: i + 1 for i, word in enumerate(NUMBER_WORDS)}


def load_numbers():
    stems = {p.stem for p in VOICE_DIR.glob("*.ogg") if not p.stem.endswith("-pygbag")}
    return [w for w in NUMBER_WORDS if w in stems]


def draw_dots(surface, count, center, box_size, color):
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


class Button:
    def __init__(self, rect, value):
        self.rect = pygame.Rect(rect)
        self.value = value
        self.state = "idle"

    def bg_color(self, mouse_pos):
        if self.state == "correct":
            return CORRECT_COLOR
        if self.state == "wrong":
            return WRONG_COLOR
        if self.rect.collidepoint(mouse_pos):
            return BUTTON_HOVER
        return BUTTON_COLOR

    def draw(self, surface, font, mouse_pos):
        color = self.bg_color(mouse_pos)
        pygame.draw.rect(surface, color, self.rect, border_radius=24)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=3, border_radius=24)
        self.draw_content(surface, font, mouse_pos)

    def draw_content(self, surface, font, mouse_pos):
        text_surf = font.render(str(self.value), True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class CountButton(Button):
    def draw_content(self, surface, font, mouse_pos):
        count = WORD_TO_INT[self.value]
        draw_dots(surface, count, self.rect.center, self.rect.height * 0.8, (255, 255, 255))


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.voice = VoicePlayer(VOICE_DIR)

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
        if platform is not None and hasattr(platform, "window"):
            try:
                platform.window.window_resize()
            except Exception:
                pass
        pygame.display.set_caption("Counting")

        self.font_word = text.SysFont("arial", 40, bold=True)
        self.font_score = text.SysFont("arial", 28, bold=True)
        self.font_feedback = text.SysFont("arial", 44, bold=True)
        self.font_title = text.SysFont("arial", 68, bold=True)
        self.font_subtitle = text.SysFont("arial", 26)
        self.font_icon = text.SysFont("arial", 24, bold=True)
        self.font_reveal = text.SysFont("arial", 160, bold=True)
        self.font_decor = text.SysFont("arial", 60, bold=True)

        self.numbers = load_numbers()
        if len(self.numbers) < 2:
            raise RuntimeError("Need at least 2 numbers in voice_cache/")

        self.wrong_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.ogg"))

        self.score = 0
        self.streak = 0
        self.last_number = None
        self.last_wrong = None
        self.feedback_until = 0
        self.feedback_text = ""
        self.feedback_color = TEXT_COLOR
        self.buttons = []
        self.current_number = None
        self.reveal_number = False
        self.particles = []
        self.milestone_text = ""

        self.card_rect = pygame.Rect(0, 0, CARD_SIZE, CARD_SIZE)
        self.card_rect.centerx = WIDTH // 2
        self.card_rect.top = 70

        self.start_button = Button((WIDTH // 2 - 140, 460, 280, 90), "Start")
        self.pause_button = Button((WIDTH - 90, 20, 60, 50), "II")
        self.home_button = pygame.Rect(20, 20, 60, 50)
        self.resume_button = Button((WIDTH // 2 - 160, 340, 320, 80), "Resume")
        self.quit_button = Button((WIDTH // 2 - 160, 440, 320, 80), "Quit")

        self.bg_decorations = [
            {
                "x": random.uniform(40, WIDTH - 40),
                "y": random.uniform(40, HEIGHT - 40),
                "speed": random.uniform(0.4, 1.0),
                "phase": random.uniform(0, math.tau),
                "text": str(random.randint(1, 10)),
                "color": random.choice(DECOR_PALETTE),
            }
            for _ in range(9)
        ]

        self.state = STATE_MENU
        self._pause_remaining = None
        self.quit_requested = False

    def start_game(self):
        self.state = STATE_PLAYING
        self.new_round()

    def enter_pause(self):
        ticks = pygame.time.get_ticks()
        self._pause_remaining = (self.feedback_until - ticks) if self.feedback_until > ticks else None
        self.voice.pause()
        self.state = STATE_PAUSED

    def resume_game(self):
        ticks = pygame.time.get_ticks()
        self.feedback_until = ticks + self._pause_remaining if self._pause_remaining else 0
        self.voice.unpause()
        self.state = STATE_PLAYING

    def speak(self, number):
        self.voice.say(number)

    def new_round(self):
        choices = [n for n in self.numbers if n != self.last_number] or self.numbers
        self.current_number = random.choice(choices)
        self.last_number = self.current_number

        wrong_choices = [
            n for n in self.numbers
            if n != self.current_number and n != self.last_wrong
        ] or [n for n in self.numbers if n != self.current_number]
        wrong_number = random.choice(wrong_choices)
        self.last_wrong = wrong_number

        pair = [self.current_number, wrong_number]
        random.shuffle(pair)

        total_w = BUTTON_SIZE * 2 + BUTTON_GAP
        start_x = (WIDTH - total_w) // 2

        self.buttons = [
            CountButton((start_x, BUTTON_Y, BUTTON_SIZE, BUTTON_SIZE), pair[0]),
            CountButton((start_x + BUTTON_SIZE + BUTTON_GAP, BUTTON_Y, BUTTON_SIZE, BUTTON_SIZE), pair[1]),
        ]
        self._button_values = pair

        self.feedback_until = 0
        self.feedback_text = ""
        self.reveal_number = False
        self.milestone_text = ""

        self.speak(self.current_number)

    def handle_menu_click(self, pos):
        if self.start_button.rect.collidepoint(pos):
            self.start_game()

    def handle_pause_click(self, pos):
        if self.home_button.collidepoint(pos):
            self.quit_requested = True
        elif self.resume_button.rect.collidepoint(pos):
            self.resume_game()
        elif self.quit_button.rect.collidepoint(pos):
            self.quit_requested = True

    def handle_click(self, pos):
        if self.home_button.collidepoint(pos):
            self.quit_requested = True
            return

        if self.pause_button.rect.collidepoint(pos):
            self.enter_pause()
            return

        if self.card_rect.collidepoint(pos):
            self.speak(self.current_number)
            return

        if pygame.time.get_ticks() < self.feedback_until:
            return

        for button, number in zip(self.buttons, self._button_values):
            if button.rect.collidepoint(pos):
                now = pygame.time.get_ticks()
                is_correct = number == self.current_number
                for b, n in zip(self.buttons, self._button_values):
                    b.state = "correct" if n == self.current_number else (
                        "wrong" if b is button else "idle"
                    )

                self.reveal_number = True

                if is_correct:
                    self.score += 1
                    self.streak += 1
                    self.feedback_text = "Great job!"
                    self.feedback_color = CORRECT_COLOR
                    self.particles.extend(fx.spawn_burst(button.rect.center, now, CONFETTI_COLORS))
                    if self.streak >= 3 and self.streak % 3 == 0:
                        self.milestone_text = f"{self.streak} in a row!"
                    else:
                        self.milestone_text = ""
                else:
                    self.streak = 0
                    self.wrong_sound.play()
                    self.feedback_text = f"That's the number {self.current_number}!"
                    self.feedback_color = WRONG_COLOR
                    self.milestone_text = ""

                self.feedback_until = now + FEEDBACK_MS
                return

    def update(self):
        now = pygame.time.get_ticks()
        if self.particles:
            self.particles = [p for p in self.particles if p.alive(now)]
        if self.feedback_until and now >= self.feedback_until:
            self.new_round()

    def draw_bg_shapes(self, now):
        for deco in self.bg_decorations:
            bob = math.sin(now / 900 * deco["speed"] + deco["phase"]) * 16
            text_surf = self.font_decor.render_copy(deco["text"], True, deco["color"])
            text_surf.set_alpha(90)
            rect = text_surf.get_rect(center=(deco["x"], deco["y"] + bob))
            self.screen.blit(text_surf, rect)

    def draw_particles(self):
        fx.draw_burst(self.screen, self.particles, pygame.time.get_ticks())

    def draw_milestone(self, text):
        banner = self.font_feedback.render(text, True, MILESTONE_GOLD)
        banner_rect = banner.get_rect(center=(WIDTH // 2, 45))
        bg_rect = banner_rect.inflate(50, 24)
        pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, border_radius=18)
        pygame.draw.rect(self.screen, MILESTONE_GOLD, bg_rect, 4, border_radius=18)
        self.screen.blit(banner, banner_rect)

    def draw_menu(self):
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(pygame.time.get_ticks())

        title_surf = self.font_title.render("Counting", True, TITLE_COLOR)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 220))
        self.screen.blit(title_surf, title_rect)

        subtitle_surf = self.font_subtitle.render(
            "Listen, then click the number you hear!", True, TEXT_COLOR
        )
        subtitle_rect = subtitle_surf.get_rect(center=(WIDTH // 2, 290))
        self.screen.blit(subtitle_surf, subtitle_rect)

        self.start_button.draw(self.screen, self.font_word, mouse_pos)

    def draw_playing(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)

        card_rect = self.card_rect
        border_color = BUTTON_HOVER if card_rect.collidepoint(mouse_pos) else CARD_BORDER
        pygame.draw.rect(self.screen, CARD_COLOR, card_rect, border_radius=28)
        pygame.draw.rect(self.screen, border_color, card_rect, width=3, border_radius=28)

        if self.reveal_number and pygame.time.get_ticks() < self.feedback_until:
            num_surf = self.font_reveal.render(str(WORD_TO_INT[self.current_number]), True, self.feedback_color)
            num_rect = num_surf.get_rect(center=card_rect.center)
            self.screen.blit(num_surf, num_rect)
        else:
            draw_speaker_icon(self.screen, card_rect.center, CARD_SIZE * 0.5, SPEAKER_COLOR)

        for button in self.buttons:
            button.draw(self.screen, self.font_word, mouse_pos)

        self.draw_particles()

        score_text = self.font_score.render(
            f"Score: {self.score}   Streak: {self.streak}", True, SCORE_COLOR
        )
        self.screen.blit(score_text, (24, 20))

        self.pause_button.draw(self.screen, self.font_icon, mouse_pos)
        draw_home_icon(self.screen, self.home_button, BUTTON_COLOR)

        if self.feedback_text and pygame.time.get_ticks() < self.feedback_until:
            fb_surf = self.font_feedback.render(self.feedback_text, True, self.feedback_color)
            fb_rect = fb_surf.get_rect(center=(WIDTH // 2, card_rect.bottom + 35))
            self.screen.blit(fb_surf, fb_rect)

        if self.milestone_text and pygame.time.get_ticks() < self.feedback_until:
            self.draw_milestone(self.milestone_text)

    def draw_paused(self):
        mouse_pos = pygame.mouse.get_pos()

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

        paused_surf = self.font_title.render("Paused", True, (255, 255, 255))
        paused_rect = paused_surf.get_rect(center=(WIDTH // 2, 240))
        self.screen.blit(paused_surf, paused_rect)

        self.resume_button.draw(self.screen, self.font_word, mouse_pos)
        self.quit_button.draw(self.screen, self.font_word, mouse_pos)

    def draw(self):
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_PLAYING:
            self.draw_playing()
        elif self.state == STATE_PAUSED:
            self.draw_playing()
            self.draw_paused()

        pygame.display.flip()

        _resized = display.maintain(WIDTH, HEIGHT)

        if _resized is not None:

            self.screen = _resized

    async def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.state == STATE_PLAYING:
                        self.enter_pause()
                    elif self.state == STATE_PAUSED:
                        self.resume_game()
                    else:
                        running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == STATE_MENU:
                        self.handle_menu_click(event.pos)
                    elif self.state == STATE_PLAYING:
                        self.handle_click(event.pos)
                    elif self.state == STATE_PAUSED:
                        self.handle_pause_click(event.pos)

            if self.state == STATE_PLAYING:
                self.update()
            self.draw()

            if self.quit_requested:
                running = False

            clock.tick(60)
            await asyncio.sleep(0)

        self.voice.stop()


if __name__ == "__main__":
    asyncio.run(Game().run())
