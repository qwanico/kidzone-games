import asyncio
import sys

import pygame

WIDTH, HEIGHT = 600, 720
BG_COLOR = (24, 26, 38)
LINE_COLOR = (90, 96, 120)
TEXT_COLOR = (230, 230, 240)
X_COLOR = (120, 220, 255)
O_COLOR = (240, 120, 140)

BOARD_SIZE = 480
BOARD_TOP = 160
BOARD_LEFT = (WIDTH - BOARD_SIZE) // 2
CELL = BOARD_SIZE // 3

HUMAN, AI, EMPTY = "X", "O", None

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
]


def winner(board):
    for a, b, c in WIN_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


def is_full(board):
    return all(cell is not None for cell in board)


def minimax(board, player):
    win = winner(board)
    if win == AI:
        return 1, None
    if win == HUMAN:
        return -1, None
    if is_full(board):
        return 0, None

    moves = [i for i, cell in enumerate(board) if cell is None]
    best_move = moves[0]
    if player == AI:
        best_score = -2
        for m in moves:
            board[m] = AI
            score, _ = minimax(board, HUMAN)
            board[m] = None
            if score > best_score:
                best_score = score
                best_move = m
        return best_score, best_move
    else:
        best_score = 2
        for m in moves:
            board[m] = HUMAN
            score, _ = minimax(board, AI)
            board[m] = None
            if score < best_score:
                best_score = score
                best_move = m
        return best_score, best_move


def cell_rect(i):
    row, col = divmod(i, 3)
    return pygame.Rect(BOARD_LEFT + col * CELL, BOARD_TOP + row * CELL, CELL, CELL)


def draw_mark(screen, i, mark):
    rect = cell_rect(i)
    pad = 30
    if mark == HUMAN:
        pygame.draw.line(screen, X_COLOR, (rect.left + pad, rect.top + pad), (rect.right - pad, rect.bottom - pad), 10)
        pygame.draw.line(screen, X_COLOR, (rect.right - pad, rect.top + pad), (rect.left + pad, rect.bottom - pad), 10)
    elif mark == AI:
        pygame.draw.circle(screen, O_COLOR, rect.center, CELL // 2 - pad, 10)


async def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tic-Tac-Toe")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 56, bold=True)
    hud_font = pygame.font.SysFont(None, 32)
    big_font = pygame.font.SysFont(None, 56, bold=True)
    subtitle_font = pygame.font.SysFont(None, 26)

    def new_round():
        return [None] * 9, HUMAN, None

    board, turn, result = new_round()
    wins = losses = draws = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif result is not None and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    board, turn, result = new_round()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if result is not None:
                    board, turn, result = new_round()
                elif turn == HUMAN:
                    for i in range(9):
                        if board[i] is None and cell_rect(i).collidepoint(event.pos):
                            board[i] = HUMAN
                            turn = AI
                            break

        if result is None and turn == AI:
            win = winner(board)
            if win or is_full(board):
                pass
            else:
                _, move_i = minimax(board, AI)
                if move_i is not None:
                    board[move_i] = AI
                turn = HUMAN

        if result is None:
            win = winner(board)
            if win == HUMAN:
                result = "win"
                wins += 1
            elif win == AI:
                result = "lose"
                losses += 1
            elif is_full(board):
                result = "draw"
                draws += 1

        screen.fill(BG_COLOR)

        title_surf = title_font.render("Tic-Tac-Toe", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        record_surf = hud_font.render(
            f"Wins: {wins}   Losses: {losses}   Draws: {draws}", True, (170, 175, 195)
        )
        screen.blit(record_surf, record_surf.get_rect(center=(WIDTH // 2, 105)))

        for i in range(1, 3):
            pygame.draw.line(
                screen, LINE_COLOR,
                (BOARD_LEFT + i * CELL, BOARD_TOP), (BOARD_LEFT + i * CELL, BOARD_TOP + BOARD_SIZE), 4
            )
            pygame.draw.line(
                screen, LINE_COLOR,
                (BOARD_LEFT, BOARD_TOP + i * CELL), (BOARD_LEFT + BOARD_SIZE, BOARD_TOP + i * CELL), 4
            )
        pygame.draw.rect(screen, LINE_COLOR, (BOARD_LEFT, BOARD_TOP, BOARD_SIZE, BOARD_SIZE), width=4, border_radius=8)

        for i, mark in enumerate(board):
            if mark:
                draw_mark(screen, i, mark)

        if result is not None:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            labels = {"win": "You Win!", "lose": "AI Wins!", "draw": "It's a Draw!"}
            done_surf = big_font.render(labels[result], True, (255, 255, 255))
            screen.blit(done_surf, done_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            again_surf = subtitle_font.render(
                "Click or press Enter to play again", True, (230, 230, 230)
            )
            screen.blit(
                again_surf, again_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            )

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(run())
