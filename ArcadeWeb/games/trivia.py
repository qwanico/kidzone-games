import asyncio
import math
import random
import sys
from pathlib import Path

import pygame

try:
    import platform
except ImportError:
    platform = None

BASE_DIR = Path(__file__).parent / "trivia_assets"
SOUNDS_DIR = BASE_DIR / "sounds"

WIDTH, HEIGHT = 1000, 750

BG_COLOR = (24, 26, 38)
TEXT_COLOR = (225, 228, 240)
TITLE_COLOR = (120, 220, 255)
SUBTITLE_COLOR = (150, 155, 180)
ACCENT = (170, 130, 255)
ACCENT_DARK = (140, 100, 220)
CARD_COLOR = (36, 39, 56)
CARD_BORDER = (60, 64, 90)
CORRECT_COLOR = (100, 220, 150)
WRONG_COLOR = (255, 100, 110)
CATEGORY_COLOR = (255, 190, 100)

CONFETTI_COLORS = [
    (255, 99, 132), (255, 205, 86), (75, 192, 192),
    (54, 162, 235), (153, 102, 255), (120, 220, 255),
]

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_RESULTS = "results"

FEEDBACK_MS = 1400

QUESTIONS = [
    {"category": "Science", "q": "What planet is known as the Red Planet?",
     "choices": ["Venus", "Mars", "Jupiter", "Saturn"], "answer": 1},
    {"category": "Science", "q": "What gas do plants absorb from the air?",
     "choices": ["Oxygen", "Nitrogen", "Carbon Dioxide", "Helium"], "answer": 2},
    {"category": "Science", "q": "How many bones are in the adult human body?",
     "choices": ["206", "150", "300", "180"], "answer": 0},
    {"category": "Science", "q": "What is the chemical symbol for gold?",
     "choices": ["Ag", "Au", "Gd", "Go"], "answer": 1},
    {"category": "Science", "q": "What force pulls objects toward Earth?",
     "choices": ["Magnetism", "Friction", "Gravity", "Tension"], "answer": 2},
    {"category": "Geography", "q": "What is the capital of France?",
     "choices": ["Berlin", "Madrid", "Paris", "Rome"], "answer": 2},
    {"category": "Geography", "q": "Which is the largest ocean on Earth?",
     "choices": ["Atlantic", "Indian", "Arctic", "Pacific"], "answer": 3},
    {"category": "Geography", "q": "Which continent is the Sahara Desert located on?",
     "choices": ["Asia", "Africa", "Australia", "South America"], "answer": 1},
    {"category": "Geography", "q": "What is the longest river in the world?",
     "choices": ["Amazon", "Nile", "Yangtze", "Mississippi"], "answer": 1},
    {"category": "Geography", "q": "Mount Everest is located in which mountain range?",
     "choices": ["Andes", "Alps", "Himalayas", "Rockies"], "answer": 2},
    {"category": "History", "q": "Who was the first President of the United States?",
     "choices": ["Abraham Lincoln", "George Washington", "Thomas Jefferson", "John Adams"], "answer": 1},
    {"category": "History", "q": "In which year did World War II end?",
     "choices": ["1943", "1945", "1948", "1950"], "answer": 1},
    {"category": "History", "q": "The ancient pyramids are located in which country?",
     "choices": ["Mexico", "Greece", "Egypt", "China"], "answer": 2},
    {"category": "History", "q": "Who painted the Mona Lisa?",
     "choices": ["Picasso", "Van Gogh", "Da Vinci", "Michelangelo"], "answer": 2},
    {"category": "Pop Culture", "q": "In Minecraft, what do you use to craft tools?",
     "choices": ["A crafting table", "A furnace", "A chest", "A bed"], "answer": 0},
    {"category": "Pop Culture", "q": "What is the name of the wizarding school in Harry Potter?",
     "choices": ["Hogwarts", "Camelot", "Narnia", "Neverland"], "answer": 0},
    {"category": "Pop Culture", "q": "Which superhero is also known as the 'Man of Steel'?",
     "choices": ["Batman", "Superman", "Iron Man", "Thor"], "answer": 1},
    {"category": "Pop Culture", "q": "In Pokemon, what type is super effective against Water?",
     "choices": ["Fire", "Grass", "Electric", "Ice"], "answer": 1},
    {"category": "Logic", "q": "What is 12 x 8?",
     "choices": ["86", "96", "106", "108"], "answer": 1},
    {"category": "Logic", "q": "If a triangle has three equal sides, it is called...",
     "choices": ["Scalene", "Isosceles", "Equilateral", "Right"], "answer": 2},
    {"category": "Logic", "q": "What is the next number in the sequence: 2, 4, 8, 16, ?",
     "choices": ["18", "24", "32", "20"], "answer": 2},
    {"category": "Logic", "q": "How many sides does a hexagon have?",
     "choices": ["5", "6", "7", "8"], "answer": 1},
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


def spawn_confetti(center, now, count=30):
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
        self.state = "idle"

    def draw(self, surface, font, mouse_pos, now=0, text_color=(20, 20, 30)):
        hovered = self.rect.collidepoint(mouse_pos)
        if self.state == "correct":
            color = CORRECT_COLOR
        elif self.state == "wrong":
            color = WRONG_COLOR
        elif hovered:
            color = self.hover
        else:
            color = self.color

        draw_rect = self.rect.copy()
        if hovered and self.state == "idle":
            bounce = math.sin(now / 140) * 4
            draw_rect.inflate_ip(6, 6)
            draw_rect.y += int(bounce)

        pygame.draw.rect(surface, color, draw_rect, border_radius=16)
        pygame.draw.rect(surface, (250, 250, 255), draw_rect, width=2, border_radius=16)
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


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self.wrong_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.ogg"))
        except pygame.error:
            self.wrong_sound = None

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
        pygame.display.set_caption("Trivia Quiz")
        if platform is not None and hasattr(platform, "window"):
            try:
                platform.window.window_resize()
            except Exception:
                pass

        self.font_title = pygame.font.SysFont("arial", 60, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 24)
        self.font_button = pygame.font.SysFont("arial", 24, bold=True)
        self.font_icon = pygame.font.SysFont("arial", 20, bold=True)
        self.font_question = pygame.font.SysFont("arial", 32, bold=True)
        self.font_category = pygame.font.SysFont("arial", 20, bold=True)
        self.font_stat = pygame.font.SysFont("arial", 26, bold=True)
        self.font_big = pygame.font.SysFont("arial", 52, bold=True)
        self.font_answer = pygame.font.SysFont("arial", 24)

        self.start_button = Button((WIDTH // 2 - 140, 460, 280, 90), "Start")
        self.home_button = pygame.Rect(20, 20, 60, 50)
        self.pause_button = pygame.Rect(90, 20, 60, 50)
        self.resume_button = Button((WIDTH // 2 - 160, 340, 320, 80), "Resume")
        self.restart_button = Button((WIDTH // 2 - 160, 440, 320, 80), "Restart")
        self.quit_button = Button((WIDTH // 2 - 160, 540, 320, 80), "Home")
        self.replay_button = Button((WIDTH // 2 - 160, 520, 320, 80), "Play Again")

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
        self.shake_until = 0
        self.shake_seed = 0.0
        self._pause_started_at = None

        self.setup_round()

    def setup_round(self):
        self.order = list(range(len(QUESTIONS)))
        random.shuffle(self.order)
        self.q_index = 0
        self.score = 0
        self.answered = False
        self.feedback_until = 0
        self.particles = []
        self.answer_buttons = []
        self.correct_choice_index = None

    def start_game(self):
        self.setup_round()
        self.state = STATE_PLAYING
        self.load_question()

    def load_question(self):
        q = QUESTIONS[self.order[self.q_index]]
        indices = list(range(4))
        random.shuffle(indices)
        self.correct_choice_index = indices.index(q["answer"])
        self.current_choices = [q["choices"][i] for i in indices]
        self.current_q = q

        self.answer_buttons = []
        col_w, row_h = 440, 90
        gap_x, gap_y = 40, 24
        start_x = WIDTH // 2 - (col_w * 2 + gap_x) // 2
        start_y = 420
        for i in range(4):
            row, col = divmod(i, 2)
            x = start_x + col * (col_w + gap_x)
            y = start_y + row * (row_h + gap_y)
            self.answer_buttons.append(Button((x, y, col_w, row_h), self.current_choices[i]))

        self.answered = False
        self.feedback_until = 0

    def enter_pause(self):
        self._pause_started_at = pygame.time.get_ticks()
        self.state = STATE_PAUSED

    def resume_game(self):
        if self._pause_started_at is not None:
            # Shift any absolute-tick deadlines forward by however long we
            # were paused, so the per-question feedback timer (and the wrong
            # -answer shake) can't expire "while paused" and unfairly jump
            # ahead the instant play resumes.
            paused_for = pygame.time.get_ticks() - self._pause_started_at
            if self.feedback_until:
                self.feedback_until += paused_for
            if self.shake_until:
                self.shake_until += paused_for
            self._pause_started_at = None
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
            return
        if self.answered:
            return
        for i, button in enumerate(self.answer_buttons):
            if button.is_hovered(pos):
                self.answer(i)
                return

    def answer(self, index):
        now = pygame.time.get_ticks()
        self.answered = True
        for i, b in enumerate(self.answer_buttons):
            if i == self.correct_choice_index:
                b.state = "correct"
            elif i == index:
                b.state = "wrong"
            else:
                b.state = "idle"

        if index == self.correct_choice_index:
            self.score += 1
            self.particles.extend(spawn_confetti(self.answer_buttons[index].rect.center, now))
        else:
            if self.wrong_sound:
                self.wrong_sound.play()
            self.shake_until = now + 400
            self.shake_seed = random.uniform(0, 100)

        self.feedback_until = now + FEEDBACK_MS

    def update(self):
        now = pygame.time.get_ticks()
        if self.particles:
            self.particles = [p for p in self.particles if p.alive(now)]
        if self.state == STATE_PLAYING and self.answered and now >= self.feedback_until:
            self.q_index += 1
            if self.q_index >= len(self.order):
                self.state = STATE_RESULTS
            else:
                self.load_question()

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

    def draw_title(self, now, y=110, text="Trivia Quiz"):
        letter_surfs = [self.font_title.render(ch, True, TITLE_COLOR) for ch in text]
        total_w = sum(s.get_width() for s in letter_surfs)
        x = WIDTH // 2 - total_w // 2
        for i, surf in enumerate(letter_surfs):
            bob = math.sin(now / 260 + i * 0.6) * 8
            rect = surf.get_rect(midtop=(x + surf.get_width() // 2, y + int(bob)))
            self.screen.blit(surf, rect)
            x += surf.get_width()

    def draw_menu(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)
        self.draw_title(now, 210)
        subtitle_surf = self.font_subtitle.render(
            f"{len(QUESTIONS)} questions. How many can you get right?", True, SUBTITLE_COLOR
        )
        self.screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 310)))
        self.start_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def wrap_text(self, text, font, max_width):
        words = text.split(" ")
        lines = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if font.size(test)[0] > max_width and current:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)
        return lines

    def draw_playing(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)

        progress_surf = self.font_stat.render(
            f"Question {self.q_index + 1}/{len(self.order)}", True, SUBTITLE_COLOR
        )
        self.screen.blit(progress_surf, (30, 24))

        score_surf = self.font_stat.render(f"Score: {self.score}", True, ACCENT)
        self.screen.blit(score_surf, score_surf.get_rect(topright=(WIDTH - 170, 24)))

        cat_surf = self.font_category.render(self.current_q["category"].upper(), True, CATEGORY_COLOR)
        self.screen.blit(cat_surf, cat_surf.get_rect(center=(WIDTH // 2, 120)))

        card_rect = pygame.Rect(0, 0, 880, 190)
        card_rect.center = (WIDTH // 2, 220)
        if now < self.shake_until:
            t = (self.shake_until - now) / 400.0
            offset = math.sin((now + self.shake_seed) / 25) * 10 * t
            card_rect.x += int(offset)

        pygame.draw.rect(self.screen, CARD_COLOR, card_rect, border_radius=20)
        pygame.draw.rect(self.screen, CARD_BORDER, card_rect, width=2, border_radius=20)

        lines = self.wrap_text(self.current_q["q"], self.font_question, card_rect.width - 60)
        total_h = len(lines) * 40
        start_y = card_rect.centery - total_h // 2
        for i, line in enumerate(lines):
            line_surf = self.font_question.render(line, True, TEXT_COLOR)
            self.screen.blit(line_surf, line_surf.get_rect(center=(card_rect.centerx, start_y + i * 40)))

        for button in self.answer_buttons:
            button.draw(self.screen, self.font_answer, mouse_pos, now=now)

        self.draw_particles(now)
        draw_pause_icon(self.screen, self.pause_button, mouse_pos)
        draw_home_icon(self.screen, self.home_button, mouse_pos)

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
        self.draw_title(now, 160, "Results")

        pct = int(100 * self.score / len(self.order)) if self.order else 0
        bounce = math.sin(now / 200) * 6
        score_surf = self.font_big.render(
            f"{self.score} / {len(self.order)}", True, CORRECT_COLOR if pct >= 50 else WRONG_COLOR
        )
        self.screen.blit(score_surf, score_surf.get_rect(center=(WIDTH // 2, 300 + int(bounce))))

        pct_surf = self.font_subtitle.render(f"{pct}% correct", True, SUBTITLE_COLOR)
        self.screen.blit(pct_surf, pct_surf.get_rect(center=(WIDTH // 2, 360)))

        if pct >= 80:
            msg = "Outstanding!"
        elif pct >= 50:
            msg = "Nice work!"
        else:
            msg = "Keep practicing!"
        msg_surf = self.font_question.render(msg, True, TEXT_COLOR)
        self.screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH // 2, 410)))

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
