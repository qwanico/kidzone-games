import asyncio
import importlib
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent
ICONS_DIR = BASE_DIR / "tile_icons"

WIDTH, HEIGHT = 1000, 700
CARD_W, CARD_H = 280, 260
CARD_GAP = 40
COLS = 3
IMAGE_SIZE = 110

BG_COLOR = (245, 245, 250)
TITLE_COLOR = (60, 60, 90)
SUBTITLE_COLOR = (110, 110, 130)

GAMES = [
    {
        "key": "feelings",
        "name": "Feelings",
        "comment": "Pick the word that\nmatches the face!",
        "module": "games.feelings",
        "entry": "class",
        "color": (100, 175, 130),
        "hover": (80, 155, 110),
        "image": ICONS_DIR / "feelings.png",
    },
    {
        "key": "fruit_finder",
        "name": "Find The Food",
        "comment": "Find the fruit or\nveggie that's named!",
        "module": "games.fruit_finder",
        "entry": "function",
        "color": (255, 190, 90),
        "hover": (235, 170, 70),
        "image": BASE_DIR / "games" / "fruit_finder_assets" / "assets" / "app_icon.png",
    },
    {
        "key": "letters",
        "name": "Letters",
        "comment": "Listen, then click\nthe letter you hear!",
        "module": "games.letters",
        "entry": "class",
        "color": (220, 110, 150),
        "hover": (200, 90, 130),
        "image": ICONS_DIR / "letters.png",
    },
    {
        "key": "sight_words",
        "name": "Sight Words",
        "comment": "Listen, then click\nthe word you hear!",
        "module": "games.sight_words",
        "entry": "class",
        "color": (90, 160, 230),
        "hover": (70, 140, 210),
        "image": ICONS_DIR / "sight_words.png",
    },
    {
        "key": "picture_words",
        "name": "Which Word",
        "comment": "Pick the word that\nmatches the picture!",
        "module": "games.picture_words",
        "entry": "class",
        "color": (230, 170, 60),
        "hover": (210, 150, 40),
        "image": BASE_DIR / "games" / "picture_words_assets" / "assets" / "apple.png",
    },
    {
        "key": "planets",
        "name": "Planets",
        "comment": "Put the planets\nin order from the Sun!",
        "module": "games.planets",
        "entry": "class",
        "color": (90, 100, 200),
        "hover": (70, 80, 180),
        "image": ICONS_DIR / "planets.png",
    },
]


class Card:
    def __init__(self, game, rect):
        self.game = game
        self.rect = pygame.Rect(rect)

    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)


def layout_cards():
    total_w = COLS * CARD_W + (COLS - 1) * CARD_GAP
    start_x = (WIDTH - total_w) // 2
    row2_count = len(GAMES) - COLS
    row2_w = row2_count * CARD_W + max(0, row2_count - 1) * CARD_GAP
    row2_start_x = (WIDTH - row2_w) // 2

    top_y = 150
    cards = []
    for i, game in enumerate(GAMES):
        if i < COLS:
            x = start_x + i * (CARD_W + CARD_GAP)
            y = top_y
        else:
            j = i - COLS
            x = row2_start_x + j * (CARD_W + CARD_GAP)
            y = top_y + CARD_H + CARD_GAP
        cards.append(Card(game, (x, y, CARD_W, CARD_H)))
    return cards


def load_images():
    for game in GAMES:
        raw = pygame.image.load(str(game["image"])).convert_alpha()
        w, h = raw.get_size()
        scale = IMAGE_SIZE / max(w, h)
        game["image_surface"] = pygame.transform.smoothscale(
            raw, (int(w * scale), int(h * scale))
        )


async def launch_game(game):
    module = importlib.import_module(game["module"])
    if game["entry"] == "class":
        await module.Game().run()
    else:
        await module.run()


async def main():
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
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for card in cards:
                    if card.is_hovered(event.pos):
                        await launch_game(card.game)
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
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
