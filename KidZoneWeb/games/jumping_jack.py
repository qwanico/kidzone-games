import asyncio
import math
import random

import pygame

try:
    import platform
except ImportError:
    platform = None

WIDTH, HEIGHT = 900, 600
BG_TOP = (255, 200, 150)
BG_MID = (255, 225, 180)
BG_BOTTOM = (255, 250, 235)
GROUND_Y = HEIGHT - 120
GROUND_COLOR = (140, 200, 110)
GROUND_DARK = (115, 175, 90)
TEXT_COLOR = (50, 50, 60)
TITLE_COLOR = (60, 60, 90)

PLAYER_X = 150
PLAYER_W, PLAYER_H = 50, 70
GRAVITY = 0.9
JUMP_VELOCITY = -16

OBSTACLE_W, OBSTACLE_H = 40, 60
SPAWN_MIN_MS = 900
SPAWN_MAX_MS = 1700

START_SPEED = 6.0
MAX_SPEED = 14.0
SPEED_RAMP_PER_SEC = 0.12

HOME_BUTTON_RECT = pygame.Rect(20, 20, 60, 50)
HOME_BUTTON_COLOR = (150, 90, 50)
HOME_BUTTON_BORDER = (255, 250, 240)


def draw_home_button(screen):
    pygame.draw.rect(screen, HOME_BUTTON_COLOR, HOME_BUTTON_RECT, border_radius=10)
    pygame.draw.rect(screen, HOME_BUTTON_BORDER, HOME_BUTTON_RECT, 2, border_radius=10)
    cx, cy = HOME_BUTTON_RECT.center
    roof = [(cx - 16, cy - 1), (cx, cy - 15), (cx + 16, cy - 1)]
    pygame.draw.polygon(screen, (255, 255, 255), roof)
    body = pygame.Rect(0, 0, 22, 15)
    body.midtop = (cx, cy - 2)
    pygame.draw.rect(screen, (255, 255, 255), body)


HILL_DEFS = [(0.25, 60, 240), (0.55, 80, 300), (0.85, 45, 200)]
CLOUD_DEFS = [(120, 90, 1.0, 8), (500, 60, 1.2, 5), (760, 110, 0.8, 10)]


def draw_background(screen, now):
    for i in range(GROUND_Y):
        t = i / GROUND_Y
        if t < 0.5:
            a, b, tt = BG_TOP, BG_MID, t / 0.5
        else:
            a, b, tt = BG_MID, BG_BOTTOM, (t - 0.5) / 0.5
        color = tuple(int(a[c] + (b[c] - a[c]) * tt) for c in range(3))
        pygame.draw.line(screen, color, (0, i), (WIDTH, i))

    pygame.draw.circle(screen, (255, 245, 210), (WIDTH - 100, 90), 46)

    t = now / 1000.0
    for base_x, y, scale, speed in CLOUD_DEFS:
        x = (base_x - t * speed * 2) % (WIDTH + 200) - 100
        for dx, dy, r in [(-30, 4, 24), (0, -8, 32), (32, 4, 26)]:
            pygame.draw.circle(screen, (255, 255, 255), (int(x + dx * scale), int(y + dy * scale)), int(r * scale))

    parallax = (now / 1000.0 * 20) % WIDTH
    for frac, h, w in HILL_DEFS:
        for off in (-WIDTH, 0, WIDTH):
            x = frac * WIDTH - parallax + off
            pygame.draw.ellipse(
                screen, (170, 205, 150), (x - w / 2, GROUND_Y - h * 0.5, w, h)
            )

    pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    pygame.draw.rect(screen, GROUND_DARK, (0, GROUND_Y, WIDTH, 6))
    tuft_spacing = 34
    ground_scroll = (now / 1000.0 * 40) % tuft_spacing
    x = -ground_scroll
    while x < WIDTH:
        pygame.draw.line(screen, GROUND_DARK, (x, GROUND_Y + 10), (x, GROUND_Y + 4), 3)
        x += tuft_spacing


