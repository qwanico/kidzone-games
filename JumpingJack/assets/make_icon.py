from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240

surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

ground_y = 190
pygame.draw.rect(surf, (140, 200, 110), (0, ground_y, SIZE, SIZE - ground_y))

rect = pygame.Rect(0, 0, 60, 84)
rect.midbottom = (100, ground_y - 6)
pygame.draw.rect(surf, (90, 130, 220), rect, border_radius=14)
pygame.draw.circle(surf, (250, 210, 170), (rect.centerx, rect.top - 8), 22)
pygame.draw.line(surf, (60, 60, 90), (rect.centerx - 12, rect.bottom), (rect.centerx - 22, rect.bottom + 20), 7)
pygame.draw.line(surf, (60, 60, 90), (rect.centerx + 12, rect.bottom), (rect.centerx + 24, rect.bottom + 16), 7)

obstacle = pygame.Rect(0, 0, 48, 72)
obstacle.midbottom = (185, ground_y)
pygame.draw.rect(surf, (200, 90, 70), obstacle, border_radius=10)
pygame.draw.rect(surf, (150, 60, 45), obstacle, width=4, border_radius=10)

pygame.image.save(surf, str(OUT / "jumpingjack_icon.png"))
print("done")
