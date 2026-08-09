import asyncio
import random
import sys

import pygame

WIDTH, HEIGHT = 600, 720
GRID_SIZE = 4
TILE, GAP = 120, 14
BOARD_TOP = 160
BOARD_LEFT = (WIDTH - (GRID_SIZE * TILE + (GRID_SIZE - 1) * GAP)) // 2

BG_COLOR = (28, 30, 42)
BOARD_COLOR = (44, 48, 66)
EMPTY_COLOR = (56, 60, 82)
TEXT_COLOR = (230, 230, 240)

TILE_COLORS = {
    0: (56, 60, 82),
    2: (110, 120, 160),
    4: (100, 140, 170),
    8: (90, 170, 160),
    16: (90, 190, 120),
    32: (170, 200, 90),
    64: (230, 200, 80),
    128: (240, 170, 70),
    256: (240, 140, 70),
    512: (240, 110, 90),
    1024: (220, 90, 130),
    2048: (200, 90, 200),
}


def new_board():
    board = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    spawn_tile(board)
    spawn_tile(board)
    return board


def spawn_tile(board):
    empties = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if board[r][c] == 0]
    if not empties:
        return
    r, c = random.choice(empties)
    board[r][c] = 4 if random.random() < 0.1 else 2


def compress_merge(row):
    vals = [v for v in row if v != 0]
    merged = []
    gained = 0
    i = 0
    while i < len(vals):
        if i + 1 < len(vals) and vals[i] == vals[i + 1]:
            merged.append(vals[i] * 2)
            gained += vals[i] * 2
            i += 2
        else:
            merged.append(vals[i])
            i += 1
    merged += [0] * (GRID_SIZE - len(merged))
    return merged, gained


def move_left(board):
    changed = False
    gained = 0
    new_rows = []
    for row in board:
        new_row, row_gain = compress_merge(row)
        if new_row != row:
            changed = True
        gained += row_gain
        new_rows.append(new_row)
    return new_rows, changed, gained


def reverse_rows(board):
    return [list(reversed(row)) for row in board]


def transpose(board):
    return [list(row) for row in zip(*board)]


def move(board, direction):
    if direction == "left":
        return move_left(board)
    if direction == "right":
        reversed_board = reverse_rows(board)
        moved, changed, gained = move_left(reversed_board)
        return reverse_rows(moved), changed, gained
    if direction == "up":
        transposed = transpose(board)
        moved, changed, gained = move_left(transposed)
        return transpose(moved), changed, gained
    if direction == "down":
        transposed = transpose(board)
        reversed_board = reverse_rows(transposed)
        moved, changed, gained = move_left(reversed_board)
        return transpose(reverse_rows(moved)), changed, gained
    return board, False, 0


def has_moves(board):
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 0:
                return True
            if c + 1 < GRID_SIZE and board[r][c] == board[r][c + 1]:
                return True
            if r + 1 < GRID_SIZE and board[r][c] == board[r + 1][c]:
                return True
    return False


HOME_RECT = pygame.Rect(20, 20, 60, 50)
PAUSE_RECT = pygame.Rect(90, 20, 60, 50)
HUD_BG_COLOR = (40, 44, 58)
HUD_BORDER_COLOR = (110, 116, 140)
HUD_ICON_COLOR = (240, 240, 245)