class Player:
    def __init__(self):
        self.y = GROUND_Y - PLAYER_H
        self.vy = 0.0
        self.on_ground = True
        self.run_phase = 0.0
        self.squash = 0.0

    def jump(self):
        if self.on_ground:
            self.vy = JUMP_VELOCITY
            self.on_ground = False
            self.squash = -0.35

    def update(self, dt):
        self.vy += GRAVITY
        self.y += self.vy
        landed = False
        if self.y >= GROUND_Y - PLAYER_H:
            if not self.on_ground:
                landed = True
            self.y = GROUND_Y - PLAYER_H
            self.vy = 0
            self.on_ground = True
        if self.on_ground:
            self.run_phase += dt * 0.015
        self.squash += (0 - self.squash) * min(1.0, dt / 90.0)
        return landed

    def rect(self):
        return pygame.Rect(PLAYER_X, int(self.y), PLAYER_W, PLAYER_H)

    def draw(self, screen):
        rect = self.rect()
        stretch = -self.vy * 0.015 if not self.on_ground else 0
        squash = max(-0.4, min(0.4, self.squash + stretch * 0.3))
        w = PLAYER_W * (1 - squash * 0.4)
        h = PLAYER_H * (1 + squash * 0.3)
        body_rect = pygame.Rect(0, 0, w, h)
        body_rect.midbottom = rect.midbottom

        if self.on_ground:
            arm_swing = int(14 * math.sin(self.run_phase * 12.566))
            leg_swing = int(10 * abs(((self.run_phase % 1.0) * 2) - 1) - 5)
        else:
            arm_swing = -10
            leg_swing = 6

        pygame.draw.line(
            screen, (60, 60, 90),
            (body_rect.centerx - 10, body_rect.bottom), (body_rect.centerx - 10 - leg_swing, body_rect.bottom + 16), 7
        )
        pygame.draw.line(
            screen, (60, 60, 90),
            (body_rect.centerx + 10, body_rect.bottom), (body_rect.centerx + 10 + leg_swing, body_rect.bottom + 16), 7
        )

        pygame.draw.rect(screen, (60, 95, 175), body_rect, border_radius=14)
        pygame.draw.rect(screen, (90, 130, 220), body_rect.inflate(-10, -10), border_radius=10)

        pygame.draw.line(
            screen, (250, 210, 170),
            (body_rect.centerx - 16, body_rect.top + 10), (body_rect.centerx - 16 - arm_swing, body_rect.top + 34), 6
        )
        pygame.draw.line(
            screen, (250, 210, 170),
            (body_rect.centerx + 16, body_rect.top + 10), (body_rect.centerx + 16 + arm_swing, body_rect.top + 34), 6
        )

        head_c = (body_rect.centerx, rect.top - 6)
        pygame.draw.circle(screen, (250, 210, 170), head_c, 18)
        pygame.draw.circle(screen, (40, 40, 50), (head_c[0] + 6, head_c[1] - 2), 2)
        pygame.draw.arc(
            screen, (40, 40, 50),
            (head_c[0] - 2, head_c[1] + 2, 12, 8), math.radians(200), math.radians(340), 2
        )
        pygame.draw.arc(screen, (70, 45, 30), (head_c[0] - 16, head_c[1] - 20, 32, 22), math.radians(20), math.radians(160), 6)


