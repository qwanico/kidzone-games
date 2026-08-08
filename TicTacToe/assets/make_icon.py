from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240

surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

for i in range(1, 3):
    pygame.draw.line(surf, (90, 96, 120), (i * 80, 10), (i * 80, 230), 6)
    pygame.draw.line(surf, (90, 96, 120), (10, i * 80), (230, i * 80), 6)

pygame.draw.line(surf, (120, 220, 255), (25, 25), (75, 75), 10)
pygame.draw.line(surf, (120, 220, 255), (75, 25), (25, 75), 10)

pygame.draw.circle(surf, (240, 120, 140), (200, 45), 32, 9)

pygame.draw.line(surf, (120, 220, 255), (105, 185), (155, 235), 10)
pygame.draw.line(surf, (120, 220, 255), (155, 185), (105, 235), 10)

pygame.image.save(surf, str(OUT / "tictactoe_icon.png"))
print("done")
