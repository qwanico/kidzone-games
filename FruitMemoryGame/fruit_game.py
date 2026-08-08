import pygame
import random
import time

pygame.init()

WIDTH = 900
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Find The Fruit!")

clock = pygame.time.Clock()

font = pygame.font.Font(None, 55)
big_font = pygame.font.Font(None, 90)


fruit_names = [
    "apple",
    "banana",
    "orange",
    "grapes",
    "watermelon",
    "strawberry",
    "lemon"
]


fruit_images = {}

for fruit in fruit_names:

    image = pygame.image.load(
        f"assets/{fruit}.png"
    )

    image = pygame.transform.scale(
        image,
        (90, 90)
    )

    fruit_images[fruit] = image



fruit_positions = {}

target = ""
start_time = 0

message = ""
message_color = (0, 180, 0)

confetti = []


def new_round():

    global target
    global start_time
    global fruit_positions
    global message

    target = random.choice(fruit_names)

    spots = [
        (120,130),
        (340,130),
        (560,130),
        (780,130),
        (120,350),
        (450,350),
        (780,350)
    ]

    random.shuffle(spots)

    fruit_positions = {}

    for fruit, spot in zip(fruit_names, spots):

        fruit_positions[fruit] = spot

    start_time = time.time()

    message = ""



def create_confetti():

    for i in range(50):

        confetti.append([
            random.randint(0, WIDTH),
            0,
            random.randint(-3,3),
            random.randint(2,6)
        ])



new_round()


running = True


while running:

    screen.fill((180,230,255))


    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False



        if event.type == pygame.MOUSEBUTTONDOWN:

            mx, my = pygame.mouse.get_pos()


            for fruit,(x,y) in fruit_positions.items():

                distance = (
                    (mx-x)**2 +
                    (my-y)**2
                ) ** .5


                if distance < 60:


                    if fruit == target:

                        message = "✓ GREAT JOB!"

                        message_color = (
                            0,
                            180,
                            0
                        )

                        create_confetti()


                    else:

                        message = "✗ TRY AGAIN!"

                        message_color = (
                            220,
                            0,
                            0
                        )



    timer = 10 - int(
        time.time() - start_time
    )


    if timer <= 0:

        message = "TIME!"

        message_color = (
            220,
            0,
            0
        )

        pygame.time.delay(700)

        new_round()



    title = font.render(
        "Find the " + target,
        True,
        (40,40,40)
    )

    screen.blit(
        title,
        (250,40)
    )


    timer_text = font.render(
        "Time: " + str(timer),
        True,
        (40,40,40)
    )

    screen.blit(
        timer_text,
        (20,20)
    )



    for fruit,(x,y) in fruit_positions.items():

        screen.blit(
            fruit_images[fruit],
            (
                x-45,
                y-45
            )
        )



    for piece in confetti[:]:

        piece[0] += piece[2]
        piece[1] += piece[3]


        pygame.draw.circle(
            screen,
            (255,200,0),
            (piece[0],piece[1]),
            5
        )


        if piece[1] > HEIGHT:

            confetti.remove(piece)



    if message:

        text = big_font.render(
            message,
            True,
            message_color
        )

        screen.blit(
            text,
            (250,500)
        )



    pygame.display.update()

    clock.tick(60)



pygame.quit()
