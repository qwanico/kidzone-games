import asyncio
import math
import random
import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent / "space_invaders_assets"

WIDTH, HEIGHT = 900, 700

BG_COLOR = (24, 26, 38)
TITLE_COLOR = (120, 220, 255)
SUBTITLE_COLOR = (150, 155, 180)
TEXT_COLOR = (225, 228, 240)
ACCENT_COLOR = (140, 255, 170)
PLAYER_COLOR = (120, 220, 255)
ENEMY_COLORS = [(255, 110, 140), (255, 190, 90), (180, 140, 255)]
BULLET_COLOR = (255, 240, 140)
ENEMY_BULLET_COLOR = (255, 110, 110)
BUTTON_COLOR = (60, 66, 96)
BUTTON_HOVER = (86, 94, 132)
OVERLAY_COLOR = (14, 15, 24, 190)

CONFETTI_COLORS = [
    (120, 220, 255), (255, 110, 140), (255, 210, 90),
    (140, 255, 170), (180, 140, 255),
]

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAMEOVER = "gameover"
STATE_WIN_WAVE = "wave_clear"

PLAYER_W, PLAYER_H = 50, 26
PLAYER_SPEED = 6.5
PLAYER_LIVES = 3
BULLET_W, BULLET_H = 4, 14
BULLET_SPEED = 9.0
ENEMY_BULLET_SPEED = 5.0

ENEMY_ROWS = 4
ENEMY_COLS = 8
ENEMY_W, ENEMY_H = 40, 28
ENEMY_GAP_X, ENEMY_GAP_Y = 18, 18
ENEMY_TOP = 90
ENEMY_STEP_DOWN = 24


class Particle:
    __slots__ = ("x0", "y0", "vx", "vy", "color", "size", "spawn", "life", "shape")

    def __init__(self, x, y, vx, vy, color, size, spawn, life, shape):
        self.x0, self.y0, self.vx, self.vy = x, y, vx, vy
        self.color, self.size, self.spawn, self.life, self.shape = color, size, spawn, life, shape

    def pos_at(self, now):
        t = (now - self.spawn) / 1000.0
        return self.x0 + self.vx * t, self.y0 + self.vy * t + 0.5 * 500 * t * t

    def alive(self, now):
        return now - self.spawn < self.life


def spawn_confetti(center, now, count=18, colors=None):
    colors = colors or CONFETTI_COLORS
    particles = []
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(100, 320)
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


