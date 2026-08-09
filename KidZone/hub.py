import json
import math
import random
import subprocess
import sys
from datetime import date
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent
GAMES_DIR = BASE_DIR.parent
ICONS_DIR = BASE_DIR / "tile_icons"
FONTS_DIR = BASE_DIR / "fonts"
PROGRESS_FILE = BASE_DIR / "progress.json"

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

# Header layout for the settings gear button, positioned relative to the
# streak pill's left edge (see streak_pill_rect()).
SETTINGS_GEAR_RADIUS = 22
SETTINGS_GEAR_GAP = 14

# ---------------------------------------------------------------------------
# Category grouping - each game carries a "category" and the home screen is
# laid out section-by-section (see layout_cards()) rather than one flat grid.
# ---------------------------------------------------------------------------
CATEGORY_ORDER = ["Learn", "Puzzles", "Active"]
SECTION_HEADER_HEIGHT = 56

GAMES = [
    {
        "name": "Feelings",
        "comment": "Pick the word that\nmatches the face!",
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
        "python": GAMES_DIR / "Math" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "Math" / "math_game.py",
        "cwd": GAMES_DIR / "Math",
        "color": (120, 180, 40),
        "hover": (100, 160, 30),
        "image": ICONS_DIR / "math.png",
    },
    {
        "name": "Memory Match",
        "comment": "Flip cards to find\nmatching pairs!",
        "category": "Puzzles",
        "python": GAMES_DIR / "MemoryMatch" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "MemoryMatch" / "memory_match.py",
        "cwd": GAMES_DIR / "MemoryMatch",
        "color": (200, 90, 150),
        "hover": (180, 72, 132),
        "image": GAMES_DIR / "MemoryMatch" / "assets" / "memorymatch_icon.png",
    },
    {
        "name": "Maze",
        "comment": "Guide the hero\nthrough the maze!",
        "category": "Puzzles",
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
        "category": "Puzzles",
        "python": GAMES_DIR / "SimonPattern" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "SimonPattern" / "simon_pattern.py",
        "cwd": GAMES_DIR / "SimonPattern",
        "color": (180, 50, 130),
        "hover": (160, 35, 112),
        "image": ICONS_DIR / "simon_pattern.png",
    },
    {
        "name": "Whack-a-Mole",
        "comment": "Click the moles\nbefore they hide!",
        "category": "Active",
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
        "category": "Active",
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
        "category": "Active",
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
        "category": "Active",
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
        "category": "Active",
        "python": GAMES_DIR / "StarCatcher" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "StarCatcher" / "star_catcher.py",
        "cwd": GAMES_DIR / "StarCatcher",
        "color": (60, 55, 110),
        "hover": (45, 42, 90),
        "image": GAMES_DIR / "StarCatcher" / "assets" / "starcatcher_icon.png",
    },
    {
        "name": "Jumping Jack",
        "comment": "Jump over obstacles\nto keep the score up!",
        "category": "Active",
        "python": GAMES_DIR / "JumpingJack" / "gameenv" / "bin" / "python",
        "script": GAMES_DIR / "JumpingJack" / "jumping_jack.py",
        "cwd": GAMES_DIR / "JumpingJack",
        "color": (221, 235, 100),
        "hover": (200, 215, 85),
        "image": GAMES_DIR / "JumpingJack" / "assets" / "jumpingjack_icon.png",
    },
]

CATEGORY_COLORS = {
    "Learn": TEAL_COLOR,
    "Puzzles": GRAPE_COLOR,
    "Active": CORAL_COLOR,
}


# ---------------------------------------------------------------------------
# Progress persistence (streaks, launch counts, achievements). Plain JSON
# file, safe-load-with-defaults - same house style as
# FruitFinder/fruit_finder.py's load_progress()/save_progress().
# ---------------------------------------------------------------------------


def default_progress():
    return {
        "last_played_date": None,
        "streak_days": 0,
        "longest_streak": 0,
        "games_played": [],
        "total_launches": 0,
        "achievements_unlocked": [],
    }


def load_progress():
    default = default_progress()
    try:
        with open(PROGRESS_FILE) as f:
            loaded = json.load(f)
            default.update(loaded)
            return default
    except (FileNotFoundError, ValueError):
        return default


def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)


def reset_progress():
    fresh = default_progress()
    save_progress(fresh)
    return fresh


