import asyncio
import math
import random
from pathlib import Path

import pygame

try:
    import platform
except ImportError:
    platform = None

BASE_DIR = Path(__file__).parent / "letters_assets"
VOICE_DIR = BASE_DIR / "voice_cache"
SOUNDS_DIR = BASE_DIR / "sounds"

WIDTH, HEIGHT = 900, 700
CARD_SIZE = 360
FEEDBACK_MS = 1600

BG_COLOR = (255, 240, 245)
BG_TOP_COLOR = (255, 246, 249)
BG_BOTTOM_COLOR = (250, 224, 233)
CARD_COLOR = (255, 255, 255)
CARD_BORDER = (230, 200, 210)
SPEAKER_COLOR = (220, 110, 150)
BUTTON_COLOR = (220, 110, 150)
BUTTON_HOVER = (200, 90, 130)
CORRECT_COLOR = (90, 200, 110)
WRONG_COLOR = (230, 90, 90)
TEXT_COLOR = (50, 50, 60)
SCORE_COLOR = (150, 70, 100)
OVERLAY_COLOR = (30, 30, 40, 190)
TITLE_COLOR = (150, 70, 100)
MILESTONE_COLOR = (215, 130, 60)

CONFETTI_COLORS = [
    (240, 130, 170),
    (200, 140, 230),
    (255, 200, 90),
    (255, 255, 255),
    (150, 200, 255),
]

BUBBLE_COLORS = [
    (255, 255, 255, 95),
    (240, 170, 200, 80),
    (220, 180, 235, 80),
]

GRAVITY = 480
MILESTONE_MS = 1300

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"


def load_letters():
    return sorted(p.stem for p in VOICE_DIR.glob("*.ogg") if not p.stem.endswith("-pygbag"))


def build_gradient(width, height, top_color, bottom_color):
    surf = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (width, y))
    return surf


def draw_home_icon(surface, rect, color, hovered=False):
    bg = tuple(min(255, c + 15) for c in color) if hovered else color
    pygame.draw.rect(surface, bg, rect, border_radius=12)
    pygame.draw.rect(surface, (255, 255, 255), rect, width=3, border_radius=12)

    cx, cy = rect.center
    w, h = rect.width, rect.height

    roof_half = w * 0.30
    roof_top_y = cy - h * 0.26
    roof_base_y = cy - h * 0.02

    body_w = w * 0.42
    body_h = h * 0.32
    body_rect = pygame.Rect(0, 0, body_w, body_h)
    body_rect.midtop = (cx, roof_base_y)
    pygame.draw.rect(surface, (255, 255, 255), body_rect, border_radius=2)

    roof_points = [
        (cx - roof_half, roof_base_y),
        (cx, roof_top_y),
        (cx + roof_half, roof_base_y),
    ]
    pygame.draw.polygon(surface, (255, 255, 255), roof_points)


