import math
import subprocess
import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent
GAMES_DIR = BASE_DIR.parent
ICONS_DIR = BASE_DIR / "tile_icons"
FONTS_DIR = BASE_DIR / "fonts"

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
TITLE_COLOR = (120, 220, 255)
SUBTITLE_COLOR = (150, 155, 180)

# Fixed header (title/tabs) stays put; only the card grid below it scrolls,
# so switching categories always lands on a stable, un-scrolled page.
GRID_TOP = 205
TAB_BAR_TOP = 128
TAB_HEIGHT = 44
TAB_PAD_X = 26
TAB_GAP = 14

CATEGORY_ORDER = ["Arcade", "Puzzles", "Skill", "Trivia"]
CATEGORY_COLORS = {
    "Arcade": (255, 200, 80),
    "Puzzles": (180, 140, 255),
    "Skill": (120, 230, 150),
    "Trivia": (255, 130, 130),
}

GAMES = [
    {
        "name": "Snake",
        "category": "Arcade",
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
        "category": "Arcade",
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
        "category": "Arcade",
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
        "category": "Puzzles",
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
        "category": "Puzzles",
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
        "category": "Skill",
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
        "category": "Arcade",
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
        "category": "Skill",
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
        "category": "Puzzles",
        "comment": "Unscramble the\nletters to spell it!",
        "python": GAMES_DIR / "WordScramble" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "WordScramble" / "word_scramble.py",
        "cwd": GAMES_DIR / "WordScramble",
        "color": (80, 150, 140),
        "hover": (64, 130, 120),
        "image": GAMES_DIR / "WordScramble" / "assets" / "wordscramble_icon.png",
    },
    {
        "name": "Color Switch",
        "category": "Arcade",
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
        "category": "Arcade",
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
        "category": "Arcade",
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
        "category": "Arcade",
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
        "category": "Arcade",
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
        "category": "Puzzles",
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
        "category": "Puzzles",
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
        "category": "Arcade",
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
        "category": "Trivia",
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
        "category": "Skill",
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
        "category": "Trivia",
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


def make_glow_background(width, height):
    """Dark arcade-cabinet backdrop: flat navy plus a couple of soft,
    low-alpha color blooms for a bit of atmosphere behind the header/grid."""
    bg = pygame.Surface((width, height))
    bg.fill(BG_COLOR)
    glow = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.circle(
        glow, (*TITLE_COLOR, 20), (int(width * 0.16), int(height * 0.08)), int(width * 0.26)
    )
    pygame.draw.circle(
        glow, (180, 120, 255, 16), (int(width * 0.86), int(height * 0.3)), int(width * 0.22)
    )
    bg.blit(glow, (0, 0))
    return bg


def draw_glow_shadow(surface, rect, color, radius, hovered):
    """Soft colored halo behind a card, like a backlit arcade button -
    brighter/wider when hovered."""
    layers = [(0, 20, 55), (0, 12, 75), (0, 6, 95)] if hovered else [(0, 12, 30), (0, 6, 45)]
    pad = 22
    for dx, dy, alpha in layers:
        shadow_surf = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (*color, alpha), (pad, pad, rect.width, rect.height), border_radius=radius)
        surface.blit(shadow_surf, (rect.x - pad + dx, rect.y - pad + dy))


def draw_card_gloss(surface, rect, radius):
    """A faint glass-like sheen across the top of a card."""
    gloss_h = max(radius, int(rect.height * 0.45))
    gloss_surf = pygame.Surface((rect.width, gloss_h), pygame.SRCALPHA)
    pygame.draw.rect(
        gloss_surf, (255, 255, 255, 24), gloss_surf.get_rect(),
        border_top_left_radius=radius, border_top_right_radius=radius,
    )
    surface.blit(gloss_surf, rect.topleft)


def readable_text_color(bg_color):
    """Pick near-black or near-white text depending on a card's own
    background brightness, so light cards (Pong, Archery) stay legible
    instead of using the same light-on-light text as dark cards."""
    r, g, b = bg_color[:3]
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    if luminance > 150:
        return (30, 32, 44), (70, 74, 92)
    return (255, 255, 255), (200, 204, 220)


def draw_title_glow(surface, rect, color):
    for pad, alpha in ((40, 10), (26, 16), (14, 24)):
        glow_surf = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (*color, alpha), glow_surf.get_rect())
        surface.blit(glow_surf, (rect.x - pad, rect.y - pad))