class Enemy:
    def __init__(self, col, row, x, y):
        self.col, self.row = col, row
        self.x, self.y = x, y
        self.alive = True
        self.color = ENEMY_COLORS[row % len(ENEMY_COLORS)]

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), ENEMY_W, ENEMY_H)


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self.sound_shoot = make_beep(700, 60, 0.12)
            self.sound_hit = make_beep(220, 140, 0.2, kind="drop")
            self.sound_explosion = make_beep(120, 180, 0.22, kind="noise")
            self.sound_lose_life = make_beep(150, 260, 0.25, kind="drop")
        except Exception:
            self.sound_shoot = self.sound_hit = self.sound_explosion = self.sound_lose_life = None

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Space Invaders")

        self.font_title = pygame.font.SysFont("arial", 60, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 22)
        self.font_hud = pygame.font.SysFont("arial", 24, bold=True)
        self.font_button = pygame.font.SysFont("arial", 26, bold=True)
        self.font_big = pygame.font.SysFont("arial", 46, bold=True)

        self.start_button = Button((WIDTH // 2 - 140, 460, 280, 70), "Start Game")
        self.resume_button = Button((WIDTH // 2 - 160, 340, 320, 70), "Resume")
        self.quit_button = Button((WIDTH // 2 - 160, 430, 320, 70), "Quit")
        self.menu_button = Button((WIDTH // 2 - 160, 500, 320, 70), "Main Menu")
        self.next_wave_button = Button((WIDTH // 2 - 160, 460, 320, 70), "Next Wave")
        self.pause_button = Button((WIDTH - 90, 20, 60, 44), "II")

        self.bg_shapes = [
            {
                "x": random.uniform(40, WIDTH - 40),
                "y": random.uniform(40, HEIGHT - 40),
                "r": random.randint(1, 3),
                "speed": random.uniform(0.2, 0.6),
                "phase": random.uniform(0, math.tau),
            }
            for _ in range(60)
        ]

        self.particles = []
        self.state = STATE_MENU
        self.quit_requested = False
        self.reset_game()

    # ---------- lifecycle ----------
    def reset_game(self):
        self.score = 0
        self.lives = PLAYER_LIVES
        self.wave = 1
        self.player_x = WIDTH / 2 - PLAYER_W / 2
        self.player_bullet = None
        self.enemy_bullets = []
        self.hit_flash_until = 0
        self.build_wave()

    def build_wave(self):
        self.enemies = []
        total_w = ENEMY_COLS * ENEMY_W + (ENEMY_COLS - 1) * ENEMY_GAP_X
        start_x = (WIDTH - total_w) / 2
        for row in range(ENEMY_ROWS):
            for col in range(ENEMY_COLS):
                x = start_x + col * (ENEMY_W + ENEMY_GAP_X)
                y = ENEMY_TOP + row * (ENEMY_H + ENEMY_GAP_Y)
                self.enemies.append(Enemy(col, row, x, y))
        base_speed = 1.0 + (self.wave - 1) * 0.35
        self.enemy_dir = 1
        self.enemy_speed = base_speed
        self.enemy_shot_chance = min(0.02 + (self.wave - 1) * 0.006, 0.06)
        self.enemy_move_timer = 0

    def start_game(self):
        self.reset_game()
        self.state = STATE_PLAYING

    def next_wave(self):
        self.wave += 1
        self.build_wave()
        self.state = STATE_PLAYING

    def enter_pause(self):
        self.state = STATE_PAUSED

    def resume_game(self):
        self.state = STATE_PLAYING

    # ---------- input ----------
    def handle_menu_click(self, pos):
        if self.start_button.rect.collidepoint(pos):
            self.start_game()

    def handle_pause_click(self, pos):
        if self.resume_button.rect.collidepoint(pos):
            self.resume_game()
        elif self.quit_button.rect.collidepoint(pos):
            self.quit_requested = True

    def handle_gameover_click(self, pos):
        if self.menu_button.rect.collidepoint(pos):
            self.state = STATE_MENU

    def handle_wave_clear_click(self, pos):
        if self.next_wave_button.rect.collidepoint(pos):
            self.next_wave()

    def handle_click(self, pos):
        if self.pause_button.rect.collidepoint(pos):
            self.enter_pause()

    def fire_player_bullet(self):
        if self.player_bullet is None:
            self.player_bullet = pygame.Rect(
                int(self.player_x + PLAYER_W / 2 - BULLET_W / 2),
                HEIGHT - 60,
                BULLET_W, BULLET_H,
            )
            if self.sound_shoot:
                self.sound_shoot.play()

    # ---------- update ----------
    def update(self):
        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player_x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player_x += PLAYER_SPEED
        self.player_x = max(0, min(WIDTH - PLAYER_W, self.player_x))

        self.update_enemies(now)
        self.update_bullets()
        self.check_collisions(now)

        if self.particles:
            self.particles = [p for p in self.particles if p.alive(now)]

        alive_enemies = [e for e in self.enemies if e.alive]
        if not alive_enemies:
            self.state = STATE_WIN_WAVE
            return

        for e in alive_enemies:
            if e.y + ENEMY_H >= HEIGHT - 90:
                self.game_over()
                return

    def update_enemies(self, now):
        alive_enemies = [e for e in self.enemies if e.alive]
        if not alive_enemies:
            return
        min_x = min(e.x for e in alive_enemies)
        max_x = max(e.x + ENEMY_W for e in alive_enemies)

        step = self.enemy_speed
        will_hit_edge = (max_x + step >= WIDTH - 10 and self.enemy_dir > 0) or \
                        (min_x - step <= 10 and self.enemy_dir < 0)

        if will_hit_edge:
            for e in alive_enemies:
                e.y += ENEMY_STEP_DOWN
            self.enemy_dir *= -1
        else:
            for e in alive_enemies:
                e.x += step * self.enemy_dir

        if random.random() < self.enemy_shot_chance:
            shooter = random.choice(alive_enemies)
            self.enemy_bullets.append(pygame.Rect(
                int(shooter.x + ENEMY_W / 2 - BULLET_W / 2),
                int(shooter.y + ENEMY_H),
                BULLET_W, BULLET_H,
            ))

    def update_bullets(self):
        if self.player_bullet is not None:
            self.player_bullet.y -= BULLET_SPEED
            if self.player_bullet.bottom < 0:
                self.player_bullet = None

        for b in self.enemy_bullets:
            b.y += ENEMY_BULLET_SPEED
        self.enemy_bullets = [b for b in self.enemy_bullets if b.top < HEIGHT]

    def check_collisions(self, now):
        if self.player_bullet is not None:
            for e in self.enemies:
                if e.alive and self.player_bullet.colliderect(e.rect):
                    e.alive = False
                    self.player_bullet = None
                    self.score += 10 * self.wave
                    if self.sound_hit:
                        self.sound_hit.play()
                    self.particles.extend(spawn_confetti(e.rect.center, now, count=14, colors=[e.color, BULLET_COLOR]))
                    break

        player_rect = pygame.Rect(int(self.player_x), HEIGHT - 50, PLAYER_W, PLAYER_H)
        hit_bullet = None
        for b in self.enemy_bullets:
            if b.colliderect(player_rect):
                hit_bullet = b
                break
        if hit_bullet is not None:
            self.enemy_bullets.remove(hit_bullet)
            self.lives -= 1
            self.hit_flash_until = now + 300
            if self.sound_lose_life:
                self.sound_lose_life.play()
            self.particles.extend(spawn_confetti(player_rect.center, now, count=20, colors=[(255, 90, 90)]))
            if self.lives <= 0:
                self.game_over()

    def game_over(self):
        if self.sound_explosion:
            self.sound_explosion.play()
        self.state = STATE_GAMEOVER

    # ---------- draw ----------
    def draw_bg_shapes(self, now):
        for shape in self.bg_shapes:
            bob = math.sin(now / 1200 * shape["speed"] + shape["phase"]) * 4
            pygame.draw.circle(
                self.screen, (150, 155, 200),
                (int(shape["x"]), int(shape["y"] + bob)), shape["r"]
            )

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
        title = "SPACE INVADERS"
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
        self.draw_bg_shapes(now)
        self.draw_title(now)
        subtitle = self.font_subtitle.render(
            "Arrows/A-D to move, Space to shoot. Clear the grid!", True, SUBTITLE_COLOR
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 290)))
        self.start_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_player(self, now):
        flash = now < self.hit_flash_until
        color = (255, 255, 255) if flash and (now // 60) % 2 == 0 else PLAYER_COLOR
        cx = self.player_x + PLAYER_W / 2
        top_y = HEIGHT - 50
        points = [
            (cx, top_y),
            (self.player_x, top_y + PLAYER_H),
            (self.player_x + PLAYER_W, top_y + PLAYER_H),
        ]
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.rect(self.screen, color, (self.player_x + 14, top_y + PLAYER_H - 6, PLAYER_W - 28, 10))

    def draw_playing(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        self.draw_bg_shapes(now)

        for e in self.enemies:
            if not e.alive:
                continue
            r = e.rect
            pygame.draw.rect(self.screen, e.color, r, border_radius=6)
            eye_y = r.top + r.height // 2
            pygame.draw.circle(self.screen, BG_COLOR, (r.left + 10, eye_y), 3)
            pygame.draw.circle(self.screen, BG_COLOR, (r.right - 10, eye_y), 3)

        if self.player_bullet is not None:
            pygame.draw.rect(self.screen, BULLET_COLOR, self.player_bullet, border_radius=2)
        for b in self.enemy_bullets:
            pygame.draw.rect(self.screen, ENEMY_BULLET_COLOR, b, border_radius=2)

        self.draw_player(now)
        self.draw_particles(now)

        hud = self.font_hud.render(
            f"Score: {self.score}    Wave: {self.wave}    Lives: {self.lives}", True, TEXT_COLOR
        )
        self.screen.blit(hud, (20, 20))

        mouse_pos = pygame.mouse.get_pos()
        self.pause_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_paused(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))
        paused_surf = self.font_title.render("Paused", True, TEXT_COLOR)
        self.screen.blit(paused_surf, paused_surf.get_rect(center=(WIDTH // 2, 230)))
        self.resume_button.draw(self.screen, self.font_button, mouse_pos, now=now)
        self.quit_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_gameover(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        self.screen.fill(BG_COLOR)
        self.draw_bg_shapes(now)
        bounce = math.sin(now / 180) * 6
        text = self.font_title.render("Game Over", True, (255, 110, 140))
        self.screen.blit(text, text.get_rect(center=(WIDTH // 2, 230 + int(bounce))))
        score_surf = self.font_subtitle.render(
            f"Final score: {self.score}   (reached wave {self.wave})", True, TEXT_COLOR
        )
        self.screen.blit(score_surf, score_surf.get_rect(center=(WIDTH // 2, 300)))
        self.menu_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_wave_clear(self):
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        self.screen.fill(BG_COLOR)
        self.draw_bg_shapes(now)
        bounce = math.sin(now / 180) * 6
        text = self.font_title.render(f"Wave {self.wave} Cleared!", True, ACCENT_COLOR)
        self.screen.blit(text, text.get_rect(center=(WIDTH // 2, 230 + int(bounce))))
        score_surf = self.font_subtitle.render(f"Score: {self.score}", True, TEXT_COLOR)
        self.screen.blit(score_surf, score_surf.get_rect(center=(WIDTH // 2, 300)))
        self.next_wave_button.draw(self.screen, self.font_button, mouse_pos, now=now)

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
        elif self.state == STATE_WIN_WAVE:
            self.draw_wave_clear()
        pygame.display.flip()

    async def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            clock.tick(60)
            await asyncio.sleep(0)
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
                        self.fire_player_bullet()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == STATE_MENU:
                        self.handle_menu_click(event.pos)
                    elif self.state == STATE_PLAYING:
                        self.handle_click(event.pos)
                    elif self.state == STATE_PAUSED:
                        self.handle_pause_click(event.pos)
                    elif self.state == STATE_GAMEOVER:
                        self.handle_gameover_click(event.pos)
                    elif self.state == STATE_WIN_WAVE:
                        self.handle_wave_clear_click(event.pos)

            if self.state == STATE_PLAYING:
                self.update()
            self.draw()

            if self.quit_requested:
                running = False


async def run():
    await Game().run()


if __name__ == "__main__":
    asyncio.run(run())
