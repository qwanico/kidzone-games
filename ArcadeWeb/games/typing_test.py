import asyncio
import math
import random
import sys
import time
from pathlib import Path

import pygame

try:
    import platform
except ImportError:
    platform = None

BASE_DIR = Path(__file__).parent / "typing_test_assets"
SOUNDS_DIR = BASE_DIR / "sounds"

WIDTH, HEIGHT = 1000, 700

BG_COLOR = (24, 26, 38)
TEXT_COLOR = (225, 228, 240)
TITLE_COLOR = (120, 220, 255)
SUBTITLE_COLOR = (150, 155, 180)
ACCENT = (100, 220, 190)
ACCENT_DARK = (75, 190, 160)
CARD_COLOR = (36, 39, 56)
CARD_BORDER = (60, 64, 90)
CORRECT_COLOR = (100, 220, 150)
WRONG_COLOR = (255, 100, 110)
WRONG_BG = (80, 40, 45)
PENDING_COLOR = (150, 155, 180)
CURSOR_COLOR = (255, 220, 100)

CONFETTI_COLORS = [
    (255, 99, 132), (255, 205, 86), (75, 192, 192),
    (54, 162, 235), (153, 102, 255), (120, 220, 255),
]

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_RESULTS = "results"

PHRASES = [
    "The quick brown fox jumps over the lazy dog.",
    "Practice makes perfect when you type every day.",
    "Pack my box with five dozen liquid jugs quickly.",
    "A journey of a thousand miles begins with a single step.",
    "Never underestimate the power of a good night's sleep.",
    "The early bird catches the worm but the second mouse gets the cheese.",
    "Programming is the art of telling a computer what to do.",
    "Video games can teach patience, logic, and quick reflexes.",
    "She sells seashells down by the seashore every summer.",
    "Curiosity is the engine of achievement in every field.",
    "The northern lights danced across the frozen midnight sky.",
    "Great things never came from comfort zones or easy choices.",
    "A balanced diet includes fruit in one hand and pizza in the other.",
    "Robots and humans might someday build cities on distant planets.",
    "Music has the power to change how an entire room feels.",
    "The library was silent except for the turning of old pages.",
    "Believe you can and you are already halfway there.",
    "The stormy ocean waves crashed loudly against the rocky cliffs.",
    "Learning to code is like learning a brand new language.",
    "Teamwork divides the task and multiplies the success.",
]


class Particle:
    __slots__ = ("x0", "y0", "vx", "vy", "color", "size", "spawn", "life", "shape")

    def __init__(self, x, y, vx, vy, color, size, spawn, life, shape):
        self.x0, self.y0 = x, y
        self.vx, self.vy = vx, vy
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


def spawn_confetti(center, now, count=36):
    particles = []
    for _ in range(count):
        angle = random.uniform(-math.pi * 0.95, -math.pi * 0.05)
        speed = random.uniform(160, 420)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        color = random.choice(CONFETTI_COLORS)
        size = random.randint(4, 8)
        shape = random.choice(["circle", "square"])
        particles.append(Particle(center[0], center[1], vx, vy, color, size, now, 1100, shape))
    return particles


class Button:
    def __init__(self, rect, label, color=ACCENT, hover=ACCENT_DARK):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.hover = hover

    def draw(self, surface, font, mouse_pos, now=0, text_color=(15, 20, 25)):
        hovered = self.rect.collidepoint(mouse_pos)
        draw_rect = self.rect.copy()
        if hovered:
            bounce = math.sin(now / 140) * 4
            draw_rect.inflate_ip(6, 6)
            draw_rect.y += int(bounce)
        color = self.hover if hovered else self.color
        pygame.draw.rect(surface, color, draw_rect, border_radius=14)
        pygame.draw.rect(surface, (250, 250, 255), draw_rect, width=2, border_radius=14)
        text_surf = font.render(self.label, True, text_color)
        surface.blit(text_surf, text_surf.get_rect(center=draw_rect.center))

    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)


HUD_BG = (40, 44, 58)
HUD_BG_HOVER = (54, 59, 76)
HUD_BORDER = (110, 116, 140)
HUD_ICON = (240, 242, 248)


