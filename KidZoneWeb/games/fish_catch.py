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
except ImportError:  # standalone `python games/fish_catch.py`
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from common import sfx
    from common import display
    from common import text

WIDTH, HEIGHT = 900, 700
BG_TOP = (30, 90, 165)
BG_BOTTOM = (110, 180, 210)
TEXT_COLOR = (255, 255, 255)
TITLE_COLOR = (255, 255, 255)

FISH_COLORS = [
    (255, 150, 60),
    (255, 210, 60),
    (230, 90, 130),
    (120, 220, 200),
    (255, 130, 170),
    (140, 200, 255),
]
JUNK_CHANCE = 0.2

FISH_W, FISH_H = 74, 42
LANE_COUNT = 5
LANE_TOP = 190
LANE_GAP = 90
MIN_SPEED, MAX_SPEED = 1.6, 3.6
SPAWN_MIN_MS = 350
SPAWN_MAX_MS = 800

START_LIVES = 3

# ---------------- HOME BUTTON ----------------
HOME_BUTTON_RECT = pygame.Rect(20, 20, 60, 50)
HOME_BUTTON_COLOR = (20, 55, 95)
HOME_BUTTON_BORDER = (235, 245, 255)


def draw_home_button(screen):
    pygame.draw.rect(screen, HOME_BUTTON_COLOR, HOME_BUTTON_RECT, border_radius=10)
    pygame.draw.rect(screen, HOME_BUTTON_BORDER, HOME_BUTTON_RECT, 2, border_radius=10)
    cx, cy = HOME_BUTTON_RECT.center
    roof = [(cx - 16, cy - 1), (cx, cy - 15), (cx + 16, cy - 1)]
    pygame.draw.polygon(screen, (255, 255, 255), roof)
    body = pygame.Rect(0, 0, 22, 15)
    body.midtop = (cx, cy - 2)
    pygame.draw.rect(screen, (255, 255, 255), body)


# ---------------- UNDERWATER BACKGROUND ----------------
def draw_background(screen):
    for i in range(HEIGHT):
        t = i / HEIGHT
        color = tuple(
            int(BG_TOP[c] + (BG_BOTTOM[c] - BG_TOP[c]) * t) for c in range(3)
        )
        pygame.draw.line(screen, color, (0, i), (WIDTH, i))


def draw_light_rays(screen, now):
    t = now / 1000.0
    ray_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(5):
        base_x = 80 + i * 190
        sway = math.sin(t * 0.4 + i) * 30
        top_x = base_x + sway
        width_top = 40
        width_bot = 140
        alpha = 22 + int(10 * math.sin(t * 0.7 + i * 1.3))
        pts = [
            (top_x - width_top / 2, 0),
            (top_x + width_top / 2, 0),
            (top_x + width_bot / 2 + sway, HEIGHT),
            (top_x - width_bot / 2 + sway, HEIGHT),
        ]
        pygame.draw.polygon(ray_surf, (255, 255, 255, max(0, alpha)), pts)
    screen.blit(ray_surf, (0, 0))


def draw_seaweed(screen, now):
    t = now / 1000.0
    bases = [70, 190, 700, 810, 400]
    for i, bx in enumerate(bases):
        sway = math.sin(t * 1.2 + i * 1.7) * 18
        pts = [(bx, HEIGHT + 10)]
        segs = 6
        h = 130
        for s in range(1, segs + 1):
            frac = s / segs
            x = bx + sway * frac * frac
            y = HEIGHT + 10 - h * frac
            pts.append((x, y))
        width_shape = pts + [(p[0] + 14, p[1]) for p in reversed(pts)]
        color = (30, 110, 70) if i % 2 == 0 else (35, 130, 85)
        pygame.draw.polygon(screen, color, width_shape)


def spawn_bubble(bubbles):
    bubbles.append(
        {
            "x": random.uniform(20, WIDTH - 20),
            "y": HEIGHT + 20,
            "r": random.uniform(3, 9),
            "speed": random.uniform(0.6, 1.8),
            "phase": random.uniform(0, 6.28),
        }
    )


