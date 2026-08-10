import asyncio
import math
import random
from pathlib import Path

import pygame

try:
    import platform
except ImportError:
    platform = None

BASE_DIR = Path(__file__).parent / "shapes_assets"
VOICE_DIR = BASE_DIR / "voice_cache"
SOUNDS_DIR = BASE_DIR / "sounds"

WIDTH, HEIGHT = 900, 700
CARD_SIZE = 300
BUTTON_SIZE = 200
BUTTON_GAP = 60
BUTTON_Y = 450
FEEDBACK_MS = 1600

BG_COLOR = (230, 250, 247)
CARD_COLOR = (255, 255, 255)
CARD_BORDER = (180, 225, 218)
SPEAKER_COLOR = (20, 150, 140)
BUTTON_COLOR = (20, 150, 140)
BUTTON_HOVER = (15, 130, 120)
CORRECT_COLOR = (90, 200, 110)
WRONG_COLOR = (230, 90, 90)
TEXT_COLOR = (50, 50, 60)
SCORE_COLOR = (15, 110, 105)
OVERLAY_COLOR = (30, 30, 40, 190)
TITLE_COLOR = (15, 110, 105)
MILESTONE_GOLD = (215, 150, 20)

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"

# Soft, low-alpha shapes drifting behind the game - decorative only, drawn
# with the real draw_shape() so they visually echo what's being taught.
DECOR_SHAPES = ["circle", "square", "triangle", "star", "diamond", "heart"]
DECOR_PALETTE = [(190, 225, 220), (150, 210, 200), (210, 235, 230), (130, 195, 185)]

CONFETTI_COLORS = [
    (255, 99, 132), (255, 205, 86), (75, 192, 192),
    (54, 162, 235), (153, 102, 255), (255, 159, 64),
]


class Particle:
    __slots__ = ("x0", "y0", "vx", "vy", "color", "size", "spawn", "life", "shape")

    def __init__(self, x, y, vx, vy, color, size, spawn, life, shape):
        self.x0 = x
        self.y0 = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.spawn = spawn
        self.life = life
        self.shape = shape

    def pos_at(self, now):
        t = (now - self.spawn) / 1000.0
        x = self.x0 + self.vx * t
        y = self.y0 + self.vy * t + 0.5 * 650 * t * t
        return x, y

    def alive(self, now):
        return now - self.spawn < self.life


def spawn_confetti(center, now, count=18):
    particles = []
    for _ in range(count):
        angle = random.uniform(-math.pi * 0.85, -math.pi * 0.15)
        speed = random.uniform(160, 380)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        color = random.choice(CONFETTI_COLORS)
        size = random.randint(5, 9)
        shape = random.choice(["circle", "square"])
        particles.append(Particle(center[0], center[1], vx, vy, color, size, now, 900, shape))
    return particles


def draw_home_icon(surface, rect, color):
    """Small house icon (triangle roof + rectangle body) on a rounded button."""
    pygame.draw.rect(surface, color, rect, border_radius=12)
    pygame.draw.rect(surface, (255, 255, 255), rect, width=2, border_radius=12)

    cx, cy = rect.center
    w, h = rect.width, rect.height

    roof_half = w * 0.28
    roof_top = (cx, cy - h * 0.26)
    roof_left = (cx - roof_half, cy - h * 0.02)
    roof_right = (cx + roof_half, cy - h * 0.02)
    pygame.draw.polygon(surface, (255, 255, 255), [roof_top, roof_left, roof_right])

    body_w, body_h = w * 0.34, h * 0.30
    body_rect = pygame.Rect(0, 0, body_w, body_h)
    body_rect.midtop = (cx, cy - h * 0.02)
    pygame.draw.rect(surface, (255, 255, 255), body_rect)


def load_shapes():
    return sorted(p.stem for p in VOICE_DIR.glob("*.ogg") if not p.stem.endswith("-pygbag"))