def draw_home_icon(surface, rect, mouse_pos):
    """Small house icon (triangle roof + rectangle body) on a rounded button."""
    hovered = rect.collidepoint(mouse_pos)
    pygame.draw.rect(surface, HUD_BG_HOVER if hovered else HUD_BG, rect, border_radius=12)
    pygame.draw.rect(surface, HUD_BORDER, rect, width=2, border_radius=12)

    cx, cy = rect.center
    w, h = rect.width, rect.height
    roof_half = w * 0.28
    roof_top = (cx, cy - h * 0.26)
    roof_left = (cx - roof_half, cy - h * 0.02)
    roof_right = (cx + roof_half, cy - h * 0.02)
    pygame.draw.polygon(surface, HUD_ICON, [roof_top, roof_left, roof_right])

    body_w, body_h = w * 0.34, h * 0.30
    body_rect = pygame.Rect(0, 0, body_w, body_h)
    body_rect.midtop = (cx, cy - h * 0.02)
    pygame.draw.rect(surface, HUD_ICON, body_rect)


def draw_pause_icon(surface, rect, mouse_pos):
    """Two-bar pause glyph on a rounded button."""
    hovered = rect.collidepoint(mouse_pos)
    pygame.draw.rect(surface, HUD_BG_HOVER if hovered else HUD_BG, rect, border_radius=12)
    pygame.draw.rect(surface, HUD_BORDER, rect, width=2, border_radius=12)

    cx, cy = rect.center
    bar_w, bar_h = rect.width * 0.14, rect.height * 0.5
    gap = rect.width * 0.13
    for dx in (-gap, gap):
        bar_rect = pygame.Rect(0, 0, bar_w, bar_h)
        bar_rect.center = (cx + dx, cy)
        pygame.draw.rect(surface, HUD_ICON, bar_rect, border_radius=2)


