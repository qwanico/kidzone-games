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
    from .common import display
except ImportError:  # standalone `python games/planets.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common import display

BASE_DIR = Path(__file__).parent / "planets_assets"
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

CONFETTI_COLORS = [
    (255, 255, 255),
    (255, 210, 90),
    (140, 210, 255),
    (150, 255, 190),
    (200, 160, 255),
]

GRAVITY = 260
POP_DURATION = 260

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


# smoothscale is a software resample with no SIMD path in the pygbag build.
# This used to run for every tray planet, every placed planet and the win
# screen on every frame - measured at ~1.7 ms/frame for 9 planets, about 10%
# of the whole 60fps budget. Sizes are integer pixels drawn from a handful of
# fixed constants plus a short pop animation, so the set of distinct sizes is
# small and bounded: caching them makes steady-state frames free.
_scaled_cache = {}


def draw_planet(surface, center, planet, height, max_width=None):
    img = planet["image"]
    width, actual_height = planet_render_size(planet, height, max_width)
    w = max(1, int(width))
    h = max(1, int(actual_height))
    key = (planet["file"], w, h)
    scaled = _scaled_cache.get(key)
    if scaled is None:
        scaled = pygame.transform.smoothscale(img, (w, h))
        _scaled_cache[key] = scaled
    surface.blit(scaled, scaled.get_rect(center=center))


def ease_out_back(t):
    c1 = 1.70158
    c3 = c1 + 1
    ts = t - 1
    return 1 + c3 * ts ** 3 + c1 * ts ** 2


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


def build_stars():
    rng = random.Random(7)
    stars = []
    for _ in range(160):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, HEIGHT)
        size = rng.choice([1, 1, 1, 2])
        brightness = rng.randint(120, 255)
        stars.append({
            "x": x,
            "y": y,
            "size": size,
            "brightness": brightness,
            "phase": rng.uniform(0, math.tau),
            "speed": rng.uniform(0.6, 1.6),
        })
    return stars


def build_nebulae():
    rng = random.Random(11)
    nebulae = []
    for _ in range(3):
        nebulae.append((rng.randint(0, WIDTH), rng.randint(0, HEIGHT)))
    return nebulae


