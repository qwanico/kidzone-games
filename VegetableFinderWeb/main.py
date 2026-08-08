import asyncio
import pygame
import random
import os

pygame.init()

# ---------------- WINDOW ----------------

WIDTH = 1280
HEIGHT = 800

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT)
)

pygame.display.set_caption(
    "Vegetable Finder"
)


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



# ---------------- SKY GRADIENT SURFACE ----------------

GRASS_TOP = 720

sky_surface = pygame.Surface((WIDTH, GRASS_TOP))

for y in range(GRASS_TOP):

    t = y / GRASS_TOP

    r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t)
    g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t)
    b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t)

    pygame.draw.line(
        sky_surface,
        (r, g, b),
        (0, y),
        (WIDTH, y)
    )



# ---------------- VOICE ----------------
# All "Find the X" lines are pre-generated as .ogg and shipped in
# voice_cache/ so the browser build never needs a live network call to
# Google TTS, and never touches .mp3 (not allowed on web builds).

VOICE_CACHE_DIR = "voice_cache"


def voice_path(vegetable):
    return os.path.join(
        VOICE_CACHE_DIR,
        f"{vegetable}.ogg"
    )


def speak_vegetable(vegetable):

    path = voice_path(vegetable)

    if not os.path.exists(path):
        print(f"No cached voice line for {vegetable}, skipping")
        return

    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()

    except Exception as e:
        print(f"Could not play voice line for {vegetable}: {e}")



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



# ---------------- SOUND EFFECTS ----------------

pygame.mixer.init()

wrong_sound = pygame.mixer.Sound("sounds/wrong.ogg")



# ---------------- VEGETABLES ----------------

vegetables = [
    "carrot",
    "corn",
    "potato",
    "tomato",
    "broccoli",
    "leafy_green",
    "garlic",
    "onion",
    "bell_pepper",
    "cucumber",
    "eggplant",
    "hot_pepper",
    "olive",
    "beans",
    "chestnut",
    "pumpkin",
    "sweet_potato",
    "mushroom",
    "peanuts",
    "salad"
]


# ---------------- LOAD IMAGES ----------------

images = {}

for vegetable in vegetables:

    img = pygame.image.load(
        f"assets/{vegetable}.png"
    )

    img = pygame.transform.scale(
        img,
        (110,110)
    )

    images[vegetable] = img



# ---------------- GRID POSITIONS ----------------

def create_positions(active_vegetables):

    spots = []

    columns = [
        80,
        330,
        580,
        830,
        1080
    ]

    rows = [
        180,
        390,
        600
    ]


    for y in rows:
        for x in columns:
            spots.append(
                (x,y)
            )


    random.shuffle(spots)


    return dict(
        zip(
            active_vegetables,
            spots
        )
    )


# ---------------- DIFFICULTY / SCORE ----------------

NUM_GRID_SPOTS = 15

STARTING_VEGETABLE_COUNT = 5
MAX_VEGETABLE_COUNT = min(len(vegetables), NUM_GRID_SPOTS)

active_count = STARTING_VEGETABLE_COUNT
score = 0

active_vegetables = random.sample(vegetables, active_count)
positions = create_positions(active_vegetables)


target = random.choice(active_vegetables)



# ---------------- ANIMATION ----------------

vegetable_scale = {}

for vegetable in vegetables:
    vegetable_scale[vegetable] = 0.1


shake_vegetable = None
correct_vegetable = None


# ---------------- BACKGROUND ----------------

def draw_background():

    screen.blit(sky_surface, (0,0))


    # Sun (with a soft glow)

    pygame.draw.circle(
        screen,
        SUN_GLOW_OUTER,
        (1160,90),
        90
    )

    pygame.draw.circle(
        screen,
        SUN_GLOW_INNER,
        (1160,90),
        75
    )

    pygame.draw.circle(
        screen,
        YELLOW,
        (1160,90),
        60
    )


    # Clouds

    clouds = [
        (150,100,1.0),
        (500,80,1.15),
        (850,120,0.9)
    ]

    for x,y,scale in clouds:

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
                (x + int(dx*scale), y + int(dy*scale)),
                int(r*scale)
            )



    # Grass

    pygame.draw.rect(
        screen,
        GRASS_SHADOW,
        (0,720,WIDTH,12)
    )

    pygame.draw.rect(
        screen,
        GRASS,
        (0,732,WIDTH,68)
    )


    # Flowers

    flowers = [
        90, 260, 430, 600, 770, 940, 1110
    ]

    for x in flowers:

        y = 760

        pygame.draw.circle(
            screen,
            WHITE,
            (x,y),
            7
        )

        pygame.draw.circle(
            screen,
            WHITE,
            (x-9,y+4),
            7
        )

        pygame.draw.circle(
            screen,
            WHITE,
            (x+9,y+4),
            7
        )

        pygame.draw.circle(
            screen,
            FLOWER_YELLOW,
            (x,y+3),
            5
        )



# ---------------- DRAW SCREEN ----------------

def draw_game():

    draw_background()


    title = title_font.render(
        f"Find the {target.replace('_', ' ')}!",
        True,
        BLACK
    )


    screen.blit(
        title,
        (380,35)
    )


    score_text = score_font.render(
        f"Score: {score}",
        True,
        BLACK
    )

    screen.blit(
        score_text,
        (20,20)
    )



