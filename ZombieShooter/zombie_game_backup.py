import pygame
import random
import math

pygame.init()

WIDTH = 1000
HEIGHT = 700

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zombie Shooter")

clock = pygame.time.Clock()

font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)

# Load images
player_image = pygame.image.load("assets/player.png")
zombie_image = pygame.image.load("assets/zombie.png")
bullet_image = pygame.image.load("assets/bullet.png")

player_image = pygame.transform.scale(player_image, (50, 50))
zombie_image = pygame.transform.scale(zombie_image, (40, 40))
bullet_image = pygame.transform.scale(bullet_image, (10, 10))


def reset_game():

    player = pygame.Rect(
        WIDTH // 2,
        HEIGHT // 2,
        50,
        50
    )

    zombies = []

    for i in range(5):
        zombies.append(
            pygame.Rect(
                random.randint(0, WIDTH - 40),
                random.randint(0, HEIGHT - 40),
                40,
                40
            )
        )

    return player, zombies, [], 100, 0, 1


player, zombies, bullets, health, score, wave = reset_game()

player_speed = 5

running = True
game_over = False


while running:

    clock.tick(60)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # Shoot
        if event.type == pygame.MOUSEBUTTONDOWN and not game_over:

            mx, my = pygame.mouse.get_pos()

            dx = mx - player.centerx
            dy = my - player.centery

            distance = math.hypot(dx, dy)

            if distance > 0:

                bullets.append([
                    player.centerx,
                    player.centery,
                    dx / distance * 12,
                    dy / distance * 12
                ])

        # Restart
        if game_over and event.type == pygame.KEYDOWN:

            if event.key == pygame.K_r:

                player, zombies, bullets, health, score, wave = reset_game()
                game_over = False


    if not game_over:

        # Arrow movement
        keys = pygame.key.get_pressed()

        if keys[pygame.K_UP]:
            player.y -= player_speed

        if keys[pygame.K_DOWN]:
            player.y += player_speed

        if keys[pygame.K_LEFT]:
            player.x -= player_speed

        if keys[pygame.K_RIGHT]:
            player.x += player_speed


        # Keep player on screen
        player.x = max(0, min(player.x, WIDTH - 50))
        player.y = max(0, min(player.y, HEIGHT - 50))


        # Move bullets
        for bullet in bullets[:]:

            bullet[0] += bullet[2]
            bullet[1] += bullet[3]

            if (
                bullet[0] < 0 or
                bullet[0] > WIDTH or
                bullet[1] < 0 or
                bullet[1] > HEIGHT
            ):
                bullets.remove(bullet)


        # Zombies chase player
        zombie_speed = 2 + wave * 0.2

        for zombie in zombies:

            dx = player.centerx - zombie.centerx
            dy = player.centery - zombie.centery

            distance = math.hypot(dx, dy)

            if distance > 0:

                zombie.x += int(dx / distance * zombie_speed)
                zombie.y += int(dy / distance * zombie_speed)


            if zombie.colliderect(player):

                health -= 1


        # Bullets hit zombies
        for bullet in bullets[:]:

            bullet_rect = pygame.Rect(
                int(bullet[0]),
                int(bullet[1]),
                10,
                10
            )

            for zombie in zombies[:]:

                if bullet_rect.colliderect(zombie):

                    zombies.remove(zombie)

                    if bullet in bullets:
                        bullets.remove(bullet)

                    score += 10
                    break


        # New wave
        if len(zombies) == 0:

            wave += 1

            for i in range(5 + wave * 2):

                zombies.append(
                    pygame.Rect(
                        random.randint(0, WIDTH - 40),
                        random.randint(0, HEIGHT - 40),
                        40,
                        40
                    )
                )


        if health <= 0:

            game_over = True


    # Draw
    screen.fill((30, 30, 30))


    screen.blit(player_image, player)


    for zombie in zombies:

        screen.blit(zombie_image, zombie)


    for bullet in bullets:

        screen.blit(
            bullet_image,
            (
                int(bullet[0]),
                int(bullet[1])
            )
        )


    screen.blit(
        font.render(f"Score: {score}", True, (255,255,255)),
        (10,10)
    )

    screen.blit(
        font.render(f"Health: {health}", True, (255,255,255)),
        (10,50)
    )

    screen.blit(
        font.render(f"Wave: {wave}", True, (255,255,255)),
        (10,90)
    )


    if game_over:

        screen.blit(
            big_font.render(
                "GAME OVER",
                True,
                (255,255,255)
            ),
            (350,300)
        )

        screen.blit(
            font.render(
                "Press R to restart",
                True,
                (255,255,255)
            ),
            (400,380)
        )


    pygame.display.update()


pygame.quit()