def article(word):
    return "an" if word[:1] in "aeiou" else "a"


def _star_points(cx, cy, outer_r, inner_r, points):
    pts = []
    angle = -math.pi / 2
    step = math.pi / points
    for i in range(points * 2):
        r = outer_r if i % 2 == 0 else inner_r
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        angle += step
    return pts


def _draw_heart(surface, cx, cy, half, color):
    r = half * 0.5
    pygame.draw.circle(surface, color, (int(cx - r), int(cy - r * 0.25)), int(r))
    pygame.draw.circle(surface, color, (int(cx + r), int(cy - r * 0.25)), int(r))
    pts = [
        (cx - half, cy - r * 0.2),
        (cx + half, cy - r * 0.2),
        (cx, cy + half),
    ]
    pygame.draw.polygon(surface, color, pts)


def draw_shape(surface, shape, center, size, color):
    x, y = center
    half = size / 2
    if shape == "circle":
        pygame.draw.circle(surface, color, (int(x), int(y)), int(half))
    elif shape == "square":
        rect = pygame.Rect(0, 0, size, size)
        rect.center = center
        pygame.draw.rect(surface, color, rect, border_radius=int(size * 0.1))
    elif shape == "rectangle":
        w, h = size * 1.3, size * 0.7
        rect = pygame.Rect(0, 0, w, h)
        rect.center = center
        pygame.draw.rect(surface, color, rect, border_radius=int(h * 0.15))
    elif shape == "oval":
        w, h = size * 1.35, size * 0.8
        rect = pygame.Rect(0, 0, w, h)
        rect.center = center
        pygame.draw.ellipse(surface, color, rect)
    elif shape == "triangle":
        pts = [(x, y - half), (x - half, y + half * 0.85), (x + half, y + half * 0.85)]
        pygame.draw.polygon(surface, color, pts)
    elif shape == "diamond":
        pts = [(x, y - half), (x + half * 0.72, y), (x, y + half), (x - half * 0.72, y)]
        pygame.draw.polygon(surface, color, pts)
    elif shape == "star":
        pts = _star_points(x, y, half, half * 0.42, 5)
        pygame.draw.polygon(surface, color, pts)
    elif shape == "heart":
        _draw_heart(surface, x, y, half, color)


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


