from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240

surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

pygame.draw.rect(surf, (90, 180, 90), (30, 0, 50, 90), border_radius=4)
pygame.draw.rect(surf, (90, 180, 90), (30, 150, 50, 90), border_radius=4)

pygame.draw.circle(surf, (250, 210, 60), (150, 120), 42)
pygame.draw.circle(surf, (30, 30, 30), (168, 108), 8)
pygame.draw.polygon(surf, (240, 140, 40), [(192, 120), (220, 110), (220, 132)])

pygame.image.save(surf, str(OUT / "flappybird_icon.png"))
print("done")