def update_streak(progress):
    """Run once at startup, before the menu loop starts. Compares
    last_played_date to today and updates streak_days/longest_streak
    accordingly, then persists the result."""
    today = date.today().isoformat()
    last = progress.get("last_played_date")

    if last is None:
        progress["streak_days"] = 1
    elif last == today:
        pass
    else:
        gap = None
        try:
            gap = (date.today() - date.fromisoformat(last)).days
        except ValueError:
            gap = None
        if gap == 1:
            progress["streak_days"] += 1
        else:
            # Gap of 2+ days (streak broken) or a weird/future date - restart.
            progress["streak_days"] = 1

    progress["longest_streak"] = max(progress.get("longest_streak", 0), progress["streak_days"])
    progress["last_played_date"] = today
    save_progress(progress)
    return progress


# Each achievement gets a short kid-friendly name, a description, a felt-board
# palette color, and a simple pygame-primitive glyph (see GLYPH_DRAWERS below).
ACHIEVEMENTS = [
    {"id": "first_steps", "name": "First Steps", "desc": "Play your first game", "color": SUN_COLOR, "glyph": "star"},
    {"id": "explorer", "name": "Explorer", "desc": "Try 5 different games", "color": GRASS_COLOR, "glyph": "compass"},
    {"id": "champion", "name": "Champion", "desc": "Play every game", "color": GRAPE_COLOR, "glyph": "crown"},
    {"id": "streak_3", "name": "3 Day Streak", "desc": "Play 3 days in a row", "color": CORAL_COLOR, "glyph": "flame"},
    {"id": "streak_7", "name": "7 Day Streak", "desc": "Play 7 days in a row", "color": CORAL_COLOR, "glyph": "flame"},
    {"id": "streak_30", "name": "30 Day Streak", "desc": "Play 30 days in a row", "color": CORAL_COLOR, "glyph": "flame"},
    {"id": "superfan", "name": "Superfan", "desc": "Launch games 50 times", "color": SKY_COLOR, "glyph": "heart"},
]


def _achievement_condition(achievement_id, progress):
    if achievement_id == "first_steps":
        return len(progress["games_played"]) >= 1
    if achievement_id == "explorer":
        return len(progress["games_played"]) >= 5
    if achievement_id == "champion":
        return len(progress["games_played"]) >= len(GAMES)
    if achievement_id == "streak_3":
        return progress["streak_days"] >= 3
    if achievement_id == "streak_7":
        return progress["streak_days"] >= 7
    if achievement_id == "streak_30":
        return progress["streak_days"] >= 30
    if achievement_id == "superfan":
        return progress["total_launches"] >= 50
    return False


def check_achievements(progress):
    """Check every achievement's condition against the current progress and
    unlock (+ save) any that are newly earned. Returns the list of newly
    unlocked achievement ids."""
    newly_unlocked = []
    for achievement in ACHIEVEMENTS:
        aid = achievement["id"]
        if aid not in progress["achievements_unlocked"] and _achievement_condition(aid, progress):
            progress["achievements_unlocked"].append(aid)
            newly_unlocked.append(aid)
    if newly_unlocked:
        save_progress(progress)
    return newly_unlocked


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


def streak_pill_rect(right_x, top_y, font, days):
    """Compute the streak pill's rect without drawing anything, so callers
    can lay out neighboring UI (e.g. the settings gear button) against it
    before the pill itself is drawn."""
    text_surf = font.render(str(days), True, CORAL_DEEP_COLOR)
    flame_d = font.get_height() * 0.6
    pad_x, pad_y, gap = 14, 8, 8
    pill_w = int(flame_d + gap + text_surf.get_width() + pad_x * 2)
    pill_h = int(max(flame_d, text_surf.get_height()) + pad_y * 2)
    pill_rect = pygame.Rect(0, 0, pill_w, pill_h)
    pill_rect.topright = (right_x, top_y)
    return pill_rect


def draw_streak_pill(surface, right_x, top_y, font, days):
    """Draw the coral streak pill (flame icon + day count) used in the
    header. `right_x` is the pill's right edge x-coordinate."""
    text_surf = font.render(str(days), True, CORAL_DEEP_COLOR)
    flame_d = font.get_height() * 0.6
    pad_x, gap = 14, 8
    pill_rect = streak_pill_rect(right_x, top_y, font, days)
    pill_w, pill_h = pill_rect.width, pill_rect.height

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


