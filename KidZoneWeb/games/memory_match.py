import asyncio
import math
import random

import pygame

WIDTH, HEIGHT = 900, 750
BG_COLOR = (245, 240, 250)
TABLE_COLOR = (228, 220, 245)
TEXT_COLOR = (50, 50, 60)
TITLE_COLOR = (60, 60, 90)

ROWS, COLS = 4, 4
CARD_W, CARD_H = 150, 150
CARD_GAP = 20
GRID_TOP = 190

CARD_BACK = (110, 100, 200)
CARD_BACK_DARK = (92, 82, 175)
CARD_FRONT = (255, 255, 255)
MATCH_COLOR = (140, 200, 120)
MISMATCH_COLOR = (225, 100, 100)

FLIP_BACK_DELAY_MS = 700
FLIP_SPEED = 6.0

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

HOME_BUTTON = pygame.Rect(20, 20, 60, 50)
HOME_BUTTON_COLOR = (110, 100, 200)
HOME_BUTTON_BORDER = (255, 255, 255)

CONFETTI_COLORS = [
    (230, 90, 110),
    (255, 190, 90),
    (90, 160, 230),
    (255, 210, 60),
    (220, 110, 150),
    (20, 150, 140),
    (150, 80, 190),
]
STREAK_MILESTONE_EVERY = 3
MILESTONE_MS = 1200


def draw_home_button(screen):
    pygame.draw.rect(screen, HOME_BUTTON_COLOR, HOME_BUTTON, border_radius=10)
    pygame.draw.rect(screen, HOME_BUTTON_BORDER, HOME_BUTTON, width=2, border_radius=10)

    rect = HOME_BUTTON
    roof = [
        (rect.centerx, rect.top + 8),
        (rect.left + 10, rect.top + 26),
        (rect.right - 10, rect.top + 26),
    ]
    pygame.draw.polygon(screen, (255, 255, 255), roof)

    body = pygame.Rect(0, 0, rect.width - 28, rect.height - 26)
    body.midtop = (rect.centerx, rect.top + 24)
    pygame.draw.rect(screen, (255, 255, 255), body, border_radius=2)

    door = pygame.Rect(0, 0, body.width * 0.34, body.height * 0.55)
    door.midbottom = body.midbottom
    pygame.draw.rect(screen, HOME_BUTTON_COLOR, door, border_radius=1)


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
        self.pop = 0.0
        self.anim_t = 1.0
        self.anim_from = False
        self.mismatch_active = False

    def start_flip(self, new_face_up):
        if new_face_up != self.face_up:
            self.anim_from = self.face_up
            self.face_up = new_face_up
            self.anim_t = 0.0

    def update(self, dt):
        if self.anim_t < 1.0:
            self.anim_t = min(1.0, self.anim_t + dt * FLIP_SPEED)
        if self.pop > 0:
            self.pop += dt * 2.2
            if self.pop >= 1:
                self.pop = 0

    def draw(self, screen, now):
        shown_face_up = self.anim_from if self.anim_t < 0.5 else self.face_up
        scale_x = max(0.08, abs(math.cos(self.anim_t * math.pi)))

        offset_x, offset_y = 0, 0
        if self.mismatch_active:
            offset_x = int(math.sin(now / 30.0) * 4)

        draw_rect = self.rect.move(offset_x, offset_y)
        if self.pop > 0:
            grow = int(6 * math.sin(self.pop * math.pi))
            draw_rect = draw_rect.inflate(grow, grow)

        w = max(4, int(draw_rect.width * scale_x))
        scaled_rect = pygame.Rect(0, 0, w, draw_rect.height)
        scaled_rect.center = draw_rect.center

        if self.matched:
            color = MATCH_COLOR
        elif self.mismatch_active and shown_face_up:
            color = MISMATCH_COLOR
        else:
            color = CARD_FRONT if shown_face_up else CARD_BACK

        pygame.draw.rect(screen, color, scaled_rect, border_radius=14)

        if not shown_face_up and not self.matched and scale_x > 0.3:
            inner = scaled_rect.inflate(-24, -24)
            if inner.width > 4 and inner.height > 4:
                pygame.draw.rect(screen, CARD_BACK_DARK, inner, width=4, border_radius=10)
                pygame.draw.circle(screen, CARD_BACK_DARK, inner.center, 14, width=3)

        pygame.draw.rect(screen, (255, 255, 255), scaled_rect, width=3, border_radius=14)

        if (shown_face_up or self.matched) and scale_x > 0.25:
            draw_shape(screen, self.shape, scaled_rect.center, int(70 * min(1.0, scale_x * 1.6)), SHAPE_COLORS[self.shape])


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