class Button:
    def __init__(self, rect, word):
        self.rect = pygame.Rect(rect)
        self.word = word
        self.state = "idle"

    def draw(self, surface, font, mouse_pos):
        if self.state == "correct":
            color = CORRECT_COLOR
        elif self.state == "wrong":
            color = WRONG_COLOR
        elif self.rect.collidepoint(mouse_pos):
            color = BUTTON_HOVER
        else:
            color = BUTTON_COLOR

        pygame.draw.rect(surface, color, self.rect, border_radius=24)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=3, border_radius=24)

        text_surf = font.render(self.word, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


def draw_speaker_icon(surface, center, size, color):
    x, y = center
    body_w, body_h = size * 0.35, size * 0.5
    body_rect = pygame.Rect(0, 0, body_w, body_h)
    body_rect.center = (x - size * 0.15, y)
    pygame.draw.rect(surface, color, body_rect, border_radius=6)

    cone = [
        (x - size * 0.15 - body_w / 2, y - size * 0.15),
        (x + size * 0.05, y - size * 0.35),
        (x + size * 0.05, y + size * 0.35),
        (x - size * 0.15 - body_w / 2, y + size * 0.15),
    ]
    pygame.draw.polygon(surface, color, cone)

    for i in range(1, 3):
        radius = size * (0.18 + i * 0.14)
        rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        rect.center = (x, y)
        pygame.draw.arc(
            surface, color, rect, -0.5, 0.5, width=5
        )


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.set_reserved(1)
        self.voice_channel = pygame.mixer.Channel(0)
        self.voice_cache = {}

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
        if platform is not None and hasattr(platform, "window"):
            try:
                platform.window.window_resize()
            except Exception:
                pass
        pygame.display.set_caption("Letters")

        self.font_word = pygame.font.SysFont("arial", 64, bold=True)
        self.font_score = pygame.font.SysFont("arial", 28, bold=True)
        self.font_feedback = pygame.font.SysFont("arial", 50, bold=True)
        self.font_title = pygame.font.SysFont("arial", 68, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 26)
        self.font_icon = pygame.font.SysFont("arial", 24, bold=True)
        self.font_reveal = pygame.font.SysFont("arial", 160, bold=True)
        self.font_milestone = pygame.font.SysFont("arial", 40, bold=True)

        self.letters = load_letters()
        if len(self.letters) < 2:
            raise RuntimeError("Need at least 2 letters in voice_cache/")

        self.wrong_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.ogg"))

        self.score = 0
        self.streak = 0
        self.last_letter = None
        self.last_wrong = None
        self.feedback_until = 0
        self.feedback_text = ""
        self.feedback_color = TEXT_COLOR
        self.buttons = []
        self.current_letter = None
        self.reveal_letter = False

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

        # --- decorative background (soft candy-pink bubbles drifting up) ---
        self.bg_surface = build_gradient(WIDTH, HEIGHT, BG_TOP_COLOR, BG_BOTTOM_COLOR)
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
            "r": random.uniform(8, 22),
            "speed": random.uniform(14, 36),
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
            pygame.draw.circle(s, (255, 255, 255, 130), (r, r), r, width=2)
            self.screen.blit(s, (b["x"] - r, b["y"] - r))

    def spawn_particles(self, cx, cy, streak):
        count = 16 + min(streak, 10) * 2
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(110, 300)
            self.particles.append({
                "x": cx,
                "y": cy,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - random.uniform(80, 180),
                "color": random.choice(CONFETTI_COLORS),
                "size": random.randint(4, 8),
                "angle": random.uniform(0, 360),
                "spin": random.uniform(-360, 360),
                "age": 0.0,
                "life": random.uniform(0.6, 1.1),
            })

    def update_particles(self, dt_ms):
        dt = dt_ms / 1000
        for p in self.particles:
            p["age"] += dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += GRAVITY * dt
            p["angle"] += p["spin"] * dt
        self.particles = [p for p in self.particles if p["age"] < p["life"]]

    def draw_particles(self):
        for p in self.particles:
            t = p["age"] / p["life"]
            alpha = max(0, int(255 * (1 - t)))
            size = p["size"] * 2
            piece = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(piece, (*p["color"], alpha), (0, 0, size, size), border_radius=2)
            rotated = pygame.transform.rotate(piece, p["angle"])
            rect = rotated.get_rect(center=(p["x"], p["y"]))
            self.screen.blit(rotated, rect)

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
        self.voice_channel.pause()
        self.state = STATE_PAUSED

    def resume_game(self):
        ticks = pygame.time.get_ticks()
        self.feedback_until = ticks + self._pause_remaining if self._pause_remaining else 0
        self.voice_channel.unpause()
        self.state = STATE_PLAYING

    def speak(self, letter):
        path = str(VOICE_DIR / f"{letter}.ogg")
        if path not in self.voice_cache:
            self.voice_cache[path] = pygame.mixer.Sound(path)
        self.voice_channel.stop()
        self.voice_channel.play(self.voice_cache[path])

    def new_round(self):
        choices = [l for l in self.letters if l != self.last_letter] or self.letters
        self.current_letter = random.choice(choices)
        self.last_letter = self.current_letter

        wrong_choices = [
            l for l in self.letters
            if l != self.current_letter and l != self.last_wrong
        ] or [l for l in self.letters if l != self.current_letter]
        wrong_letter = random.choice(wrong_choices)
        self.last_wrong = wrong_letter

        pair = [self.current_letter, wrong_letter]
        random.shuffle(pair)

        button_w, button_h = 320, 90
        gap = 40
        total_w = button_w * 2 + gap
        start_x = (WIDTH - total_w) // 2
        y = HEIGHT - 160

        self.buttons = [
            Button((start_x, y, button_w, button_h), pair[0]),
            Button((start_x + button_w + gap, y, button_w, button_h), pair[1]),
        ]
        self._button_names = pair

        self.feedback_until = 0
        self.feedback_text = ""
        self.reveal_letter = False

        self.speak(self.current_letter)

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
            self.speak(self.current_letter)
            return

        if pygame.time.get_ticks() < self.feedback_until:
            return

        for button, letter in zip(self.buttons, self._button_names):
            if button.rect.collidepoint(pos):
                is_correct = letter == self.current_letter
                for b, l in zip(self.buttons, self._button_names):
                    b.state = "correct" if l == self.current_letter else (
                        "wrong" if b is button else "idle"
                    )

                self.reveal_letter = True

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
                    self.feedback_text = f"That letter is {self.current_letter}"
                    self.feedback_color = WRONG_COLOR

                self.feedback_until = pygame.time.get_ticks() + FEEDBACK_MS
                return

    def update(self, dt=16):
        self.update_particles(dt)
        if self.feedback_until and pygame.time.get_ticks() >= self.feedback_until:
            self.new_round()

    def draw_menu(self):
        self.draw_background()
        mouse_pos = pygame.mouse.get_pos()

        title_surf = self.font_title.render("Letters", True, TITLE_COLOR)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 220))
        self.screen.blit(title_surf, title_rect)

        subtitle_surf = self.font_subtitle.render(
            "Listen, then click the letter you hear!", True, TEXT_COLOR
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

        if self.reveal_letter and pygame.time.get_ticks() < self.feedback_until:
            letter_surf = self.font_reveal.render(self.current_letter, True, self.feedback_color)
            letter_rect = letter_surf.get_rect(center=card_rect.center)
            self.screen.blit(letter_surf, letter_rect)
        else:
            draw_speaker_icon(self.screen, card_rect.center, CARD_SIZE * 0.5, SPEAKER_COLOR)

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

        self.voice_channel.stop()


if __name__ == "__main__":
    asyncio.run(Game().run())