# ---------------- DRAW VEGETABLES ----------------

def draw_vegetables():

    global shake_vegetable
    global correct_vegetable


    for vegetable in positions:


        x,y = positions[vegetable]


        scale = vegetable_scale[vegetable]


        size = int(
            110 * scale
        )


        if size < 1:
            size = 1


        img = pygame.transform.scale(
            images[vegetable],
            (size,size)
        )


        draw_x = x + (110-size)//2
        draw_y = y + (110-size)//2



        # shake wrong vegetable

        if vegetable == shake_vegetable:

            draw_x += random.randint(
                -8,
                8
            )



        screen.blit(
            img,
            (draw_x,draw_y)
        )



        # correct circle

        if vegetable == correct_vegetable:

            pygame.draw.circle(
                screen,
                GREEN,
                (x+55,y+55),
                65,
                6
            )



# ---------------- NEW ROUND ----------------

async def new_round():

    global positions
    global target
    global vegetable_scale
    global shake_vegetable
    global correct_vegetable
    global active_vegetables


    active_vegetables = random.sample(
        vegetables,
        active_count
    )


    target = random.choice(
        active_vegetables
    )


    positions = create_positions(active_vegetables)



    for vegetable in active_vegetables:

        vegetable_scale[vegetable] = 0.1



    shake_vegetable = None
    correct_vegetable = None



    # Animate vegetables appearing

    while any(
        vegetable_scale[f] < 1
        for f in active_vegetables
    ):


        draw_game()

        draw_vegetables()


        pygame.display.update()



        for vegetable in active_vegetables:

            if vegetable_scale[vegetable] < 1:

                vegetable_scale[vegetable] += .12



        await asyncio.sleep(.03)



    # pause after animation

    await asyncio.sleep(1)


    speak_vegetable(target)



# ---------------- START MENU ----------------

start_button = pygame.Rect(
    WIDTH//2 - 140,
    520,
    280,
    90
)


def draw_menu():

    draw_background()


    title = menu_title_font.render(
        "Vegetable Finder",
        True,
        BLACK
    )

    title_rect = title.get_rect(
        center=(WIDTH//2, 220)
    )

    screen.blit(title, title_rect)


    subtitle = score_font.render(
        "Find the vegetable that's named!",
        True,
        BLACK
    )

    subtitle_rect = subtitle.get_rect(
        center=(WIDTH//2, 300)
    )

    screen.blit(subtitle, subtitle_rect)


    pygame.draw.rect(
        screen,
        GREEN,
        start_button,
        border_radius=20
    )

    pygame.draw.rect(
        screen,
        BLACK,
        start_button,
        4,
        border_radius=20
    )

    start_text = button_font.render(
        "Start",
        True,
        WHITE
    )

    start_text_rect = start_text.get_rect(
        center=start_button.center
    )

    screen.blit(start_text, start_text_rect)



# ---------------- MAIN LOOP ----------------

async def main():

    global active_count
    global score
    global shake_vegetable
    global correct_vegetable

    clock = pygame.time.Clock()

    running = True

    game_state = "menu"


    while running:


        clock.tick(60)


        # FINGERDOWN covers touch on iPad/mobile browsers; MOUSEBUTTONDOWN
        # covers desktop clicks. A single physical tap on iOS Safari often
        # produces both a native FINGERDOWN and a synthesized
        # MOUSEBUTTONDOWN in the same batch, so only the first tap-like
        # event per frame is acted on - otherwise the second (stale) one
        # gets checked against the vegetable that's now sitting in that
        # spot after new_round() has already run, registering as a wrong
        # tap.

        tap_handled_this_frame = False

        for event in pygame.event.get():



            if event.type == pygame.QUIT:

                running = False


            if tap_handled_this_frame:
                continue


            tap_pos = None

            if event.type == pygame.MOUSEBUTTONDOWN:
                tap_pos = event.pos

            elif event.type == pygame.FINGERDOWN:
                tap_pos = (
                    int(event.x * WIDTH),
                    int(event.y * HEIGHT)
                )


            if tap_pos is not None:

                tap_handled_this_frame = True


                mouse_x, mouse_y = tap_pos


                if game_state == "menu":

                    if start_button.collidepoint(
                        mouse_x,
                        mouse_y
                    ):

                        game_state = "playing"

                        await new_round()


                elif game_state == "playing":

                    for vegetable in positions:


                        x,y = positions[vegetable]


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



                            if vegetable == target:


                                correct_vegetable = vegetable

                                score += 1

                                active_count = min(
                                    active_count + 1,
                                    MAX_VEGETABLE_COUNT
                                )


                                draw_game()

                                draw_vegetables()

                                pygame.display.update()



                                await asyncio.sleep(.8)


                                await new_round()

                            else:


                                shake_vegetable = vegetable

                                wrong_sound.play()


                            break


        if game_state == "menu":

            draw_menu()

        else:

            # Vegetable animation

            for vegetable in active_vegetables:

                if vegetable_scale[vegetable] < 1:

                    vegetable_scale[vegetable] += .05



            draw_game()

            draw_vegetables()


        pygame.display.update()

        # Yields to the browser event loop every frame; required by pygbag.
        await asyncio.sleep(0)


    pygame.quit()


asyncio.run(main())
