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
TOP_Y = 150
BOTTOM_MARGIN = 40
SCROLL_SPEED = 60
SCROLLBAR_COLOR = (210, 210, 220)
SCROLLBAR_THUMB_COLOR = (160, 160, 180)

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
    {
        "key": "shapes",
        "name": "Shapes",
        "comment": "Listen, then click\nthe shape you hear!",
        "module": "games.shapes",
        "entry": "class",
        "color": (20, 150, 140),
        "hover": (15, 130, 120),
        "image": ICONS_DIR / "shapes.png",
    },
    {
        "key": "counting",
        "name": "Counting",
        "comment": "Listen, then click\nthe number you hear!",
        "module": "games.counting",
        "entry": "class",
        "color": (150, 80, 190),
        "hover": (130, 60, 170),
        "image": ICONS_DIR / "counting.png",
    },
    {
        "key": "colors",
        "name": "Colors",
        "comment": "Listen, then click\nthe color you hear!",
        "module": "games.colors",
        "entry": "class",
        "color": (215, 70, 70),
        "hover": (195, 55, 55),
        "image": ICONS_DIR / "colors.png",
    },
    {
        "key": "math",
        "name": "Math",
        "comment": "Listen, then click\nthe answer you hear!",
        "module": "games.math_game",
        "entry": "class",
        "color": (120, 180, 40),
        "hover": (100, 160, 30),
        "image": ICONS_DIR / "math.png",
    },
    {
        "key": "whack_a_mole",
        "name": "Whack-a-Mole",
        "comment": "Click the moles\nbefore they hide!",
        "module": "games.whack_a_mole",
        "entry": "function",
        "color": (140, 100, 70),
        "hover": (120, 82, 55),
        "image": BASE_DIR / "games" / "whack_a_mole_assets" / "assets" / "whackamole_icon.png",
    },
    {
        "key": "balloon_pop",
        "name": "Balloon Pop",
        "comment": "Pop balloons, dodge\nthe bombs!",
        "module": "games.balloon_pop",
        "entry": "function",
        "color": (70, 200, 220),
        "hover": (55, 175, 195),
        "image": BASE_DIR / "games" / "balloon_pop_assets" / "assets" / "balloonpop_icon.png",
    },
    {
        "key": "bug_squasher",
        "name": "Bug Squasher",
        "comment": "Click the bugs before\nthey scurry away!",
        "module": "games.bug_squasher",
        "entry": "function",
        "color": (110, 140, 80),
        "hover": (92, 122, 64),
        "image": BASE_DIR / "games" / "bug_squasher_assets" / "assets" / "bugsquasher_icon.png",
    },
    {
        "key": "fish_catch",
        "name": "Fish Catch",
        "comment": "Click the fish, avoid\nthe junk!",
        "module": "games.fish_catch",
        "entry": "function",
        "color": (40, 120, 190),
        "hover": (30, 100, 170),
        "image": BASE_DIR / "games" / "fish_catch_assets" / "assets" / "fishcatch_icon.png",
    },
    {
        "key": "star_catcher",
        "name": "Star Catcher",
        "comment": "Catch falling stars,\ndodge the rocks!",
        "module": "games.star_catcher",
        "entry": "function",
        "color": (60, 55, 110),
        "hover": (45, 42, 90),
        "image": BASE_DIR / "games" / "star_catcher_assets" / "assets" / "starcatcher_icon.png",
    },
    {
        "key": "memory_match",
        "name": "Memory Match",
        "comment": "Flip cards to find\nmatching pairs!",
        "module": "games.memory_match",
        "entry": "function",
        "color": (200, 90, 150),
        "hover": (180, 72, 132),
        "image": BASE_DIR / "games" / "memory_match_assets" / "assets" / "memorymatch_icon.png",
    },
    {
        "key": "jumping_jack",
        "name": "Jumping Jack",
        "comment": "Jump over obstacles\nto keep the score up!",
        "module": "games.jumping_jack",
        "entry": "function",
        "color": (221, 235, 100),
        "hover": (200, 215, 85),
        "image": BASE_DIR / "games" / "jumping_jack_assets" / "assets" / "jumpingjack_icon.png",
    },
    {
        "key": "maze",
        "name": "Maze",
        "comment": "Guide the hero\nthrough the maze!",
        "module": "games.maze",
        "entry": "class",
        "color": (110, 120, 135),
        "hover": (90, 100, 115),
        "image": ICONS_DIR / "maze.png",
    },
    {
        "key": "simon_pattern",
        "name": "Simon Pattern",
        "comment": "Watch the pattern,\nthen click it back!",
        "module": "games.simon_pattern",
        "entry": "class",
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
    cards = []
    for i, game in enumerate(GAMES):
        row, col = divmod(i, COLS)
        row_start = row * COLS
        row_count = min(COLS, len(GAMES) - row_start)
        row_w = row_count * CARD_W + max(0, row_count - 1) * CARD_GAP
        row_start_x = (WIDTH - row_w) // 2

        x = row_start_x + col * (CARD_W + CARD_GAP)
        y = TOP_Y + row * (CARD_H + CARD_GAP)
        cards.append(Card(game, (x, y, CARD_W, CARD_H)))
    return cards


def content_height(cards):
    if not cards:
        return TOP_Y
    return max(card.rect.bottom for card in cards) + BOTTOM_MARGIN


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
    max_scroll = max(0, content_height(cards) - HEIGHT)
    scroll = 0
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_content_pos = (mouse_pos[0], mouse_pos[1] + scroll)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
                scroll = min(scroll + SCROLL_SPEED, max_scroll)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
                scroll = max(scroll - SCROLL_SPEED, 0)
            elif event.type == pygame.MOUSEWHEEL:
                scroll = max(0, min(scroll - event.y * SCROLL_SPEED, max_scroll))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for card in cards:
                    if card.is_hovered(mouse_content_pos):
                        await launch_game(card.game)
                        screen = pygame.display.set_mode((WIDTH, HEIGHT))
                        pygame.display.set_caption("Kid Zone")
                        load_images()
                        break

        content = pygame.Surface((WIDTH, content_height(cards)))
        content.fill(BG_COLOR)

        title_surf = title_font.render("Kid Zone", True, TITLE_COLOR)
        content.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        subtitle_surf = subtitle_font.render(
            "Pick a game to play!", True, SUBTITLE_COLOR
        )
        content.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        for card in cards:
            hovered = card.is_hovered(mouse_content_pos)
            color = card.game["hover"] if hovered else card.game["color"]
            rect = card.rect.inflate(6, 6) if hovered else card.rect
            pygame.draw.rect(content, color, rect, border_radius=18)
            pygame.draw.rect(content, (255, 255, 255), rect, width=3, border_radius=18)

            image = card.game["image_surface"]
            img_top = rect.top + 18
            content.blit(image, image.get_rect(midtop=(rect.centerx, img_top)))

            name_top = img_top + IMAGE_SIZE + 12
            name_surf = name_font.render(card.game["name"], True, (255, 255, 255))
            content.blit(
                name_surf, name_surf.get_rect(midtop=(rect.centerx, name_top))
            )

            comment_top = name_top + 36
            lines = card.game["comment"].split("\n")
            for i, line in enumerate(lines):
                line_surf = comment_font.render(line, True, (255, 255, 255))
                content.blit(
                    line_surf,
                    line_surf.get_rect(
                        midtop=(rect.centerx, comment_top + i * 22)
                    ),
                )

        screen.fill(BG_COLOR)
        screen.blit(content, (0, -scroll))

        if max_scroll > 0:
            track_x = WIDTH - 14
            pygame.draw.rect(screen, SCROLLBAR_COLOR, (track_x, 0, 8, HEIGHT), border_radius=4)
            thumb_h = max(30, HEIGHT * HEIGHT // content_height(cards))
            thumb_y = int(scroll / max_scroll * (HEIGHT - thumb_h)) if max_scroll else 0
            pygame.draw.rect(
                screen, SCROLLBAR_THUMB_COLOR, (track_x, thumb_y, 8, thumb_h), border_radius=4
            )

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
