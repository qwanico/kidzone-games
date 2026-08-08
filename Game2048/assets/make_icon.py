from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent
SIZE = 240

surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
pygame.draw.rect(surf, (44, 48, 66), (0, 0, SIZE, SIZE), border_radius=20)

tiles = [
    ((20, 20), (110, 120, 160), "2"),
    ((130, 20), (90, 190, 120), "8"),
    ((20, 130), (240, 170, 70), "64"),
    ((130, 130), (200, 90, 200), "2048"),
]
font_big = pygame.font.SysFont(None, 40, bold=True)
font_small = pygame.font.SysFont(None, 28, bold=True)

for (x, y), color, label in tiles:
    rect = pygame.Rect(x, y, 90, 90)
    pygame.draw.rect(surf, color, rect, border_radius=10)
    font = font_small if len(label) > 2 else font_big
    text = font.render(label, True, (255, 255, 255))
    surf.blit(text, text.get_rect(center=rect.center))

pygame.image.save(surf, str(OUT / "game2048_icon.png"))
print("done")
