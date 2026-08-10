import asyncio
import importlib
import json
import math
import random
from datetime import date
from pathlib import Path

import pygame

try:
    import platform
except ImportError:
    platform = None

BASE_DIR = Path(__file__).parent
ICONS_DIR = BASE_DIR / "tile_icons"
FONTS_DIR = BASE_DIR / "fonts"

# ---------------------------------------------------------------------------
# Responsive layout - every size below is a *default* matching the old
# fixed 1000x700 canvas; apply_responsive_layout() overwrites all of them
# at hub startup based on the real browser viewport size (see
# get_viewport_size()), so a phone gets a taller header and a 2-column
# grid while a tablet/desktop keeps the wider 3-column grid, instead of
# the hub always assuming one fixed screen size regardless of device.
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 1000, 700
CARD_W, CARD_H = 280, 260
CARD_GAP = 40
CARD_MARGIN = 40
COLS = 3
IMAGE_SIZE = 110
BOTTOM_MARGIN = 40
SCROLL_SPEED = 60
CARD_RADIUS = 26
SCALE = 1.0
IS_NARROW = False

# Fixed header (title/streak/tabs/featured) stays put; only the card grid
# below it scrolls, so switching categories always lands on a stable,
# un-scrolled page.
HEADER_Y = 58
SUBTITLE_Y = 100
STATS_Y = 130
GRID_TOP = 225
TAB_BAR_TOP = 143
TAB_HEIGHT = 44
TAB_PAD_X = 26
TAB_GAP = 14
FEATURED_TOP = 190
FEATURED_H = 150


def get_viewport_size(default=(1000, 700)):
    """The real on-screen size of the browser tab hosting this pygbag app,
    or `default` outside a real browser (desktop dev, `python main.py`)."""
    if platform is not None and hasattr(platform, "window"):
        try:
            w = int(platform.window.innerWidth)
            h = int(platform.window.innerHeight)
            if w > 200 and h > 200:
                return w, h
        except Exception:
            pass
    return default


def resize_window():
    """pygbag only recalculates the canvas's on-screen CSS size when this is
    called - it never runs automatically after a game hands control back to
    the hub with its own set_mode(), which otherwise leaves the hub rendered
    inside whatever (smaller) canvas size the last game left behind."""
    if platform is not None and hasattr(platform, "window"):
        try:
            platform.window.window_resize()
        except Exception:
            pass


def clamp(value, lo, hi):
    return max(lo, min(value, hi))


def apply_responsive_layout(width, height):
    """Recompute every size-dependent layout constant from the actual
    viewport size. Called once at hub startup, before load_images()/
    layout_cards()/category_tab_rects() etc. run, since all of those read
    these same names as module globals."""
    global WIDTH, HEIGHT, COLS, CARD_W, CARD_H, CARD_GAP, CARD_MARGIN
    global IMAGE_SIZE, CARD_RADIUS, SCALE, IS_NARROW, HEADER_Y
    global GRID_TOP, TAB_BAR_TOP, TAB_HEIGHT, TAB_PAD_X, TAB_GAP
    global FEATURED_TOP, FEATURED_H, SUBTITLE_Y, STATS_Y

    WIDTH = clamp(width, 360, 1600)
    HEIGHT = clamp(height, 480, 1300)
    IS_NARROW = WIDTH < 760
    SCALE = clamp(WIDTH / 1000, 0.62, 1.2)

    COLS = 2 if IS_NARROW else 3
    CARD_MARGIN = 22 if IS_NARROW else 40
    CARD_GAP = 18 if IS_NARROW else 32

    usable_w = WIDTH - CARD_MARGIN * 2
    CARD_W = int((usable_w - CARD_GAP * (COLS - 1)) / COLS)
    CARD_W = clamp(CARD_W, 140, 300)
    # 1.05, not the visually-tighter 0.95 the original fixed-size design
    # used - real rendered text (name + 2-line comment) needs more room
    # underneath the icon than that ratio leaves, at every screen size,
    # which was cutting the second comment line off against the card's
    # own bottom edge.
    CARD_H = int(CARD_W * 1.1)
    CARD_RADIUS = clamp(int(30 * SCALE), 18, 30)
    IMAGE_SIZE = clamp(int(CARD_W * 0.4), 56, 120)

    HEADER_Y = int(clamp(60 * SCALE, 40, 60))
    TAB_HEIGHT = int(clamp(58 * SCALE, 50, 58))
    TAB_PAD_X = int(clamp(20 * SCALE, 14, 20))
    TAB_GAP = int(clamp(14 * SCALE, 10, 14))

    # Header has three stacked rows below the mascot/title baseline -
    # subtitle, then the star/trophy progress pills - computed here once
    # so nothing else needs to (re)derive these same offsets and risk
    # drifting out of sync with them (that drift is exactly what caused
    # the subtitle and stats row to previously overlap).
    SUBTITLE_Y = HEADER_Y + int(clamp(40 * SCALE, 32, 40))
    STATS_Y = SUBTITLE_Y + int(clamp(34 * SCALE, 26, 34))

    TAB_BAR_TOP = STATS_Y + int(clamp(26 * SCALE, 20, 26))
    FEATURED_TOP = TAB_BAR_TOP + TAB_HEIGHT + int(clamp(18 * SCALE, 14, 18))
    FEATURED_H = int(clamp(158 * SCALE, 128, 158))
    GRID_TOP = FEATURED_TOP + FEATURED_H + int(clamp(22 * SCALE, 16, 22))

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
SKY_SOFT_COLOR = (214, 235, 249)    # #D6EBF9 - pale sky wash for the background gradient

BG_COLOR = BOARD_COLOR
TITLE_COLOR = TEAL_DEEP_COLOR
SUBTITLE_COLOR = INK_SOFT_COLOR
TEXT_COLOR = INK_COLOR
SCROLLBAR_COLOR = LINE_COLOR
SCROLLBAR_THUMB_COLOR = TEAL_COLOR

# Muted "greyed out" treatment for locked achievement badges.
LOCKED_BADGE_COLOR = (214, 205, 190)
LOCKED_RING_COLOR = LINE_COLOR
LOCKED_GLYPH_COLOR = (178, 166, 148)

GAMES = [
    {
        "key": "feelings",
        "name": "Feelings",
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Learn",
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
        "category": "Active",
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
        "category": "Active",
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
        "category": "Active",
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
        "category": "Active",
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
        "category": "Active",
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
        "category": "Puzzles",
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
        "category": "Active",
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
        "category": "Puzzles",
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
        "category": "Puzzles",
        "comment": "Watch the pattern,\nthen click it back!",
        "module": "games.simon_pattern",
        "entry": "class",
        "color": (180, 50, 130),
        "hover": (160, 35, 112),
        "image": ICONS_DIR / "simon_pattern.png",
    },
]


# ---------------------------------------------------------------------------
# Progress persistence - real browser localStorage, NOT a JSON file.
#
# The FruitFinder web port persists high scores into a progress.json inside
# its asset folder, but that folder lives on a virtual filesystem that gets
# freshly re-extracted from the shipped .tar.gz/.apk archive on every single
# page load (see default.tmpl's custom_site(): it always unpacks the archive
# into /data/data/{bundle} fresh). Writes there do not survive a reload, so a
# "daily streak" built the same way would silently never work. Instead we
# read/write one JSON-encoded string under a single key in the browser's
# real localStorage, via pygbag's `platform` bridge (`platform.window` is
# the actual `window` object in the hosting browser tab).
#
# `platform` is only pygbag's browser bridge inside the real
# pygbag/Emscripten runtime; under plain desktop CPython (e.g. `python
# main.py`, used for local dev/testing) `platform` is just the stdlib
# module and has no `.window`, so LocalStorageBackend degrades to an
# in-memory store for that process only - the hub still works, it just
# won't persist across restarts without a real browser.
# ---------------------------------------------------------------------------
PROGRESS_KEY = "kidzone_progress"

