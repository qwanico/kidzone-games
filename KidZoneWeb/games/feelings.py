import asyncio
import json
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
    from .common.audio import VoicePlayer, available_voices
    from .common.widgets import AnswerButton, draw_home_icon
except ImportError:  # standalone `python games/feelings.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common import fx
    from common.audio import VoicePlayer, available_voices
    from common.widgets import AnswerButton, draw_home_icon

BASE_DIR = Path(__file__).parent / "feelings_assets"
VOICE_DIR = BASE_DIR / "voice_cache"
SOUNDS_DIR = BASE_DIR / "sounds"
ANIM_DIR = BASE_DIR / "anim_frames"

WIDTH, HEIGHT = 900, 700
CARD_SIZE = 360
ANIM_SIZE = 300
FEEDBACK_MS = 1400

BG_COLOR = (240, 250, 235)
BG_TOP_COLOR = (247, 253, 240)
BG_BOTTOM_COLOR = (221, 241, 216)
CARD_COLOR = (255, 255, 255)
CARD_BORDER = (200, 220, 195)
BUTTON_COLOR = (100, 175, 130)
BUTTON_HOVER = (80, 155, 110)
CORRECT_COLOR = (90, 200, 110)
WRONG_COLOR = (230, 90, 90)
TEXT_COLOR = (50, 50, 60)
SCORE_COLOR = (70, 120, 90)
OVERLAY_COLOR = (30, 30, 40, 190)
TITLE_COLOR = (70, 120, 90)
MILESTONE_COLOR = (225, 165, 40)

CONFETTI_COLORS = [
    (255, 209, 102),
    (144, 224, 167),
    (110, 196, 255),
    (255, 255, 255),
    (198, 161, 255),
]

BUBBLE_COLORS = [
    (255, 255, 255, 90),
    (255, 241, 181, 70),
    (200, 235, 210, 95),
]

GRAVITY = 480
MILESTONE_MS = 1300

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"


def to_display_name(word: str) -> str:
    return word.capitalize()


def load_feelings():
    return available_voices(VOICE_DIR)


BUTTON_PALETTE = {
    "base": BUTTON_COLOR,
    "hover": BUTTON_HOVER,
    "correct": CORRECT_COLOR,
    "wrong": WRONG_COLOR,
}


def Button(rect, label):
    """Thin shim so existing call sites keep their shape."""
    return AnswerButton(rect, label, BUTTON_PALETTE)


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


