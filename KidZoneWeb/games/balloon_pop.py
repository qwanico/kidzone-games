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
except ImportError:  # standalone `python games/balloon_pop.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common import sfx

WIDTH, HEIGHT = 900, 700
BG_TOP = (150, 200, 245)
BG_BOTTOM = (210, 235, 250)
TEXT_COLOR = (50, 50, 60)
TITLE_COLOR = (60, 60, 90)

BALLOON_COLORS = [
    (230, 90, 110),
    (255, 190, 90),
    (90, 160, 230),
    (120, 180, 40),
    (150, 80, 190),
    (20, 150, 140),
]
BOMB_CHANCE = 0.18

BALLOON_W, BALLOON_H = 70, 90
SPAWN_MIN_MS = 350
SPAWN_MAX_MS = 850
MIN_SPEED, MAX_SPEED = 1.6, 3.4

START_LIVES = 3

# ---------------- HOME BUTTON ----------------
HOME_BUTTON_RECT = pygame.Rect(20, 20, 60, 50)
HOME_BUTTON_COLOR = (45, 55, 95)
HOME_BUTTON_BORDER = (245, 245, 250)


def draw_home_button(screen):
    pygame.draw.rect(screen, HOME_BUTTON_COLOR, HOME_BUTTON_RECT, border_radius=10)
    pygame.draw.rect(screen, HOME_BUTTON_BORDER, HOME_BUTTON_RECT, 2, border_radius=10)
    cx, cy = HOME_BUTTON_RECT.center
    roof = [(cx - 16, cy - 1), (cx, cy - 15), (cx + 16, cy - 1)]
    pygame.draw.polygon(screen, (255, 255, 255), roof)
    body = pygame.Rect(0, 0, 22, 15)
    body.midtop = (cx, cy - 2)
    pygame.draw.rect(screen, (255, 255, 255), body)


# ---------------- ANIMATED SKY BACKGROUND ----------------
CLOUD_COLOR = (255, 255, 255)
SUN_GLOW = (255, 250, 210)
SUN_COLOR = (255, 235, 150)

CLOUD_DEFS = [
    (100, 110, 1.0, 9),
    (420, 70, 1.3, 6),
    (680, 150, 0.85, 11),
    (250, 210, 1.1, 7),
]


def draw_sky(screen):
    for i in range(HEIGHT):
        t = i / HEIGHT
        color = tuple(
            int(BG_TOP[c] + (BG_BOTTOM[c] - BG_TOP[c]) * t) for c in range(3)
        )
        pygame.draw.line(screen, color, (0, i), (WIDTH, i))
    pygame.draw.circle(screen, SUN_GLOW, (WIDTH - 90, 85), 55)
    pygame.draw.circle(screen, SUN_COLOR, (WIDTH - 90, 85), 40)


def draw_clouds(screen, now):
    t = now / 1000.0
    for base_x, y, scale, speed in CLOUD_DEFS:
        x = (base_x + t * speed) % (WIDTH + 300) - 150
        puffs = [(-38, 6, 30), (0, -10, 40), (40, 4, 32), (75, 10, 24)]
        for dx, dy, r in puffs:
            pygame.draw.circle(
                screen, CLOUD_COLOR, (int(x + dx * scale), int(y + dy * scale)), int(r * scale)
            )


# ---------------- POP PARTICLES ----------------
def spawn_pop_confetti(particles, x, y, color):
    for _ in range(20):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(2.2, 6.5)
        particles.append(
            {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 1.8,
                "color": color,
                "size": random.randint(3, 8),
                "life": random.uniform(400, 800),
                "age": 0.0,
                "spin": random.uniform(-10, 10),
                "angle": random.uniform(0, 360),
                "star": random.random() < 0.3,
            }
        )


