import subprocess
import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent
GAMES_DIR = BASE_DIR.parent
ICONS_DIR = BASE_DIR / "tile_icons"

WIDTH, HEIGHT = 1100, 960
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
