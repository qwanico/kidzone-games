import asyncio
import importlib
import math
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent
ICONS_DIR = BASE_DIR / "tile_icons"
FONTS_DIR = BASE_DIR / "fonts"

WIDTH, HEIGHT = 1000, 700
CARD_W, CARD_H = 280, 260
CARD_GAP = 40
COLS = 3
IMAGE_SIZE = 110
TOP_Y = 165
BOTTOM_MARGIN = 40
SCROLL_SPEED = 60
CARD_RADIUS = 26

# ---------------------------------------------------------------------------
# Design tokens - warm cream "felt-board" palette (matches the approved
# HTML mockup: https://claude.ai/code/artifact/198bd155-dfec-4b83-bb83-bc0dec3eec30)
# ---------------------------------------------------------------------------
BOARD_COLOR = (247, 236, 216)       # #F7ECD8 - background
BOARD_2_COLOR = (241, 226, 198)     # #F1E2C6 - secondary panel
INK_COLOR = (52, 40, 31)            # #34281F - primary text
INK_SOFT_COLOR = (107, 90, 72)      # #6B5A48 - secondary text
PAPER_COLOR = (255, 251, 242)       # #FFFBF2 - card/paper surface
LINE_COLOR = (230, 214, 179)        # #E6D6B3 - hairline / track color
TEAL_COLOR = (15, 141, 131)         # #0F8D83 - brand teal
TEAL_DEEP_COLOR = (10, 107, 99)     # #0A6B63
CORAL_COLOR = (255, 107, 82)        # #FF6B52 - energy / streak
CORAL_DEEP_COLOR = (225, 80, 58)    # #E1503A
SUN_COLOR = (255, 194, 60)          # #FFC23C - mascot / rewards
SUN_DEEP_COLOR = (224, 164, 35)     # #E0A423
GRASS_COLOR = (70, 171, 104)        # #46AB68
GRAPE_COLOR = (140, 95, 199)        # #8C5FC7
SKY_COLOR = (63, 169, 221)          # #3FA9DD

BG_COLOR = BOARD_COLOR
TITLE_COLOR = TEAL_DEEP_COLOR
SUBTITLE_COLOR = INK_SOFT_COLOR
TEXT_COLOR = INK_COLOR
SCROLLBAR_COLOR = LINE_COLOR
SCROLLBAR_THUMB_COLOR = TEAL_COLOR

# Streak pill placeholder - real persistence is a separate follow-up phase.
STREAK_DAYS = 7

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


def make_background(width, height):
    """Warm cream felt-board backdrop with two soft highlight washes,
    approximating the mockup's radial-gradient body background."""
    bg = pygame.Surface((width, height))
    bg.fill(BOARD_COLOR)
    highlight = pygame.Surface((width, height), pygame.SRCALPHA)
    r1 = int(width * 0.32)
    pygame.draw.circle(highlight, (255, 255, 255, 40), (int(width * 0.18), int(height * 0.05)), r1)
    r2 = int(width * 0.28)
    pygame.draw.circle(
        highlight, (255, 255, 255, 28), (int(width * 0.85), int(height * 0.35)), r2
    )
    bg.blit(highlight, (0, 0))
    return bg


def draw_soft_shadow(surface, rect, radius, offset_y=8, pad=6, alpha=70):
    """Draw a soft drop-shadow behind a rounded rect using a layered,
    semi-transparent SRCALPHA surface (pygame has no native box-shadow)."""
    shadow_w = rect.width + pad * 2
    shadow_h = rect.height + pad * 2
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.rect(
        shadow_surf,
        (*INK_COLOR, alpha),
        shadow_surf.get_rect(),
        border_radius=radius + pad,
    )
    surface.blit(shadow_surf, (rect.x - pad, rect.y - pad + offset_y))