def build_nebula_glow():
    glow = pygame.Surface((90, 90), pygame.SRCALPHA)
    pygame.draw.circle(glow, (120, 90, 200, 35), (45, 45), 45)
    return glow


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

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
        if platform is not None and hasattr(platform, "window"):
            try:
                platform.window.window_resize()
            except Exception:
                pass
        pygame.display.set_caption("Planets")

        self.font_title = pygame.font.SysFont("arial", 64, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 24)
        self.font_word = pygame.font.SysFont("arial", 30, bold=True)
        self.font_label = pygame.font.SysFont("arial", 18, bold=True)
        self.font_small_label = pygame.font.SysFont("arial", 16, bold=True)
        self.font_score = pygame.font.SysFont("arial", 24, bold=True)

        # --- decorative animated space background ---
        self.stars = build_stars()
        self.nebulae = build_nebulae()
        self.nebula_glow = build_nebula_glow()
        self.shooting_stars = []
        self.shooting_timer = random.uniform(3, 7)

        load_planet_images()

        self.wrong_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.ogg"))

        self.start_button = Button((WIDTH // 2 - 140, 460, 280, 90), "Start")
        self.menu_button = Button((WIDTH - 150, 20, 130, 50), "Menu")
        self.home_button = pygame.Rect(20, 20, 60, 50)
        self.play_again_button = Button((WIDTH // 2 - 300, 500, 280, 80), "Play Again")
        self.win_menu_button = Button((WIDTH // 2 + 20, 500, 280, 80), "Menu")

        # --- particle burst on correct placements / win celebration ---
        self.particles = []
        self.placed_anim = {}
        self.win_confetti_timer = 0.0

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
        self.particles = []
        self.placed_anim = {}
        self.win_confetti_timer = 0.0

    def handle_menu_click(self, pos):
        if self.start_button.rect.collidepoint(pos):
            self.start_game()

    def handle_win_click(self, pos):
        if self.play_again_button.rect.collidepoint(pos):
            self.start_game()
        elif self.win_menu_button.rect.collidepoint(pos):
            self.quit_requested = True

    def handle_playing_click(self, pos):
        if self.home_button.collidepoint(pos):
            self.quit_requested = True
            return

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
                    self.placed_anim[order_index] = pygame.time.get_ticks()
                    self.spawn_particles(sx, SLOT_Y, count=22)
                    if len(self.placed) == len(PLANETS):
                        self.state = STATE_WIN
                        self.spawn_particles(WIDTH // 2, 260, count=70)
                else:
                    self.feedback_until = pygame.time.get_ticks() + FEEDBACK_MS
                    self.feedback_slot = order_index
                    self.feedback_color = WRONG_COLOR
                    self.wrong_sound.play()
                    self.selected = None
                return

    # ---------------- decorative background ----------------

    def update_background(self, dt_ms):
        dt = dt_ms / 1000
        self.shooting_timer -= dt
        if self.shooting_timer <= 0:
            self.shooting_timer = random.uniform(4, 9)
            angle = random.uniform(2.3, 2.9)
            speed = random.uniform(480, 680)
            self.shooting_stars.append({
                "x": random.uniform(WIDTH * 0.2, WIDTH * 0.85),
                "y": random.uniform(20, 120),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "age": 0.0,
                "life": 0.5,
            })
        for sh in self.shooting_stars:
            sh["age"] += dt
            sh["x"] += sh["vx"] * dt
            sh["y"] += sh["vy"] * dt
        self.shooting_stars = [sh for sh in self.shooting_stars if sh["age"] < sh["life"]]

    def draw_starfield(self):
        self.screen.fill(BG_COLOR)
        for nx, ny in self.nebulae:
            self.screen.blit(self.nebula_glow, (nx - 45, ny - 45))

        now = pygame.time.get_ticks() / 1000
        for s in self.stars:
            twinkle = 0.55 + 0.45 * math.sin(now * s["speed"] + s["phase"])
            b = max(40, min(255, int(s["brightness"] * twinkle)))
            pygame.draw.circle(self.screen, (b, b, min(255, b + 20)), (s["x"], s["y"]), s["size"])

        for sh in self.shooting_stars:
            tail_x = sh["x"] - sh["vx"] * 0.04
            tail_y = sh["y"] - sh["vy"] * 0.04
            pygame.draw.line(self.screen, (255, 255, 255), (sh["x"], sh["y"]), (tail_x, tail_y), 2)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(sh["x"]), int(sh["y"])), 2)

    # ---------------- particles ----------------

    def spawn_particles(self, cx, cy, count=20):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(90, 260)
            self.particles.append({
                "x": cx,
                "y": cy,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - random.uniform(60, 140),
                "color": random.choice(CONFETTI_COLORS),
                "size": random.randint(3, 7),
                "angle": random.uniform(0, 360),
                "spin": random.uniform(-300, 300),
                "age": 0.0,
                "life": random.uniform(0.6, 1.2),
            })

    def spawn_confetti_rain(self, count=8):
        for _ in range(count):
            self.particles.append({
                "x": random.uniform(0, WIDTH),
                "y": -20,
                "vx": random.uniform(-30, 30),
                "vy": random.uniform(60, 140),
                "color": random.choice(CONFETTI_COLORS),
                "size": random.randint(4, 8),
                "angle": random.uniform(0, 360),
                "spin": random.uniform(-180, 180),
                "age": 0.0,
                "life": random.uniform(2.2, 3.2),
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

    def placed_scale(self, order_index):
        start = self.placed_anim.get(order_index)
        if start is None:
            return 1.0
        elapsed = pygame.time.get_ticks() - start
        if elapsed >= POP_DURATION:
            return 1.0
        t = elapsed / POP_DURATION
        return max(0.05, ease_out_back(t))

    # ---------------- drawing ----------------

    def draw_menu(self):
        self.draw_starfield()
        mouse_pos = pygame.mouse.get_pos()

        title_surf = self.font_title.render("Planets", True, TITLE_COLOR)
        self.screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 220)))

        subtitle_surf = self.font_subtitle.render(
            "Put the planets in order, starting from the Sun!", True, SUBTITLE_COLOR
        )
        self.screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 290)))

        self.start_button.draw(self.screen, self.font_word, mouse_pos)

    def draw_playing(self):
        self.draw_starfield()
        mouse_pos = pygame.mouse.get_pos()

        pygame.draw.line(
            self.screen, (40, 45, 80), (SUN_POS[0] + 40, SLOT_Y), (SLOT_XS[-1], SLOT_Y), 3
        )

        pulse = 1 + 0.06 * math.sin(pygame.time.get_ticks() / 400)
        glow = pygame.Surface((140, 140), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*SUN_GLOW, 70), (70, 70), int(70 * pulse))
        self.screen.blit(glow, (SUN_POS[0] - 70, SUN_POS[1] - 70))
        pygame.draw.circle(self.screen, SUN_COLOR, SUN_POS, 40)

        for order_index, sx in enumerate(SLOT_XS, start=1):
            if order_index in self.placed:
                planet = self.placed[order_index]
                scale = self.placed_scale(order_index)
                draw_planet(self.screen, (sx, SLOT_Y), planet, SLOT_DISPLAY_H * scale, SLOT_MAX_W * scale)
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

        self.draw_particles()

        score_text = self.font_score.render(
            f"Placed: {len(self.placed)} / {len(PLANETS)}", True, SCORE_COLOR
        )
        self.screen.blit(score_text, (100, 30))

        self.menu_button.draw(self.screen, self.font_label, mouse_pos)
        draw_home_icon(self.screen, self.home_button, BUTTON_COLOR, self.home_button.collidepoint(mouse_pos))

    def draw_win(self):
        self.draw_starfield()
        self.draw_particles()
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

        _resized = display.maintain(WIDTH, HEIGHT)

        if _resized is not None:

            self.screen = _resized

    async def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = clock.tick(60)
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

            self.update_background(dt)
            self.update_particles(dt)

            if self.state == STATE_WIN:
                self.win_confetti_timer -= dt / 1000
                if self.win_confetti_timer <= 0:
                    self.win_confetti_timer = 0.5
                    self.spawn_confetti_rain()

            self.draw()

            if self.quit_requested:
                running = False

            await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(Game().run())
