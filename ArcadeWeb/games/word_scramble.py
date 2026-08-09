import asyncio
import random
import sys

import pygame

WIDTH, HEIGHT = 900, 650
BG_COLOR = (26, 28, 40)
TEXT_COLOR = (230, 230, 240)
TILE_COLOR = (70, 76, 100)
TILE_DONE_COLOR = (44, 48, 66)
ANSWER_SLOT_COLOR = (50, 55, 76)
CORRECT_COLOR = (90, 200, 130)
WRONG_COLOR = (220, 90, 100)

WORDS = [
    "PYTHON", "GALAXY", "ROCKET", "PUZZLE", "WIZARD",
    "DRAGON", "CIRCUIT", "MYSTERY", "VOYAGE", "QUANTUM",
]

TILE_SIZE = 64
TILE_GAP = 12
FEEDBACK_MS = 700


def scramble(word):
    letters = list(word)
    shuffled = letters[:]
    while shuffled == letters:
        random.shuffle(shuffled)
    return shuffled


def scramble_rects(count):
    total_w = count * TILE_SIZE + (count - 1) * TILE_GAP
    start_x = (WIDTH - total_w) // 2
    return [
        pygame.Rect(start_x + i * (TILE_SIZE + TILE_GAP), 380, TILE_SIZE, TILE_SIZE)
        for i in range(count)
    ]


def answer_rects(count):
    total_w = count * TILE_SIZE + (count - 1) * TILE_GAP
    start_x = (WIDTH - total_w) // 2
    return [
        pygame.Rect(start_x + i * (TILE_SIZE + TILE_GAP), 260, TILE_SIZE, TILE_SIZE)
        for i in range(count)
    ]


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


async def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    pygame.display.set_caption("Word Scramble")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 56, bold=True)
    hud_font = pygame.font.SysFont(None, 32)
    tile_font = pygame.font.SysFont(None, 40, bold=True)
    big_font = pygame.font.SysFont(None, 56, bold=True)
    subtitle_font = pygame.font.SysFont(None, 26)

    order = random.sample(WORDS, len(WORDS))

    def start_word(index):
        word = order[index]
        letters = scramble(word)
        return word, letters, [], None, 0

    word, letters, answer, feedback, feedback_at = start_word(0)
    word_index = 0
    correct_count = 0
    game_over = False
    running = True
    paused = False
    pause_started_at = 0

    resume_rect = pygame.Rect(WIDTH // 2 - PAUSE_BTN_W // 2, HEIGHT // 2 - 20, PAUSE_BTN_W, PAUSE_BTN_H)
    restart_rect = pygame.Rect(WIDTH // 2 - PAUSE_BTN_W // 2, HEIGHT // 2 + 55, PAUSE_BTN_W, PAUSE_BTN_H)
    home_menu_rect = pygame.Rect(WIDTH // 2 - PAUSE_BTN_W // 2, HEIGHT // 2 + 130, PAUSE_BTN_W, PAUSE_BTN_H)

    def restart_game():
        nonlocal order, word, letters, answer, feedback, feedback_at, word_index, correct_count, game_over
        order = random.sample(WORDS, len(WORDS))
        word, letters, answer, feedback, feedback_at = start_word(0)
        word_index = 0
        correct_count = 0
        game_over = False

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
                elif game_over and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    restart_game()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HOME_RECT.collidepoint(event.pos):
                    running = False
                elif paused:
                    if resume_rect.collidepoint(event.pos):
                        feedback_at += now - pause_started_at
                        paused = False
                    elif restart_rect.collidepoint(event.pos):
                        restart_game()
                        paused = False
                    elif home_menu_rect.collidepoint(event.pos):
                        running = False
                elif PAUSE_RECT.collidepoint(event.pos):
                    paused = True
                    pause_started_at = now
                elif game_over:
                    restart_game()
                elif feedback is None:
                    s_rects = scramble_rects(len(letters))
                    for i, rect in enumerate(s_rects):
                        if i not in answer and rect.collidepoint(event.pos):
                            answer.append(i)
                            break
                    else:
                        a_rects = answer_rects(len(word))
                        for pos, rect in enumerate(a_rects):
                            if pos < len(answer) and rect.collidepoint(event.pos):
                                answer.pop(pos)
                                break

        if not paused:
            if feedback is None and len(answer) == len(word):
                attempt = "".join(letters[i] for i in answer)
                if attempt == word:
                    feedback = "correct"
                    correct_count += 1
                else:
                    feedback = "wrong"
                feedback_at = now

            if feedback is not None and now - feedback_at >= FEEDBACK_MS:
                if word_index + 1 >= len(order):
                    game_over = True
                else:
                    word_index += 1
                    word, letters, answer, feedback, feedback_at = start_word(word_index)

        screen.fill(BG_COLOR)

        title_surf = title_font.render("Word Scramble", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))

        if not game_over:
            progress_surf = hud_font.render(
                f"Word {word_index + 1} / {len(order)}   Correct: {correct_count}", True, (170, 175, 195)
            )
            screen.blit(progress_surf, progress_surf.get_rect(center=(WIDTH // 2, 110)))

            a_rects = answer_rects(len(word))
            for pos, rect in enumerate(a_rects):
                color = ANSWER_SLOT_COLOR
                if feedback == "correct":
                    color = CORRECT_COLOR
                elif feedback == "wrong":
                    color = WRONG_COLOR
                pygame.draw.rect(screen, color, rect, border_radius=10)
                pygame.draw.rect(screen, (255, 255, 255), rect, width=2, border_radius=10)
                if pos < len(answer):
                    letter = letters[answer[pos]]
                    letter_surf = tile_font.render(letter, True, (255, 255, 255))
                    screen.blit(letter_surf, letter_surf.get_rect(center=rect.center))

            s_rects = scramble_rects(len(letters))
            for i, rect in enumerate(s_rects):
                placed = i in answer
                color = TILE_DONE_COLOR if placed else TILE_COLOR
                pygame.draw.rect(screen, color, rect, border_radius=10)
                pygame.draw.rect(screen, (255, 255, 255), rect, width=2, border_radius=10)
                if not placed:
                    letter_surf = tile_font.render(letters[i], True, (255, 255, 255))
                    screen.blit(letter_surf, letter_surf.get_rect(center=rect.center))

            if feedback == "wrong":
                msg_surf = hud_font.render("Try again!", True, WRONG_COLOR)
                screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH // 2, 480)))
            elif feedback == "correct":
                msg_surf = hud_font.render("Correct!", True, CORRECT_COLOR)
                screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH // 2, 480)))
            else:
                hint_surf = subtitle_font.render(
                    "Click letters to spell the word, click again to undo", True, (170, 175, 195)
                )
                screen.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, 480)))
        else:
            done_surf = big_font.render(
                f"Finished! {correct_count} / {len(order)} correct", True, (255, 255, 255)
            )
            screen.blit(done_surf, done_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            again_surf = subtitle_font.render(
                "Click or press Enter to play again", True, (230, 230, 230)
            )
            screen.blit(
                again_surf, again_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            )

        draw_home_icon(screen, HOME_RECT)
        draw_pause_icon(screen, PAUSE_RECT)

        if paused:
            draw_pause_menu(screen, title_font, hud_font, resume_rect, restart_rect, home_menu_rect)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(run())
