import pygame

pygame.init()

screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("My First Game")

x = 400
y = 300
speed = 5

running = True

while running:
    screen.fill((0, 0, 0))

    pygame.draw.rect(screen, (0, 255, 0), (x, y, 50, 50))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT]:
        x -= speed
    if keys[pygame.K_RIGHT]:
        x += speed
    if keys[pygame.K_UP]:
        y -= speed
    if keys[pygame.K_DOWN]:
        y += speed

    pygame.display.update()

pygame.quit()