# ---------------------------------------------------------------------------
# Small badge/icon glyphs - all drawn with pygame primitives, no images or
# emoji, so they match the hand-drawn felt-board style used elsewhere
# (Sunny, the streak pill's flame teardrop, etc).
# ---------------------------------------------------------------------------


def _star_points(center, outer_r, inner_r, points, rotation=-90):
    cx, cy = center
    pts = []
    for i in range(points * 2):
        angle = math.radians(rotation + i * 180 / points)
        r = outer_r if i % 2 == 0 else inner_r
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return pts


def glyph_star(surface, center, size, color):
    pygame.draw.polygon(surface, color, _star_points(center, size * 0.5, size * 0.22, 5))


def glyph_compass(surface, center, size, color):
    pygame.draw.polygon(surface, color, _star_points(center, size * 0.5, size * 0.18, 4))
    pygame.draw.circle(surface, color, (int(center[0]), int(center[1])), max(2, int(size * 0.08)))


def glyph_crown(surface, center, size, color):
    cx, cy = center
    half_w = size * 0.42
    base_y = cy + size * 0.22
    top_y = cy - size * 0.30
    base_rect = pygame.Rect(0, 0, int(half_w * 2), int(size * 0.16))
    base_rect.midtop = (cx, base_y - size * 0.02)
    pygame.draw.rect(surface, color, base_rect, border_radius=3)
    peak_w = half_w * 2 / 3
    peak_positions = (cx - half_w + peak_w / 2, cx, cx + half_w - peak_w / 2)
    for i, px in enumerate(peak_positions):
        peak_top = top_y if i == 1 else top_y + size * 0.12
        pts = [(px - peak_w / 2, base_y), (px, peak_top), (px + peak_w / 2, base_y)]
        pygame.draw.polygon(surface, color, pts)
        pygame.draw.circle(surface, color, (int(px), int(peak_top)), max(2, int(size * 0.06)))


def glyph_flame(surface, center, size, color):
    # Same "rounded square rotated 45 degrees" teardrop trick as the header
    # streak pill's flame icon, just bigger and centered on `center`.
    d = max(2, int(size * 0.8))
    flame_surf = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.rect(
        flame_surf,
        color,
        (0, 0, d, d),
        border_top_left_radius=d // 2,
        border_top_right_radius=d // 2,
        border_bottom_right_radius=d // 2,
        border_bottom_left_radius=0,
    )
    flame_surf = pygame.transform.rotate(flame_surf, -45)
    flame_rect = flame_surf.get_rect(center=(int(center[0]), int(center[1])))
    surface.blit(flame_surf, flame_rect)


def glyph_heart(surface, center, size, color):
    cx, cy = center
    r = size * 0.22
    pygame.draw.circle(surface, color, (int(cx - r * 0.9), int(cy - r * 0.4)), int(r))
    pygame.draw.circle(surface, color, (int(cx + r * 0.9), int(cy - r * 0.4)), int(r))
    pts = [(cx - r * 1.8, cy - r * 0.1), (cx + r * 1.8, cy - r * 0.1), (cx, cy + r * 1.7)]
    pygame.draw.polygon(surface, color, pts)


GLYPH_DRAWERS = {
    "star": glyph_star,
    "compass": glyph_compass,
    "crown": glyph_crown,
    "flame": glyph_flame,
    "heart": glyph_heart,
}

LOCKED_GLYPH_COLOR = (196, 184, 166)  # muted silhouette, matches board palette


def draw_achievement_badge(surface, center, radius, achievement, unlocked):
    """Circular medallion badge. Unlocked badges use the achievement's full
    palette color; locked ones render greyed-out/silhouette."""
    center = (int(center[0]), int(center[1]))
    if unlocked:
        ring_color = achievement["color"]
        fill_color = PAPER_COLOR
        glyph_color = achievement["color"]
    else:
        ring_color = LINE_COLOR
        fill_color = BOARD_2_COLOR
        glyph_color = LOCKED_GLYPH_COLOR

    pygame.draw.circle(surface, fill_color, center, radius)
    pygame.draw.circle(surface, ring_color, center, radius, width=4)
    drawer = GLYPH_DRAWERS.get(achievement["glyph"], glyph_star)
    drawer(surface, center, radius * 1.3, glyph_color)


