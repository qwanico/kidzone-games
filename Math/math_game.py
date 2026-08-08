import math
import random
import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent
VOICE_DIR = BASE_DIR / "voice_cache"
SOUNDS_DIR = BASE_DIR / "sounds"
ASSETS_DIR = BASE_DIR / "assets"

WIDTH, HEIGHT = 900, 700
CARD_SIZE = 360
FEEDBACK_MS = 1600
FRUIT_SIZE = 30

BG_COLOR = (245, 250, 215)
CARD_COLOR = (255, 255, 255)
CARD_BORDER = (210, 225, 165)
SPEAKER_COLOR = (120, 180, 40)
BUTTON_COLOR = (120, 180, 40)
BUTTON_HOVER = (100, 160, 30)
CORRECT_COLOR = (90, 200, 110)
WRONG_COLOR = (230, 90, 90)
TEXT_COLOR = (50, 50, 60)
SCORE_COLOR = (90, 130, 30)
OVERLAY_COLOR = (30, 30, 40, 190)
TITLE_COLOR = (90, 130, 30)
GLOW_COLOR = (255, 210, 90)

CONFETTI_COLORS = [
    (255, 99, 132), (255, 205, 86), (75, 192, 192),
    (54, 162, 235), (153, 102, 255), (255, 159, 64),
]

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"


def load_problems():
    stems = {p.stem for p in VOICE_DIR.glob("*.mp3")}
    problems = []
    for a in range(1, 6):
        for b in range(1, 6):
            if f"{a}_plus_{b}" in stems:
                problems.append((a, b))
    return problems


def fruit_grid_positions(count, area_rect, icon_size):
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
            x = start_x + col * (icon_size + gap)
            positions.append((x, y))
    return positions


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


class Button:
    def __init__(self, rect, value, mode="text"):
        self.rect = pygame.Rect(rect)
        self.value = value
        self.state = "idle"
        self.mode = mode  # "text" or "fruit"

    def draw(self, surface, font, mouse_pos, fruit_icon=None, number_font=None, now=0):
        hovered = self.rect.collidepoint(mouse_pos)

        if self.state == "correct":
            color = CORRECT_COLOR
        elif self.state == "wrong":
            color = WRONG_COLOR
        elif hovered:
            color = BUTTON_HOVER
        else:
            color = BUTTON_COLOR

        draw_rect = self.rect.copy()
        if hovered and self.state == "idle":
            bounce = math.sin(now / 140) * 4
            draw_rect.inflate_ip(6, 6)
            draw_rect.y += int(bounce)

        pygame.draw.rect(surface, color, draw_rect, border_radius=24)
        pygame.draw.rect(surface, (255, 255, 255), draw_rect, width=3, border_radius=24)

        if self.mode == "fruit" and fruit_icon is not None:
            number_surf = number_font.render(str(self.value), True, (255, 255, 255))
            number_rect = number_surf.get_rect(midtop=(draw_rect.centerx, draw_rect.top + 8))
            surface.blit(number_surf, number_rect)

            icon_area = draw_rect.copy()
            icon_area.top = number_rect.bottom + 4
            icon_area.height = max(icon_area.bottom - icon_area.top - 8, fruit_icon.get_height())
            for x, y in fruit_grid_positions(self.value, icon_area, fruit_icon.get_width()):
                surface.blit(fruit_icon, (x, y))
        else:
            text_surf = font.render(str(self.value), True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=draw_rect.center)
            surface.blit(text_surf, text_rect)


