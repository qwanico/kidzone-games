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
    paused = False
    pause_started_at = 0

    resume_rect = pygame.Rect(WIDTH // 2 - PAUSE_BTN_W // 2, HEIGHT // 2 - 20, PAUSE_BTN_W, PAUSE_BTN_H)
    restart_rect = pygame.Rect(WIDTH // 2 - PAUSE_BTN_W // 2, HEIGHT // 2 + 55, PAUSE_BTN_W, PAUSE_BTN_H)
    home_menu_rect = pygame.Rect(WIDTH // 2 - PAUSE_BTN_W // 2, HEIGHT // 2 + 130, PAUSE_BTN_W, PAUSE_BTN_H)

    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif paused:
                    pass
                elif state == "final" and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    state, go_at, go_time, times, round_num = new_game()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HOME_RECT.collidepoint(event.pos):
                    running = False
                elif paused:
                    if resume_rect.collidepoint(event.pos):
                        go_at += now - pause_started_at
                        paused = False
                    elif restart_rect.collidepoint(event.pos):
                        state, go_at, go_time, times, round_num = new_game()
                        paused = False
                    elif home_menu_rect.collidepoint(event.pos):
                        running = False
                elif state != "go" and PAUSE_RECT.collidepoint(event.pos):
                    paused = True
                    pause_started_at = now
                elif state == "wait":
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

        if not paused:
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

        draw_home_icon(screen, HOME_RECT)
        if state != "go":
            draw_pause_icon(screen, PAUSE_RECT)

        if paused:
            draw_pause_menu(screen, title_font, hud_font, resume_rect, restart_rect, home_menu_rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
