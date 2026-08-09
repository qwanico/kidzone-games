import math
import subprocess
import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent
GAMES_DIR = BASE_DIR.parent
ICONS_DIR = BASE_DIR / "tile_icons"
FONTS_DIR = BASE_DIR / "fonts"

WIDTH, HEIGHT = 1000, 800
CARD_W, CARD_H = 280, 260
CARD_GAP = 40
COLS = 3
IMAGE_SIZE = 110
TOP_Y = 150
BOTTOM_MARGIN = 40
SCROLL_SPEED = 60

# ---------------------------------------------------------------------------
# "Felt-board" design tokens - ported from the approved Kid Zone visual
# redesign concept (warm cream background, chunky rounded cards, Sunny the
# mascot). Colors match the mockup's CSS custom properties 1:1.
# ---------------------------------------------------------------------------
BOARD_COLOR = (247, 236, 216)        # #F7ECD8 - warm cream background
BOARD_2_COLOR = (241, 226, 198)      # #F1E2C6 - secondary panel cream
INK_COLOR = (52, 40, 31)             # #34281F - warm dark brown text
INK_SOFT_COLOR = (107, 90, 72)       # #6B5A48 - softer secondary text
PAPER_COLOR = (255, 251, 242)        # #FFFBF2 - card/paper surface
LINE_COLOR = (230, 214, 179)         # #E6D6B3 - hairline / divider
TEAL_COLOR = (15, 141, 131)          # #0F8D83 - brand teal
TEAL_DEEP_COLOR = (10, 107, 99)      # #0A6B63
CORAL_COLOR = (255, 107, 82)         # #FF6B52 - energy / streak
CORAL_DEEP_COLOR = (225, 80, 58)     # #E1503A
SUN_COLOR = (255, 194, 60)           # #FFC23C - Sunny the mascot / rewards
SUN_DEEP_COLOR = (224, 164, 35)      # #E0A423
GRASS_COLOR = (70, 171, 104)         # #46AB68
GRAPE_COLOR = (140, 95, 199)         # #8C5FC7
SKY_COLOR = (63, 169, 221)           # #3FA9DD
SHADOW_COLOR = (52, 40, 31)          # ink, used at low alpha for drop shadows

BG_COLOR = BOARD_COLOR
TEXT_COLOR = INK_COLOR
TITLE_COLOR = TEAL_DEEP_COLOR
SUBTITLE_COLOR = INK_SOFT_COLOR
SCROLLBAR_COLOR = BOARD_2_COLOR
SCROLLBAR_THUMB_COLOR = CORAL_COLOR

CARD_RADIUS = 28