def wrap_phrase(phrase, font, max_width):
    words = phrase.split(" ")
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        if font.size(test)[0] > max_width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self.wrong_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.ogg"))
        except pygame.error:
            self.wrong_sound = None

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
        pygame.display.set_caption("Typing Speed Test")
        if platform is not None and hasattr(platform, "window"):
            try:
                platform.window.window_resize()
            except Exception:
                pass

        self.font_title = pygame.font.SysFont("arial", 58, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 24)
        self.font_button = pygame.font.SysFont("arial", 24, bold=True)
        self.font_icon = pygame.font.SysFont("arial", 20, bold=True)
        self.font_stat = pygame.font.SysFont("arial", 26, bold=True)
        self.font_big = pygame.font.SysFont("arial", 60, bold=True)
        self.font_phrase = pygame.font.SysFont("couriernew,consolas,monospace", 34, bold=True)

        self.start_button = Button((WIDTH // 2 - 140, 460, 280, 90), "Start")
        self.home_button = pygame.Rect(20, 20, 60, 50)
        self.pause_button = pygame.Rect(90, 20, 60, 50)
        self.resume_button = Button((WIDTH // 2 - 160, 340, 320, 80), "Resume")
        self.restart_button = Button((WIDTH // 2 - 160, 440, 320, 80), "Restart")
        self.quit_button = Button((WIDTH // 2 - 160, 540, 320, 80), "Home")
        self.replay_button = Button((WIDTH // 2 - 160, 540, 320, 80), "Try Again")

        self.bg_shapes = [
            {
                "x": random.uniform(30, WIDTH - 30),
                "y": random.uniform(30, HEIGHT - 30),
                "r": random.randint(10, 24),
                "speed": random.uniform(0.4, 1.0),
                "phase": random.uniform(0, math.tau),
                "color": random.choice(CONFETTI_COLORS),
            }
            for _ in range(12)
        ]

        self.state = STATE_MENU
        self.quit_requested = False
        self.particles = []
        self._pause_start_offset = None

        self.new_phrase()

    def new_phrase(self):
        self.phrase = random.choice(PHRASES)
        self.typed = ""
        self.total_typed = 0
        self.total_correct = 0
        self.start_time = None
        self.end_time = None
        self.wpm = 0.0
        self.accuracy = 0.0
        self.particles = []

    def start_game(self):
        self.new_phrase()
        self.state = STATE_PLAYING

    def enter_pause(self):
        if self.start_time is not None and self.end_time is None:
            self._pause_start_offset = time.time() - self.start_time
        self.state = STATE_PAUSED

    def resume_game(self):
        if self._pause_start_offset is not None:
            self.start_time = time.time() - self._pause_start_offset
        self.state = STATE_PLAYING

    def handle_menu_click(self, pos):
        if self.start_button.is_hovered(pos):
            self.start_game()

    def handle_pause_click(self, pos):
        if self.resume_button.is_hovered(pos):
            self.resume_game()
        elif self.restart_button.is_hovered(pos):
            self.start_game()
        elif self.quit_button.is_hovered(pos):
            self.quit_requested = True

    def handle_results_click(self, pos):
        if self.replay_button.is_hovered(pos):
            self.start_game()

    def handle_playing_click(self, pos):
        if self.home_button.collidepoint(pos):
            self.quit_requested = True
            return
        if self.pause_button.collidepoint(pos):
            self.enter_pause()

    def type_char(self, ch):
        if self.end_time is not None:
            return
        if self.start_time is None:
            self.start_time = time.time()

        if len(self.typed) >= len(self.phrase):
            return

        target = self.phrase[len(self.typed)]
        self.total_typed += 1
        if ch == target:
            self.total_correct += 1
        else:
            if self.wrong_sound:
                self.wrong_sound.play()
        self.typed += ch

        if len(self.typed) >= len(self.phrase):
            self.finish()

    def backspace(self):
        if self.end_time is not None:
            return
        if self.typed:
            self.typed = self.typed[:-1]

    def finish(self):
        self.end_time = time.time()
        elapsed_minutes = max((self.end_time - self.start_time) / 60.0, 1 / 600)
        word_count = len(self.phrase) / 5.0
        self.wpm = word_count / elapsed_minutes
        self.accuracy = (self.total_correct / self.total_typed * 100.0) if self.total_typed else 100.0
        self.state = STATE_RESULTS
        now = pygame.time.get_ticks()
        self.particles.extend(spawn_confetti((WIDTH // 2, 300), now))

    def update(self):
        now = pygame.time.get_ticks()
        if self.particles:
            self.particles = [p for p in self.particles if p.alive(now)]

    def draw_bg_shapes(self, now):
        for shape in self.bg_shapes:
            bob = math.sin(now / 900 * shape["speed"] + shape["phase"]) * 14
            r = shape["r"]
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*shape["color"], 40), (r, r), r)
            self.screen.blit(surf, (shape["x"] - r, shape["y"] - r + bob))

    def draw_particles(self, now):
        for p in self.particles:
            x, y = p.pos_at(now)
            t = (now - p.spawn) / p.life
            alpha = max(0, int(255 * (1 - t)))
            surf = pygame.Surface((p.size * 2, p.size * 2), pygame.SRCALPHA)
            if p.shape == "circle":
                pygame.draw.circle(surf, (*p.color, alpha), (p.size, p.size), p.size)
            else:
                pygame.draw.rect(surf, (*p.color, alpha), surf.get_rect())
            self.screen.blit(surf, (x - p.size, y - p.size))

    def draw_title(self, now, y=110, text="Typing Speed Test"):
        letter_surfs = [self.font_title.render(ch, True, TITLE_COLOR) for ch in text]
        total_w = sum(s.get_width() for s in letter_surfs)
        x = WIDTH // 2 - total_w // 2
        for i, surf in enumerate(letter_surfs):
            bob = math.sin(now / 260 + i * 0.6) * 6
            rect = surf.get_rect(midtop=(x + surf.get_width() // 2, y + int(bob)))
            self.screen.blit(surf, rect)
            x += surf.get_width()

    def draw_menu(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)
        self.draw_title(now, 220)
        subtitle_surf = self.font_subtitle.render(
            "Type the phrase as fast and accurately as you can!", True, SUBTITLE_COLOR
        )
        self.screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 320)))
        self.start_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_playing(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)
        self.draw_title(now, 40)

        if self.start_time is not None and self.end_time is None:
            elapsed = time.time() - self.start_time
        else:
            elapsed = 0.0
        timer_surf = self.font_stat.render(f"Time: {elapsed:0.1f}s", True, TEXT_COLOR)
        self.screen.blit(timer_surf, (30, 24))

        progress_surf = self.font_stat.render(
            f"{len(self.typed)}/{len(self.phrase)}", True, ACCENT
        )
        self.screen.blit(progress_surf, progress_surf.get_rect(topright=(WIDTH - 170, 24)))

        card_rect = pygame.Rect(0, 0, 880, 220)
        card_rect.center = (WIDTH // 2, 330)
        pygame.draw.rect(self.screen, CARD_COLOR, card_rect, border_radius=20)
        pygame.draw.rect(self.screen, CARD_BORDER, card_rect, width=2, border_radius=20)

        lines = wrap_phrase(self.phrase, self.font_phrase, card_rect.width - 60)
        line_h = self.font_phrase.get_height() + 10
        total_h = len(lines) * line_h
        start_y = card_rect.centery - total_h // 2

        char_index = 0
        cursor_pos = None
        for li, line in enumerate(lines):
            line_w = sum(self.font_phrase.size(c)[0] for c in line)
            x = card_rect.centerx - line_w // 2
            y = start_y + li * line_h
            for ch in line:
                if char_index < len(self.typed):
                    typed_ch = self.typed[char_index]
                    if typed_ch == ch:
                        color = CORRECT_COLOR
                        bg = None
                    else:
                        color = WRONG_COLOR
                        bg = WRONG_BG
                else:
                    color = PENDING_COLOR
                    bg = None
                ch_surf = self.font_phrase.render(ch, True, color)
                cw = ch_surf.get_width()
                if bg:
                    pygame.draw.rect(self.screen, bg, (x, y, cw, self.font_phrase.get_height()))
                self.screen.blit(ch_surf, (x, y))
                if char_index == len(self.typed) and cursor_pos is None:
                    cursor_pos = (x, y)
                x += cw
                char_index += 1
            if len(self.typed) == char_index and cursor_pos is None and li == len(lines) - 1:
                cursor_pos = (x, y)

        if cursor_pos and self.end_time is None:
            if (now // 500) % 2 == 0:
                cx, cy = cursor_pos
                pygame.draw.rect(self.screen, CURSOR_COLOR, (cx, cy, 3, self.font_phrase.get_height()))

        draw_pause_icon(self.screen, self.pause_button, mouse_pos)
        draw_home_icon(self.screen, self.home_button, mouse_pos)
        hint_surf = self.font_subtitle.render("Backspace to fix a mistake", True, SUBTITLE_COLOR)
        self.screen.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, card_rect.bottom + 40)))

    def draw_paused(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 18, 200))
        self.screen.blit(overlay, (0, 0))
        paused_surf = self.font_title.render("Paused", True, TITLE_COLOR)
        self.screen.blit(paused_surf, paused_surf.get_rect(center=(WIDTH // 2, 240)))
        self.resume_button.draw(self.screen, self.font_button, mouse_pos, now=now)
        self.restart_button.draw(self.screen, self.font_button, mouse_pos, now=now)
        self.quit_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_results(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)
        self.draw_title(now, 140, "Results")

        bounce = math.sin(now / 200) * 6
        wpm_surf = self.font_big.render(f"{self.wpm:0.0f} WPM", True, ACCENT)
        self.screen.blit(wpm_surf, wpm_surf.get_rect(center=(WIDTH // 2, 290 + int(bounce))))

        acc_color = CORRECT_COLOR if self.accuracy >= 90 else (WRONG_COLOR if self.accuracy < 70 else TITLE_COLOR)
        acc_surf = self.font_stat.render(f"Accuracy: {self.accuracy:0.1f}%", True, acc_color)
        self.screen.blit(acc_surf, acc_surf.get_rect(center=(WIDTH // 2, 370)))

        elapsed = (self.end_time - self.start_time) if (self.start_time and self.end_time) else 0
        detail_surf = self.font_subtitle.render(
            f"{len(self.phrase)} characters in {elapsed:0.1f}s", True, SUBTITLE_COLOR
        )
        self.screen.blit(detail_surf, detail_surf.get_rect(center=(WIDTH // 2, 415)))

        self.draw_particles(now)
        self.replay_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw(self):
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_PLAYING:
            self.draw_playing()
        elif self.state == STATE_PAUSED:
            self.draw_playing()
            self.draw_paused()
        elif self.state == STATE_RESULTS:
            self.draw_results()
        pygame.display.flip()

    async def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == STATE_PLAYING:
                            self.enter_pause()
                        elif self.state == STATE_PAUSED:
                            self.resume_game()
                        else:
                            running = False
                    elif self.state == STATE_PLAYING:
                        if event.key == pygame.K_BACKSPACE:
                            self.backspace()
                        elif event.unicode and event.unicode.isprintable():
                            self.type_char(event.unicode)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == STATE_MENU:
                        self.handle_menu_click(event.pos)
                    elif self.state == STATE_PLAYING:
                        self.handle_playing_click(event.pos)
                    elif self.state == STATE_PAUSED:
                        self.handle_pause_click(event.pos)
                    elif self.state == STATE_RESULTS:
                        self.handle_results_click(event.pos)

            self.update()
            self.draw()

            if self.quit_requested:
                running = False

            clock.tick(60)
            await asyncio.sleep(0)


async def run():
    await Game().run()


if __name__ == "__main__":
    asyncio.run(run())
