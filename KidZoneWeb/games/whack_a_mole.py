import asyncio
import math
import random

from pathlib import Path

import pygame

try:
    import platform
except ImportError:
    platform = None

try:
    from .common import sfx
    from .common import display
    from .common import text
except ImportError:  # standalone `python games/whack_a_mole.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common import sfx
    from common import display
    from common import text

WIDTH, HEIGHT = 900, 700
BG_COLOR = (140, 200, 110)
HOLE_COLOR = (90, 60, 40)
HOLE_RIM_COLOR = (60, 40, 25)
TEXT_COLOR = (50, 50, 60)
TITLE_COLOR = (60, 60, 90)

ROWS, COLS = 3, 3
HOLE_RADIUS = 70
GRID_GAP_X = 260
GRID_GAP_Y = 170
GRID_TOP = 260

ROUND_SECONDS = 30
MOLE_MIN_UP_MS = 550
MOLE_MAX_UP_MS = 1100
MOLE_MIN_GAP_MS = 400
MOLE_MAX_GAP_MS = 1200

MOLE_BODY = (120, 80, 55)
MOLE_BODY_DARK = (95, 60, 40)
MOLE_NOSE = (230, 150, 150)
WHACKED_COLOR = (230, 90, 90)

# ---------------- HOME BUTTON ----------------
HOME_BUTTON_RECT = pygame.Rect(20, 20, 60, 50)
HOME_BUTTON_COLOR = (80, 55, 40)
HOME_BUTTON_BORDER = (245, 245, 235)


def draw_home_button(screen):
    pygame.draw.rect(screen, HOME_BUTTON_COLOR, HOME_BUTTON_RECT, border_radius=10)
    pygame.draw.rect(screen, HOME_BUTTON_BORDER, HOME_BUTTON_RECT, 2, border_radius=10)
    cx, cy = HOME_BUTTON_RECT.center
    roof = [(cx - 16, cy - 1), (cx, cy - 15), (cx + 16, cy - 1)]
    pygame.draw.polygon(screen, (255, 255, 255), roof)
    body = pygame.Rect(0, 0, 22, 15)
    body.midtop = (cx, cy - 2)
    pygame.draw.rect(screen, (255, 255, 255), body)


# ---------------- MEADOW BACKGROUND ----------------
GRASS_DARK = (115, 180, 90)
GRASS_LIGHT = (160, 215, 130)
SKY_COLOR = (170, 220, 235)
SUN_COLOR = (255, 230, 140)
CLOUD_COLOR = (255, 255, 255)

SKY_HEIGHT = 150


def build_background_surface():
    surface = pygame.Surface((WIDTH, HEIGHT))
    surface.fill(SKY_COLOR)
    pygame.draw.rect(surface, BG_COLOR, (0, SKY_HEIGHT, WIDTH, HEIGHT - SKY_HEIGHT))

    pygame.draw.circle(surface, SUN_COLOR, (WIDTH - 90, 70), 45)

    rng = random.Random(99)
    for _ in range(900):
        bx = rng.randint(0, WIDTH)
        by = rng.randint(SKY_HEIGHT, HEIGHT)
        blade_h = rng.randint(6, 13)
        color = rng.choice((GRASS_DARK, GRASS_LIGHT))
        pygame.draw.line(
            surface, color, (bx, by), (bx + rng.randint(-3, 3), by - blade_h), 2
        )

    return surface


BACKGROUND_SURFACE = build_background_surface()

CLOUD_DEFS = [(120, 90, 1.0, 6), (520, 60, 0.8, 4), (760, 105, 1.1, 8)]


def draw_clouds(screen, now):
    t = now / 1000.0
    for base_x, y, scale, speed in CLOUD_DEFS:
        x = (base_x + t * speed) % (WIDTH + 300) - 150
        for dx, dy, r in ((-30, 6, 22), (0, -6, 30), (32, 6, 24)):
            pygame.draw.circle(
                screen, CLOUD_COLOR, (int(x + dx * scale), int(y + dy * scale)), int(r * scale)
            )


# ---------------- WHACK PARTICLES ----------------
DIRT_COLORS = [(120, 85, 55), (95, 65, 40), (150, 110, 70)]
STAR_COLOR = (255, 220, 90)


def spawn_whack_burst(particles, x, y):
    for _ in range(14):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.5, 4.5)
        particles.append(
            {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 2.0,
                "color": random.choice(DIRT_COLORS),
                "size": random.randint(3, 6),
                "life": random.uniform(350, 600),
                "age": 0.0,
                "kind": "dirt",
            }
        )
    for _ in range(6):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(2.0, 4.0)
        particles.append(
            {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "color": STAR_COLOR,
                "size": random.randint(3, 5),
                "life": random.uniform(300, 500),
                "age": 0.0,
                "kind": "star",
            }
        )


