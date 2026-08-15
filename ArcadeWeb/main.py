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


def draw_title_glow(surface, rect, color):
    for pad, alpha in ((40, 10), (26, 16), (14, 24)):
        glow_surf = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (*color, alpha), glow_surf.get_rect())
        surface.blit(glow_surf, (rect.x - pad, rect.y - pad))


def readable_text_color(bg_color):
    """Pick near-black or near-white text depending on a card's own
    background brightness, so light cards (Pong, Archery) stay legible
    instead of using the same light-on-light text as dark cards."""
    r, g, b = bg_color[:3]
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    if luminance > 150:
        return (30, 32, 44), (70, 74, 92)
    return (255, 255, 255), (200, 204, 220)


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
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    pygame.display.set_caption("Arcade")
    if platform is not None and hasattr(platform, "window"):
        try:
            platform.window.window_resize()
        except Exception:
            pass
    clock = pygame.time.Clock()
    load_images()

    title_font = pygame.font.Font(str(FONTS_DIR / "Baloo2-ExtraBold.ttf"), 54)
    subtitle_font = pygame.font.Font(str(FONTS_DIR / "Nunito-Regular.ttf"), 20)
    name_font = pygame.font.Font(str(FONTS_DIR / "Baloo2-Bold.ttf"), 24)
    comment_font = pygame.font.Font(str(FONTS_DIR / "Nunito-Regular.ttf"), 16)
    nav_font = pygame.font.Font(str(FONTS_DIR / "Baloo2-Bold.ttf"), 18)
    tab_font = pygame.font.Font(str(FONTS_DIR / "Baloo2-Bold.ttf"), 19)

    active_category = CATEGORY_ORDER[0]
    cards = layout_cards(active_category)
    max_scroll = max(0, content_height(cards) - (HEIGHT - GRID_TOP))
    scroll = 0
    running = True

    header_bg = make_glow_background(WIDTH, GRID_TOP)
    grid_bg = make_glow_background(WIDTH, max(content_height(cards), HEIGHT - GRID_TOP))

    nav_button = pygame.Rect(24, 20, 190, 42)

    # Touch has no scroll wheel, so a drag on the grid scrolls it; a short
    # drag (under the threshold) is instead treated as a tap-to-launch.
    # Same pattern as KidZoneWeb/main.py's menu screen.
    DRAG_CLICK_THRESHOLD = 12
    dragging = False
    drag_start_y = 0
    drag_scroll_start = 0
    drag_moved = 0

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
                if nav_button.collidepoint(event.pos):
                    go_to_kidzone()
                    continue
                clicked_tab = False
                for cat, rect in zip(CATEGORY_ORDER, tab_rects):
                    if rect.collidepoint(event.pos):
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

                if not clicked_tab and event.pos[1] >= GRID_TOP:
                    dragging = True
                    drag_start_y = event.pos[1]
                    drag_scroll_start = scroll
                    drag_moved = 0
            elif event.type == pygame.MOUSEMOTION and dragging:
                dy = event.pos[1] - drag_start_y
                drag_moved = max(drag_moved, abs(dy))
                scroll = max(0, min(drag_scroll_start - dy, max_scroll))
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if dragging and drag_moved < DRAG_CLICK_THRESHOLD:
                    tap_pos = (event.pos[0], event.pos[1] - GRID_TOP + scroll)
                    for card in cards:
                        if card.is_hovered(tap_pos):
                            await launch_game(card.game)
                            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
                            pygame.display.set_caption("Arcade")
                            if platform is not None and hasattr(platform, "window"):
                                try:
                                    platform.window.window_resize()
                                except Exception:
                                    pass
                            load_images()
                            break
                dragging = False

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
