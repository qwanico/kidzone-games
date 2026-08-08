import math
import random
import sys
from pathlib import Path

import pygame
from pygame import Vector2

BASE_DIR = Path(__file__).parent
SOUNDS_DIR = BASE_DIR / "sounds"

WIDTH, HEIGHT = 900, 800

BG_COLOR = (24, 26, 38)
TEXT_COLOR = (225, 228, 240)
TITLE_COLOR = (120, 220, 255)
SUBTITLE_COLOR = (150, 155, 180)
ACCENT = (255, 120, 170)
ACCENT_DARK = (220, 90, 140)
CORRECT_COLOR = (100, 220, 150)
WRONG_COLOR = (255, 100, 110)
PLAYFIELD_COLOR = (32, 35, 52)
WALL_COLOR = (90, 96, 130)
FLIPPER_COLOR = (255, 200, 90)
BALL_COLOR = (230, 235, 245)

CONFETTI_COLORS = [
    (255, 99, 132), (255, 205, 86), (75, 192, 192),
    (54, 162, 235), (153, 102, 255), (120, 220, 255),
]

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAMEOVER = "gameover"

# Playfield geometry
PF_LEFT, PF_RIGHT = 60, 660
PF_TOP, PF_BOTTOM = 90, 760

GRAVITY = 1500.0
MAX_SPEED = 1100.0
BALL_RADIUS = 11
BALL_LIVES = 3

LEFT_PIVOT = Vector2(PF_LEFT + 150, PF_BOTTOM - 40)
RIGHT_PIVOT = Vector2(PF_RIGHT - 150, PF_BOTTOM - 40)
FLIPPER_LEN = 95
FLIPPER_THICKNESS = 16

LEFT_REST_DEG = 55
LEFT_ACTIVE_DEG = -25
RIGHT_REST_DEG = 180 - LEFT_REST_DEG
RIGHT_ACTIVE_DEG = 180 - LEFT_ACTIVE_DEG
FLIPPER_ANGULAR_SPEED = math.radians(950)  # deg/s -> rad/s of travel

BUMPER_SCORE = 100
BUMPER_KICK = 620

BUMPERS = [
    {"pos": Vector2(360, 260), "r": 30},
    {"pos": Vector2(255, 340), "r": 24},
    {"pos": Vector2(465, 340), "r": 24},
]

WALLS = [
    (Vector2(PF_LEFT, PF_TOP), Vector2(PF_LEFT, PF_BOTTOM - 170)),
    (Vector2(PF_RIGHT, PF_TOP), Vector2(PF_RIGHT, PF_BOTTOM - 170)),
    (Vector2(PF_LEFT, PF_TOP), Vector2(PF_RIGHT, PF_TOP)),
    (Vector2(PF_LEFT, PF_BOTTOM - 170), Vector2(LEFT_PIVOT.x - 55, PF_BOTTOM - 55)),
    (Vector2(PF_RIGHT, PF_BOTTOM - 170), Vector2(RIGHT_PIVOT.x + 55, PF_BOTTOM - 55)),
]

LAUNCH_POS = Vector2((PF_LEFT + PF_RIGHT) / 2, PF_TOP + 40)


class Particle:
    __slots__ = ("x0", "y0", "vx", "vy", "color", "size", "spawn", "life", "shape")

    def __init__(self, x, y, vx, vy, color, size, spawn, life, shape):
        self.x0, self.y0 = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.size = size
        self.spawn = spawn
        self.life = life
        self.shape = shape

    def pos_at(self, now):
        t = (now - self.spawn) / 1000.0
        x = self.x0 + self.vx * t
        y = self.y0 + self.vy * t + 0.5 * 650 * t * t
        return x, y

    def alive(self, now):
        return now - self.spawn < self.life


def spawn_confetti(center, now, count=26, colors=None):
    particles = []
    colors = colors or CONFETTI_COLORS
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(120, 340)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        color = random.choice(colors)
        size = random.randint(3, 7)
        shape = random.choice(["circle", "square"])
        particles.append(Particle(center[0], center[1], vx, vy, color, size, now, 500, shape))
    return particles


def closest_point_on_segment(p, a, b):
    ab = b - a
    length_sq = ab.length_squared()
    if length_sq == 0:
        return Vector2(a)
    t = (p - a).dot(ab) / length_sq
    t = max(0.0, min(1.0, t))
    return a + ab * t


class Ball:
    def __init__(self, pos, vel):
        self.pos = Vector2(pos)
        self.vel = Vector2(vel)
        self.r = BALL_RADIUS

    def integrate(self, dt):
        self.vel.y += GRAVITY * dt
        if self.vel.length_squared() > MAX_SPEED * MAX_SPEED:
            self.vel.scale_to_length(MAX_SPEED)
        self.pos += self.vel * dt