DEFAULT_PROGRESS = {
    "last_played_date": None,
    "streak_days": 0,
    "longest_streak": 0,
    "games_played": [],
    "total_launches": 0,
    "achievements_unlocked": [],
}


class LocalStorageBackend:
    """Bridge to the real browser `window.localStorage`. Reachability is
    probed once at construction; every call is wrapped so a desktop/dev
    environment (where `platform` is the stdlib module with no `.window`)
    degrades to an in-memory fallback instead of crashing."""

    def __init__(self):
        self._window = None
        try:
            import platform  # pygbag's browser bridge - real only in-browser

            window = platform.window
            window.localStorage  # touch it now; raises if not really present
            self._window = window
        except Exception:
            self._window = None
        self._memory = None

    @property
    def reachable(self):
        return self._window is not None

    def get_item(self):
        if self._window is not None:
            try:
                return self._window.localStorage.getItem(PROGRESS_KEY)
            except Exception:
                pass
        return self._memory

    def set_item(self, value):
        if self._window is not None:
            try:
                self._window.localStorage.setItem(PROGRESS_KEY, value)
                return
            except Exception:
                pass
        self._memory = value


_storage = LocalStorageBackend()


def load_progress(backend=None):
    backend = backend if backend is not None else _storage
    progress = dict(DEFAULT_PROGRESS)
    raw = backend.get_item()
    if raw:
        try:
            saved = json.loads(raw)
            if isinstance(saved, dict):
                progress.update(saved)
        except (ValueError, TypeError):
            pass
    # Defensive copies so callers can mutate lists without aliasing DEFAULT_PROGRESS.
    progress["games_played"] = list(progress.get("games_played") or [])
    progress["achievements_unlocked"] = list(progress.get("achievements_unlocked") or [])
    return progress


def save_progress(progress, backend=None):
    backend = backend if backend is not None else _storage
    backend.set_item(json.dumps(progress))


def reset_progress(backend=None):
    progress = dict(DEFAULT_PROGRESS)
    progress["games_played"] = []
    progress["achievements_unlocked"] = []
    save_progress(progress, backend)
    return progress


def check_achievements(progress):
    """Check every achievement condition against the current progress and
    unlock (record + return) any that are newly earned."""
    conditions = {
        "first_steps": len(progress["games_played"]) >= 1,
        "explorer": len(progress["games_played"]) >= 5,
        "champion": len(progress["games_played"]) >= len(GAMES),
        "streak_3": progress["streak_days"] >= 3,
        "streak_7": progress["streak_days"] >= 7,
        "streak_30": progress["streak_days"] >= 30,
        "superfan": progress["total_launches"] >= 50,
    }
    newly_unlocked = []
    for key, met in conditions.items():
        if met and key not in progress["achievements_unlocked"]:
            progress["achievements_unlocked"].append(key)
            newly_unlocked.append(key)
    return newly_unlocked


def apply_daily_streak(progress, today=None, backend=None):
    """Run once at hub startup (before the menu loop): compare
    last_played_date to today and bump/reset the streak accordingly, then
    persist immediately."""
    if today is None:
        today = date.today()

    last_raw = progress.get("last_played_date")
    last_date = None
    if last_raw:
        try:
            last_date = date.fromisoformat(last_raw)
        except ValueError:
            last_date = None

    if last_date is None:
        progress["streak_days"] = 1
    elif last_date == today:
        pass  # already counted today - no change
    elif (today - last_date).days == 1:
        progress["streak_days"] += 1
    else:
        progress["streak_days"] = 1  # gap bigger than one day - reset

    progress["longest_streak"] = max(progress.get("longest_streak", 0), progress["streak_days"])
    progress["last_played_date"] = today.isoformat()
    newly_unlocked = check_achievements(progress)
    save_progress(progress, backend)
    return newly_unlocked


def record_game_launch(progress, game_name, backend=None):
    """Hook called from the card click handler in main() wherever
    launch_game() fires: tracks which games were played and how many times
    any game has been launched in total, then unlocks/saves as needed."""
    if game_name not in progress["games_played"]:
        progress["games_played"].append(game_name)
    progress["total_launches"] += 1
    newly_unlocked = check_achievements(progress)
    save_progress(progress, backend)
    return newly_unlocked


def make_gate_question():
    """A fresh simple addition question for the parental gate, with one
    correct and two plausible-but-wrong multiple-choice answers."""
    a = random.randint(4, 15)
    b = random.randint(4, 15)
    answer = a + b

    wrong_choices = set()
    while len(wrong_choices) < 2:
        candidate = answer + random.choice([-4, -3, -2, -1, 1, 2, 3, 4])
        if candidate >= 0 and candidate != answer:
            wrong_choices.add(candidate)

    choices = [answer] + list(wrong_choices)
    random.shuffle(choices)
    return {"a": a, "b": b, "answer": answer, "choices": choices}


class Card:
    def __init__(self, game, rect):
        self.game = game
        self.rect = pygame.Rect(rect)

    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)