def draw_background(screen):
    screen.fill(BG_COLOR)
    grid_w = COLS * CARD_W + (COLS - 1) * CARD_GAP
    grid_h = ROWS * CARD_H + (ROWS - 1) * CARD_GAP
    table_rect = pygame.Rect(0, 0, grid_w + 60, grid_h + 60)
    table_rect.center = (WIDTH // 2, GRID_TOP + grid_h // 2)
    pygame.draw.rect(screen, TABLE_COLOR, table_rect, border_radius=28)

    dot_rng = random.Random(7)
    for _ in range(40):
        x = dot_rng.randint(20, WIDTH - 20)
        y = dot_rng.randint(20, HEIGHT - 20)
        if table_rect.collidepoint(x, y):
            continue
        pygame.draw.circle(screen, (235, 228, 250), (x, y), 5)


def spawn_confetti(particles, cx, cy, count=18):
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(100, 300)
        particles.append(
            {
                "x": cx,
                "y": cy,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - random.uniform(60, 160),
                "age": 0.0,
                "life": random.uniform(0.6, 1.1),
                "color": random.choice(CONFETTI_COLORS),
                "size": random.randint(4, 8),
                "angle": random.uniform(0, 360),
                "spin": random.uniform(-300, 300),
            }
        )


def update_particles(particles, dt):
    for p in particles:
        p["age"] += dt
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        p["vy"] += 380 * dt
        p["angle"] += p["spin"] * dt
    particles[:] = [p for p in particles if p["age"] < p["life"]]


def draw_particles(screen, particles):
    for p in particles:
        t = p["age"] / p["life"]
        alpha = max(0, int(255 * (1 - t)))
        size = p["size"]
        piece = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.rect(piece, (*p["color"], alpha), (0, 0, size * 2, size * 2), border_radius=2)
        rotated = pygame.transform.rotate(piece, p["angle"])
        rect = rotated.get_rect(center=(p["x"], p["y"]))
        screen.blit(rotated, rect)


def spawn_shockwave(shockwaves, x, y, color):
    shockwaves.append({"x": x, "y": y, "color": color, "age": 0.0, "life": 0.3, "max_r": 90})


def update_shockwaves(shockwaves, dt):
    for s in shockwaves:
        s["age"] += dt
    shockwaves[:] = [s for s in shockwaves if s["age"] < s["life"]]


def draw_shockwaves(screen, shockwaves):
    for s in shockwaves:
        t = min(1.0, s["age"] / s["life"])
        r = max(2, int(10 + (s["max_r"] - 10) * (1 - (1 - t) * (1 - t))))
        alpha = max(0, int(180 * (1 - t)))
        width = max(1, int(5 * (1 - t)) + 1)
        surf = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*s["color"], alpha), (r + 4, r + 4), r, width=width)
        screen.blit(surf, (s["x"] - r - 4, s["y"] - r - 4))


