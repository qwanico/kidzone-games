import asyncio
import math
import random
import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent / "pong_assets"
SOUNDS_DIR = BASE_DIR / "sounds"

WIDTH, HEIGHT = 900, 700

BG_COLOR = (24, 26, 38)
TITLE_COLOR = (120, 220, 255)
SUBTITLE_COLOR = (150, 155, 180)
TEXT_COLOR = (225, 228, 240)
ACCENT_COLOR = (255, 170, 60)
PLAYER_COLOR = (120, 220, 255)
AI_COLOR = (255, 110, 140)
BALL_COLOR = (240, 240, 250)
BUTTON_COLOR = (60, 66, 96)
BUTTON_HOVER = (86, 94, 132)
OVERLAY_COLOR = (14, 15, 24, 190)
ICON_BG = (40, 44, 58)
ICON_BG_HOVER = (54, 59, 78)
ICON_BORDER = (100, 106, 132)
ICON_COLOR = (255, 255, 255)
WIN_SCORE = 7

CONFETTI_COLORS = [
    (120, 220, 255), (255, 110, 140), (255, 210, 90),
    (140, 255, 170), (180, 140, 255),
]

PADDLE_W, PADDLE_H = 16, 110
PADDLE_SPEED = 8.0
BALL_SIZE = 16
BALL_SPEED_START = 6.0
BALL_SPEED_MAX = 15.0
BALL_SPEED_STEP = 0.35

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAMEOVER = "gameover"


class Particle:
    __slots__ = ("x0", "y0", "vx", "vy", "color", "size", "spawn", "life", "shape")

    def __init__(self, x, y, vx, vy, color, size, spawn, life, shape):
        self.x0, self.y0, self.vx, self.vy = x, y, vx, vy
        self.color, self.size, self.spawn, self.life, self.shape = color, size, spawn, life, shape

    def pos_at(self, now):
        t = (now - self.spawn) / 1000.0
        return self.x0 + self.vx * t, self.y0 + self.vy * t + 0.5 * 650 * t * t

    def alive(self, now):
        return now - self.spawn < self.life


def spawn_confetti(center, now, count=22):
    particles = []
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(120, 380)
        vx, vy = math.cos(angle) * speed, math.sin(angle) * speed
        color = random.choice(CONFETTI_COLORS)
        size = random.randint(4, 8)
        shape = random.choice(["circle", "square"])
        particles.append(Particle(center[0], center[1], vx, vy, color, size, now, 900, shape))
    return particles