def spawn_bomb_burst(particles, x, y):
    for _ in range(26):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(2.5, 7.5)
        particles.append(
            {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "color": random.choice(
                    [(70, 70, 75), (110, 110, 115), (30, 30, 35), (255, 150, 60), (255, 210, 110)]
                ),
                "size": random.randint(4, 9),
                "life": random.uniform(350, 650),
                "age": 0.0,
                "spin": 0,
                "angle": 0,
                "star": False,
            }
        )


def _draw_star(surf, cx, cy, r, color, alpha):
    pts = []
    for i in range(10):
        ang = math.pi / 5 * i - math.pi / 2
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
    pygame.draw.polygon(surf, (*color, alpha), pts)


def update_particles(particles, dt_ms):
    for p in particles:
        p["age"] += dt_ms
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.12
        p["angle"] += p["spin"]
    particles[:] = [p for p in particles if p["age"] < p["life"]]


def draw_particles(screen, particles):
    for p in particles:
        t = p["age"] / p["life"]
        alpha = max(0, int(255 * (1 - t)))
        size = p["size"]
        surf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
        if p["star"]:
            _draw_star(surf, size * 1.5, size * 1.5, size * 1.4, p["color"], alpha)
        else:
            pygame.draw.rect(
                surf, (*p["color"], alpha), (size * 0.5, size * 0.5, size, size), border_radius=2
            )
        rotated = pygame.transform.rotate(surf, p["angle"])
        rect = rotated.get_rect(center=(p["x"], p["y"]))
        screen.blit(rotated, rect)


# ---------------- SHOCKWAVE RINGS ----------------
def spawn_shockwave(shockwaves, x, y, color):
    shockwaves.append(
        {"x": x, "y": y, "color": color, "age": 0.0, "life": 300, "max_r": 62}
    )


def update_shockwaves(shockwaves, dt_ms):
    for s in shockwaves:
        s["age"] += dt_ms
    shockwaves[:] = [s for s in shockwaves if s["age"] < s["life"]]


def _ease_out(t):
    return 1 - (1 - t) * (1 - t)


def draw_shockwaves(screen, shockwaves):
    for s in shockwaves:
        t = min(1.0, s["age"] / s["life"])
        r = max(2, int(8 + (s["max_r"] - 8) * _ease_out(t)))
        alpha = max(0, int(220 * (1 - t)))
        width = max(1, int(5 * (1 - t)) + 1)
        surf = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*s["color"], alpha), (r + 4, r + 4), r, width=width)
        screen.blit(surf, (s["x"] - r - 4, s["y"] - r - 4))


# ---------------- BALLOON FLAPS (rubber pieces flying apart) ----------------
class BalloonFlap:
    def __init__(self, x, y, color, direction):
        self.x = x
        self.y = y
        self.vx = direction * random.uniform(1.8, 3.6)
        self.vy = random.uniform(-4.2, -1.8)
        self.color = color
        self.angle = random.uniform(0, 360)
        self.spin = direction * random.uniform(8, 18)
        self.age = 0.0
        self.life = random.uniform(380, 560)

    def update(self, dt_ms):
        self.age += dt_ms
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.16
        self.angle += self.spin

    def alive(self):
        return self.age < self.life

    def draw(self, screen):
        t = self.age / self.life
        scale = max(0.0, 1.0 - t * 0.7)
        alpha = max(0, int(255 * (1 - t)))
        w, h = max(1, int(26 * scale)), max(1, int(36 * scale))
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (*self.color, alpha), (0, 0, w, h))
        rotated = pygame.transform.rotate(surf, self.angle)
        rect = rotated.get_rect(center=(self.x, self.y))
        screen.blit(rotated, rect)


def spawn_flaps(flaps, x, y, color):
    flaps.append(BalloonFlap(x, y, color, -1))
    flaps.append(BalloonFlap(x, y, color, 1))


def update_flaps(flaps, dt_ms):
    for f in flaps:
        f.update(dt_ms)
    flaps[:] = [f for f in flaps if f.alive()]


def draw_flaps(screen, flaps):
    for f in flaps:
        f.draw(screen)


