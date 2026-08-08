from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240

surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
surf.fill((0, 0, 0, 0))

pygame.draw.rect(surf, (20, 24, 30), (0, 0, SIZE, SIZE), border_radius=24)

segments = [(60, 180), (60, 140), (100, 140), (100, 100), (140, 100), (140, 60)]
for i, (x, y) in enumerate(segments):
    color = (130, 245, 170) if i == len(segments) - 1 else (90, 220, 140)
    pygame.draw.rect(surf, color, (x - 20, y - 20, 40, 40), border_radius=10)

pygame.draw.circle(surf, (240, 90, 100), (180, 60), 14)

pygame.image.save(surf, str(OUT / "snake_icon.png"))
print("done")
