import math
import random
import sys

import pygame

WIDTH, HEIGHT = 900, 700
BG_COLOR = (225, 235, 200)
TEXT_COLOR = (50, 50, 60)
TITLE_COLOR = (60, 60, 90)

ROUND_SECONDS = 30
BUG_RADIUS = 24
MIN_SPEED, MAX_SPEED = 1.4, 3.2
SPAWN_MIN_MS = 300
SPAWN_MAX_MS = 750

BUG_COLORS = [
    (90, 70, 170),
    (170, 60, 60),
    (60, 140, 90),
    (200, 130, 40),
]
SQUASH_FLASH_MS = 200


class Bug:
    def __init__(self):
        edge = random.choice(["top", "bottom", "left", "right"])
        if edge == "top":
            self.x, self.y = random.uniform(0, WIDTH), -BUG_RADIUS
        elif edge == "bottom":
            self.x, self.y = random.uniform(0, WIDTH), HEIGHT + BUG_RADIUS
        elif edge == "left":
            self.x, self.y = -BUG_RADIUS, random.uniform(0, HEIGHT)
        else:
            self.x, self.y = WIDTH + BUG_RADIUS, random.uniform(0, HEIGHT)

        target_x = random.uniform(WIDTH * 0.2, WIDTH * 0.8)
        target_y = random.uniform(HEIGHT * 0.2, HEIGHT * 0.8)
        angle = math.atan2(target_y - self.y, target_x - self.x)
        angle += random.uniform(-0.4, 0.4)
        speed = random.uniform(MIN_SPEED, MAX_SPEED)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = random.choice(BUG_COLORS)
        self.wiggle_phase = random.uniform(0, 6.28)
        self.squashed = False
        self.squash_at = 0
        self.leg_offset = 0.0

    def update(self, now):
        if self.squashed:
            return
        self.leg_offset = math.sin(now / 60.0 + self.wiggle_phase)
        self.x += self.vx + self.leg_offset * 0.6
        self.y += self.vy

    def off_screen(self):
        margin = BUG_RADIUS * 3
        return (
            self.x < -margin
            or self.x > WIDTH + margin
            or self.y < -margin
            or self.y > HEIGHT + margin
        )

    def contains(self, pos):
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return dx * dx + dy * dy <= BUG_RADIUS * BUG_RADIUS

    def draw(self, screen, now):
        if self.squashed:
            t = (now - self.squash_at) / SQUASH_FLASH_MS
            if t > 1:
                return
            radius = int(BUG_RADIUS * (1 + t))
            alpha_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                alpha_surf,
                (255, 255, 255, int(180 * (1 - t))),
                (radius, radius),
                radius,
            )
            screen.blit(alpha_surf, (self.x - radius, self.y - radius))
            return

        angle = math.atan2(self.vy, self.vx)
        body_len = BUG_RADIUS * 1.4
        for i in range(3):
            leg_a = angle + math.pi / 2 + self.leg_offset * 0.3
            leg_b = angle - math.pi / 2 - self.leg_offset * 0.3
            offset = (i - 1) * 10
            base_x = self.x - math.cos(angle) * offset
            base_y = self.y - math.sin(angle) * offset
            pygame.draw.line(
                screen,
                (40, 40, 40),
                (base_x, base_y),
                (base_x + math.cos(leg_a) * 16, base_y + math.sin(leg_a) * 16),
                3,
            )
            pygame.draw.line(
                screen,
                (40, 40, 40),
                (base_x, base_y),
                (base_x + math.cos(leg_b) * 16, base_y + math.sin(leg_b) * 16),
                3,
            )

        body_rect = pygame.Rect(0, 0, body_len, BUG_RADIUS * 1.1)
        body_rect.center = (self.x, self.y)
        pygame.draw.ellipse(screen, self.color, body_rect)
        pygame.draw.line(
            screen,
            (25, 25, 25),
            body_rect.midtop,
            body_rect.midbottom,
            2,
        )

        head_x = self.x + math.cos(angle) * body_len / 2
        head_y = self.y + math.sin(angle) * body_len / 2
        pygame.draw.circle(screen, (25, 25, 25), (int(head_x), int(head_y)), 8)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Bug Squasher")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 64, bold=True)
    subtitle_font = pygame.font.SysFont(None, 30)
    hud_font = pygame.font.SysFont(None, 40, bold=True)
    big_font = pygame.font.SysFont(None, 72, bold=True)

    def new_game():
        return [], 0, pygame.time.get_ticks() + ROUND_SECONDS * 1000, pygame.time.get_ticks()

    bugs, score, end_time, next_spawn_at = new_game()
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
                    bugs, score, end_time, next_spawn_at = new_game()
                    game_over = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_over:
                    bugs, score, end_time, next_spawn_at = new_game()
                    game_over = False
                else:
                    for bug in bugs:
                        if not bug.squashed and bug.contains(event.pos):
                            bug.squashed = True
                            bug.squash_at = now
                            score += 1
                            break

        if not game_over:
            if now >= next_spawn_at:
                bugs.append(Bug())
                next_spawn_at = now + random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS)

            for bug in bugs:
                bug.update(now)

            bugs = [
                b
                for b in bugs
                if not b.off_screen()
                and (not b.squashed or now - b.squash_at < SQUASH_FLASH_MS)
            ]

            if now >= end_time:
                game_over = True

        screen.fill(BG_COLOR)

        title_surf = title_font.render("Bug Squasher", True, TITLE_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        subtitle_surf = subtitle_font.render(
            "Click the bugs before they scurry away!", True, (70, 80, 60)
        )
        screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        for bug in bugs:
            bug.draw(screen, now)

        score_surf = hud_font.render(f"Score: {score}", True, TEXT_COLOR)
        screen.blit(score_surf, (30, 140))

        seconds_left = max(0, (end_time - now) // 1000 + (0 if game_over else 1))
        timer_surf = hud_font.render(f"Time: {seconds_left}", True, TEXT_COLOR)
        screen.blit(timer_surf, timer_surf.get_rect(topright=(WIDTH - 30, 140)))

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
