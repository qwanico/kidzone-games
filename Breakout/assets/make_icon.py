from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240

surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

colors = [(230, 90, 110), (255, 170, 60), (255, 220, 60), (120, 210, 90)]
brick_w, brick_h, gap = 52, 20, 6
cols = 4
start_x = (SIZE - (cols * brick_w + (cols - 1) * gap)) // 2
for row in range(3):
    for col in range(cols):
        x = start_x + col * (brick_w + gap)
        y = 30 + row * (brick_h + gap)
        pygame.draw.rect(surf, colors[row % len(colors)], (x, y, brick_w, brick_h), border_radius=4)

pygame.draw.rect(surf, (120, 220, 255), (75, 190, 90, 16), border_radius=8)
pygame.draw.circle(surf, (240, 210, 90), (120, 165), 12)

pygame.image.save(surf, str(OUT / "breakout_icon.png"))
print("done")
