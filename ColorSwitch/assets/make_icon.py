from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240

surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

blocks = [
    (30, 190, 180, 34, (230, 90, 110)),
    (55, 150, 130, 34, (255, 220, 60)),
    (75, 110, 90, 34, (120, 210, 90)),
    (95, 70, 50, 34, (90, 170, 230)),
]
for x, y, w, h, color in blocks:
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surf, color, rect)
    pygame.draw.rect(surf, (255, 255, 255), rect, width=2)

pygame.image.save(surf, str(OUT / "colorswitch_icon.png"))
print("done")
