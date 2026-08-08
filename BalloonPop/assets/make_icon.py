from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240

surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

balloons = [
    ((230, 90, 110), (75, 110), 55, 70),
    ((90, 160, 230), (150, 75), 50, 64),
    ((255, 190, 90), (175, 150), 46, 58),
]

for color, center, w, h in balloons:
    string_end = (center[0], center[1] + h // 2 + 45)
    pygame.draw.line(surf, (150, 150, 150), (center[0], center[1] + h // 2), string_end, 3)

for color, center, w, h in balloons:
    rect = pygame.Rect(0, 0, w, h)
    rect.center = center
    pygame.draw.ellipse(surf, color, rect)
    highlight = pygame.Rect(0, 0, w // 4, h // 3)
    highlight.center = (center[0] - w // 4, center[1] - h // 4)
    pygame.draw.ellipse(surf, tuple(min(255, c + 60) for c in color), highlight)

pygame.image.save(surf, str(OUT / "balloonpop_icon.png"))
print("done")