def draw_icon_button_bg(surface, center, radius, hovered):
    """Paper-colored circular button with a soft drop shadow, matching the
    streak pill's paper/shadow treatment. Returns the button's hit rect."""
    center = (int(center[0]), int(center[1]))
    pad = 8
    shadow_surf = pygame.Surface((radius * 2 + pad * 2, radius * 2 + pad * 2), pygame.SRCALPHA)
    pygame.draw.circle(shadow_surf, (*SHADOW_COLOR, 45), (radius + pad, radius + pad + 3), radius)
    surface.blit(shadow_surf, (center[0] - radius - pad, center[1] - radius - pad))

    fill = BOARD_2_COLOR if hovered else PAPER_COLOR
    pygame.draw.circle(surface, fill, center, radius)
    pygame.draw.circle(surface, LINE_COLOR, center, radius, width=2)

    rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    rect.center = center
    return rect


def draw_gear_icon(surface, center, radius, color, hole_color):
    cx, cy = center
    teeth = 8
    outer_r = radius * 0.95
    inner_r = radius * 0.55
    tooth_w = radius * 0.34
    for i in range(teeth):
        angle = math.radians(i * (360 / teeth))
        dx, dy = math.cos(angle), math.sin(angle)
        tip = (cx + dx * outer_r, cy + dy * outer_r)
        base = (cx + dx * inner_r * 0.85, cy + dy * inner_r * 0.85)
        perp = (-dy, dx)
        hw = tooth_w / 2
        pts = [
            (base[0] + perp[0] * hw, base[1] + perp[1] * hw),
            (tip[0] + perp[0] * hw, tip[1] + perp[1] * hw),
            (tip[0] - perp[0] * hw, tip[1] - perp[1] * hw),
            (base[0] - perp[0] * hw, base[1] - perp[1] * hw),
        ]
        pygame.draw.polygon(surface, color, pts)
    pygame.draw.circle(surface, color, (int(cx), int(cy)), int(inner_r))
    pygame.draw.circle(surface, hole_color, (int(cx), int(cy)), max(2, int(inner_r * 0.45)))


def draw_settings_button(surface, center, radius, hovered):
    """Gear-shaped icon button used to open the parental gate. Drawn in the
    same paper-button style as the header's streak pill."""
    rect = draw_icon_button_bg(surface, center, radius, hovered)
    fill_bg = BOARD_2_COLOR if hovered else PAPER_COLOR
    draw_gear_icon(surface, center, radius * 0.62, INK_SOFT_COLOR, fill_bg)
    return rect


def draw_back_button(surface, rect, font, hovered):
    color = BOARD_2_COLOR if hovered else PAPER_COLOR
    pygame.draw.rect(surface, color, rect, border_radius=16)
    pygame.draw.rect(surface, LINE_COLOR, rect, width=2, border_radius=16)
    text_surf = font.render("Back", True, INK_COLOR)
    surface.blit(text_surf, text_surf.get_rect(center=rect.center))


# ---------------------------------------------------------------------------
# Parental gate: a simple arithmetic question a 3-7 year old can't answer,
# gating access to the settings/reset screen. Low-stakes - a wrong answer
# just reshuffles the question, no lockout or penalty.
# ---------------------------------------------------------------------------

GATE_BTN_W, GATE_BTN_H = 170, 90
GATE_BACK_BUTTON = pygame.Rect(24, HEIGHT - 74, 140, 50)


def new_gate_challenge():
    a = random.randint(4, 15)
    b = random.randint(4, 15)
    correct = a + b
    wrongs = set()
    while len(wrongs) < 2:
        delta = random.choice([-4, -3, -2, -1, 1, 2, 3, 4])
        candidate = correct + delta
        if candidate > 0 and candidate != correct:
            wrongs.add(candidate)
    choices = [correct] + list(wrongs)
    random.shuffle(choices)
    return {"a": a, "b": b, "answer": correct, "choices": choices}


def gate_choice_rects():
    gap = 40
    total_w = GATE_BTN_W * 3 + gap * 2
    start_x = (WIDTH - total_w) // 2
    y = 420
    return [pygame.Rect(start_x + i * (GATE_BTN_W + gap), y, GATE_BTN_W, GATE_BTN_H) for i in range(3)]


