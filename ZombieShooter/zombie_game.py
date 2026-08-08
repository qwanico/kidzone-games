import pygame
import random
import math

pygame.init()

WIDTH = 1000
HEIGHT = 700

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Nightmare Survival")

clock = pygame.time.Clock()

# Colors
BLACK = (0,0,0)
WHITE = (255,255,255)
RED = (180,0,0)
GREEN = (0,120,0)
DARK = (25,25,25)
BROWN = (45,35,25)

font = pygame.font.Font(None,36)
big_font = pygame.font.Font(None,80)


# Player
player = pygame.Rect(
    WIDTH//2,
    HEIGHT//2,
    45,
    45
)

player_speed = 5
health = 100


# Bullets
bullets = []


# Zombies
zombies = []

for i in range(8):

    zombies.append(
        pygame.Rect(
            random.randint(0,WIDTH),
            random.randint(0,HEIGHT),
            45,
            45
        )
    )


score = 0
wave = 1
game_over = False


# Blood particles
blood = []


def shoot():

    mx,my = pygame.mouse.get_pos()

    dx = mx - player.centerx
    dy = my - player.centery

    distance = math.hypot(dx,dy)

    if distance:

        bullets.append([
            player.centerx,
            player.centery,
            dx/distance*14,
            dy/distance*14
        ])



running = True


while running:

    clock.tick(60)


    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running=False


        if event.type == pygame.MOUSEBUTTONDOWN:

            if not game_over:
                shoot()


    if not game_over:


        # Movement
        keys = pygame.key.get_pressed()


        if keys[pygame.K_UP]:
            player.y -= player_speed

        if keys[pygame.K_DOWN]:
            player.y += player_speed

        if keys[pygame.K_LEFT]:
            player.x -= player_speed

        if keys[pygame.K_RIGHT]:
            player.x += player_speed



        # Bullet movement
        for bullet in bullets[:]:

            bullet[0]+=bullet[2]
            bullet[1]+=bullet[3]


            if (
                bullet[0]<0 or
                bullet[0]>WIDTH or
                bullet[1]<0 or
                bullet[1]>HEIGHT
            ):
                bullets.remove(bullet)



        # Zombies chase player
        for zombie in zombies:


            dx = player.centerx-zombie.centerx
            dy = player.centery-zombie.centery

            distance = math.hypot(dx,dy)


            if distance:

                speed = 1.5 + wave*.2

                zombie.x += int(dx/distance*speed)
                zombie.y += int(dy/distance*speed)


            if zombie.colliderect(player):

                health -= 1



        # Bullet hits

        for bullet in bullets[:]:

            bullet_rect = pygame.Rect(
                bullet[0],
                bullet[1],
                10,
                10
            )


            for zombie in zombies[:]:

                if bullet_rect.colliderect(zombie):

                    zombies.remove(zombie)

                    if bullet in bullets:
                        bullets.remove(bullet)


                    score += 10


                    # blood effect
                    for i in range(8):

                        blood.append([
                            zombie.centerx,
                            zombie.centery,
                            random.randint(-3,3),
                            random.randint(-3,3)
                        ])


                    break     # New waves
    if len(zombies) == 0:

        wave += 1

        for i in range(5 + wave * 3):

            zombies.append(
                pygame.Rect(
                    random.randint(0, WIDTH-45),
                    random.randint(0, HEIGHT-45),
                    45,
                    45
                )
            )


    if health <= 0:

        game_over = True



    # DRAWING

    # Old dark horror background
    screen.fill(BROWN)


    # Floor noise effect
    for i in range(80):

        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)

        pygame.draw.circle(
            screen,
            DARK,
            (x,y),
            2
        )


    # Blood particles
    for drop in blood[:]:

        drop[0] += drop[2]
        drop[1] += drop[3]

        pygame.draw.circle(
            screen,
            RED,
            (int(drop[0]), int(drop[1])),
            3
        )


        if random.random() < .05:

            blood.remove(drop)



    # Draw zombies with shadows
    for zombie in zombies:

        shadow = zombie.copy()
        shadow.x += 5
        shadow.y += 5

        pygame.draw.rect(
            screen,
            BLACK,
            shadow
        )


        pygame.draw.rect(
            screen,
            GREEN,
            zombie
        )



    # Draw player shadow

    player_shadow = player.copy()
    player_shadow.x += 5
    player_shadow.y += 5


    pygame.draw.rect(
        screen,
        BLACK,
        player_shadow
    )


    pygame.draw.rect(
        screen,
        (50,120,255),
        player
    )



    # Draw bullets

    for bullet in bullets:

        pygame.draw.circle(
            screen,
            (255,220,0),
            (
                int(bullet[0]),
                int(bullet[1])
            ),
            5
        )



    # Flashlight effect
    darkness = pygame.Surface((WIDTH,HEIGHT))

    darkness.fill((0,0,0))

    darkness.set_alpha(210)


    light_radius = 180


    pygame.draw.circle(
        darkness,
        (0,0,0,0),
        player.center,
        light_radius
    )


    screen.blit(darkness,(0,0))



    # HUD

    score_text = font.render(
        f"Score: {score}",
        True,
        WHITE
    )

    health_text = font.render(
        f"Health: {health}",
        True,
        WHITE
    )

    wave_text = font.render(
        f"Wave: {wave}",
        True,
        WHITE
    )


    screen.blit(score_text,(10,10))
    screen.blit(health_text,(10,45))
    screen.blit(wave_text,(10,80))



    # Game over

    if game_over:

        over = big_font.render(
            "YOU DIED",
            True,
            RED
        )

        restart = font.render(
            "Close and restart game",
            True,
            WHITE
        )


        screen.blit(
            over,
            (
                WIDTH//2-over.get_width()//2,
                HEIGHT//2-50
            )
        )

        screen.blit(
            restart,
            (
                WIDTH//2-restart.get_width()//2,
                HEIGHT//2+40
            )
        )



    pygame.display.update()


pygame.quit()
