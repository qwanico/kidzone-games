import subprocess
import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent
GAMES_DIR = BASE_DIR.parent
ICONS_DIR = BASE_DIR / "tile_icons"

WIDTH, HEIGHT = 1100, 1550
CARD_W, CARD_H = 250, 230
CARD_GAP = 36
COLS = 4
IMAGE_SIZE = 96

BG_COLOR = (24, 26, 38)
TEXT_COLOR = (225, 228, 240)
TITLE_COLOR = (120, 220, 255)
SUBTITLE_COLOR = (150, 155, 180)

GAMES = [
    {
        "name": "Snake",
        "comment": "Eat food, grow long,\ndon't hit yourself!",
        "python": GAMES_DIR / "Snake" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Snake" / "snake.py",
        "cwd": GAMES_DIR / "Snake",
        "color": (60, 140, 95),
        "hover": (48, 120, 78),
        "image": GAMES_DIR / "Snake" / "assets" / "snake_icon.png",
    },
    {
        "name": "Breakout",
        "comment": "Bounce the ball,\nbreak every brick!",
        "python": GAMES_DIR / "Breakout" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Breakout" / "breakout.py",
        "cwd": GAMES_DIR / "Breakout",
        "color": (90, 100, 160),
        "hover": (72, 82, 140),
        "image": GAMES_DIR / "Breakout" / "assets" / "breakout_icon.png",
    },
    {
        "name": "Flappy Bird",
        "comment": "Flap through the\npipes without hitting!",
        "python": GAMES_DIR / "FlappyBird" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "FlappyBird" / "flappy_bird.py",
        "cwd": GAMES_DIR / "FlappyBird",
        "color": (70, 150, 190),
        "hover": (55, 130, 170),
        "image": GAMES_DIR / "FlappyBird" / "assets" / "flappybird_icon.png",
    },
    {
        "name": "2048",
        "comment": "Slide and merge tiles\nto reach 2048!",
        "python": GAMES_DIR / "Game2048" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Game2048" / "game_2048.py",
        "cwd": GAMES_DIR / "Game2048",
        "color": (150, 120, 90),
        "hover": (130, 102, 74),
        "image": GAMES_DIR / "Game2048" / "assets" / "game2048_icon.png",
    },
    {
        "name": "Tic-Tac-Toe",
        "comment": "Outsmart the AI\nin classic X's and O's!",
        "python": GAMES_DIR / "TicTacToe" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "TicTacToe" / "tic_tac_toe.py",
        "cwd": GAMES_DIR / "TicTacToe",
        "color": (70, 76, 100),
        "hover": (56, 62, 84),
        "image": GAMES_DIR / "TicTacToe" / "assets" / "tictactoe_icon.png",
    },
    {
        "name": "Reaction Timer",
        "comment": "How fast are your\nreflexes? Test them!",
        "python": GAMES_DIR / "ReactionTimer" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "ReactionTimer" / "reaction_timer.py",
        "cwd": GAMES_DIR / "ReactionTimer",
        "color": (150, 70, 160),
        "hover": (130, 56, 140),
        "image": GAMES_DIR / "ReactionTimer" / "assets" / "reactiontimer_icon.png",
    },
    {
        "name": "Rock Paper Scissors",
        "comment": "Beat the computer\nin best of rounds!",
        "python": GAMES_DIR / "RockPaperScissors" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "RockPaperScissors" / "rock_paper_scissors.py",
        "cwd": GAMES_DIR / "RockPaperScissors",
        "color": (190, 110, 70),
        "hover": (170, 92, 55),
        "image": GAMES_DIR / "RockPaperScissors" / "assets" / "rockpaperscissors_icon.png",
    },
    {
        "name": "Air Hockey",
        "comment": "Score goals against\nthe AI paddle!",
        "python": GAMES_DIR / "AirHockey" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "AirHockey" / "air_hockey.py",
        "cwd": GAMES_DIR / "AirHockey",
        "color": (40, 90, 130),
        "hover": (30, 74, 110),
        "image": GAMES_DIR / "AirHockey" / "assets" / "airhockey_icon.png",
    },
    {
        "name": "Word Scramble",
        "comment": "Unscramble the\nletters to spell it!",
        "python": GAMES_DIR / "WordScramble" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "WordScramble" / "word_scramble.py",
        "cwd": GAMES_DIR / "WordScramble",
        "color": (100, 105, 130),
        "hover": (82, 87, 112),
        "image": GAMES_DIR / "WordScramble" / "assets" / "wordscramble_icon.png",
    },
    {
        "name": "Color Switch",
        "comment": "Stack the blocks,\ndon't miss the edge!",
        "python": GAMES_DIR / "ColorSwitch" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "ColorSwitch" / "color_switch.py",
        "cwd": GAMES_DIR / "ColorSwitch",
        "color": (170, 90, 130),
        "hover": (150, 74, 112),
        "image": GAMES_DIR / "ColorSwitch" / "assets" / "colorswitch_icon.png",
    },
    {
        "name": "Pong",
        "comment": "Classic paddle battle\nagainst the AI!",
        "python": GAMES_DIR / "Pong" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Pong" / "pong.py",
        "cwd": GAMES_DIR / "Pong",
        "color": (232, 232, 233),
        "hover": (210, 210, 212),
        "image": GAMES_DIR / "Pong" / "assets" / "pong_icon.png",
    },
    {
        "name": "Space Invaders",
        "comment": "Blast the alien fleet\nbefore they land!",
        "python": GAMES_DIR / "SpaceInvaders" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "SpaceInvaders" / "space_invaders.py",
        "cwd": GAMES_DIR / "SpaceInvaders",
        "color": (235, 235, 80),
        "hover": (215, 215, 60),
        "image": GAMES_DIR / "SpaceInvaders" / "assets" / "spaceinvaders_icon.png",
    },
    {
        "name": "Asteroids",
        "comment": "Rotate, thrust, and\nblast the rocks!",
        "python": GAMES_DIR / "Asteroids" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Asteroids" / "asteroids.py",
        "cwd": GAMES_DIR / "Asteroids",
        "color": (117, 233, 37),
        "hover": (97, 213, 20),
        "image": GAMES_DIR / "Asteroids" / "assets" / "asteroids_icon.png",
    },
    {
        "name": "Tetris",
        "comment": "Stack the falling\nblocks and clear lines!",
        "python": GAMES_DIR / "Tetris" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Tetris" / "tetris.py",
        "cwd": GAMES_DIR / "Tetris",
        "color": (227, 115, 235),
        "hover": (207, 95, 215),
        "image": GAMES_DIR / "Tetris" / "assets" / "tetris_icon.png",
    },
    {
        "name": "Connect Four",
        "comment": "Drop discs and get\n4 in a row to win!",
        "python": GAMES_DIR / "ConnectFour" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "ConnectFour" / "connect_four.py",
        "cwd": GAMES_DIR / "ConnectFour",
        "color": (143, 233, 159),
        "hover": (123, 213, 139),
        "image": GAMES_DIR / "ConnectFour" / "assets" / "connectfour_icon.png",
    },
    {
        "name": "Minesweeper",
        "comment": "Clear the board without\nhitting a mine!",
        "python": GAMES_DIR / "Minesweeper" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Minesweeper" / "minesweeper.py",
        "cwd": GAMES_DIR / "Minesweeper",
        "color": (43, 36, 234),
        "hover": (34, 28, 210),
        "image": GAMES_DIR / "Minesweeper" / "assets" / "minesweeper_icon.png",
    },
    {
        "name": "Pinball",
        "comment": "Flip the flippers,\nrack up the score!",
        "python": GAMES_DIR / "Pinball" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Pinball" / "pinball.py",
        "cwd": GAMES_DIR / "Pinball",
        "color": (37, 235, 133),
        "hover": (28, 213, 115),
        "image": GAMES_DIR / "Pinball" / "assets" / "pinball_icon.png",
    },
    {
        "name": "Typing Speed Test",
        "comment": "How fast can you\ntype the phrase?",
        "python": GAMES_DIR / "TypingTest" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "TypingTest" / "typing_test.py",
        "cwd": GAMES_DIR / "TypingTest",
        "color": (40, 234, 233),
        "hover": (30, 213, 212),
        "image": GAMES_DIR / "TypingTest" / "assets" / "typingtest_icon.png",
    },
    {
        "name": "Archery",
        "comment": "Aim, charge power,\nand hit the bullseye!",
        "python": GAMES_DIR / "Archery" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Archery" / "archery.py",
        "cwd": GAMES_DIR / "Archery",
        "color": (224, 171, 154),
        "hover": (204, 151, 134),
        "image": GAMES_DIR / "Archery" / "assets" / "archery_icon.png",
    },
    {
        "name": "Trivia",
        "comment": "Answer questions and\ntest your knowledge!",
        "python": GAMES_DIR / "Trivia" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Trivia" / "trivia.py",
        "cwd": GAMES_DIR / "Trivia",
        "color": (137, 36, 40),
        "hover": (117, 28, 32),
        "image": GAMES_DIR / "Trivia" / "assets" / "trivia_icon.png",
    },
]


