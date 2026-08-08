import math
import random
import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent

WIDTH, HEIGHT = 900, 800

BG_COLOR = (24, 26, 38)
TITLE_COLOR = (120, 220, 255)
SUBTITLE_COLOR = (150, 155, 180)
TEXT_COLOR = (225, 228, 240)
BOARD_BG = (32, 34, 50)
GRID_LINE = (48, 51, 72)
BUTTON_COLOR = (60, 66, 96)
BUTTON_HOVER = (86, 94, 132)
OVERLAY_COLOR = (14, 15, 24, 190)
ACCENT_COLOR = (140, 255, 170)

CONFETTI_COLORS = [
    (120, 220, 255), (255, 110, 140), (255, 210, 90),
    (140, 255, 170), (180, 140, 255),
]

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAMEOVER = "gameover"

COLS, ROWS = 10, 20
CELL = 30
BOARD_X = 60
BOARD_Y = 70

SOFT_DROP_SPEED_MULT = 18
LOCK_DELAY_MS = 450

# Each shape defined as 4 rotation states, each a list of (col, row) in a 4x4 box.
SHAPES = {
    "I": {
        "color": (100, 220, 255),
        "rots": [
            [(0, 1), (1, 1), (2, 1), (3, 1)],
            [(2, 0), (2, 1), (2, 2), (2, 3)],
            [(0, 2), (1, 2), (2, 2), (3, 2)],
            [(1, 0), (1, 1), (1, 2), (1, 3)],
        ],
    },
    "O": {
        "color": (255, 220, 90),
        "rots": [
            [(1, 0), (2, 0), (1, 1), (2, 1)],
        ] * 4,
    },
    "T": {
        "color": (200, 120, 255),
        "rots": [
            [(1, 0), (0, 1), (1, 1), (2, 1)],
            [(1, 0), (1, 1), (2, 1), (1, 2)],
            [(0, 1), (1, 1), (2, 1), (1, 2)],
            [(1, 0), (0, 1), (1, 1), (1, 2)],
        ],
    },
    "S": {
        "color": (120, 255, 140),
        "rots": [
            [(1, 0), (2, 0), (0, 1), (1, 1)],
            [(1, 0), (1, 1), (2, 1), (2, 2)],
            [(1, 1), (2, 1), (0, 2), (1, 2)],
            [(0, 0), (0, 1), (1, 1), (1, 2)],
        ],
    },
    "Z": {
        "color": (255, 110, 140),
        "rots": [
            [(0, 0), (1, 0), (1, 1), (2, 1)],
            [(2, 0), (1, 1), (2, 1), (1, 2)],
            [(0, 1), (1, 1), (1, 2), (2, 2)],
            [(1, 0), (0, 1), (1, 1), (0, 2)],
        ],
    },
    "J": {
        "color": (100, 140, 255),
        "rots": [
            [(0, 0), (0, 1), (1, 1), (2, 1)],
            [(1, 0), (2, 0), (1, 1), (1, 2)],
            [(0, 1), (1, 1), (2, 1), (2, 2)],
            [(1, 0), (1, 1), (0, 2), (1, 2)],
        ],
    },
    "L": {
        "color": (255, 170, 60),
        "rots": [
            [(2, 0), (0, 1), (1, 1), (2, 1)],
            [(1, 0), (1, 1), (1, 2), (2, 2)],
            [(0, 1), (1, 1), (2, 1), (0, 2)],
            [(0, 0), (1, 0), (1, 1), (1, 2)],
        ],
    },
}
SHAPE_KEYS = list(SHAPES.keys())


class Particle:
    __slots__ = ("x0", "y0", "vx", "vy", "color", "size", "spawn", "life", "shape")

    def __init__(self, x, y, vx, vy, color, size, spawn, life, shape):
        self.x0, self.y0, self.vx, self.vy = x, y, vx, vy
        self.color, self.size, self.spawn, self.life, self.shape = color, size, spawn, life, shape

    def pos_at(self, now):
        t = (now - self.spawn) / 1000.0
        return self.x0 + self.vx * t, self.y0 + self.vy * t + 0.5 * 500 * t * t

    def alive(self, now):
        return now - self.spawn < self.life


def spawn_confetti(center, now, count=20, colors=None):
    colors = colors or CONFETTI_COLORS
    particles = []
    for _ in range(count):
        angle = random.uniform(-math.pi, 0)
        speed = random.uniform(120, 340)
        vx, vy = math.cos(angle) * speed, math.sin(angle) * speed
        color = random.choice(colors)
        size = random.randint(3, 7)
        shape = random.choice(["circle", "square"])
        particles.append(Particle(center[0], center[1], vx, vy, color, size, now, 800, shape))
    return particles


