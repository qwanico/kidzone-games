import asyncio
import pygame
import random
import time
import math
import os
import json
from pathlib import Path

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    import platform
except ImportError:
    platform = None

pygame.init()

BASE_DIR = Path(__file__).parent / "fruit_finder_assets"

# ---------------- WINDOW ----------------

WIDTH = 1520
HEIGHT = 980

# The actual display window is (re)created each time run() starts, since
# the shared Kid Zone hub reclaims the display for its own menu between
# games. `screen` just needs a placeholder value at import time so the
# module-level drawing helpers below have something to reference.
screen = pygame.display.get_surface()


# ---------------- COLORS ----------------

SKY = (135, 206, 235)
SKY_TOP = (180, 228, 250)
SKY_BOTTOM = (115, 190, 232)
GRASS = (80, 190, 80)
GRASS_SHADOW = (60, 160, 60)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (70, 220, 70)
YELLOW = (255, 220, 80)
SUN_GLOW_OUTER = (255, 244, 190)
SUN_GLOW_INNER = (255, 232, 150)
FLOWER_YELLOW = (255, 225, 90)
GREY = (150, 150, 150)
RED = (210, 80, 80)
OVERLAY_BLACK = (0, 0, 0)
HILL_FAR = (152, 208, 132)
HILL_NEAR = (112, 188, 98)
FENCE_WOOD = (177, 137, 96)
FENCE_WOOD_DARK = (138, 100, 66)
BUSH_GREEN = (66, 150, 70)
BUSH_GREEN_DARK = (48, 128, 54)
GRASS_BLADE_LIGHT = (102, 206, 96)
GRASS_BLADE_DARK = (63, 168, 64)
MILESTONE_GOLD = (235, 150, 30)



# ---------------- BACKGROUND SURFACE (a few scenes, built once) ----------------

GRASS_TOP = 860


# Different times-of-day for the scene. "day" keeps the original colors;
# the others just swap the palette fed into the same drawing routine below.
BACKGROUND_PALETTES = {
    "day": dict(
        sky_top=(180, 228, 250), sky_bottom=(115, 190, 232),
        sun_glow_outer=(255, 244, 190), sun_glow_inner=(255, 232, 150), sun=(255, 220, 80),
        hill_far=(152, 208, 132), hill_near=(112, 188, 98),
        grass=(80, 190, 80), grass_shadow=(60, 160, 60),
        grass_blade_light=(102, 206, 96), grass_blade_dark=(63, 168, 64),
        fence_wood=(177, 137, 96), fence_wood_dark=(138, 100, 66),
        bush_green=(66, 150, 70), bush_green_dark=(48, 128, 54),
        flower_center=(255, 225, 90),
    ),
    "sunset": dict(
        sky_top=(255, 183, 140), sky_bottom=(255, 140, 120),
        sun_glow_outer=(255, 225, 170), sun_glow_inner=(255, 190, 120), sun=(255, 170, 80),
        hill_far=(178, 150, 140), hill_near=(140, 110, 110),
        grass=(150, 170, 80), grass_shadow=(120, 140, 60),
        grass_blade_light=(170, 190, 100), grass_blade_dark=(130, 150, 70),
        fence_wood=(177, 137, 96), fence_wood_dark=(138, 100, 66),
        bush_green=(110, 140, 70), bush_green_dark=(80, 110, 55),
        flower_center=(255, 200, 90),
    ),
    "dusk": dict(
        sky_top=(120, 120, 190), sky_bottom=(70, 80, 150),
        sun_glow_outer=(220, 210, 255), sun_glow_inner=(190, 180, 240), sun=(230, 220, 255),
        hill_far=(90, 110, 120), hill_near=(60, 80, 95),
        grass=(60, 120, 90), grass_shadow=(45, 95, 72),
        grass_blade_light=(80, 140, 105), grass_blade_dark=(50, 105, 80),
        fence_wood=(120, 95, 80), fence_wood_dark=(90, 70, 60),
        bush_green=(55, 110, 80), bush_green_dark=(40, 85, 62),
        flower_center=(230, 220, 150),
    ),
}