class Flipper:
    def __init__(self, pivot, rest_deg, active_deg, side):
        self.pivot = Vector2(pivot)
        self.rest_angle = math.radians(rest_deg)
        self.active_angle = math.radians(active_deg)
        self.angle = self.rest_angle
        self.omega = 0.0
        self.side = side
        self.active = False

    def tip(self, angle=None):
        angle = self.angle if angle is None else angle
        return self.pivot + Vector2(math.cos(angle), math.sin(angle)) * FLIPPER_LEN

    def update(self, dt, active):
        self.active = active
        target = self.active_angle if active else self.rest_angle
        diff = target - self.angle
        max_step = FLIPPER_ANGULAR_SPEED * dt
        if abs(diff) <= max_step:
            new_angle = target
        else:
            new_angle = self.angle + max_step * (1 if diff > 0 else -1)
        self.omega = (new_angle - self.angle) / dt if dt > 0 else 0.0
        self.angle = new_angle

    def collide(self, ball):
        cp = closest_point_on_segment(ball.pos, self.pivot, self.tip())
        diff = ball.pos - cp
        dist = diff.length()
        min_dist = ball.r + FLIPPER_THICKNESS / 2
        if dist >= min_dist or dist == 0:
            return False
        normal = diff / dist
        ball.pos = cp + normal * min_dist

        r_vec = cp - self.pivot
        point_vel = Vector2(-r_vec.y, r_vec.x) * self.omega

        rel_vel = ball.vel - point_vel
        vn = rel_vel.dot(normal)
        if vn < 0:
            rel_vel -= normal * (1.8 * vn)
        ball.vel = rel_vel + point_vel
        # extra transfer of flipper motion for a punchy, real "flick" feel
        ball.vel += point_vel * 0.9
        return True