class Card:
    def __init__(self, game, rect):
        self.game = game
        self.rect = pygame.Rect(rect)

    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)


def layout_cards():
    top_y = 150
    cards = []
    for i, game in enumerate(GAMES):
        row, col = divmod(i, COLS)
        row_start = row * COLS
        row_count = min(COLS, len(GAMES) - row_start)
        row_w = row_count * CARD_W + max(0, row_count - 1) * CARD_GAP
        row_start_x = (WIDTH - row_w) // 2

        x = row_start_x + col * (CARD_W + CARD_GAP)
        y = top_y + row * (CARD_H + CARD_GAP)
        cards.append(Card(game, (x, y, CARD_W, CARD_H)))
    return cards


def launch_game(game):
    subprocess.run(
        [str(game["python"]), str(game["script"])],
        cwd=str(game["cwd"]),
    )


def load_images():
    for game in GAMES:
        raw = pygame.image.load(str(game["image"])).convert_alpha()
        w, h = raw.get_size()
        scale = IMAGE_SIZE / max(w, h)
        game["image_surface"] = pygame.transform.smoothscale(
            raw, (int(w * scale), int(h * scale))
        )


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Arcade")
    clock = pygame.time.Clock()
    load_images()

    title_font = pygame.font.SysFont(None, 64, bold=True)
    subtitle_font = pygame.font.SysFont(None, 26)
    name_font = pygame.font.SysFont(None, 30, bold=True)
    comment_font = pygame.font.SysFont(None, 20)

    cards = layout_cards()
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for card in cards:
                    if card.is_hovered(event.pos):
                        pygame.display.quit()
                        pygame.mixer.quit()
                        launch_game(card.game)
                        pygame.mixer.init()
                        screen = pygame.display.set_mode((WIDTH, HEIGHT))
                        pygame.display.set_caption("Arcade")
                        load_images()
                        break

        screen.fill(BG_COLOR)

        title_surf = title_font.render("Arcade", True, TITLE_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        subtitle_surf = subtitle_font.render(
            "Pick a game to play!", True, SUBTITLE_COLOR
        )
        screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        for card in cards:
            hovered = card.is_hovered(mouse_pos)
            color = card.game["hover"] if hovered else card.game["color"]
            rect = card.rect.inflate(6, 6) if hovered else card.rect
            pygame.draw.rect(screen, color, rect, border_radius=14)
            pygame.draw.rect(screen, (60, 64, 84), rect, width=2, border_radius=14)

            image = card.game["image_surface"]
            img_top = rect.top + 16
            screen.blit(image, image.get_rect(midtop=(rect.centerx, img_top)))

            name_top = img_top + IMAGE_SIZE + 10
            name_surf = name_font.render(card.game["name"], True, TEXT_COLOR)
            screen.blit(
                name_surf, name_surf.get_rect(midtop=(rect.centerx, name_top))
            )

            comment_top = name_top + 32
            lines = card.game["comment"].split("\n")
            for i, line in enumerate(lines):
                line_surf = comment_font.render(line, True, (200, 204, 220))
                screen.blit(
                    line_surf,
                    line_surf.get_rect(
                        midtop=(rect.centerx, comment_top + i * 20)
                    ),
                )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