class Obstacle:
    def __init__(self, x):
        self.x = x
        self.passed = False
        self.kind = random.choice(["cactus", "rock"])

    def update(self, speed):
        self.x -= speed

    def off_screen(self):
        return self.x < -OBSTACLE_W

    def rect(self):
        return pygame.Rect(int(self.x), GROUND_Y - OBSTACLE_H, OBSTACLE_W, OBSTACLE_H)

    def draw(self, screen):
        rect = self.rect()
        if self.kind == "cactus":
            pygame.draw.rect(screen, (60, 140, 80), rect.inflate(-16, 0), border_radius=8)
            arm = pygame.Rect(0, 0, 14, 26)
            arm.midtop = (rect.left + 6, rect.top + 14)
            pygame.draw.rect(screen, (60, 140, 80), arm, border_radius=6)
            arm2 = pygame.Rect(0, 0, 14, 22)
            arm2.midtop = (rect.right - 6, rect.top + 22)
            pygame.draw.rect(screen, (60, 140, 80), arm2, border_radius=6)
            for i in range(3):
                yy = rect.top + 10 + i * 16
                pygame.draw.line(screen, (40, 110, 60), (rect.centerx - 6, yy), (rect.centerx - 6, yy + 8), 2)
        else:
            pygame.draw.polygon(
                screen, (120, 115, 110),
                [(rect.left, rect.bottom), (rect.left + 6, rect.top + 10), (rect.centerx - 4, rect.top),
                 (rect.right - 6, rect.top + 14), (rect.right, rect.bottom)]
            )
            pygame.draw.polygon(
                screen, (95, 90, 85),
                [(rect.left, rect.bottom), (rect.left + 6, rect.top + 10), (rect.centerx - 4, rect.top),
                 (rect.right - 6, rect.top + 14), (rect.right, rect.bottom)], width=2
            )


def spawn_dust(particles, x, y, upward=False):
    for _ in range(10):
        angle = random.uniform(-2.6, -0.6) if upward else random.uniform(math.pi * 0.15, math.pi * 0.85)
        speed = random.uniform(1.0, 3.0)
        particles.append(
            {
                "x": x + random.uniform(-8, 8),
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": -abs(math.sin(angle) * speed) if upward else -math.sin(angle) * speed * 0.3,
                "size": random.uniform(3, 7),
                "life": random.uniform(300, 550),
                "age": 0.0,
                "color": (225, 210, 165),
            }
        )


def spawn_crash(particles, x, y):
    for _ in range(24):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(2.0, 6.0)
        particles.append(
            {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 1.0,
                "size": random.uniform(3, 8),
                "life": random.uniform(350, 650),
                "age": 0.0,
                "color": random.choice([(220, 90, 70), (255, 200, 90), (250, 250, 250)]),
            }
        )


def update_particles(particles, dt_ms):
    for p in particles:
        p["age"] += dt_ms
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.12
    particles[:] = [p for p in particles if p["age"] < p["life"]]


def draw_particles(screen, particles):
    for p in particles:
        t = p["age"] / p["life"]
        alpha = max(0, int(220 * (1 - t)))
        r = max(1, int(p["size"] * (1 - t * 0.5)))
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*p["color"], alpha), (r, r), r)
        screen.blit(surf, (p["x"] - r, p["y"] - r))


