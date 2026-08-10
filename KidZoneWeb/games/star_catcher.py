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
except ImportError:  # standalone `python games/star_catcher.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common import sfx

WIDTH, HEIGHT = 900, 700
BG_TOP = (25, 25, 60)
BG_BOTTOM = (60, 50, 110)
TEXT_COLOR = (255, 255, 255)
TITLE_COLOR = (255, 255, 255)

BASKET_W, BASKET_H = 130, 46
BASKET_Y = HEIGHT - 70
BASKET_COLOR = (200, 140, 60)

STAR_COLOR = (255, 220, 90)
ROCK_COLOR = (110, 110, 120)
ITEM_RADIUS = 24
ROCK_CHANCE = 0.28
MIN_SPEED, MAX_SPEED = 2.4, 5.0
SPAWN_MIN_MS = 300
SPAWN_MAX_MS = 700

START_LIVES = 3

HOME_BUTTON = pygame.Rect(20, 20, 60, 50)
HOME_BUTTON_COLOR = (80, 70, 140)
HOME_BUTTON_BORDER = (255, 255, 255)

SPARKLE_COLORS = [(255, 230, 120), (255, 255, 255), (255, 200, 90)]
STREAK_MILESTONE_EVERY = 5
MILESTONE_MS = 1200


def draw_star(screen, center, radius, color, glow=True):
    if glow:
        g = pygame.Surface((radius * 5, radius * 5), pygame.SRCALPHA)
        pygame.draw.circle(g, (*color, 55), (radius * 2.5, radius * 2.5), radius * 2.1)
        screen.blit(g, (center[0] - radius * 2.5, center[1] - radius * 2.5))
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = radius if i % 2 == 0 else radius * 0.45
        points.append((center[0] + math.cos(angle) * r, center[1] - math.sin(angle) * r))
    pygame.draw.polygon(screen, color, points)
    inner = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = (radius if i % 2 == 0 else radius * 0.45) * 0.55
        inner.append((center[0] + math.cos(angle) * r, center[1] - math.sin(angle) * r))
    pygame.draw.polygon(screen, (255, 255, 255), inner)


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


class FallingItem:
    def __init__(self):
        self.x = random.randint(ITEM_RADIUS, WIDTH - ITEM_RADIUS)
        self.y = -ITEM_RADIUS
        self.speed = random.uniform(MIN_SPEED, MAX_SPEED)
        self.is_rock = random.random() < ROCK_CHANCE
        self.caught = False
        self.spin = random.uniform(0, 6.28)
        self.trail_timer = 0.0

    def update(self):
        self.y += self.speed
        self.spin += 0.05

    def off_screen(self):
        return self.y > HEIGHT + ITEM_RADIUS

    def rect(self):
        return pygame.Rect(
            self.x - ITEM_RADIUS, self.y - ITEM_RADIUS, ITEM_RADIUS * 2, ITEM_RADIUS * 2
        )

    def draw(self, screen):
        if self.is_rock:
            pts = []
            for i in range(7):
                angle = self.spin + i * (2 * math.pi / 7)
                r = ITEM_RADIUS * (0.8 + 0.2 * math.sin(i * 2))
                pts.append((self.x + math.cos(angle) * r, self.y + math.sin(angle) * r))
            pygame.draw.polygon(screen, ROCK_COLOR, pts)
            pygame.draw.polygon(screen, (75, 75, 85), pts, width=2)
            crack_a = (self.x - ITEM_RADIUS * 0.2, self.y - ITEM_RADIUS * 0.3)
            crack_b = (self.x + ITEM_RADIUS * 0.1, self.y + ITEM_RADIUS * 0.2)
            crack_c = (self.x + ITEM_RADIUS * 0.35, self.y - ITEM_RADIUS * 0.1)
            pygame.draw.line(screen, (75, 75, 85), crack_a, crack_b, 2)
            pygame.draw.line(screen, (75, 75, 85), crack_b, crack_c, 2)
        else:
            draw_star(screen, (self.x, self.y), ITEM_RADIUS, STAR_COLOR)


def make_background_stars():
    stars = []
    for _ in range(70):
        stars.append(
            (
                random.uniform(0, WIDTH),
                random.uniform(0, HEIGHT * 0.65),
                random.uniform(1.0, 2.6),
                random.uniform(0, 6.28),
                random.uniform(0.6, 1.6),
            )
        )
    return stars


