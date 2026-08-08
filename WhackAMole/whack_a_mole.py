import random
import sys

import pygame

WIDTH, HEIGHT = 900, 700
BG_COLOR = (140, 200, 110)
HOLE_COLOR = (90, 60, 40)
HOLE_RIM_COLOR = (60, 40, 25)
TEXT_COLOR = (50, 50, 60)
TITLE_COLOR = (60, 60, 90)

ROWS, COLS = 3, 3
HOLE_RADIUS = 70
GRID_GAP_X = 260
GRID_GAP_Y = 170
GRID_TOP = 260

ROUND_SECONDS = 30
MOLE_MIN_UP_MS = 550
MOLE_MAX_UP_MS = 1100
MOLE_MIN_GAP_MS = 400
MOLE_MAX_GAP_MS = 1200

MOLE_BODY = (120, 80, 55)
MOLE_BODY_DARK = (95, 60, 40)
MOLE_NOSE = (230, 150, 150)
WHACKED_COLOR = (230, 90, 90)


class Hole:
    def __init__(self, center):
        self.center = center
        self.up = False
        self.whacked = False
        self.next_event_at = pygame.time.get_ticks() + random.randint(
            MOLE_MIN_GAP_MS, MOLE_MAX_GAP_MS
        )
        self.up_until = 0

    def update(self, now):
        if not self.up and now >= self.next_event_at:
            self.up = True
            self.whacked = False
            self.up_until = now + random.randint(MOLE_MIN_UP_MS, MOLE_MAX_UP_MS)
        elif self.up and now >= self.up_until:
            self.up = False
            self.next_event_at = now + random.randint(
                MOLE_MIN_GAP_MS, MOLE_MAX_GAP_MS
            )

    def try_whack(self, pos, now):
        if not self.up or self.whacked:
            return False
        dx = pos[0] - self.center[0]
        dy = pos[1] - (self.center[1] - 25)
        if dx * dx + dy * dy <= HOLE_RADIUS * HOLE_RADIUS:
            self.whacked = True
            self.up = False
            self.next_event_at = now + random.randint(
                MOLE_MIN_GAP_MS, MOLE_MAX_GAP_MS
            )
            return True
        return False

    def draw(self, screen):
        pygame.draw.ellipse(
            screen,
            HOLE_RIM_COLOR,
            (
                self.center[0] - HOLE_RADIUS - 6,
                self.center[1] - 22,
                (HOLE_RADIUS + 6) * 2,
                70,
            ),
        )
        if self.up:
            body_color = WHACKED_COLOR if self.whacked else MOLE_BODY
            dark_color = MOLE_BODY_DARK
            head_center = (self.center[0], self.center[1] - 25)
            pygame.draw.circle(screen, body_color, head_center, HOLE_RADIUS - 10)
            ear_r = 16
            pygame.draw.circle(
                screen, dark_color, (head_center[0] - 40, head_center[1] - 45), ear_r
            )
            pygame.draw.circle(
                screen, dark_color, (head_center[0] + 40, head_center[1] - 45), ear_r
            )
            eye_y = head_center[1] - 8
            pygame.draw.circle(screen, (30, 30, 30), (head_center[0] - 18, eye_y), 6)
            pygame.draw.circle(screen, (30, 30, 30), (head_center[0] + 18, eye_y), 6)
            pygame.draw.ellipse(
                screen,
                MOLE_NOSE,
                (head_center[0] - 14, head_center[1] + 8, 28, 18),
            )
        pygame.draw.ellipse(
            screen,
            HOLE_COLOR,
            (
                self.center[0] - HOLE_RADIUS,
                self.center[1] - 15,
                HOLE_RADIUS * 2,
                55,
            ),
        )


def build_holes():
    holes = []
    grid_w = (COLS - 1) * GRID_GAP_X
    start_x = (WIDTH - grid_w) // 2
    for row in range(ROWS):
        for col in range(COLS):
            x = start_x + col * GRID_GAP_X
            y = GRID_TOP + row * GRID_GAP_Y
            holes.append(Hole((x, y)))
    return holes


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Whack-a-Mole")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 64, bold=True)
    subtitle_font = pygame.font.SysFont(None, 30)
    hud_font = pygame.font.SysFont(None, 40, bold=True)
    big_font = pygame.font.SysFont(None, 72, bold=True)

    def new_game():
        return build_holes(), 0, pygame.time.get_ticks() + ROUND_SECONDS * 1000

    holes, score, end_time = new_game()
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
                    holes, score, end_time = new_game()
                    game_over = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_over:
                    holes, score, end_time = new_game()
                    game_over = False
                else:
                    for hole in holes:
                        if hole.try_whack(event.pos, now):
                            score += 1
                            break

        if not game_over:
            for hole in holes:
                hole.update(now)
            if now >= end_time:
                game_over = True

        screen.fill(BG_COLOR)

        title_surf = title_font.render("Whack-a-Mole", True, TITLE_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        subtitle_surf = subtitle_font.render(
            "Click the moles before they hide!", True, (70, 70, 80)
        )
        screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        for hole in holes:
            hole.draw(screen)

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