# ---------------------------------------------------------------------------
# Category tab icons - simple hand-drawn-primitive silhouettes that read
# clearly at small tab-icon size.
# ---------------------------------------------------------------------------


def glyph_joystick(surface, center, size, color):
    cx, cy = center
    base_r = size * 0.28
    base_rect = pygame.Rect(0, 0, base_r * 2, base_r * 0.9)
    base_rect.center = (cx, cy + size * 0.22)
    pygame.draw.ellipse(surface, color, base_rect)
    pygame.draw.line(
        surface, color, (cx, cy + size * 0.15), (cx, cy - size * 0.28),
        max(2, int(size * 0.14)),
    )
    pygame.draw.circle(surface, color, (int(cx), int(cy - size * 0.32)), max(2, int(size * 0.18)))


def glyph_puzzle(surface, center, size, color):
    cx, cy = center
    s = size * 0.62
    rect = pygame.Rect(0, 0, s, s)
    rect.center = (cx, cy)
    pygame.draw.rect(surface, color, rect, border_radius=max(1, int(size * 0.08)))
    pygame.draw.circle(surface, color, (int(cx + s / 2), int(cy)), max(1, int(size * 0.14)))


def glyph_target(surface, center, size, color):
    cx, cy = center
    pygame.draw.circle(surface, color, (int(cx), int(cy)), max(2, int(size * 0.42)), width=max(2, int(size * 0.1)))
    pygame.draw.circle(surface, color, (int(cx), int(cy)), max(1, int(size * 0.2)), width=max(1, int(size * 0.08)))
    pygame.draw.circle(surface, color, (int(cx), int(cy)), max(1, int(size * 0.08)))


def glyph_question(surface, center, size, color):
    cx, cy = center
    r = size * 0.22
    rect = pygame.Rect(0, 0, r * 2, r * 2)
    rect.center = (cx, cy - size * 0.16)
    pygame.draw.arc(surface, color, rect, math.radians(-40), math.radians(230), max(2, int(size * 0.12)))
    pygame.draw.circle(surface, color, (int(cx), int(cy + size * 0.32)), max(2, int(size * 0.07)))


