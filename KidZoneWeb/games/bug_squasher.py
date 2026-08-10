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
except ImportError:  # standalone `python games/bug_squasher.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common import sfx

WIDTH, HEIGHT = 900, 700
BG_COLOR = (225, 235, 200)
TEXT_COLOR = (50, 50, 60)
TITLE_COLOR = (60, 60, 90)

ROUND_SECONDS = 30
BUG_RADIUS = 24
MIN_SPEED, MAX_SPEED = 1.4, 3.2
SPAWN_MIN_MS = 300
SPAWN_MAX_MS = 750

BUG_COLORS = [
    (90, 70, 170),
    (170, 60, 60),
    (60, 140, 90),
    (200, 130, 40),
]
SQUASH_FLASH_MS = 200

# ---------------- HOME BUTTON ----------------
HOME_BUTTON_RECT = pygame.Rect(20, 20, 60, 50)
HOME_BUTTON_COLOR = (70, 60, 45)
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


# ---------------- GARDEN BACKGROUND ----------------
GRASS_DARK = (195, 215, 165)
GRASS_LIGHT = (240, 248, 218)
DIRT_PATCH = (205, 185, 145)
FLOWER_CENTER = (255, 210, 90)


def build_background_surface():
    surface = pygame.Surface((WIDTH, HEIGHT))
    surface.fill(BG_COLOR)
    rng = random.Random(4242)

    for cx, cy in ((160, 470), (420, 560), (700, 500), (250, 260), (650, 220)):
        pygame.draw.ellipse(surface, DIRT_PATCH, (cx - 50, cy - 24, 100, 48))

    for _ in range(650):
        bx = rng.randint(0, WIDTH)
        by = rng.randint(0, HEIGHT)
        blade_h = rng.randint(6, 14)
        color = rng.choice((GRASS_DARK, GRASS_LIGHT))
        pygame.draw.line(
            surface, color, (bx, by), (bx + rng.randint(-3, 3), by - blade_h), 2
        )

    flower_spots = [(90, 620), (320, 655), (600, 615), (820, 645), (140, 190), (770, 200)]
    for x, y in flower_spots:
        for dx, dy in ((0, 0), (-9, 4), (9, 4), (0, -8)):
            pygame.draw.circle(surface, (255, 255, 255), (x + dx, y + dy), 6)
        pygame.draw.circle(surface, FLOWER_CENTER, (x, y + 1), 4)

    return surface


BACKGROUND_SURFACE = build_background_surface()


# ---------------- SQUASH PARTICLES ----------------
PARTICLE_COLORS = [(120, 200, 90), (90, 160, 70), (210, 225, 130), (150, 180, 60)]


def spawn_squash_burst(particles, x, y):
    for _ in range(16):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.5, 5.0)
        particles.append(
            {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 1.5,
                "color": random.choice(PARTICLE_COLORS),
                "size": random.randint(3, 6),
                "life": random.uniform(400, 700),
                "age": 0.0,
            }
        )


def update_particles(particles, dt_ms):
    for p in particles:
        p["age"] += dt_ms
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.15
    particles[:] = [p for p in particles if p["age"] < p["life"]]


def draw_particles(screen, particles):
    for p in particles:
        t = p["age"] / p["life"]
        alpha = max(0, int(255 * (1 - t)))
        size = p["size"]
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*p["color"], alpha), (size, size), size)
        screen.blit(surf, (p["x"] - size, p["y"] - size))


