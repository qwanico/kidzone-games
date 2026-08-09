import math
import random
import sys

import pygame

WIDTH, HEIGHT = 600, 800
TABLE_COLOR = (30, 60, 90)
LINE_COLOR = (80, 130, 170)
TEXT_COLOR = (255, 255, 255)

GOAL_W = 200
GOAL_LEFT = (WIDTH - GOAL_W) // 2

PADDLE_R = 34
PUCK_R = 18
PLAYER_COLOR = (120, 220, 255)
AI_COLOR = (240, 120, 140)
PUCK_COLOR = (240, 220, 90)

MAX_SPEED = 12
AI_SPEED = 5.5
WIN_SCORE = 7


def clamp(value, low, high):
    return max(low, min(high, value))


def reset_puck(direction):
    speed = 4.5
    angle = random.uniform(-0.6, 0.6) + (0 if direction > 0 else math.pi)
    return [WIDTH / 2, HEIGHT / 2], [math.sin(angle) * speed, math.cos(angle) * speed * direction]


HOME_RECT = pygame.Rect(20, 20, 60, 50)
PAUSE_RECT = pygame.Rect(90, 20, 60, 50)
HUD_BUTTON_BG = (40, 44, 58)
HUD_BUTTON_BORDER = (110, 116, 136)
PAUSE_OVERLAY_COLOR = (0, 0, 0, 170)
PAUSE_BTN_W, PAUSE_BTN_H = 240, 60


def draw_hud_button(screen, rect):
    pygame.draw.rect(screen, HUD_BUTTON_BG, rect, border_radius=10)
    pygame.draw.rect(screen, HUD_BUTTON_BORDER, rect, width=2, border_radius=10)


def draw_home_icon(screen, rect):
    draw_hud_button(screen, rect)
    cx, cy = rect.center
    roof = [(cx - 16, cy - 2), (cx, cy - 15), (cx + 16, cy - 2)]
    pygame.draw.polygon(screen, (255, 255, 255), roof)
    body = pygame.Rect(0, 0, 22, 15)
    body.midtop = (cx, cy - 3)
    pygame.draw.rect(screen, (255, 255, 255), body)


def draw_pause_icon(screen, rect):
    draw_hud_button(screen, rect)
    cx, cy = rect.center
    bar_w, bar_h = 8, 26
    left_bar = pygame.Rect(0, 0, bar_w, bar_h)
    left_bar.center = (cx - 7, cy)
    right_bar = pygame.Rect(0, 0, bar_w, bar_h)
    right_bar.center = (cx + 7, cy)
    pygame.draw.rect(screen, (255, 255, 255), left_bar, border_radius=2)
    pygame.draw.rect(screen, (255, 255, 255), right_bar, border_radius=2)


