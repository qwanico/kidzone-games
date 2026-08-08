import math
import random
import sys

import pygame

WIDTH, HEIGHT = 900, 700
BG_TOP = (25, 25, 60)
BG_BOTTOM = (60, 50, 110)
TEXT_COLOR = (255, 255, 255)
TITLE_COLOR = (255, 255, 255)

BASKET_W, BASKET_H = 130, 46
BASKET_Y = HEIGHT - 70
BASKET_COLOR = (200, 140, 60)

STAR_COLOR = (255, 220, 90)
ROCK_COLOR = (110, 110, 120)
ITEM_RADIUS = 24
ROCK_CHANCE = 0.28
MIN_SPEED, MAX_SPEED = 2.4, 5.0
SPAWN_MIN_MS = 300
SPAWN_MAX_MS = 700

START_LIVES = 3


def draw_star(screen, center, radius, color):
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = radius if i % 2 == 0 else radius * 0.45
        points.append((center[0] + math.cos(angle) * r, center[1] - math.sin(angle) * r))
    pygame.draw.polygon(screen, color, points)


class FallingItem:
    def __init__(self):
        self.x = random.randint(ITEM_RADIUS, WIDTH - ITEM_RADIUS)
        self.y = -ITEM_RADIUS
        self.speed = random.uniform(MIN_SPEED, MAX_SPEED)
        self.is_rock = random.random() < ROCK_CHANCE
        self.caught = False
        self.spin = random.uniform(0, 6.28)

    def update(self):
        self.y += self.speed
        self.spin += 0.05

    def off_screen(self):
        return self.y > HEIGHT + ITEM_RADIUS

    def rect(self):
        return pygame.Rect(
            self.x - ITEM_RADIUS, self.y - ITEM_RADIUS, ITEM_RADIUS * 2, ITEM_RADIUS * 2
        )

    def draw(self, screen):
        if self.is_rock:
            pts = []
            for i in range(7):
                angle = self.spin + i * (2 * math.pi / 7)
                r = ITEM_RADIUS * (0.8 + 0.2 * math.sin(i * 2))
                pts.append((self.x + math.cos(angle) * r, self.y + math.sin(angle) * r))
            pygame.draw.polygon(screen, ROCK_COLOR, pts)
        else:
            draw_star(screen, (self.x, self.y), ITEM_RADIUS, STAR_COLOR)


def draw_background(screen):
    for i in range(HEIGHT):
        t = i / HEIGHT
        color = tuple(
            int(BG_TOP[c] + (BG_BOTTOM[c] - BG_TOP[c]) * t) for c in range(3)
        )
        pygame.draw.line(screen, color, (0, i), (WIDTH, i))


def draw_basket(screen, x):
    rect = pygame.Rect(0, 0, BASKET_W, BASKET_H)
    rect.center = (x, BASKET_Y)
    pygame.draw.polygon(
        screen,
        BASKET_COLOR,
        [
            (rect.left + 10, rect.top),
            (rect.right - 10, rect.top),
            (rect.right, rect.bottom),
            (rect.left, rect.bottom),
        ],
    )
    for i in range(3):
        lx = rect.left + 20 + i * (rect.width - 40) / 2
        pygame.draw.line(screen, (150, 100, 40), (lx, rect.top + 6), (lx, rect.bottom - 6), 3)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Star Catcher")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 64, bold=True)
    subtitle_font = pygame.font.SysFont(None, 30)
    hud_font = pygame.font.SysFont(None, 40, bold=True)
    big_font = pygame.font.SysFont(None, 72, bold=True)

    def new_game():
        return [], 0, START_LIVES, WIDTH // 2, pygame.time.get_ticks() + random.randint(
            SPAWN_MIN_MS, SPAWN_MAX_MS
        )

    items, score, lives, basket_x, next_spawn_at = new_game()
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
                    items, score, lives, basket_x, next_spawn_at = new_game()
                    game_over = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_over:
                items, score, lives, basket_x, next_spawn_at = new_game()
                game_over = False
            elif event.type == pygame.MOUSEMOTION and not game_over:
                basket_x = event.pos[0]

        keys = pygame.key.get_pressed()
        if not game_over:
            if keys[pygame.K_LEFT]:
                basket_x -= 8
            if keys[pygame.K_RIGHT]:
                basket_x += 8
            basket_x = max(BASKET_W // 2, min(WIDTH - BASKET_W // 2, basket_x))

            if now >= next_spawn_at:
                items.append(FallingItem())
                next_spawn_at = now + random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS)

            basket_rect = pygame.Rect(0, 0, BASKET_W, BASKET_H)
            basket_rect.center = (basket_x, BASKET_Y)

            remaining = []
            for item in items:
                item.update()
                if not item.caught and basket_rect.collidepoint(item.x, item.y) and item.y > BASKET_Y - BASKET_H // 2:
                    item.caught = True
                    if item.is_rock:
                        lives -= 1
                    else:
                        score += 1
                    continue
                if not item.off_screen():
                    remaining.append(item)
            items = remaining

            if lives <= 0:
                game_over = True

        draw_background(screen)

        title_surf = title_font.render("Star Catcher", True, TITLE_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        subtitle_surf = subtitle_font.render(
            "Move the basket to catch stars, dodge rocks!", True, (220, 220, 255)
        )
        screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        for item in items:
            item.draw(screen)

        draw_basket(screen, basket_x)

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

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
