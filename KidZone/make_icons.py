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


def draw_maze_icon():
    surf = new_surface()
    wall_color = (110, 120, 135)
    path_color = (255, 255, 255)
    goal_color = (255, 205, 60)
    player_color = (90, 160, 230)

    board = pygame.Rect(14, 14, SIZE - 28, SIZE - 28)
    pygame.draw.rect(surf, wall_color, board, border_radius=18)
    inner = board.inflate(-16, -16)
    pygame.draw.rect(surf, path_color, inner, border_radius=12)

    # staggered interior wall segments that read as maze corridors
    # (offset from one another so they don't form a symmetric cross)
    seg_color = wall_color
    ox, oy = inner.left, inner.top
    pygame.draw.rect(surf, seg_color, pygame.Rect(ox + 44, oy + 10, 14, 70), border_radius=6)
    pygame.draw.rect(surf, seg_color, pygame.Rect(ox + 80, oy + 70, 80, 14), border_radius=6)
    pygame.draw.rect(surf, seg_color, pygame.Rect(ox + 138, oy + 100, 14, 66), border_radius=6)
    pygame.draw.rect(surf, seg_color, pygame.Rect(ox + 20, oy + 140, 68, 14), border_radius=6)

    # player circle near the start (top-left)
    player_center = (inner.left + 20, inner.top + 20)
    pygame.draw.circle(surf, player_color, player_center, 18)
    pygame.draw.circle(surf, (60, 130, 200), player_center, 18, width=3)

    # goal star near the bottom-right
    cx, cy = inner.right - 22, inner.bottom - 22
    points = []
    radius = 22
    import math as _m
    for i in range(10):
        angle = -_m.pi / 2 + i * _m.pi / 5
        r = radius if i % 2 == 0 else radius * 0.45
        points.append((cx + _m.cos(angle) * r, cy + _m.sin(angle) * r))
    pygame.draw.polygon(surf, goal_color, points)
    pygame.draw.polygon(surf, (255, 255, 255), points, width=2)

    pygame.image.save(surf, str(OUT / "maze.png"))


def draw_simon_pattern_icon():
    surf = new_surface()
    quad_colors = [
        (70, 180, 90),   # green, top-left
        (215, 70, 70),   # red, top-right
        (235, 195, 40),  # yellow, bottom-left
        (60, 120, 215),  # blue, bottom-right
    ]
    cell = 104
    gap = 12
    grid_w = cell * 2 + gap
    start_x = (SIZE - grid_w) // 2
    start_y = (SIZE - grid_w) // 2
    for i, color in enumerate(quad_colors):
        row, col = divmod(i, 2)
        rect = pygame.Rect(
            start_x + col * (cell + gap), start_y + row * (cell + gap), cell, cell
        )
        pygame.draw.rect(surf, color, rect, border_radius=20)
        pygame.draw.rect(surf, (255, 255, 255), rect, width=4, border_radius=20)
    # highlight ring on the top-right (red) panel to suggest "lit up"
    lit_rect = pygame.Rect(start_x + cell + gap, start_y, cell, cell)
    glow = pygame.Surface((cell + 24, cell + 24), pygame.SRCALPHA)
    pygame.draw.rect(glow, (255, 255, 255, 130), glow.get_rect(), border_radius=26)
    surf.blit(glow, (lit_rect.left - 12, lit_rect.top - 12))
    pygame.draw.rect(surf, (255, 150, 150), lit_rect, border_radius=20)
    pygame.draw.rect(surf, (255, 255, 255), lit_rect, width=4, border_radius=20)
    pygame.image.save(surf, str(OUT / "simon_pattern.png"))


draw_letters_icon()
draw_sight_words_icon()
draw_shapes_icon()
draw_counting_icon()
draw_colors_icon()
draw_math_icon()
draw_maze_icon()
draw_simon_pattern_icon()
print("done")
