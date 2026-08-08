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

draw_star(surf, (120, 95), 60, (255, 220, 90))

basket_rect = pygame.Rect(50, 165, 140, 50)
pygame.draw.polygon(
    surf,
    (200, 140, 60),
    [
        (basket_rect.left + 12, basket_rect.top),
        (basket_rect.right - 12, basket_rect.top),
        (basket_rect.right, basket_rect.bottom),
        (basket_rect.left, basket_rect.bottom),
    ],
)
for i in range(3):
    lx = basket_rect.left + 24 + i * (basket_rect.width - 48) / 2
    pygame.draw.line(surf, (150, 100, 40), (lx, basket_rect.top + 6), (lx, basket_rect.bottom - 6), 4)

pygame.image.save(surf, str(OUT / "starcatcher_icon.png"))
print("done")
