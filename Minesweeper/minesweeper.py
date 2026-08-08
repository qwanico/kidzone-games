import math
import random
import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent
SOUNDS_DIR = BASE_DIR / "sounds"

WIDTH, HEIGHT = 900, 800
GRID_W, GRID_H = 12, 12
NUM_MINES = 20
CELL = 42

BOARD_PIXEL_W = GRID_W * CELL
BOARD_PIXEL_H = GRID_H * CELL
BOARD_X = (WIDTH - BOARD_PIXEL_W) // 2
BOARD_Y = 175

BG_COLOR = (24, 26, 38)
TEXT_COLOR = (225, 228, 240)
TITLE_COLOR = (120, 220, 255)
SUBTITLE_COLOR = (150, 155, 180)
ACCENT = (255, 176, 80)
ACCENT_DARK = (215, 140, 55)

CELL_HIDDEN = (66, 70, 96)
CELL_HIDDEN_HOVER = (82, 87, 116)
CELL_REVEALED = (40, 43, 60)
GRID_LINE = (24, 26, 38)
MINE_COLOR = (255, 90, 90)
FLAG_COLOR = (255, 176, 80)
WIN_COLOR = (120, 230, 150)
LOSE_COLOR = (255, 90, 90)

NUMBER_COLORS = {
    1: (110, 170, 255),
    2: (120, 220, 150),
    3: (255, 120, 120),
    4: (170, 130, 255),
    5: (255, 170, 90),
    6: (100, 220, 220),
    7: (230, 230, 230),
    8: (170, 175, 195),
}

CONFETTI_COLORS = [
    (255, 99, 132), (255, 205, 86), (75, 192, 192),
    (54, 162, 235), (153, 102, 255), (120, 220, 255),
]

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAMEOVER = "gameover"


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


def spawn_confetti(center, now, count=26):
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

    def draw(self, surface, font, mouse_pos, now=0, text_color=(20, 20, 30)):
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


class Cell:
    __slots__ = ("mine", "revealed", "flagged", "adjacent")

    def __init__(self):
        self.mine = False
        self.revealed = False
        self.flagged = False
        self.adjacent = 0