def draw_gate_screen(surface, challenge, mouse_pos, fonts):
    surface.fill(BG_COLOR)

    q_surf = fonts["title"].render(
        f"Grown-ups: what is {challenge['a']} + {challenge['b']}?", True, INK_COLOR
    )
    surface.blit(q_surf, q_surf.get_rect(center=(WIDTH // 2, 220)))

    sub_surf = fonts["subtitle"].render(
        "(This keeps settings just for grown-ups!)", True, SUBTITLE_COLOR
    )
    surface.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, 270)))

    rects = gate_choice_rects()
    for rect, value in zip(rects, challenge["choices"]):
        hovered = rect.collidepoint(mouse_pos)
        color = TEAL_COLOR if hovered else PAPER_COLOR
        text_color = PAPER_COLOR if hovered else INK_COLOR
        draw_card_shadow(surface, rect, 20, hovered)
        pygame.draw.rect(surface, color, rect, border_radius=20)
        pygame.draw.rect(surface, LINE_COLOR, rect, width=3, border_radius=20)
        val_surf = fonts["name"].render(str(value), True, text_color)
        surface.blit(val_surf, val_surf.get_rect(center=rect.center))

    back_hovered = GATE_BACK_BUTTON.collidepoint(mouse_pos)
    draw_back_button(surface, GATE_BACK_BUTTON, fonts["comment"], back_hovered)

    return rects


# ---------------------------------------------------------------------------
# Parent settings screen: streak stats, achievement grid, reset progress
# (with a confirm step) and a way back to the hub menu.
# ---------------------------------------------------------------------------

SETTINGS_BACK_BUTTON = pygame.Rect(24, HEIGHT - 74, 140, 50)
SETTINGS_RESET_BUTTON = pygame.Rect(WIDTH - 24 - 240, HEIGHT - 74, 240, 50)
CONFIRM_YES_BUTTON = pygame.Rect(WIDTH // 2 - 170, HEIGHT // 2 + 35, 150, 60)
CONFIRM_NO_BUTTON = pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 + 35, 150, 60)

ACHIEVEMENT_GRID_COLS = 4
ACHIEVEMENT_CELL_W, ACHIEVEMENT_CELL_H = 220, 150


def achievement_grid_rects():
    grid_w = ACHIEVEMENT_GRID_COLS * ACHIEVEMENT_CELL_W
    start_x = (WIDTH - grid_w) // 2
    start_y = 250
    rects = []
    for i in range(len(ACHIEVEMENTS)):
        row, col = divmod(i, ACHIEVEMENT_GRID_COLS)
        x = start_x + col * ACHIEVEMENT_CELL_W
        y = start_y + row * ACHIEVEMENT_CELL_H
        rects.append(pygame.Rect(x, y, ACHIEVEMENT_CELL_W, ACHIEVEMENT_CELL_H))
    return rects