# Placeholder streak count for the new header pill. Real day-by-day streak
# persistence is a separate feature being built later - this is visual only.
STREAK_DAYS = 7

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
        "name": "Bug Squasher",
        "comment": "Click the bugs before\nthey scurry away!",
        "python": GAMES_DIR / "BugSquasher" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "BugSquasher" / "bug_squasher.py",
        "cwd": GAMES_DIR / "BugSquasher",
        "color": (110, 140, 80),
        "hover": (92, 122, 64),
        "image": GAMES_DIR / "BugSquasher" / "assets" / "bugsquasher_icon.png",
    },
    {
        "name": "Fish Catch",
        "comment": "Click the fish, avoid\nthe junk!",
        "python": GAMES_DIR / "FishCatch" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "FishCatch" / "fish_catch.py",
        "cwd": GAMES_DIR / "FishCatch",
        "color": (40, 120, 190),
        "hover": (30, 100, 170),
        "image": GAMES_DIR / "FishCatch" / "assets" / "fishcatch_icon.png",
    },
    {
        "name": "Star Catcher",
        "comment": "Catch falling stars,\ndodge the rocks!",
        "python": GAMES_DIR / "StarCatcher" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "StarCatcher" / "star_catcher.py",
        "cwd": GAMES_DIR / "StarCatcher",
        "color": (60, 55, 110),
        "hover": (45, 42, 90),
        "image": GAMES_DIR / "StarCatcher" / "assets" / "starcatcher_icon.png",
    },
    {
        "name": "Memory Match",
        "comment": "Flip cards to find\nmatching pairs!",
        "python": GAMES_DIR / "MemoryMatch" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "MemoryMatch" / "memory_match.py",
        "cwd": GAMES_DIR / "MemoryMatch",
        "color": (200, 90, 150),
        "hover": (180, 72, 132),
        "image": GAMES_DIR / "MemoryMatch" / "assets" / "memorymatch_icon.png",
    },
    {
        "name": "Jumping Jack",
        "comment": "Jump over obstacles\nto keep the score up!",
        "python": GAMES_DIR / "JumpingJack" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "JumpingJack" / "jumping_jack.py",
        "cwd": GAMES_DIR / "JumpingJack",
        "color": (221, 235, 100),
        "hover": (200, 215, 85),
        "image": GAMES_DIR / "JumpingJack" / "assets" / "jumpingjack_icon.png",
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


def draw_sunny(surface, center, size, ticks, spin=True):
    """Draw Sunny, the bouncy sun mascot, centered at `center` with a given
    bounding `size` (diameter). Animates a gentle vertical bob plus a slow
    ray rotation using pygame.time.get_ticks() values passed in via `ticks`.
    """
    t = ticks / 1000.0

    # Gentle bob: matches the mockup's 3.4s ease-in-out bob cycle.
    bob = math.sin(t * (2 * math.pi / 3.4)) * (size * 0.09)
    cx, cy = center[0], center[1] + bob

    # Slow ray rotation (a full turn every ~22s, like the mockup's spin).
    rotation = (t * (360.0 / 22.0)) if spin else 0.0

    face_radius = size * 0.32

    # 8 chunky rounded rays, alternating long/wide (cardinal) and
    # short/narrow (diagonal), same proportions as the reference mockup.
    for i in range(8):
        angle_deg = i * 45 + rotation
        angle_rad = math.radians(angle_deg)
        if i % 2 == 0:
            length = size * 0.46
            width = size * 0.20
        else:
            length = size * 0.38
            width = size * 0.16
        dx, dy = math.cos(angle_rad), math.sin(angle_rad)
        perp_x, perp_y = -dy, dx
        half_w = width / 2
        tip = (cx + dx * length, cy + dy * length)
        base = (cx, cy)
        points = [
            (base[0] + perp_x * half_w, base[1] + perp_y * half_w),
            (tip[0] + perp_x * half_w, tip[1] + perp_y * half_w),
            (tip[0] - perp_x * half_w, tip[1] - perp_y * half_w),
            (base[0] - perp_x * half_w, base[1] - perp_y * half_w),
        ]
        pygame.draw.polygon(surface, SUN_COLOR, points)
        pygame.draw.circle(surface, SUN_COLOR, (int(tip[0]), int(tip[1])), int(half_w))

    # Face (drawn after rays so it hides the ray bases).
    pygame.draw.circle(surface, SUN_COLOR, (int(cx), int(cy)), int(face_radius))

    # Eyes.
    eye_offset_x = size * 0.11
    eye_y = cy - size * 0.08
    eye_r = max(2, int(size * 0.06))
    pygame.draw.circle(surface, INK_COLOR, (int(cx - eye_offset_x), int(eye_y)), eye_r)
    pygame.draw.circle(surface, INK_COLOR, (int(cx + eye_offset_x), int(eye_y)), eye_r)

    # Rosy cheeks - small translucent coral circles.
    cheek_offset_x = size * 0.30
    cheek_y = cy + size * 0.06
    cheek_r = max(2, int(size * 0.08))
    cheek_surf = pygame.Surface((cheek_r * 2, cheek_r * 2), pygame.SRCALPHA)
    pygame.draw.circle(cheek_surf, (*CORAL_COLOR, 140), (cheek_r, cheek_r), cheek_r)
    surface.blit(cheek_surf, (cx - cheek_offset_x - cheek_r, cheek_y - cheek_r))
    surface.blit(cheek_surf, (cx + cheek_offset_x - cheek_r, cheek_y - cheek_r))

    # Curved smile.
    smile_w = size * 0.34
    smile_h = size * 0.24
    smile_rect = pygame.Rect(0, 0, int(smile_w), int(smile_h * 2))
    smile_rect.center = (int(cx), int(cy + size * 0.02))
    smile_thickness = max(2, int(size * 0.045))
    pygame.draw.arc(surface, INK_COLOR, smile_rect, math.pi, 2 * math.pi, smile_thickness)


def draw_card_shadow(surface, rect, radius, hovered):
    """Layer a few large, low-alpha rounded rects behind a card to fake a
    soft drop shadow (pygame has no native box-shadow blur)."""
    if hovered:
        layers = [(0, 18, 40), (0, 12, 55), (0, 7, 70)]
    else:
        layers = [(0, 10, 35), (0, 6, 50)]
    pad = 24
    for dx, dy, alpha in layers:
        shadow_surf = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
        shadow_rect = pygame.Rect(pad, pad, rect.width, rect.height)
        pygame.draw.rect(shadow_surf, (*SHADOW_COLOR, alpha), shadow_rect, border_radius=radius)
        surface.blit(shadow_surf, (rect.x - pad + dx, rect.y - pad + dy))


def draw_streak_pill(surface, right_x, top_y, font, days):
    """Draw the coral streak pill (flame icon + day count) used in the
    header. `right_x` is the pill's right edge x-coordinate."""
    text_surf = font.render(str(days), True, CORAL_DEEP_COLOR)
    flame_d = font.get_height() * 0.6
    pad_x, pad_y, gap = 14, 8, 8
    pill_w = int(flame_d + gap + text_surf.get_width() + pad_x * 2)
    pill_h = int(max(flame_d, text_surf.get_height()) + pad_y * 2)
    pill_rect = pygame.Rect(0, 0, pill_w, pill_h)
    pill_rect.topright = (right_x, top_y)

    shadow_surf = pygame.Surface((pill_w + 16, pill_h + 16), pygame.SRCALPHA)
    pygame.draw.rect(
        shadow_surf, (*SHADOW_COLOR, 45), (8, 8 + 4, pill_w, pill_h), border_radius=pill_h // 2
    )
    surface.blit(shadow_surf, (pill_rect.x - 8, pill_rect.y - 8))
    pygame.draw.rect(surface, PAPER_COLOR, pill_rect, border_radius=pill_h // 2)

    # Flame icon: a square rounded on three corners (sharp bottom-left),
    # rotated 45 degrees into a teardrop - same trick as the mockup's CSS
    # `border-radius: 50% 50% 50% 0; transform: rotate(45deg)`.
    flame_cx = pill_rect.x + pad_x + flame_d / 2
    flame_cy = pill_rect.centery
    d = int(flame_d)
    flame_surf = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.rect(
        flame_surf,
        CORAL_COLOR,
        (0, 0, d, d),
        border_top_left_radius=d // 2,
        border_top_right_radius=d // 2,
        border_bottom_right_radius=d // 2,
        border_bottom_left_radius=0,
    )
    flame_surf = pygame.transform.rotate(flame_surf, -45)
    flame_rect = flame_surf.get_rect(center=(int(flame_cx), int(flame_cy)))
    surface.blit(flame_surf, flame_rect)

    surface.blit(
        text_surf,
        text_surf.get_rect(midleft=(flame_cx + flame_d / 2 + gap, pill_rect.centery)),
    )
    return pill_rect


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

    title_font = pygame.font.Font(str(FONTS_DIR / "Baloo2-ExtraBold.ttf"), 56)
    subtitle_font = pygame.font.Font(str(FONTS_DIR / "Nunito-Bold.ttf"), 22)
    name_font = pygame.font.Font(str(FONTS_DIR / "Baloo2-Bold.ttf"), 28)
    comment_font = pygame.font.Font(str(FONTS_DIR / "Nunito-Regular.ttf"), 18)
    streak_font = pygame.font.Font(str(FONTS_DIR / "Baloo2-Bold.ttf"), 20)

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
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
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
                        pygame.display.quit()
                        pygame.mixer.quit()
                        launch_game(card.game)
                        pygame.mixer.init()
                        screen = pygame.display.set_mode((WIDTH, HEIGHT))
                        pygame.display.set_caption("Kid Zone")
                        load_images()
                        break

        ticks = pygame.time.get_ticks()

        content = pygame.Surface((WIDTH, content_height(cards)))
        content.fill(BG_COLOR)

        # ---- Header: Sunny + title, subtitle, streak pill ----
        title_surf = title_font.render("Kid Zone", True, TITLE_COLOR)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 62))
        mascot_size = 64
        mascot_center = (title_rect.left - mascot_size * 0.55 - 10, title_rect.centery)
        draw_sunny(content, mascot_center, mascot_size, ticks)
        content.blit(title_surf, title_rect)

        subtitle_surf = subtitle_font.render(
            "Pick a game to play!", True, SUBTITLE_COLOR
        )
        content.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 104)))

        draw_streak_pill(content, WIDTH - 24, 22, streak_font, STREAK_DAYS)

        for card in cards:
            hovered = card.is_hovered(mouse_content_pos)
            color = card.game["hover"] if hovered else card.game["color"]

            if hovered:
                scale = 1.05
                w, h = int(CARD_W * scale), int(CARD_H * scale)
                rect = pygame.Rect(0, 0, w, h)
                rect.center = card.rect.center
            else:
                rect = card.rect

            draw_card_shadow(content, rect, CARD_RADIUS, hovered)
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

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
