import asyncio
import math
import random
from pathlib import Path

import pygame

try:
    import platform
except ImportError:
    platform = None

BASE_DIR = Path(__file__).parent / "simon_pattern_assets"
SOUNDS_DIR = BASE_DIR / "sounds"

WIDTH, HEIGHT = 900, 780
FEEDBACK_MS = 1500
FLASH_ON_MS = 550
FLASH_GAP_MS = 250
PRESS_MS = 260
ROUND_START_LEN = 1

PANEL_SIZE = 220
PANEL_GAP = 24

BG_COLOR = (250, 246, 255)
TEXT_COLOR = (50, 50, 60)
SCORE_COLOR = (110, 70, 140)
TITLE_COLOR = (150, 50, 120)
OVERLAY_COLOR = (30, 30, 40, 190)
CORRECT_COLOR = (90, 200, 110)
WRONG_COLOR = (230, 90, 90)
BUTTON_COLOR = (180, 50, 130)
BUTTON_HOVER = (160, 35, 112)
MILESTONE_GOLD = (215, 150, 20)

CONFETTI_COLORS = [
    (255, 99, 132), (255, 205, 86), (75, 192, 192),
    (54, 162, 235), (153, 102, 255), (255, 159, 64),
]

# Classic Simon layout: green top-left, red top-right, yellow bottom-left, blue bottom-right.
PANEL_DEFS = [
    {"name": "green", "color": (70, 180, 90), "lit": (140, 235, 150)},
    {"name": "red", "color": (215, 70, 70), "lit": (255, 140, 140)},
    {"name": "yellow", "color": (235, 195, 40), "lit": (255, 235, 130)},
    {"name": "blue", "color": (60, 120, 215), "lit": (140, 180, 255)},
]

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"

PHASE_SHOWING = "showing"
PHASE_INPUT = "input"
PHASE_SUCCESS = "success"
PHASE_FAIL = "fail"


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


def spawn_confetti(center, now, count=24):
    particles = []
    for _ in range(count):
        angle = random.uniform(-math.pi * 0.95, -math.pi * 0.05)
        speed = random.uniform(160, 400)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        color = random.choice(CONFETTI_COLORS)
        size = random.randint(5, 9)
        shape = random.choice(["circle", "square"])
        particles.append(Particle(center[0], center[1], vx, vy, color, size, now, 1000, shape))
    return particles


class Button:
    def __init__(self, rect, label):
        self.rect = pygame.Rect(rect)
        self.label = label

    def draw(self, surface, font, mouse_pos, now=0):
        hovered = self.rect.collidepoint(mouse_pos)
        color = BUTTON_HOVER if hovered else BUTTON_COLOR
        draw_rect = self.rect.copy()
        if hovered:
            bounce = math.sin(now / 140) * 4
            draw_rect.inflate_ip(6, 6)
            draw_rect.y += int(bounce)
        pygame.draw.rect(surface, color, draw_rect, border_radius=24)
        pygame.draw.rect(surface, (255, 255, 255), draw_rect, width=3, border_radius=24)
        text_surf = font.render(self.label, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=draw_rect.center)
        surface.blit(text_surf, text_rect)


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


