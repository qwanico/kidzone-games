from pathlib import Path

import pygame

pygame.init()

OUT = Path(__file__).parent / "tile_icons"
OUT.mkdir(exist_ok=True)
SIZE = 240


def new_surface():
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    return surf


def draw_letters_icon():
    surf = new_surface()
    font = pygame.font.SysFont(None, 90, bold=True)
    blocks = [
        ("A", (230, 90, 110), (20, 70)),
        ("B", (240, 170, 60), (90, 30)),
        ("C", (110, 180, 220), (150, 90)),
    ]
    for letter, color, pos in blocks:
        rect = pygame.Rect(pos[0], pos[1], 90, 90)
        pygame.draw.rect(surf, color, rect, border_radius=16)
        pygame.draw.rect(surf, (255, 255, 255), rect, width=4, border_radius=16)
        text = font.render(letter, True, (255, 255, 255))
        surf.blit(text, text.get_rect(center=rect.center))
    pygame.image.save(surf, str(OUT / "letters.png"))


def draw_sight_words_icon():
    surf = new_surface()
    # speech bubble
    bubble_rect = pygame.Rect(20, 30, 200, 140)
    pygame.draw.rect(surf, (255, 255, 255), bubble_rect, border_radius=30)
    pygame.draw.rect(surf, (90, 160, 230), bubble_rect, width=6, border_radius=30)
    tail = [(70, 165), (70, 210), (120, 165)]
    pygame.draw.polygon(surf, (255, 255, 255), tail)
    pygame.draw.polygon(surf, (90, 160, 230), tail, width=6)

    font = pygame.font.SysFont(None, 54, bold=True)
    text = font.render("the", True, (60, 90, 130))
    surf.blit(text, text.get_rect(center=(bubble_rect.centerx, bubble_rect.centery)))

    # sound waves near top-right
    for i, radius in enumerate((14, 24, 34)):
        rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        rect.center = (205, 55)
        pygame.draw.arc(
            surf,
            (90, 160, 230),
            rect,
            -0.6,
            0.6,
            4,
        )
    pygame.image.save(surf, str(OUT / "sight_words.png"))


def draw_shapes_icon():
    surf = new_surface()
    blocks = [
        ("circle", (20, 150, 140), (20, 70)),
        ("square", (240, 170, 60), (90, 30)),
        ("triangle", (230, 90, 110), (150, 90)),
    ]
    for shape, color, pos in blocks:
        rect = pygame.Rect(pos[0], pos[1], 90, 90)
        pygame.draw.rect(surf, color, rect, border_radius=16)
        pygame.draw.rect(surf, (255, 255, 255), rect, width=4, border_radius=16)
        cx, cy = rect.center
        if shape == "circle":
            pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 26)
        elif shape == "square":
            sq = pygame.Rect(0, 0, 48, 48)
            sq.center = (cx, cy)
            pygame.draw.rect(surf, (255, 255, 255), sq, border_radius=8)
        elif shape == "triangle":
            half = 28
            pts = [(cx, cy - half), (cx - half, cy + half * 0.85), (cx + half, cy + half * 0.85)]
            pygame.draw.polygon(surf, (255, 255, 255), pts)
    pygame.image.save(surf, str(OUT / "shapes.png"))


def draw_counting_icon():
    surf = new_surface()
    font = pygame.font.SysFont(None, 90, bold=True)
    blocks = [
        ("1", (150, 80, 190), (20, 70)),
        ("2", (240, 170, 60), (90, 30)),
        ("3", (110, 180, 220), (150, 90)),
    ]
    for num, color, pos in blocks:
        rect = pygame.Rect(pos[0], pos[1], 90, 90)
        pygame.draw.rect(surf, color, rect, border_radius=16)
        pygame.draw.rect(surf, (255, 255, 255), rect, width=4, border_radius=16)
        text = font.render(num, True, (255, 255, 255))
        surf.blit(text, text.get_rect(center=rect.center))
    pygame.image.save(surf, str(OUT / "counting.png"))


def draw_colors_icon():
    surf = new_surface()
    swatches = [
        (215, 70, 70),   # red
        (250, 210, 30),  # yellow
        (40, 170, 70),   # green
        (40, 90, 230),   # blue
        (250, 140, 30),  # orange
        (140, 60, 190),  # purple
    ]
    cols, rows = 3, 2
    cell, gap = 56, 14
    grid_w = cols * cell + (cols - 1) * gap
    grid_h = rows * cell + (rows - 1) * gap
    start_x = (SIZE - grid_w) // 2
    start_y = (SIZE - grid_h) // 2
    for i, color in enumerate(swatches):
        r, c = divmod(i, cols)
        rect = pygame.Rect(
            start_x + c * (cell + gap), start_y + r * (cell + gap), cell, cell
        )
        pygame.draw.rect(surf, color, rect, border_radius=14)
        pygame.draw.rect(surf, (255, 255, 255), rect, width=3, border_radius=14)
    pygame.image.save(surf, str(OUT / "colors.png"))


def draw_math_icon():
    surf = new_surface()
    font_big = pygame.font.SysFont(None, 90, bold=True)
    font_small = pygame.font.SysFont(None, 64, bold=True)

    blocks = [
        ("3", (120, 180, 40), (20, 70)),
        ("+", (240, 170, 60), (90, 30)),
        ("2", (110, 180, 220), (150, 90)),
    ]
    for label, color, pos in blocks:
        rect = pygame.Rect(pos[0], pos[1], 90, 90)
        pygame.draw.rect(surf, color, rect, border_radius=16)
        pygame.draw.rect(surf, (255, 255, 255), rect, width=4, border_radius=16)
        font = font_small if label == "+" else font_big
        text = font.render(label, True, (255, 255, 255))
        surf.blit(text, text.get_rect(center=rect.center))
    pygame.image.save(surf, str(OUT / "math.png"))


draw_letters_icon()
draw_sight_words_icon()
draw_shapes_icon()
draw_counting_icon()
draw_colors_icon()
draw_math_icon()
print("done")