def build_background_surface(palette):

    surface = pygame.Surface((WIDTH, HEIGHT))

    texture_rng = random.Random(12345)


    # Sky gradient

    for y in range(GRASS_TOP):

        t = y / GRASS_TOP

        sky_top = palette["sky_top"]
        sky_bottom = palette["sky_bottom"]

        r = int(sky_top[0] + (sky_bottom[0] - sky_top[0]) * t)
        g = int(sky_top[1] + (sky_bottom[1] - sky_top[1]) * t)
        b = int(sky_top[2] + (sky_bottom[2] - sky_top[2]) * t)

        pygame.draw.line(
            surface,
            (r, g, b),
            (0, y),
            (WIDTH, y)
        )


    # Sun with soft rays and glow

    sun_x, sun_y = 1400, 90

    for i in range(12):

        angle = (math.pi * 2 / 12) * i

        inner = 68
        outer = 118

        pygame.draw.line(
            surface,
            palette["sun_glow_outer"],
            (sun_x + math.cos(angle) * inner, sun_y + math.sin(angle) * inner),
            (sun_x + math.cos(angle) * outer, sun_y + math.sin(angle) * outer),
            4
        )

    pygame.draw.circle(surface, palette["sun_glow_outer"], (sun_x, sun_y), 90)
    pygame.draw.circle(surface, palette["sun_glow_inner"], (sun_x, sun_y), 75)
    pygame.draw.circle(surface, palette["sun"], (sun_x, sun_y), 60)


    # Rolling hills (silhouettes peeking above the grass line)

    hills = [
        (-200, GRASS_TOP-170, 900, 260, palette["hill_far"]),
        (520, GRASS_TOP-140, 820, 220, palette["hill_far"]),
        (-120, GRASS_TOP-110, 720, 200, palette["hill_near"]),
        (680, GRASS_TOP-125, 900, 220, palette["hill_near"]),
        (1320, GRASS_TOP-95, 620, 180, palette["hill_near"]),
    ]

    for x,y,w,h,color in hills:

        pygame.draw.ellipse(surface, color, (x,y,w,h))


    # Grass base

    pygame.draw.rect(
        surface,
        palette["grass_shadow"],
        (0,GRASS_TOP,WIDTH,12)
    )

    pygame.draw.rect(
        surface,
        palette["grass"],
        (0,GRASS_TOP+12,WIDTH,HEIGHT-GRASS_TOP-12)
    )


    # Grass blade texture

    for _ in range(900):

        bx = texture_rng.randint(0, WIDTH)
        by = texture_rng.randint(GRASS_TOP+16, HEIGHT-6)
        blade_h = texture_rng.randint(5, 11)
        color = texture_rng.choice((palette["grass_blade_light"], palette["grass_blade_dark"]))

        pygame.draw.line(
            surface,
            color,
            (bx, by),
            (bx + texture_rng.randint(-3,3), by - blade_h),
            2
        )


    # Garden fence along the grass line

    pygame.draw.rect(
        surface,
        palette["fence_wood"],
        (0, GRASS_TOP-16, WIDTH, 9)
    )

    for post_x in range(30, WIDTH, 150):

        post_rect = (post_x, GRASS_TOP-34, 12, 52)

        pygame.draw.rect(surface, palette["fence_wood"], post_rect, border_radius=3)
        pygame.draw.rect(surface, palette["fence_wood_dark"], post_rect, 2, border_radius=3)


    # Bushes framing the corners

    def draw_bush(cx, cy):

        for dx,dy,r,color in (
            (-24,4,22,palette["bush_green_dark"]),
            (24,4,22,palette["bush_green_dark"]),
            (0,-10,28,palette["bush_green"]),
            (-14,-4,20,palette["bush_green"]),
            (14,-4,20,palette["bush_green"]),
        ):
            pygame.draw.circle(surface, color, (cx+dx, cy+dy), r)

    draw_bush(55, GRASS_TOP+16)
    draw_bush(WIDTH-55, GRASS_TOP+16)


    # Flowers

    flowers = [
        180, 400, 830, 1140, 1360
    ]

    for x in flowers:

        y = GRASS_TOP+42

        pygame.draw.circle(surface, WHITE, (x,y), 7)
        pygame.draw.circle(surface, WHITE, (x-9,y+4), 7)
        pygame.draw.circle(surface, WHITE, (x+9,y+4), 7)
        pygame.draw.circle(surface, palette["flower_center"], (x,y+3), 5)


    return surface


BACKGROUND_SCENES = [
    build_background_surface(palette)
    for palette in BACKGROUND_PALETTES.values()
]

background_surface = random.choice(BACKGROUND_SCENES)



# ---------------- VOICE ----------------

VOICE_CACHE_DIR = str(BASE_DIR / "voice_cache")

os.makedirs(
    VOICE_CACHE_DIR,
    exist_ok=True
)


muted = False


def voice_path(fruit):
    return os.path.join(
        VOICE_CACHE_DIR,
        f"{fruit}.ogg"
    )


# Loaded voice clips are cached here so each line is decoded once and then
# just replayed - repeatedly streaming a fresh file through
# pygame.mixer.music (as this used to do, once per round and once per
# streak callout) gets choppier the longer a session runs, since it's
# meant for long continuous tracks, not being reloaded constantly.
voice_sound_cache = {}


def get_voice_sound(path):

    if path not in voice_sound_cache:
        voice_sound_cache[path] = pygame.mixer.Sound(path)

    return voice_sound_cache[path]


def speak_fruit(fruit):

    if muted:
        return 0

    path = voice_path(fruit)

    if not os.path.exists(path):

        try:
            gTTS(f"Find the {display_name(fruit)}").save(path)

        except Exception as e:
            print(f"Could not generate voice line for {fruit}: {e}")
            return 0

    try:
        sound = get_voice_sound(path)
        voice_channel.play(sound)
        return sound.get_length()

    except Exception as e:
        print(f"Could not play voice line for {fruit}: {e}")
        return 0


# ---------------- STREAK CALLOUTS ----------------

CALLOUT_DIR = os.path.join(VOICE_CACHE_DIR, "callouts")

CALLOUT_PHRASES = {
    "great_job": "Great job!",
    "awesome": "Awesome!",
    "fantastic": "Fantastic!",
    "on_a_roll": "You're on a roll!",
    "amazing_streak": "Amazing streak!",
    "way_to_go": "Way to go!",
}


def speak_callout():

    if muted:
        return

    key = random.choice(list(CALLOUT_PHRASES))

    path = os.path.join(CALLOUT_DIR, f"{key}.ogg")

    if not os.path.exists(path):

        try:
            os.makedirs(CALLOUT_DIR, exist_ok=True)
            gTTS(CALLOUT_PHRASES[key]).save(path)

        except Exception as e:
            print(f"Could not generate callout line for {key}: {e}")
            return

    try:
        voice_channel.play(get_voice_sound(path))

    except Exception as e:
        print(f"Could not play callout line for {key}: {e}")



# ---------------- FONTS ----------------

title_font = pygame.font.Font(
    None,
    65
)

score_font = pygame.font.Font(
    None,
    45
)

menu_title_font = pygame.font.Font(
    None,
    100
)

button_font = pygame.font.Font(
    None,
    55
)

milestone_font = pygame.font.Font(
    None,
    70
)



# ---------------- SOUND EFFECTS ----------------

pygame.mixer.init()

# Reserve channel 0 exclusively for spoken voice lines so background music
# and sound effects (auto-assigned to whatever channel is free) can never
# get placed on it and fight the voice for playback.
pygame.mixer.set_reserved(1)
voice_channel = pygame.mixer.Channel(0)

SOUNDS_DIR = BASE_DIR / "sounds"

