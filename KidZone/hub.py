import subprocess
import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent
GAMES_DIR = BASE_DIR.parent
ICONS_DIR = BASE_DIR / "tile_icons"

WIDTH, HEIGHT = 1000, 1650
CARD_W, CARD_H = 280, 260
CARD_GAP = 40
COLS = 3
IMAGE_SIZE = 110

BG_COLOR = (245, 245, 250)
TEXT_COLOR = (50, 50, 60)
TITLE_COLOR = (60, 60, 90)
SUBTITLE_COLOR = (110, 110, 130)

GAMES = [
    {
        "name": "Feelings",
        "comment": "Pick the word that\nmatches the face!",
        "python": GAMES_DIR / "Feelings" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Feelings" / "feelings.py",
        "cwd": GAMES_DIR / "Feelings",
        "color": (100, 175, 130),
        "hover": (80, 155, 110),
        "image": ICONS_DIR / "feelings.png",
    },
    {
        "name": "Find The Food",
        "comment": "Find the fruit or\nveggie that's named!",
        "python": GAMES_DIR / "FruitFinder" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "FruitFinder" / "fruit_finder.py",
        "cwd": GAMES_DIR / "FruitFinder",
        "color": (255, 190, 90),
        "hover": (235, 170, 70),
        "image": GAMES_DIR / "FruitFinder" / "assets" / "app_icon.png",
    },
    {
        "name": "Letters",
        "comment": "Listen, then click\nthe letter you hear!",
        "python": GAMES_DIR / "Letters" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Letters" / "letters.py",
        "cwd": GAMES_DIR / "Letters",
        "color": (220, 110, 150),
        "hover": (200, 90, 130),
        "image": ICONS_DIR / "letters.png",
    },
    {
        "name": "Sight Words",
        "comment": "Listen, then click\nthe word you hear!",
        "python": GAMES_DIR / "SightWords" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "SightWords" / "sight_words.py",
        "cwd": GAMES_DIR / "SightWords",
        "color": (90, 160, 230),
        "hover": (70, 140, 210),
        "image": ICONS_DIR / "sight_words.png",
    },
    {
        "name": "Which Word",
        "comment": "Pick the word that\nmatches the picture!",
        "python": GAMES_DIR / "PictureWords" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "PictureWords" / "picture_words.py",
        "cwd": GAMES_DIR / "PictureWords",
        "color": (230, 170, 60),
        "hover": (210, 150, 40),
        "image": GAMES_DIR / "PictureWords" / "assets" / "apple.png",
    },
    {
        "name": "Planets",
        "comment": "Put the planets\nin order from the Sun!",
        "python": GAMES_DIR / "Planets" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Planets" / "planets.py",
        "cwd": GAMES_DIR / "Planets",
        "color": (90, 100, 200),
        "hover": (70, 80, 180),
        "image": ICONS_DIR / "planets.png",
    },
    {
        "name": "Shapes",
        "comment": "Listen, then click\nthe shape you hear!",
        "python": GAMES_DIR / "Shapes" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Shapes" / "shapes.py",
        "cwd": GAMES_DIR / "Shapes",
        "color": (20, 150, 140),
        "hover": (15, 130, 120),
        "image": ICONS_DIR / "shapes.png",
    },
    {
        "name": "Counting",
        "comment": "Listen, then click\nthe number you hear!",
        "python": GAMES_DIR / "Counting" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Counting" / "counting.py",
        "cwd": GAMES_DIR / "Counting",
        "color": (150, 80, 190),
        "hover": (130, 60, 170),
        "image": ICONS_DIR / "counting.png",
    },
    {
        "name": "Colors",
        "comment": "Listen, then click\nthe color you hear!",
        "python": GAMES_DIR / "Colors" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Colors" / "colors.py",
        "cwd": GAMES_DIR / "Colors",
        "color": (215, 70, 70),
        "hover": (195, 55, 55),
        "image": ICONS_DIR / "colors.png",
    },
    {
        "name": "Math",
        "comment": "Listen, then click\nthe answer you hear!",
        "python": GAMES_DIR / "Math" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Math" / "math_game.py",
        "cwd": GAMES_DIR / "Math",
        "color": (120, 180, 40),
        "hover": (100, 160, 30),
        "image": ICONS_DIR / "math.png",
    },
    {
        "name": "Whack-a-Mole",
        "comment": "Click the moles\nbefore they hide!",
        "python": GAMES_DIR / "WhackAMole" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "WhackAMole" / "whack_a_mole.py",
        "cwd": GAMES_DIR / "WhackAMole",
        "color": (140, 100, 70),
        "hover": (120, 82, 55),
        "image": GAMES_DIR / "WhackAMole" / "assets" / "whackamole_icon.png",
    },
    {
        "name": "Balloon Pop",
        "comment": "Pop balloons, dodge\nthe bombs!",
        "python": GAMES_DIR / "BalloonPop" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "BalloonPop" / "balloon_pop.py",
        "cwd": GAMES_DIR / "BalloonPop",
        "color": (70, 200, 220),
        "hover": (55, 175, 195),
        "image": GAMES_DIR / "BalloonPop" / "assets" / "balloonpop_icon.png",
    },
    {
        "name": "Maze",
        "comment": "Guide the hero\nthrough the maze!",
        "python": GAMES_DIR / "Maze" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Maze" / "maze.py",
        "cwd": GAMES_DIR / "Maze",
        "color": (110, 120, 135),
        "hover": (90, 100, 115),
        "image": ICONS_DIR / "maze.png",
    },
    {
        "name": "Simon Pattern",
        "comment": "Watch the pattern,\nthen click it back!",
        "python": GAMES_DIR / "SimonPattern" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "SimonPattern" / "simon_pattern.py",
        "cwd": GAMES_DIR / "SimonPattern",
        "color": (180, 50, 130),
        "hover": (160, 35, 112),
        "image": ICONS_DIR / "simon_pattern.png",
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
    pygame.display.set_caption("Kid Zone")
    clock = pygame.time.Clock()
    load_images()

    title_font = pygame.font.SysFont(None, 64, bold=True)
    subtitle_font = pygame.font.SysFont(None, 28)
    name_font = pygame.font.SysFont(None, 34, bold=True)
    comment_font = pygame.font.SysFont(None, 22)

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
                        pygame.display.set_caption("Kid Zone")
                        load_images()
                        break

        screen.fill(BG_COLOR)

        title_surf = title_font.render("Kid Zone", True, TITLE_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        subtitle_surf = subtitle_font.render(
            "Pick a game to play!", True, SUBTITLE_COLOR
        )
        screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        for card in cards:
            hovered = card.is_hovered(mouse_pos)
            color = card.game["hover"] if hovered else card.game["color"]
            rect = card.rect.inflate(6, 6) if hovered else card.rect
            pygame.draw.rect(screen, color, rect, border_radius=18)
            pygame.draw.rect(screen, (255, 255, 255), rect, width=3, border_radius=18)

            image = card.game["image_surface"]
            img_top = rect.top + 18
            screen.blit(image, image.get_rect(midtop=(rect.centerx, img_top)))

            name_top = img_top + IMAGE_SIZE + 12
            name_surf = name_font.render(card.game["name"], True, (255, 255, 255))
            screen.blit(
                name_surf, name_surf.get_rect(midtop=(rect.centerx, name_top))
            )

            comment_top = name_top + 36
            lines = card.game["comment"].split("\n")
            for i, line in enumerate(lines):
                line_surf = comment_font.render(line, True, (255, 255, 255))
                screen.blit(
                    line_surf,
                    line_surf.get_rect(
                        midtop=(rect.centerx, comment_top + i * 22)
                    ),
                )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
