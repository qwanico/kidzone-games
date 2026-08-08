import asyncio
import math
import random

import pygame

WIDTH, HEIGHT = 900, 750
BG_COLOR = (245, 240, 250)
TEXT_COLOR = (50, 50, 60)
TITLE_COLOR = (60, 60, 90)

ROWS, COLS = 4, 4
CARD_W, CARD_H = 150, 150
CARD_GAP = 20
GRID_TOP = 190

CARD_BACK = (110, 100, 200)
CARD_FRONT = (255, 255, 255)
MATCH_COLOR = (140, 200, 120)

FLIP_BACK_DELAY_MS = 700

SHAPES = ["circle", "square", "triangle", "star", "heart", "diamond", "cross", "hexagon"]
SHAPE_COLORS = {
    "circle": (230, 90, 110),
    "square": (255, 190, 90),
    "triangle": (90, 160, 230),
    "star": (255, 210, 60),
    "heart": (220, 110, 150),
    "diamond": (20, 150, 140),
    "cross": (150, 80, 190),
    "hexagon": (120, 180, 40),
}


def draw_shape(surf, shape, center, size, color):
    if shape == "circle":
        pygame.draw.circle(surf, color, center, size // 2)
    elif shape == "square":
        rect = pygame.Rect(0, 0, size, size)
        rect.center = center
        pygame.draw.rect(surf, color, rect, border_radius=10)
    elif shape == "triangle":
        h = size
        pts = [
            (center[0], center[1] - h / 2),
            (center[0] - h / 2, center[1] + h / 2),
            (center[0] + h / 2, center[1] + h / 2),
        ]
        pygame.draw.polygon(surf, color, pts)
    elif shape == "star":
        points = []
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5
            r = size / 2 if i % 2 == 0 else size / 4.5
            points.append((center[0] + math.cos(angle) * r, center[1] - math.sin(angle) * r))
        pygame.draw.polygon(surf, color, points)
    elif shape == "heart":
        r = size // 4
        pygame.draw.circle(surf, color, (center[0] - r, center[1] - r // 2), r)
        pygame.draw.circle(surf, color, (center[0] + r, center[1] - r // 2), r)
        pts = [
            (center[0] - size / 2, center[1] - r // 4),
            (center[0] + size / 2, center[1] - r // 4),
            (center[0], center[1] + size / 2),
        ]
        pygame.draw.polygon(surf, color, pts)
    elif shape == "diamond":
        pts = [
            (center[0], center[1] - size / 2),
            (center[0] + size / 2, center[1]),
            (center[0], center[1] + size / 2),
            (center[0] - size / 2, center[1]),
        ]
        pygame.draw.polygon(surf, color, pts)
    elif shape == "cross":
        thick = size // 3
        rect1 = pygame.Rect(0, 0, thick, size)
        rect1.center = center
        rect2 = pygame.Rect(0, 0, size, thick)
        rect2.center = center
        pygame.draw.rect(surf, color, rect1, border_radius=6)
        pygame.draw.rect(surf, color, rect2, border_radius=6)
    elif shape == "hexagon":
        points = []
        for i in range(6):
            angle = math.pi / 6 + i * math.pi / 3
            points.append(
                (center[0] + math.cos(angle) * size / 2, center[1] + math.sin(angle) * size / 2)
            )
        pygame.draw.polygon(surf, color, points)


class Card:
    def __init__(self, shape, rect):
        self.shape = shape
        self.rect = rect
        self.face_up = False
        self.matched = False

    def draw(self, screen):
        color = MATCH_COLOR if self.matched else (CARD_FRONT if self.face_up else CARD_BACK)
        pygame.draw.rect(screen, color, self.rect, border_radius=14)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, width=3, border_radius=14)
        if self.face_up or self.matched:
            draw_shape(screen, self.shape, self.rect.center, 70, SHAPE_COLORS[self.shape])


def build_cards():
    shapes = SHAPES * 2
    random.shuffle(shapes)
    grid_w = COLS * CARD_W + (COLS - 1) * CARD_GAP
    start_x = (WIDTH - grid_w) // 2
    cards = []
    for i, shape in enumerate(shapes):
        row, col = divmod(i, COLS)
        x = start_x + col * (CARD_W + CARD_GAP)
        y = GRID_TOP + row * (CARD_H + CARD_GAP)
        cards.append(Card(shape, pygame.Rect(x, y, CARD_W, CARD_H)))
    return cards


async def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Memory Match")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 64, bold=True)
    subtitle_font = pygame.font.SysFont(None, 30)
    hud_font = pygame.font.SysFont(None, 40, bold=True)
    big_font = pygame.font.SysFont(None, 64, bold=True)

    def new_game():
        return build_cards(), [], 0, None

    cards, open_cards, moves, resolve_at = new_game()
    won = False
    running = True

    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif won and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    cards, open_cards, moves, resolve_at = new_game()
                    won = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if won:
                    cards, open_cards, moves, resolve_at = new_game()
                    won = False
                elif resolve_at is None and len(open_cards) < 2:
                    for card in cards:
                        if (
                            not card.face_up
                            and not card.matched
                            and card.rect.collidepoint(event.pos)
                        ):
                            card.face_up = True
                            open_cards.append(card)
                            if len(open_cards) == 2:
                                moves += 1
                                if open_cards[0].shape == open_cards[1].shape:
                                    open_cards[0].matched = True
                                    open_cards[1].matched = True
                                    open_cards = []
                                    if all(c.matched for c in cards):
                                        won = True
                                else:
                                    resolve_at = now + FLIP_BACK_DELAY_MS
                            break

        if resolve_at is not None and now >= resolve_at:
            for card in open_cards:
                card.face_up = False
            open_cards = []
            resolve_at = None

        screen.fill(BG_COLOR)

        title_surf = title_font.render("Memory Match", True, TITLE_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        subtitle_surf = subtitle_font.render(
            "Flip two cards to find a matching pair!", True, (90, 90, 110)
        )
        screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        for card in cards:
            card.draw(screen)

        moves_surf = hud_font.render(f"Moves: {moves}", True, TEXT_COLOR)
        screen.blit(moves_surf, (30, 140))

        if won:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))
            done_surf = big_font.render(f"Matched in {moves} moves!", True, (255, 255, 255))
            screen.blit(done_surf, done_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            again_surf = subtitle_font.render(
                "Click or press Enter to play again", True, (230, 230, 230)
            )
            screen.blit(
                again_surf, again_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
            )

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(run())
