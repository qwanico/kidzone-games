import asyncio
import sys

import pygame

WIDTH, HEIGHT = 800, 700
BG_COLOR = (18, 20, 30)
TEXT_COLOR = (230, 230, 240)

PADDLE_W, PADDLE_H = 120, 18
PADDLE_Y = HEIGHT - 50
PADDLE_SPEED = 9
PADDLE_COLOR = (120, 220, 255)

BALL_RADIUS = 10
BALL_COLOR = (240, 210, 90)
BALL_SPEED = 6.5

BRICK_ROWS, BRICK_COLS = 6, 10
BRICK_W, BRICK_H = 70, 26
BRICK_GAP = 6
BRICK_TOP = 80
BRICK_COLORS = [
    (230, 90, 110),
    (255, 170, 60),
    (255, 220, 60),
    (120, 210, 90),
    (90, 170, 230),
    (150, 100, 220),
]

START_LIVES = 3


def build_bricks():
    bricks = []
    grid_w = BRICK_COLS * BRICK_W + (BRICK_COLS - 1) * BRICK_GAP
    start_x = (WIDTH - grid_w) // 2
    for row in range(BRICK_ROWS):
        for col in range(BRICK_COLS):
            x = start_x + col * (BRICK_W + BRICK_GAP)
            y = BRICK_TOP + row * (BRICK_H + BRICK_GAP)
            bricks.append(
                {"rect": pygame.Rect(x, y, BRICK_W, BRICK_H), "color": BRICK_COLORS[row % len(BRICK_COLORS)]}
            )
    return bricks


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
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Breakout")
    clock = pygame.time.Clock()

    hud_font = pygame.font.SysFont(None, 34, bold=True)
    big_font = pygame.font.SysFont(None, 60, bold=True)
    subtitle_font = pygame.font.SysFont(None, 26)
    pause_font = pygame.font.SysFont(None, 30, bold=True)

    def new_game():
        paddle_x = WIDTH // 2 - PADDLE_W // 2
        ball_pos = [WIDTH // 2, PADDLE_Y - BALL_RADIUS - 4]
        ball_vel = [BALL_SPEED * 0.7, -BALL_SPEED]
        return build_bricks(), paddle_x, ball_pos, ball_vel, 0, START_LIVES

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

    bricks, paddle_x, ball_pos, ball_vel, score, lives = new_game()
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
                elif (game_over or won) and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    bricks, paddle_x, ball_pos, ball_vel, score, lives = new_game()
                    game_over = False
                    won = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HOME_RECT.collidepoint(event.pos) and not paused:
                    running = False
                elif PAUSE_RECT.collidepoint(event.pos) and not paused:
                    paused = True
                elif paused and RESUME_RECT.collidepoint(event.pos):
                    paused = False
                elif paused and RESTART_RECT.collidepoint(event.pos):
                    bricks, paddle_x, ball_pos, ball_vel, score, lives = new_game()
                    game_over = False
                    won = False
                    paused = False
                elif paused and PAUSE_HOME_RECT.collidepoint(event.pos):
                    running = False
                elif paused:
                    pass
                elif game_over or won:
                    bricks, paddle_x, ball_pos, ball_vel, score, lives = new_game()
                    game_over = False
                    won = False

        keys = pygame.key.get_pressed()
        if not game_over and not won and not paused:
            if keys[pygame.K_LEFT]:
                paddle_x -= PADDLE_SPEED
            if keys[pygame.K_RIGHT]:
                paddle_x += PADDLE_SPEED
            mouse_x = pygame.mouse.get_pos()[0]
            if pygame.mouse.get_focused():
                paddle_x = mouse_x - PADDLE_W // 2
            paddle_x = max(0, min(WIDTH - PADDLE_W, paddle_x))
            paddle_rect = pygame.Rect(paddle_x, PADDLE_Y, PADDLE_W, PADDLE_H)

            ball_pos[0] += ball_vel[0]
            ball_pos[1] += ball_vel[1]

            if ball_pos[0] - BALL_RADIUS <= 0 or ball_pos[0] + BALL_RADIUS >= WIDTH:
                ball_vel[0] *= -1
                ball_pos[0] = max(BALL_RADIUS, min(WIDTH - BALL_RADIUS, ball_pos[0]))
            if ball_pos[1] - BALL_RADIUS <= 0:
                ball_vel[1] *= -1
                ball_pos[1] = BALL_RADIUS

            ball_rect = pygame.Rect(
                ball_pos[0] - BALL_RADIUS, ball_pos[1] - BALL_RADIUS,
                BALL_RADIUS * 2, BALL_RADIUS * 2,
            )

            if ball_vel[1] > 0 and ball_rect.colliderect(paddle_rect):
                ball_pos[1] = PADDLE_Y - BALL_RADIUS
                offset = (ball_pos[0] - (paddle_x + PADDLE_W / 2)) / (PADDLE_W / 2)
                ball_vel[0] = offset * BALL_SPEED
                ball_vel[1] = -abs(ball_vel[1])

            hit_index = ball_rect.collidelist([b["rect"] for b in bricks])
            if hit_index != -1:
                brick_rect = bricks[hit_index]["rect"]
                overlap_x = min(ball_rect.right, brick_rect.right) - max(ball_rect.left, brick_rect.left)
                overlap_y = min(ball_rect.bottom, brick_rect.bottom) - max(ball_rect.top, brick_rect.top)
                if overlap_x < overlap_y:
                    ball_vel[0] *= -1
                else:
                    ball_vel[1] *= -1
                bricks.pop(hit_index)
                score += 10
                if not bricks:
                    won = True

            if ball_pos[1] - BALL_RADIUS > HEIGHT:
                lives -= 1
                if lives <= 0:
                    game_over = True
                else:
                    ball_pos = [WIDTH // 2, PADDLE_Y - BALL_RADIUS - 4]
                    ball_vel = [BALL_SPEED * 0.7, -BALL_SPEED]

        screen.fill(BG_COLOR)

        for brick in bricks:
            pygame.draw.rect(screen, brick["color"], brick["rect"], border_radius=4)

        paddle_rect = pygame.Rect(paddle_x, PADDLE_Y, PADDLE_W, PADDLE_H)
        pygame.draw.rect(screen, PADDLE_COLOR, paddle_rect, border_radius=8)
        pygame.draw.circle(screen, BALL_COLOR, (int(ball_pos[0]), int(ball_pos[1])), BALL_RADIUS)

        score_surf = hud_font.render(f"Score: {score}", True, TEXT_COLOR)
        screen.blit(score_surf, (170, 28))
        lives_surf = hud_font.render(f"Lives: {'*' * max(0, lives)}", True, TEXT_COLOR)
        screen.blit(lives_surf, lives_surf.get_rect(topright=(WIDTH - 14, 14)))

        if game_over or won:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            label = "You Win!" if won else "Game Over"
            done_surf = big_font.render(f"{label}  Score: {score}", True, (255, 255, 255))
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
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(run())