CATEGORY_GLYPHS = {
    "Arcade": glyph_joystick,
    "Puzzles": glyph_puzzle,
    "Skill": glyph_target,
    "Trivia": glyph_question,
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


TAB_ICON_SIZE = int(TAB_HEIGHT * 0.5)
TAB_ICON_GAP = 8


def category_tab_rects(font):
    widths = [
        TAB_ICON_SIZE + TAB_ICON_GAP + font.size(cat)[0] + TAB_PAD_X * 2
        for cat in CATEGORY_ORDER
    ]
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
            # Soft colored glow halo behind the active tab, like a lit sign.
            for pad, alpha in ((16, 12), (9, 20)):
                glow_surf = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
                pygame.draw.rect(
                    glow_surf, (*color, alpha), glow_surf.get_rect(), border_radius=rect.height // 2
                )
                surface.blit(glow_surf, (rect.x - pad, rect.y - pad))
            pygame.draw.rect(surface, color, rect, border_radius=rect.height // 2)
            text_color = BG_COLOR
        else:
            fill = SCROLLBAR_THUMB_COLOR if hovered else SCROLLBAR_COLOR
            pygame.draw.rect(surface, fill, rect, border_radius=rect.height // 2)
            pygame.draw.rect(surface, color, rect, width=2, border_radius=rect.height // 2)
            text_color = color
        text_surf = font.render(cat, True, text_color)
        content_w = TAB_ICON_SIZE + TAB_ICON_GAP + text_surf.get_width()
        content_x = rect.centerx - content_w / 2
        icon_center = (content_x + TAB_ICON_SIZE / 2, rect.centery)
        CATEGORY_GLYPHS[cat](surface, icon_center, TAB_ICON_SIZE, text_color)
        text_x = content_x + TAB_ICON_SIZE + TAB_ICON_GAP
        surface.blit(text_surf, text_surf.get_rect(midleft=(text_x, rect.centery)))
    return rects


def content_height(cards):
    if not cards:
        return 0
    return max(card.rect.bottom for card in cards) + BOTTOM_MARGIN


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

    title_font = pygame.font.Font(str(FONTS_DIR / "Baloo2-ExtraBold.ttf"), 54)
    subtitle_font = pygame.font.Font(str(FONTS_DIR / "Nunito-Regular.ttf"), 20)
    name_font = pygame.font.Font(str(FONTS_DIR / "Baloo2-Bold.ttf"), 24)
    comment_font = pygame.font.Font(str(FONTS_DIR / "Nunito-Regular.ttf"), 16)
    tab_font = pygame.font.Font(str(FONTS_DIR / "Baloo2-Bold.ttf"), 19)

    active_category = CATEGORY_ORDER[0]
    cards = layout_cards(active_category)
    max_scroll = max(0, content_height(cards) - (HEIGHT - GRID_TOP))
    scroll = 0
    running = True

    header_bg = make_glow_background(WIDTH, GRID_TOP)
    grid_bg = make_glow_background(WIDTH, max(content_height(cards), HEIGHT - GRID_TOP))

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
                            grid_bg = make_glow_background(
                                WIDTH, max(content_height(cards), HEIGHT - GRID_TOP)
                            )
                        break

                if not clicked_tab and mouse_pos[1] >= GRID_TOP:
                    for card in cards:
                        if card.is_hovered(mouse_grid_pos):
                            pygame.display.quit()
                            pygame.mixer.quit()
                            launch_game(card.game)
                            pygame.mixer.init()
                            screen = pygame.display.set_mode((WIDTH, HEIGHT))
                            pygame.display.set_caption("Arcade")
                            load_images()
                            break

        screen.blit(header_bg, (0, 0))

        title_surf = title_font.render("Arcade", True, TITLE_COLOR)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 60))
        draw_title_glow(screen, title_rect, TITLE_COLOR)
        screen.blit(title_surf, title_rect)
        subtitle_surf = subtitle_font.render(
            "Pick a game to play!", True, SUBTITLE_COLOR
        )
        screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        draw_category_tabs(screen, active_category, mouse_pos, tab_font)

        # ---- Scrollable card grid, clipped so it never draws over the header ----
        grid_h = max(content_height(cards), HEIGHT - GRID_TOP)
        grid_surface = grid_bg.copy()

        CARD_RADIUS = 20
        for card in cards:
            hovered = mouse_pos[1] >= GRID_TOP and card.is_hovered(mouse_grid_pos)
            color = card.game["hover"] if hovered else card.game["color"]
            border_color = CATEGORY_COLORS[card.game["category"]]
            rect = card.rect.inflate(6, 6) if hovered else card.rect

            draw_glow_shadow(grid_surface, rect, color, CARD_RADIUS, hovered)
            pygame.draw.rect(grid_surface, color, rect, border_radius=CARD_RADIUS)
            draw_card_gloss(grid_surface, rect, CARD_RADIUS)
            pygame.draw.rect(
                grid_surface, border_color, rect, width=3 if hovered else 2, border_radius=CARD_RADIUS
            )

            image = card.game["image_surface"]
            img_top = rect.top + 16
            grid_surface.blit(image, image.get_rect(midtop=(rect.centerx, img_top)))

            name_color, comment_color = readable_text_color(color)

            name_top = img_top + IMAGE_SIZE + 10
            name_surf = name_font.render(card.game["name"], True, name_color)
            grid_surface.blit(
                name_surf, name_surf.get_rect(midtop=(rect.centerx, name_top))
            )

            comment_top = name_top + 32
            lines = card.game["comment"].split("\n")
            for i, line in enumerate(lines):
                line_surf = comment_font.render(line, True, comment_color)
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

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