async def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
    if platform is not None and hasattr(platform, "window"):
        try:
            platform.window.window_resize()
        except Exception:
            pass
    pygame.display.set_caption("Jumping Jack")
    clock = pygame.time.Clock()
    frame = pygame.Surface((WIDTH, HEIGHT))

    title_font = pygame.font.SysFont(None, 56, bold=True)
    subtitle_font = pygame.font.SysFont(None, 28)
    hud_font = pygame.font.SysFont(None, 40, bold=True)
    big_font = pygame.font.SysFont(None, 64, bold=True)

    best_score = 0

    def new_game():
        return (
            Player(),
            [],
            0.0,
            START_SPEED,
            pygame.time.get_ticks() + random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS),
        )

    player, obstacles, score, speed, next_spawn_at = new_game()
    game_over = False
    new_best = False
    running = True
    particles = []
    shake_timer = 0.0
    shake_strength = 0.0
    flash_timer = 0.0
    flash_life = 1.0
    dust_timer = 0.0

    while running:
        now = pygame.time.get_ticks()
        dt = clock.get_time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_RETURN):
                    if game_over:
                        player, obstacles, score, speed, next_spawn_at = new_game()
                        game_over = False
                        particles = []
                    else:
                        player.jump()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HOME_BUTTON_RECT.collidepoint(event.pos):
                    running = False
                elif game_over:
                    player, obstacles, score, speed, next_spawn_at = new_game()
                    game_over = False
                    particles = []
                else:
                    player.jump()

        if not game_over:
            landed = player.update(dt)
            if landed:
                spawn_dust(particles, player.rect().centerx, GROUND_Y)
            if player.on_ground:
                dust_timer += dt
                if dust_timer > 90:
                    dust_timer = 0
                    spawn_dust(particles, player.rect().centerx - 20, GROUND_Y)

            speed = min(MAX_SPEED, speed + SPEED_RAMP_PER_SEC * dt / 1000.0)
            score += speed * dt / 1000.0

            if now >= next_spawn_at:
                obstacles.append(Obstacle(WIDTH + OBSTACLE_W))
                next_spawn_at = now + random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS)

            for obstacle in obstacles:
                obstacle.update(speed)
            obstacles = [o for o in obstacles if not o.off_screen()]

            player_rect = player.rect().inflate(-14, -6)
            for obstacle in obstacles:
                if player_rect.colliderect(obstacle.rect()):
                    game_over = True
                    if score > best_score:
                        best_score = score
                        new_best = True
                    spawn_crash(particles, player_rect.centerx, player_rect.centery)
                    shake_timer = 260.0
                    shake_strength = 12.0
                    flash_timer = 150.0
                    flash_life = 150.0
                    break

            update_particles(particles, dt)

        if shake_timer > 0:
            shake_timer = max(0.0, shake_timer - dt)
            power = shake_strength * (shake_timer / 260.0)
            shake_x = int(random.uniform(-1, 1) * power)
            shake_y = int(random.uniform(-1, 1) * power)
        else:
            shake_x, shake_y = 0, 0

        if flash_timer > 0:
            flash_timer = max(0.0, flash_timer - dt)

        draw_background(frame, now)

        title_surf = title_font.render("Jumping Jack", True, TITLE_COLOR)
        frame.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 45)))
        subtitle_surf = subtitle_font.render(
            "Click, tap Space, or Up to jump over obstacles!", True, (110, 90, 60)
        )
        frame.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 80)))

        draw_particles(frame, particles)
        for obstacle in obstacles:
            obstacle.draw(frame)
        player.draw(frame)

        score_surf = hud_font.render(f"Score: {int(score)}", True, TEXT_COLOR)
        frame.blit(score_surf, (100, 100))

        draw_home_button(frame)

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            frame.blit(overlay, (0, 0))

            panel = pygame.Rect(0, 0, 440, 230)
            panel.center = (WIDTH // 2, HEIGHT // 2)
            panel_surf = pygame.Surface(panel.size, pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (255, 250, 240, 235), panel_surf.get_rect(), border_radius=24)
            pygame.draw.rect(panel_surf, (170, 100, 60, 255), panel_surf.get_rect(), 5, border_radius=24)
            frame.blit(panel_surf, panel.topleft)

            done_surf = big_font.render(f"Score: {int(score)}", True, (100, 70, 50))
            frame.blit(done_surf, done_surf.get_rect(center=(panel.centerx, panel.top + 65)))

            best_surf = subtitle_font.render(f"Best: {int(best_score)}", True, (120, 90, 60))
            frame.blit(best_surf, best_surf.get_rect(center=(panel.centerx, panel.top + 115)))

            if new_best:
                nb_surf = subtitle_font.render("New Best!", True, (210, 140, 20))
                frame.blit(nb_surf, nb_surf.get_rect(center=(panel.centerx, panel.top + 145)))

            again_surf = subtitle_font.render(
                "Click or press Space to play again", True, (90, 70, 55)
            )
            frame.blit(
                again_surf, again_surf.get_rect(center=(panel.centerx, panel.bottom - 28))
            )

        screen.fill((0, 0, 0))
        screen.blit(frame, (shake_x, shake_y))

        if flash_timer > 0:
            alpha = int(140 * (flash_timer / flash_life))
            flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((255, 90, 70, alpha))
            screen.blit(flash_surf, (0, 0))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(run())