wrong_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.ogg"))

# A few different correct-answer sounds, picked at random each time so it
# doesn't get repetitive. Volume is applied below via apply_volumes() -
# kept low by default so they don't drown out the "Find the X" voice line
# that speaks over them once the next round starts (the applause clip
# especially, since it runs long at 4.5s).
correct_sounds = [
    pygame.mixer.Sound(str(SOUNDS_DIR / "correct.ogg")),
    pygame.mixer.Sound(str(SOUNDS_DIR / "chime1.ogg")),
    pygame.mixer.Sound(str(SOUNDS_DIR / "chime2.ogg")),
]


def play_wrong_sound():
    if not muted:
        wrong_sound.play()


def play_correct_sound():
    if not muted:
        random.choice(correct_sounds).play()



# ---------------- BACKGROUND MUSIC ----------------
# Uses a dedicated Sound/Channel (not pygame.mixer.music, which is
# already streaming the "Find the X" voice lines) so the loop keeps
# playing underneath the spoken prompts instead of being interrupted.

background_music = pygame.mixer.Sound(str(SOUNDS_DIR / "background_music.ogg"))

# Deliberately NOT started here. Starting the loop at module-import time
# left an orphaned channel looping forever: run() starts its own channel
# and only that one gets stopped on exit, so the import-time channel kept
# playing underneath (two overlapping copies in-game, and music still
# looping back on the hub after quitting). run() owns this channel now.
music_channel = None



# ---------------- VOLUME CONTROLS ----------------
# Separate levels for the three sound sources, adjustable from Settings.
# The mute button (top corner, in-game) stays as an instant all-off on
# top of whatever these are set to.

VOLUME_STEP = 0.1

music_volume = 0.35
voice_volume = 1.0
effects_volume = 0.35

# The background music channel plays continuously, so jumping its volume
# straight to the target on every settings click produces an audible pop.
# music_volume_current chases music_volume smoothly instead (see
# update_music_fade below); everything else is short one-shot sounds where
# an instant change isn't noticeable the same way.
music_volume_current = music_volume

MUSIC_FADE_RATE = 2.5


def apply_volumes():

    voice_channel.set_volume(voice_volume)

    wrong_sound.set_volume(effects_volume)

    for s in correct_sounds:
        s.set_volume(effects_volume)


def update_music_fade(dt):

    global music_volume_current

    target = 0 if muted else music_volume

    if music_volume_current == target:
        # Already there - skip re-setting the channel volume every single
        # frame. Calling set_volume() 60 times a second even with an
        # unchanged value is what was making the background music choppy.
        return

    if music_volume_current < target:
        music_volume_current = min(target, music_volume_current + MUSIC_FADE_RATE * dt)

    elif music_volume_current > target:
        music_volume_current = max(target, music_volume_current - MUSIC_FADE_RATE * dt)

    if music_channel is not None:
        music_channel.set_volume(music_volume_current)


apply_volumes()



# ---------------- PROGRESS (high scores, lifetime stats) ----------------

PROGRESS_FILE = str(BASE_DIR / "progress.json")


def load_progress():

    default = {
        "high_scores": {},
        "total_correct": 0,
        "best_streak_ever": 0,
        "items_found": []
    }

    try:
        with open(PROGRESS_FILE) as f:
            loaded = json.load(f)
            default.update(loaded)
            return default

    except (FileNotFoundError, ValueError):
        return default


def save_progress():

    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)


def get_high_score(for_mode, for_category):
    return progress["high_scores"].get(for_mode, {}).get(for_category, 0)


progress = load_progress()



# ---------------- FRUITS ----------------

FRUIT_NAMES = [
    "apple",
    "green_apple",
    "avocado",
    "banana",
    "blueberry",
    "cherry",
    "coconut",
    "grapes",
    "kiwi",
    "lemon",
    "lime",
    "mango",
    "melon",
    "orange",
    "peach",
    "pear",
    "pineapple",
    "strawberry",
    "tomato",
    "watermelon"
]

VEGETABLE_NAMES = [
    "beans",
    "bell_pepper",
    "broccoli",
    "carrot",
    "chestnut",
    "corn",
    "cucumber",
    "eggplant",
    "garlic",
    "hot_pepper",
    "leafy_green",
    "mushroom",
    "olive",
    "onion",
    "peanuts",
    "peas",
    "ginger",
    "potato",
    "pumpkin",
    "salad"
]

OTHER_FOOD_NAMES = [
    "bread",
    "croissant",
    "pretzel",
    "bagel",
    "pancakes",
    "waffle",
    "egg",
    "cheese",
    "hamburger",
    "hot_dog",
    "pizza",
    "fries",
    "taco",
    "burrito",
    "sandwich",
    "popcorn",
    "sushi",
    "dumpling",
    "spaghetti",
    "ramen",
    "rice_ball",
    "bacon",
    "drumstick",
    "donut",
    "cookie",
    "cupcake",
    "cake",
    "pie",
    "chocolate",
    "lollipop"
]

fruits = FRUIT_NAMES + VEGETABLE_NAMES + OTHER_FOOD_NAMES


def display_name(fruit):
    return fruit.replace("_", " ")


CATEGORIES = ["mixed", "fruits", "vegetables", "other"]
CATEGORY_LABELS = {
    "mixed": "Mixed",
    "fruits": "Fruits only",
    "vegetables": "Vegetables only",
    "other": "Other Foods"
}

category = "mixed"


def current_pool():

    if category == "fruits":
        return FRUIT_NAMES

    if category == "vegetables":
        return VEGETABLE_NAMES

    if category == "other":
        return OTHER_FOOD_NAMES

    return fruits


def max_count_for_category():
    return min(len(current_pool()), NUM_GRID_SPOTS)


MODES = ["endless", "timed"]
MODE_LABELS = {
    "endless": "Endless",
    "timed": "Timed (60s)"
}

TIMED_MODE_SECONDS = 60