CATEGORY_ORDER = ["Learn", "Puzzles", "Active"]
CATEGORY_COLORS = {
    "Learn": TEAL_COLOR,
    "Puzzles": GRAPE_COLOR,
    "Active": CORAL_COLOR,
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


def category_tab_rects():
    """Three big equal-width buttons spanning the same margins as the card
    grid below them - large, evenly-spaced touch targets rather than pills
    sized tightly to their own label text."""
    n = len(CATEGORY_ORDER)
    usable_w = WIDTH - CARD_MARGIN * 2
    tab_w = (usable_w - TAB_GAP * (n - 1)) // n
    rects = []
    x = CARD_MARGIN
    for _ in range(n):
        rects.append(pygame.Rect(x, TAB_BAR_TOP, tab_w, TAB_HEIGHT))
        x += tab_w + TAB_GAP
    return rects


def draw_category_tabs(surface, active_category, mouse_pos, font):
    rects = category_tab_rects()
    icon_size = int(TAB_HEIGHT * 0.48)
    icon_gap = int(clamp(10 * SCALE, 7, 10))
    for cat, rect in zip(CATEGORY_ORDER, rects):
        color = CATEGORY_COLORS[cat]
        is_active = cat == active_category
        hovered = rect.collidepoint(mouse_pos)
        draw_soft_shadow(surface, rect, rect.height // 2, offset_y=4, pad=6, alpha=45)
        if is_active:
            pygame.draw.rect(surface, color, rect, border_radius=rect.height // 2)
            pygame.draw.rect(surface, PAPER_COLOR, rect, width=3, border_radius=rect.height // 2)
            text_color = PAPER_COLOR
        else:
            fill = PAPER_COLOR if hovered else BOARD_2_COLOR
            pygame.draw.rect(surface, fill, rect, border_radius=rect.height // 2)
            pygame.draw.rect(surface, color, rect, width=3, border_radius=rect.height // 2)
            text_color = color
        text_surf = font.render(cat.upper(), True, text_color)
        content_w = icon_size + icon_gap + text_surf.get_width()
        content_x = rect.centerx - content_w / 2
        icon_center = (content_x + icon_size / 2, rect.centery)
        CATEGORY_GLYPHS[cat](surface, icon_center, icon_size, text_color)
        text_x = content_x + icon_size + icon_gap
        surface.blit(text_surf, text_surf.get_rect(midleft=(text_x, rect.centery)))
    return rects


def content_height(cards):
    if not cards:
        return 0
    return max(card.rect.bottom for card in cards) + BOTTOM_MARGIN


def load_images():
    for game in GAMES:
        raw = pygame.image.load(str(game["image"])).convert_alpha()
        w, h = raw.get_size()
        scale = IMAGE_SIZE / max(w, h)
        game["image_surface"] = pygame.transform.smoothscale(
            raw, (int(w * scale), int(h * scale))
        )


def _draw_cloud(surface, cx, cy, scale=1.0):
    puffs = [(-30, 4, 24), (0, -8, 32), (32, 3, 26), (58, 8, 20)]
    for dx, dy, r in puffs:
        pygame.draw.circle(
            surface, (255, 255, 255, 100),
            (int(cx + dx * scale), int(cy + dy * scale)), max(1, int(r * scale)),
        )


CLOUD_LAYOUT = [(0.12, 0.06, 1.0), (0.55, 0.03, 0.8), (0.86, 0.14, 0.65)]


def make_background(width, height, y_offset=0, total_height=None):
    """Soft sky-to-cream gradient with a few gentle, stationary clouds -
    calm playground feel without motion or a busy pattern. `y_offset`/
    `total_height` let the header/grid slices of the same page share one
    continuous gradient/cloud layout instead of each restarting fresh
    from their own top edge, which would show as a visible seam."""
    total_height = total_height or height
    bg = pygame.Surface((width, height))
    fade_span = max(1, total_height * 0.55)
    for y in range(height):
        t = clamp((y_offset + y) / fade_span, 0.0, 1.0)
        r = int(SKY_SOFT_COLOR[0] + (BOARD_COLOR[0] - SKY_SOFT_COLOR[0]) * t)
        g = int(SKY_SOFT_COLOR[1] + (BOARD_COLOR[1] - SKY_SOFT_COLOR[1]) * t)
        b = int(SKY_SOFT_COLOR[2] + (BOARD_COLOR[2] - SKY_SOFT_COLOR[2]) * t)
        pygame.draw.line(bg, (r, g, b), (0, y), (width, y))

    cloud_layer = pygame.Surface((width, height), pygame.SRCALPHA)
    for cx_f, cy_f, cscale in CLOUD_LAYOUT:
        cx = cx_f * width
        cy = cy_f * total_height - y_offset
        if -80 <= cy <= height + 80:
            _draw_cloud(cloud_layer, cx, cy, cscale)
    bg.blit(cloud_layer, (0, 0))

    highlight = pygame.Surface((width, height), pygame.SRCALPHA)
    r1 = int(width * 0.32)
    pygame.draw.circle(highlight, (255, 255, 255, 30), (int(width * 0.18), int(height * 0.05) - y_offset), r1)
    r2 = int(width * 0.28)
    pygame.draw.circle(
        highlight, (255, 255, 255, 22), (int(width * 0.85), int(total_height * 0.35) - y_offset), r2
    )
    bg.blit(highlight, (0, 0))
    return bg


_shadow_cache = {}
_gloss_cache = {}


def draw_soft_shadow(surface, rect, radius, offset_y=8, pad=6, alpha=70):
    """Draw a soft drop-shadow behind a rounded rect using a layered,
    semi-transparent SRCALPHA surface (pygame has no native box-shadow).
    Every card/pill/button on screen draws one of these every frame, so the
    rendered surface is cached by its (small, fixed-per-layout) size/radius/
    alpha instead of being reallocated 60 times a second."""
    shadow_w = rect.width + pad * 2
    shadow_h = rect.height + pad * 2
    key = (shadow_w, shadow_h, radius, alpha)
    shadow_surf = _shadow_cache.get(key)
    if shadow_surf is None:
        shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surf,
            (*INK_COLOR, alpha),
            shadow_surf.get_rect(),
            border_radius=radius + pad,
        )
        _shadow_cache[key] = shadow_surf
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

    # Small twinkling sparkle drifting near the mascot - lightweight (one
    # 4-point star, no particles) idle-animation touch.
    twinkle = (math.sin(t * 2.1) + 1) / 2  # 0..1
    if twinkle > 0.35:
        sparkle_alpha = int(clamp((twinkle - 0.35) / 0.65, 0, 1) * 220)
        sparkle_r = face_r * (0.16 + 0.06 * twinkle)
        sx = cx + face_r * 1.55
        sy = cy - face_r * 1.05 + math.sin(t * 1.4) * face_r * 0.12
        s = int(sparkle_r * 2.4)
        sparkle_surf = pygame.Surface((s, s), pygame.SRCALPHA)
        c = s / 2
        pts = [
            (c, c - sparkle_r), (c + sparkle_r * 0.22, c - sparkle_r * 0.22),
            (c + sparkle_r, c), (c + sparkle_r * 0.22, c + sparkle_r * 0.22),
            (c, c + sparkle_r), (c - sparkle_r * 0.22, c + sparkle_r * 0.22),
            (c - sparkle_r, c), (c - sparkle_r * 0.22, c - sparkle_r * 0.22),
        ]
        pygame.draw.polygon(sparkle_surf, (*PAPER_COLOR, sparkle_alpha), pts)
        surface.blit(sparkle_surf, (int(sx - c), int(sy - c)))


def draw_streak_pill(surface, right_x, center_y, days, ticks, font):
    """Small rounded pill with a coral flame icon + day count, top-right
    of the header. `days` is the real loaded/updated streak_days value from
    progress (see apply_daily_streak). Sized from SCALE like every other
    header element so it can never collide with the title/mascot group on
    a narrow phone width."""
    pill_h = int(clamp(40 * SCALE, 30, 40))
    flame_d = pill_h * 0.6
    num_surf = font.render(str(days), True, CORAL_DEEP_COLOR)
    pill_w = int(flame_d + 14 + num_surf.get_width() + 16)
    rect = pygame.Rect(0, 0, pill_w, pill_h)
    rect.midright = (right_x, center_y)

    draw_soft_shadow(surface, rect, radius=pill_h // 2, offset_y=4, pad=4, alpha=55)
    pygame.draw.rect(surface, PAPER_COLOR, rect, border_radius=pill_h // 2)
    pygame.draw.rect(surface, LINE_COLOR, rect, width=2, border_radius=pill_h // 2)

    flicker = math.sin(ticks / 130.0) * 2
    flame_center = (rect.x + flame_d * 0.6, rect.centery)
    draw_teardrop(surface, flame_center, int(pill_h * 0.19), CORAL_COLOR, angle_deg=180 + flicker)

    surface.blit(num_surf, num_surf.get_rect(midleft=(rect.x + flame_d + 10, rect.centery)))
    return rect


def draw_stat_pill(surface, right_x, center_y, value, glyph_fn, glyph_color, font):
    """Compact ⭐/🏆-style progress pill - reuses the same achievement
    glyphs already drawn on the settings screen, just smaller, so this
    reads as the *same* reward system rather than a second one."""
    pill_h = int(clamp(34 * SCALE, 28, 34))
    num_surf = font.render(str(value), True, INK_COLOR)
    pill_w = int(pill_h + 16 + num_surf.get_width() + 16)
    rect = pygame.Rect(0, 0, pill_w, pill_h)
    rect.midright = (right_x, center_y)

    draw_soft_shadow(surface, rect, radius=pill_h // 2, offset_y=3, pad=3, alpha=45)
    pygame.draw.rect(surface, PAPER_COLOR, rect, border_radius=pill_h // 2)
    pygame.draw.rect(surface, LINE_COLOR, rect, width=2, border_radius=pill_h // 2)

    glyph_center = (rect.x + pill_h * 0.5, rect.centery)
    glyph_fn(surface, glyph_center, pill_h * 0.36, glyph_color)
    surface.blit(num_surf, num_surf.get_rect(midleft=(rect.x + pill_h * 0.5 + 15, rect.centery)))
    return rect


def draw_featured_card(surface, rect, game, fonts, play_hovered):
    """'Today's Adventure' banner - an obvious, unmissable starting point
    for a child, built entirely from an existing game's own name/icon/
    description/click-handler rather than a fake placeholder game."""
    draw_soft_shadow(surface, rect, radius=CARD_RADIUS, offset_y=8, pad=8, alpha=65)
    pygame.draw.rect(surface, game["color"], rect, border_radius=CARD_RADIUS)
    pygame.draw.rect(surface, PAPER_COLOR, rect, width=3, border_radius=CARD_RADIUS)

    pad = int(clamp(18 * SCALE, 12, 18))

    icon_size = int(rect.height * 0.6)
    icon = pygame.transform.smoothscale(game["image_surface"], (icon_size, icon_size))
    plate_rect = pygame.Rect(0, 0, icon_size + pad, icon_size + pad)
    plate_rect.midleft = (rect.x + pad, rect.centery)
    pygame.draw.rect(surface, PAPER_COLOR, plate_rect, border_radius=int(CARD_RADIUS * 0.7))
    surface.blit(icon, icon.get_rect(center=plate_rect.center))

    btn_w = int(clamp(148 * SCALE, 118, 156))
    btn_h = int(clamp(46 * SCALE, 38, 48))
    play_rect = pygame.Rect(0, 0, btn_w, btn_h)
    play_rect.bottomright = (rect.right - pad, rect.bottom - pad)

    text_x = plate_rect.right + pad
    # Always measured against the button's actual position (it never
    # moves off bottom-right) - using a looser limit on narrow screens
    # previously let wide description text get drawn and then silently
    # painted over by the button itself, instead of being skipped.
    text_right_limit = play_rect.left - pad

    eyebrow_surf = fonts["featured_eyebrow"].render("TODAY'S ADVENTURE", True, PAPER_COLOR)
    surface.blit(eyebrow_surf, (text_x, rect.y + pad))

    title_surf = fonts["featured_title"].render(game["name"], True, PAPER_COLOR)
    title_y = rect.y + pad + eyebrow_surf.get_height() + 2
    surface.blit(title_surf, (text_x, title_y))

    desc_line = game["comment"].replace("\n", " ")
    desc_font = fonts["featured_desc"]
    desc_surf = desc_font.render(desc_line, True, PAPER_COLOR)
    if desc_surf.get_width() > text_right_limit - text_x and text_right_limit > text_x:
        # narrow layout: drop the description rather than clip it, the
        # eyebrow + title + PLAY NOW button already carry the message.
        pass
    else:
        surface.blit(desc_surf, (text_x, title_y + title_surf.get_height() + 4))

    draw_button(
        surface, play_rect, "PLAY NOW", fonts["featured_btn"],
        PAPER_COLOR, BOARD_2_COLOR, play_hovered, text_color=game["color"],
    )
    return play_rect


def draw_button(surface, rect, label, font, base_color, hover_color, hovered, text_color=(255, 255, 255)):
    """Generic felt-board rounded-pill button: soft shadow, filled color,
    paper-colored ring, centered label. Used for the gate/settings/reset
    buttons so they match the existing card styling."""
    color = hover_color if hovered else base_color
    draw_soft_shadow(surface, rect, radius=rect.height // 2, offset_y=4, pad=4, alpha=60)
    pygame.draw.rect(surface, color, rect, border_radius=rect.height // 2)
    pygame.draw.rect(surface, PAPER_COLOR, rect, width=3, border_radius=rect.height // 2)
    text_surf = font.render(label, True, text_color)
    surface.blit(text_surf, text_surf.get_rect(center=rect.center))


def draw_lock_icon(surface, center, size, color, hole_color):
    """A simple padlock built from pygame primitives - body, shackle arc,
    and a punched-through keyhole - used for the parent settings button."""
    body_rect = pygame.Rect(0, 0, size * 0.85, size * 0.62)
    body_rect.center = (center[0], center[1] + size * 0.16)
    pygame.draw.rect(surface, color, body_rect, border_radius=int(size * 0.14))

    shackle_r = size * 0.26
    shackle_rect = pygame.Rect(0, 0, shackle_r * 2, shackle_r * 2)
    shackle_rect.midbottom = (center[0], body_rect.top + size * 0.05)
    pygame.draw.arc(
        surface, color, shackle_rect, math.radians(15), math.radians(165),
        max(2, int(size * 0.14)),
    )

    keyhole_r = max(2, int(size * 0.09))
    pygame.draw.circle(surface, hole_color, body_rect.center, keyhole_r)


def draw_arcade_icon(surface, center, size, color, hole_color):
    """A tiny game controller - rounded body plus two button dots - used
    for the link over to the Arcade hub."""
    body_rect = pygame.Rect(0, 0, size * 0.9, size * 0.5)
    body_rect.center = center
    pygame.draw.rect(surface, color, body_rect, border_radius=int(size * 0.22))

    dot_r = max(2, int(size * 0.09))
    pygame.draw.circle(surface, hole_color, (center[0] + size * 0.2, center[1] - size * 0.06), dot_r)
    pygame.draw.circle(surface, hole_color, (center[0] + size * 0.32, center[1] + size * 0.06), dot_r)

    stick_w = max(2, int(size * 0.08))
    cx = center[0] - size * 0.24
    cy = center[1]
    pygame.draw.line(surface, hole_color, (cx - size * 0.1, cy), (cx + size * 0.1, cy), stick_w)
    pygame.draw.line(surface, hole_color, (cx, cy - size * 0.1), (cx, cy + size * 0.1), stick_w)


def go_to_arcade():
    if platform is not None and hasattr(platform, "window"):
        try:
            platform.window.location.href = "/arcade/"
            return
        except Exception:
            pass
    print("(would navigate to /arcade/ — Arcade)")


def draw_icon_button(surface, center, radius, hovered, icon_fn):
    """Small round felt-board icon button (settings gear/lock) drawn in the
    same paper/shadow/hairline style as the streak pill."""
    rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    rect.center = center
    fill = BOARD_2_COLOR if hovered else PAPER_COLOR
    draw_soft_shadow(surface, rect, radius=radius, offset_y=4, pad=4, alpha=55)
    pygame.draw.circle(surface, fill, center, radius)
    pygame.draw.circle(surface, LINE_COLOR, center, radius, width=2)
    icon_fn(surface, center, radius * 0.9, INK_COLOR if hovered else INK_SOFT_COLOR, fill)
    return rect


# ---------------------------------------------------------------------------
# Achievement badges - simple pygame-drawn glyphs on a circular medallion,
# matching the felt-board palette used everywhere else in the hub.
# ---------------------------------------------------------------------------
def draw_glyph_check(surface, center, r, color):
    pts = [
        (center[0] - r, center[1] + r * 0.05),
        (center[0] - r * 0.2, center[1] + r * 0.65),
        (center[0] + r, center[1] - r * 0.55),
    ]
    pygame.draw.lines(surface, color, False, pts, max(3, int(r * 0.32)))


def draw_glyph_star(surface, center, r, color):
    pts = []
    for i in range(10):
        angle = math.radians(-90 + i * 36)
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((center[0] + rad * math.cos(angle), center[1] + rad * math.sin(angle)))
    pygame.draw.polygon(surface, color, pts)


def draw_glyph_trophy(surface, center, r, color):
    cup_rect = pygame.Rect(0, 0, r * 1.3, r * 0.9)
    cup_rect.center = (center[0], center[1] - r * 0.15)
    pygame.draw.rect(surface, color, cup_rect, border_radius=int(r * 0.25))

    handle_r = max(1, int(r * 0.32))
    handle_w = max(2, int(r * 0.16))
    pygame.draw.circle(surface, color, (cup_rect.left, cup_rect.centery), handle_r, width=handle_w)
    pygame.draw.circle(surface, color, (cup_rect.right, cup_rect.centery), handle_r, width=handle_w)

    stem_rect = pygame.Rect(0, 0, max(2, r * 0.22), max(2, r * 0.28))
    stem_rect.midtop = (center[0], cup_rect.bottom)
    pygame.draw.rect(surface, color, stem_rect)

    base_rect = pygame.Rect(0, 0, r * 0.9, max(2, r * 0.16))
    base_rect.midtop = (center[0], stem_rect.bottom)
    pygame.draw.rect(surface, color, base_rect, border_radius=int(r * 0.08))


def draw_glyph_flame(surface, center, r, color):
    draw_teardrop(surface, center, max(2, int(r * 0.85)), color, angle_deg=180)


def draw_glyph_heart(surface, center, r, color):
    lobe_r = max(2, r * 0.5)
    offset = lobe_r * 0.65
    pygame.draw.circle(surface, color, (center[0] - offset, center[1] - lobe_r * 0.25), int(lobe_r))
    pygame.draw.circle(surface, color, (center[0] + offset, center[1] - lobe_r * 0.25), int(lobe_r))
    tip = (center[0], center[1] + r * 0.75)
    left_p = (center[0] - r, center[1] - lobe_r * 0.1)
    right_p = (center[0] + r, center[1] - lobe_r * 0.1)
    pygame.draw.polygon(surface, color, [left_p, right_p, tip])


# ---------------------------------------------------------------------------
# Category tab icons - same hand-drawn-primitive style as the achievement
# glyphs above, just simpler silhouettes that read clearly at tab-icon size.
# ---------------------------------------------------------------------------


def draw_glyph_book(surface, center, size, color):
    cx, cy = center
    w, h = size * 0.42, size * 0.62
    gap = max(1, size * 0.05)
    r = max(1, int(size * 0.1))
    left_rect = pygame.Rect(0, 0, w, h)
    left_rect.topright = (cx - gap / 2, cy - h / 2)
    right_rect = pygame.Rect(0, 0, w, h)
    right_rect.topleft = (cx + gap / 2, cy - h / 2)
    pygame.draw.rect(surface, color, left_rect, border_top_left_radius=r, border_bottom_left_radius=r)
    pygame.draw.rect(surface, color, right_rect, border_top_right_radius=r, border_bottom_right_radius=r)


def draw_glyph_puzzle(surface, center, size, color):
    cx, cy = center
    s = size * 0.62
    rect = pygame.Rect(0, 0, s, s)
    rect.center = (cx, cy)
    pygame.draw.rect(surface, color, rect, border_radius=max(1, int(size * 0.08)))
    pygame.draw.circle(surface, color, (int(cx + s / 2), int(cy)), max(1, int(size * 0.14)))


def draw_glyph_bolt(surface, center, size, color):
    cx, cy = center
    s = size * 0.5
    pts = [
        (cx - s * 0.1, cy - s),
        (cx + s * 0.4, cy - s * 0.05),
        (cx + s * 0.05, cy - s * 0.05),
        (cx + s * 0.1, cy + s),
        (cx - s * 0.4, cy + s * 0.05),
        (cx - s * 0.05, cy + s * 0.05),
    ]
    pygame.draw.polygon(surface, color, pts)


CATEGORY_GLYPHS = {
    "Learn": draw_glyph_book,
    "Puzzles": draw_glyph_puzzle,
    "Active": draw_glyph_bolt,
}


ACHIEVEMENTS = [
    {"id": "first_steps", "name": "First Steps", "color": TEAL_COLOR, "glyph": draw_glyph_check},
    {"id": "explorer", "name": "Explorer", "color": SKY_COLOR, "glyph": draw_glyph_star},
    {"id": "champion", "name": "Champion", "color": SUN_COLOR, "glyph": draw_glyph_trophy},
    {"id": "streak_3", "name": "3-Day Streak", "color": CORAL_COLOR, "glyph": draw_glyph_flame},
    {"id": "streak_7", "name": "7-Day Streak", "color": CORAL_DEEP_COLOR, "glyph": draw_glyph_flame},
    {"id": "streak_30", "name": "30-Day Streak", "color": SUN_DEEP_COLOR, "glyph": draw_glyph_flame},
    {"id": "superfan", "name": "Super Fan", "color": GRAPE_COLOR, "glyph": draw_glyph_heart},
]


def draw_badge(surface, center, radius, achievement, unlocked):
    """Circular medallion: full color + glyph when unlocked, greyed-out
    silhouette when locked."""
    if unlocked:
        fill_color = achievement["color"]
        ring_color = PAPER_COLOR
        glyph_color = (255, 255, 255)
        shadow_alpha = 55
    else:
        fill_color = LOCKED_BADGE_COLOR
        ring_color = LOCKED_RING_COLOR
        glyph_color = LOCKED_GLYPH_COLOR
        shadow_alpha = 30

    shadow_rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
    draw_soft_shadow(surface, shadow_rect, radius=radius, offset_y=5, pad=5, alpha=shadow_alpha)
    pygame.draw.circle(surface, fill_color, center, radius)
    pygame.draw.circle(surface, ring_color, center, radius, width=4)
    achievement["glyph"](surface, center, radius * 0.55, glyph_color)


def silence_all_audio():
    """The hub plays no sound of its own, so when a game hands control back
    we unconditionally stop every channel. Games are each responsible for
    stopping their own music/voice channels, but one that leaks a looping
    channel would otherwise keep playing over the menu forever - this is
    the backstop so a single game's cleanup bug can't do that again."""
    try:
        pygame.mixer.stop()
    except Exception:
        pass
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass


async def launch_game(game):
    module = importlib.import_module(game["module"])
    try:
        if game["entry"] == "class":
            await module.Game().run()
        else:
            await module.run()
    finally:
        # finally, so a game that raises still can't leave audio looping
        # over the hub (and the caller still restores the display).
        silence_all_audio()


STATE_MENU = "menu"
STATE_GATE = "gate"
STATE_SETTINGS = "settings"


async def main():
    pygame.init()

    # ---- Responsive sizing: use the real browser viewport instead of a
    # fixed 1000x700 canvas, so phones get a taller/narrower layout with
    # fewer columns instead of a huge letterboxed black margin. ----
    apply_responsive_layout(*get_viewport_size())

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
    resize_window()
    pygame.display.set_caption("Kid Zone")
    clock = pygame.time.Clock()
    load_images()

    title_size = int(clamp(58 * SCALE, 36, 60))
    subtitle_size = int(clamp(22 * SCALE, 16, 23))
    stat_pill_size = int(clamp(18 * SCALE, 15, 18))
    name_font = pygame.font.Font(FONTS_DIR / "Baloo2-Bold.ttf", int(clamp(28 * SCALE, 20, 29)))
    comment_font = pygame.font.Font(FONTS_DIR / "Nunito-Regular.ttf", int(clamp(18 * SCALE, 14, 18)))
    gate_title_font = pygame.font.Font(FONTS_DIR / "Baloo2-ExtraBold.ttf", 40)
    settings_title_font = pygame.font.Font(
        FONTS_DIR / "Baloo2-ExtraBold.ttf", int(clamp(40 * SCALE, 28, 40))
    )
    stat_font = pygame.font.Font(FONTS_DIR / "Baloo2-Bold.ttf", int(clamp(22 * SCALE, 16, 22)))
    badge_label_font = pygame.font.Font(FONTS_DIR / "Nunito-Bold.ttf", int(clamp(15 * SCALE, 12, 15)))
    button_font = pygame.font.Font(FONTS_DIR / "Baloo2-Bold.ttf", 22)

    title_font = pygame.font.Font(FONTS_DIR / "Baloo2-ExtraBold.ttf", title_size)
    subtitle_font = pygame.font.Font(FONTS_DIR / "Nunito-Regular.ttf", subtitle_size)
    stat_pill_font = pygame.font.Font(FONTS_DIR / "Baloo2-Bold.ttf", stat_pill_size)
    tab_font = pygame.font.Font(FONTS_DIR / "Baloo2-Bold.ttf", int(clamp(24 * SCALE, 17, 25)))
    featured_fonts = {
        "featured_eyebrow": pygame.font.Font(FONTS_DIR / "Nunito-Bold.ttf", int(clamp(15 * SCALE, 12, 15))),
        "featured_title": pygame.font.Font(FONTS_DIR / "Baloo2-Bold.ttf", int(clamp(28 * SCALE, 20, 29))),
        "featured_desc": pygame.font.Font(FONTS_DIR / "Nunito-Regular.ttf", int(clamp(17 * SCALE, 13, 17))),
        "featured_btn": pygame.font.Font(FONTS_DIR / "Baloo2-Bold.ttf", int(clamp(19 * SCALE, 15, 19))),
    }

    active_category = CATEGORY_ORDER[0]
    cards = layout_cards(active_category)
    max_scroll = max(0, content_height(cards) - (HEIGHT - GRID_TOP))
    scroll = 0
    running = True

    # Today's Adventure: an existing game (Find The Food), not an invented
    # placeholder - keeps a single, obvious starting point for a child.
    featured_game = next((g for g in GAMES if g["key"] == "fruit_finder"), GAMES[0])

    header_bg = make_background(WIDTH, GRID_TOP, y_offset=0, total_height=HEIGHT)
    grid_bg = make_background(
        WIDTH, max(content_height(cards), HEIGHT - GRID_TOP),
        y_offset=GRID_TOP, total_height=HEIGHT,
    )
    settings_bg = make_background(WIDTH, HEIGHT)

    # Real persistence: load saved progress, then run the once-per-startup
    # daily streak check (see apply_daily_streak's docstring) before the
    # menu loop even starts.
    progress = load_progress()
    apply_daily_streak(progress)

    state = STATE_MENU

    gate_question = make_gate_question()
    gate_message = ""
    gate_message_until = 0
    confirm_reset = False

    DRAG_CLICK_THRESHOLD = 12
    dragging = False
    drag_start_y = 0
    drag_scroll_start = 0
    drag_moved = 0

    # Brief squash-and-recover press feedback before a card/featured/play
    # launch actually hands off to the game - purely visual, drawn as a
    # few extra frames on top of the current screen rather than requiring
    # a rewrite of the whole per-frame drawing pipeline.
    async def press_feedback(rect, color):
        for step in range(6):
            shrink = int(clamp(8 * SCALE, 4, 8) * math.sin(step / 5 * math.pi))
            r = rect.inflate(-shrink, -shrink)
            pygame.draw.rect(screen, color, r, border_radius=CARD_RADIUS)
            pygame.display.flip()
            await asyncio.sleep(0.014)

    # --- Fixed layout for the header row (mascot/title, stat pills, nav) ---
    gear_radius = int(clamp(22 * SCALE, 18, 22))
    gear_center = (WIDTH - CARD_MARGIN - gear_radius, HEADER_Y)
    gear_rect = pygame.Rect(0, 0, gear_radius * 2, gear_radius * 2)
    gear_rect.center = gear_center

    nav_center = (CARD_MARGIN + gear_radius, HEADER_Y)
    nav_rect = pygame.Rect(0, 0, gear_radius * 2, gear_radius * 2)
    nav_rect.center = nav_center

    featured_rect = pygame.Rect(CARD_MARGIN, FEATURED_TOP, WIDTH - CARD_MARGIN * 2, FEATURED_H)

    # Shrink the "Kid Zone" title/mascot group to fit if needed, so it can
    # never collide with the gear icon + streak pill cluster on the right
    # (or the arcade-nav icon on the left) on a narrow phone width - a
    # fixed font size that was fine at 1000px wide isn't guaranteed to be
    # safe at 380px wide.
    mascot_size = int(clamp(104 * SCALE, 68, 104))
    title_gap = int(clamp(18 * SCALE, 10, 18))
    side_reserve = gear_radius * 2 + CARD_MARGIN + 96
    available_center_w = max(150, WIDTH - side_reserve * 2)
    for candidate_size in range(title_size, 21, -2):
        candidate_font = pygame.font.Font(FONTS_DIR / "Baloo2-ExtraBold.ttf", candidate_size)
        candidate_w = candidate_font.size("Kid Zone")[0]
        if mascot_size + title_gap + candidate_w <= available_center_w or candidate_size <= 22:
            title_font = candidate_font
            break

    GATE_BTN_W = int(clamp(150 * SCALE, 110, 150))
    GATE_BTN_H = int(clamp(64 * SCALE, 52, 64))
    gate_gap = int(clamp(30 * SCALE, 16, 30))
    gate_total_w = GATE_BTN_W * 3 + gate_gap * 2
    gate_max_w = WIDTH - 24
    if gate_total_w > gate_max_w:
        # 3 buttons at their own width floor can be a few px wider than the
        # narrowest legal WIDTH (360) - shrink to guarantee they always fit
        # on-screen instead of overflowing both edges.
        GATE_BTN_W = max(80, (gate_max_w - gate_gap * 2) // 3)
        gate_total_w = GATE_BTN_W * 3 + gate_gap * 2
    gate_start_x = WIDTH // 2 - gate_total_w // 2

    # Gate screen's title/question/hint/buttons/message are stacked from a
    # single starting offset so the text block above the buttons can never
    # collide with them, regardless of HEIGHT (fixed pixel offsets here
    # once caused the hint text to overlap the buttons on tall/narrow
    # phone viewports, since the buttons used to be placed at a HEIGHT
    # fraction independent of the text stack above them).
    GATE_TITLE_Y = int(clamp(HEIGHT * 0.12, 70, 130))
    GATE_Q_Y = GATE_TITLE_Y + int(clamp(58 * SCALE, 48, 70))
    GATE_HINT_Y = GATE_Q_Y + int(clamp(38 * SCALE, 32, 45))
    GATE_BTN_Y = GATE_HINT_Y + int(clamp(38 * SCALE, 32, 48))
    GATE_MSG_Y = GATE_BTN_Y + GATE_BTN_H + int(clamp(40 * SCALE, 30, 50))
    GATE_BACK_Y = max(GATE_MSG_Y + int(clamp(50 * SCALE, 40, 60)), int(HEIGHT * 0.71))

    gate_choice_rects = [
        pygame.Rect(
            gate_start_x + i * (GATE_BTN_W + gate_gap), GATE_BTN_Y, GATE_BTN_W, GATE_BTN_H
        )
        for i in range(3)
    ]
    gate_back_rect = pygame.Rect(0, 0, 220, 52)
    gate_back_rect.center = (WIDTH // 2, GATE_BACK_Y)

    settings_back_rect = pygame.Rect(
        0, 0, int(clamp(130 * SCALE, 100, 130)), int(clamp(50 * SCALE, 40, 50))
    )
    settings_back_rect.topleft = (CARD_MARGIN, CARD_MARGIN)

    # The "Parent Settings" title is normally dead-centered, but on a narrow
    # phone width a true center overlaps the back button in the top-left -
    # shift it right just enough to clear the button instead, only when
    # that overlap would actually happen (desktop/tablet stay dead-centered).
    settings_title_gap = int(clamp(20 * SCALE, 14, 20))
    settings_title_min_left = settings_back_rect.right + settings_title_gap
    settings_title_w = settings_title_font.size("Parent Settings")[0]
    if WIDTH // 2 - settings_title_w // 2 < settings_title_min_left:
        SETTINGS_TITLE_X = settings_title_min_left + settings_title_w // 2
    else:
        SETTINGS_TITLE_X = WIDTH // 2
    reset_button_rect = pygame.Rect(0, 0, 260, 56)
    reset_button_rect.center = (WIDTH // 2, HEIGHT - int(clamp(88 * SCALE, 70, 88)))
    confirm_yes_rect = pygame.Rect(0, 0, 160, 56)
    confirm_no_rect = pygame.Rect(0, 0, 160, 56)
    confirm_yes_rect.center = (WIDTH // 2 - 96, HEIGHT - int(clamp(88 * SCALE, 70, 88)))
    confirm_no_rect.center = (WIDTH // 2 + 96, HEIGHT - int(clamp(88 * SCALE, 70, 88)))

    # Settings screen: title/stats/games-played/badges are stacked from one
    # sequence (same fix pattern as the gate screen) instead of independent
    # fixed pixels / a HEIGHT fraction, so the badge grid can never overlap
    # the text above it on a short viewport, and the stats line wraps to two
    # rows on narrow widths instead of overflowing off both edges.
    SETTINGS_TITLE_Y = int(clamp(HEIGHT * 0.09, 45, 70))
    STATS_LINE_GAP = int(clamp(28 * SCALE, 22, 30))
    STATS_Y = SETTINGS_TITLE_Y + int(clamp(48 * SCALE, 38, 55))
    if IS_NARROW:
        STATS_Y2 = STATS_Y + STATS_LINE_GAP
        GAMES_Y = STATS_Y2 + STATS_LINE_GAP
    else:
        STATS_Y2 = None
        GAMES_Y = STATS_Y + STATS_LINE_GAP

    badges_per_row = 2 if IS_NARROW else 4
    badge_radius = int(clamp(45 * SCALE, 28, 45))
    badge_gap_x = int(clamp(40 * SCALE, 18, 40))
    badge_row_gap = int(clamp(66 * SCALE, 46, 66))
    badge_rows = [
        ACHIEVEMENTS[i:i + badges_per_row] for i in range(0, len(ACHIEVEMENTS), badges_per_row)
    ]
    badge_start_y = GAMES_Y + int(clamp(50 * SCALE, 40, 60)) + badge_radius
    badge_positions = []
    for row_index, row in enumerate(badge_rows):
        row_w = len(row) * badge_radius * 2 + (len(row) - 1) * badge_gap_x
        row_start_x = WIDTH // 2 - row_w // 2 + badge_radius
        row_y = badge_start_y + row_index * (badge_radius * 2 + badge_row_gap)
        for i, achievement in enumerate(row):
            cx = row_start_x + i * (badge_radius * 2 + badge_gap_x)
            badge_positions.append((achievement, (cx, row_y)))

    while running:
        mouse_pos = pygame.mouse.get_pos()
        # Grid-local mouse position for card hit-testing - the header/tab bar
        # are fixed on screen now, only the grid below GRID_TOP scrolls.
        mouse_grid_pos = (mouse_pos[0], mouse_pos[1] - GRID_TOP + scroll)
        ticks = pygame.time.get_ticks()
        tab_rects = category_tab_rects()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif state == STATE_MENU:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
                    scroll = min(scroll + SCROLL_SPEED, max_scroll)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
                    scroll = max(scroll - SCROLL_SPEED, 0)
                elif event.type == pygame.MOUSEWHEEL:
                    scroll = max(0, min(scroll - event.y * SCROLL_SPEED, max_scroll))
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if gear_rect.collidepoint(event.pos):
                        gate_question = make_gate_question()
                        gate_message = ""
                        state = STATE_GATE
                    elif nav_rect.collidepoint(event.pos):
                        go_to_arcade()
                    elif featured_rect.collidepoint(event.pos):
                        await press_feedback(featured_rect, featured_game["hover"])
                        record_game_launch(progress, featured_game["name"])
                        await launch_game(featured_game)
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
                        resize_window()
                        pygame.display.set_caption("Kid Zone")
                        load_images()
                    else:
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
                                    grid_bg = make_background(
                                        WIDTH, max(content_height(cards), HEIGHT - GRID_TOP),
                                        y_offset=GRID_TOP, total_height=HEIGHT,
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
                                press_rect = card.rect.move(0, GRID_TOP - scroll)
                                await press_feedback(press_rect, card.game["hover"])
                                record_game_launch(progress, card.game["name"])
                                await launch_game(card.game)
                                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
                                resize_window()
                                pygame.display.set_caption("Kid Zone")
                                load_images()
                                break
                    dragging = False

            elif state == STATE_GATE:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if gate_back_rect.collidepoint(event.pos):
                        state = STATE_MENU
                    else:
                        for i, rect in enumerate(gate_choice_rects):
                            if rect.collidepoint(event.pos):
                                if gate_question["choices"][i] == gate_question["answer"]:
                                    state = STATE_SETTINGS
                                    confirm_reset = False
                                else:
                                    gate_message = "Not quite - try again!"
                                    gate_message_until = ticks + 1500
                                    gate_question = make_gate_question()
                                break

            elif state == STATE_SETTINGS:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if settings_back_rect.collidepoint(event.pos):
                        state = STATE_MENU
                        confirm_reset = False
                    elif confirm_reset:
                        if confirm_yes_rect.collidepoint(event.pos):
                            progress = reset_progress()
                            confirm_reset = False
                        elif confirm_no_rect.collidepoint(event.pos):
                            confirm_reset = False
                    elif reset_button_rect.collidepoint(event.pos):
                        confirm_reset = True

        if state == STATE_MENU:
            screen.fill(BG_COLOR)
            screen.blit(header_bg, (0, 0))

            title_surf = title_font.render("Kid Zone", True, TITLE_COLOR)
            total_w = mascot_size + title_gap + title_surf.get_width()
            start_x = WIDTH // 2 - total_w // 2
            mascot_center = (start_x + mascot_size // 2, HEADER_Y)
            screen.blit(
                title_surf,
                title_surf.get_rect(midleft=(start_x + mascot_size + title_gap, HEADER_Y)),
            )
            draw_sunny(screen, mascot_center, mascot_size, ticks)

            subtitle_surf = subtitle_font.render(
                "Adventure Starts Here!", True, SUBTITLE_COLOR
            )
            screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, SUBTITLE_Y)))

            # Compact progress area - reuses the same progress fields the
            # achievements screen already tracks (games explored / total
            # achievements unlocked), no new backend state invented. On its
            # own row below the subtitle so the two can never collide.
            explored = len(progress["games_played"])
            earned = len(progress["achievements_unlocked"])
            trophy_rect = draw_stat_pill(
                screen, WIDTH - CARD_MARGIN, STATS_Y, earned, draw_glyph_trophy, SUN_DEEP_COLOR, stat_pill_font
            )
            star_rect = draw_stat_pill(
                screen, trophy_rect.left - 10, STATS_Y, explored, draw_glyph_star, TEAL_COLOR, stat_pill_font
            )

            # Streak pill lives on this same row (chained off the star pill),
            # not up on the HEADER_Y row - that row is already tight with the
            # nav icon/mascot/title/gear on narrow phones, and anchoring the
            # streak pill next to the gear there collided with the title text.
            draw_streak_pill(
                screen, star_rect.left - 10, STATS_Y, progress["streak_days"], ticks, stat_pill_font
            )

            gear_hovered = gear_rect.collidepoint(mouse_pos)
            draw_icon_button(screen, gear_rect.center, gear_radius, gear_hovered, draw_lock_icon)

            nav_hovered = nav_rect.collidepoint(mouse_pos)
            draw_icon_button(screen, nav_rect.center, gear_radius, nav_hovered, draw_arcade_icon)

            draw_category_tabs(screen, active_category, mouse_pos, tab_font)

            featured_hovered = featured_rect.collidepoint(mouse_pos)
            draw_featured_card(screen, featured_rect, featured_game, featured_fonts, featured_hovered)

            # ---- Scrollable card grid, clipped so it never draws over the header ----
            grid_h = max(content_height(cards), HEIGHT - GRID_TOP)
            grid_surface = grid_bg.copy()

            for card in cards:
                hovered = mouse_pos[1] >= GRID_TOP and card.is_hovered(mouse_grid_pos)
                color = card.game["hover"] if hovered else card.game["color"]

                if hovered:
                    rect = card.rect.inflate(16, 16)
                    rect.centery -= 4
                    draw_soft_shadow(grid_surface, rect, CARD_RADIUS, offset_y=16, pad=10, alpha=95)
                else:
                    rect = card.rect
                    draw_soft_shadow(grid_surface, rect, CARD_RADIUS, offset_y=8, pad=6, alpha=70)

                pygame.draw.rect(grid_surface, color, rect, border_radius=CARD_RADIUS)

                # Subtle glossy sheen across the top of the card so it reads
                # as a polished game tile rather than a flat color swatch.
                # Cached like draw_soft_shadow - every visible card shares one
                # of only two sizes (hovered/not), so there's no need to
                # rebuild this surface for every card on every frame.
                gloss_h = max(CARD_RADIUS, int(rect.height * 0.38))
                gloss_key = (rect.width, gloss_h)
                gloss_surf = _gloss_cache.get(gloss_key)
                if gloss_surf is None:
                    gloss_surf = pygame.Surface((rect.width, gloss_h), pygame.SRCALPHA)
                    pygame.draw.rect(
                        gloss_surf, (255, 255, 255, 30), gloss_surf.get_rect(),
                        border_top_left_radius=CARD_RADIUS, border_top_right_radius=CARD_RADIUS,
                    )
                    _gloss_cache[gloss_key] = gloss_surf
                grid_surface.blit(gloss_surf, rect.topleft)

                pygame.draw.rect(grid_surface, PAPER_COLOR, rect, width=3, border_radius=CARD_RADIUS)

                image = card.game["image_surface"]
                img_top = rect.top + int(clamp(18 * SCALE, 12, 18))
                grid_surface.blit(image, image.get_rect(midtop=(rect.centerx, img_top)))

                name_top = img_top + IMAGE_SIZE + int(clamp(12 * SCALE, 8, 12))
                name_surf = name_font.render(card.game["name"], True, (255, 255, 255))
                grid_surface.blit(
                    name_surf, name_surf.get_rect(midtop=(rect.centerx, name_top))
                )

                comment_top = name_top + name_surf.get_height() + int(clamp(8 * SCALE, 5, 8))
                line_step = comment_font.get_height() + 2
                lines = card.game["comment"].split("\n")
                for i, line in enumerate(lines):
                    line_surf = comment_font.render(line, True, (255, 255, 255))
                    grid_surface.blit(
                        line_surf,
                        line_surf.get_rect(
                            midtop=(rect.centerx, comment_top + i * line_step)
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

        elif state == STATE_GATE:
            screen.blit(settings_bg, (0, 0))

            title_surf = gate_title_font.render("Grown-ups Only", True, TITLE_COLOR)
            screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, GATE_TITLE_Y)))

            q_text = f"What is {gate_question['a']} + {gate_question['b']}?"
            q_surf = name_font.render(q_text, True, TEXT_COLOR)
            screen.blit(q_surf, q_surf.get_rect(center=(WIDTH // 2, GATE_Q_Y)))

            hint_surf = comment_font.render(
                "Answer the question to open parent settings.", True, SUBTITLE_COLOR
            )
            screen.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, GATE_HINT_Y)))

            for i, rect in enumerate(gate_choice_rects):
                hovered = rect.collidepoint(mouse_pos)
                draw_button(
                    screen, rect, str(gate_question["choices"][i]), button_font,
                    TEAL_COLOR, TEAL_DEEP_COLOR, hovered,
                )

            if gate_message and ticks < gate_message_until:
                msg_surf = comment_font.render(gate_message, True, CORAL_DEEP_COLOR)
                screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH // 2, GATE_MSG_Y)))

            back_hovered = gate_back_rect.collidepoint(mouse_pos)
            draw_button(
                screen, gate_back_rect, "Back to Kid Zone", button_font,
                INK_SOFT_COLOR, INK_COLOR, back_hovered,
            )

        elif state == STATE_SETTINGS:
            screen.blit(settings_bg, (0, 0))

            title_surf = settings_title_font.render("Parent Settings", True, TITLE_COLOR)
            screen.blit(title_surf, title_surf.get_rect(center=(SETTINGS_TITLE_X, SETTINGS_TITLE_Y)))

            streak_word = "day" if progress["streak_days"] == 1 else "days"
            longest_word = "day" if progress["longest_streak"] == 1 else "days"
            if IS_NARROW:
                # Two shorter lines instead of one long joined string, which
                # would otherwise overflow off both edges of a phone width.
                streak_surf = stat_font.render(
                    f"Current Streak: {progress['streak_days']} {streak_word}", True, TEXT_COLOR
                )
                screen.blit(streak_surf, streak_surf.get_rect(center=(WIDTH // 2, STATS_Y)))
                longest_surf = stat_font.render(
                    f"Longest Streak: {progress['longest_streak']} {longest_word}", True, TEXT_COLOR
                )
                screen.blit(longest_surf, longest_surf.get_rect(center=(WIDTH // 2, STATS_Y2)))
            else:
                stats_text = (
                    f"Current Streak: {progress['streak_days']} {streak_word}   |   "
                    f"Longest Streak: {progress['longest_streak']} {longest_word}"
                )
                stats_surf = stat_font.render(stats_text, True, TEXT_COLOR)
                screen.blit(stats_surf, stats_surf.get_rect(center=(WIDTH // 2, STATS_Y)))

            games_text = (
                f"Games played: {len(progress['games_played'])}/{len(GAMES)}   |   "
                f"Total launches: {progress['total_launches']}"
            )
            games_surf = comment_font.render(games_text, True, SUBTITLE_COLOR)
            screen.blit(games_surf, games_surf.get_rect(center=(WIDTH // 2, GAMES_Y)))

            for achievement, center in badge_positions:
                unlocked = achievement["id"] in progress["achievements_unlocked"]
                draw_badge(screen, center, badge_radius, achievement, unlocked)
                label_color = TEXT_COLOR if unlocked else INK_SOFT_COLOR
                label_surf = badge_label_font.render(achievement["name"], True, label_color)
                screen.blit(
                    label_surf,
                    label_surf.get_rect(midtop=(center[0], center[1] + badge_radius + 8)),
                )

            if confirm_reset:
                confirm_surf = comment_font.render(
                    "Erase all progress and streaks?", True, CORAL_DEEP_COLOR
                )
                confirm_msg_y = confirm_yes_rect.top - int(clamp(30 * SCALE, 24, 34))
                screen.blit(confirm_surf, confirm_surf.get_rect(center=(WIDTH // 2, confirm_msg_y)))
                yes_hovered = confirm_yes_rect.collidepoint(mouse_pos)
                no_hovered = confirm_no_rect.collidepoint(mouse_pos)
                draw_button(
                    screen, confirm_yes_rect, "Yes, Reset", button_font,
                    CORAL_COLOR, CORAL_DEEP_COLOR, yes_hovered,
                )
                draw_button(
                    screen, confirm_no_rect, "Cancel", button_font,
                    INK_SOFT_COLOR, INK_COLOR, no_hovered,
                )
            else:
                reset_hovered = reset_button_rect.collidepoint(mouse_pos)
                draw_button(
                    screen, reset_button_rect, "Reset Progress", button_font,
                    CORAL_COLOR, CORAL_DEEP_COLOR, reset_hovered,
                )

            back_hovered = settings_back_rect.collidepoint(mouse_pos)
            draw_button(
                screen, settings_back_rect, "< Back", button_font,
                TEAL_COLOR, TEAL_DEEP_COLOR, back_hovered,
            )

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