def draw_background(screen, bg_stars, now):
    for i in range(HEIGHT):
        t = i / HEIGHT
        color = tuple(
            int(BG_TOP[c] + (BG_BOTTOM[c] - BG_TOP[c]) * t) for c in range(3)
        )
        pygame.draw.line(screen, color, (0, i), (WIDTH, i))

    moon_center = (WIDTH - 110, 80)
    glow = pygame.Surface((180, 180), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 250, 220, 40), (90, 90), 90)
    screen.blit(glow, (moon_center[0] - 90, moon_center[1] - 90))
    pygame.draw.circle(screen, (245, 240, 210), moon_center, 42)
    pygame.draw.circle(screen, (225, 220, 190), (moon_center[0] - 12, moon_center[1] - 10), 8)
    pygame.draw.circle(screen, (225, 220, 190), (moon_center[0] + 14, moon_center[1] + 8), 6)
    pygame.draw.circle(screen, (225, 220, 190), (moon_center[0] + 4, moon_center[1] - 18), 5)

    for x, y, r, phase, speed in bg_stars:
        b = 150 + int(100 * (0.5 + 0.5 * math.sin(now / 500.0 * speed + phase)))
        color = (b, b, min(255, b + 30))
        pygame.draw.circle(screen, color, (int(x), int(y)), max(1, int(r)))


def draw_basket(screen, x, squash):
    w = BASKET_W * (1.0 + squash * 0.14)
    h = BASKET_H * (1.0 - squash * 0.18)
    rect = pygame.Rect(0, 0, w, h)
    rect.center = (x, BASKET_Y)
    pygame.draw.polygon(
        screen,
        BASKET_COLOR,
        [
            (rect.left + 10, rect.top),
            (rect.right - 10, rect.top),
            (rect.right, rect.bottom),
            (rect.left, rect.bottom),
        ],
    )
    pygame.draw.line(screen, (235, 195, 140), (rect.left + 12, rect.top + 3), (rect.right - 12, rect.top + 3), 3)
    for i in range(3):
        lx = rect.left + 20 + i * (rect.width - 40) / 2
        pygame.draw.line(screen, (150, 100, 40), (lx, rect.top + 6), (lx, rect.bottom - 6), 3)


def spawn_sparkles(particles, x, y):
    for _ in range(16):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(60, 190)
        particles.append(
            {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "age": 0.0,
                "life": random.uniform(0.35, 0.65),
                "color": random.choice(SPARKLE_COLORS),
                "size": random.uniform(2.5, 5.0),
            }
        )


def spawn_dust(particles, x, y):
    for _ in range(18):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(50, 160)
        particles.append(
            {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "age": 0.0,
                "life": random.uniform(0.3, 0.6),
                "color": random.choice([(90, 90, 100), (60, 60, 68), (130, 130, 140)]),
                "size": random.uniform(3.0, 6.5),
            }
        )


def update_particles(particles, dt):
    for p in particles:
        p["age"] += dt
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        p["vy"] += 220 * dt
    particles[:] = [p for p in particles if p["age"] < p["life"]]


def draw_particles(screen, particles):
    for p in particles:
        t = p["age"] / p["life"]
        alpha = max(0, int(255 * (1 - t)))
        size = max(1, int(p["size"]))
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*p["color"], alpha), (size, size), size)
        screen.blit(surf, (p["x"] - size, p["y"] - size))


def spawn_shockwave(shockwaves, x, y, color):
    shockwaves.append({"x": x, "y": y, "color": color, "age": 0.0, "life": 0.28, "max_r": 50})


def update_shockwaves(shockwaves, dt):
    for s in shockwaves:
        s["age"] += dt
    shockwaves[:] = [s for s in shockwaves if s["age"] < s["life"]]


def draw_shockwaves(screen, shockwaves):
    for s in shockwaves:
        t = min(1.0, s["age"] / s["life"])
        r = max(2, int(8 + (s["max_r"] - 8) * (1 - (1 - t) * (1 - t))))
        alpha = max(0, int(200 * (1 - t)))
        width = max(1, int(4 * (1 - t)) + 1)
        surf = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*s["color"], alpha), (r + 4, r + 4), r, width=width)
        screen.blit(surf, (s["x"] - r - 4, s["y"] - r - 4))