def update_bubbles(bubbles, now):
    for b in bubbles:
        b["y"] -= b["speed"]
        b["x"] += math.sin(now / 500.0 + b["phase"]) * 0.4
    bubbles[:] = [b for b in bubbles if b["y"] > -20]
    if random.random() < 0.06:
        spawn_bubble(bubbles)


def draw_bubbles(screen, bubbles):
    for b in bubbles:
        pygame.draw.circle(screen, (255, 255, 255), (int(b["x"]), int(b["y"])), int(b["r"]), width=1)


# ---------------- CATCH / MISS EFFECTS ----------------
def spawn_catch_burst(particles, x, y):
    for _ in range(18):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.8, 5.0)
        particles.append(
            {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 1.0,
                "color": random.choice([(255, 255, 255), (200, 235, 255), (255, 230, 150)]),
                "size": random.uniform(2.5, 6),
                "life": random.uniform(350, 650),
                "age": 0.0,
            }
        )


def spawn_murk_burst(particles, x, y):
    for _ in range(20):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.5, 4.5)
        particles.append(
            {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "color": random.choice([(70, 55, 40), (95, 75, 55), (50, 40, 30)]),
                "size": random.uniform(4, 10),
                "life": random.uniform(450, 800),
                "age": 0.0,
            }
        )


def update_particles(particles, dt_ms):
    for p in particles:
        p["age"] += dt_ms
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.05
    particles[:] = [p for p in particles if p["age"] < p["life"]]


def draw_particles(screen, particles):
    for p in particles:
        t = p["age"] / p["life"]
        alpha = max(0, int(220 * (1 - t)))
        r = max(1, int(p["size"] * (1 - t * 0.4)))
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*p["color"], alpha), (r, r), r)
        screen.blit(surf, (p["x"] - r, p["y"] - r))


def spawn_shockwave(shockwaves, x, y, color):
    shockwaves.append({"x": x, "y": y, "color": color, "age": 0.0, "life": 300, "max_r": 55})


def update_shockwaves(shockwaves, dt_ms):
    for s in shockwaves:
        s["age"] += dt_ms
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
        surf = font.render_copy(p["text"], True, p["color"])
        w, h = surf.get_size()
        if abs(scale - 1.0) > 0.01:
            surf = pygame.transform.smoothscale(surf, (max(1, int(w * scale)), max(1, int(h * scale))))
        surf.set_alpha(alpha)
        screen.blit(surf, surf.get_rect(center=(p["x"], p["y"])))