mode = "endless"


ACHIEVEMENTS = [
    {
        "name": "First Find",
        "desc": "Find your first item",
        "check": lambda p: p["total_correct"] >= 1
    },
    {
        "name": "Getting the Hang of It",
        "desc": "Find 10 items total",
        "check": lambda p: p["total_correct"] >= 10
    },
    {
        "name": "Fruit & Veggie Pro",
        "desc": "Find 50 items total",
        "check": lambda p: p["total_correct"] >= 50
    },
    {
        "name": "Century Club",
        "desc": "Find 100 items total",
        "check": lambda p: p["total_correct"] >= 100
    },
    {
        "name": "On a Roll",
        "desc": "Reach a 5-in-a-row streak",
        "check": lambda p: p["best_streak_ever"] >= 5
    },
    {
        "name": "Unstoppable",
        "desc": "Reach a 10-in-a-row streak",
        "check": lambda p: p["best_streak_ever"] >= 10
    },
    {
        "name": "Quick Picker",
        "desc": "Score 15+ in a 60s Timed (Mixed) run",
        "check": lambda p: p["high_scores"].get("timed", {}).get("mixed", 0) >= 15
    },
    {
        "name": "Curious Cook",
        "desc": "Find 10 different items",
        "check": lambda p: len(set(p.get("items_found", []))) >= 10
    },
    {
        "name": "Foodie",
        "desc": "Find 25 different items",
        "check": lambda p: len(set(p.get("items_found", []))) >= 25
    },
    {
        "name": "Gourmet",
        "desc": "Find 50 different items",
        "check": lambda p: len(set(p.get("items_found", []))) >= 50
    },
    {
        "name": "New Flavors",
        "desc": "Find something from Other Foods",
        "check": lambda p: bool(set(p.get("items_found", [])) & set(OTHER_FOOD_NAMES))
    },
    {
        "name": "Pantry Master",
        "desc": "Find every item at least once",
        "check": lambda p: len(set(p.get("items_found", []))) >= len(fruits)
    },
]


# ---------------- LOAD IMAGES ----------------

images = {}

for fruit in fruits:

    img = pygame.image.load(
        str(BASE_DIR / "assets" / f"{fruit}.png")
    )

    img = pygame.transform.scale(
        img,
        (110,110)
    )

    images[fruit] = img



# ---------------- GRID POSITIONS ----------------

def create_positions(active_fruits):

    spots = []

    columns = [
        60,
        318,
        576,
        834,
        1092,
        1350
    ]

    rows = [
        160,
        307,
        455,
        602,
        750
    ]


    for y in rows:
        for x in columns:
            spots.append(
                (x,y)
            )


    random.shuffle(spots)


    return dict(
        zip(
            active_fruits,
            spots
        )
    )


# ---------------- DIFFICULTY / SCORE ----------------

NUM_GRID_SPOTS = 30

STARTING_FRUIT_COUNT = 5
MIN_STARTING_FRUIT_COUNT = 2

active_count = STARTING_FRUIT_COUNT
score = 0
streak = 0

active_fruits = random.sample(current_pool(), active_count)
positions = create_positions(active_fruits)


target = random.choice(active_fruits)



# ---------------- ANIMATION ----------------

fruit_scale = {}

for fruit in fruits:
    fruit_scale[fruit] = 0.1


BOB_AMPLITUDE = 4
BOB_SPEED = 2.2

bob_phase = {}

for fruit in fruits:
    bob_phase[fruit] = random.Random(fruit).uniform(0, 2 * math.pi)


shake_fruit = None
correct_fruit = None
shake_start_time = 0.0

WRONG_FLASH_DURATION = 0.6


def draw_check_badge(cx, cy):

    r = 24

    pygame.draw.circle(screen, GREEN, (cx, cy), r)
    pygame.draw.circle(screen, WHITE, (cx, cy), r, 3)

    pygame.draw.lines(
        screen,
        WHITE,
        False,
        [(cx - 11, cy), (cx - 3, cy + 9), (cx + 13, cy - 11)],
        5
    )


def draw_x_badge(cx, cy, alpha):

    r = 24

    badge = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)

    pygame.draw.circle(badge, (*RED, alpha), (r, r), r)
    pygame.draw.circle(badge, (255, 255, 255, alpha), (r, r), r, 3)

    pygame.draw.line(badge, (255, 255, 255, alpha), (r - 10, r - 10), (r + 10, r + 10), 5)
    pygame.draw.line(badge, (255, 255, 255, alpha), (r - 10, r + 10), (r + 10, r - 10), 5)

    screen.blit(badge, (cx - r, cy - r))


# ---------------- BACKGROUND ----------------

CLOUD_DEFS = [
    (180, 100, 1.0, 7),
    (600, 80, 1.15, 11),
    (1010, 120, 0.9, 5),
]


def draw_clouds():

    now = time.time()

    for base_x, y, scale, speed in CLOUD_DEFS:

        x = (base_x + now * speed) % (WIDTH + 400) - 200

        puffs = [
            (-40,6,32),
            (0,-10,42),
            (42,4,34),
            (78,10,26)
        ]

        for dx,dy,r in puffs:

            pygame.draw.circle(
                screen,
                WHITE,
                (int(x + dx*scale), int(y + dy*scale)),
                int(r*scale)
            )


def draw_background():

    screen.blit(background_surface, (0,0))
    draw_clouds()



# ---------------- DRAW SCREEN ----------------