def make_beep(freq=440, ms=80, volume=0.2, kind="sine"):
    try:
        sample_rate = 44100
        n = int(sample_rate * ms / 1000)
        import array
        buf = array.array("h")
        amp = int(32767 * volume)
        for i in range(n):
            t = i / sample_rate
            env = 1.0 - (i / n)
            if kind == "noise":
                val = int(amp * env * random.uniform(-1, 1))
            else:
                val = int(amp * env * math.sin(2 * math.pi * freq * t))
            buf.append(val)
            buf.append(val)
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception:
        return None


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
        pygame.draw.rect(surface, color, draw_rect, border_radius=16)
        pygame.draw.rect(surface, TITLE_COLOR, draw_rect, width=2, border_radius=16)
        text_surf = font.render(self.label, True, TEXT_COLOR)
        surface.blit(text_surf, text_surf.get_rect(center=draw_rect.center))


class Piece:
    def __init__(self, key):
        self.key = key
        self.color = SHAPES[key]["color"]
        self.rot = 0
        self.col = 3
        # Spawn within the visible grid (not above it) so that a stack which
        # has topped out is correctly detected as an invalid spawn position.
        self.row = 0

    def cells(self, rot=None, col=None, row=None):
        rot = self.rot if rot is None else rot
        col = self.col if col is None else col
        row = self.row if row is None else row
        return [(col + c, row + r) for c, r in SHAPES[self.key]["rots"][rot % 4]]