class Panel:
    def __init__(self, index, rect, definition):
        self.index = index
        self.rect = pygame.Rect(rect)
        self.name = definition["name"]
        self.color = definition["color"]
        self.lit_color = definition["lit"]

    def draw(self, surface, mouse_pos, active, pressed, dim, now=0):
        rect = self.rect.copy()
        hovered = (not dim) and rect.collidepoint(mouse_pos)

        if active or pressed:
            color = self.lit_color
            scale = 1.06
        elif hovered:
            color = self.lit_color
            scale = 1.02
        else:
            color = self.color
            scale = 1.0

        draw_rect = rect.inflate(
            int(rect.width * (scale - 1)), int(rect.height * (scale - 1))
        )

        if active or pressed:
            glow_pulse = (math.sin(now / 90) + 1) / 2
            glow_rect = draw_rect.inflate(16 + glow_pulse * 10, 16 + glow_pulse * 10)
            glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(
                glow_surf, (255, 255, 255, int(90 + glow_pulse * 80)),
                glow_surf.get_rect(), border_radius=28,
            )
            surface.blit(glow_surf, glow_rect.topleft)

        alpha = 120 if dim else 255
        panel_surf = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (*color, alpha), panel_surf.get_rect(), border_radius=26)
        pygame.draw.rect(
            panel_surf, (255, 255, 255, alpha), panel_surf.get_rect(), width=4, border_radius=26
        )
        surface.blit(panel_surf, draw_rect.topleft)


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
        if platform is not None and hasattr(platform, "window"):
            try:
                platform.window.window_resize()
            except Exception:
                pass
        pygame.display.set_caption("Simon Pattern")

        self.font_title = pygame.font.SysFont("arial", 64, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 26)
        self.font_word = pygame.font.SysFont("arial", 32, bold=True)
        self.font_icon = pygame.font.SysFont("arial", 24, bold=True)
        self.font_score = pygame.font.SysFont("arial", 28, bold=True)
        self.font_feedback = pygame.font.SysFont("arial", 44, bold=True)

        self.wrong_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.ogg"))

        grid_w = PANEL_SIZE * 2 + PANEL_GAP
        grid_h = PANEL_SIZE * 2 + PANEL_GAP
        origin_x = (WIDTH - grid_w) // 2
        origin_y = 210
        self.panels = []
        for i, definition in enumerate(PANEL_DEFS):
            row, col = divmod(i, 2)
            x = origin_x + col * (PANEL_SIZE + PANEL_GAP)
            y = origin_y + row * (PANEL_SIZE + PANEL_GAP)
            self.panels.append(Panel(i, (x, y, PANEL_SIZE, PANEL_SIZE), definition))

        self.start_button = Button((WIDTH // 2 - 140, origin_y + grid_h + 40, 280, 90), "Start")
        self.pause_button = Button((WIDTH - 90, 20, 60, 50), "II")
        self.home_button = pygame.Rect(20, 20, 60, 50)
        self.resume_button = Button((WIDTH // 2 - 160, HEIGHT // 2 - 40, 320, 80), "Resume")
        self.quit_button = Button((WIDTH // 2 - 160, HEIGHT // 2 + 60, 320, 80), "Quit")

        self.bg_shapes = [
            {
                "x": random.uniform(40, WIDTH - 40),
                "y": random.uniform(40, HEIGHT - 40),
                "r": random.randint(10, 22),
                "speed": random.uniform(0.4, 1.0),
                "phase": random.uniform(0, math.tau),
                "color": random.choice(CONFETTI_COLORS),
            }
            for _ in range(10)
        ]

        self.best = 0
        self.particles = []
        self.quit_requested = False
        self.state = STATE_MENU
        self._pause_remaining = None

        self.sequence = []
        self.phase = PHASE_SHOWING
        self.show_step = 0
        self.show_sub = "on"
        self.timer_until = 0
        self.active_panel = None
        self.pressed_panel = None
        self.press_until = 0
        self.input_index = 0
        self.feedback_text = ""
        self.feedback_color = TEXT_COLOR
        self.milestone_text = ""

    # ---- game flow ----
    def start_game(self):
        self.state = STATE_PLAYING
        self.best = 0
        self.new_sequence(ROUND_START_LEN)

    def new_sequence(self, length):
        self.sequence = [random.randrange(4) for _ in range(length)]
        self.begin_showing()

    def begin_showing(self):
        now = pygame.time.get_ticks()
        self.phase = PHASE_SHOWING
        self.show_step = 0
        self.show_sub = "on"
        self.active_panel = self.sequence[0]
        self.timer_until = now + FLASH_ON_MS
        self.input_index = 0
        self.feedback_text = ""

    def enter_pause(self):
        ticks = pygame.time.get_ticks()
        self._pause_remaining = (self.timer_until - ticks) if self.timer_until > ticks else None
        self.state = STATE_PAUSED

    def resume_game(self):
        ticks = pygame.time.get_ticks()
        if self._pause_remaining:
            self.timer_until = ticks + self._pause_remaining
        self.state = STATE_PLAYING

    # ---- events ----
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

    def handle_playing_click(self, pos):
        if self.home_button.collidepoint(pos):
            self.quit_requested = True
            return

        if self.pause_button.rect.collidepoint(pos):
            self.enter_pause()
            return

        if self.phase != PHASE_INPUT:
            return

        for panel in self.panels:
            if panel.rect.collidepoint(pos):
                self.on_panel_clicked(panel.index)
                return

    def on_panel_clicked(self, index):
        now = pygame.time.get_ticks()
        self.pressed_panel = index
        self.press_until = now + PRESS_MS

        expected = self.sequence[self.input_index]
        if index == expected:
            # Small satisfying burst on every correct tap, not just at the
            # end of the round - makes each press feel rewarding.
            panel = self.panels[index]
            self.particles.extend(spawn_confetti(panel.rect.center, now, count=6))

            self.input_index += 1
            if self.input_index >= len(self.sequence):
                self.round_success(now)
        else:
            self.round_fail(now)

    def round_success(self, now):
        self.phase = PHASE_SUCCESS
        self.best = max(self.best, len(self.sequence))
        self.feedback_text = "Great job!"
        self.feedback_color = CORRECT_COLOR
        for panel in self.panels:
            self.particles.extend(spawn_confetti(panel.rect.center, now, count=8))
        self.particles.extend(spawn_confetti((WIDTH // 2, HEIGHT // 2), now, count=16))
        self.timer_until = now + FEEDBACK_MS

        if len(self.sequence) >= 5 and len(self.sequence) % 5 == 0:
            self.milestone_text = f"{len(self.sequence)} in a row!"
            self.particles.extend(spawn_confetti((WIDTH // 2, HEIGHT // 2), now, count=24))
        else:
            self.milestone_text = ""

    def round_fail(self, now):
        self.phase = PHASE_FAIL
        self.wrong_sound.play()
        self.feedback_text = "Try again!"
        self.feedback_color = WRONG_COLOR
        self.milestone_text = ""
        self.timer_until = now + FEEDBACK_MS

    def update(self):
        now = pygame.time.get_ticks()
        if self.particles:
            self.particles = [p for p in self.particles if p.alive(now)]

        if self.pressed_panel is not None and now >= self.press_until:
            self.pressed_panel = None

        if self.phase == PHASE_SHOWING:
            if now >= self.timer_until:
                if self.show_sub == "on":
                    self.active_panel = None
                    self.show_sub = "off"
                    self.timer_until = now + FLASH_GAP_MS
                else:
                    self.show_step += 1
                    if self.show_step >= len(self.sequence):
                        self.phase = PHASE_INPUT
                        self.active_panel = None
                        self.input_index = 0
                    else:
                        self.active_panel = self.sequence[self.show_step]
                        self.show_sub = "on"
                        self.timer_until = now + FLASH_ON_MS
        elif self.phase == PHASE_SUCCESS:
            if now >= self.timer_until:
                self.new_sequence(len(self.sequence) + 1)
        elif self.phase == PHASE_FAIL:
            if now >= self.timer_until:
                self.new_sequence(ROUND_START_LEN)

    # ---- drawing ----
    def draw_bg_shapes(self, now):
        for shape in self.bg_shapes:
            bob = math.sin(now / 900 * shape["speed"] + shape["phase"]) * 14
            r = shape["r"]
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*shape["color"], 45), (r, r), r)
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

    def draw_milestone(self, text):
        banner = self.font_feedback.render(text, True, MILESTONE_GOLD)
        banner_rect = banner.get_rect(center=(WIDTH // 2, HEIGHT - 40))
        bg_rect = banner_rect.inflate(50, 24)
        pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, border_radius=18)
        pygame.draw.rect(self.screen, MILESTONE_GOLD, bg_rect, 4, border_radius=18)
        self.screen.blit(banner, banner_rect)

    def draw_menu(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)

        title = "Simon Pattern"
        letter_surfs = [self.font_title.render(ch, True, TITLE_COLOR) for ch in title]
        total_w = sum(s.get_width() for s in letter_surfs)
        x = WIDTH // 2 - total_w // 2
        for i, surf in enumerate(letter_surfs):
            bob = math.sin(now / 260 + i * 0.6) * 8
            rect = surf.get_rect(midtop=(x + surf.get_width() // 2, 90 + int(bob)))
            self.screen.blit(surf, rect)
            x += surf.get_width()

        subtitle_surf = self.font_subtitle.render(
            "Watch the pattern, then click it back!", True, TEXT_COLOR
        )
        subtitle_rect = subtitle_surf.get_rect(center=(WIDTH // 2, 165))
        self.screen.blit(subtitle_surf, subtitle_rect)

        pulse_index = int(now / 500) % 4
        for panel in self.panels:
            active = panel.index == pulse_index
            panel.draw(self.screen, mouse_pos, active, False, False, now=now)

        self.start_button.draw(self.screen, self.font_word, mouse_pos, now=now)

    def draw_playing(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)

        dim = self.phase == PHASE_SHOWING
        for panel in self.panels:
            active = panel.index == self.active_panel
            pressed = panel.index == self.pressed_panel
            panel.draw(self.screen, mouse_pos, active, pressed, dim and not active, now=now)

        self.draw_particles(now)

        score_text = self.font_score.render(
            f"Round: {len(self.sequence)}   Best: {self.best}", True, SCORE_COLOR
        )
        self.screen.blit(score_text, (24, 20))

        self.pause_button.draw(self.screen, self.font_icon, mouse_pos, now=now)
        draw_home_icon(self.screen, self.home_button, BUTTON_COLOR)

        status = ""
        if self.phase == PHASE_SHOWING:
            status = "Watch..."
        elif self.phase == PHASE_INPUT:
            status = "Your turn!"
        if status and self.phase in (PHASE_SHOWING, PHASE_INPUT):
            status_surf = self.font_subtitle.render(status, True, TEXT_COLOR)
            status_rect = status_surf.get_rect(center=(WIDTH // 2, 150))
            self.screen.blit(status_surf, status_rect)

        if self.feedback_text and now < self.timer_until:
            bounce = math.sin(now / 90) * 3
            fb_surf = self.font_feedback.render(self.feedback_text, True, self.feedback_color)
            fb_rect = fb_surf.get_rect(center=(WIDTH // 2, 150 + int(bounce)))
            self.screen.blit(fb_surf, fb_rect)

        if self.milestone_text and now < self.timer_until:
            self.draw_milestone(self.milestone_text)

    def draw_paused(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

        paused_surf = self.font_title.render("Paused", True, (255, 255, 255))
        paused_rect = paused_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 140))
        self.screen.blit(paused_surf, paused_rect)

        self.resume_button.draw(self.screen, self.font_word, mouse_pos, now=now)
        self.quit_button.draw(self.screen, self.font_word, mouse_pos, now=now)

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
                        self.handle_playing_click(event.pos)
                    elif self.state == STATE_PAUSED:
                        self.handle_pause_click(event.pos)

            if self.state == STATE_PLAYING:
                self.update()
            self.draw()

            if self.quit_requested:
                running = False

            clock.tick(60)
            await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(Game().run())