PAUSE_BTN_W, PAUSE_BTN_H = 220, 54
RESUME_RECT = pygame.Rect(WIDTH // 2 - PAUSE_BTN_W // 2, HEIGHT // 2 - 20, PAUSE_BTN_W, PAUSE_BTN_H)
RESTART_RECT = pygame.Rect(WIDTH // 2 - PAUSE_BTN_W // 2, HEIGHT // 2 + 44, PAUSE_BTN_W, PAUSE_BTN_H)
PAUSE_HOME_RECT = pygame.Rect(WIDTH // 2 - PAUSE_BTN_W // 2, HEIGHT // 2 + 108, PAUSE_BTN_W, PAUSE_BTN_H)


def draw_home_icon(screen, rect):
    cx, cy = rect.centerx, rect.centery
    pygame.draw.polygon(
        screen, HUD_ICON_COLOR,
        [(cx, cy - 13), (cx - 15, cy + 1), (cx + 15, cy + 1)],
    )
    pygame.draw.rect(screen, HUD_ICON_COLOR, (cx - 9, cy + 1, 18, 13))


def draw_pause_icon(screen, rect):
    cx, cy = rect.centerx, rect.centery
    pygame.draw.rect(screen, HUD_ICON_COLOR, (cx - 11, cy - 11, 8, 22), border_radius=2)
    pygame.draw.rect(screen, HUD_ICON_COLOR, (cx + 3, cy - 11, 8, 22), border_radius=2)


def draw_hud_button(screen, rect, draw_icon):
    pygame.draw.rect(screen, HUD_BG_COLOR, rect, border_radius=10)
    pygame.draw.rect(screen, HUD_BORDER_COLOR, rect, width=2, border_radius=10)
    draw_icon(screen, rect)


def draw_hud(screen):
    draw_hud_button(screen, HOME_RECT, draw_home_icon)
    draw_hud_button(screen, PAUSE_RECT, draw_pause_icon)


async def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    pygame.display.set_caption("2048")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 64, bold=True)
    hud_font = pygame.font.SysFont(None, 34, bold=True)
    tile_font = pygame.font.SysFont(None, 46, bold=True)
    big_font = pygame.font.SysFont(None, 56, bold=True)
    subtitle_font = pygame.font.SysFont(None, 24)
    pause_font = pygame.font.SysFont(None, 30, bold=True)

    def new_game():
        return new_board(), 0

    def draw_pause_overlay():
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))
        title_surf = big_font.render("Paused", True, (255, 255, 255))
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 90)))
        for rect, label in ((RESUME_RECT, "Resume"), (RESTART_RECT, "Restart"), (PAUSE_HOME_RECT, "Home")):
            pygame.draw.rect(screen, HUD_BG_COLOR, rect, border_radius=10)
            pygame.draw.rect(screen, HUD_BORDER_COLOR, rect, width=2, border_radius=10)
            label_surf = pause_font.render(label, True, (255, 255, 255))
            screen.blit(label_surf, label_surf.get_rect(center=rect.center))

    board, score = new_game()
    game_over = False
    won = False
    paused = False
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif paused:
                    pass
                elif game_over and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    board, score = new_game()
                    game_over = False
                    won = False
                elif won and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    won = False
                elif not game_over:
                    direction = None
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        direction = "left"
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        direction = "right"
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        direction = "up"
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        direction = "down"
                    if direction:
                        board, changed, gained = move(board, direction)
                        if changed:
                            score += gained
                            spawn_tile(board)
                            if any(2048 in row for row in board) and not won:
                                won = True
                            if not has_moves(board):
                                game_over = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HOME_RECT.collidepoint(event.pos) and not paused:
                    running = False
                elif PAUSE_RECT.collidepoint(event.pos) and not paused:
                    paused = True
                elif paused and RESUME_RECT.collidepoint(event.pos):
                    paused = False
                elif paused and RESTART_RECT.collidepoint(event.pos):
                    board, score = new_game()
                    game_over = False
                    won = False
                    paused = False
                elif paused and PAUSE_HOME_RECT.collidepoint(event.pos):
                    running = False
                elif paused:
                    pass
                elif game_over:
                    board, score = new_game()
                    game_over = False
                    won = False

        screen.fill(BG_COLOR)

        title_surf = title_font.render("2048", True, TEXT_COLOR)
        screen.blit(title_surf, (170, 30))
        score_surf = hud_font.render(f"Score: {score}", True, TEXT_COLOR)
        screen.blit(score_surf, score_surf.get_rect(topright=(WIDTH - 30, 50)))

        board_rect = pygame.Rect(
            BOARD_LEFT - GAP, BOARD_TOP - GAP,
            GRID_SIZE * TILE + (GRID_SIZE + 1) * GAP,
            GRID_SIZE * TILE + (GRID_SIZE + 1) * GAP,
        )
        pygame.draw.rect(screen, BOARD_COLOR, board_rect, border_radius=12)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                value = board[r][c]
                x = BOARD_LEFT + c * (TILE + GAP)
                y = BOARD_TOP + r * (TILE + GAP)
                color = TILE_COLORS.get(value, (100, 30, 30))
                pygame.draw.rect(screen, color, (x, y, TILE, TILE), border_radius=8)
                if value:
                    text_color = (60, 60, 70) if value <= 4 else (255, 255, 255)
                    val_surf = tile_font.render(str(value), True, text_color)
                    screen.blit(val_surf, val_surf.get_rect(center=(x + TILE // 2, y + TILE // 2)))

        if game_over or won:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            label = "You reached 2048!" if won else "Game Over"
            done_surf = big_font.render(label, True, (255, 255, 255))
            screen.blit(done_surf, done_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            hint = "Press Space to keep playing" if won else "Click or press Space to try again"
            again_surf = subtitle_font.render(hint, True, (230, 230, 230))
            screen.blit(
                again_surf, again_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            )

        if paused:
            draw_pause_overlay()
        else:
            draw_hud(screen)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(run())