def draw_confirm_overlay(surface, mouse_pos, fonts):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((*SHADOW_COLOR, 140))
    surface.blit(overlay, (0, 0))

    box = pygame.Rect(0, 0, 480, 220)
    box.center = (WIDTH // 2, HEIGHT // 2)
    pygame.draw.rect(surface, PAPER_COLOR, box, border_radius=24)
    pygame.draw.rect(surface, LINE_COLOR, box, width=3, border_radius=24)

    text_surf = fonts["name"].render("Are you sure?", True, INK_COLOR)
    surface.blit(text_surf, text_surf.get_rect(center=(WIDTH // 2, box.top + 55)))
    sub_surf = fonts["comment"].render(
        "This clears all streaks and achievements.", True, INK_SOFT_COLOR
    )
    surface.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, box.top + 92)))

    for rect, label, base_color, deep_color in (
        (CONFIRM_YES_BUTTON, "Yes", CORAL_COLOR, CORAL_DEEP_COLOR),
        (CONFIRM_NO_BUTTON, "No", TEAL_COLOR, TEAL_DEEP_COLOR),
    ):
        hovered = rect.collidepoint(mouse_pos)
        pygame.draw.rect(surface, deep_color if hovered else base_color, rect, border_radius=14)
        label_surf = fonts["comment"].render(label, True, PAPER_COLOR)
        surface.blit(label_surf, label_surf.get_rect(center=rect.center))


def draw_settings_screen(surface, progress, mouse_pos, fonts, confirm_reset):
    surface.fill(BG_COLOR)

    title_surf = fonts["title"].render("Grown-Up Settings", True, TITLE_COLOR)
    surface.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 55)))

    streak_days = progress["streak_days"]
    longest = progress["longest_streak"]
    streak_line = f"Current streak: {streak_days} day{'s' if streak_days != 1 else ''}"
    longest_line = f"Longest streak: {longest} day{'s' if longest != 1 else ''}"
    s1 = fonts["subtitle"].render(streak_line, True, INK_COLOR)
    s2 = fonts["subtitle"].render(longest_line, True, INK_COLOR)
    surface.blit(s1, s1.get_rect(center=(WIDTH // 2, 100)))
    surface.blit(s2, s2.get_rect(center=(WIDTH // 2, 128)))

    ach_title = fonts["subtitle"].render("Achievements", True, SUBTITLE_COLOR)
    surface.blit(ach_title, ach_title.get_rect(center=(WIDTH // 2, 175)))

    for rect, achievement in zip(achievement_grid_rects(), ACHIEVEMENTS):
        unlocked = achievement["id"] in progress["achievements_unlocked"]
        badge_center = (rect.centerx, rect.top + 52)
        draw_achievement_badge(surface, badge_center, 40, achievement, unlocked)
        name_color = INK_COLOR if unlocked else INK_SOFT_COLOR
        name_surf = fonts["comment"].render(achievement["name"], True, name_color)
        surface.blit(name_surf, name_surf.get_rect(center=(rect.centerx, rect.top + 108)))

    back_hovered = SETTINGS_BACK_BUTTON.collidepoint(mouse_pos)
    draw_back_button(surface, SETTINGS_BACK_BUTTON, fonts["comment"], back_hovered)

    reset_hovered = SETTINGS_RESET_BUTTON.collidepoint(mouse_pos)
    pygame.draw.rect(
        surface,
        CORAL_DEEP_COLOR if reset_hovered else CORAL_COLOR,
        SETTINGS_RESET_BUTTON,
        border_radius=16,
    )
    reset_text = fonts["comment"].render("Reset Progress", True, PAPER_COLOR)
    surface.blit(reset_text, reset_text.get_rect(center=SETTINGS_RESET_BUTTON.center))

    if confirm_reset:
        draw_confirm_overlay(surface, mouse_pos, fonts)


def layout_cards():
    """Lay the grid out section-by-section (Learn / Puzzles / Active) rather
    than as one flat grid, so the home screen reads as organized categories.
    Returns (cards, section_headers) where section_headers is a list of
    (label, color, top_y) for the draw code to render above each group."""
    cards = []
    section_headers = []
    y = TOP_Y
    for category in CATEGORY_ORDER:
        games_in_category = [g for g in GAMES if g["category"] == category]
        if not games_in_category:
            continue

        section_headers.append((category, CATEGORY_COLORS[category], y))
        y += SECTION_HEADER_HEIGHT

        for i, game in enumerate(games_in_category):
            row, col = divmod(i, COLS)
            row_start = row * COLS
            row_count = min(COLS, len(games_in_category) - row_start)
            row_w = row_count * CARD_W + max(0, row_count - 1) * CARD_GAP
            row_start_x = (WIDTH - row_w) // 2

            x = row_start_x + col * (CARD_W + CARD_GAP)
            card_y = y + row * (CARD_H + CARD_GAP)
            cards.append(Card(game, (x, card_y, CARD_W, CARD_H)))

        rows = math.ceil(len(games_in_category) / COLS)
        y += rows * (CARD_H + CARD_GAP)

    return cards, section_headers


def draw_section_header(surface, label, color, top_y, font):
    text_surf = font.render(label, True, color)
    text_rect = text_surf.get_rect(midtop=(WIDTH // 2, top_y + 6))
    surface.blit(text_surf, text_rect)
    underline_rect = pygame.Rect(0, 0, max(70, text_rect.width + 24), 4)
    underline_rect.midtop = (WIDTH // 2, text_rect.bottom + 6)
    pygame.draw.rect(surface, color, underline_rect, border_radius=2)


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


# Hub menu state machine. The grid/scroll flow lives in STATE_MENU;
# STATE_GATE is the parental math-question gate; STATE_SETTINGS is the
# streak/achievements/reset screen it unlocks.
STATE_MENU = "menu"
STATE_GATE = "gate"
STATE_SETTINGS = "settings"


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
    section_font = pygame.font.Font(str(FONTS_DIR / "Baloo2-Bold.ttf"), 26)
    fonts = {
        "title": title_font,
        "subtitle": subtitle_font,
        "name": name_font,
        "comment": comment_font,
        "streak": streak_font,
        "section": section_font,
    }

    # ---- Real progress/streak tracking, loaded once at startup ----
    progress = load_progress()
    update_streak(progress)

    cards, section_headers = layout_cards()
    max_scroll = max(0, content_height(cards) - HEIGHT)
    scroll = 0
    running = True

    state = STATE_MENU
    gate_challenge = None
    settings_confirm_reset = False

    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_content_pos = (mouse_pos[0], mouse_pos[1] + scroll)

        # Header layout (streak pill + settings gear) computed up front so
        # this frame's click handling matches what actually gets drawn.
        pill_rect = streak_pill_rect(WIDTH - 24, 22, streak_font, progress["streak_days"])
        gear_center = (
            pill_rect.left - SETTINGS_GEAR_GAP - SETTINGS_GEAR_RADIUS,
            pill_rect.centery,
        )
        settings_button_rect = pygame.Rect(0, 0, SETTINGS_GEAR_RADIUS * 2, SETTINGS_GEAR_RADIUS * 2)
        settings_button_rect.center = (int(gear_center[0]), int(gear_center[1]))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if state in (STATE_GATE, STATE_SETTINGS):
                    state = STATE_MENU
                    settings_confirm_reset = False
                else:
                    running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN and state == STATE_MENU:
                scroll = min(scroll + SCROLL_SPEED, max_scroll)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP and state == STATE_MENU:
                scroll = max(scroll - SCROLL_SPEED, 0)
            elif event.type == pygame.MOUSEWHEEL and state == STATE_MENU:
                scroll = max(0, min(scroll - event.y * SCROLL_SPEED, max_scroll))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == STATE_MENU:
                    if settings_button_rect.collidepoint(mouse_content_pos):
                        gate_challenge = new_gate_challenge()
                        state = STATE_GATE
                    else:
                        for card in cards:
                            if card.is_hovered(mouse_content_pos):
                                # Record the launch + which game before handing
                                # off to the subprocess, then re-check
                                # achievements against the updated progress.
                                progress["total_launches"] += 1
                                if card.game["name"] not in progress["games_played"]:
                                    progress["games_played"].append(card.game["name"])
                                save_progress(progress)
                                check_achievements(progress)

                                pygame.display.quit()
                                pygame.mixer.quit()
                                launch_game(card.game)
                                pygame.mixer.init()
                                screen = pygame.display.set_mode((WIDTH, HEIGHT))
                                pygame.display.set_caption("Kid Zone")
                                load_images()
                                break

                elif state == STATE_GATE:
                    if GATE_BACK_BUTTON.collidepoint(mouse_pos):
                        state = STATE_MENU
                    else:
                        for rect, value in zip(gate_choice_rects(), gate_challenge["choices"]):
                            if rect.collidepoint(mouse_pos):
                                if value == gate_challenge["answer"]:
                                    settings_confirm_reset = False
                                    state = STATE_SETTINGS
                                else:
                                    gate_challenge = new_gate_challenge()
                                break

                elif state == STATE_SETTINGS:
                    if settings_confirm_reset:
                        if CONFIRM_YES_BUTTON.collidepoint(mouse_pos):
                            progress = reset_progress()
                            settings_confirm_reset = False
                        elif CONFIRM_NO_BUTTON.collidepoint(mouse_pos):
                            settings_confirm_reset = False
                    else:
                        if SETTINGS_BACK_BUTTON.collidepoint(mouse_pos):
                            state = STATE_MENU
                        elif SETTINGS_RESET_BUTTON.collidepoint(mouse_pos):
                            settings_confirm_reset = True

        if state == STATE_GATE:
            draw_gate_screen(screen, gate_challenge, mouse_pos, fonts)
            pygame.display.flip()
            clock.tick(60)
            continue

        if state == STATE_SETTINGS:
            draw_settings_screen(screen, progress, mouse_pos, fonts, settings_confirm_reset)
            pygame.display.flip()
            clock.tick(60)
            continue

        # ---- STATE_MENU: scrolling grid + header ----
        ticks = pygame.time.get_ticks()

        content = pygame.Surface((WIDTH, content_height(cards)))
        content.fill(BG_COLOR)

        # ---- Header: Sunny + title, subtitle, streak pill, settings gear ----
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

        draw_streak_pill(content, WIDTH - 24, 22, streak_font, progress["streak_days"])
        gear_hovered = settings_button_rect.collidepoint(mouse_content_pos)
        draw_settings_button(content, gear_center, SETTINGS_GEAR_RADIUS, gear_hovered)

        for label, color, top_y in section_headers:
            draw_section_header(content, label, color, top_y, section_font)

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
