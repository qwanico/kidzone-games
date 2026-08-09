import random
import sys

import pygame

WIDTH, HEIGHT = 800, 800
GRID_SIZE = 20
COLS, ROWS = WIDTH // GRID_SIZE, HEIGHT // GRID_SIZE

BG_COLOR = (20, 24, 30)
GRID_COLOR = (30, 35, 44)
SNAKE_COLOR = (90, 220, 140)
SNAKE_HEAD_COLOR = (130, 245, 170)
FOOD_COLOR = (240, 90, 100)
TEXT_COLOR = (230, 230, 240)

MOVE_INTERVAL_MS = 110


def random_food(snake):
    while True:
        pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        if pos not in snake:
            return pos


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


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Snake")
    clock = pygame.time.Clock()

    hud_font = pygame.font.SysFont(None, 34, bold=True)
    big_font = pygame.font.SysFont(None, 64, bold=True)
    subtitle_font = pygame.font.SysFont(None, 26)
    pause_font = pygame.font.SysFont(None, 30, bold=True)

    def new_game():
        snake = [(COLS // 2, ROWS // 2)]
        direction = (1, 0)
        food = random_food(snake)
        return snake, direction, food, pygame.time.get_ticks()

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

    snake, direction, food, last_move = new_game()
    pending_direction = direction
    score = 0
    game_over = False
    paused = False
    pause_started_at = 0
    running = True

    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif paused:
                    pass
                elif game_over and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    snake, direction, food, last_move = new_game()
                    pending_direction = direction
                    score = 0
                    game_over = False
                elif not game_over:
                    if event.key in (pygame.K_UP, pygame.K_w) and direction != (0, 1):
                        pending_direction = (0, -1)
                    elif event.key in (pygame.K_DOWN, pygame.K_s) and direction != (0, -1):
                        pending_direction = (0, 1)
                    elif event.key in (pygame.K_LEFT, pygame.K_a) and direction != (1, 0):
                        pending_direction = (-1, 0)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d) and direction != (-1, 0):
                        pending_direction = (1, 0)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HOME_RECT.collidepoint(event.pos) and not paused:
                    running = False
                elif PAUSE_RECT.collidepoint(event.pos) and not paused:
                    paused = True
                    pause_started_at = now
                elif paused and RESUME_RECT.collidepoint(event.pos):
                    paused = False
                    last_move += now - pause_started_at
                elif paused and RESTART_RECT.collidepoint(event.pos):
                    snake, direction, food, last_move = new_game()
                    pending_direction = direction
                    score = 0
                    game_over = False
                    paused = False
                elif paused and PAUSE_HOME_RECT.collidepoint(event.pos):
                    running = False
                elif paused:
                    pass
                elif game_over:
                    snake, direction, food, last_move = new_game()
                    pending_direction = direction
                    score = 0
                    game_over = False

        if not paused and not game_over and now - last_move >= MOVE_INTERVAL_MS:
            direction = pending_direction
            last_move = now
            head = snake[0]
            new_head = ((head[0] + direction[0]) % COLS, (head[1] + direction[1]) % ROWS)

            if new_head in snake:
                game_over = True
            else:
                snake.insert(0, new_head)
                if new_head == food:
                    score += 1
                    food = random_food(snake)
                else:
                    snake.pop()

        screen.fill(BG_COLOR)

        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))

        fx, fy = food
        pygame.draw.rect(
            screen, FOOD_COLOR,
            (fx * GRID_SIZE + 2, fy * GRID_SIZE + 2, GRID_SIZE - 4, GRID_SIZE - 4),
            border_radius=6,
        )

        for i, (sx, sy) in enumerate(snake):
            color = SNAKE_HEAD_COLOR if i == 0 else SNAKE_COLOR
            pygame.draw.rect(
                screen, color,
                (sx * GRID_SIZE + 1, sy * GRID_SIZE + 1, GRID_SIZE - 2, GRID_SIZE - 2),
                border_radius=5,
            )

        title_surf = hud_font.render(f"Score: {score}", True, TEXT_COLOR)
        screen.blit(title_surf, (170, 28))

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            done_surf = big_font.render(f"Final Score: {score}", True, (255, 255, 255))
            screen.blit(done_surf, done_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            again_surf = subtitle_font.render(
                "Click or press Enter to play again", True, (230, 230, 230)
            )
            screen.blit(
                again_surf, again_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            )

        if paused:
            draw_pause_overlay()
        else:
            draw_hud(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
