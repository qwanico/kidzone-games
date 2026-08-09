import math
import random
import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent

WIDTH, HEIGHT = 900, 700

BG_COLOR = (24, 26, 38)
TITLE_COLOR = (120, 220, 255)
SUBTITLE_COLOR = (150, 155, 180)
TEXT_COLOR = (225, 228, 240)
SHIP_COLOR = (120, 220, 255)
BULLET_COLOR = (255, 240, 140)
ASTEROID_COLOR = (170, 175, 200)
BUTTON_COLOR = (60, 66, 96)
BUTTON_HOVER = (86, 94, 132)
OVERLAY_COLOR = (14, 15, 24, 190)
ICON_BG = (40, 44, 58)
ICON_BG_HOVER = (54, 59, 78)
ICON_BORDER = (100, 106, 132)
ICON_COLOR = (255, 255, 255)
ACCENT_COLOR = (140, 255, 170)

CONFETTI_COLORS = [
    (120, 220, 255), (255, 110, 140), (255, 210, 90),
    (140, 255, 170), (180, 140, 255),
]

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAMEOVER = "gameover"

SHIP_TURN_SPEED = 4.2
SHIP_THRUST = 0.25
SHIP_MAX_SPEED = 7.5
SHIP_FRICTION = 0.988
SHIP_RADIUS = 14
LIVES_START = 3
BULLET_SPEED = 9.0
BULLET_LIFE_MS = 900
FIRE_COOLDOWN_MS = 240
RESPAWN_INVULN_MS = 1800

ASTEROID_SIZES = {"large": 40, "medium": 24, "small": 13}
ASTEROID_SPEED_RANGE = {"large": (0.6, 1.4), "medium": (1.0, 2.0), "small": (1.6, 2.8)}
ASTEROID_SCORE = {"large": 20, "medium": 50, "small": 100}


class Particle:
    __slots__ = ("x0", "y0", "vx", "vy", "color", "size", "spawn", "life", "shape")

    def __init__(self, x, y, vx, vy, color, size, spawn, life, shape):
        self.x0, self.y0, self.vx, self.vy = x, y, vx, vy
        self.color, self.size, self.spawn, self.life, self.shape = color, size, spawn, life, shape

    def pos_at(self, now):
        t = (now - self.spawn) / 1000.0
        return self.x0 + self.vx * t, self.y0 + self.vy * t

    def alive(self, now):
        return now - self.spawn < self.life


def spawn_confetti(center, now, count=16, colors=None):
    colors = colors or CONFETTI_COLORS
    particles = []
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(60, 260)
        vx, vy = math.cos(angle) * speed, math.sin(angle) * speed
        color = random.choice(colors)
        size = random.randint(3, 7)
        shape = random.choice(["circle", "square"])
        particles.append(Particle(center[0], center[1], vx, vy, color, size, now, 700, shape))
    return particles


def make_beep(freq=440, ms=80, volume=0.2, kind="sine"):
    try:
        sample_rate = 44100
        n = int(sample_rate * ms / 1000)
        import array
        buf = array.array("h")
        amp = int(32767 * volume)
        for i in range(n):
            t = i / sample_rate
            env = 1.0 - (i / n)
            if kind == "noise":
                val = int(amp * env * random.uniform(-1, 1))
            else:
                f = freq * (1.0 - 0.4 * (i / n)) if kind == "drop" else freq
                val = int(amp * env * math.sin(2 * math.pi * f * t))
            buf.append(val)
            buf.append(val)
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception:
        return None


def wrap_pos(x, y, margin=0):
    if x < -margin:
        x = WIDTH + margin
    elif x > WIDTH + margin:
        x = -margin
    if y < -margin:
        y = HEIGHT + margin
    elif y > HEIGHT + margin:
        y = -margin
    return x, y