def draw_milestone(screen, font, text, alpha):
    surf = font.render(text, True, (255, 255, 255))
    rect = surf.get_rect(center=(WIDTH // 2, 185))
    bg = rect.inflate(44, 24)
    panel = pygame.Surface(bg.size, pygame.SRCALPHA)
    a = max(0, min(255, alpha))
    pygame.draw.rect(panel, (70, 140, 70, min(230, a)), panel.get_rect(), border_radius=16)
    pygame.draw.rect(panel, (255, 255, 255, a), panel.get_rect(), 3, border_radius=16)
    screen.blit(panel, bg.topleft)
    surf.set_alpha(a)
    screen.blit(surf, rect)


class Bug:
    def __init__(self):
        edge = random.choice(["top", "bottom", "left", "right"])
        if edge == "top":
            self.x, self.y = random.uniform(0, WIDTH), -BUG_RADIUS
        elif edge == "bottom":
            self.x, self.y = random.uniform(0, WIDTH), HEIGHT + BUG_RADIUS
        elif edge == "left":
            self.x, self.y = -BUG_RADIUS, random.uniform(0, HEIGHT)
        else:
            self.x, self.y = WIDTH + BUG_RADIUS, random.uniform(0, HEIGHT)

        target_x = random.uniform(WIDTH * 0.2, WIDTH * 0.8)
        target_y = random.uniform(HEIGHT * 0.2, HEIGHT * 0.8)
        angle = math.atan2(target_y - self.y, target_x - self.x)
        angle += random.uniform(-0.4, 0.4)
        speed = random.uniform(MIN_SPEED, MAX_SPEED)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = random.choice(BUG_COLORS)
        self.wiggle_phase = random.uniform(0, 6.28)
        self.squashed = False
        self.squash_at = 0
        self.leg_offset = 0.0

    def update(self, now):
        if self.squashed:
            return
        self.leg_offset = math.sin(now / 60.0 + self.wiggle_phase)
        self.x += self.vx + self.leg_offset * 0.6
        self.y += self.vy

    def off_screen(self):
        margin = BUG_RADIUS * 3
        return (
            self.x < -margin
            or self.x > WIDTH + margin
            or self.y < -margin
            or self.y > HEIGHT + margin
        )

    def contains(self, pos):
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return dx * dx + dy * dy <= BUG_RADIUS * BUG_RADIUS

    def draw(self, screen, now):
        if self.squashed:
            t = (now - self.squash_at) / SQUASH_FLASH_MS
            if t > 1:
                return
            radius = int(BUG_RADIUS * (1 + t))
            alpha_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                alpha_surf,
                (255, 255, 255, int(180 * (1 - t))),
                (radius, radius),
                radius,
            )
            screen.blit(alpha_surf, (self.x - radius, self.y - radius))
            return

        angle = math.atan2(self.vy, self.vx)
        body_len = BUG_RADIUS * 1.4
        for i in range(3):
            leg_a = angle + math.pi / 2 + self.leg_offset * 0.3
            leg_b = angle - math.pi / 2 - self.leg_offset * 0.3
            offset = (i - 1) * 10
            base_x = self.x - math.cos(angle) * offset
            base_y = self.y - math.sin(angle) * offset
            pygame.draw.line(
                screen,
                (40, 40, 40),
                (base_x, base_y),
                (base_x + math.cos(leg_a) * 16, base_y + math.sin(leg_a) * 16),
                3,
            )
            pygame.draw.line(
                screen,
                (40, 40, 40),
                (base_x, base_y),
                (base_x + math.cos(leg_b) * 16, base_y + math.sin(leg_b) * 16),
                3,
            )

        body_rect = pygame.Rect(0, 0, body_len, BUG_RADIUS * 1.1)
        body_rect.center = (self.x, self.y)
        pygame.draw.ellipse(screen, self.color, body_rect)
        pygame.draw.line(
            screen,
            (25, 25, 25),
            body_rect.midtop,
            body_rect.midbottom,
            2,
        )

        head_x = self.x + math.cos(angle) * body_len / 2
        head_y = self.y + math.sin(angle) * body_len / 2
        pygame.draw.circle(screen, (25, 25, 25), (int(head_x), int(head_y)), 8)


async def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
    if platform is not None and hasattr(platform, "window"):
        try:
            platform.window.window_resize()
        except Exception:
            pass
    pygame.display.set_caption("Bug Squasher")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 64, bold=True)
    subtitle_font = pygame.font.SysFont(None, 30)
    hud_font = pygame.font.SysFont(None, 40, bold=True)
    big_font = pygame.font.SysFont(None, 72, bold=True)
    milestone_font = pygame.font.SysFont(None, 46, bold=True)

    def new_game():
        return [], 0, pygame.time.get_ticks() + ROUND_SECONDS * 1000, pygame.time.get_ticks()

    bugs, score, end_time, next_spawn_at = new_game()
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
                    bugs, score, end_time, next_spawn_at = new_game()
                    game_over = False
                    particles = []
                    streak = 0
                    new_best = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HOME_BUTTON_RECT.collidepoint(event.pos):
                    running = False
                elif game_over:
                    bugs, score, end_time, next_spawn_at = new_game()
                    game_over = False
                    particles = []
                    streak = 0
                    new_best = False
                else:
                    hit = False
                    for bug in bugs:
                        if not bug.squashed and bug.contains(event.pos):
                            bug.squashed = True
                            bug.squash_at = now
                            score += 1
                            sfx.good()
                            streak += 1
                            spawn_squash_burst(particles, bug.x, bug.y)
                            if streak >= 3 and streak % 5 == 0:
                                milestone_text = f"{streak} squash streak!"
                                milestone_until = now + 1400
                            hit = True
                            break
                    if not hit:
                        streak = 0

        if not game_over:
            if now >= next_spawn_at:
                bugs.append(Bug())
                next_spawn_at = now + random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS)

            for bug in bugs:
                bug.update(now)

            bugs = [
                b
                for b in bugs
                if not b.off_screen()
                and (not b.squashed or now - b.squash_at < SQUASH_FLASH_MS)
            ]

            update_particles(particles, clock.get_time())

            if now >= end_time:
                game_over = True
                if score > best_score:
                    best_score = score
                    new_best = True

        screen.blit(BACKGROUND_SURFACE, (0, 0))

        title_surf = title_font.render("Bug Squasher", True, TITLE_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        subtitle_surf = subtitle_font.render(
            "Click the bugs before they scurry away!", True, (70, 80, 60)
        )
        screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        for bug in bugs:
            bug.draw(screen, now)

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
            pygame.draw.rect(panel_surf, (250, 250, 240, 235), panel_surf.get_rect(), border_radius=24)
            pygame.draw.rect(panel_surf, (90, 140, 70, 255), panel_surf.get_rect(), 5, border_radius=24)
            screen.blit(panel_surf, panel.topleft)

            done_surf = big_font.render(f"Score: {score}", True, (60, 60, 90))
            screen.blit(done_surf, done_surf.get_rect(center=(panel.centerx, panel.top + 70)))

            best_surf = hud_font.render(f"Best: {best_score}", True, (70, 90, 60))
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
        clock.tick(60)
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(run())