# ---------------- FLOATING POP TEXT ----------------
def spawn_poptext(poptexts, x, y, text, color):
    poptexts.append({"x": x, "y": y, "text": text, "color": color, "age": 0.0, "life": 650})


def update_poptexts(poptexts, dt_ms):
    for p in poptexts:
        p["age"] += dt_ms
        p["y"] -= 0.05 * dt_ms
    poptexts[:] = [p for p in poptexts if p["age"] < p["life"]]


def draw_poptexts(screen, font, poptexts):
    for p in poptexts:
        t = p["age"] / p["life"]
        alpha = max(0, int(255 * (1 - t)))
        scale = 1.0 + 0.5 * min(1.0, p["age"] / 120.0)
        surf = font.render(p["text"], True, p["color"])
        w, h = surf.get_size()
        if abs(scale - 1.0) > 0.01:
            surf = pygame.transform.smoothscale(surf, (max(1, int(w * scale)), max(1, int(h * scale))))
        surf.set_alpha(alpha)
        rect = surf.get_rect(center=(p["x"], p["y"]))
        screen.blit(surf, rect)


def draw_milestone(screen, font, text, alpha):
    surf = font.render(text, True, (255, 255, 255))
    rect = surf.get_rect(center=(WIDTH // 2, 185))
    bg = rect.inflate(44, 24)
    panel = pygame.Surface(bg.size, pygame.SRCALPHA)
    a = max(0, min(255, alpha))
    pygame.draw.rect(panel, (90, 130, 210, min(230, a)), panel.get_rect(), border_radius=16)
    pygame.draw.rect(panel, (255, 255, 255, a), panel.get_rect(), 3, border_radius=16)
    screen.blit(panel, bg.topleft)
    surf.set_alpha(a)
    screen.blit(surf, rect)


class Balloon:
    def __init__(self):
        self.x = random.randint(BALLOON_W, WIDTH - BALLOON_W)
        self.y = HEIGHT + BALLOON_H
        self.speed = random.uniform(MIN_SPEED, MAX_SPEED)
        self.is_bomb = random.random() < BOMB_CHANCE
        self.color = random.choice(BALLOON_COLORS)
        self.popped = False
        self.wobble_phase = random.uniform(0, 6.28)

    def update(self, now):
        self.y -= self.speed
        self.x += 1.2 * _wobble(now, self.wobble_phase)

    def off_screen(self):
        return self.y < -BALLOON_H

    def contains(self, pos):
        cx, cy = self.x, self.y
        dx = (pos[0] - cx) / (BALLOON_W / 2)
        dy = (pos[1] - cy) / (BALLOON_H / 2)
        return dx * dx + dy * dy <= 1.0

    def draw(self, screen, now):
        if self.is_bomb:
            cx, cy = int(self.x), int(self.y)
            r = 32
            pygame.draw.circle(screen, (18, 18, 22), (cx, cy + 4), r)
            pygame.draw.circle(screen, (52, 52, 60), (cx - 10, cy - 6), int(r * 0.38))
            pygame.draw.circle(screen, (0, 0, 0), (cx, cy + 4), r, width=2)
            fuse_mid = (cx + 12, cy - r + 2)
            fuse_end = (cx + 22, cy - r - 14)
            pygame.draw.line(screen, (150, 105, 60), (cx + 4, cy - r + 8), fuse_mid, 4)
            pygame.draw.line(screen, (150, 105, 60), fuse_mid, fuse_end, 4)
            pulse = 5 + int(3 * math.sin(now / 90.0))
            glow = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 190, 80, 90), (30, 30), 16 + pulse)
            screen.blit(glow, (fuse_end[0] - 30, fuse_end[1] - 30))
            pygame.draw.circle(screen, (255, 210, 90), fuse_end, 6 + pulse // 2)
            pygame.draw.circle(screen, (255, 245, 180), fuse_end, 3)
        else:
            rect = pygame.Rect(0, 0, BALLOON_W, BALLOON_H)
            rect.center = (int(self.x), int(self.y))
            pygame.draw.line(
                screen, (120, 120, 120), (self.x, self.y + BALLOON_H // 2),
                (self.x, self.y + BALLOON_H // 2 + 40), 2
            )
            pygame.draw.ellipse(screen, self.color, rect)
            pygame.draw.ellipse(screen, tuple(max(0, c - 40) for c in self.color), rect, width=2)
            highlight = pygame.Rect(0, 0, 18, 26)
            highlight.center = (int(self.x - 16), int(self.y - 20))
            pygame.draw.ellipse(screen, tuple(min(255, c + 60) for c in self.color), highlight)


def _wobble(now, phase):
    return math.sin(now / 400.0 + phase) * 0.6


async def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
    if platform is not None and hasattr(platform, "window"):
        try:
            platform.window.window_resize()
        except Exception:
            pass
    pygame.display.set_caption("Balloon Pop")
    clock = pygame.time.Clock()
    frame = pygame.Surface((WIDTH, HEIGHT))

    title_font = pygame.font.SysFont(None, 64, bold=True)
    subtitle_font = pygame.font.SysFont(None, 30)
    hud_font = pygame.font.SysFont(None, 40, bold=True)
    big_font = pygame.font.SysFont(None, 72, bold=True)
    milestone_font = pygame.font.SysFont(None, 46, bold=True)
    poptext_font = pygame.font.SysFont(None, 34, bold=True)

    def new_game():
        return [], 0, START_LIVES, pygame.time.get_ticks() + random.randint(
            SPAWN_MIN_MS, SPAWN_MAX_MS
        )

    def reset_effects():
        return [], [], [], []  # particles, shockwaves, flaps, poptexts

    balloons, score, lives, next_spawn_at = new_game()
    game_over = False
    running = True

    particles, shockwaves, flaps, poptexts = reset_effects()
    streak = 0
    best_score = 0
    new_best = False
    milestone_text = None
    milestone_until = 0
    shake_timer = 0.0
    shake_strength = 0.0
    flash_timer = 0.0
    flash_life = 1.0
    flash_color = (255, 255, 255)

    while running:
        now = pygame.time.get_ticks()
        dt = clock.get_time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif game_over and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    balloons, score, lives, next_spawn_at = new_game()
                    game_over = False
                    particles, shockwaves, flaps, poptexts = reset_effects()
                    streak = 0
                    new_best = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HOME_BUTTON_RECT.collidepoint(event.pos):
                    running = False
                elif game_over:
                    balloons, score, lives, next_spawn_at = new_game()
                    game_over = False
                    particles, shockwaves, flaps, poptexts = reset_effects()
                    streak = 0
                    new_best = False
                else:
                    for balloon in balloons:
                        if not balloon.popped and balloon.contains(event.pos):
                            balloon.popped = True
                            if balloon.is_bomb:
                                lives -= 1
                                sfx.bad()
                                streak = 0
                                spawn_bomb_burst(particles, balloon.x, balloon.y)
                                spawn_shockwave(shockwaves, balloon.x, balloon.y, (255, 140, 60))
                                spawn_flaps(flaps, balloon.x, balloon.y, (45, 45, 50))
                                shake_timer = 220.0
                                shake_strength = 10.0
                                flash_timer = 140.0
                                flash_life = 140.0
                                flash_color = (255, 140, 60)
                            else:
                                score += 1
                                sfx.good()
                                streak += 1
                                spawn_pop_confetti(particles, balloon.x, balloon.y, balloon.color)
                                spawn_shockwave(shockwaves, balloon.x, balloon.y, balloon.color)
                                spawn_flaps(flaps, balloon.x, balloon.y, balloon.color)
                                spawn_poptext(poptexts, balloon.x, balloon.y - 20, "+1", (255, 255, 255))
                                if streak >= 3 and streak % 3 == 0:
                                    milestone_text = f"{streak} in a row!"
                                    milestone_until = now + 1400
                            break

        if not game_over:
            if now >= next_spawn_at:
                balloons.append(Balloon())
                next_spawn_at = now + random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS)

            for balloon in balloons:
                balloon.update(now)
            balloons = [
                b for b in balloons if not b.popped and not b.off_screen()
            ]

            update_particles(particles, dt)
            update_shockwaves(shockwaves, dt)
            update_flaps(flaps, dt)
            update_poptexts(poptexts, dt)

            if lives <= 0:
                game_over = True
                if score > best_score:
                    best_score = score
                    new_best = True

        if shake_timer > 0:
            shake_timer = max(0.0, shake_timer - dt)
            power = shake_strength * (shake_timer / 220.0)
            shake_x = int(random.uniform(-1, 1) * power)
            shake_y = int(random.uniform(-1, 1) * power)
        else:
            shake_x, shake_y = 0, 0

        if flash_timer > 0:
            flash_timer = max(0.0, flash_timer - dt)

        draw_sky(frame)
        draw_clouds(frame, now)

        title_surf = title_font.render("Balloon Pop", True, TITLE_COLOR)
        frame.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        subtitle_surf = subtitle_font.render(
            "Pop the balloons, avoid the bombs!", True, (70, 70, 90)
        )
        frame.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        draw_shockwaves(frame, shockwaves)

        for balloon in balloons:
            balloon.draw(frame, now)

        draw_flaps(frame, flaps)
        draw_particles(frame, particles)
        draw_poptexts(frame, poptext_font, poptexts)

        score_surf = hud_font.render(f"Score: {score}", True, TEXT_COLOR)
        frame.blit(score_surf, (30, 140))

        lives_surf = hud_font.render(f"Lives: {'*' * max(0, lives)}", True, TEXT_COLOR)
        frame.blit(lives_surf, lives_surf.get_rect(topright=(WIDTH - 30, 140)))

        if milestone_text and now < milestone_until:
            remaining = milestone_until - now
            alpha = 255 if remaining > 300 else int(255 * remaining / 300)
            draw_milestone(frame, milestone_font, milestone_text, alpha)
        elif now >= milestone_until:
            milestone_text = None

        draw_home_button(frame)

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            frame.blit(overlay, (0, 0))

            panel = pygame.Rect(0, 0, 460, 260)
            panel.center = (WIDTH // 2, HEIGHT // 2)
            panel_surf = pygame.Surface(panel.size, pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (245, 248, 255, 235), panel_surf.get_rect(), border_radius=24)
            pygame.draw.rect(panel_surf, (60, 90, 160, 255), panel_surf.get_rect(), 5, border_radius=24)
            frame.blit(panel_surf, panel.topleft)

            done_surf = big_font.render(f"Score: {score}", True, (60, 60, 90))
            frame.blit(done_surf, done_surf.get_rect(center=(panel.centerx, panel.top + 70)))

            best_surf = hud_font.render(f"Best: {best_score}", True, (60, 80, 120))
            frame.blit(best_surf, best_surf.get_rect(center=(panel.centerx, panel.top + 125)))

            if new_best:
                nb_surf = subtitle_font.render("New Best!", True, (200, 130, 20))
                frame.blit(nb_surf, nb_surf.get_rect(center=(panel.centerx, panel.top + 160)))

            again_surf = subtitle_font.render(
                "Click or press Enter to play again", True, (70, 70, 80)
            )
            frame.blit(
                again_surf, again_surf.get_rect(center=(panel.centerx, panel.bottom - 30))
            )

        screen.fill((0, 0, 0))
        screen.blit(frame, (shake_x, shake_y))

        if flash_timer > 0:
            alpha = int(160 * (flash_timer / flash_life))
            flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((*flash_color, alpha))
            screen.blit(flash_surf, (0, 0))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(run())
