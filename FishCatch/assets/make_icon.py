from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240

surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

pygame.draw.rect(surf, (70, 150, 210), (0, 130, SIZE, 110))

color = (255, 170, 60)
body_rect = pygame.Rect(0, 0, 130, 76)
body_rect.center = (130, 120)

tail_pts = [
    (body_rect.left, body_rect.centery),
    (body_rect.left - 34, body_rect.centery - 28),
    (body_rect.left - 34, body_rect.centery + 28),
]
pygame.draw.polygon(surf, color, tail_pts)
pygame.draw.ellipse(surf, color, body_rect)
pygame.draw.circle(surf, (255, 255, 255), (body_rect.centerx + 32, body_rect.centery - 8), 11)
pygame.draw.circle(surf, (20, 20, 20), (body_rect.centerx + 32, body_rect.centery - 8), 5)

pygame.image.save(surf, str(OUT / "fishcatch_icon.png"))
print("done")