class Button:
    def __init__(self, rect, label, color=ACCENT, hover=ACCENT_DARK):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.hover = hover

    def draw(self, surface, font, mouse_pos, now=0, text_color=(15, 20, 25)):
        hovered = self.rect.collidepoint(mouse_pos)
        draw_rect = self.rect.copy()
        if hovered:
            bounce = math.sin(now / 140) * 4
            draw_rect.inflate_ip(6, 6)
            draw_rect.y += int(bounce)
        color = self.hover if hovered else self.color
        pygame.draw.rect(surface, color, draw_rect, border_radius=14)
        pygame.draw.rect(surface, (250, 250, 255), draw_rect, width=2, border_radius=14)
        text_surf = font.render(self.label, True, text_color)
        surface.blit(text_surf, text_surf.get_rect(center=draw_rect.center))

    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self.wrong_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.wav"))
        except pygame.error:
            self.wrong_sound = None

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pinball")

        self.font_title = pygame.font.SysFont("arial", 56, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 22)
        self.font_button = pygame.font.SysFont("arial", 24, bold=True)
        self.font_icon = pygame.font.SysFont("arial", 20, bold=True)
        self.font_stat = pygame.font.SysFont("arial", 26, bold=True)
        self.font_big = pygame.font.SysFont("arial", 54, bold=True)

        self.start_button = Button((WIDTH // 2 - 140, 480, 280, 90), "Start")
        self.pause_button = Button((WIDTH - 90, 20, 60, 46), "II")
        self.resume_button = Button((WIDTH // 2 - 160, 340, 320, 80), "Resume")
        self.quit_button = Button((WIDTH // 2 - 160, 440, 320, 80), "Quit")
        self.play_again_button = Button((WIDTH // 2 - 160, 480, 320, 80), "Play Again")
        self.menu_button = Button((WIDTH // 2 - 160, 580, 320, 80), "Menu")

        self.bg_shapes = [
            {
                "x": random.uniform(30, WIDTH - 30),
                "y": random.uniform(30, HEIGHT - 30),
                "r": random.randint(10, 20),
                "speed": random.uniform(0.4, 1.0),
                "phase": random.uniform(0, math.tau),
                "color": random.choice(CONFETTI_COLORS),
            }
            for _ in range(10)
        ]

        self.state = STATE_MENU
        self.quit_requested = False
        self.particles = []
        self.bumper_pulse = {}
        self.left_key = False
        self.right_key = False

        self.new_game()

    def new_game(self):
        self.score = 0
        self.balls_left = BALL_LIVES
        self.left_flipper = Flipper(LEFT_PIVOT, LEFT_REST_DEG, LEFT_ACTIVE_DEG, "left")
        self.right_flipper = Flipper(RIGHT_PIVOT, RIGHT_REST_DEG, RIGHT_ACTIVE_DEG, "right")
        self.particles = []
        self.bumper_pulse = {id(b): 0 for b in BUMPERS}
        self.spawn_ball()

    def spawn_ball(self):
        vel = (random.uniform(-130, 130), random.uniform(-40, 60))
        self.ball = Ball(LAUNCH_POS, vel)
        self.ball_in_play = True

    def start_game(self):
        self.new_game()
        self.state = STATE_PLAYING

    def enter_pause(self):
        self.state = STATE_PAUSED

    def resume_game(self):
        self.state = STATE_PLAYING

    def handle_menu_click(self, pos):
        if self.start_button.is_hovered(pos):
            self.start_game()

    def handle_pause_click(self, pos):
        if self.resume_button.is_hovered(pos):
            self.resume_game()
        elif self.quit_button.is_hovered(pos):
            self.quit_requested = True

    def handle_gameover_click(self, pos):
        if self.play_again_button.is_hovered(pos):
            self.start_game()
        elif self.menu_button.is_hovered(pos):
            self.state = STATE_MENU

    def handle_pause_button_click(self, pos):
        if self.pause_button.is_hovered(pos):
            self.enter_pause()

    def resolve_wall_collisions(self, ball):
        for a, b in WALLS:
            cp = closest_point_on_segment(ball.pos, a, b)
            diff = ball.pos - cp
            dist = diff.length()
            if dist < ball.r and dist > 0:
                normal = diff / dist
                ball.pos = cp + normal * ball.r
                vn = ball.vel.dot(normal)
                if vn < 0:
                    ball.vel -= normal * (1.7 * vn)

    def resolve_bumper_collisions(self, ball, now):
        for bumper in BUMPERS:
            diff = ball.pos - bumper["pos"]
            dist = diff.length()
            min_dist = ball.r + bumper["r"]
            if dist < min_dist and dist > 0:
                normal = diff / dist
                ball.pos = bumper["pos"] + normal * min_dist
                ball.vel = normal * BUMPER_KICK
                self.score += BUMPER_SCORE
                self.bumper_pulse[id(bumper)] = now
                self.particles.extend(
                    spawn_confetti(bumper["pos"], now, count=14, colors=[FLIPPER_COLOR, ACCENT, (255, 255, 255)])
                )

    def update_physics(self, dt):
        substeps = 3
        sub_dt = dt / substeps
        now = pygame.time.get_ticks()
        for _ in range(substeps):
            if not self.ball_in_play:
                break
            self.ball.integrate(sub_dt)
            self.resolve_wall_collisions(self.ball)
            self.resolve_bumper_collisions(self.ball, now)
            self.left_flipper.collide(self.ball)
            self.right_flipper.collide(self.ball)

            if self.ball.pos.y - self.ball.r > HEIGHT + 20:
                self.lose_ball()
                break

    def lose_ball(self):
        self.ball_in_play = False
        self.balls_left -= 1
        if self.wrong_sound:
            self.wrong_sound.play()
        if self.balls_left <= 0:
            self.state = STATE_GAMEOVER
        else:
            self.spawn_ball()

    def update(self, dt):
        now = pygame.time.get_ticks()
        if self.particles:
            self.particles = [p for p in self.particles if p.alive(now)]
        if self.state != STATE_PLAYING:
            return
        self.left_flipper.update(dt, self.left_key)
        self.right_flipper.update(dt, self.right_key)
        self.update_physics(dt)

    def draw_bg_shapes(self, now):
        for shape in self.bg_shapes:
            bob = math.sin(now / 900 * shape["speed"] + shape["phase"]) * 14
            r = shape["r"]
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*shape["color"], 35), (r, r), r)
            self.screen.blit(surf, (shape["x"] - r, shape["y"] - r + bob))

    def draw_particles(self, now):
        for p in self.particles:
            x, y = p.pos_at(now)
            t = (now - p.spawn) / p.life
            alpha = max(0, int(255 * (1 - t)))
            surf = pygame.Surface((p.size * 2, p.size * 2), pygame.SRCALPHA)
            if p.shape == "circle":
                pygame.draw.circle(surf, (*p.color, alpha), (p.size, p.size), p.size)
            else:
                pygame.draw.rect(surf, (*p.color, alpha), surf.get_rect())
            self.screen.blit(surf, (x - p.size, y - p.size))

    def draw_title(self, now, y=110, text="Pinball"):
        letter_surfs = [self.font_title.render(ch, True, TITLE_COLOR) for ch in text]
        total_w = sum(s.get_width() for s in letter_surfs)
        x = WIDTH // 2 - total_w // 2
        for i, surf in enumerate(letter_surfs):
            bob = math.sin(now / 260 + i * 0.6) * 7
            rect = surf.get_rect(midtop=(x + surf.get_width() // 2, y + int(bob)))
            self.screen.blit(surf, rect)
            x += surf.get_width()

    def draw_menu(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)
        self.draw_title(now, 220)
        subtitle_surf = self.font_subtitle.render(
            "LEFT / RIGHT arrows control the flippers.", True, SUBTITLE_COLOR
        )
        self.screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 330)))
        rules_surf = self.font_subtitle.render(
            f"You have {BALL_LIVES} balls. Rack up points on the bumpers!", True, SUBTITLE_COLOR
        )
        self.screen.blit(rules_surf, rules_surf.get_rect(center=(WIDTH // 2, 364)))
        self.start_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_table(self, now):
        pf_rect = pygame.Rect(PF_LEFT, PF_TOP, PF_RIGHT - PF_LEFT, PF_BOTTOM - PF_TOP)
        pygame.draw.rect(self.screen, PLAYFIELD_COLOR, pf_rect, border_radius=10)

        for a, b in WALLS:
            pygame.draw.line(self.screen, WALL_COLOR, a, b, 6)

        for bumper in BUMPERS:
            pulse_t = now - self.bumper_pulse.get(id(bumper), -9999)
            glow = max(0, 1 - pulse_t / 260) if pulse_t < 260 else 0
            r = int(bumper["r"] + glow * 8)
            color = tuple(min(255, int(c + glow * 90)) for c in (ACCENT_DARK if pulse_t >= 260 else ACCENT))
            pygame.draw.circle(self.screen, color, bumper["pos"], r)
            pygame.draw.circle(self.screen, (255, 255, 255), bumper["pos"], r, width=2)

        for flipper in (self.left_flipper, self.right_flipper):
            tip = flipper.tip()
            pygame.draw.line(self.screen, FLIPPER_COLOR, flipper.pivot, tip, FLIPPER_THICKNESS)
            pygame.draw.circle(self.screen, FLIPPER_COLOR, flipper.pivot, FLIPPER_THICKNESS // 2)
            pygame.draw.circle(self.screen, FLIPPER_COLOR, tip, FLIPPER_THICKNESS // 2)

        if self.ball_in_play:
            pygame.draw.circle(self.screen, BALL_COLOR, self.ball.pos, self.ball.r)
            pygame.draw.circle(self.screen, (140, 145, 165), self.ball.pos, self.ball.r, width=1)

    def draw_playing(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)

        score_surf = self.font_stat.render(f"Score: {self.score}", True, ACCENT)
        self.screen.blit(score_surf, (30, 24))

        balls_surf = self.font_stat.render(f"Balls: {self.balls_left}", True, TEXT_COLOR)
        self.screen.blit(balls_surf, balls_surf.get_rect(topright=(WIDTH - 170, 24)))

        self.draw_table(now)
        self.draw_particles(now)
        self.pause_button.draw(self.screen, self.font_icon, mouse_pos, now=now)

    def draw_paused(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 18, 200))
        self.screen.blit(overlay, (0, 0))
        paused_surf = self.font_title.render("Paused", True, TITLE_COLOR)
        self.screen.blit(paused_surf, paused_surf.get_rect(center=(WIDTH // 2, 240)))
        self.resume_button.draw(self.screen, self.font_button, mouse_pos, now=now)
        self.quit_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_gameover(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        self.draw_playing()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 18, 205))
        self.screen.blit(overlay, (0, 0))

        bounce = math.sin(now / 200) * 6
        msg_surf = self.font_big.render("Game Over", True, WRONG_COLOR)
        self.screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH // 2, 340 + int(bounce))))

        score_surf = self.font_stat.render(f"Final Score: {self.score}", True, TEXT_COLOR)
        self.screen.blit(score_surf, score_surf.get_rect(center=(WIDTH // 2, 400)))

        self.play_again_button.draw(self.screen, self.font_button, mouse_pos, now=now)
        self.menu_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw(self):
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_PLAYING:
            self.draw_playing()
        elif self.state == STATE_PAUSED:
            self.draw_playing()
            self.draw_paused()
        elif self.state == STATE_GAMEOVER:
            self.draw_gameover()
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = min(clock.tick(60) / 1000.0, 1 / 30) or (1 / 60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == STATE_PLAYING:
                            self.enter_pause()
                        elif self.state == STATE_PAUSED:
                            self.resume_game()
                        else:
                            running = False
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self.left_key = True
                    elif event.key in (pygame.K_RIGHT, pygame.K_l):
                        self.right_key = True
                elif event.type == pygame.KEYUP:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.left_key = False
                    elif event.key in (pygame.K_RIGHT, pygame.K_l):
                        self.right_key = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == STATE_MENU:
                        self.handle_menu_click(event.pos)
                    elif self.state == STATE_PLAYING:
                        self.handle_pause_button_click(event.pos)
                    elif self.state == STATE_PAUSED:
                        self.handle_pause_click(event.pos)
                    elif self.state == STATE_GAMEOVER:
                        self.handle_gameover_click(event.pos)

            self.update(dt)
            self.draw()

            if self.quit_requested:
                running = False

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
