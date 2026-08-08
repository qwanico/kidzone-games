import sys

import pygame

WIDTH, HEIGHT = 600, 800
BG_COLOR = (22, 24, 34)
TEXT_COLOR = (255, 255, 255)

BLOCK_H = 42
DROP_Y = 560
START_WIDTH = 260

COLORS = [
    (230, 90, 110), (255, 170, 60), (255, 220, 60), (120, 210, 90),
    (90, 170, 230), (150, 100, 220), (240, 120, 170),
]

BASE_SPEED = 3.0
SPEED_STEP = 0.12
MAX_SPEED = 8.0


class Block:
    def __init__(self, x, w, y, color):
        self.x = x
        self.w = w
        self.y = y
        self.color = color

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.w), BLOCK_H)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Color Switch")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 48, bold=True)
    hud_font = pygame.font.SysFont(None, 40, bold=True)
    big_font = pygame.font.SysFont(None, 60, bold=True)
    subtitle_font = pygame.font.SysFont(None, 26)

    def new_game():
        base = Block((WIDTH - START_WIDTH) / 2, START_WIDTH, DROP_Y, COLORS[0])
        moving = Block(0.0, START_WIDTH, DROP_Y - BLOCK_H, COLORS[1])
        return [base], moving, 1.0, BASE_SPEED, 0

    stack, moving, direction, speed, score = new_game()
    game_over = False
    running = True

    def drop():
        nonlocal moving, direction, speed, score, game_over
        top = stack[-1]
        left = max(moving.x, top.x)
        right = min(moving.x + moving.w, top.x + top.w)
        overlap = right - left
        if overlap <= 4:
            game_over = True
            return
        placed = Block(left, overlap, moving.y, moving.color)
        stack.append(placed)
        score += 1
        for b in stack:
            b.y += BLOCK_H
        stack[:] = [b for b in stack if b.y < HEIGHT + BLOCK_H]
        speed = min(MAX_SPEED, speed + SPEED_STEP)
        direction = 1.0 if placed.x < WIDTH / 2 else -1.0
        start_x = 0.0 if direction > 0 else WIDTH - placed.w
        moving = Block(start_x, placed.w, placed.y - BLOCK_H, COLORS[len(stack) % len(COLORS)])

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if game_over:
                        stack, moving, direction, speed, score = new_game()
                        game_over = False
                    else:
                        drop()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_over:
                    stack, moving, direction, speed, score = new_game()
                    game_over = False
                else:
                    drop()

        if not game_over:
            moving.x += direction * speed
            if moving.x <= 0:
                moving.x = 0
                direction = 1.0
            elif moving.x + moving.w >= WIDTH:
                moving.x = WIDTH - moving.w
                direction = -1.0

        screen.fill(BG_COLOR)

        for b in stack:
            pygame.draw.rect(screen, b.color, b.rect())
            pygame.draw.rect(screen, (255, 255, 255), b.rect(), width=2)

        if not game_over:
            pygame.draw.rect(screen, moving.color, moving.rect())
            pygame.draw.rect(screen, (255, 255, 255), moving.rect(), width=2)

        title_surf = title_font.render("Color Switch", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 40)))
        score_surf = hud_font.render(f"Score: {score}", True, TEXT_COLOR)
        screen.blit(score_surf, score_surf.get_rect(center=(WIDTH // 2, 90)))

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            done_surf = big_font.render(f"Final Score: {score}", True, (255, 255, 255))
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
