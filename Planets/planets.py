import asyncio
import random
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent
SOUNDS_DIR = BASE_DIR / "sounds"
IMAGES_DIR = BASE_DIR / "images"

WIDTH, HEIGHT = 900, 700
FEEDBACK_MS = 700

BG_COLOR = (8, 10, 30)
TEXT_COLOR = (230, 230, 245)
TITLE_COLOR = (200, 210, 255)
SUBTITLE_COLOR = (170, 180, 220)
SCORE_COLOR = (170, 180, 220)
BUTTON_COLOR = (90, 100, 200)
BUTTON_HOVER = (110, 120, 220)
CORRECT_COLOR = (90, 200, 130)
WRONG_COLOR = (230, 90, 90)
SLOT_COLOR = (60, 65, 100)
SLOT_SELECTABLE = (120, 130, 200)
SUN_COLOR = (255, 200, 70)
SUN_GLOW = (255, 220, 130)

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_WIN = "win"

PLANETS = [
    {"name": "Mercury", "file": "mercury.png", "radius": 14},
    {"name": "Venus", "file": "venus.png", "radius": 19},
    {"name": "Earth", "file": "earth.png", "radius": 20},
    {"name": "Mars", "file": "mars.png", "radius": 16},
    {"name": "Jupiter", "file": "jupiter.png", "radius": 34},
    {"name": "Saturn", "file": "saturn.png", "radius": 30},
    {"name": "Uranus", "file": "uranus.png", "radius": 23},
    {"name": "Neptune", "file": "neptune.png", "radius": 23},
]


TRAY_DISPLAY_H = 78
TRAY_MAX_W = 190
SLOT_DISPLAY_H = 60
SLOT_MAX_W = 85
WIN_DISPLAY_H = 46
WIN_MAX_W = 70


def load_planet_images():
    for planet in PLANETS:
        planet["image"] = pygame.image.load(str(IMAGES_DIR / planet["file"])).convert_alpha()


def planet_render_size(planet, height, max_width=None):
    img = planet["image"]
    scale = height / img.get_height()
    width = img.get_width() * scale
    if max_width is not None and width > max_width:
        scale = max_width / img.get_width()
        width = max_width
        height = img.get_height() * scale
    return width, height


def draw_planet(surface, center, planet, height, max_width=None):
    img = planet["image"]
    width, actual_height = planet_render_size(planet, height, max_width)
    scaled = pygame.transform.smoothscale(img, (max(1, int(width)), max(1, int(actual_height))))
    surface.blit(scaled, scaled.get_rect(center=center))

SUN_POS = (60, 210)
SLOT_Y = 210
SLOT_LEFT = 190
SLOT_RIGHT = 860
SLOT_XS = [
    SLOT_LEFT + i * (SLOT_RIGHT - SLOT_LEFT) / (len(PLANETS) - 1)
    for i in range(len(PLANETS))
]

TRAY_COLS = 4
TRAY_TOP = 430
TRAY_ROW_GAP = 140
TRAY_LEFT = 130
TRAY_RIGHT = 770


def tray_pos(index):
    col = index % TRAY_COLS
    row = index // TRAY_COLS
    x = TRAY_LEFT + col * (TRAY_RIGHT - TRAY_LEFT) / (TRAY_COLS - 1)
    y = TRAY_TOP + row * TRAY_ROW_GAP
    return x, y


def make_starfield():
    surf = pygame.Surface((WIDTH, HEIGHT))
    surf.fill(BG_COLOR)
    rng = random.Random(7)
    for _ in range(160):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, HEIGHT)
        size = rng.choice([1, 1, 1, 2])
        brightness = rng.randint(120, 255)
        pygame.draw.circle(surf, (brightness, brightness, min(255, brightness + 20)), (x, y), size)
    for _ in range(3):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, HEIGHT)
        glow = pygame.Surface((90, 90), pygame.SRCALPHA)
        pygame.draw.circle(glow, (120, 90, 200, 35), (45, 45), 45)
        surf.blit(glow, (x - 45, y - 45))
    return surf


