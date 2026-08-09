import asyncio
import importlib
import math
from pathlib import Path

import pygame

try:
    import platform
except ImportError:
    platform = None

BASE_DIR = Path(__file__).parent
ICONS_DIR = BASE_DIR / "tile_icons"

WIDTH, HEIGHT = 1100, 800
CARD_W, CARD_H = 250, 230
CARD_GAP = 36
COLS = 4
IMAGE_SIZE = 96
BOTTOM_MARGIN = 40
SCROLL_SPEED = 60
SCROLLBAR_COLOR = (50, 54, 70)
SCROLLBAR_THUMB_COLOR = (100, 106, 130)

BG_COLOR = (24, 26, 38)
TEXT_COLOR = (225, 228, 240)
TITLE_COLOR = (120, 220, 255)
SUBTITLE_COLOR = (150, 155, 180)

NAV_BUTTON_COLOR = (44, 48, 68)
NAV_BUTTON_HOVER = (58, 63, 88)
NAV_BUTTON_BORDER = (120, 220, 255)

# Fixed header (title/tabs) stays put; only the card grid below it scrolls,
# so switching categories always lands on a stable, un-scrolled page.
GRID_TOP = 205
TAB_BAR_TOP = 128
TAB_HEIGHT = 44
TAB_PAD_X = 26
TAB_GAP = 14

GAMES = [
    {"key": "snake", "name": "Snake", "category": "Arcade", "comment": "Eat food, grow long,\ndon't hit yourself!",
     "module": "games.snake", "entry": "function", "color": (60, 140, 95), "hover": (48, 120, 78)},
    {"key": "breakout", "name": "Breakout", "category": "Arcade", "comment": "Bounce the ball,\nbreak every brick!",
     "module": "games.breakout", "entry": "function", "color": (90, 100, 160), "hover": (72, 82, 140)},
    {"key": "flappy_bird", "name": "Flappy Bird", "category": "Arcade", "comment": "Flap through the\npipes without hitting!",
     "module": "games.flappy_bird", "entry": "function", "color": (70, 150, 190), "hover": (55, 130, 170)},
    {"key": "game_2048", "name": "2048", "category": "Puzzles", "comment": "Slide and merge tiles\nto reach 2048!",
     "module": "games.game_2048", "entry": "function", "color": (150, 120, 90), "hover": (130, 102, 74)},
    {"key": "tic_tac_toe", "name": "Tic-Tac-Toe", "category": "Puzzles", "comment": "Outsmart the AI\nin classic X's and O's!",
     "module": "games.tic_tac_toe", "entry": "function", "color": (70, 76, 100), "hover": (56, 62, 84)},
    {"key": "reaction_timer", "name": "Reaction Timer", "category": "Skill", "comment": "How fast are your\nreflexes? Test them!",
     "module": "games.reaction_timer", "entry": "function", "color": (150, 70, 160), "hover": (130, 56, 140)},
    {"key": "rock_paper_scissors", "name": "Rock Paper Scissors", "category": "Arcade", "comment": "Beat the computer\nin best of rounds!",
     "module": "games.rock_paper_scissors", "entry": "function", "color": (190, 110, 70), "hover": (170, 92, 55)},
    {"key": "air_hockey", "name": "Air Hockey", "category": "Skill", "comment": "Score goals against\nthe AI paddle!",
     "module": "games.air_hockey", "entry": "function", "color": (40, 90, 130), "hover": (30, 74, 110)},
    {"key": "word_scramble", "name": "Word Scramble", "category": "Puzzles", "comment": "Unscramble the\nletters to spell it!",
     "module": "games.word_scramble", "entry": "function", "color": (80, 150, 140), "hover": (64, 130, 120)},
    {"key": "color_switch", "name": "Color Switch", "category": "Arcade", "comment": "Stack the blocks,\ndon't miss the edge!",
     "module": "games.color_switch", "entry": "function", "color": (170, 90, 130), "hover": (150, 74, 112)},
    {"key": "pong", "name": "Pong", "category": "Arcade", "comment": "Classic paddle battle\nagainst the AI!",
     "module": "games.pong", "entry": "function", "color": (232, 232, 233), "hover": (210, 210, 212)},
    {"key": "space_invaders", "name": "Space Invaders", "category": "Arcade", "comment": "Blast the alien fleet\nbefore they land!",
     "module": "games.space_invaders", "entry": "function", "color": (235, 235, 80), "hover": (215, 215, 60)},
    {"key": "asteroids", "name": "Asteroids", "category": "Arcade", "comment": "Rotate, thrust, and\nblast the rocks!",
     "module": "games.asteroids", "entry": "function", "color": (117, 233, 37), "hover": (97, 213, 20)},
    {"key": "tetris", "name": "Tetris", "category": "Arcade", "comment": "Stack the falling\nblocks and clear lines!",
     "module": "games.tetris", "entry": "function", "color": (227, 115, 235), "hover": (207, 95, 215)},
    {"key": "connect_four", "name": "Connect Four", "category": "Puzzles", "comment": "Drop discs and get\n4 in a row to win!",
     "module": "games.connect_four", "entry": "function", "color": (143, 233, 159), "hover": (123, 213, 139)},
    {"key": "minesweeper", "name": "Minesweeper", "category": "Puzzles", "comment": "Clear the board without\nhitting a mine!",
     "module": "games.minesweeper", "entry": "function", "color": (43, 36, 234), "hover": (34, 28, 210)},
    {"key": "pinball", "name": "Pinball", "category": "Arcade", "comment": "Flip the flippers,\nrack up the score!",
     "module": "games.pinball", "entry": "function", "color": (37, 235, 133), "hover": (28, 213, 115)},
    {"key": "typing_test", "name": "Typing Speed Test", "category": "Trivia", "comment": "How fast can you\ntype the phrase?",
     "module": "games.typing_test", "entry": "function", "color": (40, 234, 233), "hover": (30, 213, 212)},
    {"key": "archery", "name": "Archery", "category": "Skill", "comment": "Aim, charge power,\nand hit the bullseye!",
     "module": "games.archery", "entry": "function", "color": (224, 171, 154), "hover": (204, 151, 134)},
    {"key": "trivia", "name": "Trivia", "category": "Trivia", "comment": "Answer questions and\ntest your knowledge!",
     "module": "games.trivia", "entry": "function", "color": (137, 36, 40), "hover": (117, 28, 32)},
]