def neighbors(x, y):
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_W and 0 <= ny < GRID_H:
                yield nx, ny


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self.wrong_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.wav"))
        except pygame.error:
            self.wrong_sound = None

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Minesweeper")

        self.font_title = pygame.font.SysFont("arial", 68, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 24)
        self.font_button = pygame.font.SysFont("arial", 26, bold=True)
        self.font_icon = pygame.font.SysFont("arial", 22, bold=True)
        self.font_stat = pygame.font.SysFont("arial", 28, bold=True)
        self.font_cell = pygame.font.SysFont("arial", 22, bold=True)
        self.font_big = pygame.font.SysFont("arial", 54, bold=True)

        self.start_button = Button((WIDTH // 2 - 140, 460, 280, 90), "Start")
        self.pause_button = Button((WIDTH - 90, 20, 60, 46), "II")
        self.resume_button = Button((WIDTH // 2 - 160, 340, 320, 80), "Resume")
        self.quit_button = Button((WIDTH // 2 - 160, 440, 320, 80), "Quit")
        self.restart_button = Button((20, 20, 60, 46), "R")
        self.play_again_button = Button((WIDTH // 2 - 160, 500, 320, 80), "Play Again")
        self.menu_button = Button((WIDTH // 2 - 160, 600, 320, 80), "Menu")

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
        self._pause_saved_ticks = None
        self.particles = []
        self.shake_until = 0
        self.shake_seed = 0.0
        self.exploded_cell = None

        self.new_board()

    def new_board(self):
        self.grid = [[Cell() for _ in range(GRID_H)] for _ in range(GRID_W)]
        self.first_click_done = False
        self.revealed_count = 0
        self.flags_placed = 0
        self.start_ticks = None
        self.elapsed = 0
        self.result = None  # "won" / "lost"
        self.particles = []
        self.exploded_cell = None

    def place_mines(self, safe_x, safe_y):
        safe_cells = set(neighbors(safe_x, safe_y))
        safe_cells.add((safe_x, safe_y))
        all_cells = [
            (x, y) for x in range(GRID_W) for y in range(GRID_H)
            if (x, y) not in safe_cells
        ]
        random.shuffle(all_cells)
        mine_cells = all_cells[:NUM_MINES]
        for (x, y) in mine_cells:
            self.grid[x][y].mine = True
        for x in range(GRID_W):
            for y in range(GRID_H):
                if self.grid[x][y].mine:
                    continue
                self.grid[x][y].adjacent = sum(
                    1 for (nx, ny) in neighbors(x, y) if self.grid[nx][ny].mine
                )

    def flood_reveal(self, x, y):
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            cell = self.grid[cx][cy]
            if cell.revealed or cell.flagged:
                continue
            cell.revealed = True
            self.revealed_count += 1
            if cell.adjacent == 0 and not cell.mine:
                for nx, ny in neighbors(cx, cy):
                    ncell = self.grid[nx][ny]
                    if not ncell.revealed and not ncell.flagged:
                        stack.append((nx, ny))

    def reveal(self, x, y):
        cell = self.grid[x][y]
        if cell.revealed or cell.flagged:
            return
        if not self.first_click_done:
            self.place_mines(x, y)
            self.first_click_done = True
            self.start_ticks = pygame.time.get_ticks()

        if cell.mine:
            cell.revealed = True
            self.exploded_cell = (x, y)
            self.reveal_all_mines()
            self.result = "lost"
            self.state = STATE_GAMEOVER
            if self.wrong_sound:
                self.wrong_sound.play()
            now = pygame.time.get_ticks()
            self.shake_until = now + 500
            self.shake_seed = random.uniform(0, 100)
            return

        self.flood_reveal(x, y)
        self.check_win()

    def reveal_all_mines(self):
        for col in self.grid:
            for cell in col:
                if cell.mine:
                    cell.revealed = True

    def check_win(self):
        total_safe = GRID_W * GRID_H - NUM_MINES
        if self.revealed_count >= total_safe:
            self.result = "won"
            self.state = STATE_GAMEOVER
            now = pygame.time.get_ticks()
            center = (BOARD_X + BOARD_PIXEL_W // 2, BOARD_Y + BOARD_PIXEL_H // 2)
            self.particles.extend(spawn_confetti(center, now, 40))

    def toggle_flag(self, x, y):
        cell = self.grid[x][y]
        if cell.revealed:
            return
        cell.flagged = not cell.flagged
        self.flags_placed += 1 if cell.flagged else -1

    def cell_at_pos(self, pos):
        mx, my = pos
        if not (BOARD_X <= mx < BOARD_X + BOARD_PIXEL_W and BOARD_Y <= my < BOARD_Y + BOARD_PIXEL_H):
            return None
        x = (mx - BOARD_X) // CELL
        y = (my - BOARD_Y) // CELL
        return int(x), int(y)

    def start_game(self):
        self.new_board()
        self.state = STATE_PLAYING

    def enter_pause(self):
        if self.start_ticks is not None:
            self._pause_saved_ticks = pygame.time.get_ticks() - self.start_ticks
        self.state = STATE_PAUSED

    def resume_game(self):
        if self._pause_saved_ticks is not None:
            self.start_ticks = pygame.time.get_ticks() - self._pause_saved_ticks
        self.state = STATE_PLAYING

    def handle_menu_click(self, pos):
        if self.start_button.is_hovered(pos):
            self.start_game()

    def handle_pause_click(self, pos):
        if self.resume_button.is_hovered(pos):
            self.resume_game()
        elif self.quit_button.is_hovered(pos):
            self.quit_requested = True

    def handle_gameover_click(self, pos):
        if self.play_again_button.is_hovered(pos):
            self.start_game()
        elif self.menu_button.is_hovered(pos):
            self.state = STATE_MENU

    def handle_playing_click(self, pos, button):
        if self.pause_button.is_hovered(pos):
            self.enter_pause()
            return
        if self.restart_button.is_hovered(pos):
            self.start_game()
            return
        cell_pos = self.cell_at_pos(pos)
        if cell_pos is None:
            return
        x, y = cell_pos
        if button == 1:
            self.reveal(x, y)
        elif button == 3:
            self.toggle_flag(x, y)

    def update(self):
        now = pygame.time.get_ticks()
        if self.state == STATE_PLAYING and self.start_ticks is not None:
            self.elapsed = (now - self.start_ticks) // 1000
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

    def draw_title(self, now, y=110):
        title = "Minesweeper"
        letter_surfs = [self.font_title.render(ch, True, TITLE_COLOR) for ch in title]
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
        self.draw_title(now, 200)
        subtitle_surf = self.font_subtitle.render(
            "Clear the field without hitting a mine!", True, SUBTITLE_COLOR
        )
        self.screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 300)))
        rules_surf = self.font_subtitle.render(
            "Left-click reveals, right-click flags.", True, SUBTITLE_COLOR
        )
        self.screen.blit(rules_surf, rules_surf.get_rect(center=(WIDTH // 2, 335)))
        self.start_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_board(self, now):
        shake_x, shake_y = 0, 0
        if now < self.shake_until:
            t = (self.shake_until - now) / 500.0
            shake_x = int(math.sin((now + self.shake_seed) / 20) * 8 * t)
            shake_y = int(math.cos((now + self.shake_seed) / 17) * 6 * t)

        mouse_pos = pygame.mouse.get_pos()
        hover_cell = self.cell_at_pos(mouse_pos) if self.state == STATE_PLAYING else None

        for x in range(GRID_W):
            for y in range(GRID_H):
                cell = self.grid[x][y]
                rect = pygame.Rect(
                    BOARD_X + x * CELL + shake_x, BOARD_Y + y * CELL + shake_y, CELL, CELL
                )
                if cell.revealed:
                    if cell.mine:
                        color = MINE_COLOR if (x, y) == self.exploded_cell else (90, 45, 45)
                    else:
                        color = CELL_REVEALED
                else:
                    color = CELL_HIDDEN_HOVER if hover_cell == (x, y) else CELL_HIDDEN

                pygame.draw.rect(self.screen, color, rect.inflate(-2, -2), border_radius=4)

                if cell.revealed and cell.mine:
                    pygame.draw.circle(self.screen, (20, 20, 25), rect.center, 10)
                elif cell.revealed and cell.adjacent > 0:
                    num_surf = self.font_cell.render(
                        str(cell.adjacent), True, NUMBER_COLORS.get(cell.adjacent, TEXT_COLOR)
                    )
                    self.screen.blit(num_surf, num_surf.get_rect(center=rect.center))
                elif not cell.revealed and cell.flagged:
                    flag_points = [
                        (rect.centerx - 6, rect.centery + 10),
                        (rect.centerx - 6, rect.centery - 10),
                        (rect.centerx + 8, rect.centery - 5),
                    ]
                    pygame.draw.line(
                        self.screen, (200, 200, 210),
                        (rect.centerx - 6, rect.centery + 10), (rect.centerx - 6, rect.centery - 10), 2
                    )
                    pygame.draw.polygon(self.screen, FLAG_COLOR, flag_points)

        border_rect = pygame.Rect(BOARD_X + shake_x, BOARD_Y + shake_y, BOARD_PIXEL_W, BOARD_PIXEL_H)
        pygame.draw.rect(self.screen, (60, 64, 88), border_rect, width=3, border_radius=6)

    def draw_playing(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)
        self.draw_title(now, 40)

        mines_left = NUM_MINES - self.flags_placed
        stat_surf = self.font_stat.render(f"Mines: {mines_left}", True, ACCENT)
        self.screen.blit(stat_surf, (110, 24))

        timer_surf = self.font_stat.render(f"Time: {self.elapsed}s", True, TEXT_COLOR)
        self.screen.blit(timer_surf, timer_surf.get_rect(topright=(WIDTH - 170, 24)))

        self.draw_board(now)
        self.draw_particles(now)

        self.restart_button.draw(self.screen, self.font_icon, mouse_pos, now=now)
        self.pause_button.draw(self.screen, self.font_icon, mouse_pos, now=now)

    def draw_paused(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 18, 200))
        self.screen.blit(overlay, (0, 0))
        paused_surf = self.font_title.render("Paused", True, TITLE_COLOR)
        self.screen.blit(paused_surf, paused_surf.get_rect(center=(WIDTH // 2, 240)))
        self.resume_button.draw(self.screen, self.font_button, mouse_pos, now=now)
        self.quit_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_gameover(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        self.draw_playing()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 18, 200))
        self.screen.blit(overlay, (0, 0))

        if self.result == "won":
            msg, color = "You Win!", WIN_COLOR
        else:
            msg, color = "Boom! Game Over", LOSE_COLOR

        bounce = math.sin(now / 200) * 6
        msg_surf = self.font_big.render(msg, True, color)
        self.screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH // 2, 380 + int(bounce))))

        time_surf = self.font_subtitle.render(f"Time: {self.elapsed}s", True, TEXT_COLOR)
        self.screen.blit(time_surf, time_surf.get_rect(center=(WIDTH // 2, 440)))

        self.draw_particles(now)
        self.play_again_button.draw(self.screen, self.font_button, mouse_pos, now=now)
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
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == STATE_MENU:
                        self.handle_menu_click(event.pos)
                    elif self.state == STATE_PLAYING:
                        self.handle_playing_click(event.pos, event.button)
                    elif self.state == STATE_PAUSED:
                        self.handle_pause_click(event.pos)
                    elif self.state == STATE_GAMEOVER:
                        self.handle_gameover_click(event.pos)

            self.update()
            self.draw()

            if self.quit_requested:
                running = False

            clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
