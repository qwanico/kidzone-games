from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240

surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
pygame.draw.rect(surf, (30, 60, 90), (0, 0, SIZE, SIZE), border_radius=20)
pygame.draw.line(surf, (80, 130, 170), (0, 120), (SIZE, 120), 4)
pygame.draw.circle(surf, (80, 130, 170), (120, 120), 44, 3)

pygame.draw.circle(surf, (240, 120, 140), (120, 55), 30)
pygame.draw.circle(surf, (120, 220, 255), (120, 185), 30)
pygame.draw.circle(surf, (240, 220, 90), (120, 120), 16)

pygame.image.save(surf, str(OUT / "airhockey_icon.png"))
print("done")
