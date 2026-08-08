from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240

surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

pygame.draw.circle(surf, (200, 110, 90), (60, 70), 45)

rect = pygame.Rect(0, 0, 80, 80)
rect.center = (180, 70)
pygame.draw.rect(surf, (100, 170, 220), rect, border_radius=12)

center = (120, 180)
radius = 45
color = (220, 190, 90)
pygame.draw.line(surf, color, (center[0] - radius * 0.7, center[1] - radius * 0.7), (center[0] + radius * 0.7, center[1] + radius * 0.7), 12)
pygame.draw.line(surf, color, (center[0] + radius * 0.7, center[1] - radius * 0.7), (center[0] - radius * 0.7, center[1] + radius * 0.7), 12)
pygame.draw.circle(surf, color, (int(center[0] - radius * 0.7), int(center[1] + radius * 0.7)), 12)
pygame.draw.circle(surf, color, (int(center[0] + radius * 0.7), int(center[1] + radius * 0.7)), 12)

pygame.image.save(surf, str(OUT / "rockpaperscissors_icon.png"))
print("done")