def draw_pause_menu(screen, font_title, font_btn, resume_rect, restart_rect, home_rect):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill(PAUSE_OVERLAY_COLOR)
    screen.blit(overlay, (0, 0))

    title_surf = font_title.render("Paused", True, (255, 255, 255))
    screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, resume_rect.top - 60)))

    for rect, label in ((resume_rect, "Resume"), (restart_rect, "Restart"), (home_rect, "Home")):
        pygame.draw.rect(screen, HUD_BUTTON_BG, rect, border_radius=14)
        pygame.draw.rect(screen, (255, 255, 255), rect, width=2, border_radius=14)
        label_surf = font_btn.render(label, True, (255, 255, 255))
        screen.blit(label_surf, label_surf.get_rect(center=rect.center))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Air Hockey")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 48, bold=True)
    score_font = pygame.font.SysFont(None, 64, bold=True)
    big_font = pygame.font.SysFont(None, 60, bold=True)
    subtitle_font = pygame.font.SysFont(None, 26)

    def new_game():
        puck_pos, puck_vel = reset_puck(random.choice([-1, 1]))
        player_pos = [WIDTH / 2, HEIGHT - 80]
        ai_pos = [WIDTH / 2, 80]
        return puck_pos, puck_vel, player_pos, ai_pos, 0, 0

    puck_pos, puck_vel, player_pos, ai_pos, player_score, ai_score = new_game()
    winner = None
    running = True
    paused = False

    resume_rect = pygame.Rect(WIDTH // 2 - PAUSE_BTN_W // 2, HEIGHT // 2 - 20, PAUSE_BTN_W, PAUSE_BTN_H)
    restart_rect = pygame.Rect(WIDTH // 2 - PAUSE_BTN_W // 2, HEIGHT // 2 + 55, PAUSE_BTN_W, PAUSE_BTN_H)
    home_menu_rect = pygame.Rect(WIDTH // 2 - PAUSE_BTN_W // 2, HEIGHT // 2 + 130, PAUSE_BTN_W, PAUSE_BTN_H)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif paused:
                    pass
                elif winner and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    puck_pos, puck_vel, player_pos, ai_pos, player_score, ai_score = new_game()
                    winner = None
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HOME_RECT.collidepoint(event.pos):
                    running = False
                elif paused:
                    if resume_rect.collidepoint(event.pos):
                        paused = False
                    elif restart_rect.collidepoint(event.pos):
                        puck_pos, puck_vel, player_pos, ai_pos, player_score, ai_score = new_game()
                        winner = None
                        paused = False
                    elif home_menu_rect.collidepoint(event.pos):
                        running = False
                elif PAUSE_RECT.collidepoint(event.pos):
                    paused = True
                elif winner:
                    puck_pos, puck_vel, player_pos, ai_pos, player_score, ai_score = new_game()
                    winner = None
            elif event.type == pygame.MOUSEMOTION and not winner and not paused:
                mx, my = event.pos
                player_pos[0] = clamp(mx, PADDLE_R, WIDTH - PADDLE_R)
                player_pos[1] = clamp(my, HEIGHT / 2 + PADDLE_R, HEIGHT - PADDLE_R)

        if not winner and not paused:
            if ai_pos[0] < puck_pos[0] - 2:
                ai_pos[0] += min(AI_SPEED, puck_pos[0] - ai_pos[0])
            elif ai_pos[0] > puck_pos[0] + 2:
                ai_pos[0] -= min(AI_SPEED, ai_pos[0] - puck_pos[0])
            target_y = 80 if puck_pos[1] < HEIGHT / 2 else 130
            if ai_pos[1] < target_y - 2:
                ai_pos[1] += min(AI_SPEED, target_y - ai_pos[1])
            elif ai_pos[1] > target_y + 2:
                ai_pos[1] -= min(AI_SPEED, ai_pos[1] - target_y)
            ai_pos[0] = clamp(ai_pos[0], PADDLE_R, WIDTH - PADDLE_R)
            ai_pos[1] = clamp(ai_pos[1], PADDLE_R, HEIGHT / 2 - PADDLE_R)

            puck_pos[0] += puck_vel[0]
            puck_pos[1] += puck_vel[1]

            if puck_pos[0] - PUCK_R <= 0 or puck_pos[0] + PUCK_R >= WIDTH:
                puck_vel[0] *= -1
                puck_pos[0] = clamp(puck_pos[0], PUCK_R, WIDTH - PUCK_R)

            for paddle_pos in (player_pos, ai_pos):
                dx = puck_pos[0] - paddle_pos[0]
                dy = puck_pos[1] - paddle_pos[1]
                dist = math.hypot(dx, dy)
                min_dist = PADDLE_R + PUCK_R
                if dist < min_dist and dist > 0:
                    nx, ny = dx / dist, dy / dist
                    puck_pos[0] = paddle_pos[0] + nx * min_dist
                    puck_pos[1] = paddle_pos[1] + ny * min_dist
                    speed = math.hypot(*puck_vel) + 1.2
                    speed = min(speed, MAX_SPEED)
                    puck_vel[0] = nx * speed
                    puck_vel[1] = ny * speed

            if puck_pos[1] - PUCK_R <= 0:
                if GOAL_LEFT <= puck_pos[0] <= GOAL_LEFT + GOAL_W:
                    player_score += 1
                    if player_score >= WIN_SCORE:
                        winner = "player"
                    else:
                        puck_pos, puck_vel = reset_puck(1)
                else:
                    puck_vel[1] *= -1
                    puck_pos[1] = PUCK_R
            elif puck_pos[1] + PUCK_R >= HEIGHT:
                if GOAL_LEFT <= puck_pos[0] <= GOAL_LEFT + GOAL_W:
                    ai_score += 1
                    if ai_score >= WIN_SCORE:
                        winner = "ai"
                    else:
                        puck_pos, puck_vel = reset_puck(-1)
                else:
                    puck_vel[1] *= -1
                    puck_pos[1] = HEIGHT - PUCK_R

        screen.fill(TABLE_COLOR)
        pygame.draw.line(screen, LINE_COLOR, (0, HEIGHT / 2), (WIDTH, HEIGHT / 2), 3)
        pygame.draw.circle(screen, LINE_COLOR, (WIDTH // 2, HEIGHT // 2), 80, 3)
        pygame.draw.rect(screen, (20, 40, 60), (GOAL_LEFT, 0, GOAL_W, 8))
        pygame.draw.rect(screen, (20, 40, 60), (GOAL_LEFT, HEIGHT - 8, GOAL_W, 8))

        pygame.draw.circle(screen, AI_COLOR, (int(ai_pos[0]), int(ai_pos[1])), PADDLE_R)
        pygame.draw.circle(screen, PLAYER_COLOR, (int(player_pos[0]), int(player_pos[1])), PADDLE_R)
        pygame.draw.circle(screen, PUCK_COLOR, (int(puck_pos[0]), int(puck_pos[1])), PUCK_R)

        title_surf = title_font.render("Air Hockey", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 30)))

        score_surf = score_font.render(f"{ai_score} : {player_score}", True, TEXT_COLOR)
        screen.blit(score_surf, score_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        if winner:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            label = "You Win!" if winner == "player" else "Computer Wins!"
            done_surf = big_font.render(label, True, (255, 255, 255))
            screen.blit(done_surf, done_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            again_surf = subtitle_font.render(
                "Click or press Enter to play again", True, (230, 230, 230)
            )
            screen.blit(
                again_surf, again_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            )

        draw_home_icon(screen, HOME_RECT)
        draw_pause_icon(screen, PAUSE_RECT)

        if paused:
            draw_pause_menu(screen, title_font, subtitle_font, resume_rect, restart_rect, home_menu_rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
