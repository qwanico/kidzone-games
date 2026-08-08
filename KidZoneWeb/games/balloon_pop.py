import asyncio
import math
import random

import pygame

WIDTH, HEIGHT = 900, 700
BG_TOP = (150, 200, 245)
BG_BOTTOM = (210, 235, 250)
TEXT_COLOR = (50, 50, 60)
TITLE_COLOR = (60, 60, 90)

BALLOON_COLORS = [
    (230, 90, 110),
    (255, 190, 90),
    (90, 160, 230),
    (120, 180, 40),
    (150, 80, 190),
    (20, 150, 140),
]
BOMB_COLOR = (50, 50, 55)
BOMB_CHANCE = 0.18

BALLOON_W, BALLOON_H = 70, 90
SPAWN_MIN_MS = 350
SPAWN_MAX_MS = 850
MIN_SPEED, MAX_SPEED = 1.6, 3.4

START_LIVES = 3


class Balloon:
    def __init__(self):
        self.x = random.randint(BALLOON_W, WIDTH - BALLOON_W)
        self.y = HEIGHT + BALLOON_H
        self.speed = random.uniform(MIN_SPEED, MAX_SPEED)
        self.is_bomb = random.random() < BOMB_CHANCE
        self.color = BOMB_COLOR if self.is_bomb else random.choice(BALLOON_COLORS)
        self.popped = False
        self.wobble_phase = random.uniform(0, 6.28)

    def update(self, now):
        self.y -= self.speed
        self.x += 1.2 * _wobble(now, self.wobble_phase)

    def off_screen(self):
        return self.y < -BALLOON_H

    def contains(self, pos):
        cx, cy = self.x, self.y
        dx = (pos[0] - cx) / (BALLOON_W / 2)
        dy = (pos[1] - cy) / (BALLOON_H / 2)
        return dx * dx + dy * dy <= 1.0

    def draw(self, screen):
        rect = pygame.Rect(0, 0, BALLOON_W, BALLOON_H)
        rect.center = (int(self.x), int(self.y))
        pygame.draw.line(
            screen, (120, 120, 120), (self.x, self.y + BALLOON_H // 2),
            (self.x, self.y + BALLOON_H // 2 + 40), 2
        )
        pygame.draw.ellipse(screen, self.color, rect)
        highlight = pygame.Rect(0, 0, 18, 26)
        highlight.center = (int(self.x - 16), int(self.y - 20))
        pygame.draw.ellipse(screen, tuple(min(255, c + 60) for c in self.color), highlight)
        if self.is_bomb:
            font = pygame.font.SysFont(None, 34, bold=True)
            skull = font.render("X", True, (255, 255, 255))
            screen.blit(skull, skull.get_rect(center=rect.center))


def _wobble(now, phase):
    return math.sin(now / 400.0 + phase) * 0.6


def draw_background(screen):
    for i in range(HEIGHT):
        t = i / HEIGHT
        color = tuple(
            int(BG_TOP[c] + (BG_BOTTOM[c] - BG_TOP[c]) * t) for c in range(3)
        )
        pygame.draw.line(screen, color, (0, i), (WIDTH, i))


async def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Balloon Pop")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 64, bold=True)
    subtitle_font = pygame.font.SysFont(None, 30)
    hud_font = pygame.font.SysFont(None, 40, bold=True)
    big_font = pygame.font.SysFont(None, 72, bold=True)

    def new_game():
        return [], 0, START_LIVES, pygame.time.get_ticks() + random.randint(
            SPAWN_MIN_MS, SPAWN_MAX_MS
        )

    balloons, score, lives, next_spawn_at = new_game()
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
                elif game_over and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    balloons, score, lives, next_spawn_at = new_game()
                    game_over = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_over:
                    balloons, score, lives, next_spawn_at = new_game()
                    game_over = False
                else:
                    for balloon in balloons:
                        if not balloon.popped and balloon.contains(event.pos):
                            balloon.popped = True
                            if balloon.is_bomb:
                                lives -= 1
                            else:
                                score += 1
                            break

        if not game_over:
            if now >= next_spawn_at:
                balloons.append(Balloon())
                next_spawn_at = now + random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS)

            for balloon in balloons:
                balloon.update(now)
            balloons = [
                b for b in balloons if not b.popped and not b.off_screen()
            ]

            if lives <= 0:
                game_over = True

        draw_background(screen)

        title_surf = title_font.render("Balloon Pop", True, TITLE_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        subtitle_surf = subtitle_font.render(
            "Pop the balloons, avoid the bombs!", True, (70, 70, 90)
        )
        screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        for balloon in balloons:
            balloon.draw(screen)

        score_surf = hud_font.render(f"Score: {score}", True, TEXT_COLOR)
        screen.blit(score_surf, (30, 140))

        lives_surf = hud_font.render(f"Lives: {'*' * max(0, lives)}", True, TEXT_COLOR)
        screen.blit(lives_surf, lives_surf.get_rect(topright=(WIDTH - 30, 140)))

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))
            done_surf = big_font.render(f"Final Score: {score}", True, (255, 255, 255))
            screen.blit(done_surf, done_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            again_surf = subtitle_font.render(
                "Click or press Enter to play again", True, (230, 230, 230)
            )
            screen.blit(
                again_surf, again_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
            )

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(run())
