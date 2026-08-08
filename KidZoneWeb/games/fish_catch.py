import asyncio
import math
import random

import pygame

WIDTH, HEIGHT = 900, 700
BG_TOP = (40, 110, 190)
BG_BOTTOM = (100, 170, 220)
TEXT_COLOR = (255, 255, 255)
TITLE_COLOR = (255, 255, 255)

FISH_COLORS = [
    (255, 150, 60),
    (255, 210, 60),
    (230, 90, 130),
    (120, 220, 200),
]
JUNK_COLOR = (90, 80, 75)
JUNK_CHANCE = 0.2

FISH_W, FISH_H = 70, 40
LANE_COUNT = 5
LANE_TOP = 190
LANE_GAP = 90
MIN_SPEED, MAX_SPEED = 1.6, 3.6
SPAWN_MIN_MS = 350
SPAWN_MAX_MS = 800

START_LIVES = 3


class Fish:
    def __init__(self):
        self.lane = random.randint(0, LANE_COUNT - 1)
        self.y = LANE_TOP + self.lane * LANE_GAP + random.uniform(-10, 10)
        self.dir = random.choice([-1, 1])
        self.x = -FISH_W if self.dir == 1 else WIDTH + FISH_W
        self.speed = random.uniform(MIN_SPEED, MAX_SPEED)
        self.is_junk = random.random() < JUNK_CHANCE
        self.color = JUNK_COLOR if self.is_junk else random.choice(FISH_COLORS)
        self.caught = False
        self.bob_phase = random.uniform(0, 6.28)

    def update(self, now):
        self.x += self.speed * self.dir
        self.y += math.sin(now / 300.0 + self.bob_phase) * 0.3

    def off_screen(self):
        return self.x < -FISH_W * 2 or self.x > WIDTH + FISH_W * 2

    def contains(self, pos):
        dx = (pos[0] - self.x) / (FISH_W / 2)
        dy = (pos[1] - self.y) / (FISH_H / 2)
        return dx * dx + dy * dy <= 1.0

    def draw(self, screen):
        facing = self.dir
        body_rect = pygame.Rect(0, 0, FISH_W * 0.7, FISH_H)
        body_rect.center = (self.x, self.y)

        if self.is_junk:
            pygame.draw.rect(screen, self.color, body_rect, border_radius=8)
            font = pygame.font.SysFont(None, 26, bold=True)
            label = font.render("X", True, (255, 255, 255))
            screen.blit(label, label.get_rect(center=body_rect.center))
            return

        tail_x = self.x - facing * FISH_W * 0.35
        tail_pts = [
            (tail_x, self.y),
            (tail_x - facing * 20, self.y - 16),
            (tail_x - facing * 20, self.y + 16),
        ]
        pygame.draw.polygon(screen, self.color, tail_pts)
        pygame.draw.ellipse(screen, self.color, body_rect)
        eye_x = self.x + facing * FISH_W * 0.22
        pygame.draw.circle(screen, (255, 255, 255), (int(eye_x), int(self.y - 4)), 6)
        pygame.draw.circle(screen, (20, 20, 20), (int(eye_x), int(self.y - 4)), 3)


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
    pygame.display.set_caption("Fish Catch")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 64, bold=True)
    subtitle_font = pygame.font.SysFont(None, 30)
    hud_font = pygame.font.SysFont(None, 40, bold=True)
    big_font = pygame.font.SysFont(None, 72, bold=True)

    def new_game():
        return [], 0, START_LIVES, pygame.time.get_ticks() + random.randint(
            SPAWN_MIN_MS, SPAWN_MAX_MS
        )

    fish_list, score, lives, next_spawn_at = new_game()
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
                    fish_list, score, lives, next_spawn_at = new_game()
                    game_over = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_over:
                    fish_list, score, lives, next_spawn_at = new_game()
                    game_over = False
                else:
                    for fish in fish_list:
                        if not fish.caught and fish.contains(event.pos):
                            fish.caught = True
                            if fish.is_junk:
                                lives -= 1
                            else:
                                score += 1
                            break

        if not game_over:
            if now >= next_spawn_at:
                fish_list.append(Fish())
                next_spawn_at = now + random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS)

            for fish in fish_list:
                fish.update(now)

            fish_list = [f for f in fish_list if not f.caught and not f.off_screen()]

            if lives <= 0:
                game_over = True

        draw_background(screen)

        title_surf = title_font.render("Fish Catch", True, TITLE_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        subtitle_surf = subtitle_font.render(
            "Click the fish, avoid the junk!", True, (230, 240, 255)
        )
        screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        for fish in fish_list:
            fish.draw(screen)

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
