from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240

surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

letters = [("W", (70, 76, 100), -18), ("O", (90, 200, 130), 10), ("R", (70, 76, 100), -8), ("D", (220, 190, 90), 16)]
tile = 56
gap = 10
total_w = len(letters) * tile + (len(letters) - 1) * gap
start_x = (SIZE - total_w) // 2
font = pygame.font.SysFont(None, 40, bold=True)

for i, (letter, color, dy) in enumerate(letters):
    x = start_x + i * (tile + gap)
    y = 90 + dy
    rect = pygame.Rect(x, y, tile, tile)
    pygame.draw.rect(surf, color, rect, border_radius=10)
    pygame.draw.rect(surf, (255, 255, 255), rect, width=2, border_radius=10)
    text = font.render(letter, True, (255, 255, 255))
    surf.blit(text, text.get_rect(center=rect.center))

pygame.image.save(surf, str(OUT / "wordscramble_icon.png"))
print("done")