def make_beep(freq=440, ms=90, volume=0.25):
    try:
        sample_rate = 44100
        n = int(sample_rate * ms / 1000)
        import array
        buf = array.array("h")
        amp = int(32767 * volume)
        for i in range(n):
            t = i / sample_rate
            env = 1.0 - (i / n)
            val = int(amp * env * math.sin(2 * math.pi * freq * t))
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


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self.sound_hit = make_beep(320, 60, 0.2)
            self.sound_score = make_beep(180, 220, 0.25)
            self.sound_wall = make_beep(500, 40, 0.15)
        except Exception:
            self.sound_hit = self.sound_score = self.sound_wall = None

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pong")

        self.font_title = pygame.font.SysFont("arial", 68, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 24)
        self.font_score = pygame.font.SysFont("arial", 64, bold=True)
        self.font_button = pygame.font.SysFont("arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("arial", 20)

        self.start_button = Button((WIDTH // 2 - 140, 440, 280, 70), "Start Game")
        self.resume_button = Button((WIDTH // 2 - 160, 340, 320, 70), "Resume")
        self.restart_button = Button((WIDTH // 2 - 160, 430, 320, 70), "Restart")
        self.pause_home_button = Button((WIDTH // 2 - 160, 520, 320, 70), "Home")
        self.menu_button = Button((WIDTH // 2 - 160, 500, 320, 70), "Main Menu")
        self.home_button = IconButton((20, 20, 60, 50), "home")
        self.pause_button = IconButton((90, 20, 60, 50), "pause")

        self.bg_shapes = [
            {
                "x": random.uniform(40, WIDTH - 40),
                "y": random.uniform(40, HEIGHT - 40),
                "r": random.randint(10, 24),
                "speed": random.uniform(0.4, 1.0),
                "phase": random.uniform(0, math.tau),
                "color": random.choice(CONFETTI_COLORS),
            }
            for _ in range(12)
        ]

        self.particles = []
        self.state = STATE_MENU
        self.quit_requested = False
        self._pause_saved = None
        self.pause_started = None
        self.pause_accum = 0
        self.reset_match()

    # ---------- match lifecycle ----------
    def reset_match(self):
        self.player_score = 0
        self.ai_score = 0
        self.player_y = HEIGHT / 2 - PADDLE_H / 2
        self.ai_y = HEIGHT / 2 - PADDLE_H / 2
        self.ai_reaction_offset = 0.0
        self.ai_react_timer = 0
        self.winner = None
        self.reset_ball(direction=random.choice([-1, 1]))

    def reset_ball(self, direction=1):
        self.ball_x = WIDTH / 2 - BALL_SIZE / 2
        self.ball_y = HEIGHT / 2 - BALL_SIZE / 2
        angle = random.uniform(-0.35, 0.35)
        speed = BALL_SPEED_START
        self.ball_vx = math.cos(angle) * speed * direction
        self.ball_vy = math.sin(angle) * speed
        self.serve_timer = self.game_now() + 700

    def start_game(self):
        self.reset_match()
        self.state = STATE_PLAYING

    def restart_game(self):
        self.reset_match()
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

    # ---------- update ----------
    def update(self, dt_ms):
        now = self.game_now()
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.player_y -= PADDLE_SPEED
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.player_y += PADDLE_SPEED
        self.player_y = max(0, min(HEIGHT - PADDLE_H, self.player_y))

        self.update_ai(now)

        if now < self.serve_timer:
            if self.particles:
                self.particles = [p for p in self.particles if p.alive(now)]
            return

        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        if self.ball_y <= 0:
            self.ball_y = 0
            self.ball_vy *= -1
            if self.sound_wall:
                self.sound_wall.play()
        elif self.ball_y + BALL_SIZE >= HEIGHT:
            self.ball_y = HEIGHT - BALL_SIZE
            self.ball_vy *= -1
            if self.sound_wall:
                self.sound_wall.play()

        player_rect = pygame.Rect(30, int(self.player_y), PADDLE_W, PADDLE_H)
        ai_rect = pygame.Rect(WIDTH - 30 - PADDLE_W, int(self.ai_y), PADDLE_W, PADDLE_H)
        ball_rect = pygame.Rect(int(self.ball_x), int(self.ball_y), BALL_SIZE, BALL_SIZE)

        if self.ball_vx < 0 and ball_rect.colliderect(player_rect):
            self.bounce_off_paddle(player_rect, direction=1)
        elif self.ball_vx > 0 and ball_rect.colliderect(ai_rect):
            self.bounce_off_paddle(ai_rect, direction=-1)

        if self.ball_x + BALL_SIZE < 0:
            self.ai_score += 1
            self.on_score(scored_by_player=False)
        elif self.ball_x > WIDTH:
            self.player_score += 1
            self.on_score(scored_by_player=True)

        if self.particles:
            self.particles = [p for p in self.particles if p.alive(now)]

    def bounce_off_paddle(self, paddle_rect, direction):
        speed = math.hypot(self.ball_vx, self.ball_vy)
        speed = min(speed + BALL_SPEED_STEP, BALL_SPEED_MAX)
        offset = (self.ball_y + BALL_SIZE / 2 - paddle_rect.centery) / (PADDLE_H / 2)
        offset = max(-1, min(1, offset))
        angle = offset * math.radians(55)
        self.ball_vx = math.cos(angle) * speed * direction
        self.ball_vy = math.sin(angle) * speed
        if direction > 0:
            self.ball_x = paddle_rect.right
        else:
            self.ball_x = paddle_rect.left - BALL_SIZE
        if self.sound_hit:
            self.sound_hit.play()
        now = self.game_now()
        self.particles.extend(spawn_confetti(
            (self.ball_x + BALL_SIZE / 2, self.ball_y + BALL_SIZE / 2), now, count=8
        ))

    def on_score(self, scored_by_player):
        now = self.game_now()
        color_center = (WIDTH * 0.25, HEIGHT / 2) if scored_by_player else (WIDTH * 0.75, HEIGHT / 2)
        self.particles.extend(spawn_confetti(color_center, now, count=26))
        if self.sound_score:
            self.sound_score.play()
        if self.player_score >= WIN_SCORE or self.ai_score >= WIN_SCORE:
            self.winner = "You" if self.player_score >= WIN_SCORE else "The AI"
            self.state = STATE_GAMEOVER
        else:
            self.reset_ball(direction=-1 if scored_by_player else 1)

    def update_ai(self, now):
        # AI tracks the ball but with reaction delay + imperfection so it's beatable.
        if now >= self.ai_react_timer:
            self.ai_react_timer = now + random.randint(80, 200)
            target = self.ball_y + BALL_SIZE / 2 - PADDLE_H / 2
            self.ai_reaction_offset = target + random.uniform(-38, 38)

        center = self.ai_y + PADDLE_H / 2
        target_center = self.ai_reaction_offset + PADDLE_H / 2
        diff = target_center - center
        max_speed = PADDLE_SPEED * 0.82
        if abs(diff) > 4:
            step = max(-max_speed, min(max_speed, diff * 0.18))
            self.ai_y += step
        self.ai_y = max(0, min(HEIGHT - PADDLE_H, self.ai_y))

    # ---------- draw ----------
    def draw_bg_shapes(self, now):
        for shape in self.bg_shapes:
            bob = math.sin(now / 900 * shape["speed"] + shape["phase"]) * 14
            r = shape["r"]
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*shape["color"], 40), (r, r), r)
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

    def draw_title(self, now, y=170):
        title = "PONG"
        letter_surfs = [self.font_title.render(ch, True, TITLE_COLOR) for ch in title]
        total_w = sum(s.get_width() for s in letter_surfs)
        x = WIDTH // 2 - total_w // 2
        for i, surf in enumerate(letter_surfs):
            bob = math.sin(now / 260 + i * 0.6) * 10
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
            "First to 7 wins! W/S or arrows to move.", True, SUBTITLE_COLOR
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 280)))
        self.start_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_court(self, now):
        self.screen.fill(BG_COLOR)
        self.draw_bg_shapes(now)
        for y in range(0, HEIGHT, 30):
            pygame.draw.rect(self.screen, (60, 64, 90), (WIDTH // 2 - 3, y, 6, 16))

        pygame.draw.rect(
            self.screen, PLAYER_COLOR, (30, int(self.player_y), PADDLE_W, PADDLE_H), border_radius=6
        )
        pygame.draw.rect(
            self.screen, AI_COLOR,
            (WIDTH - 30 - PADDLE_W, int(self.ai_y), PADDLE_W, PADDLE_H), border_radius=6
        )

        if now >= self.serve_timer:
            pygame.draw.rect(
                self.screen, BALL_COLOR,
                (int(self.ball_x), int(self.ball_y), BALL_SIZE, BALL_SIZE), border_radius=4
            )
        else:
            pulse = (math.sin(now / 120) + 1) / 2
            r = int(BALL_SIZE / 2 + pulse * 4)
            pygame.draw.circle(
                self.screen, BALL_COLOR,
                (int(self.ball_x + BALL_SIZE / 2), int(self.ball_y + BALL_SIZE / 2)), r
            )

        self.draw_particles(now)

        player_text = self.font_score.render(str(self.player_score), True, PLAYER_COLOR)
        ai_text = self.font_score.render(str(self.ai_score), True, AI_COLOR)
        self.screen.blit(player_text, player_text.get_rect(midtop=(WIDTH // 2 - 90, 30)))
        self.screen.blit(ai_text, ai_text.get_rect(midtop=(WIDTH // 2 + 90, 30)))

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
        self.draw_bg_shapes(now)
        self.draw_particles(now)
        color = ACCENT_COLOR if self.winner == "You" else AI_COLOR
        bounce = math.sin(now / 180) * 6
        win_surf = self.font_title.render(f"{self.winner} win!", True, color)
        self.screen.blit(win_surf, win_surf.get_rect(center=(WIDTH // 2, 230 + int(bounce))))
        score_surf = self.font_subtitle.render(
            f"Final score: {self.player_score} - {self.ai_score}", True, TEXT_COLOR
        )
        self.screen.blit(score_surf, score_surf.get_rect(center=(WIDTH // 2, 300)))
        self.menu_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw(self):
        now = self.game_now()
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_PLAYING:
            self.draw_court(now)
        elif self.state == STATE_PAUSED:
            self.draw_court(now)
            self.draw_paused()
        elif self.state == STATE_GAMEOVER:
            self.draw_gameover()
        pygame.display.flip()

    async def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt_ms = clock.tick(60)
            await asyncio.sleep(0)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.state == STATE_PLAYING:
                        self.enter_pause()
                    elif self.state == STATE_PAUSED:
                        self.resume_game()
                    else:
                        running = False
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
                self.update(dt_ms)
            self.draw()

            if self.quit_requested:
                running = False


async def run():
    await Game().run()


if __name__ == "__main__":
    asyncio.run(run())
