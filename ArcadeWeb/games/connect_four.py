import asyncio
import math
import random
import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent / "connect_four_assets"

WIDTH, HEIGHT = 900, 800

BG_COLOR = (24, 26, 38)
TITLE_COLOR = (120, 220, 255)
SUBTITLE_COLOR = (150, 155, 180)
TEXT_COLOR = (225, 228, 240)
BOARD_COLOR = (45, 50, 82)
SLOT_EMPTY = (24, 26, 38)
PLAYER_COLOR = (255, 190, 90)
AI_COLOR = (255, 90, 130)
BUTTON_COLOR = (60, 66, 96)
BUTTON_HOVER = (86, 94, 132)
OVERLAY_COLOR = (14, 15, 24, 190)
ICON_BG = (40, 44, 58)
ICON_BG_HOVER = (54, 59, 78)
ICON_BORDER = (100, 106, 132)
ICON_COLOR = (255, 255, 255)
ACCENT_COLOR = (140, 255, 170)

CONFETTI_COLORS = [
    (120, 220, 255), (255, 110, 140), (255, 210, 90),
    (140, 255, 170), (180, 140, 255),
]

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAMEOVER = "gameover"

COLS, ROWS = 7, 6
CELL = 90
BOARD_X = (WIDTH - COLS * CELL) // 2
BOARD_Y = 180
PIECE_R = CELL // 2 - 8

PLAYER = 1
AI = 2

AI_MOVE_DELAY_MS = 550


class Particle:
    __slots__ = ("x0", "y0", "vx", "vy", "color", "size", "spawn", "life", "shape")

    def __init__(self, x, y, vx, vy, color, size, spawn, life, shape):
        self.x0, self.y0, self.vx, self.vy = x, y, vx, vy
        self.color, self.size, self.spawn, self.life, self.shape = color, size, spawn, life, shape

    def pos_at(self, now):
        t = (now - self.spawn) / 1000.0
        return self.x0 + self.vx * t, self.y0 + self.vy * t + 0.5 * 600 * t * t

    def alive(self, now):
        return now - self.spawn < self.life


def spawn_confetti(center, now, count=22, colors=None):
    colors = colors or CONFETTI_COLORS
    particles = []
    for _ in range(count):
        angle = random.uniform(-math.pi * 0.9, -math.pi * 0.1)
        speed = random.uniform(140, 380)
        vx, vy = math.cos(angle) * speed, math.sin(angle) * speed
        color = random.choice(colors)
        size = random.randint(4, 8)
        shape = random.choice(["circle", "square"])
        particles.append(Particle(center[0], center[1], vx, vy, color, size, now, 900, shape))
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


