"""The listen-and-choose game skeleton.

Eight games - Colors, Counting, Feelings, Letters, Math, Picture Words,
Shapes and Sight Words - are the same game wearing different clothes: play a
spoken prompt, show two or more answers, score the tap, celebrate a streak,
move on. Each one had its own copy of the whole thing, so the real per-game
content (which is small: an item list and how to draw one) sat inside ~450
lines of identical scaffolding, and every fix to the loop, the pause state or
the scoring had to be made eight times.

This owns everything that was identical:

  * the async loop, the menu/playing/paused state machine, and the Escape and
    quit handling;
  * display setup, the per-frame `display.maintain()` that keeps SCALED
    correct across a rotation, and the pygbag `window_resize()` call;
  * pause that survives mid-feedback (the remaining feedback time is banked
    and restored, so pausing does not skip a round);
  * scoring, streaks, feedback text and its timing, the correct/wrong button
    flash, particles and the streak milestone banner;
  * the menu, the pause overlay, the score line, and the home/pause buttons.

A subclass supplies the parts that actually differ. The minimum is a voice
directory, a title, `load_items()`, and `draw_prompt()`; everything else has
a working default:

    class Game(VoiceQuizGame):
        TITLE = "Colors"
        VOICE_DIR = BASE_DIR / "voice_cache"
        SOUNDS_DIR = BASE_DIR / "sounds"

        def load_items(self):
            return [c for c in COLOR_RGB if c in self.available_voices()]

        def draw_prompt(self, surface, rect, revealed):
            ...

Subclasses keep their own module-level `WIDTH`/`HEIGHT` and palette names, so
the hub's launch contract (`module` + `entry` in the registry) is unchanged
and each game still runs standalone with `python games/<name>.py`.
"""

import asyncio
import math
import random

import pygame

from . import display
from . import fx
from . import text
from .audio import VoicePlayer
from .widgets import AnswerButton, draw_home_icon, draw_speaker_icon

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"

DEFAULT_CONFETTI = [
    (255, 99, 132), (255, 205, 86), (75, 192, 192),
    (54, 162, 235), (153, 102, 255), (255, 159, 64),
]