def draw_game():

    draw_background()


    title = title_font.render(
        f"Find the {display_name(target)}!",
        True,
        BLACK
    )

    title_rect = title.get_rect(
        center=(WIDTH//2, 60)
    )

    screen.blit(title, title_rect)


    score_text = score_font.render(
        f"Score: {score}",
        True,
        BLACK
    )

    screen.blit(
        score_text,
        (20,20)
    )


    next_x = 20 + score_text.get_width() + 30

    if streak >= 2:

        streak_text = score_font.render(
            f"Streak: {streak}",
            True,
            BLACK
        )

        screen.blit(streak_text, (next_x, 20))

        next_x += streak_text.get_width() + 30


    if mode == "timed" and timer_remaining is not None:

        timer_color = RED if timer_remaining <= 10 else BLACK

        timer_text = score_font.render(
            f"Time: {int(math.ceil(timer_remaining))}s",
            True,
            timer_color
        )

        screen.blit(timer_text, (next_x, 20))



def draw_milestone(text):

    banner = milestone_font.render(text, True, MILESTONE_GOLD)

    banner_rect = banner.get_rect(center=(WIDTH//2, 130))

    bg_rect = banner_rect.inflate(50, 26)

    pygame.draw.rect(screen, WHITE, bg_rect, border_radius=18)
    pygame.draw.rect(screen, MILESTONE_GOLD, bg_rect, 4, border_radius=18)

    screen.blit(banner, banner_rect)



# ---------------- DRAW FRUITS ----------------

def draw_fruits():

    global shake_fruit
    global correct_fruit


    for fruit in positions:


        x,y = positions[fruit]


        scale = fruit_scale[fruit]


        size = int(
            110 * scale
        )


        if size < 1:
            size = 1


        img = pygame.transform.scale(
            images[fruit],
            (size,size)
        )


        draw_x = x + (110-size)//2
        draw_y = y + (110-size)//2


        # idle bob (skip while still growing in during the reveal animation)

        if scale >= 1:

            draw_y += int(
                math.sin(time.time()*BOB_SPEED + bob_phase[fruit]) * BOB_AMPLITUDE
            )



        # shake wrong fruit (brief - fades out rather than shaking forever)

        wrong_elapsed = time.time() - shake_start_time

        if fruit == shake_fruit and wrong_elapsed < WRONG_FLASH_DURATION:

            draw_x += random.randint(
                -8,
                8
            )



        screen.blit(
            img,
            (draw_x,draw_y)
        )



        # correct circle + green check badge

        if fruit == correct_fruit:

            pygame.draw.circle(
                screen,
                GREEN,
                (x+55,y+55),
                65,
                6
            )

            draw_check_badge(x + 95, y + 15)


        # friendly red X badge, fading out over WRONG_FLASH_DURATION

        if fruit == shake_fruit and wrong_elapsed < WRONG_FLASH_DURATION:

            alpha = max(0, int(255 * (1 - wrong_elapsed / WRONG_FLASH_DURATION)))

            draw_x_badge(x + 95, y + 15, alpha)



# ---------------- CONFETTI ----------------

CONFETTI_COLORS = [
    (255, 99, 99),
    (255, 189, 74),
    (255, 232, 92),
    (110, 220, 110),
    (94, 189, 255),
    (186, 120, 255),
    (255, 130, 200),
]

GRAVITY = 480

particles = []


def spawn_confetti(cx, cy, streak):

    # More pieces the longer the streak, capped so it doesn't get silly.
    count = 16 + min(streak, 12) * 2

    for _ in range(count):

        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(120, 340)

        particles.append({
            "x": cx,
            "y": cy,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed - random.uniform(90, 200),
            "color": random.choice(CONFETTI_COLORS),
            "size": random.randint(4, 9),
            "spin": random.uniform(-360, 360),
            "angle": random.uniform(0, 360),
            "age": 0.0,
            "life": random.uniform(0.7, 1.2),
        })


def update_particles(dt):

    global particles

    for p in particles:

        p["age"] += dt
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        p["vy"] += GRAVITY * dt
        p["angle"] += p["spin"] * dt

    particles = [p for p in particles if p["age"] < p["life"]]


def draw_particles():

    for p in particles:

        t = p["age"] / p["life"]
        alpha = max(0, int(255 * (1 - t)))

        size = p["size"] * 2

        piece = pygame.Surface((size, size), pygame.SRCALPHA)

        pygame.draw.rect(
            piece,
            (*p["color"], alpha),
            (0, 0, size, size),
            border_radius=2
        )

        rotated = pygame.transform.rotate(piece, p["angle"])

        rect = rotated.get_rect(center=(p["x"], p["y"]))

        screen.blit(rotated, rect)



# ---------------- NEW ROUND ----------------

async def new_round():

    global positions
    global target
    global fruit_scale
    global shake_fruit
    global correct_fruit
    global active_fruits


    active_fruits = random.sample(
        current_pool(),
        active_count
    )


    target = random.choice(
        active_fruits
    )


    positions = create_positions(active_fruits)



    for fruit in active_fruits:

        fruit_scale[fruit] = 0.1



    shake_fruit = None
    correct_fruit = None



    # Animate fruits appearing

    while any(
        fruit_scale[f] < 1
        for f in active_fruits
    ):


        draw_game()

        draw_fruits()

        update_particles(.03)
        draw_particles()


        pygame.display.update()



        for fruit in active_fruits:

            if fruit_scale[fruit] < 1:

                fruit_scale[fruit] += .12



        await asyncio.sleep(.03)



    # pause after animation

    await asyncio.sleep(1)


    duration = speak_fruit(target)

    # Hold the round here for (at least) the length of the voice line so a
    # fast correct answer can't immediately start the next round and cut
    # her off mid-word.
    await asyncio.sleep(max(1.0, min(duration, 2.5)))


async def animate_correct(fruit, milestone_text):

    duration = 0.8
    start_time = time.time()

    while True:

        elapsed = time.time() - start_time

        if elapsed >= duration:
            break

        progress = elapsed / duration

        fruit_scale[fruit] = 1.0 + 0.35 * math.sin(progress * math.pi)

        draw_game()
        draw_fruits()

        update_particles(0.016)
        draw_particles()

        draw_pause_button()
        draw_mute_button()

        if milestone_text:
            draw_milestone(milestone_text)

        pygame.display.update()

        await asyncio.sleep(0.016)

    fruit_scale[fruit] = 1.0


async def start_game():

    global score
    global streak
    global active_count
    global game_state
    global timer_remaining
    global new_best_this_run
    global background_surface

    score = 0
    streak = 0
    active_count = min(STARTING_FRUIT_COUNT, max_count_for_category())
    timer_remaining = TIMED_MODE_SECONDS if mode == "timed" else None
    new_best_this_run = False

    background_surface = random.choice(BACKGROUND_SCENES)

    game_state = "playing"

    await new_round()


timer_remaining = None
new_best_this_run = False



# ---------------- SMALL FONT (for compact buttons) ----------------

small_font = pygame.font.Font(
    None,
    32
)



# ---------------- START MENU ----------------

start_button = pygame.Rect(
    WIDTH//2 - 140,
    450,
    280,
    85
)

settings_button = pygame.Rect(
    WIDTH//2 - 140,
    545,
    280,
    62
)

achievements_button = pygame.Rect(
    WIDTH//2 - 140,
    617,
    280,
    62
)

quit_button = pygame.Rect(
    WIDTH//2 - 140,
    689,
    280,
    62
)


def draw_menu():

    draw_background()


    title = menu_title_font.render(
        "Find The Food",
        True,
        BLACK
    )

    title_rect = title.get_rect(
        center=(WIDTH//2, 220)
    )

    screen.blit(title, title_rect)


    info_text = score_font.render(
        f"Mode: {MODE_LABELS[mode]}   •   Category: {CATEGORY_LABELS[category]}",
        True,
        BLACK
    )

    info_rect = info_text.get_rect(
        center=(WIDTH//2, 300)
    )

    screen.blit(info_text, info_rect)


    best_text = score_font.render(
        f"Best: {get_high_score(mode, category)}",
        True,
        BLACK
    )

    best_rect = best_text.get_rect(
        center=(WIDTH//2, 343)
    )

    screen.blit(best_text, best_rect)


    draw_menu_button(start_button, "Start", GREEN)
    draw_menu_button(settings_button, "Settings", GREY)
    draw_menu_button(achievements_button, "Achievements", GREY)
    draw_menu_button(quit_button, "Quit", RED)


def draw_menu_button(rect, label, color):

    pygame.draw.rect(
        screen,
        color,
        rect,
        border_radius=20
    )

    pygame.draw.rect(
        screen,
        BLACK,
        rect,
        4,
        border_radius=20
    )

    text = button_font.render(
        label,
        True,
        WHITE
    )

    text_rect = text.get_rect(
        center=rect.center
    )

    screen.blit(text, text_rect)



# ---------------- MUTE BUTTON ----------------

mute_button = pygame.Rect(
    WIDTH - 170,
    20,
    150,
    50
)


def draw_mute_button():

    color = RED if muted else GREEN
    label = "Sound: Off" if muted else "Sound: On"

    pygame.draw.rect(
        screen,
        color,
        mute_button,
        border_radius=14
    )

    pygame.draw.rect(
        screen,
        BLACK,
        mute_button,
        3,
        border_radius=14
    )

    text = small_font.render(
        label,
        True,
        WHITE
    )

    text_rect = text.get_rect(
        center=mute_button.center
    )

    screen.blit(text, text_rect)



# ---------------- HOME BUTTON ----------------

home_button = pygame.Rect(
    20,
    20,
    60,
    50
)


def draw_home_button():

    pygame.draw.rect(
        screen,
        (70, 130, 220),
        home_button,
        border_radius=10
    )

    pygame.draw.rect(
        screen,
        BLACK,
        home_button,
        2,
        border_radius=10
    )

    cx, cy = home_button.center

    pygame.draw.polygon(
        screen,
        WHITE,
        [
            (cx - 12, cy),
            (cx, cy - 12),
            (cx + 12, cy),
        ]
    )

    pygame.draw.rect(
        screen,
        WHITE,
        (cx - 8, cy, 16, 12)
    )



# ---------------- PAUSE BUTTON (during play) ----------------

pause_button = pygame.Rect(
    20,
    75,
    150,
    45
)


def draw_pause_button():

    pygame.draw.rect(
        screen,
        GREY,
        pause_button,
        border_radius=12
    )

    pygame.draw.rect(
        screen,
        BLACK,
        pause_button,
        3,
        border_radius=12
    )

    text = small_font.render(
        "Pause",
        True,
        WHITE
    )

    text_rect = text.get_rect(
        center=pause_button.center
    )

    screen.blit(text, text_rect)



# ---------------- PAUSE OVERLAY ----------------

resume_button = pygame.Rect(
    WIDTH//2 - 140,
    420,
    280,
    80
)

quit_to_menu_button = pygame.Rect(
    WIDTH//2 - 140,
    520,
    280,
    80
)


def draw_pause_overlay():

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(160)
    overlay.fill(OVERLAY_BLACK)

    screen.blit(overlay, (0, 0))


    title = menu_title_font.render(
        "Paused",
        True,
        WHITE
    )

    title_rect = title.get_rect(
        center=(WIDTH//2, 300)
    )

    screen.blit(title, title_rect)


    draw_menu_button(resume_button, "Resume", GREEN)
    draw_menu_button(quit_to_menu_button, "Quit to Menu", RED)



# ---------------- GAME OVER (Timed mode) ----------------

play_again_button = pygame.Rect(
    WIDTH//2 - 140,
    460,
    280,
    80
)

game_over_menu_button = pygame.Rect(
    WIDTH//2 - 140,
    560,
    280,
    80
)


def draw_game_over():

    draw_background()

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(160)
    overlay.fill(OVERLAY_BLACK)

    screen.blit(overlay, (0, 0))


    title = menu_title_font.render(
        "Time's Up!",
        True,
        WHITE
    )

    title_rect = title.get_rect(
        center=(WIDTH//2, 220)
    )

    screen.blit(title, title_rect)


    score_line = score_font.render(
        f"Score: {score}",
        True,
        WHITE
    )

    score_rect = score_line.get_rect(
        center=(WIDTH//2, 295)
    )

    screen.blit(score_line, score_rect)


    best_line = score_font.render(
        f"Best: {get_high_score(mode, category)}",
        True,
        WHITE
    )

    best_rect = best_line.get_rect(
        center=(WIDTH//2, 335)
    )

    screen.blit(best_line, best_rect)


    if new_best_this_run:

        new_best_text = score_font.render(
            "New Best!",
            True,
            MILESTONE_GOLD
        )

        new_best_rect = new_best_text.get_rect(
            center=(WIDTH//2, 375)
        )

        screen.blit(new_best_text, new_best_rect)


    draw_menu_button(play_again_button, "Play Again", GREEN)
    draw_menu_button(game_over_menu_button, "Menu", GREY)



# ---------------- SETTINGS SCREEN ----------------

SETTINGS_ROW_TOP = 165
SETTINGS_ROW_STEP = 76
SETTINGS_BTN_H = 58


def settings_row_y(index):
    return SETTINGS_ROW_TOP + index * SETTINGS_ROW_STEP


minus_button = pygame.Rect(WIDTH//2 - 180, settings_row_y(0), 60, SETTINGS_BTN_H)
plus_button = pygame.Rect(WIDTH//2 + 120, settings_row_y(0), 60, SETTINGS_BTN_H)

category_button = pygame.Rect(WIDTH//2 - 220, settings_row_y(1), 440, SETTINGS_BTN_H)

mode_button = pygame.Rect(WIDTH//2 - 220, settings_row_y(2), 440, SETTINGS_BTN_H)

music_minus_button = pygame.Rect(WIDTH//2 - 180, settings_row_y(3), 60, SETTINGS_BTN_H)
music_plus_button = pygame.Rect(WIDTH//2 + 120, settings_row_y(3), 60, SETTINGS_BTN_H)

voice_minus_button = pygame.Rect(WIDTH//2 - 180, settings_row_y(4), 60, SETTINGS_BTN_H)
voice_plus_button = pygame.Rect(WIDTH//2 + 120, settings_row_y(4), 60, SETTINGS_BTN_H)

effects_minus_button = pygame.Rect(WIDTH//2 - 180, settings_row_y(5), 60, SETTINGS_BTN_H)
effects_plus_button = pygame.Rect(WIDTH//2 + 120, settings_row_y(5), 60, SETTINGS_BTN_H)

settings_back_button = pygame.Rect(
    WIDTH//2 - 140,
    settings_row_y(6) + 20,
    280,
    80
)


def draw_stepper_row(minus_rect, plus_rect, label_text, value_text):

    center_y = minus_rect.centery

    label_surf = score_font.render(label_text, True, BLACK)
    label_rect = label_surf.get_rect(midright=(WIDTH//2 - 200, center_y))
    screen.blit(label_surf, label_rect)

    value_surf = button_font.render(value_text, True, BLACK)
    value_rect = value_surf.get_rect(center=(WIDTH//2, center_y))
    screen.blit(value_surf, value_rect)

    draw_menu_button(minus_rect, "-", GREY)
    draw_menu_button(plus_rect, "+", GREY)


def draw_settings():

    draw_background()


    title = menu_title_font.render(
        "Settings",
        True,
        BLACK
    )

    title_rect = title.get_rect(
        center=(WIDTH//2, 95)
    )

    screen.blit(title, title_rect)


    draw_stepper_row(minus_button, plus_button, "Starting items:", str(STARTING_FRUIT_COUNT))

    draw_menu_button(category_button, f"Category: {CATEGORY_LABELS[category]}", GREY)
    draw_menu_button(mode_button, f"Mode: {MODE_LABELS[mode]}", GREY)

    draw_stepper_row(music_minus_button, music_plus_button, "Music:", f"{round(music_volume*100)}%")
    draw_stepper_row(voice_minus_button, voice_plus_button, "Voice:", f"{round(voice_volume*100)}%")
    draw_stepper_row(effects_minus_button, effects_plus_button, "Effects:", f"{round(effects_volume*100)}%")

    draw_menu_button(settings_back_button, "Back", GREY)



# ---------------- ACHIEVEMENTS SCREEN ----------------

achievements_back_button = pygame.Rect(
    WIDTH//2 - 140,
    800,
    280,
    60
)


def draw_achievements():

    draw_background()


    title = menu_title_font.render(
        "Achievements",
        True,
        BLACK
    )

    title_rect = title.get_rect(
        center=(WIDTH//2, 130)
    )

    screen.blit(title, title_rect)


    row_y = 210
    row_height = 78

    for achievement in ACHIEVEMENTS:

        unlocked = achievement["check"](progress)

        dot_color = GREEN if unlocked else WHITE

        pygame.draw.circle(screen, dot_color, (140, row_y), 14)
        pygame.draw.circle(screen, BLACK, (140, row_y), 14, 3)

        name_color = BLACK if unlocked else GREY

        name_text = score_font.render(achievement["name"], True, name_color)
        screen.blit(name_text, (180, row_y - 24))

        desc_text = small_font.render(achievement["desc"], True, GREY)
        screen.blit(desc_text, (180, row_y + 4))

        row_y += row_height


    draw_menu_button(achievements_back_button, "Back", GREY)



async def run():
    global screen, game_state
    global muted, category, mode
    global STARTING_FRUIT_COUNT, music_volume, voice_volume, effects_volume
    global correct_fruit, shake_fruit, shake_start_time, score, streak, new_best_this_run, active_count
    global timer_remaining
    global music_channel

    # background_music.play() was already consumed once at module import
    # time, so re-entering the game needs a fresh play() call here - and
    # exiting (see the end of this function) must explicitly stop it,
    # since nothing else does and it loops forever otherwise, overlapping
    # with whatever plays next.
    music_channel = background_music.play(loops=-1)

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
    if platform is not None and hasattr(platform, "window"):
        try:
            platform.window.window_resize()
        except Exception:
            pass
    pygame.display.set_caption("Find The Food")
    pygame.display.set_icon(pygame.image.load(str(BASE_DIR / "assets" / "app_icon.png")))


    clock = pygame.time.Clock()

    running = True

    game_state = "menu"



    while running:


        clock.tick(60)



        for event in pygame.event.get():



            if event.type == pygame.QUIT:

                running = False


            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    if game_state == "playing":
                        game_state = "paused"

                    elif game_state == "paused":
                        game_state = "playing"



            if event.type == pygame.MOUSEBUTTONDOWN:


                mouse_x, mouse_y = event.pos


                if mute_button.collidepoint(mouse_x, mouse_y):

                    muted = not muted

                    apply_volumes()


                elif game_state == "menu":

                    if start_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        await start_game()


                    elif settings_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        game_state = "settings"


                    elif achievements_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        game_state = "achievements"


                    elif quit_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        running = False


                elif game_state == "achievements":

                    if achievements_back_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        game_state = "menu"


                elif game_state == "game_over":

                    if play_again_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        await start_game()


                    elif game_over_menu_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        game_state = "menu"


                elif game_state == "settings":

                    if minus_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        STARTING_FRUIT_COUNT = max(
                            MIN_STARTING_FRUIT_COUNT,
                            STARTING_FRUIT_COUNT - 1
                        )


                    elif plus_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        STARTING_FRUIT_COUNT = min(
                            max_count_for_category(),
                            STARTING_FRUIT_COUNT + 1
                        )


                    elif category_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        next_index = (CATEGORIES.index(category) + 1) % len(CATEGORIES)
                        category = CATEGORIES[next_index]

                        STARTING_FRUIT_COUNT = min(
                            STARTING_FRUIT_COUNT,
                            max_count_for_category()
                        )


                    elif mode_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        next_index = (MODES.index(mode) + 1) % len(MODES)
                        mode = MODES[next_index]


                    elif music_minus_button.collidepoint(mouse_x, mouse_y):

                        music_volume = round(max(0.0, music_volume - VOLUME_STEP), 2)
                        apply_volumes()


                    elif music_plus_button.collidepoint(mouse_x, mouse_y):

                        music_volume = round(min(1.0, music_volume + VOLUME_STEP), 2)
                        apply_volumes()


                    elif voice_minus_button.collidepoint(mouse_x, mouse_y):

                        voice_volume = round(max(0.0, voice_volume - VOLUME_STEP), 2)
                        apply_volumes()


                    elif voice_plus_button.collidepoint(mouse_x, mouse_y):

                        voice_volume = round(min(1.0, voice_volume + VOLUME_STEP), 2)
                        apply_volumes()


                    elif effects_minus_button.collidepoint(mouse_x, mouse_y):

                        effects_volume = round(max(0.0, effects_volume - VOLUME_STEP), 2)
                        apply_volumes()


                    elif effects_plus_button.collidepoint(mouse_x, mouse_y):

                        effects_volume = round(min(1.0, effects_volume + VOLUME_STEP), 2)
                        apply_volumes()


                    elif settings_back_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        game_state = "menu"


                elif game_state == "paused":

                    if home_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        running = False

                        continue


                    elif resume_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        game_state = "playing"


                    elif quit_to_menu_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        game_state = "menu"


                elif game_state == "playing":

                    if home_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        running = False

                        continue


                    elif pause_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        game_state = "paused"

                        continue


                    for fruit in positions:


                        x,y = positions[fruit]


                        hitbox = pygame.Rect(
                            x,
                            y,
                            110,
                            110
                        )



                        if hitbox.collidepoint(
                            mouse_x,
                            mouse_y
                        ):



                            if fruit == target:


                                correct_fruit = fruit

                                score += 1
                                streak += 1

                                spawn_confetti(x + 55, y + 55, streak)

                                progress["total_correct"] += 1

                                if fruit not in progress["items_found"]:
                                    progress["items_found"].append(fruit)

                                if streak > progress["best_streak_ever"]:
                                    progress["best_streak_ever"] = streak

                                if score > get_high_score(mode, category):
                                    progress["high_scores"].setdefault(mode, {})[category] = score
                                    new_best_this_run = True

                                save_progress()

                                active_count = min(
                                    active_count + 1,
                                    max_count_for_category()
                                )

                                milestone_text = None

                                if streak >= 3 and streak % 3 == 0:
                                    milestone_text = f"{streak} in a row!"

                                play_correct_sound()

                                await animate_correct(fruit, milestone_text)


                                await new_round()


                            else:


                                shake_fruit = fruit
                                shake_start_time = time.time()

                                streak = 0

                                play_wrong_sound()


                            break



        if game_state == "menu":

            draw_menu()

        elif game_state == "settings":

            draw_settings()

        elif game_state == "achievements":

            draw_achievements()

        elif game_state == "paused":

            draw_game()

            draw_fruits()

            draw_particles()

            draw_pause_button()

            draw_pause_overlay()

            draw_home_button()

        elif game_state == "game_over":

            draw_game_over()

        else:

            # Fruit animation

            for fruit in active_fruits:

                if fruit_scale[fruit] < 1:

                    fruit_scale[fruit] += .05


            if mode == "timed":

                timer_remaining -= clock.get_time() / 1000

                if timer_remaining <= 0:
                    timer_remaining = 0
                    game_state = "game_over"


            draw_game()

            draw_fruits()

            update_particles(clock.get_time() / 1000)
            draw_particles()

            draw_pause_button()

            draw_home_button()


        draw_mute_button()

        update_music_fade(clock.get_time() / 1000)

        pygame.display.update()

        await asyncio.sleep(0)

    if music_channel is not None:
        music_channel.stop()
    voice_channel.stop()


if __name__ == "__main__":
    asyncio.run(run())