class IconButton:
    """Small square icon button for the always-visible Home/Pause HUD controls."""

    def __init__(self, rect, kind):
        self.rect = pygame.Rect(rect)
        self.kind = kind  # "home" or "pause"

    def draw(self, surface, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        bg = ICON_BG_HOVER if hovered else ICON_BG
        pygame.draw.rect(surface, bg, self.rect, border_radius=12)
        pygame.draw.rect(surface, ICON_BORDER, self.rect, width=2, border_radius=12)
        cx, cy = self.rect.center
        if self.kind == "home":
            roof = [(cx - 15, cy - 1), (cx, cy - 15), (cx + 15, cy - 1)]
            pygame.draw.polygon(surface, ICON_COLOR, roof)
            body = pygame.Rect(0, 0, 20, 14)
            body.midtop = (cx, cy - 3)
            pygame.draw.rect(surface, ICON_COLOR, body)
        else:  # pause
            bar = pygame.Rect(0, 0, 7, 22)
            bar.center = (cx - 7, cy)
            pygame.draw.rect(surface, ICON_COLOR, bar, border_radius=2)
            bar2 = bar.copy()
            bar2.center = (cx + 7, cy)
            pygame.draw.rect(surface, ICON_COLOR, bar2, border_radius=2)


# ---------- pure game logic (board is list of ROWS lists of COLS, row 0 = top) ----------

def make_board():
    return [[0 for _ in range(COLS)] for _ in range(ROWS)]


def valid_columns(board):
    return [c for c in range(COLS) if board[0][c] == 0]


def drop_row(board, col):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return None


def check_winner_at(board, row, col):
    piece = board[row][col]
    if piece == 0:
        return False
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1
        r, c = row + dr, col + dc
        while 0 <= r < ROWS and 0 <= c < COLS and board[r][c] == piece:
            count += 1
            r += dr
            c += dc
        r, c = row - dr, col - dc
        while 0 <= r < ROWS and 0 <= c < COLS and board[r][c] == piece:
            count += 1
            r -= dr
            c -= dc
        if count >= 4:
            return True
    return False


def is_full(board):
    return all(board[0][c] != 0 for c in range(COLS))


def score_window(window, piece):
    opp = PLAYER if piece == AI else AI
    score = 0
    count_p = window.count(piece)
    count_o = window.count(opp)
    count_e = window.count(0)
    if count_p == 4:
        score += 100
    elif count_p == 3 and count_e == 1:
        score += 8
    elif count_p == 2 and count_e == 2:
        score += 3
    if count_o == 3 and count_e == 1:
        score -= 10
    return score


def evaluate_board(board, piece):
    score = 0
    center_col = COLS // 2
    center_count = sum(1 for r in range(ROWS) if board[r][center_col] == piece)
    score += center_count * 4

    for r in range(ROWS):
        row = board[r]
        for c in range(COLS - 3):
            score += score_window(row[c:c + 4], piece)
    for c in range(COLS):
        col_vals = [board[r][c] for r in range(ROWS)]
        for r in range(ROWS - 3):
            score += score_window(col_vals[r:r + 4], piece)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += score_window(window, piece)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + 3 - i][c + i] for i in range(4)]
            score += score_window(window, piece)
    return score