def update_particles(particles, dt_ms):
    for p in particles:
        p["age"] += dt_ms
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        if p["kind"] == "dirt":
            p["vy"] += 0.18
    particles[:] = [p for p in particles if p["age"] < p["life"]]


def draw_particles(screen, particles):
    for p in particles:
        t = p["age"] / p["life"]
        alpha = max(0, int(255 * (1 - t)))
        size = p["size"]
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        if p["kind"] == "star":
            pygame.draw.polygon(
                surf,
                (*p["color"], alpha),
                [(size, 0), (size * 1.6, size * 1.6), (size, size * 2), (size * 0.4, size * 1.6)],
            )
        else:
            pygame.draw.circle(surf, (*p["color"], alpha), (size, size), size)
        screen.blit(surf, (p["x"] - size, p["y"] - size))


def draw_milestone(screen, font, text, alpha):
    surf = font.render_copy(text, True, (255, 255, 255))
    rect = surf.get_rect(center=(WIDTH // 2, 185))
    bg = rect.inflate(44, 24)
    panel = pygame.Surface(bg.size, pygame.SRCALPHA)
    a = max(0, min(255, alpha))
    pygame.draw.rect(panel, (150, 100, 40, min(230, a)), panel.get_rect(), border_radius=16)
    pygame.draw.rect(panel, (255, 255, 255, a), panel.get_rect(), 3, border_radius=16)
    screen.blit(panel, bg.topleft)
    surf.set_alpha(a)
    screen.blit(surf, rect)


class Hole:
    def __init__(self, center):
        self.center = center
        self.up = False
        self.whacked = False
        self.next_event_at = pygame.time.get_ticks() + random.randint(
            MOLE_MIN_GAP_MS, MOLE_MAX_GAP_MS
        )
        self.up_until = 0
        self.pop_scale = 1.0

    def update(self, now):
        if not self.up and now >= self.next_event_at:
            self.up = True
            self.whacked = False
            self.pop_scale = 0.2
            self.up_until = now + random.randint(MOLE_MIN_UP_MS, MOLE_MAX_UP_MS)
        elif self.up and now >= self.up_until:
            self.up = False
            self.next_event_at = now + random.randint(
                MOLE_MIN_GAP_MS, MOLE_MAX_GAP_MS
            )
        if self.pop_scale < 1.0:
            self.pop_scale = min(1.0, self.pop_scale + 0.18)

    def try_whack(self, pos, now):
        if not self.up or self.whacked:
            return False
        dx = pos[0] - self.center[0]
        dy = pos[1] - (self.center[1] - 25)
        if dx * dx + dy * dy <= HOLE_RADIUS * HOLE_RADIUS:
            self.whacked = True
            self.up = False
            self.next_event_at = now + random.randint(
                MOLE_MIN_GAP_MS, MOLE_MAX_GAP_MS
            )
            return True
        return False

    def draw(self, screen):
        pygame.draw.ellipse(
            screen,
            HOLE_RIM_COLOR,
            (
                self.center[0] - HOLE_RADIUS - 6,
                self.center[1] - 22,
                (HOLE_RADIUS + 6) * 2,
                70,
            ),
        )
        if self.up:
            body_color = WHACKED_COLOR if self.whacked else MOLE_BODY
            dark_color = MOLE_BODY_DARK
            scale = self.pop_scale
            head_center = (self.center[0], self.center[1] - 25 + (1 - scale) * 30)
            pygame.draw.circle(screen, body_color, head_center, int((HOLE_RADIUS - 10) * scale))
            ear_r = int(16 * scale)
            pygame.draw.circle(
                screen, dark_color, (head_center[0] - 40, head_center[1] - 45), ear_r
            )
            pygame.draw.circle(
                screen, dark_color, (head_center[0] + 40, head_center[1] - 45), ear_r
            )
            eye_y = head_center[1] - 8
            pygame.draw.circle(screen, (30, 30, 30), (head_center[0] - 18, eye_y), int(6 * scale))
            pygame.draw.circle(screen, (30, 30, 30), (head_center[0] + 18, eye_y), int(6 * scale))
            pygame.draw.ellipse(
                screen,
                MOLE_NOSE,
                (head_center[0] - 14, head_center[1] + 8, 28, 18),
            )
        pygame.draw.ellipse(
            screen,
            HOLE_COLOR,
            (
                self.center[0] - HOLE_RADIUS,
                self.center[1] - 15,
                HOLE_RADIUS * 2,
                55,
            ),
        )


def build_holes():
    holes = []
    grid_w = (COLS - 1) * GRID_GAP_X
    start_x = (WIDTH - grid_w) // 2
    for row in range(ROWS):
        for col in range(COLS):
            x = start_x + col * GRID_GAP_X
            y = GRID_TOP + row * GRID_GAP_Y
            holes.append(Hole((x, y)))
    return holes


async def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
    if platform is not None and hasattr(platform, "window"):
        try:
            platform.window.window_resize()
        except Exception:
            pass
    pygame.display.set_caption("Whack-a-Mole")
    clock = pygame.time.Clock()

    title_font = text.SysFont(None, 64, bold=True)
    subtitle_font = text.SysFont(None, 30)
    hud_font = text.SysFont(None, 40, bold=True)
    big_font = text.SysFont(None, 72, bold=True)
    milestone_font = text.SysFont(None, 46, bold=True)

    def new_game():
        return build_holes(), 0, pygame.time.get_ticks() + ROUND_SECONDS * 1000

    holes, score, end_time = new_game()
    game_over = False
    running = True

    particles = []
    streak = 0
    best_score = 0
    new_best = False
    milestone_text = None
    milestone_until = 0

    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif game_over and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    holes, score, end_time = new_game()
                    game_over = False
                    particles = []
                    streak = 0
                    new_best = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HOME_BUTTON_RECT.collidepoint(event.pos):
                    running = False
                elif game_over:
                    holes, score, end_time = new_game()
                    game_over = False
                    particles = []
                    streak = 0
                    new_best = False
                else:
                    hit_hole = None
                    for hole in holes:
                        if hole.try_whack(event.pos, now):
                            hit_hole = hole
                            break
                    if hit_hole is not None:
                        score += 1
                        sfx.good()
                        streak += 1
                        spawn_whack_burst(particles, hit_hole.center[0], hit_hole.center[1] - 40)
                        if streak >= 3 and streak % 3 == 0:
                            milestone_text = f"{streak} in a row!"
                            milestone_until = now + 1400
                    else:
                        streak = 0

        if not game_over:
            for hole in holes:
                hole.update(now)
            update_particles(particles, clock.get_time())
            if now >= end_time:
                game_over = True
                if score > best_score:
                    best_score = score
                    new_best = True

        screen.blit(BACKGROUND_SURFACE, (0, 0))
        draw_clouds(screen, now)

        title_surf = title_font.render("Whack-a-Mole", True, TITLE_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        subtitle_surf = subtitle_font.render(
            "Click the moles before they hide!", True, (70, 70, 80)
        )
        screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        for hole in holes:
            hole.draw(screen)

        draw_particles(screen, particles)

        score_surf = hud_font.render(f"Score: {score}", True, TEXT_COLOR)
        screen.blit(score_surf, (30, 140))

        seconds_left = max(0, (end_time - now) // 1000 + (0 if game_over else 1))
        timer_surf = hud_font.render(f"Time: {seconds_left}", True, TEXT_COLOR)
        screen.blit(timer_surf, timer_surf.get_rect(topright=(WIDTH - 30, 140)))

        if milestone_text and now < milestone_until:
            remaining = milestone_until - now
            alpha = 255 if remaining > 300 else int(255 * remaining / 300)
            draw_milestone(screen, milestone_font, milestone_text, alpha)
        elif now >= milestone_until:
            milestone_text = None

        draw_home_button(screen)

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))

            panel = pygame.Rect(0, 0, 460, 260)
            panel.center = (WIDTH // 2, HEIGHT // 2)
            panel_surf = pygame.Surface(panel.size, pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (250, 245, 230, 235), panel_surf.get_rect(), border_radius=24)
            pygame.draw.rect(panel_surf, (120, 85, 55, 255), panel_surf.get_rect(), 5, border_radius=24)
            screen.blit(panel_surf, panel.topleft)

            done_surf = big_font.render(f"Score: {score}", True, (60, 60, 90))
            screen.blit(done_surf, done_surf.get_rect(center=(panel.centerx, panel.top + 70)))

            best_surf = hud_font.render(f"Best: {best_score}", True, (90, 65, 45))
            screen.blit(best_surf, best_surf.get_rect(center=(panel.centerx, panel.top + 125)))

            if new_best:
                nb_surf = subtitle_font.render("New Best!", True, (200, 130, 20))
                screen.blit(nb_surf, nb_surf.get_rect(center=(panel.centerx, panel.top + 160)))

            again_surf = subtitle_font.render(
                "Click or press Enter to play again", True, (70, 70, 80)
            )
            screen.blit(
                again_surf, again_surf.get_rect(center=(panel.centerx, panel.bottom - 30))
            )

        pygame.display.flip()

        _resized = display.maintain(WIDTH, HEIGHT)

        if _resized is not None:

            screen = _resized
        clock.tick(60)
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(run())