def draw_milestone(screen, font, text):
    banner = font.render(text, True, (110, 90, 30))
    rect = banner.get_rect(center=(WIDTH // 2, 130))
    bg_rect = rect.inflate(40, 22)
    pygame.draw.rect(screen, (255, 250, 230), bg_rect, border_radius=16)
    pygame.draw.rect(screen, (235, 190, 60), bg_rect, width=3, border_radius=16)
    screen.blit(banner, rect)


async def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("Memory Match")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 64, bold=True)
    subtitle_font = pygame.font.SysFont(None, 30)
    hud_font = pygame.font.SysFont(None, 40, bold=True)
    big_font = pygame.font.SysFont(None, 64, bold=True)
    milestone_font = pygame.font.SysFont(None, 38, bold=True)

    particles = []
    shockwaves = []
    best_moves = None

    def new_game():
        return build_cards(), [], 0, None

    cards, open_cards, moves, resolve_at = new_game()
    won = False
    running = True
    match_streak = 0
    milestone_text = None
    milestone_until = 0
    new_best = False

    while running:
        now = pygame.time.get_ticks()
        dt = clock.get_time() / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif won and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    cards, open_cards, moves, resolve_at = new_game()
                    won = False
                    match_streak = 0
                    milestone_text = None
                    new_best = False
                    particles, shockwaves = [], []
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HOME_BUTTON.collidepoint(event.pos):
                    running = False
                elif won:
                    cards, open_cards, moves, resolve_at = new_game()
                    won = False
                    match_streak = 0
                    milestone_text = None
                    new_best = False
                    particles, shockwaves = [], []
                elif resolve_at is None and len(open_cards) < 2:
                    for card in cards:
                        if (
                            not card.face_up
                            and not card.matched
                            and card.rect.collidepoint(event.pos)
                        ):
                            card.start_flip(True)
                            open_cards.append(card)
                            if len(open_cards) == 2:
                                moves += 1
                                if open_cards[0].shape == open_cards[1].shape:
                                    open_cards[0].matched = True
                                    open_cards[1].matched = True
                                    open_cards[0].pop = 0.001
                                    open_cards[1].pop = 0.001
                                    spawn_confetti(
                                        particles,
                                        open_cards[0].rect.centerx,
                                        open_cards[0].rect.centery,
                                    )
                                    spawn_shockwave(
                                        shockwaves,
                                        open_cards[0].rect.centerx,
                                        open_cards[0].rect.centery,
                                        MATCH_COLOR,
                                    )
                                    match_streak += 1
                                    if match_streak >= STREAK_MILESTONE_EVERY:
                                        milestone_text = f"{match_streak} matches in a row!"
                                        milestone_until = now + MILESTONE_MS
                                    open_cards = []
                                    if all(c.matched for c in cards):
                                        won = True
                                        spawn_confetti(
                                            particles, WIDTH // 2, HEIGHT // 2, count=90
                                        )
                                        if best_moves is None or moves < best_moves:
                                            best_moves = moves
                                            new_best = True
                                else:
                                    match_streak = 0
                                    open_cards[0].mismatch_active = True
                                    open_cards[1].mismatch_active = True
                                    resolve_at = now + FLIP_BACK_DELAY_MS
                            break

        if resolve_at is not None and now >= resolve_at:
            for card in open_cards:
                card.start_flip(False)
                card.mismatch_active = False
            open_cards = []
            resolve_at = None

        for card in cards:
            card.update(dt)

        update_particles(particles, dt)
        update_shockwaves(shockwaves, dt)

        draw_background(screen)

        title_surf = title_font.render("Memory Match", True, TITLE_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        subtitle_surf = subtitle_font.render(
            "Flip two cards to find a matching pair!", True, (90, 90, 110)
        )
        screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        draw_shockwaves(screen, shockwaves)

        for card in cards:
            card.draw(screen, now)

        draw_particles(screen, particles)

        moves_surf = hud_font.render(f"Moves: {moves}", True, TEXT_COLOR)
        screen.blit(moves_surf, (30, 140))

        if best_moves is not None:
            best_surf = hud_font.render(f"Best: {best_moves}", True, TEXT_COLOR)
            screen.blit(best_surf, best_surf.get_rect(topright=(WIDTH - 30, 140)))

        if milestone_text and now < milestone_until:
            draw_milestone(screen, milestone_font, milestone_text)
        elif now >= milestone_until:
            milestone_text = None

        if won:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))
            draw_particles(screen, particles)
            done_surf = big_font.render(f"Matched in {moves} moves!", True, (255, 255, 255))
            screen.blit(done_surf, done_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
            if new_best:
                best_line = subtitle_font.render("New Best!", True, (255, 220, 120))
                screen.blit(best_line, best_line.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 14)))
            again_surf = subtitle_font.render(
                "Click or press Enter to play again", True, (230, 230, 230)
            )
            screen.blit(
                again_surf, again_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 56))
            )

        draw_home_button(screen)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(run())