def choose_ai_move(board):
    valid = valid_columns(board)
    if not valid:
        return None

    # 1. Win if possible
    for c in valid:
        r = drop_row(board, c)
        board[r][c] = AI
        won = check_winner_at(board, r, c)
        board[r][c] = 0
        if won:
            return c

    # 2. Block opponent's win
    for c in valid:
        r = drop_row(board, c)
        board[r][c] = PLAYER
        won = check_winner_at(board, r, c)
        board[r][c] = 0
        if won:
            return c

    # 3. Heuristic scoring with slight randomness, weighted toward center
    scored = []
    for c in valid:
        r = drop_row(board, c)
        board[r][c] = AI
        s = evaluate_board(board, AI)
        board[r][c] = 0
        s += random.uniform(-2, 2)
        scored.append((s, c))
    scored.sort(key=lambda x: -x[0])
    top = [c for s, c in scored if s >= scored[0][0] - 3]
    return random.choice(top)


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self.sound_drop = make_beep(300, 90, 0.18)
            self.sound_win = make_beep(660, 260, 0.25)
            self.sound_draw = make_beep(220, 200, 0.2)
        except Exception:
            self.sound_drop = self.sound_win = self.sound_draw = None

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Connect Four")

        self.font_title = pygame.font.SysFont("arial", 56, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 22)
        self.font_hud = pygame.font.SysFont("arial", 26, bold=True)
        self.font_button = pygame.font.SysFont("arial", 26, bold=True)

        self.start_button = Button((WIDTH // 2 - 140, 460, 280, 70), "Start Game")
        self.resume_button = Button((WIDTH // 2 - 160, 340, 320, 70), "Resume")
        self.restart_button = Button((WIDTH // 2 - 160, 430, 320, 70), "Restart")
        self.pause_home_button = Button((WIDTH // 2 - 160, 520, 320, 70), "Home")
        self.menu_button = Button((WIDTH // 2 - 160, 500, 320, 70), "Main Menu")
        self.home_button = IconButton((20, 20, 60, 50), "home")
        self.pause_button = IconButton((90, 20, 60, 50), "pause")

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
        self.pause_started = None
        self.pause_accum = 0
        self.reset_game()

    # ---------- lifecycle ----------
    def reset_game(self):
        self.board = make_board()
        self.turn = PLAYER
        self.winner = None
        self.win_cells = []
        self.ai_move_at = None
        self.last_drop_col = None

    def start_game(self):
        self.reset_game()
        self.state = STATE_PLAYING

    def restart_game(self):
        self.reset_game()
        self.pause_started = None
        self.state = STATE_PLAYING

    def enter_pause(self):
        self.state = STATE_PAUSED
        self.pause_started = pygame.time.get_ticks()

    def resume_game(self):
        if self.pause_started is not None:
            self.pause_accum += pygame.time.get_ticks() - self.pause_started
            self.pause_started = None
        self.state = STATE_PLAYING

    def game_now(self):
        """Game-clock ms, excluding time spent paused (avoids a catch-up jump on resume)."""
        if self.state == STATE_PAUSED and self.pause_started is not None:
            return self.pause_started - self.pause_accum
        return pygame.time.get_ticks() - self.pause_accum

    # ---------- input ----------
    def handle_menu_click(self, pos):
        if self.start_button.rect.collidepoint(pos):
            self.start_game()

    def handle_pause_click(self, pos):
        if self.resume_button.rect.collidepoint(pos):
            self.resume_game()
        elif self.restart_button.rect.collidepoint(pos):
            self.restart_game()
        elif self.pause_home_button.rect.collidepoint(pos):
            self.quit_requested = True

    def handle_gameover_click(self, pos):
        if self.menu_button.rect.collidepoint(pos):
            self.state = STATE_MENU

    def col_from_x(self, x):
        col = (x - BOARD_X) // CELL
        if 0 <= col < COLS:
            return int(col)
        return None

    def handle_click(self, pos):
        if self.home_button.rect.collidepoint(pos):
            self.quit_requested = True
            return
        if self.pause_button.rect.collidepoint(pos):
            self.enter_pause()
            return
        if self.turn != PLAYER or self.winner:
            return
        col = self.col_from_x(pos[0])
        if col is None:
            return
        self.drop_piece(col, PLAYER)

    def drop_piece(self, col, piece):
        row = drop_row(self.board, col)
        if row is None:
            return False
        self.board[row][col] = piece
        self.last_drop_col = col
        if self.sound_drop:
            self.sound_drop.play()
        now = self.game_now()
        cx = BOARD_X + col * CELL + CELL / 2
        cy = BOARD_Y + row * CELL + CELL / 2
        self.particles.extend(spawn_confetti((cx, cy), now, count=6, colors=[PLAYER_COLOR if piece == PLAYER else AI_COLOR]))

        if check_winner_at(self.board, row, col):
            self.winner = piece
            self.find_win_cells(row, col, piece)
            self.particles.extend(spawn_confetti((WIDTH / 2, BOARD_Y), now, count=40))
            if self.sound_win:
                self.sound_win.play()
            self.state = STATE_GAMEOVER
        elif is_full(self.board):
            self.winner = 0
            if self.sound_draw:
                self.sound_draw.play()
            self.state = STATE_GAMEOVER
        else:
            self.turn = AI if piece == PLAYER else PLAYER
            if self.turn == AI:
                self.ai_move_at = self.game_now() + AI_MOVE_DELAY_MS
        return True

    def find_win_cells(self, row, col, piece):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            cells = [(row, col)]
            r, c = row + dr, col + dc
            while 0 <= r < ROWS and 0 <= c < COLS and self.board[r][c] == piece:
                cells.append((r, c))
                r += dr
                c += dc
            r, c = row - dr, col - dc
            while 0 <= r < ROWS and 0 <= c < COLS and self.board[r][c] == piece:
                cells.append((r, c))
                r -= dr
                c -= dc
            if len(cells) >= 4:
                self.win_cells = cells
                return

    # ---------- update ----------
    def update(self):
        now = self.game_now()
        if self.turn == AI and not self.winner and self.ai_move_at and now >= self.ai_move_at:
            self.ai_move_at = None
            col = choose_ai_move(self.board)
            if col is not None:
                self.drop_piece(col, AI)

        if self.particles:
            self.particles = [p for p in self.particles if p.alive(now)]

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

    def draw_title(self, now, y=80):
        title = "CONNECT FOUR"
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
        self.draw_title(now, y=170)
        subtitle = self.font_subtitle.render(
            "Click a column to drop your disc. Beat the AI!", True, SUBTITLE_COLOR
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 290)))
        self.start_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_board(self, now):
        mouse_pos = pygame.mouse.get_pos()
        board_rect = pygame.Rect(BOARD_X - 10, BOARD_Y - 10, COLS * CELL + 20, ROWS * CELL + 20)
        pygame.draw.rect(self.screen, BOARD_COLOR, board_rect, border_radius=14)

        hover_col = self.col_from_x(mouse_pos[0]) if self.turn == PLAYER and not self.winner else None
        if hover_col is not None:
            cx = BOARD_X + hover_col * CELL + CELL / 2
            bob = math.sin(now / 200) * 4
            pygame.draw.circle(self.screen, (*PLAYER_COLOR, 180), (int(cx), BOARD_Y - 34 + int(bob)), PIECE_R)

        for r in range(ROWS):
            for c in range(COLS):
                cx = BOARD_X + c * CELL + CELL // 2
                cy = BOARD_Y + r * CELL + CELL // 2
                piece = self.board[r][c]
                if piece == 0:
                    color = SLOT_EMPTY
                elif piece == PLAYER:
                    color = PLAYER_COLOR
                else:
                    color = AI_COLOR

                glow = (r, c) in self.win_cells
                if glow and (now // 200) % 2 == 0:
                    pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), PIECE_R + 5)
                pygame.draw.circle(self.screen, color, (cx, cy), PIECE_R)
                pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), PIECE_R, width=2)

    def draw_playing(self):
        now = self.game_now()
        self.screen.fill(BG_COLOR)
        self.draw_bg_shapes(now)
        self.draw_board(now)
        self.draw_particles(now)

        turn_text = "Your turn" if self.turn == PLAYER else "AI is thinking..."
        color = PLAYER_COLOR if self.turn == PLAYER else AI_COLOR
        hud = self.font_hud.render(turn_text, True, color)
        self.screen.blit(hud, hud.get_rect(center=(WIDTH // 2, 60)))

        mouse_pos = pygame.mouse.get_pos()
        self.home_button.draw(self.screen, mouse_pos)
        self.pause_button.draw(self.screen, mouse_pos)

    def draw_paused(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))
        paused_surf = self.font_title.render("Paused", True, TEXT_COLOR)
        self.screen.blit(paused_surf, paused_surf.get_rect(center=(WIDTH // 2, 300)))
        self.resume_button.draw(self.screen, self.font_button, mouse_pos, now=now)
        self.restart_button.draw(self.screen, self.font_button, mouse_pos, now=now)
        self.pause_home_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_gameover(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        self.screen.fill(BG_COLOR)
        self.draw_bg_shapes(now)
        self.draw_board(now)
        self.draw_particles(now)

        bounce = math.sin(now / 180) * 6
        if self.winner == PLAYER:
            text, color = "You Win!", PLAYER_COLOR
        elif self.winner == AI:
            text, color = "AI Wins!", AI_COLOR
        else:
            text, color = "Draw!", TEXT_COLOR

        overlay = pygame.Surface((WIDTH, 140), pygame.SRCALPHA)
        overlay.fill((*BG_COLOR, 220))
        self.screen.blit(overlay, (0, 0))
        win_surf = self.font_title.render(text, True, color)
        self.screen.blit(win_surf, win_surf.get_rect(center=(WIDTH // 2, 55 + int(bounce))))

        self.menu_button.rect.center = (WIDTH // 2, HEIGHT - 60)
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

    async def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            clock.tick(60)
            await asyncio.sleep(0)
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
                    elif self.state == STATE_GAMEOVER:
                        self.handle_gameover_click(event.pos)

            if self.state == STATE_PLAYING:
                self.update()
            self.draw()

            if self.quit_requested:
                running = False


async def run():
    await Game().run()


if __name__ == "__main__":
    asyncio.run(run())