def spawn_poptext(poptexts, x, y, text, color):
    poptexts.append({"x": x, "y": y, "text": text, "color": color, "age": 0.0, "life": 0.65})


def update_poptexts(poptexts, dt):
    for p in poptexts:
        p["age"] += dt
        p["y"] -= 32 * dt
    poptexts[:] = [p for p in poptexts if p["age"] < p["life"]]


def draw_poptexts(screen, font, poptexts):
    for p in poptexts:
        t = p["age"] / p["life"]
        alpha = max(0, int(255 * (1 - t)))
        scale = 1.0 + 0.5 * min(1.0, p["age"] / 0.12)
        surf = font.render(p["text"], True, p["color"])
        w, h = surf.get_size()
        if abs(scale - 1.0) > 0.01:
            surf = pygame.transform.smoothscale(surf, (max(1, int(w * scale)), max(1, int(h * scale))))
        surf.set_alpha(alpha)
        screen.blit(surf, surf.get_rect(center=(p["x"], p["y"])))


def draw_milestone(screen, font, text):
    banner = font.render(text, True, (255, 235, 150))
    rect = banner.get_rect(center=(WIDTH // 2, 130))
    bg_rect = rect.inflate(40, 22)
    bg = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(bg, (40, 30, 80, 210), bg.get_rect(), border_radius=16)
    pygame.draw.rect(bg, (255, 220, 120, 255), bg.get_rect(), width=3, border_radius=16)
    screen.blit(bg, bg_rect)
    screen.blit(banner, rect)


async def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
    if platform is not None and hasattr(platform, "window"):
        try:
            platform.window.window_resize()
        except Exception:
            pass
    pygame.display.set_caption("Star Catcher")
    clock = pygame.time.Clock()
    frame = pygame.Surface((WIDTH, HEIGHT))

    title_font = pygame.font.SysFont(None, 64, bold=True)
    subtitle_font = pygame.font.SysFont(None, 30)
    hud_font = pygame.font.SysFont(None, 40, bold=True)
    big_font = pygame.font.SysFont(None, 72, bold=True)
    milestone_font = pygame.font.SysFont(None, 40, bold=True)
    poptext_font = pygame.font.SysFont(None, 32, bold=True)

    bg_stars = make_background_stars()
    particles = []
    shockwaves = []
    poptexts = []
    best_score = 0

    def new_game():
        return [], 0, START_LIVES, WIDTH // 2, pygame.time.get_ticks() + random.randint(
            SPAWN_MIN_MS, SPAWN_MAX_MS
        )

    items, score, lives, basket_x, next_spawn_at = new_game()
    game_over = False
    running = True
    catch_streak = 0
    milestone_text = None
    milestone_until = 0
    new_best = False
    basket_squash = 0.0
    shake_timer = 0.0
    shake_strength = 0.0
    flash_timer = 0.0
    flash_life = 1.0

    while running:
        now = pygame.time.get_ticks()
        dt = clock.get_time() / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif game_over and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    items, score, lives, basket_x, next_spawn_at = new_game()
                    game_over = False
                    catch_streak = 0
                    milestone_text = None
                    new_best = False
                    particles, shockwaves, poptexts = [], [], []
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HOME_BUTTON.collidepoint(event.pos):
                    running = False
                elif game_over:
                    items, score, lives, basket_x, next_spawn_at = new_game()
                    game_over = False
                    catch_streak = 0
                    milestone_text = None
                    new_best = False
                    particles, shockwaves, poptexts = [], [], []
            elif event.type == pygame.MOUSEMOTION and not game_over:
                basket_x = event.pos[0]

        keys = pygame.key.get_pressed()
        if not game_over:
            if keys[pygame.K_LEFT]:
                basket_x -= 8
            if keys[pygame.K_RIGHT]:
                basket_x += 8
            basket_x = max(BASKET_W // 2, min(WIDTH - BASKET_W // 2, basket_x))

            if now >= next_spawn_at:
                items.append(FallingItem())
                next_spawn_at = now + random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS)

            basket_rect = pygame.Rect(0, 0, BASKET_W, BASKET_H)
            basket_rect.center = (basket_x, BASKET_Y)

            remaining = []
            for item in items:
                item.update()
                if not item.is_rock and random.random() < 0.3:
                    particles.append(
                        {
                            "x": item.x + random.uniform(-4, 4),
                            "y": item.y + random.uniform(-4, 4),
                            "vx": 0,
                            "vy": -20,
                            "age": 0.0,
                            "life": random.uniform(0.2, 0.35),
                            "color": (255, 235, 160),
                            "size": random.uniform(1.5, 2.8),
                        }
                    )
                if not item.caught and basket_rect.collidepoint(item.x, item.y) and item.y > BASKET_Y - BASKET_H // 2:
                    item.caught = True
                    basket_squash = 1.0
                    if item.is_rock:
                        lives -= 1
                        sfx.bad()
                        catch_streak = 0
                        spawn_dust(particles, item.x, item.y)
                        spawn_shockwave(shockwaves, item.x, item.y, (140, 140, 150))
                        shake_timer = 0.2
                        shake_strength = 9.0
                        flash_timer = 0.13
                        flash_life = 0.13
                    else:
                        score += 1
                        sfx.good()
                        catch_streak += 1
                        spawn_sparkles(particles, item.x, item.y)
                        spawn_shockwave(shockwaves, item.x, item.y, STAR_COLOR)
                        spawn_poptext(poptexts, item.x, item.y - 15, "+1", (255, 255, 255))
                        if catch_streak > 0 and catch_streak % STREAK_MILESTONE_EVERY == 0:
                            milestone_text = f"{catch_streak} in a row!"
                            milestone_until = now + MILESTONE_MS
                    continue
                if not item.off_screen():
                    remaining.append(item)
            items = remaining

            update_particles(particles, dt)
            update_shockwaves(shockwaves, dt)
            update_poptexts(poptexts, dt)
            basket_squash = max(0.0, basket_squash - dt * 4.0)

            if lives <= 0:
                game_over = True
                if score > best_score:
                    best_score = score
                    new_best = True

        if shake_timer > 0:
            shake_timer = max(0.0, shake_timer - dt)
            power = shake_strength * (shake_timer / 0.2)
            shake_x = int(random.uniform(-1, 1) * power)
            shake_y = int(random.uniform(-1, 1) * power)
        else:
            shake_x, shake_y = 0, 0

        if flash_timer > 0:
            flash_timer = max(0.0, flash_timer - dt)

        draw_background(frame, bg_stars, now)

        title_surf = title_font.render("Star Catcher", True, TITLE_COLOR)
        frame.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        subtitle_surf = subtitle_font.render(
            "Move the basket to catch stars, dodge rocks!", True, (220, 220, 255)
        )
        frame.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        draw_shockwaves(frame, shockwaves)

        for item in items:
            item.draw(frame)

        draw_basket(frame, basket_x, basket_squash)
        draw_particles(frame, particles)
        draw_poptexts(frame, poptext_font, poptexts)

        score_surf = hud_font.render(f"Score: {score}", True, TEXT_COLOR)
        frame.blit(score_surf, (30, 140))

        lives_surf = hud_font.render(f"Lives: {'*' * max(0, lives)}", True, TEXT_COLOR)
        frame.blit(lives_surf, lives_surf.get_rect(topright=(WIDTH - 30, 140)))

        if milestone_text and now < milestone_until:
            draw_milestone(frame, milestone_font, milestone_text)
        elif now >= milestone_until:
            milestone_text = None

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            frame.blit(overlay, (0, 0))
            done_surf = big_font.render(f"Final Score: {score}", True, (255, 255, 255))
            frame.blit(done_surf, done_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
            best_surf = subtitle_font.render(
                "New Best!" if new_best else f"Best: {best_score}",
                True,
                (255, 220, 120) if new_best else (230, 230, 230),
            )
            frame.blit(best_surf, best_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 14)))
            again_surf = subtitle_font.render(
                "Click or press Enter to play again", True, (230, 230, 230)
            )
            frame.blit(
                again_surf, again_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 56))
            )

        draw_home_button(frame)

        screen.fill((0, 0, 0))
        screen.blit(frame, (shake_x, shake_y))

        if flash_timer > 0:
            alpha = int(140 * (flash_timer / flash_life))
            flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((160, 160, 170, alpha))
            screen.blit(flash_surf, (0, 0))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(run())
