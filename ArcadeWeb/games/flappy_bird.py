import asyncio
import random
import sys

import pygame

WIDTH, HEIGHT = 500, 750
BG_TOP = (110, 190, 230)
BG_BOTTOM = (200, 230, 245)
GROUND_H = 60
GROUND_COLOR = (210, 180, 100)
TEXT_COLOR = (255, 255, 255)

BIRD_X = 130
BIRD_RADIUS = 16
GRAVITY = 0.45
FLAP_VELOCITY = -8.5

PIPE_W = 70
PIPE_GAP = 190
PIPE_SPEED = 3.2
PIPE_SPACING_MS = 1400
PIPE_COLOR = (90, 180, 90)


class Pipe:
    def __init__(self, x):
        self.x = x
        margin = 90
        self.gap_y = random.randint(margin + PIPE_GAP // 2, HEIGHT - GROUND_H - margin - PIPE_GAP // 2)
        self.scored = False

    def update(self):
        self.x -= PIPE_SPEED

    def off_screen(self):
        return self.x < -PIPE_W

    def top_rect(self):
        return pygame.Rect(self.x, 0, PIPE_W, self.gap_y - PIPE_GAP // 2)

    def bottom_rect(self):
        top_h = self.gap_y + PIPE_GAP // 2
        return pygame.Rect(self.x, top_h, PIPE_W, HEIGHT - GROUND_H - top_h)

    def draw(self, screen):
        for rect in (self.top_rect(), self.bottom_rect()):
            pygame.draw.rect(screen, PIPE_COLOR, rect)
            pygame.draw.rect(screen, (60, 140, 60), rect, width=3)


def draw_background(screen):
    for i in range(HEIGHT - GROUND_H):
        t = i / (HEIGHT - GROUND_H)
        color = tuple(int(BG_TOP[c] + (BG_BOTTOM[c] - BG_TOP[c]) * t) for c in range(3))
        pygame.draw.line(screen, color, (0, i), (WIDTH, i))
    pygame.draw.rect(screen, GROUND_COLOR, (0, HEIGHT - GROUND_H, WIDTH, GROUND_H))


async def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Flappy Bird")
    clock = pygame.time.Clock()

    hud_font = pygame.font.SysFont(None, 46, bold=True)
    big_font = pygame.font.SysFont(None, 60, bold=True)
    subtitle_font = pygame.font.SysFont(None, 26)

    def new_game():
        return HEIGHT / 2, 0.0, [], 0, pygame.time.get_ticks()

    bird_y, bird_vel, pipes, score, last_spawn = new_game()
    game_over = False
    running = True

    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_RETURN):
                    if game_over:
                        bird_y, bird_vel, pipes, score, last_spawn = new_game()
                        game_over = False
                    else:
                        bird_vel = FLAP_VELOCITY
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_over:
                    bird_y, bird_vel, pipes, score, last_spawn = new_game()
                    game_over = False
                else:
                    bird_vel = FLAP_VELOCITY

        if not game_over:
            bird_vel += GRAVITY
            bird_y += bird_vel

            if now - last_spawn >= PIPE_SPACING_MS:
                pipes.append(Pipe(WIDTH + PIPE_W))
                last_spawn = now

            for pipe in pipes:
                pipe.update()
                if not pipe.scored and pipe.x + PIPE_W < BIRD_X:
                    pipe.scored = True
                    score += 1
            pipes = [p for p in pipes if not p.off_screen()]

            bird_rect = pygame.Rect(
                BIRD_X - BIRD_RADIUS, bird_y - BIRD_RADIUS, BIRD_RADIUS * 2, BIRD_RADIUS * 2
            )
            if bird_y - BIRD_RADIUS <= 0 or bird_y + BIRD_RADIUS >= HEIGHT - GROUND_H:
                game_over = True
            for pipe in pipes:
                if bird_rect.colliderect(pipe.top_rect()) or bird_rect.colliderect(pipe.bottom_rect()):
                    game_over = True
                    break

        draw_background(screen)
        for pipe in pipes:
            pipe.draw(screen)

        pygame.draw.circle(screen, (250, 210, 60), (BIRD_X, int(bird_y)), BIRD_RADIUS)
        pygame.draw.circle(screen, (30, 30, 30), (BIRD_X + 6, int(bird_y) - 4), 3)
        pygame.draw.polygon(
            screen, (240, 140, 40),
            [(BIRD_X + BIRD_RADIUS, bird_y), (BIRD_X + BIRD_RADIUS + 12, bird_y - 4), (BIRD_X + BIRD_RADIUS + 12, bird_y + 4)]
        )

        score_surf = hud_font.render(str(score), True, TEXT_COLOR)
        screen.blit(score_surf, score_surf.get_rect(midtop=(WIDTH // 2, 20)))

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            done_surf = big_font.render(f"Score: {score}", True, (255, 255, 255))
            screen.blit(done_surf, done_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            again_surf = subtitle_font.render(
                "Click or press Space to play again", True, (230, 230, 230)
            )
            screen.blit(
                again_surf, again_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            )

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(run())