for game in GAMES:
    game["image"] = BASE_DIR / "games" / f"{game['key']}_assets" / "assets" / f"{game['key']}_icon.png"


class Card:
    def __init__(self, game, rect):
        self.game = game
        self.rect = pygame.Rect(rect)

    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)


CATEGORY_ORDER = ["Arcade", "Puzzles", "Skill", "Trivia"]
CATEGORY_COLORS = {
    "Arcade": (255, 200, 80),
    "Puzzles": (180, 140, 255),
    "Skill": (120, 230, 150),
    "Trivia": (255, 130, 130),
}


def layout_cards(active_category):
    """Lay out just the given category's games in a grid, using local
    coordinates starting at y=0 (the caller positions the resulting grid
    surface below the fixed header/tab bar and handles scrolling)."""
    games_in_category = [g for g in GAMES if g["category"] == active_category]
    cards = []
    for i, game in enumerate(games_in_category):
        row, col = divmod(i, COLS)
        row_start = row * COLS
        row_count = min(COLS, len(games_in_category) - row_start)
        row_w = row_count * CARD_W + max(0, row_count - 1) * CARD_GAP
        row_start_x = (WIDTH - row_w) // 2

        x = row_start_x + col * (CARD_W + CARD_GAP)
        y = row * (CARD_H + CARD_GAP)
        cards.append(Card(game, (x, y, CARD_W, CARD_H)))

    return cards


def category_tab_rects(font):
    widths = [font.size(cat)[0] + TAB_PAD_X * 2 for cat in CATEGORY_ORDER]
    total_w = sum(widths) + TAB_GAP * (len(widths) - 1)
    start_x = (WIDTH - total_w) // 2
    rects = []
    x = start_x
    for w in widths:
        rects.append(pygame.Rect(x, TAB_BAR_TOP, w, TAB_HEIGHT))
        x += w + TAB_GAP
    return rects