class Button:
    def __init__(self, rect, label):
        self.rect = pygame.Rect(rect)
        self.label = label

    def draw(self, surface, font, mouse_pos, color=BUTTON_COLOR, hover=BUTTON_HOVER):
        c = hover if self.rect.collidepoint(mouse_pos) else color
        pygame.draw.rect(surface, c, self.rect, border_radius=20)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=3, border_radius=20)
        text_surf = font.render(self.label, True, (255, 255, 255))
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Planets")

        self.font_title = pygame.font.SysFont("arial", 64, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 24)
        self.font_word = pygame.font.SysFont("arial", 30, bold=True)
        self.font_label = pygame.font.SysFont("arial", 18, bold=True)
        self.font_small_label = pygame.font.SysFont("arial", 16, bold=True)
        self.font_score = pygame.font.SysFont("arial", 24, bold=True)

        self.starfield = make_starfield()
        load_planet_images()

        self.wrong_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.wav"))

        self.start_button = Button((WIDTH // 2 - 140, 460, 280, 90), "Start")
        self.menu_button = Button((WIDTH - 150, 20, 130, 50), "Menu")
        self.play_again_button = Button((WIDTH // 2 - 300, 500, 280, 80), "Play Again")
        self.win_menu_button = Button((WIDTH // 2 + 20, 500, 280, 80), "Menu")

        self.state = STATE_MENU
        self.quit_requested = False

    def start_game(self):
        self.state = STATE_PLAYING
        order = list(range(len(PLANETS)))
        random.shuffle(order)
        self.tray = [dict(PLANETS[i], order=i + 1) for i in order]
        self.placed = {}
        self.selected = None
        self.feedback_until = 0
        self.feedback_slot = None
        self.feedback_color = None

    def handle_menu_click(self, pos):
        if self.start_button.rect.collidepoint(pos):
            self.start_game()

    def handle_win_click(self, pos):
        if self.play_again_button.rect.collidepoint(pos):
            self.start_game()
        elif self.win_menu_button.rect.collidepoint(pos):
            self.quit_requested = True

    def handle_playing_click(self, pos):
        if self.menu_button.rect.collidepoint(pos):
            self.quit_requested = True
            return

        if pygame.time.get_ticks() < self.feedback_until:
            return

        for i, planet in enumerate(self.tray):
            tx, ty = tray_pos(i)
            if (pos[0] - tx) ** 2 + (pos[1] - ty) ** 2 <= 45 ** 2:
                self.selected = None if self.selected is planet else planet
                return

        for order_index, sx in enumerate(SLOT_XS, start=1):
            if order_index in self.placed:
                continue
            if (pos[0] - sx) ** 2 + (pos[1] - SLOT_Y) ** 2 <= 45 ** 2:
                if self.selected is None:
                    return
                if self.selected["order"] == order_index:
                    self.placed[order_index] = self.selected
                    self.tray.remove(self.selected)
                    self.selected = None
                    if len(self.placed) == len(PLANETS):
                        self.state = STATE_WIN
                else:
                    self.feedback_until = pygame.time.get_ticks() + FEEDBACK_MS
                    self.feedback_slot = order_index
                    self.feedback_color = WRONG_COLOR
                    self.wrong_sound.play()
                    self.selected = None
                return

    def draw_menu(self):
        self.screen.blit(self.starfield, (0, 0))
        mouse_pos = pygame.mouse.get_pos()

        title_surf = self.font_title.render("Planets", True, TITLE_COLOR)
        self.screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 220)))

        subtitle_surf = self.font_subtitle.render(
            "Put the planets in order, starting from the Sun!", True, SUBTITLE_COLOR
        )
        self.screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 290)))

        self.start_button.draw(self.screen, self.font_word, mouse_pos)

    def draw_playing(self):
        self.screen.blit(self.starfield, (0, 0))
        mouse_pos = pygame.mouse.get_pos()

        pygame.draw.line(
            self.screen, (40, 45, 80), (SUN_POS[0] + 40, SLOT_Y), (SLOT_XS[-1], SLOT_Y), 3
        )

        glow = pygame.Surface((140, 140), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*SUN_GLOW, 70), (70, 70), 70)
        self.screen.blit(glow, (SUN_POS[0] - 70, SUN_POS[1] - 70))
        pygame.draw.circle(self.screen, SUN_COLOR, SUN_POS, 40)

        for order_index, sx in enumerate(SLOT_XS, start=1):
            if order_index in self.placed:
                planet = self.placed[order_index]
                draw_planet(self.screen, (sx, SLOT_Y), planet, SLOT_DISPLAY_H, SLOT_MAX_W)
                label = self.font_small_label.render(planet["name"], True, TEXT_COLOR)
                self.screen.blit(label, label.get_rect(center=(sx, SLOT_Y + 55)))
                continue

            if self.feedback_slot == order_index and pygame.time.get_ticks() < self.feedback_until:
                ring_color = self.feedback_color
            elif self.selected is not None:
                ring_color = SLOT_SELECTABLE
            else:
                ring_color = SLOT_COLOR
            pygame.draw.circle(self.screen, ring_color, (int(sx), SLOT_Y), 32, width=4)
            num_surf = self.font_label.render(str(order_index), True, ring_color)
            self.screen.blit(num_surf, num_surf.get_rect(center=(sx, SLOT_Y)))

        for i, planet in enumerate(self.tray):
            tx, ty = tray_pos(i)
            width, height = planet_render_size(planet, TRAY_DISPLAY_H, TRAY_MAX_W)
            hovered = (mouse_pos[0] - tx) ** 2 + (mouse_pos[1] - ty) ** 2 <= 45 ** 2
            if planet is self.selected:
                ring_rect = pygame.Rect(0, 0, width + 20, height + 20)
                ring_rect.center = (tx, ty)
                pygame.draw.ellipse(self.screen, (255, 255, 255), ring_rect, width=3)
            elif hovered:
                ring_rect = pygame.Rect(0, 0, width + 16, height + 16)
                ring_rect.center = (tx, ty)
                pygame.draw.ellipse(self.screen, (150, 160, 210), ring_rect, width=2)
            draw_planet(self.screen, (tx, ty), planet, TRAY_DISPLAY_H, TRAY_MAX_W)
            label = self.font_small_label.render(planet["name"], True, TEXT_COLOR)
            self.screen.blit(label, label.get_rect(center=(tx, ty + height / 2 + 20)))

        score_text = self.font_score.render(
            f"Placed: {len(self.placed)} / {len(PLANETS)}", True, SCORE_COLOR
        )
        self.screen.blit(score_text, (24, 20))

        self.menu_button.draw(self.screen, self.font_label, mouse_pos)

    def draw_win(self):
        self.screen.blit(self.starfield, (0, 0))
        mouse_pos = pygame.mouse.get_pos()

        title_surf = self.font_title.render("Great job!", True, CORRECT_COLOR)
        self.screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 200)))

        subtitle_surf = self.font_subtitle.render(
            "You put all 8 planets in the right order!", True, SUBTITLE_COLOR
        )
        self.screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 260)))

        for order_index, sx in enumerate(SLOT_XS, start=1):
            planet = self.placed[order_index]
            small_x = 150 + (order_index - 1) * ((WIDTH - 300) / (len(PLANETS) - 1))
            draw_planet(self.screen, (small_x, 360), planet, WIN_DISPLAY_H, WIN_MAX_W)

        self.play_again_button.draw(self.screen, self.font_word, mouse_pos)
        self.win_menu_button.draw(self.screen, self.font_word, mouse_pos)

    def draw(self):
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_PLAYING:
            self.draw_playing()
        elif self.state == STATE_WIN:
            self.draw_win()

        pygame.display.flip()

    async def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.state == STATE_MENU:
                        running = False
                    else:
                        self.quit_requested = True
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == STATE_MENU:
                        self.handle_menu_click(event.pos)
                    elif self.state == STATE_PLAYING:
                        self.handle_playing_click(event.pos)
                    elif self.state == STATE_WIN:
                        self.handle_win_click(event.pos)

            self.draw()

            if self.quit_requested:
                running = False

            clock.tick(60)
            await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(Game().run())