class ShapeButton(Button):
    def draw_content(self, surface, font, mouse_pos):
        draw_shape(surface, self.value, self.rect.center, self.rect.height * 0.62, (255, 255, 255))


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
        pygame.display.set_caption("Shapes")

        self.font_word = pygame.font.SysFont("arial", 40, bold=True)
        self.font_score = pygame.font.SysFont("arial", 28, bold=True)
        self.font_feedback = pygame.font.SysFont("arial", 44, bold=True)
        self.font_title = pygame.font.SysFont("arial", 68, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 26)
        self.font_icon = pygame.font.SysFont("arial", 24, bold=True)

        self.shapes = load_shapes()
        if len(self.shapes) < 2:
            raise RuntimeError("Need at least 2 shapes in voice_cache/")

        self.wrong_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.ogg"))

        self.score = 0
        self.streak = 0
        self.last_shape = None
        self.last_wrong = None
        self.feedback_until = 0
        self.feedback_text = ""
        self.feedback_color = TEXT_COLOR
        self.buttons = []
        self.current_shape = None
        self.reveal_shape = False
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
                "size": random.randint(18, 34),
                "speed": random.uniform(0.4, 1.0),
                "phase": random.uniform(0, math.tau),
                "shape": random.choice(DECOR_SHAPES),
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
        self.voice_channel.pause()
        self.state = STATE_PAUSED

    def resume_game(self):
        ticks = pygame.time.get_ticks()
        self.feedback_until = ticks + self._pause_remaining if self._pause_remaining else 0
        self.voice_channel.unpause()
        self.state = STATE_PLAYING

    def speak(self, shape):
        path = str(VOICE_DIR / f"{shape}.ogg")
        if path not in self.voice_cache:
            self.voice_cache[path] = pygame.mixer.Sound(path)
        self.voice_channel.stop()
        self.voice_channel.play(self.voice_cache[path])

    def new_round(self):
        choices = [s for s in self.shapes if s != self.last_shape] or self.shapes
        self.current_shape = random.choice(choices)
        self.last_shape = self.current_shape

        wrong_choices = [
            s for s in self.shapes
            if s != self.current_shape and s != self.last_wrong
        ] or [s for s in self.shapes if s != self.current_shape]
        wrong_shape = random.choice(wrong_choices)
        self.last_wrong = wrong_shape

        pair = [self.current_shape, wrong_shape]
        random.shuffle(pair)

        total_w = BUTTON_SIZE * 2 + BUTTON_GAP
        start_x = (WIDTH - total_w) // 2

        self.buttons = [
            ShapeButton((start_x, BUTTON_Y, BUTTON_SIZE, BUTTON_SIZE), pair[0]),
            ShapeButton((start_x + BUTTON_SIZE + BUTTON_GAP, BUTTON_Y, BUTTON_SIZE, BUTTON_SIZE), pair[1]),
        ]
        self._button_values = pair

        self.feedback_until = 0
        self.feedback_text = ""
        self.reveal_shape = False
        self.milestone_text = ""

        self.speak(self.current_shape)

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
            self.speak(self.current_shape)
            return

        if pygame.time.get_ticks() < self.feedback_until:
            return

        for button, shape in zip(self.buttons, self._button_values):
            if button.rect.collidepoint(pos):
                now = pygame.time.get_ticks()
                is_correct = shape == self.current_shape
                for b, s in zip(self.buttons, self._button_values):
                    b.state = "correct" if s == self.current_shape else (
                        "wrong" if b is button else "idle"
                    )

                self.reveal_shape = True

                if is_correct:
                    self.score += 1
                    self.streak += 1
                    self.feedback_text = "Great job!"
                    self.feedback_color = CORRECT_COLOR
                    self.particles.extend(spawn_confetti(button.rect.center, now))
                    if self.streak >= 3 and self.streak % 3 == 0:
                        self.milestone_text = f"{self.streak} in a row!"
                    else:
                        self.milestone_text = ""
                else:
                    self.streak = 0
                    self.wrong_sound.play()
                    self.feedback_text = f"That's {article(self.current_shape)} {self.current_shape}!"
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
            size = deco["size"]
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            draw_shape(surf, deco["shape"], (size, size), size * 1.5, (*deco["color"], 90))
            self.screen.blit(surf, (deco["x"] - size, deco["y"] - size + bob))

    def draw_particles(self):
        for p in self.particles:
            now = pygame.time.get_ticks()
            x, y = p.pos_at(now)
            t = (now - p.spawn) / p.life
            alpha = max(0, int(255 * (1 - t)))
            surf = pygame.Surface((p.size * 2, p.size * 2), pygame.SRCALPHA)
            if p.shape == "circle":
                pygame.draw.circle(surf, (*p.color, alpha), (p.size, p.size), p.size)
            else:
                pygame.draw.rect(surf, (*p.color, alpha), surf.get_rect())
            self.screen.blit(surf, (x - p.size, y - p.size))

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

        title_surf = self.font_title.render("Shapes", True, TITLE_COLOR)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 220))
        self.screen.blit(title_surf, title_rect)

        subtitle_surf = self.font_subtitle.render(
            "Listen, then click the shape you hear!", True, TEXT_COLOR
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

        if self.reveal_shape and pygame.time.get_ticks() < self.feedback_until:
            draw_shape(self.screen, self.current_shape, card_rect.center, CARD_SIZE * 0.62, self.feedback_color)
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

        self.voice_channel.stop()


if __name__ == "__main__":
    asyncio.run(Game().run())
