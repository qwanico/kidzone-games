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


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
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

    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif game_over and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    order = random.sample(WORDS, len(WORDS))
                    word, letters, answer, feedback, feedback_at = start_word(0)
                    word_index = 0
                    correct_count = 0
                    game_over = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_over:
                    order = random.sample(WORDS, len(WORDS))
                    word, letters, answer, feedback, feedback_at = start_word(0)
                    word_index = 0
                    correct_count = 0
                    game_over = False
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

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