class Button:
    def __init__(self, rect, label):
        self.rect = pygame.Rect(rect)
        self.label = label

    def draw(self, surface, font, mouse_pos, now=0):
        hovered = self.rect.collidepoint(mouse_pos)
        color = BUTTON_HOVER if hovered else BUTTON_COLOR
        draw_rect = self.rect.copy()
        if hovered:
            bounce = math.sin(now / 140) * 4
            draw_rect.inflate_ip(6, 6)
            draw_rect.y += int(bounce)
        pygame.draw.rect(surface, color, draw_rect, border_radius=16)
        pygame.draw.rect(surface, TITLE_COLOR, draw_rect, width=2, border_radius=16)
        text_surf = font.render(self.label, True, TEXT_COLOR)
        surface.blit(text_surf, text_surf.get_rect(center=draw_rect.center))


class IconButton:
    """Small square icon button for the always-visible Home/Pause HUD controls."""

    def __init__(self, rect, kind):
        self.rect = pygame.Rect(rect)
        self.kind = kind  # "home" or "pause"

    def draw(self, surface, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        bg = ICON_BG_HOVER if hovered else ICON_BG
        pygame.draw.rect(surface, bg, self.rect, border_radius=12)
        pygame.draw.rect(surface, ICON_BORDER, self.rect, width=2, border_radius=12)
        cx, cy = self.rect.center
        if self.kind == "home":
            roof = [(cx - 15, cy - 1), (cx, cy - 15), (cx + 15, cy - 1)]
            pygame.draw.polygon(surface, ICON_COLOR, roof)
            body = pygame.Rect(0, 0, 20, 14)
            body.midtop = (cx, cy - 3)
            pygame.draw.rect(surface, ICON_COLOR, body)
        else:  # pause
            bar = pygame.Rect(0, 0, 7, 22)
            bar.center = (cx - 7, cy)
            pygame.draw.rect(surface, ICON_COLOR, bar, border_radius=2)
            bar2 = bar.copy()
            bar2.center = (cx + 7, cy)
            pygame.draw.rect(surface, ICON_COLOR, bar2, border_radius=2)


class Asteroid:
    def __init__(self, x, y, size, vx=None, vy=None):
        self.x, self.y = x, y
        self.size = size
        lo, hi = ASTEROID_SPEED_RANGE[size]
        speed = random.uniform(lo, hi)
        angle = random.uniform(0, math.tau)
        self.vx = vx if vx is not None else math.cos(angle) * speed
        self.vy = vy if vy is not None else math.sin(angle) * speed
        self.radius = ASTEROID_SIZES[size]
        self.rot = random.uniform(0, math.tau)
        self.rot_speed = random.uniform(-0.02, 0.02)
        n = random.randint(8, 12)
        self.shape = [
            random.uniform(0.75, 1.15) for _ in range(n)
        ]

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.x, self.y = wrap_pos(self.x, self.y, self.radius)
        self.rot += self.rot_speed

    def points(self):
        n = len(self.shape)
        pts = []
        for i, mult in enumerate(self.shape):
            angle = self.rot + (math.tau * i / n)
            r = self.radius * mult
            pts.append((self.x + math.cos(angle) * r, self.y + math.sin(angle) * r))
        return pts


class Bullet:
    def __init__(self, x, y, vx, vy, spawn):
        self.x, self.y, self.vx, self.vy, self.spawn = x, y, vx, vy, spawn

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.x, self.y = wrap_pos(self.x, self.y)

    def alive(self, now):
        return now - self.spawn < BULLET_LIFE_MS


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self.sound_shoot = make_beep(760, 60, 0.1)
            self.sound_explosion_big = make_beep(140, 220, 0.22, kind="noise")
            self.sound_explosion_small = make_beep(260, 120, 0.18, kind="noise")
            self.sound_thrust = make_beep(90, 60, 0.05)
        except Exception:
            self.sound_shoot = self.sound_explosion_big = self.sound_explosion_small = self.sound_thrust = None

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Asteroids")

        self.font_title = pygame.font.SysFont("arial", 60, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 22)
        self.font_hud = pygame.font.SysFont("arial", 24, bold=True)
        self.font_button = pygame.font.SysFont("arial", 26, bold=True)

        self.start_button = Button((WIDTH // 2 - 140, 460, 280, 70), "Start Game")
        self.resume_button = Button((WIDTH // 2 - 160, 340, 320, 70), "Resume")
        self.restart_button = Button((WIDTH // 2 - 160, 430, 320, 70), "Restart")
        self.pause_home_button = Button((WIDTH // 2 - 160, 520, 320, 70), "Home")
        self.menu_button = Button((WIDTH // 2 - 160, 500, 320, 70), "Main Menu")
        self.home_button = IconButton((20, 20, 60, 50), "home")
        self.pause_button = IconButton((90, 20, 60, 50), "pause")

        self.stars = [
            (random.uniform(0, WIDTH), random.uniform(0, HEIGHT), random.uniform(0.5, 1.0))
            for _ in range(80)
        ]

        self.particles = []
        self.state = STATE_MENU
        self.quit_requested = False
        self.pause_started = None
        self.pause_accum = 0
        self.reset_game()

    # ---------- lifecycle ----------
    def reset_game(self):
        self.score = 0
        self.lives = LIVES_START
        self.wave = 1
        self.respawn_ship()
        self.last_shot = 0
        self.bullets = []
        self.spawn_wave()

    def respawn_ship(self):
        self.ship_x, self.ship_y = WIDTH / 2, HEIGHT / 2
        self.ship_vx, self.ship_vy = 0.0, 0.0
        self.ship_angle = -90.0
        self.thrusting = False
        self.invuln_until = self.game_now() + RESPAWN_INVULN_MS

    def spawn_wave(self):
        self.asteroids = []
        count = 3 + self.wave
        for _ in range(count):
            while True:
                x = random.uniform(0, WIDTH)
                y = random.uniform(0, HEIGHT)
                if math.hypot(x - self.ship_x, y - self.ship_y) > 140:
                    break
            self.asteroids.append(Asteroid(x, y, "large"))

    def start_game(self):
        self.reset_game()
        self.state = STATE_PLAYING

    def restart_game(self):
        self.reset_game()
        self.pause_started = None
        self.state = STATE_PLAYING

    def enter_pause(self):
        self.state = STATE_PAUSED
        self.pause_started = pygame.time.get_ticks()

    def resume_game(self):
        if self.pause_started is not None:
            self.pause_accum += pygame.time.get_ticks() - self.pause_started
            self.pause_started = None
        self.state = STATE_PLAYING

    def game_now(self):
        """Game-clock ms, excluding time spent paused (avoids a catch-up jump on resume)."""
        if self.state == STATE_PAUSED and self.pause_started is not None:
            return self.pause_started - self.pause_accum
        return pygame.time.get_ticks() - self.pause_accum

    # ---------- input ----------
    def handle_menu_click(self, pos):
        if self.start_button.rect.collidepoint(pos):
            self.start_game()

    def handle_pause_click(self, pos):
        if self.resume_button.rect.collidepoint(pos):
            self.resume_game()
        elif self.restart_button.rect.collidepoint(pos):
            self.restart_game()
        elif self.pause_home_button.rect.collidepoint(pos):
            self.quit_requested = True

    def handle_gameover_click(self, pos):
        if self.menu_button.rect.collidepoint(pos):
            self.state = STATE_MENU

    def handle_click(self, pos):
        if self.home_button.rect.collidepoint(pos):
            self.quit_requested = True
        elif self.pause_button.rect.collidepoint(pos):
            self.enter_pause()

    def fire_bullet(self):
        now = self.game_now()
        if now - self.last_shot < FIRE_COOLDOWN_MS:
            return
        self.last_shot = now
        rad = math.radians(self.ship_angle)
        nose_x = self.ship_x + math.cos(rad) * SHIP_RADIUS
        nose_y = self.ship_y + math.sin(rad) * SHIP_RADIUS
        vx = self.ship_vx + math.cos(rad) * BULLET_SPEED
        vy = self.ship_vy + math.sin(rad) * BULLET_SPEED
        self.bullets.append(Bullet(nose_x, nose_y, vx, vy, now))
        if self.sound_shoot:
            self.sound_shoot.play()

    # ---------- update ----------
    def update(self):
        now = self.game_now()
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.ship_angle -= SHIP_TURN_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.ship_angle += SHIP_TURN_SPEED

        self.thrusting = bool(keys[pygame.K_UP] or keys[pygame.K_w])
        if self.thrusting:
            rad = math.radians(self.ship_angle)
            self.ship_vx += math.cos(rad) * SHIP_THRUST
            self.ship_vy += math.sin(rad) * SHIP_THRUST
            speed = math.hypot(self.ship_vx, self.ship_vy)
            if speed > SHIP_MAX_SPEED:
                scale = SHIP_MAX_SPEED / speed
                self.ship_vx *= scale
                self.ship_vy *= scale

        self.ship_vx *= SHIP_FRICTION
        self.ship_vy *= SHIP_FRICTION
        self.ship_x += self.ship_vx
        self.ship_y += self.ship_vy
        self.ship_x, self.ship_y = wrap_pos(self.ship_x, self.ship_y, SHIP_RADIUS)

        for a in self.asteroids:
            a.update()
        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.alive(now)]

        self.check_bullet_hits(now)
        self.check_ship_hit(now)

        if self.particles:
            self.particles = [p for p in self.particles if p.alive(now)]

        if not self.asteroids:
            self.wave += 1
            self.spawn_wave()

    def check_bullet_hits(self, now):
        remaining_bullets = []
        for b in self.bullets:
            hit_asteroid = None
            for a in self.asteroids:
                if math.hypot(b.x - a.x, b.y - a.y) < a.radius:
                    hit_asteroid = a
                    break
            if hit_asteroid is not None:
                self.destroy_asteroid(hit_asteroid, now)
            else:
                remaining_bullets.append(b)
        self.bullets = remaining_bullets

    def destroy_asteroid(self, asteroid, now):
        self.asteroids.remove(asteroid)
        self.score += ASTEROID_SCORE[asteroid.size]
        if asteroid.size == "large":
            new_size = "medium"
            snd = self.sound_explosion_big
        elif asteroid.size == "medium":
            new_size = "small"
            snd = self.sound_explosion_small
        else:
            new_size = None
            snd = self.sound_explosion_small
        if snd:
            snd.play()
        self.particles.extend(spawn_confetti((asteroid.x, asteroid.y), now, count=14, colors=[ASTEROID_COLOR, BULLET_COLOR]))
        if new_size is not None:
            for _ in range(2):
                self.asteroids.append(Asteroid(asteroid.x, asteroid.y, new_size))

    def check_ship_hit(self, now):
        if now < self.invuln_until:
            return
        for a in self.asteroids:
            if math.hypot(self.ship_x - a.x, self.ship_y - a.y) < a.radius + SHIP_RADIUS * 0.6:
                self.lives -= 1
                self.particles.extend(spawn_confetti((self.ship_x, self.ship_y), now, count=24, colors=[(255, 90, 90), SHIP_COLOR]))
                if self.lives <= 0:
                    self.state = STATE_GAMEOVER
                else:
                    self.respawn_ship()
                return

    # ---------- draw ----------
    def draw_stars(self, now):
        for x, y, tw in self.stars:
            b = (math.sin(now / 700 * tw) + 1) / 2
            c = int(120 + b * 80)
            pygame.draw.circle(self.screen, (c, c, c + 20), (int(x), int(y)), 1)

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

    def draw_title(self, now, y=170):
        title = "ASTEROIDS"
        letter_surfs = [self.font_title.render(ch, True, TITLE_COLOR) for ch in title]
        total_w = sum(s.get_width() for s in letter_surfs)
        x = WIDTH // 2 - total_w // 2
        for i, surf in enumerate(letter_surfs):
            bob = math.sin(now / 260 + i * 0.5) * 8
            rect = surf.get_rect(midtop=(x + surf.get_width() // 2, y + int(bob)))
            self.screen.blit(surf, rect)
            x += surf.get_width()

    def draw_menu(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_stars(now)
        self.draw_title(now)
        subtitle = self.font_subtitle.render(
            "Arrows/WASD to rotate + thrust, Space to shoot.", True, SUBTITLE_COLOR
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 290)))
        self.start_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_ship(self, now):
        if now < self.invuln_until and (now // 120) % 2 == 0:
            return
        rad = math.radians(self.ship_angle)
        nose = (self.ship_x + math.cos(rad) * SHIP_RADIUS, self.ship_y + math.sin(rad) * SHIP_RADIUS)
        back_l_ang = rad + math.radians(150)
        back_r_ang = rad - math.radians(150)
        back_l = (self.ship_x + math.cos(back_l_ang) * SHIP_RADIUS, self.ship_y + math.sin(back_l_ang) * SHIP_RADIUS)
        back_r = (self.ship_x + math.cos(back_r_ang) * SHIP_RADIUS, self.ship_y + math.sin(back_r_ang) * SHIP_RADIUS)
        pygame.draw.polygon(self.screen, SHIP_COLOR, [nose, back_l, back_r], width=0)
        pygame.draw.polygon(self.screen, (255, 255, 255), [nose, back_l, back_r], width=2)

        if self.thrusting and (now // 80) % 2 == 0:
            flame_ang = rad + math.pi
            flame_tip = (self.ship_x + math.cos(flame_ang) * SHIP_RADIUS * 1.8,
                         self.ship_y + math.sin(flame_ang) * SHIP_RADIUS * 1.8)
            mid = ((back_l[0] + back_r[0]) / 2, (back_l[1] + back_r[1]) / 2)
            pygame.draw.polygon(self.screen, (255, 170, 60), [back_l, flame_tip, back_r])

    def draw_playing(self):
        now = self.game_now()
        self.screen.fill(BG_COLOR)
        self.draw_stars(now)

        for a in self.asteroids:
            pygame.draw.polygon(self.screen, ASTEROID_COLOR, a.points(), width=2)

        for b in self.bullets:
            pygame.draw.circle(self.screen, BULLET_COLOR, (int(b.x), int(b.y)), 3)

        self.draw_ship(now)
        self.draw_particles(now)

        hud = self.font_hud.render(
            f"Score: {self.score}    Wave: {self.wave}    Lives: {self.lives}", True, TEXT_COLOR
        )
        self.screen.blit(hud, (20, 20))

        mouse_pos = pygame.mouse.get_pos()
        self.home_button.draw(self.screen, mouse_pos)
        self.pause_button.draw(self.screen, mouse_pos)

    def draw_paused(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))
        paused_surf = self.font_title.render("Paused", True, TEXT_COLOR)
        self.screen.blit(paused_surf, paused_surf.get_rect(center=(WIDTH // 2, 230)))
        self.resume_button.draw(self.screen, self.font_button, mouse_pos, now=now)
        self.restart_button.draw(self.screen, self.font_button, mouse_pos, now=now)
        self.pause_home_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_gameover(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        self.screen.fill(BG_COLOR)
        self.draw_stars(now)
        bounce = math.sin(now / 180) * 6
        text = self.font_title.render("Game Over", True, (255, 110, 140))
        self.screen.blit(text, text.get_rect(center=(WIDTH // 2, 230 + int(bounce))))
        score_surf = self.font_subtitle.render(
            f"Final score: {self.score}   (reached wave {self.wave})", True, TEXT_COLOR
        )
        self.screen.blit(score_surf, score_surf.get_rect(center=(WIDTH // 2, 300)))
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
            clock.tick(60)
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
                    elif event.key == pygame.K_SPACE and self.state == STATE_PLAYING:
                        self.fire_bullet()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == STATE_MENU:
                        self.handle_menu_click(event.pos)
                    elif self.state == STATE_PLAYING:
                        self.handle_click(event.pos)
                    elif self.state == STATE_PAUSED:
                        self.handle_pause_click(event.pos)
                    elif self.state == STATE_GAMEOVER:
                        self.handle_gameover_click(event.pos)

            if self.state == STATE_PLAYING:
                self.update()
            self.draw()

            if self.quit_requested:
                running = False

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
