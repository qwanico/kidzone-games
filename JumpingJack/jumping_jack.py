import random
import sys

import pygame

WIDTH, HEIGHT = 900, 600
BG_TOP = (255, 230, 180)
BG_BOTTOM = (255, 250, 235)
GROUND_Y = HEIGHT - 120
GROUND_COLOR = (140, 200, 110)
TEXT_COLOR = (50, 50, 60)
TITLE_COLOR = (60, 60, 90)

PLAYER_X = 150
PLAYER_W, PLAYER_H = 50, 70
GRAVITY = 0.9
JUMP_VELOCITY = -16

OBSTACLE_W, OBSTACLE_H = 40, 60
OBSTACLE_COLOR = (200, 90, 70)
SPAWN_MIN_MS = 900
SPAWN_MAX_MS = 1700

START_SPEED = 6.0
MAX_SPEED = 14.0
SPEED_RAMP_PER_SEC = 0.12


class Player:
    def __init__(self):
        self.y = GROUND_Y - PLAYER_H
        self.vy = 0.0
        self.on_ground = True
        self.run_phase = 0.0

    def jump(self):
        if self.on_ground:
            self.vy = JUMP_VELOCITY
            self.on_ground = False

    def update(self, dt):
        self.vy += GRAVITY
        self.y += self.vy
        if self.y >= GROUND_Y - PLAYER_H:
            self.y = GROUND_Y - PLAYER_H
            self.vy = 0
            self.on_ground = True
        if self.on_ground:
            self.run_phase += dt * 0.015

    def rect(self):
        return pygame.Rect(PLAYER_X, int(self.y), PLAYER_W, PLAYER_H)

    def draw(self, screen):
        rect = self.rect()
        pygame.draw.rect(screen, (90, 130, 220), rect, border_radius=12)
        pygame.draw.circle(screen, (250, 210, 170), (rect.centerx, rect.top - 6), 18)
        if self.on_ground:
            leg_swing = int(10 * abs(((self.run_phase % 1.0) * 2) - 1) - 5)
        else:
            leg_swing = 6
        pygame.draw.line(
            screen, (60, 60, 90),
            (rect.centerx - 10, rect.bottom), (rect.centerx - 10 - leg_swing, rect.bottom + 16), 6
        )
        pygame.draw.line(
            screen, (60, 60, 90),
            (rect.centerx + 10, rect.bottom), (rect.centerx + 10 + leg_swing, rect.bottom + 16), 6
        )


class Obstacle:
    def __init__(self, x):
        self.x = x
        self.passed = False

    def update(self, speed):
        self.x -= speed

    def off_screen(self):
        return self.x < -OBSTACLE_W

    def rect(self):
        return pygame.Rect(int(self.x), GROUND_Y - OBSTACLE_H, OBSTACLE_W, OBSTACLE_H)

    def draw(self, screen):
        rect = self.rect()
        pygame.draw.rect(screen, OBSTACLE_COLOR, rect, border_radius=8)
        pygame.draw.rect(screen, (150, 60, 45), rect, width=3, border_radius=8)


def draw_background(screen):
    for i in range(GROUND_Y):
        t = i / GROUND_Y
        color = tuple(
            int(BG_TOP[c] + (BG_BOTTOM[c] - BG_TOP[c]) * t) for c in range(3)
        )
        pygame.draw.line(screen, color, (0, i), (WIDTH, i))
    pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Jumping Jack")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 56, bold=True)
    subtitle_font = pygame.font.SysFont(None, 28)
    hud_font = pygame.font.SysFont(None, 40, bold=True)
    big_font = pygame.font.SysFont(None, 64, bold=True)

    def new_game():
        return (
            Player(),
            [],
            0.0,
            START_SPEED,
            pygame.time.get_ticks() + random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS),
        )

    player, obstacles, score, speed, next_spawn_at = new_game()
    game_over = False
    running = True

    while running:
        now = pygame.time.get_ticks()
        dt = clock.get_time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_RETURN):
                    if game_over:
                        player, obstacles, score, speed, next_spawn_at = new_game()
                        game_over = False
                    else:
                        player.jump()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_over:
                    player, obstacles, score, speed, next_spawn_at = new_game()
                    game_over = False
                else:
                    player.jump()

        if not game_over:
            player.update(dt)
            speed = min(MAX_SPEED, speed + SPEED_RAMP_PER_SEC * dt / 1000.0)
            score += speed * dt / 1000.0

            if now >= next_spawn_at:
                obstacles.append(Obstacle(WIDTH + OBSTACLE_W))
                next_spawn_at = now + random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS)

            for obstacle in obstacles:
                obstacle.update(speed)
            obstacles = [o for o in obstacles if not o.off_screen()]

            player_rect = player.rect().inflate(-14, -6)
            for obstacle in obstacles:
                if player_rect.colliderect(obstacle.rect()):
                    game_over = True
                    break

        draw_background(screen)

        title_surf = title_font.render("Jumping Jack", True, TITLE_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 45)))
        subtitle_surf = subtitle_font.render(
            "Click, tap Space, or Up to jump over obstacles!", True, (110, 90, 60)
        )
        screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 80)))

        for obstacle in obstacles:
            obstacle.draw(screen)
        player.draw(screen)

        score_surf = hud_font.render(f"Score: {int(score)}", True, TEXT_COLOR)
        screen.blit(score_surf, (30, 100))

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))
            done_surf = big_font.render(f"Final Score: {int(score)}", True, (255, 255, 255))
            screen.blit(done_surf, done_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            again_surf = subtitle_font.render(
                "Click or press Space to play again", True, (230, 230, 230)
            )
            screen.blit(
                again_surf, again_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