class VoiceQuizGame:
    """Base for the eight voice-prompt quiz games."""

    # ---- identity -----------------------------------------------------
    TITLE = "Quiz"
    SUBTITLE = "Listen, then tap what you hear!"
    VOICE_DIR = None          # required: Path to the spoken clips
    SOUNDS_DIR = None         # required: Path to wrong.ogg

    # ---- layout -------------------------------------------------------
    WIDTH, HEIGHT = 900, 700
    CARD_SIZE = 300
    CARD_TOP = 70
    BUTTON_SIZE = 200         # square answer buttons
    BUTTON_W = None           # override for wide buttons; defaults to BUTTON_SIZE
    BUTTON_H = None
    BUTTON_GAP = 60
    BUTTON_Y = 450
    SCORE_POS = (24, 20)
    FEEDBACK_OFFSET = 35      # below the card
    CHOICES = 2
    FEEDBACK_MS = 1600

    # ---- palette ------------------------------------------------------
    BG_COLOR = (255, 246, 235)
    CARD_COLOR = (255, 255, 255)
    CARD_BORDER = (230, 210, 180)
    TEXT_COLOR = (50, 50, 60)
    TITLE_COLOR = (150, 85, 25)
    SCORE_COLOR = (150, 85, 25)
    SPEAKER_COLOR = (225, 130, 45)
    BUTTON_COLOR = (225, 130, 45)
    BUTTON_HOVER = (205, 110, 30)
    CORRECT_COLOR = (90, 200, 110)
    WRONG_COLOR = (230, 90, 90)
    OVERLAY_COLOR = (30, 30, 40, 190)
    MILESTONE_COLOR = (215, 150, 20)
    CONFETTI_COLORS = DEFAULT_CONFETTI

    # ---- decoration ---------------------------------------------------
    # "shapes": drifting translucent circles over a flat fill.
    # "bubbles": bubbles rising over a vertical gradient (needs BG_TOP/BOTTOM).
    BACKGROUND = "shapes"
    BG_SHAPE_COLORS = None    # defaults to CONFETTI_COLORS
    BG_SHAPE_COUNT = 12
    BG_SHAPE_RADIUS = (20, 42)
    BG_SHAPE_ALPHA = 70
    BG_SHAPE_BOB = 16
    BG_TOP_COLOR = (255, 246, 235)
    BG_BOTTOM_COLOR = (255, 226, 235)
    BUBBLE_COLORS = [(255, 190, 215, 90), (255, 215, 230, 90)]
    BUBBLE_COUNT = 14
    BUBBLE_RADIUS = (8, 22)
    BUBBLE_SPEED = (14, 36)
    BUBBLE_DRIFT = 10
    BUBBLE_RING = True        # soft highlight ring; off gives a bokeh glow
    # "burst": upward fan sampled from a timestamp. "confetti": dt-integrated
    # with gravity.
    PARTICLES = "burst"
    GRAVITY = 480

    # ===================================================================
    # Hooks a subclass implements
    # ===================================================================

    def load_items(self):
        """Return the list of playable items. Needs at least two."""
        raise NotImplementedError

    def draw_prompt(self, surface, rect, revealed):
        """Draw the card's contents. `revealed` is True during the pause
        after an answer, when most games show the answer instead of the
        speaker glyph."""
        draw_speaker_icon(surface, rect.center, self.CARD_SIZE * 0.5, self.SPEAKER_COLOR)

    def make_button(self, rect, value):
        """Build one answer button. The default is a labelled AnswerButton."""
        return AnswerButton(rect, str(value), self.button_palette())

    def voice_name(self, item):
        """Clip stem for `item`, when it differs from the item itself."""
        return str(item)

    def correct_value(self):
        """What a button's value must equal for the tap to be right.
        Usually the item itself, but Math's buttons hold sums rather than
        the (a, b) problem being asked."""
        return self.current

    def correct_message(self, item):
        return "Great job!"

    def wrong_message(self, item):
        return f"That's {item}!"

    def not_enough_items_message(self):
        return f"Need at least 2 items in {self.VOICE_DIR}"

    # ===================================================================
    # Shared implementation
    # ===================================================================

    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.voice = VoicePlayer(self.VOICE_DIR)

        self.screen = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT), pygame.SCALED | pygame.RESIZABLE
        )
        self._resize_browser_canvas()
        pygame.display.set_caption(self.TITLE)

        self.font_word = text.SysFont("arial", 40, bold=True)
        self.font_score = text.SysFont("arial", 28, bold=True)
        self.font_feedback = text.SysFont("arial", 44, bold=True)
        self.font_title = text.SysFont("arial", 68, bold=True)
        self.font_subtitle = text.SysFont("arial", 26)
        self.font_icon = text.SysFont("arial", 24, bold=True)
        self.font_milestone = text.SysFont("arial", 40, bold=True)

        self.items = self.load_items()
        if len(self.items) < 2:
            raise RuntimeError(self.not_enough_items_message())

        self.wrong_sound = pygame.mixer.Sound(str(self.SOUNDS_DIR / "wrong.ogg"))

        self.score = 0
        self.streak = 0
        self.current = None
        self.last_item = None
        self.last_wrong = None
        self.buttons = []
        self.revealed = False
        self.feedback_until = 0
        self.feedback_text = ""
        self.feedback_color = self.TEXT_COLOR
        self.milestone_text = ""
        self.milestone_until = 0
        self.particles = []

        self.card_rect = pygame.Rect(0, 0, self.CARD_SIZE, self.CARD_SIZE)
        self.card_rect.centerx = self.WIDTH // 2
        self.card_rect.top = self.CARD_TOP

        palette = self.button_palette()
        self.start_button = AnswerButton(
            (self.WIDTH // 2 - 140, 460, 280, 90), "Start", palette)
        self.pause_button = AnswerButton((self.WIDTH - 90, 20, 60, 50), "II", palette)
        self.resume_button = AnswerButton(
            (self.WIDTH // 2 - 160, 340, 320, 80), "Resume", palette)
        self.quit_button = AnswerButton(
            (self.WIDTH // 2 - 160, 440, 320, 80), "Quit", palette)
        self.home_button = pygame.Rect(20, 20, 60, 50)

        self.init_background()

        self.state = STATE_MENU
        self._pause_remaining = None
        self.quit_requested = False

        self.setup()

    def setup(self):
        """Last step of __init__, for subclass state. Runs after fonts,
        items and layout exist."""

    def button_palette(self):
        return {
            "base": self.BUTTON_COLOR,
            "hover": self.BUTTON_HOVER,
            "correct": self.CORRECT_COLOR,
            "wrong": self.WRONG_COLOR,
        }

    def available_voices(self):
        """Clip stems present on disk. `-pygbag` variants are pygbag's own
        re-encodes of the same clip and must not be offered as items."""
        return {
            p.stem for p in self.VOICE_DIR.glob("*.ogg")
            if not p.stem.endswith("-pygbag")
        }

    def _resize_browser_canvas(self):
        try:
            import platform
        except ImportError:
            return
        if hasattr(platform, "window"):
            try:
                platform.window.window_resize()
            except Exception:
                pass

    # ---- background ---------------------------------------------------

    def init_background(self):
        if self.BACKGROUND == "bubbles":
            self.bg_surface = fx.build_gradient(
                self.WIDTH, self.HEIGHT, self.BG_TOP_COLOR, self.BG_BOTTOM_COLOR)
            self.bubbles = [
                self._make_bubble(initial=True) for _ in range(self.BUBBLE_COUNT)
            ]
        else:
            palette = self.BG_SHAPE_COLORS or self.CONFETTI_COLORS
            self.bg_decorations = [
                {
                    "x": random.uniform(40, self.WIDTH - 40),
                    "y": random.uniform(40, self.HEIGHT - 40),
                    "r": random.randint(*self.BG_SHAPE_RADIUS),
                    "speed": random.uniform(0.4, 1.0),
                    "phase": random.uniform(0, math.tau),
                    "color": random.choice(palette),
                }
                for _ in range(self.BG_SHAPE_COUNT)
            ]

    def _make_bubble(self, initial=False):
        return {
            "x": random.uniform(0, self.WIDTH),
            "y": random.uniform(0, self.HEIGHT) if initial
                 else self.HEIGHT + random.uniform(0, 60),
            "r": random.uniform(*self.BUBBLE_RADIUS),
            "speed": random.uniform(*self.BUBBLE_SPEED),
            "drift": random.uniform(-self.BUBBLE_DRIFT, self.BUBBLE_DRIFT),
            "phase": random.uniform(0, math.tau),
            "color": random.choice(self.BUBBLE_COLORS),
        }

    def update_background(self, dt_ms):
        if self.BACKGROUND != "bubbles":
            return
        dt = dt_ms / 1000
        now = pygame.time.get_ticks() / 1000
        for b in self.bubbles:
            b["y"] -= b["speed"] * dt
            b["x"] += math.sin(now + b["phase"]) * b["drift"] * dt
            if b["y"] < -30:
                b["y"] = self.HEIGHT + random.uniform(0, 40)
                b["x"] = random.uniform(0, self.WIDTH)

    def draw_background(self, now):
        if self.BACKGROUND == "bubbles":
            self.screen.blit(self.bg_surface, (0, 0))
            for b in self.bubbles:
                r = int(b["r"])
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, b["color"], (r, r), r)
                if self.BUBBLE_RING:
                    pygame.draw.circle(s, (255, 255, 255, 130), (r, r), r, width=2)
                self.screen.blit(s, (b["x"] - r, b["y"] - r))
            return

        self.screen.fill(self.BG_COLOR)
        for deco in self.bg_decorations:
            bob = math.sin(now / 900 * deco["speed"] + deco["phase"]) * self.BG_SHAPE_BOB
            r = deco["r"]
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*deco["color"][:3], self.BG_SHAPE_ALPHA), (r, r), r)
            self.screen.blit(surf, (deco["x"] - r, deco["y"] - r + bob))

    # ---- particles ----------------------------------------------------

    def spawn_particles(self, center, now):
        if self.PARTICLES == "confetti":
            self.particles.extend(fx.spawn_confetti(
                center[0], center[1], self.CONFETTI_COLORS,
                count=16 + min(self.streak, 10) * 2))
        else:
            self.particles.extend(fx.spawn_burst(center, now, self.CONFETTI_COLORS))

    def update_particles(self, dt_ms, now):
        if self.PARTICLES == "confetti":
            fx.update_confetti(self.particles, dt_ms, self.GRAVITY)
        elif self.particles:
            self.particles = [p for p in self.particles if p.alive(now)]

    def draw_particles(self, now):
        if self.PARTICLES == "confetti":
            fx.draw_confetti(self.screen, self.particles)
        else:
            fx.draw_burst(self.screen, self.particles, now)

    # ---- state --------------------------------------------------------

    def start_game(self):
        self.state = STATE_PLAYING
        self.new_round()

    def enter_pause(self):
        ticks = pygame.time.get_ticks()
        # Bank whatever is left of the feedback window, so pausing during it
        # does not swallow the round when play resumes.
        self._pause_remaining = (
            (self.feedback_until - ticks) if self.feedback_until > ticks else None
        )
        self.voice.pause()
        self.state = STATE_PAUSED

    def resume_game(self):
        ticks = pygame.time.get_ticks()
        self.feedback_until = (
            ticks + self._pause_remaining if self._pause_remaining else 0
        )
        self.voice.unpause()
        self.state = STATE_PLAYING

    def speak(self, item):
        self.voice.say(self.voice_name(item))

    def choose_round_items(self):
        """Pick the target plus distractors, avoiding an immediate repeat of
        either, then return them in display order."""
        choices = [i for i in self.items if i != self.last_item] or self.items
        self.current = random.choice(choices)
        self.last_item = self.current

        pool = [
            i for i in self.items
            if i != self.current and i != self.last_wrong
        ] or [i for i in self.items if i != self.current]

        wrong = random.sample(pool, min(self.CHOICES - 1, len(pool)))
        self.last_wrong = wrong[0] if wrong else None

        shown = [self.current] + wrong
        random.shuffle(shown)
        return shown

    def button_rects(self, count):
        w = self.BUTTON_W or self.BUTTON_SIZE
        h = self.BUTTON_H or self.BUTTON_SIZE
        total = w * count + self.BUTTON_GAP * (count - 1)
        start_x = (self.WIDTH - total) // 2
        step = w + self.BUTTON_GAP
        return [
            pygame.Rect(start_x + i * step, self.BUTTON_Y, w, h)
            for i in range(count)
        ]

    def new_round(self):
        shown = self.choose_round_items()
        rects = self.button_rects(len(shown))
        self.buttons = [self.make_button(r, v) for r, v in zip(rects, shown)]
        self.button_values = shown

        self.feedback_until = 0
        self.feedback_text = ""
        self.revealed = False
        self.milestone_text = ""
        self.milestone_until = 0

        self.on_new_round()
        self.speak(self.current)

    def on_new_round(self):
        """After the round is dealt and before the clip plays. Games with a
        per-item animation restart it here."""

    def answer(self, button, value):
        """Score one tap and start the feedback window."""
        now = pygame.time.get_ticks()
        target = self.correct_value()
        is_correct = value == target

        for b, v in zip(self.buttons, self.button_values):
            if v == target:
                b.state = "correct"
            elif b is button:
                b.state = "wrong"
            else:
                b.state = "idle"

        self.revealed = True
        self.feedback_until = now + self.FEEDBACK_MS

        if is_correct:
            self.score += 1
            self.streak += 1
            self.feedback_text = self.correct_message(self.current)
            self.feedback_color = self.CORRECT_COLOR
            self.spawn_particles(button.rect.center, now)
            if self.streak >= 3 and self.streak % 3 == 0:
                self.milestone_text = f"{self.streak} in a row!"
                self.milestone_until = self.feedback_until
        else:
            self.streak = 0
            self.wrong_sound.play()
            self.feedback_text = self.wrong_message(self.current)
            self.feedback_color = self.WRONG_COLOR

    # ---- input --------------------------------------------------------

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
            self.speak(self.current)
            return
        # Taps during the feedback pause are ignored, so a child hammering
        # the screen cannot answer the next round by accident.
        if pygame.time.get_ticks() < self.feedback_until:
            return
        for button, value in zip(self.buttons, self.button_values):
            if button.rect.collidepoint(pos):
                self.answer(button, value)
                return

    # ---- frame --------------------------------------------------------

    def update(self, dt_ms):
        now = pygame.time.get_ticks()
        self.update_background(dt_ms)
        self.update_particles(dt_ms, now)
        if self.feedback_until and now >= self.feedback_until:
            self.new_round()

    def draw_menu(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        self.draw_background(now)

        title_surf = self.font_title.render(self.TITLE, True, self.TITLE_COLOR)
        self.screen.blit(title_surf, title_surf.get_rect(center=(self.WIDTH // 2, 220)))

        sub_surf = self.font_subtitle.render(self.SUBTITLE, True, self.TEXT_COLOR)
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(self.WIDTH // 2, 290)))

        self.start_button.draw(self.screen, self.font_word, mouse_pos)

    def draw_card(self, mouse_pos):
        rect = self.card_rect
        border = self.BUTTON_HOVER if rect.collidepoint(mouse_pos) else self.CARD_BORDER
        pygame.draw.rect(self.screen, self.CARD_COLOR, rect, border_radius=28)
        pygame.draw.rect(self.screen, border, rect, width=3, border_radius=28)
        revealed = self.revealed and pygame.time.get_ticks() < self.feedback_until
        self.draw_prompt(self.screen, rect, revealed)

    def draw_milestone(self):
        if pygame.time.get_ticks() >= self.milestone_until:
            return
        banner = self.font_milestone.render(
            self.milestone_text, True, self.MILESTONE_COLOR)
        banner_rect = banner.get_rect(center=(self.WIDTH // 2, 45))
        bg_rect = banner_rect.inflate(50, 24)
        pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, border_radius=18)
        pygame.draw.rect(self.screen, self.MILESTONE_COLOR, bg_rect, 4, border_radius=18)
        self.screen.blit(banner, banner_rect)

    def draw_playing(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        self.draw_background(now)
        self.draw_card(mouse_pos)

        for button in self.buttons:
            button.draw(self.screen, self.font_word, mouse_pos)

        self.draw_particles(now)

        score_surf = self.font_score.render(
            f"Score: {self.score}   Streak: {self.streak}", True, self.SCORE_COLOR)
        self.screen.blit(score_surf, self.SCORE_POS)

        self.pause_button.draw(self.screen, self.font_icon, mouse_pos)
        draw_home_icon(self.screen, self.home_button, self.BUTTON_COLOR,
                       self.home_button.collidepoint(mouse_pos))

        if self.feedback_text and now < self.feedback_until:
            fb = self.font_feedback.render(self.feedback_text, True, self.feedback_color)
            self.screen.blit(
                fb, fb.get_rect(
                    center=(self.WIDTH // 2,
                            self.card_rect.bottom + self.FEEDBACK_OFFSET)))

        if self.milestone_text:
            self.draw_milestone()

    def draw_paused(self):
        mouse_pos = pygame.mouse.get_pos()
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill(self.OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

        paused = self.font_title.render("Paused", True, (255, 255, 255))
        self.screen.blit(paused, paused.get_rect(center=(self.WIDTH // 2, 240)))

        self.resume_button.draw(self.screen, self.font_word, mouse_pos)
        self.quit_button.draw(self.screen, self.font_word, mouse_pos)

    def draw(self):
        if self.state == STATE_MENU:
            self.draw_menu()
        else:
            self.draw_playing()
            if self.state == STATE_PAUSED:
                self.draw_paused()

        pygame.display.flip()

        # A rotation only takes effect through a fresh set_mode, and it has to
        # happen in the running game's own loop - the hub's is not executing.
        resized = display.maintain(self.WIDTH, self.HEIGHT)
        if resized is not None:
            self.screen = resized

    def handle_event(self, event):
        """Return False to stop the loop. Subclasses may extend this."""
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.state == STATE_PLAYING:
                self.enter_pause()
            elif self.state == STATE_PAUSED:
                self.resume_game()
            else:
                return False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == STATE_MENU:
                self.handle_menu_click(event.pos)
            elif self.state == STATE_PLAYING:
                self.handle_click(event.pos)
            elif self.state == STATE_PAUSED:
                self.handle_pause_click(event.pos)
        return True

    async def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt_ms = clock.tick(60)
            for event in pygame.event.get():
                if not self.handle_event(event):
                    running = False
            if self.state == STATE_PLAYING:
                self.update(dt_ms)
            self.draw()
            if self.quit_requested:
                running = False
            await asyncio.sleep(0)

        self.voice.stop()