def draw_teardrop(surface, center, radius, color, angle_deg=0, alpha=255):
    """A rounded droplet shape (circle + point), rotated to taste.
    Used both standalone (streak flame) and as a building block."""
    size = radius * 4
    temp = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    fill = (*color, alpha) if alpha < 255 else color
    pygame.draw.circle(temp, fill, (c, c + radius), radius)
    tip = (c, c - radius * 2)
    left = (c - radius, c + radius)
    right = (c + radius, c + radius)
    pygame.draw.polygon(temp, fill, [left, right, tip])
    rotated = pygame.transform.rotate(temp, angle_deg)
    surface.blit(rotated, rotated.get_rect(center=center))


def draw_sunny(surface, center, size, ticks):
    """Draw Sunny the mascot: a gently bobbing sun face with rotating rays,
    round eyes, rosy cheeks, and a curved smile. Pure per-frame drawing
    driven by pygame.time.get_ticks(), safe to call every frame inside the
    async loop (no threads/state needed beyond the ticks argument)."""
    t = ticks / 1000.0
    bob = math.sin(t * (2 * math.pi / 3.4)) * (size * 0.09)
    cx = center[0]
    cy = center[1] + bob

    face_r = size * 0.28
    ray_len = size * 0.24
    ray_w = size * 0.11
    n_rays = 8
    spin_deg = (ticks / 1000.0) * 9.0  # slow continuous rotation

    for i in range(n_rays):
        angle = math.radians(i * (360 / n_rays) + spin_deg)
        ray_surf = pygame.Surface((ray_w, ray_len), pygame.SRCALPHA)
        pygame.draw.rect(
            ray_surf, SUN_COLOR, ray_surf.get_rect(), border_radius=int(ray_w / 2)
        )
        rotated = pygame.transform.rotate(ray_surf, -math.degrees(angle))
        dist = face_r + ray_len * 0.42
        rx = cx + dist * math.sin(angle)
        ry = cy - dist * math.cos(angle)
        surface.blit(rotated, rotated.get_rect(center=(rx, ry)))

    pygame.draw.circle(surface, SUN_DEEP_COLOR, (int(cx), int(cy + face_r * 0.08)), int(face_r))
    pygame.draw.circle(surface, SUN_COLOR, (int(cx), int(cy)), int(face_r))

    eye_r = max(2, int(face_r * 0.13))
    eye_off_x = face_r * 0.36
    eye_off_y = -face_r * 0.08
    pygame.draw.circle(surface, INK_COLOR, (int(cx - eye_off_x), int(cy + eye_off_y)), eye_r)
    pygame.draw.circle(surface, INK_COLOR, (int(cx + eye_off_x), int(cy + eye_off_y)), eye_r)

    cheek_r = max(2, int(face_r * 0.2))
    cheek_off_x = face_r * 0.58
    cheek_off_y = face_r * 0.18
    cheek_surf = pygame.Surface((cheek_r * 2, cheek_r * 2), pygame.SRCALPHA)
    pygame.draw.circle(cheek_surf, (*CORAL_COLOR, 130), (cheek_r, cheek_r), cheek_r)
    surface.blit(cheek_surf, (int(cx - cheek_off_x - cheek_r), int(cy + cheek_off_y - cheek_r)))
    surface.blit(cheek_surf, (int(cx + cheek_off_x - cheek_r), int(cy + cheek_off_y - cheek_r)))

    smile_w = face_r * 1.0
    smile_h = face_r * 0.7
    smile_rect = pygame.Rect(0, 0, int(smile_w), int(smile_h))
    smile_rect.center = (int(cx), int(cy + face_r * 0.2))
    pygame.draw.arc(
        surface, INK_COLOR, smile_rect, math.radians(200), math.radians(340),
        max(2, int(face_r * 0.14)),
    )