def draw_milestone(screen, font, text, alpha):
    surf = font.render_copy(text, True, (255, 255, 255))
    rect = surf.get_rect(center=(WIDTH // 2, 185))
    bg = rect.inflate(44, 24)
    panel = pygame.Surface(bg.size, pygame.SRCALPHA)
    a = max(0, min(255, alpha))
    pygame.draw.rect(panel, (30, 110, 170, min(230, a)), panel.get_rect(), border_radius=16)
    pygame.draw.rect(panel, (255, 255, 255, a), panel.get_rect(), 3, border_radius=16)
    screen.blit(panel, bg.topleft)
    surf.set_alpha(a)
    screen.blit(surf, rect)


class Fish:
    def __init__(self):
        self.lane = random.randint(0, LANE_COUNT - 1)
        self.y = LANE_TOP + self.lane * LANE_GAP + random.uniform(-10, 10)
        self.dir = random.choice([-1, 1])
        self.x = -FISH_W if self.dir == 1 else WIDTH + FISH_W
        self.speed = random.uniform(MIN_SPEED, MAX_SPEED)
        self.is_junk = random.random() < JUNK_CHANCE
        self.color = random.choice(FISH_COLORS)
        self.caught = False
        self.bob_phase = random.uniform(0, 6.28)

    def update(self, now):
        self.x += self.speed * self.dir
        self.y += math.sin(now / 300.0 + self.bob_phase) * 0.3

    def off_screen(self):
        return self.x < -FISH_W * 2 or self.x > WIDTH + FISH_W * 2

    def contains(self, pos):
        dx = (pos[0] - self.x) / (FISH_W / 2)
        dy = (pos[1] - self.y) / (FISH_H / 2)
        return dx * dx + dy * dy <= 1.0

    def draw(self, screen, now):
        facing = self.dir
        squash = 1.0 + math.sin(now / 180.0 + self.bob_phase) * 0.06

        if self.is_junk:
            cx, cy = int(self.x), int(self.y)
            can_rect = pygame.Rect(0, 0, 34, 40)
            can_rect.center = (cx, cy + 2)
            pygame.draw.rect(screen, (85, 90, 95), can_rect, border_radius=6)
            pygame.draw.rect(screen, (60, 64, 68), can_rect, width=2, border_radius=6)
            lid = pygame.Rect(0, 0, 40, 10)
            lid.midtop = (cx, cy - 20)
            pygame.draw.ellipse(screen, (60, 64, 68), lid)
            for dy in (-8, 0, 8):
                pygame.draw.line(
                    screen, (105, 110, 115), (can_rect.left + 4, cy + dy), (can_rect.right - 4, cy + dy), 2
                )
            return

        body_rect = pygame.Rect(0, 0, FISH_W * 0.7, FISH_H * squash)
        body_rect.center = (self.x, self.y)

        tail_x = self.x - facing * FISH_W * 0.35
        tail_pts = [
            (tail_x, self.y),
            (tail_x - facing * 20, self.y - 16 * squash),
            (tail_x - facing * 20, self.y + 16 * squash),
        ]
        dark = tuple(max(0, c - 60) for c in self.color)
        pygame.draw.polygon(screen, dark, tail_pts)

        fin_pts = [
            (self.x, self.y - FISH_H * 0.18),
            (self.x - facing * 6, self.y - FISH_H * 0.5),
            (self.x + facing * 10, self.y - FISH_H * 0.15),
        ]
        pygame.draw.polygon(screen, dark, fin_pts)

        pygame.draw.ellipse(screen, self.color, body_rect)
        belly = body_rect.inflate(-body_rect.width * 0.4, -body_rect.height * 0.55)
        belly.centery = body_rect.centery + body_rect.height * 0.18
        pygame.draw.ellipse(screen, tuple(min(255, c + 55) for c in self.color), belly)

        eye_x = self.x + facing * FISH_W * 0.22
        pygame.draw.circle(screen, (255, 255, 255), (int(eye_x), int(self.y - 4)), 6)
        pygame.draw.circle(screen, (20, 20, 20), (int(eye_x + facing), int(self.y - 4)), 3)


async def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    if platform is not None and hasattr(platform, "window"):
        try:
            platform.window.window_resize()
        except Exception:
            pass
    pygame.display.set_caption("Fish Catch")
    clock = pygame.time.Clock()
    frame = pygame.Surface((WIDTH, HEIGHT))

    title_font = text.SysFont(None, 64, bold=True)
    subtitle_font = text.SysFont(None, 30)
    hud_font = text.SysFont(None, 40, bold=True)
    big_font = text.SysFont(None, 72, bold=True)
    milestone_font = text.SysFont(None, 46, bold=True)
    poptext_font = text.SysFont(None, 34, bold=True)

    def new_game():
        return [], 0, START_LIVES, pygame.time.get_ticks() + random.randint(
            SPAWN_MIN_MS, SPAWN_MAX_MS
        )

    def reset_effects():
        return [], [], []  # particles, shockwaves, poptexts

    fish_list, score, lives, next_spawn_at = new_game()
    game_over = False
    running = True

    particles, shockwaves, poptexts = reset_effects()
    bubbles = []
    for _ in range(14):
        spawn_bubble(bubbles)
    streak = 0
    best_score = 0
    new_best = False
    milestone_text = None
    milestone_until = 0
    shake_timer = 0.0
    shake_strength = 0.0
    flash_timer = 0.0
    flash_life = 1.0
    flash_color = (60, 45, 30)

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
                    fish_list, score, lives, next_spawn_at = new_game()
                    game_over = False
                    particles, shockwaves, poptexts = reset_effects()
                    streak = 0
                    new_best = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HOME_BUTTON_RECT.collidepoint(event.pos):
                    running = False
                elif game_over:
                    fish_list, score, lives, next_spawn_at = new_game()
                    game_over = False
                    particles, shockwaves, poptexts = reset_effects()
                    streak = 0
                    new_best = False
                else:
                    for fish in fish_list:
                        if not fish.caught and fish.contains(event.pos):
                            fish.caught = True
                            if fish.is_junk:
                                lives -= 1
                                sfx.bad()
                                streak = 0
                                spawn_murk_burst(particles, fish.x, fish.y)
                                spawn_shockwave(shockwaves, fish.x, fish.y, (90, 70, 50))
                                shake_timer = 200.0
                                shake_strength = 9.0
                                flash_timer = 130.0
                                flash_life = 130.0
                            else:
                                score += 1
                                sfx.good()
                                streak += 1
                                spawn_catch_burst(particles, fish.x, fish.y)
                                spawn_shockwave(shockwaves, fish.x, fish.y, fish.color)
                                spawn_poptext(poptexts, fish.x, fish.y - 20, "+1", (255, 255, 255))
                                if streak >= 3 and streak % 3 == 0:
                                    milestone_text = f"{streak} in a row!"
                                    milestone_until = now + 1400
                            break

        if not game_over:
            if now >= next_spawn_at:
                fish_list.append(Fish())
                next_spawn_at = now + random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS)

            for fish in fish_list:
                fish.update(now)

            fish_list = [f for f in fish_list if not f.caught and not f.off_screen()]

            update_particles(particles, dt)
            update_shockwaves(shockwaves, dt)
            update_poptexts(poptexts, dt)
            update_bubbles(bubbles, now)

            if lives <= 0:
                game_over = True
                if score > best_score:
                    best_score = score
                    new_best = True

        if shake_timer > 0:
            shake_timer = max(0.0, shake_timer - dt)
            power = shake_strength * (shake_timer / 200.0)
            shake_x = int(random.uniform(-1, 1) * power)
            shake_y = int(random.uniform(-1, 1) * power)
        else:
            shake_x, shake_y = 0, 0

        if flash_timer > 0:
            flash_timer = max(0.0, flash_timer - dt)

        draw_background(frame)
        draw_light_rays(frame, now)
        draw_bubbles(frame, bubbles)
        draw_seaweed(frame, now)

        title_surf = title_font.render("Fish Catch", True, TITLE_COLOR)
        frame.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        subtitle_surf = subtitle_font.render(
            "Click the fish, avoid the junk!", True, (230, 240, 255)
        )
        frame.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 100)))

        draw_shockwaves(frame, shockwaves)

        for fish in fish_list:
            fish.draw(frame, now)

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
            pygame.draw.rect(panel_surf, (235, 248, 255, 235), panel_surf.get_rect(), border_radius=24)
            pygame.draw.rect(panel_surf, (25, 95, 150, 255), panel_surf.get_rect(), 5, border_radius=24)
            frame.blit(panel_surf, panel.topleft)

            done_surf = big_font.render(f"Score: {score}", True, (25, 70, 110))
            frame.blit(done_surf, done_surf.get_rect(center=(panel.centerx, panel.top + 70)))

            best_surf = hud_font.render(f"Best: {best_score}", True, (40, 90, 130))
            frame.blit(best_surf, best_surf.get_rect(center=(panel.centerx, panel.top + 125)))

            if new_best:
                nb_surf = subtitle_font.render("New Best!", True, (210, 140, 20))
                frame.blit(nb_surf, nb_surf.get_rect(center=(panel.centerx, panel.top + 160)))

            again_surf = subtitle_font.render(
                "Click or press Enter to play again", True, (60, 80, 100)
            )
            frame.blit(
                again_surf, again_surf.get_rect(center=(panel.centerx, panel.bottom - 30))
            )

        screen.fill((0, 0, 0))
        screen.blit(frame, (shake_x, shake_y))

        if flash_timer > 0:
            alpha = int(150 * (flash_timer / flash_life))
            flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((*flash_color, alpha))
            screen.blit(flash_surf, (0, 0))

        pygame.display.flip()

        _resized = display.maintain(WIDTH, HEIGHT)

        if _resized is not None:

            screen = _resized
        clock.tick(60)
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(run())