def draw_speaker_icon(surface, center, size, color, pulse=0.0):
    x, y = center
    size = size * (1.0 + pulse * 0.08)
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

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Math")

        self.font_word = pygame.font.SysFont("arial", 64, bold=True)
        self.font_score = pygame.font.SysFont("arial", 28, bold=True)
        self.font_feedback = pygame.font.SysFont("arial", 50, bold=True)
        self.font_title = pygame.font.SysFont("arial", 68, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 26)
        self.font_icon = pygame.font.SysFont("arial", 24, bold=True)
        self.font_equation = pygame.font.SysFont("arial", 90, bold=True)
        self.font_number = pygame.font.SysFont("arial", 30, bold=True)

        self.problems = load_problems()
        if len(self.problems) < 2:
            raise RuntimeError("Need at least 2 problems in voice_cache/")

        self.wrong_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.wav"))

        raw_fruit = pygame.image.load(str(ASSETS_DIR / "apple.png")).convert_alpha()
        self.fruit_icon = pygame.transform.smoothscale(raw_fruit, (FRUIT_SIZE, FRUIT_SIZE))

        self.score = 0
        self.streak = 0
        self.last_problem = None
        self.feedback_until = 0
        self.feedback_text = ""
        self.feedback_color = TEXT_COLOR
        self.buttons = []
        self.current_problem = None
        self.current_sum = None
        self.answered = False
        self.particles = []
        self.shake_until = 0
        self.shake_seed = 0.0

        self.card_rect = pygame.Rect(0, 0, CARD_SIZE, CARD_SIZE)
        self.card_rect.centerx = WIDTH // 2
        self.card_rect.top = 60

        self.start_button = Button((WIDTH // 2 - 140, 460, 280, 90), "Start")
        self.pause_button = Button((WIDTH - 90, 20, 60, 50), "II")
        self.resume_button = Button((WIDTH // 2 - 160, 340, 320, 80), "Resume")
        self.quit_button = Button((WIDTH // 2 - 160, 440, 320, 80), "Quit")

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

        self.state = STATE_MENU
        self._pause_remaining = None
        self.quit_requested = False

    def start_game(self):
        self.state = STATE_PLAYING
        self.new_round()

    def enter_pause(self):
        ticks = pygame.time.get_ticks()
        self._pause_remaining = (self.feedback_until - ticks) if self.feedback_until > ticks else None
        pygame.mixer.music.pause()
        self.state = STATE_PAUSED

    def resume_game(self):
        ticks = pygame.time.get_ticks()
        self.feedback_until = ticks + self._pause_remaining if self._pause_remaining else 0
        pygame.mixer.music.unpause()
        self.state = STATE_PLAYING

    def speak(self, problem):
        a, b = problem
        pygame.mixer.music.stop()
        pygame.mixer.music.load(str(VOICE_DIR / f"{a}_plus_{b}.mp3"))
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play()

    def new_round(self):
        choices = [p for p in self.problems if p != self.last_problem] or self.problems
        self.current_problem = random.choice(choices)
        self.last_problem = self.current_problem

        a, b = self.current_problem
        correct = a + b
        self.current_sum = correct

        lo, hi = max(2, correct - 3), min(10, correct + 3)
        wrong_choices = [n for n in range(lo, hi + 1) if n != correct]
        wrong_sum = random.choice(wrong_choices)

        pair = [correct, wrong_sum]
        random.shuffle(pair)

        button_w, button_h = 340, 150
        gap = 40
        total_w = button_w * 2 + gap
        start_x = (WIDTH - total_w) // 2
        y = HEIGHT - 195

        self.buttons = [
            Button((start_x, y, button_w, button_h), pair[0], mode="fruit"),
            Button((start_x + button_w + gap, y, button_w, button_h), pair[1], mode="fruit"),
        ]
        self._button_values = pair

        self.feedback_until = 0
        self.feedback_text = ""
        self.answered = False
        self.particles = []

        self.speak(self.current_problem)

    def handle_menu_click(self, pos):
        if self.start_button.rect.collidepoint(pos):
            self.start_game()

    def handle_pause_click(self, pos):
        if self.resume_button.rect.collidepoint(pos):
            self.resume_game()
        elif self.quit_button.rect.collidepoint(pos):
            self.quit_requested = True

    def handle_click(self, pos):
        if self.pause_button.rect.collidepoint(pos):
            self.enter_pause()
            return

        if self.card_rect.collidepoint(pos):
            self.speak(self.current_problem)
            return

        if pygame.time.get_ticks() < self.feedback_until:
            return

        for button, value in zip(self.buttons, self._button_values):
            if button.rect.collidepoint(pos):
                now = pygame.time.get_ticks()
                is_correct = value == self.current_sum
                for b, v in zip(self.buttons, self._button_values):
                    b.state = "correct" if v == self.current_sum else (
                        "wrong" if b is button else "idle"
                    )

                self.answered = True

                if is_correct:
                    self.score += 1
                    self.streak += 1
                    self.feedback_text = "Great job!"
                    self.feedback_color = CORRECT_COLOR
                    self.particles.extend(spawn_confetti(button.rect.center, now))
                    self.particles.extend(spawn_confetti(self.card_rect.center, now))
                else:
                    self.streak = 0
                    self.wrong_sound.play()
                    a, b = self.current_problem
                    self.feedback_text = f"{a} + {b} = {self.current_sum}!"
                    self.feedback_color = WRONG_COLOR
                    self.shake_until = now + 400
                    self.shake_seed = random.uniform(0, 100)

                self.feedback_until = now + FEEDBACK_MS
                return

    def update(self):
        now = pygame.time.get_ticks()
        if self.particles:
            self.particles = [p for p in self.particles if p.alive(now)]
        if self.feedback_until and now >= self.feedback_until:
            self.new_round()

    def draw_bg_shapes(self, now):
        for shape in self.bg_shapes:
            bob = math.sin(now / 900 * shape["speed"] + shape["phase"]) * 14
            r = shape["r"]
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*shape["color"], 55), (r, r), r)
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

    def draw_menu(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()

        self.draw_bg_shapes(now)

        title = "Math"
        letter_surfs = [self.font_title.render(ch, True, TITLE_COLOR) for ch in title]
        total_w = sum(s.get_width() for s in letter_surfs)
        x = WIDTH // 2 - total_w // 2
        for i, surf in enumerate(letter_surfs):
            bob = math.sin(now / 260 + i * 0.6) * 10
            rect = surf.get_rect(midtop=(x + surf.get_width() // 2, 190 + int(bob)))
            self.screen.blit(surf, rect)
            x += surf.get_width()

        subtitle_surf = self.font_subtitle.render(
            "Listen, then click the answer!", True, TEXT_COLOR
        )
        subtitle_rect = subtitle_surf.get_rect(center=(WIDTH // 2, 290))
        self.screen.blit(subtitle_surf, subtitle_rect)

        self.start_button.draw(self.screen, self.font_word, mouse_pos, now=now)

    def draw_playing(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()

        self.draw_bg_shapes(now)

        card_rect = self.card_rect.copy()
        if now < self.shake_until:
            t = (self.shake_until - now) / 400.0
            offset = math.sin((now + self.shake_seed) / 25) * 10 * t
            card_rect.x += int(offset)

        if not self.answered:
            pulse = (math.sin(now / 260) + 1) / 2
            glow_rect = card_rect.inflate(int(10 + pulse * 10), int(10 + pulse * 10))
            glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(
                glow_surf, (*GLOW_COLOR, int(60 + pulse * 60)),
                glow_surf.get_rect(), border_radius=32,
            )
            self.screen.blit(glow_surf, glow_rect.topleft)

        border_color = BUTTON_HOVER if card_rect.collidepoint(mouse_pos) else CARD_BORDER
        pygame.draw.rect(self.screen, CARD_COLOR, card_rect, border_radius=28)
        pygame.draw.rect(self.screen, border_color, card_rect, width=3, border_radius=28)

        a, b = self.current_problem
        if self.answered and now < self.feedback_until:
            equation_text = f"{a} + {b} = {self.current_sum}"
            equation_color = self.feedback_color
        else:
            equation_text = f"{a} + {b} = ?"
            equation_color = TEXT_COLOR

        eq_surf = self.font_equation.render(equation_text, True, equation_color)
        eq_rect = eq_surf.get_rect(center=(card_rect.centerx, card_rect.centery - 45))
        self.screen.blit(eq_surf, eq_rect)

        speaker_pulse = (math.sin(now / 200) + 1) / 2 if not self.answered else 0.0
        draw_speaker_icon(
            self.screen, (card_rect.centerx, card_rect.centery + 90), CARD_SIZE * 0.28,
            SPEAKER_COLOR, pulse=speaker_pulse,
        )

        for button in self.buttons:
            button.draw(
                self.screen, self.font_word, mouse_pos,
                fruit_icon=self.fruit_icon, number_font=self.font_number, now=now,
            )

        self.draw_particles(now)

        score_text = self.font_score.render(
            f"Score: {self.score}   Streak: {self.streak}", True, SCORE_COLOR
        )
        self.screen.blit(score_text, (24, 20))

        if self.streak >= 2:
            for i in range(min(self.streak, 6)):
                bob = math.sin(now / 180 + i) * 3
                pygame.draw.circle(
                    self.screen, GLOW_COLOR, (26 + i * 18, 58 + int(bob)), 6,
                )

        self.pause_button.draw(self.screen, self.font_icon, mouse_pos, now=now)

        if self.feedback_text and now < self.feedback_until:
            bounce = math.sin(now / 90) * 3
            fb_surf = self.font_feedback.render(self.feedback_text, True, self.feedback_color)
            fb_rect = fb_surf.get_rect(center=(WIDTH // 2, card_rect.bottom + 40 + int(bounce)))
            self.screen.blit(fb_surf, fb_rect)

    def draw_paused(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

        paused_surf = self.font_title.render("Paused", True, (255, 255, 255))
        paused_rect = paused_surf.get_rect(center=(WIDTH // 2, 240))
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

    def run(self):
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

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
