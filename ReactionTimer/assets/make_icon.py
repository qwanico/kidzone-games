from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240

surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

pygame.draw.circle(surf, (70, 190, 110), (120, 120), 100)
pygame.draw.circle(surf, (255, 255, 255), (120, 120), 100, 6)

pygame.draw.circle(surf, (40, 44, 60), (120, 120), 10)
pygame.draw.line(surf, (40, 44, 60), (120, 120), (120, 55), 8)
pygame.draw.line(surf, (40, 44, 60), (120, 120), (165, 140), 8)

pygame.image.save(surf, str(OUT / "reactiontimer_icon.png"))
print("done")
