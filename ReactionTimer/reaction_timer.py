import random
import sys

import pygame

WIDTH, HEIGHT = 800, 600
TEXT_COLOR = (255, 255, 255)

WAIT_COLOR = (200, 70, 70)
GO_COLOR = (70, 190, 110)
EARLY_COLOR = (140, 70, 190)
IDLE_COLOR = (40, 44, 60)

ROUNDS = 5
MIN_DELAY_MS = 1000
MAX_DELAY_MS = 3500
EARLY_MESSAGE_MS = 1000


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Reaction Timer")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 56, bold=True)
    big_font = pygame.font.SysFont(None, 72, bold=True)
    hud_font = pygame.font.SysFont(None, 32)
    subtitle_font = pygame.font.SysFont(None, 26)

    def start_round(now):
        return now + random.randint(MIN_DELAY_MS, MAX_DELAY_MS)

    def new_game():
        now = pygame.time.get_ticks()
        return "wait", start_round(now), 0, [], 0

    state, go_at, go_time, times, round_num = new_game()
    running = True

    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif state == "final" and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    state, go_at, go_time, times, round_num = new_game()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "wait":
                    state = "early"
                    go_at = now + EARLY_MESSAGE_MS
                elif state == "go":
                    reaction = now - go_time
                    times.append(reaction)
                    round_num += 1
                    if round_num >= ROUNDS:
                        state = "final"
                    else:
                        state = "wait"
                        go_at = start_round(now)
                elif state == "early":
                    pass
                elif state == "final":
                    state, go_at, go_time, times, round_num = new_game()

        if state == "wait" and now >= go_at:
            state = "go"
            go_time = now
        elif state == "early" and now >= go_at:
            state = "wait"
            go_at = start_round(now)

        if state == "wait":
            bg = WAIT_COLOR
            message = "Wait for green..."
        elif state == "go":
            bg = GO_COLOR
            message = "Click now!"
        elif state == "early":
            bg = EARLY_COLOR
            message = "Too soon! Wait for green."
        else:
            bg = IDLE_COLOR
            message = ""

        screen.fill(bg)

        title_surf = title_font.render("Reaction Timer", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))

        if state != "final":
            round_surf = hud_font.render(f"Round {round_num + 1} / {ROUNDS}", True, TEXT_COLOR)
            screen.blit(round_surf, round_surf.get_rect(center=(WIDTH // 2, 110)))
            msg_surf = big_font.render(message, True, TEXT_COLOR)
            screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        else:
            avg = sum(times) / len(times) if times else 0
            best = min(times) if times else 0
            done_surf = big_font.render(f"Average: {avg:.0f} ms", True, TEXT_COLOR)
            screen.blit(done_surf, done_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
            best_surf = hud_font.render(f"Best: {best} ms", True, TEXT_COLOR)
            screen.blit(best_surf, best_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10)))
            times_str = "  ".join(f"{t}ms" for t in times)
            times_surf = subtitle_font.render(times_str, True, (200, 200, 210))
            screen.blit(times_surf, times_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 55)))
            again_surf = subtitle_font.render(
                "Click or press Enter to play again", True, (230, 230, 230)
            )
            screen.blit(
                again_surf, again_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 110))
            )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
