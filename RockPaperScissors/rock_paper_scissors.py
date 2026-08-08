import random
import sys

import pygame

WIDTH, HEIGHT = 800, 650
BG_COLOR = (26, 28, 40)
TEXT_COLOR = (230, 230, 240)
PANEL_COLOR = (40, 44, 62)

CHOICES = ["rock", "paper", "scissors"]
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}

BUTTON_SIZE = 160
BUTTON_GAP = 50
BUTTON_TOP = 400
BUTTON_COLORS = {
    "rock": (200, 110, 90),
    "paper": (100, 170, 220),
    "scissors": (220, 190, 90),
}


def draw_choice(screen, choice, center, radius, color):
    if choice == "rock":
        pygame.draw.circle(screen, color, center, radius)
    elif choice == "paper":
        rect = pygame.Rect(0, 0, radius * 1.8, radius * 1.8)
        rect.center = center
        pygame.draw.rect(screen, color, rect, border_radius=14)
    elif choice == "scissors":
        thickness = max(6, radius // 5)
        pygame.draw.line(
            screen, color,
            (center[0] - radius * 0.7, center[1] - radius * 0.7),
            (center[0] + radius * 0.7, center[1] + radius * 0.7),
            thickness,
        )
        pygame.draw.line(
            screen, color,
            (center[0] + radius * 0.7, center[1] - radius * 0.7),
            (center[0] - radius * 0.7, center[1] + radius * 0.7),
            thickness,
        )
        pygame.draw.circle(screen, color, (int(center[0] - radius * 0.7), int(center[1] + radius * 0.7)), thickness)
        pygame.draw.circle(screen, color, (int(center[0] + radius * 0.7), int(center[1] + radius * 0.7)), thickness)


def button_rects():
    total_w = len(CHOICES) * BUTTON_SIZE + (len(CHOICES) - 1) * BUTTON_GAP
    start_x = (WIDTH - total_w) // 2
    rects = {}
    for i, choice in enumerate(CHOICES):
        x = start_x + i * (BUTTON_SIZE + BUTTON_GAP)
        rects[choice] = pygame.Rect(x, BUTTON_TOP, BUTTON_SIZE, BUTTON_SIZE)
    return rects


def judge(player, computer):
    if player == computer:
        return "tie"
    return "win" if BEATS[player] == computer else "lose"


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rock Paper Scissors")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 56, bold=True)
    hud_font = pygame.font.SysFont(None, 32)
    result_font = pygame.font.SysFont(None, 48, bold=True)
    label_font = pygame.font.SysFont(None, 28, bold=True)
    subtitle_font = pygame.font.SysFont(None, 24)

    rects = button_rects()
    player_choice = None
    computer_choice = None
    result = None
    wins = losses = ties = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for choice, rect in rects.items():
                    if rect.collidepoint(event.pos):
                        player_choice = choice
                        computer_choice = random.choice(CHOICES)
                        result = judge(player_choice, computer_choice)
                        if result == "win":
                            wins += 1
                        elif result == "lose":
                            losses += 1
                        else:
                            ties += 1
                        break

        screen.fill(BG_COLOR)

        title_surf = title_font.render("Rock Paper Scissors", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 50)))
        record_surf = hud_font.render(
            f"Wins: {wins}   Losses: {losses}   Ties: {ties}", True, (170, 175, 195)
        )
        screen.blit(record_surf, record_surf.get_rect(center=(WIDTH // 2, 95)))

        panel_rect = pygame.Rect(80, 140, WIDTH - 160, 210)
        pygame.draw.rect(screen, PANEL_COLOR, panel_rect, border_radius=16)

        you_center = (panel_rect.left + panel_rect.width // 4, panel_rect.centery)
        cpu_center = (panel_rect.right - panel_rect.width // 4, panel_rect.centery)

        you_label = label_font.render("You", True, TEXT_COLOR)
        screen.blit(you_label, you_label.get_rect(center=(you_center[0], panel_rect.top + 25)))
        cpu_label = label_font.render("Computer", True, TEXT_COLOR)
        screen.blit(cpu_label, cpu_label.get_rect(center=(cpu_center[0], panel_rect.top + 25)))

        if player_choice:
            draw_choice(screen, player_choice, (you_center[0], you_center[1] + 15), 55, BUTTON_COLORS[player_choice])
            draw_choice(screen, computer_choice, (cpu_center[0], cpu_center[1] + 15), 55, BUTTON_COLORS[computer_choice])
        else:
            hint_surf = subtitle_font.render("Pick a move below to play!", True, (170, 175, 195))
            screen.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, panel_rect.centery + 15)))

        if result:
            labels = {"win": "You Win!", "lose": "Computer Wins!", "tie": "Tie!"}
            colors = {"win": (110, 220, 140), "lose": (240, 110, 110), "tie": (220, 200, 100)}
            result_surf = result_font.render(labels[result], True, colors[result])
            screen.blit(result_surf, result_surf.get_rect(center=(WIDTH // 2, 375)))

        for choice, rect in rects.items():
            pygame.draw.rect(screen, BUTTON_COLORS[choice], rect, border_radius=16)
            pygame.draw.rect(screen, (255, 255, 255), rect, width=3, border_radius=16)
            draw_choice(screen, choice, rect.center, 45, (255, 255, 255))
            name_surf = label_font.render(choice.capitalize(), True, (255, 255, 255))
            screen.blit(name_surf, name_surf.get_rect(midtop=(rect.centerx, rect.bottom + 8)))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