def load_animations(feelings):
    manifest = json.loads((ANIM_DIR / "manifest.json").read_text())
    return {name: FrameAnimation(manifest[name]) for name in feelings}


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
        pygame.display.set_caption("Feelings")

        self.font_word = pygame.font.SysFont("arial", 42, bold=True)
        self.font_score = pygame.font.SysFont("arial", 28, bold=True)
        self.font_feedback = pygame.font.SysFont("arial", 50, bold=True)
        self.font_title = pygame.font.SysFont("arial", 68, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 26)
        self.font_icon = pygame.font.SysFont("arial", 24, bold=True)
        self.font_milestone = pygame.font.SysFont("arial", 40, bold=True)

        self.feelings = load_feelings()
        if len(self.feelings) < 2:
            raise RuntimeError("Need at least 2 feelings in voice_cache/")

        self.animations = load_animations(self.feelings)

        self.wrong_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.ogg"))

        self.score = 0
        self.streak = 0
        self.last_feeling = None
        self.last_wrong = None
        self.feedback_until = 0
        self.feedback_text = ""
        self.feedback_color = TEXT_COLOR
        self.buttons = []
        self.current_feeling = None

        self.card_rect = pygame.Rect(0, 0, CARD_SIZE, CARD_SIZE)
        self.card_rect.centerx = WIDTH // 2
        self.card_rect.top = 60

        self.start_button = Button((WIDTH // 2 - 140, 460, 280, 90), "Start")
        self.pause_button = Button((WIDTH - 90, 20, 60, 50), "II")
        self.home_button = pygame.Rect(20, 20, 60, 50)
        self.resume_button = Button((WIDTH // 2 - 160, 340, 320, 80), "Resume")
        self.quit_button = Button((WIDTH // 2 - 160, 440, 320, 80), "Quit")

        self.state = STATE_MENU
        self._pause_remaining = None
        self.quit_requested = False

        # --- decorative background (soft drifting bubbles over a calm gradient) ---
        self.bg_surface = fx.build_gradient(WIDTH, HEIGHT, BG_TOP_COLOR, BG_BOTTOM_COLOR)
        self.bubbles = [self._make_bubble(initial=True) for _ in range(14)]

        # --- confetti / particle burst on correct answers ---
        self.particles = []

        # --- streak milestone callout ---
        self.milestone_text = ""
        self.milestone_until = 0

    def _make_bubble(self, initial=False):
        return {
            "x": random.uniform(0, WIDTH),
            "y": random.uniform(0, HEIGHT) if initial else HEIGHT + random.uniform(0, 60),
            "r": random.uniform(9, 24),
            "speed": random.uniform(12, 32),
            "drift": random.uniform(-10, 10),
            "phase": random.uniform(0, math.tau),
            "color": random.choice(BUBBLE_COLORS),
        }

    def update_background(self, dt_ms):
        dt = dt_ms / 1000
        now = pygame.time.get_ticks() / 1000
        for b in self.bubbles:
            b["y"] -= b["speed"] * dt
            b["x"] += math.sin(now + b["phase"]) * b["drift"] * dt
            if b["y"] < -30:
                b["y"] = HEIGHT + random.uniform(0, 40)
                b["x"] = random.uniform(0, WIDTH)

    def draw_background(self):
        self.screen.blit(self.bg_surface, (0, 0))
        for b in self.bubbles:
            r = int(b["r"])
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, b["color"], (r, r), r)
            pygame.draw.circle(s, (255, 255, 255, 120), (r, r), r, width=2)
            self.screen.blit(s, (b["x"] - r, b["y"] - r))

    def spawn_particles(self, cx, cy, streak):
        self.particles.extend(
            fx.spawn_confetti(cx, cy, CONFETTI_COLORS, count=16 + min(streak, 10) * 2)
        )

    def update_particles(self, dt_ms):
        fx.update_confetti(self.particles, dt_ms, GRAVITY)

    def draw_particles(self):
        fx.draw_confetti(self.screen, self.particles)

    def draw_milestone(self):
        if pygame.time.get_ticks() >= self.milestone_until:
            return
        banner = self.font_milestone.render(self.milestone_text, True, MILESTONE_COLOR)
        banner_rect = banner.get_rect(center=(WIDTH // 2, 95))
        bg_rect = banner_rect.inflate(44, 22)
        pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, border_radius=18)
        pygame.draw.rect(self.screen, MILESTONE_COLOR, bg_rect, width=3, border_radius=18)
        self.screen.blit(banner, banner_rect)

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

    def speak(self, feeling):
        self.voice.say(feeling)

    def new_round(self):
        choices = [f for f in self.feelings if f != self.last_feeling] or self.feelings
        self.current_feeling = random.choice(choices)
        self.last_feeling = self.current_feeling

        wrong_choices = [
            f for f in self.feelings
            if f != self.current_feeling and f != self.last_wrong
        ] or [f for f in self.feelings if f != self.current_feeling]
        wrong_feeling = random.choice(wrong_choices)
        self.last_wrong = wrong_feeling

        pair = [self.current_feeling, wrong_feeling]
        random.shuffle(pair)

        button_w, button_h = 320, 90
        gap = 40
        total_w = button_w * 2 + gap
        start_x = (WIDTH - total_w) // 2
        y = HEIGHT - 160

        self.buttons = [
            Button((start_x, y, button_w, button_h), to_display_name(pair[0])),
            Button((start_x + button_w + gap, y, button_w, button_h), to_display_name(pair[1])),
        ]
        self._button_names = pair

        self.feedback_until = 0
        self.feedback_text = ""
        self.animations[self.current_feeling].reset()

        self.speak(self.current_feeling)

    def handle_menu_click(self, pos):
        if self.start_button.rect.collidepoint(pos):
            self.start_game()

    def handle_pause_click(self, pos):
        if self.home_button.collidepoint(pos):
            self.quit_requested = True
            return
        if self.resume_button.rect.collidepoint(pos):
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
            self.speak(self.current_feeling)
            self.animations[self.current_feeling].reset()
            return

        if pygame.time.get_ticks() < self.feedback_until:
            return

        for button, feeling in zip(self.buttons, self._button_names):
            if button.rect.collidepoint(pos):
                is_correct = feeling == self.current_feeling
                for b, f in zip(self.buttons, self._button_names):
                    b.state = "correct" if f == self.current_feeling else (
                        "wrong" if b is button else "idle"
                    )

                if is_correct:
                    self.score += 1
                    self.streak += 1
                    self.feedback_text = "Great job!"
                    self.feedback_color = CORRECT_COLOR
                    self.spawn_particles(button.rect.centerx, button.rect.centery, self.streak)
                    if self.streak >= 3 and self.streak % 3 == 0:
                        self.milestone_text = f"{self.streak} in a row!"
                        self.milestone_until = pygame.time.get_ticks() + MILESTONE_MS
                else:
                    self.streak = 0
                    self.wrong_sound.play()
                    self.feedback_text = f"That's {to_display_name(self.current_feeling)}!"
                    self.feedback_color = WRONG_COLOR

                self.feedback_until = pygame.time.get_ticks() + FEEDBACK_MS
                return

    def update(self, dt):
        self.animations[self.current_feeling].update(dt)
        self.update_particles(dt)
        if self.feedback_until and pygame.time.get_ticks() >= self.feedback_until:
            self.new_round()

    def draw_menu(self):
        self.draw_background()
        mouse_pos = pygame.mouse.get_pos()

        title_surf = self.font_title.render("Feelings", True, TITLE_COLOR)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 220))
        self.screen.blit(title_surf, title_rect)

        subtitle_surf = self.font_subtitle.render(
            "Pick the word that matches the face!", True, TEXT_COLOR
        )
        subtitle_rect = subtitle_surf.get_rect(center=(WIDTH // 2, 290))
        self.screen.blit(subtitle_surf, subtitle_rect)

        self.start_button.draw(self.screen, self.font_word, mouse_pos)

    def draw_playing(self):
        self.draw_background()
        mouse_pos = pygame.mouse.get_pos()

        card_rect = self.card_rect
        border_color = BUTTON_HOVER if card_rect.collidepoint(mouse_pos) else CARD_BORDER
        pygame.draw.rect(self.screen, CARD_COLOR, card_rect, border_radius=28)
        pygame.draw.rect(self.screen, border_color, card_rect, width=3, border_radius=28)

        frame_surf = self.animations[self.current_feeling].current()
        frame_rect = frame_surf.get_rect(center=card_rect.center)
        self.screen.blit(frame_surf, frame_rect)

        for button in self.buttons:
            button.draw(self.screen, self.font_word, mouse_pos)

        self.draw_particles()

        score_text = self.font_score.render(
            f"Score: {self.score}   Streak: {self.streak}", True, SCORE_COLOR
        )
        self.screen.blit(score_text, (100, 32))

        self.pause_button.draw(self.screen, self.font_icon, mouse_pos)
        draw_home_icon(self.screen, self.home_button, BUTTON_COLOR, self.home_button.collidepoint(mouse_pos))

        self.draw_milestone()

        if self.feedback_text and pygame.time.get_ticks() < self.feedback_until:
            fb_surf = self.font_feedback.render(self.feedback_text, True, self.feedback_color)
            fb_rect = fb_surf.get_rect(center=(WIDTH // 2, card_rect.bottom + 40))
            self.screen.blit(fb_surf, fb_rect)

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

        # Redraw the home button on top of the overlay (undimmed) so it stays
        # a clear, immediate one-tap way out even while paused.
        draw_home_icon(self.screen, self.home_button, BUTTON_COLOR, self.home_button.collidepoint(mouse_pos))

    def draw(self):
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_PLAYING:
            self.draw_playing()
        elif self.state == STATE_PAUSED:
            self.draw_playing()
            self.draw_paused()

        pygame.display.flip()

    async def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = clock.tick(60)
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

            self.update_background(dt)
            if self.state == STATE_PLAYING:
                self.update(dt)
            self.draw()

            if self.quit_requested:
                running = False

            await asyncio.sleep(0)

        self.voice.stop()


if __name__ == "__main__":
    asyncio.run(Game().run())