def new_bag():
    bag = SHAPE_KEYS.copy()
    random.shuffle(bag)
    return bag


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self.sound_lock = make_beep(220, 60, 0.15)
            self.sound_clear = make_beep(600, 180, 0.22)
            self.sound_rotate = make_beep(500, 40, 0.1)
            self.sound_gameover = make_beep(140, 400, 0.25, kind="noise")
        except Exception:
            self.sound_lock = self.sound_clear = self.sound_rotate = self.sound_gameover = None

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Block Stacker")

        self.font_title = pygame.font.SysFont("arial", 56, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 22)
        self.font_hud = pygame.font.SysFont("arial", 24, bold=True)
        self.font_button = pygame.font.SysFont("arial", 26, bold=True)
        self.font_small = pygame.font.SysFont("arial", 18)

        self.start_button = Button((WIDTH // 2 - 140, 460, 280, 70), "Start Game")
        self.resume_button = Button((WIDTH // 2 - 160, 340, 320, 70), "Resume")
        self.quit_button = Button((WIDTH // 2 - 160, 430, 320, 70), "Quit")
        self.menu_button = Button((WIDTH // 2 - 160, 500, 320, 70), "Main Menu")
        self.pause_button = Button((WIDTH - 90, 20, 60, 44), "II")

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

        self.particles = []
        self.state = STATE_MENU
        self.quit_requested = False
        self.reset_game()

    # ---------- lifecycle ----------
    def reset_game(self):
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.bag = new_bag()
        self.next_bag = new_bag()
        self.current = Piece(self._draw_from_bag())
        self.next_key = self._peek_next()
        self.fall_timer = 0
        self.fall_interval = 800
        self.soft_dropping = False
        self.lock_timer = None
        self.line_flash = []
        self.line_flash_until = 0
        self.game_over_reason = ""

    def _draw_from_bag(self):
        if not self.bag:
            self.bag = self.next_bag
            self.next_bag = new_bag()
        return self.bag.pop(0)

    def _peek_next(self):
        return self.bag[0] if self.bag else self.next_bag[0]

    def start_game(self):
        self.reset_game()
        self.state = STATE_PLAYING

    def enter_pause(self):
        self.state = STATE_PAUSED

    def resume_game(self):
        self.state = STATE_PLAYING

    # ---------- input ----------
    def handle_menu_click(self, pos):
        if self.start_button.rect.collidepoint(pos):
            self.start_game()

    def handle_pause_click(self, pos):
        if self.resume_button.rect.collidepoint(pos):
            self.resume_game()
        elif self.quit_button.rect.collidepoint(pos):
            self.quit_requested = True

    def handle_gameover_click(self, pos):
        if self.menu_button.rect.collidepoint(pos):
            self.state = STATE_MENU

    def handle_click(self, pos):
        if self.pause_button.rect.collidepoint(pos):
            self.enter_pause()

    # ---------- collision helpers ----------
    def valid_position(self, cells):
        for c, r in cells:
            if c < 0 or c >= COLS or r >= ROWS:
                return False
            if r >= 0 and self.board[r][c] is not None:
                return False
        return True

    def try_move(self, dc, dr):
        cells = self.current.cells(col=self.current.col + dc, row=self.current.row + dr)
        if self.valid_position(cells):
            self.current.col += dc
            self.current.row += dr
            return True
        return False

    def try_rotate(self):
        new_rot = (self.current.rot + 1) % 4
        for kick in (0, -1, 1, -2, 2):
            cells = self.current.cells(rot=new_rot, col=self.current.col + kick)
            if self.valid_position(cells):
                self.current.rot = new_rot
                self.current.col += kick
                if self.sound_rotate:
                    self.sound_rotate.play()
                return True
        return False

    def hard_drop(self):
        drop = 0
        while self.try_move(0, 1):
            drop += 1
        self.score += drop * 2
        self.lock_piece()

    def spawn_next(self):
        key = self._draw_from_bag()
        self.current = Piece(key)
        self.next_key = self._peek_next()
        self.lock_timer = None
        if not self.valid_position(self.current.cells()):
            self.game_over_reason = "Stack topped out!"
            if self.sound_gameover:
                self.sound_gameover.play()
            self.state = STATE_GAMEOVER

    def lock_piece(self):
        now = pygame.time.get_ticks()
        for c, r in self.current.cells():
            if 0 <= r < ROWS and 0 <= c < COLS:
                self.board[r][c] = self.current.color
        if self.sound_lock:
            self.sound_lock.play()
        self.clear_lines(now)
        if self.state == STATE_PLAYING:
            self.spawn_next()

    def clear_lines(self, now):
        full_rows = [r for r in range(ROWS) if all(self.board[r][c] is not None for c in range(COLS))]
        if not full_rows:
            return
        for r in full_rows:
            cx = BOARD_X + COLS * CELL / 2
            cy = BOARD_Y + r * CELL + CELL / 2
            self.particles.extend(spawn_confetti((cx, cy), now, count=16))
        if self.sound_clear:
            self.sound_clear.play()

        new_board = [row for i, row in enumerate(self.board) if i not in full_rows]
        for _ in full_rows:
            new_board.insert(0, [None for _ in range(COLS)])
        self.board = new_board

        n = len(full_rows)
        points = {1: 100, 2: 300, 3: 500, 4: 800}.get(n, 800)
        self.score += points * self.level
        self.lines_cleared += n
        new_level = 1 + self.lines_cleared // 10
        if new_level != self.level:
            self.level = new_level
        self.fall_interval = max(90, 800 - (self.level - 1) * 65)

    # ---------- update ----------
    def update(self, dt_ms):
        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        self.soft_dropping = keys[pygame.K_DOWN] or keys[pygame.K_s]

        interval = self.fall_interval / SOFT_DROP_SPEED_MULT if self.soft_dropping else self.fall_interval
        self.fall_timer += dt_ms
        if self.fall_timer >= interval:
            self.fall_timer = 0
            if self.try_move(0, 1):
                if self.soft_dropping:
                    self.score += 1
                self.lock_timer = None
            else:
                if self.lock_timer is None:
                    self.lock_timer = now
                elif now - self.lock_timer >= LOCK_DELAY_MS:
                    self.lock_piece()

        if self.particles:
            self.particles = [p for p in self.particles if p.alive(now)]

    def handle_keydown(self, key):
        if key in (pygame.K_LEFT, pygame.K_a):
            self.try_move(-1, 0)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.try_move(1, 0)
        elif key in (pygame.K_UP, pygame.K_w):
            self.try_rotate()
        elif key == pygame.K_SPACE:
            self.hard_drop()

    # ---------- draw ----------
    def draw_bg_shapes(self, now):
        for shape in self.bg_shapes:
            bob = math.sin(now / 900 * shape["speed"] + shape["phase"]) * 14
            r = shape["r"]
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*shape["color"], 35), (r, r), r)
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

    def draw_title(self, now, y=140):
        title = "BLOCK STACKER"
        letter_surfs = [self.font_title.render(ch, True, TITLE_COLOR) for ch in title]
        total_w = sum(s.get_width() for s in letter_surfs)
        x = WIDTH // 2 - total_w // 2
        for i, surf in enumerate(letter_surfs):
            bob = math.sin(now / 260 + i * 0.5) * 8
            rect = surf.get_rect(midtop=(x + surf.get_width() // 2, y + int(bob)))
            self.screen.blit(surf, rect)
            x += surf.get_width()

    def draw_menu(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)
        self.draw_title(now)
        subtitle = self.font_subtitle.render(
            "Arrows/WASD move+rotate, Down to soft drop, Space to hard drop.", True, SUBTITLE_COLOR
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 260)))
        self.start_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def cell_rect(self, c, r):
        return pygame.Rect(BOARD_X + c * CELL, BOARD_Y + r * CELL, CELL, CELL)

    def draw_block(self, rect, color):
        pygame.draw.rect(self.screen, color, rect.inflate(-2, -2), border_radius=4)
        pygame.draw.rect(self.screen, (255, 255, 255), rect.inflate(-2, -2), width=1, border_radius=4)

    def draw_playing(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        self.draw_bg_shapes(now)

        board_rect = pygame.Rect(BOARD_X - 4, BOARD_Y - 4, COLS * CELL + 8, ROWS * CELL + 8)
        pygame.draw.rect(self.screen, BOARD_BG, board_rect, border_radius=8)
        for r in range(ROWS):
            for c in range(COLS):
                pygame.draw.rect(self.screen, GRID_LINE, self.cell_rect(c, r), width=1)
                color = self.board[r][c]
                if color:
                    self.draw_block(self.cell_rect(c, r), color)

        # ghost piece
        ghost = Piece(self.current.key)
        ghost.rot, ghost.col, ghost.row = self.current.rot, self.current.col, self.current.row
        while self.valid_position(ghost.cells(row=ghost.row + 1)):
            ghost.row += 1
        for c, r in ghost.cells():
            if r >= 0:
                rect = self.cell_rect(c, r).inflate(-6, -6)
                pygame.draw.rect(self.screen, self.current.color, rect, width=2, border_radius=4)

        for c, r in self.current.cells():
            if r >= 0:
                self.draw_block(self.cell_rect(c, r), self.current.color)

        pygame.draw.rect(self.screen, GRID_LINE, board_rect, width=2, border_radius=8)

        self.draw_particles(now)

        panel_x = BOARD_X + COLS * CELL + 50
        hud1 = self.font_hud.render(f"Score: {self.score}", True, TEXT_COLOR)
        hud2 = self.font_hud.render(f"Lines: {self.lines_cleared}", True, TEXT_COLOR)
        hud3 = self.font_hud.render(f"Level: {self.level}", True, TEXT_COLOR)
        self.screen.blit(hud1, (panel_x, BOARD_Y))
        self.screen.blit(hud2, (panel_x, BOARD_Y + 36))
        self.screen.blit(hud3, (panel_x, BOARD_Y + 72))

        next_label = self.font_small.render("NEXT", True, SUBTITLE_COLOR)
        self.screen.blit(next_label, (panel_x, BOARD_Y + 130))
        preview_origin = (panel_x, BOARD_Y + 160)
        for c, r in SHAPES[self.next_key]["rots"][0]:
            rect = pygame.Rect(preview_origin[0] + c * 22, preview_origin[1] + r * 22, 22, 22)
            self.draw_block(rect, SHAPES[self.next_key]["color"])

        mouse_pos = pygame.mouse.get_pos()
        self.pause_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_paused(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))
        paused_surf = self.font_title.render("Paused", True, TEXT_COLOR)
        self.screen.blit(paused_surf, paused_surf.get_rect(center=(WIDTH // 2, 230)))
        self.resume_button.draw(self.screen, self.font_button, mouse_pos, now=now)
        self.quit_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_gameover(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        self.screen.fill(BG_COLOR)
        self.draw_bg_shapes(now)
        bounce = math.sin(now / 180) * 6
        text = self.font_title.render("Game Over", True, (255, 110, 140))
        self.screen.blit(text, text.get_rect(center=(WIDTH // 2, 230 + int(bounce))))
        score_surf = self.font_subtitle.render(
            f"Final score: {self.score}   Lines: {self.lines_cleared}   Level: {self.level}",
            True, TEXT_COLOR,
        )
        self.screen.blit(score_surf, score_surf.get_rect(center=(WIDTH // 2, 300)))
        self.menu_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw(self):
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_PLAYING:
            self.draw_playing()
        elif self.state == STATE_PAUSED:
            self.draw_playing()
            self.draw_paused()
        elif self.state == STATE_GAMEOVER:
            self.draw_gameover()
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt_ms = clock.tick(60)
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
                        self.handle_keydown(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == STATE_MENU:
                        self.handle_menu_click(event.pos)
                    elif self.state == STATE_PLAYING:
                        self.handle_click(event.pos)
                    elif self.state == STATE_PAUSED:
                        self.handle_pause_click(event.pos)
                    elif self.state == STATE_GAMEOVER:
                        self.handle_gameover_click(event.pos)

            if self.state == STATE_PLAYING:
                self.update(dt_ms)
            self.draw()

            if self.quit_requested:
                running = False

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
