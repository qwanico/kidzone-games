from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240

surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

hole_color = (90, 60, 40)
pygame.draw.ellipse(surf, hole_color, (40, 150, 160, 60))

head_center = (120, 120)
pygame.draw.circle(surf, (120, 80, 55), head_center, 80)
ear_r = 22
pygame.draw.circle(surf, (95, 60, 40), (head_center[0] - 55, head_center[1] - 55), ear_r)
pygame.draw.circle(surf, (95, 60, 40), (head_center[0] + 55, head_center[1] - 55), ear_r)

eye_y = head_center[1] - 8
pygame.draw.circle(surf, (30, 30, 30), (head_center[0] - 26, eye_y), 9)
pygame.draw.circle(surf, (30, 30, 30), (head_center[0] + 26, eye_y), 9)

pygame.draw.ellipse(surf, (230, 150, 150), (head_center[0] - 20, head_center[1] + 12, 40, 26))

pygame.draw.ellipse(surf, hole_color, (40, 150, 160, 40))

pygame.image.save(surf, str(OUT / "whackamole_icon.png"))
print("done")
