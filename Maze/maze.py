import math
import random
import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent
SOUNDS_DIR = BASE_DIR / "sounds"

WIDTH, HEIGHT = 900, 800
FEEDBACK_MS = 1600
BUMP_COOLDOWN_MS = 500
MOVE_REPEAT_MS = 140

BG_COLOR = (245, 244, 235)
WALL_COLOR = (110, 120, 135)
WALL_HOVER = (90, 100, 115)
PATH_COLOR = (255, 255, 255)
PATH_BORDER = (225, 224, 214)
GOAL_COLOR = (255, 205, 60)
PLAYER_COLOR = (90, 160, 230)
PLAYER_DARK = (60, 130, 200)
TEXT_COLOR = (50, 50, 60)
SCORE_COLOR = (75, 85, 100)
TITLE_COLOR = (70, 80, 100)
BUTTON_COLOR = (110, 120, 135)
BUTTON_HOVER = (90, 100, 115)
CORRECT_COLOR = (90, 200, 110)
OVERLAY_COLOR = (30, 30, 40, 190)

CONFETTI_COLORS = [
    (255, 99, 132), (255, 205, 86), (75, 192, 192),
    (54, 162, 235), (153, 102, 255), (255, 159, 64),
]

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"

# Three hand-picked, BFS-verified solvable mazes of increasing size.
MAZES = [
    [
        "###########",
        "#S#.......#",
        "#.###.#####",
        "#...#.....#",
        "###.#.###.#",
        "#.#.#.#...#",
        "#.#.###.#.#",
        "#.#.....#.#",
        "#.#######.#",
        "#........G#",
        "###########",
    ],
    [
        "###############",
        "#S....#...#...#",
        "#####.#.#.#.#.#",
        "#...#.#.#...#.#",
        "#.#.#.#.#######",
        "#.#...#.......#",
        "#.#######.###.#",
        "#.#.....#.#...#",
        "#.###.#.###.#.#",
        "#.....#.....#.#",
        "#############.#",
        "#.#...#.......#",
        "#.#.#.#.#######",
        "#...#........G#",
        "###############",
    ],
    [
        "###################",
        "#S#.........#.....#",
        "#.###.#####.#.#####",
        "#.#...#.....#.....#",
        "#.#.###.#########.#",
        "#.#...#...........#",
        "#.###.###########.#",
        "#.....#.........#.#",
        "#######.#######.#.#",
        "#.....#...#...#.#.#",
        "#.#.###.#.#.#.###.#",
        "#.#...#.#...#...#.#",
        "#.###.#.#######.#.#",
        "#.#.#...#.....#...#",
        "#.#.#####.###.#####",
        "#.......#.#.#.....#",
        "#######.#.#.#####.#",
        "#.........#......G#",
        "###################",
    ],
]

PLAY_TOP = 150
PLAY_BOTTOM = HEIGHT - 30
PLAY_AREA_H = PLAY_BOTTOM - PLAY_TOP


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


