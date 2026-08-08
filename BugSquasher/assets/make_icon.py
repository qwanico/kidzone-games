import math
from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240

surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

center = (120, 130)
angle = -0.5
body_len = 100

for i in range(3):
    offset = (i - 1) * 22
    base_x = center[0] - math.cos(angle) * offset
    base_y = center[1] - math.sin(angle) * offset
    for sign in (1, -1):
        leg_angle = angle + sign * math.pi / 2
        end = (base_x + math.cos(leg_angle) * 34, base_y + math.sin(leg_angle) * 34)
        pygame.draw.line(surf, (40, 40, 40), (base_x, base_y), end, 6)

body_rect = pygame.Rect(0, 0, body_len, 70)
body_rect.center = center
pygame.draw.ellipse(surf, (90, 70, 170), body_rect)
pygame.draw.line(surf, (25, 25, 25), body_rect.midtop, body_rect.midbottom, 4)

head_x = center[0] + math.cos(angle) * body_len / 2
head_y = center[1] + math.sin(angle) * body_len / 2
pygame.draw.circle(surf, (25, 25, 25), (int(head_x), int(head_y)), 20)

pygame.image.save(surf, str(OUT / "bugsquasher_icon.png"))
print("done")