def draw_category_tabs(surface, active_category, mouse_pos, font):
    rects = category_tab_rects(font)
    for cat, rect in zip(CATEGORY_ORDER, rects):
        color = CATEGORY_COLORS[cat]
        is_active = cat == active_category
        hovered = rect.collidepoint(mouse_pos)
        if is_active:
            pygame.draw.rect(surface, color, rect, border_radius=rect.height // 2)
            text_color = BG_COLOR
        else:
            fill = SCROLLBAR_THUMB_COLOR if hovered else SCROLLBAR_COLOR
            pygame.draw.rect(surface, fill, rect, border_radius=rect.height // 2)
            pygame.draw.rect(surface, color, rect, width=2, border_radius=rect.height // 2)
            text_color = color
        text_surf = font.render(cat, True, text_color)
        surface.blit(text_surf, text_surf.get_rect(center=rect.center))
    return rects


def content_height(cards):
    if not cards:
        return 0
    return max(card.rect.bottom for card in cards) + BOTTOM_MARGIN


async def launch_game(game):
    module = importlib.import_module(game["module"])
    if game["entry"] == "class":
        await module.Game().run()
    else:
        await module.run()


def load_images():
    for game in GAMES:
        raw = pygame.image.load(str(game["image"])).convert_alpha()
        w, h = raw.get_size()
        scale = IMAGE_SIZE / max(w, h)
        game["image_surface"] = pygame.transform.smoothscale(
            raw, (int(w * scale), int(h * scale))
        )


def go_to_kidzone():
    if platform is not None and hasattr(platform, "window"):
        try:
            platform.window.location.href = "/"
            return
        except Exception:
            pass
    print("(would navigate to / — Kid Zone)")


async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("Arcade")
    clock = pygame.time.Clock()
    load_images()

    title_font = pygame.font.SysFont(None, 64, bold=True)
    subtitle_font = pygame.font.SysFont(None, 26)
    name_font = pygame.font.SysFont(None, 30, bold=True)
    comment_font = pygame.font.SysFont(None, 20)
    nav_font = pygame.font.SysFont(None, 22, bold=True)
    tab_font = pygame.font.SysFont(None, 26, bold=True)

    active_category = CATEGORY_ORDER[0]
    cards = layout_cards(active_category)
    max_scroll = max(0, content_height(cards) - (HEIGHT - GRID_TOP))
    scroll = 0
    running = True

    nav_button = pygame.Rect(24, 20, 190, 42)

    while running:
        mouse_pos = pygame.mouse.get_pos()
        # Grid-local mouse position for card hit-testing - the header/tab bar
        # are fixed on screen now, only the grid below GRID_TOP scrolls.
        mouse_grid_pos = (mouse_pos[0], mouse_pos[1] - GRID_TOP + scroll)
        tab_rects = category_tab_rects(tab_font)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
                scroll = min(scroll + SCROLL_SPEED, max_scroll)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
                scroll = max(scroll - SCROLL_SPEED, 0)
            elif event.type == pygame.MOUSEWHEEL:
                scroll = max(0, min(scroll - event.y * SCROLL_SPEED, max_scroll))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if nav_button.collidepoint(mouse_pos):
                    go_to_kidzone()
                    continue
                clicked_tab = False
                for cat, rect in zip(CATEGORY_ORDER, tab_rects):
                    if rect.collidepoint(mouse_pos):
                        clicked_tab = True
                        if cat != active_category:
                            active_category = cat
                            cards = layout_cards(active_category)
                            max_scroll = max(
                                0, content_height(cards) - (HEIGHT - GRID_TOP)
                            )
                            scroll = 0
                        break

                if not clicked_tab and mouse_pos[1] >= GRID_TOP:
                    for card in cards:
                        if card.is_hovered(mouse_grid_pos):
                            await launch_game(card.game)
                            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
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

        draw_category_tabs(screen, active_category, mouse_pos, tab_font)

        # ---- Scrollable card grid, clipped so it never draws over the header ----
        grid_h = max(content_height(cards), HEIGHT - GRID_TOP)
        grid_surface = pygame.Surface((WIDTH, grid_h))
        grid_surface.fill(BG_COLOR)

        for card in cards:
            hovered = mouse_pos[1] >= GRID_TOP and card.is_hovered(mouse_grid_pos)
            color = card.game["hover"] if hovered else card.game["color"]
            rect = card.rect.inflate(6, 6) if hovered else card.rect
            pygame.draw.rect(grid_surface, color, rect, border_radius=14)
            pygame.draw.rect(grid_surface, (60, 64, 84), rect, width=2, border_radius=14)

            image = card.game["image_surface"]
            img_top = rect.top + 16
            grid_surface.blit(image, image.get_rect(midtop=(rect.centerx, img_top)))

            name_top = img_top + IMAGE_SIZE + 10
            name_surf = name_font.render(card.game["name"], True, TEXT_COLOR)
            grid_surface.blit(
                name_surf, name_surf.get_rect(midtop=(rect.centerx, name_top))
            )

            comment_top = name_top + 32
            lines = card.game["comment"].split("\n")
            for i, line in enumerate(lines):
                line_surf = comment_font.render(line, True, (200, 204, 220))
                grid_surface.blit(
                    line_surf,
                    line_surf.get_rect(
                        midtop=(rect.centerx, comment_top + i * 20)
                    ),
                )

        prev_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(0, GRID_TOP, WIDTH, HEIGHT - GRID_TOP))
        screen.blit(grid_surface, (0, GRID_TOP - scroll))
        screen.set_clip(prev_clip)

        nav_hovered = nav_button.collidepoint(mouse_pos)
        pygame.draw.rect(screen, NAV_BUTTON_HOVER if nav_hovered else NAV_BUTTON_COLOR, nav_button, border_radius=12)
        pygame.draw.rect(screen, NAV_BUTTON_BORDER, nav_button, width=2, border_radius=12)
        nav_text = nav_font.render("Kid Zone", True, NAV_BUTTON_BORDER)
        screen.blit(nav_text, nav_text.get_rect(center=nav_button.center))

        if max_scroll > 0:
            track_x = WIDTH - 14
            track_h = HEIGHT - GRID_TOP
            pygame.draw.rect(
                screen, SCROLLBAR_COLOR, (track_x, GRID_TOP, 8, track_h), border_radius=4
            )
            thumb_h = max(30, track_h * track_h // grid_h)
            thumb_y = GRID_TOP + (
                int(scroll / max_scroll * (track_h - thumb_h)) if max_scroll else 0
            )
            pygame.draw.rect(
                screen, SCROLLBAR_THUMB_COLOR, (track_x, thumb_y, 8, thumb_h), border_radius=4
            )

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