def draw_streak_pill(surface, right_x, center_y, days, ticks):
    """Small rounded pill with a coral flame icon + day count, top-right
    of the header. Visual only for now - real streak persistence is a
    separate follow-up phase."""
    pill_h = 40
    pill_w = 96
    rect = pygame.Rect(0, 0, pill_w, pill_h)
    rect.midright = (right_x, center_y)

    draw_soft_shadow(surface, rect, radius=pill_h // 2, offset_y=4, pad=4, alpha=55)
    pygame.draw.rect(surface, PAPER_COLOR, rect, border_radius=pill_h // 2)
    pygame.draw.rect(surface, LINE_COLOR, rect, width=2, border_radius=pill_h // 2)

    flicker = math.sin(ticks / 130.0) * 2
    flame_center = (rect.x + 24, rect.centery)
    draw_teardrop(surface, flame_center, int(pill_h * 0.19), CORAL_COLOR, angle_deg=180 + flicker)

    font = pygame.font.Font(FONTS_DIR / "Baloo2-Bold.ttf", 20)
    num_surf = font.render(str(days), True, CORAL_DEEP_COLOR)
    surface.blit(num_surf, num_surf.get_rect(midleft=(rect.x + 44, rect.centery)))


async def launch_game(game):
    module = importlib.import_module(game["module"])
    if game["entry"] == "class":
        await module.Game().run()
    else:
        await module.run()


async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("Kid Zone")
    clock = pygame.time.Clock()
    load_images()

    title_font = pygame.font.Font(FONTS_DIR / "Baloo2-ExtraBold.ttf", 54)
    subtitle_font = pygame.font.Font(FONTS_DIR / "Nunito-Regular.ttf", 22)
    name_font = pygame.font.Font(FONTS_DIR / "Baloo2-Bold.ttf", 28)
    comment_font = pygame.font.Font(FONTS_DIR / "Nunito-Regular.ttf", 18)

    cards = layout_cards()
    max_scroll = max(0, content_height(cards) - HEIGHT)
    scroll = 0
    running = True

    base_bg = make_background(WIDTH, content_height(cards))

    DRAG_CLICK_THRESHOLD = 12
    dragging = False
    drag_start_y = 0
    drag_scroll_start = 0
    drag_moved = 0

    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_content_pos = (mouse_pos[0], mouse_pos[1] + scroll)
        ticks = pygame.time.get_ticks()

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
                    tap_pos = (event.pos[0], event.pos[1] + scroll)
                    for card in cards:
                        if card.is_hovered(tap_pos):
                            await launch_game(card.game)
                            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
                            pygame.display.set_caption("Kid Zone")
                            load_images()
                            break
                dragging = False

        content = base_bg.copy()

        title_surf = title_font.render("Kid Zone", True, TITLE_COLOR)
        mascot_size = 62
        gap = 16
        total_w = mascot_size + gap + title_surf.get_width()
        start_x = WIDTH // 2 - total_w // 2
        header_y = 58
        mascot_center = (start_x + mascot_size // 2, header_y)
        content.blit(
            title_surf,
            title_surf.get_rect(midleft=(start_x + mascot_size + gap, header_y)),
        )
        draw_sunny(content, mascot_center, mascot_size, ticks)

        subtitle_surf = subtitle_font.render(
            "Pick a game to play!", True, SUBTITLE_COLOR
        )
        content.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 108)))

        draw_streak_pill(content, WIDTH - 40, header_y, STREAK_DAYS, ticks)

        for card in cards:
            hovered = card.is_hovered(mouse_content_pos)
            color = card.game["hover"] if hovered else card.game["color"]

            if hovered:
                rect = card.rect.inflate(16, 16)
                rect.centery -= 4
                draw_soft_shadow(content, rect, CARD_RADIUS, offset_y=16, pad=10, alpha=95)
            else:
                rect = card.rect
                draw_soft_shadow(content, rect, CARD_RADIUS, offset_y=8, pad=6, alpha=70)

            pygame.draw.rect(content, color, rect, border_radius=CARD_RADIUS)
            pygame.draw.rect(content, PAPER_COLOR, rect, width=3, border_radius=CARD_RADIUS)

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
