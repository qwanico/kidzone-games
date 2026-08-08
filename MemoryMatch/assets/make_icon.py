import math
from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240


def draw_star(surf, center, radius, color):
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = radius if i % 2 == 0 else radius * 0.45
        points.append((center[0] + math.cos(angle) * r, center[1] - math.sin(angle) * r))
    pygame.draw.polygon(surf, color, points)


surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

card_back_rect = pygame.Rect(20, 40, 90, 110)
pygame.draw.rect(surf, (110, 100, 200), card_back_rect, border_radius=14)
pygame.draw.rect(surf, (255, 255, 255), card_back_rect, width=4, border_radius=14)

card_front_rect = pygame.Rect(128, 40, 90, 110)
pygame.draw.rect(surf, (255, 255, 255), card_front_rect, border_radius=14)
pygame.draw.rect(surf, (255, 255, 255), card_front_rect, width=4, border_radius=14)
draw_star(surf, card_front_rect.center, 38, (255, 210, 60))

card3_rect = pygame.Rect(75, 155, 90, 60)
pygame.draw.rect(surf, (140, 200, 120), card3_rect, border_radius=14)
pygame.draw.rect(surf, (255, 255, 255), card3_rect, width=4, border_radius=14)
pygame.draw.circle(surf, (230, 90, 110), card3_rect.center, 22)

pygame.image.save(surf, str(OUT / "memorymatch_icon.png"))
print("done")