def parse_maze(rows):
    grid = [list(row) for row in rows]
    start = goal = None
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == "S":
                start = (x, y)
                grid[y][x] = "."
            elif ch == "G":
                goal = (x, y)
    return grid, start, goal


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze")

        self.font_title = pygame.font.SysFont("arial", 68, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 26)
        self.font_word = pygame.font.SysFont("arial", 32, bold=True)
        self.font_icon = pygame.font.SysFont("arial", 24, bold=True)
        self.font_score = pygame.font.SysFont("arial", 28, bold=True)
        self.font_feedback = pygame.font.SysFont("arial", 44, bold=True)

        self.bump_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.wav"))
        self.bump_sound.set_volume(0.5)

        self.level_index = 0
        self.mazes_solved = 0
        self.grid = []
        self.start = (0, 0)
        self.goal = (0, 0)
        self.player = (0, 0)
        self.cell_size = 30
        self.origin = (0, 0)
        self.last_bump = 0
        self.bump_shake_until = 0
        self.bump_offset = (0, 0)
        self.last_move = 0
        self.feedback_until = 0
        self.feedback_text = ""
        self.particles = []
        self.won = False

        self.start_button = Button((WIDTH // 2 - 140, HEIGHT // 2 + 40, 280, 90), "Start")
        self.pause_button = Button((WIDTH - 90, 20, 60, 50), "II")
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

        self.state = STATE_MENU
        self._pause_remaining = None
        self.quit_requested = False

    # ---- level management ----
    def load_level(self):
        rows = MAZES[self.level_index % len(MAZES)]
        self.grid, self.start, self.goal = parse_maze(rows)
        self.player = self.start
        cols = len(self.grid[0])
        gh = len(self.grid)
        cell_w = (WIDTH - 60) / cols
        cell_h = PLAY_AREA_H / gh
        self.cell_size = int(min(cell_w, cell_h, 44))
        total_w = self.cell_size * cols
        total_h = self.cell_size * gh
        origin_x = (WIDTH - total_w) // 2
        origin_y = PLAY_TOP + (PLAY_AREA_H - total_h) // 2
        self.origin = (origin_x, origin_y)
        self.won = False
        self.feedback_until = 0
        self.particles = []

    def start_game(self):
        self.level_index = 0
        self.mazes_solved = 0
        self.load_level()
        self.state = STATE_PLAYING

    def enter_pause(self):
        self.state = STATE_PAUSED

    def resume_game(self):
        self.state = STATE_PLAYING

    def cell_to_px(self, cx, cy):
        ox, oy = self.origin
        return ox + cx * self.cell_size, oy + cy * self.cell_size

    def is_wall(self, x, y):
        if y < 0 or y >= len(self.grid) or x < 0 or x >= len(self.grid[0]):
            return True
        return self.grid[y][x] == "#"

    def try_move(self, dx, dy):
        if self.won:
            return
        now = pygame.time.get_ticks()
        px, py = self.player
        nx, ny = px + dx, py + dy
        if self.is_wall(nx, ny):
            self.bump_shake_until = now + 220
            self.bump_offset = (dx, dy)
            if now - self.last_bump > BUMP_COOLDOWN_MS:
                self.last_bump = now
                self.bump_sound.play()
            return
        self.player = (nx, ny)
        if self.player == self.goal:
            self.won = True
            self.mazes_solved += 1
            self.feedback_text = "Great job!"
            self.feedback_until = now + FEEDBACK_MS
            gx, gy = self.cell_to_px(nx + 0.5, ny + 0.5)
            self.particles.extend(spawn_confetti((gx, gy), now))
            self.particles.extend(spawn_confetti((WIDTH // 2, HEIGHT // 2), now))

    def advance_level(self):
        self.level_index += 1
        self.load_level()

    # ---- event handling ----
    def handle_menu_click(self, pos):
        if self.start_button.rect.collidepoint(pos):
            self.start_game()

    def handle_pause_click(self, pos):
        if self.resume_button.rect.collidepoint(pos):
            self.resume_game()
        elif self.quit_button.rect.collidepoint(pos):
            self.quit_requested = True

    def handle_playing_click(self, pos):
        if self.pause_button.rect.collidepoint(pos):
            self.enter_pause()

    def handle_key(self, key):
        moves = {
            pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
            pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
        }
        if key in moves:
            self.try_move(*moves[key])

    # ---- update ----
    def update(self):
        now = pygame.time.get_ticks()
        if self.particles:
            self.particles = [p for p in self.particles if p.alive(now)]
        if self.won and self.feedback_until and now >= self.feedback_until:
            self.advance_level()

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

    def draw_menu(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)

        title = "Maze"
        letter_surfs = [self.font_title.render(ch, True, TITLE_COLOR) for ch in title]
        total_w = sum(s.get_width() for s in letter_surfs)
        x = WIDTH // 2 - total_w // 2
        for i, surf in enumerate(letter_surfs):
            bob = math.sin(now / 260 + i * 0.6) * 10
            rect = surf.get_rect(midtop=(x + surf.get_width() // 2, 220 + int(bob)))
            self.screen.blit(surf, rect)
            x += surf.get_width()

        subtitle_surf = self.font_subtitle.render(
            "Use arrow keys or WASD to find the goal!", True, TEXT_COLOR
        )
        subtitle_rect = subtitle_surf.get_rect(center=(WIDTH // 2, 320))
        self.screen.blit(subtitle_surf, subtitle_rect)

        # little maze preview icon
        preview = pygame.Rect(0, 0, 160, 100)
        preview.center = (WIDTH // 2, 420)
        pygame.draw.rect(self.screen, WALL_COLOR, preview, border_radius=10)
        inner = preview.inflate(-24, -24)
        pygame.draw.rect(self.screen, PATH_COLOR, inner, border_radius=6)
        star_bob = math.sin(now / 260) * 4
        self.draw_star((preview.centerx + 40, preview.centery + int(star_bob)), 14, GOAL_COLOR)
        self.draw_player((preview.centerx - 40, preview.centery), 14, now)

        self.start_button.draw(self.screen, self.font_word, mouse_pos, now=now)

    def draw_star(self, center, radius, color):
        cx, cy = center
        points = []
        for i in range(10):
            angle = -math.pi / 2 + i * math.pi / 5
            r = radius if i % 2 == 0 else radius * 0.45
            points.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, (255, 255, 255), points, width=2)

    def draw_player(self, center, radius, now):
        cx, cy = center
        bob = math.sin(now / 180) * 2
        pygame.draw.circle(self.screen, PLAYER_COLOR, (cx, int(cy + bob)), radius)
        pygame.draw.circle(self.screen, PLAYER_DARK, (cx, int(cy + bob)), radius, width=2)
        eye_dx = radius * 0.35
        eye_dy = radius * -0.1
        for sign in (-1, 1):
            pygame.draw.circle(
                self.screen, (255, 255, 255),
                (int(cx + sign * eye_dx), int(cy + bob + eye_dy)), max(2, radius // 4)
            )

    def draw_maze(self, now):
        cols = len(self.grid[0])
        rows = len(self.grid)
        shake_x = shake_y = 0
        if now < self.bump_shake_until:
            t = (self.bump_shake_until - now) / 220.0
            dx, dy = self.bump_offset
            shake_x = math.sin(now / 20) * 6 * t * dx
            shake_y = math.sin(now / 20) * 6 * t * dy

        for y in range(rows):
            for x in range(cols):
                px, py = self.cell_to_px(x, y)
                rect = pygame.Rect(int(px), int(py), self.cell_size + 1, self.cell_size + 1)
                if self.grid[y][x] == "#":
                    color = WALL_HOVER if (x, y) == (0, 0) else WALL_COLOR
                    pygame.draw.rect(self.screen, WALL_COLOR, rect, border_radius=4)
                else:
                    pygame.draw.rect(self.screen, PATH_COLOR, rect)
                    pygame.draw.rect(self.screen, PATH_BORDER, rect, width=1)

        gx, gy = self.cell_to_px(self.goal[0] + 0.5, self.goal[1] + 0.5)
        star_bob = math.sin(now / 260) * 4
        self.draw_star((gx, gy + star_bob), self.cell_size * 0.4, GOAL_COLOR)

        pcx, pcy = self.cell_to_px(self.player[0] + 0.5, self.player[1] + 0.5)
        self.draw_player((pcx + shake_x, pcy + shake_y), self.cell_size * 0.38, now)

    def draw_playing(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)

        board_rect = pygame.Rect(20, PLAY_TOP - 10, WIDTH - 40, PLAY_AREA_H + 20)
        pygame.draw.rect(self.screen, (255, 255, 255), board_rect, border_radius=18)
        pygame.draw.rect(self.screen, PATH_BORDER, board_rect, width=2, border_radius=18)

        self.draw_maze(now)
        self.draw_particles(now)

        score_text = self.font_score.render(
            f"Level: {self.level_index % len(MAZES) + 1}   Solved: {self.mazes_solved}",
            True, SCORE_COLOR,
        )
        self.screen.blit(score_text, (24, 20))

        self.pause_button.draw(self.screen, self.font_icon, mouse_pos, now=now)

        if self.won and now < self.feedback_until:
            bounce = math.sin(now / 90) * 3
            fb_surf = self.font_feedback.render(self.feedback_text, True, CORRECT_COLOR)
            fb_rect = fb_surf.get_rect(center=(WIDTH // 2, PLAY_TOP - 30 + int(bounce)))
            self.screen.blit(fb_surf, fb_rect)

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
                elif event.type == pygame.KEYDOWN and self.state == STATE_PLAYING:
                    self.handle_key(event.key)
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

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
