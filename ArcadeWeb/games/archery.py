import asyncio
import math
import random
import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent / "archery_assets"
SOUNDS_DIR = BASE_DIR / "sounds"

WIDTH, HEIGHT = 1000, 780

BG_COLOR = (24, 26, 38)
TEXT_COLOR = (225, 228, 240)
TITLE_COLOR = (120, 220, 255)
SUBTITLE_COLOR = (150, 155, 180)
ACCENT = (120, 220, 255)
ACCENT_DARK = (90, 185, 220)
CORRECT_COLOR = (100, 220, 150)
WRONG_COLOR = (255, 100, 110)

CONFETTI_COLORS = [
    (255, 99, 132), (255, 205, 86), (75, 192, 192),
    (54, 162, 235), (153, 102, 255), (120, 220, 255),
]

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_RESULTS = "results"

SUB_AIMING = "aiming"
SUB_CHARGING = "charging"
SUB_FLYING = "flying"
SUB_IMPACT = "impact"

ARROWS_PER_ROUND = 6
MAX_CHARGE_MS = 1200
MIN_POWER = 0.3
FLIGHT_MS = 550
IMPACT_MS = 900
ARC_HEIGHT = 90

TARGET_CENTER = (WIDTH // 2, 230)
TARGET_R = 95
BOW_POS = (WIDTH // 2, HEIGHT - 70)

RING_SPECS = [
    (0.12, 10, (255, 210, 60)),
    (0.32, 8, (220, 70, 70)),
    (0.55, 6, (70, 110, 220)),
    (0.78, 4, (35, 35, 40)),
    (1.0, 2, (230, 230, 235)),
]


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


def spawn_confetti(center, now, count=30):
    particles = []
    for _ in range(count):
        angle = random.uniform(-math.pi * 0.95, -math.pi * 0.05)
        speed = random.uniform(140, 380)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        color = random.choice(CONFETTI_COLORS)
        size = random.randint(4, 8)
        shape = random.choice(["circle", "square"])
        particles.append(Particle(center[0], center[1], vx, vy, color, size, now, 1000, shape))
    return particles


def get_score(dist):
    frac = dist / TARGET_R
    for threshold, points, _ in RING_SPECS:
        if frac <= threshold:
            return points
    return 0


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
            self.wrong_sound = pygame.mixer.Sound(str(SOUNDS_DIR / "wrong.ogg"))
        except pygame.error:
            self.wrong_sound = None

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Archery Target")

        self.font_title = pygame.font.SysFont("arial", 58, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 24)
        self.font_button = pygame.font.SysFont("arial", 24, bold=True)
        self.font_icon = pygame.font.SysFont("arial", 20, bold=True)
        self.font_stat = pygame.font.SysFont("arial", 26, bold=True)
        self.font_big = pygame.font.SysFont("arial", 60, bold=True)
        self.font_score_pop = pygame.font.SysFont("arial", 44, bold=True)

        self.start_button = Button((WIDTH // 2 - 140, 460, 280, 90), "Start")
        self.pause_button = Button((WIDTH - 90, 20, 60, 46), "II")
        self.resume_button = Button((WIDTH // 2 - 160, 340, 320, 80), "Resume")
        self.quit_button = Button((WIDTH // 2 - 160, 440, 320, 80), "Quit")
        self.replay_button = Button((WIDTH // 2 - 160, 560, 320, 80), "Play Again")

        self.bg_shapes = [
            {
                "x": random.uniform(30, WIDTH - 30),
                "y": random.uniform(30, HEIGHT - 30),
                "r": random.randint(10, 24),
                "speed": random.uniform(0.4, 1.0),
                "phase": random.uniform(0, math.tau),
                "color": random.choice(CONFETTI_COLORS),
            }
            for _ in range(12)
        ]

        self.state = STATE_MENU
        self.quit_requested = False
        self.particles = []
        self._pause_saved = None

        self.new_round()

    def new_round(self):
        self.arrow_index = 0
        self.total_score = 0
        self.shot_history = []
        self.particles = []
        self.new_shot()

    def new_shot(self):
        self.sub_state = SUB_AIMING
        self.wind = random.uniform(-6, 6)
        self.charge = 0.0
        self.charge_start = None
        self.aim_pos = pygame.mouse.get_pos()
        self.flight_start = None
        self.flight_from = None
        self.flight_to = None
        self.flight_power = 0.0
        self.short_shot = False
        self.impact_start = None
        self.last_score = None
        self.last_hit_pos = None

    def start_game(self):
        self.new_round()
        self.state = STATE_PLAYING

    def enter_pause(self):
        now = pygame.time.get_ticks()
        saved = {}
        if self.sub_state == SUB_CHARGING and self.charge_start is not None:
            saved["charge_elapsed"] = now - self.charge_start
        elif self.sub_state == SUB_FLYING and self.flight_start is not None:
            saved["flight_elapsed"] = now - self.flight_start
        elif self.sub_state == SUB_IMPACT and self.impact_start is not None:
            saved["impact_elapsed"] = now - self.impact_start
        self._pause_saved = saved
        self.state = STATE_PAUSED

    def resume_game(self):
        now = pygame.time.get_ticks()
        saved = self._pause_saved or {}
        if "charge_elapsed" in saved:
            self.charge_start = now - saved["charge_elapsed"]
        if "flight_elapsed" in saved:
            self.flight_start = now - saved["flight_elapsed"]
        if "impact_elapsed" in saved:
            self.impact_start = now - saved["impact_elapsed"]
        self.state = STATE_PLAYING

    def handle_menu_click(self, pos):
        if self.start_button.is_hovered(pos):
            self.start_game()

    def handle_pause_click(self, pos):
        if self.resume_button.is_hovered(pos):
            self.resume_game()
        elif self.quit_button.is_hovered(pos):
            self.quit_requested = True

    def handle_results_click(self, pos):
        if self.replay_button.is_hovered(pos):
            self.start_game()

    def mouse_down(self, pos):
        if self.pause_button.is_hovered(pos):
            self.enter_pause()
            return
        if self.sub_state == SUB_AIMING:
            self.sub_state = SUB_CHARGING
            self.charge_start = pygame.time.get_ticks()

    def mouse_up(self, pos):
        if self.sub_state == SUB_CHARGING:
            self.fire(pos)

    def fire(self, release_pos):
        now = pygame.time.get_ticks()
        elapsed = now - (self.charge_start or now)
        power = min(elapsed / MAX_CHARGE_MS, 1.0)
        self.flight_power = power
        self.aim_pos = release_pos
        self.flight_from = BOW_POS
        self.short_shot = power < MIN_POWER

        if self.short_shot:
            # falls short — arrow lands partway, never reaches target
            mx = (BOW_POS[0] + release_pos[0]) / 2
            my = BOW_POS[1] - (BOW_POS[1] - release_pos[1]) * (power / MIN_POWER) * 0.4
            self.flight_to = (mx, my)
        else:
            power_factor = (power - MIN_POWER) / (1 - MIN_POWER)
            vertical_drop = (1 - power_factor) * 55
            landing_x = release_pos[0] + self.wind * 8
            landing_y = release_pos[1] + vertical_drop
            self.flight_to = (landing_x, landing_y)

        self.flight_start = now
        self.sub_state = SUB_FLYING

    def resolve_impact(self):
        now = pygame.time.get_ticks()
        self.last_hit_pos = self.flight_to
        if self.short_shot:
            self.last_score = 0
        else:
            dist = math.hypot(
                self.flight_to[0] - TARGET_CENTER[0], self.flight_to[1] - TARGET_CENTER[1]
            )
            self.last_score = get_score(dist)

        self.total_score += self.last_score
        self.shot_history.append(self.last_score)

        if self.last_score >= 8:
            self.particles.extend(spawn_confetti(self.last_hit_pos, now))
        elif self.last_score == 0:
            if self.wrong_sound:
                self.wrong_sound.play()

        self.impact_start = now
        self.sub_state = SUB_IMPACT

    def update(self):
        now = pygame.time.get_ticks()
        if self.particles:
            self.particles = [p for p in self.particles if p.alive(now)]

        if self.state != STATE_PLAYING:
            return

        if self.sub_state == SUB_CHARGING:
            elapsed = now - self.charge_start
            self.charge = min(elapsed / MAX_CHARGE_MS, 1.0)
        elif self.sub_state == SUB_FLYING:
            if now - self.flight_start >= FLIGHT_MS:
                self.resolve_impact()
        elif self.sub_state == SUB_IMPACT:
            if now - self.impact_start >= IMPACT_MS:
                self.arrow_index += 1
                if self.arrow_index >= ARROWS_PER_ROUND:
                    self.state = STATE_RESULTS
                else:
                    self.new_shot()

    def current_arrow_pos(self, now):
        if self.sub_state != SUB_FLYING:
            return self.flight_to or BOW_POS
        t = min((now - self.flight_start) / FLIGHT_MS, 1.0)
        x = self.flight_from[0] + (self.flight_to[0] - self.flight_from[0]) * t
        y = self.flight_from[1] + (self.flight_to[1] - self.flight_from[1]) * t
        lift = math.sin(math.pi * t) * ARC_HEIGHT
        return x, y - lift

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

    def draw_title(self, now, y=110, text="Archery Target"):
        letter_surfs = [self.font_title.render(ch, True, TITLE_COLOR) for ch in text]
        total_w = sum(s.get_width() for s in letter_surfs)
        x = WIDTH // 2 - total_w // 2
        for i, surf in enumerate(letter_surfs):
            bob = math.sin(now / 260 + i * 0.6) * 6
            rect = surf.get_rect(midtop=(x + surf.get_width() // 2, y + int(bob)))
            self.screen.blit(surf, rect)
            x += surf.get_width()

    def draw_menu(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)
        self.draw_title(now, 200)
        subtitle_surf = self.font_subtitle.render(
            "Hold to charge power, release to fire. Watch the wind!", True, SUBTITLE_COLOR
        )
        self.screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, 300)))
        rules_surf = self.font_subtitle.render(
            f"{ARROWS_PER_ROUND} arrows per round. Aim for the gold!", True, SUBTITLE_COLOR
        )
        self.screen.blit(rules_surf, rules_surf.get_rect(center=(WIDTH // 2, 334)))
        self.start_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw_target(self):
        for threshold, points, color in reversed(RING_SPECS):
            r = int(TARGET_R * threshold)
            pygame.draw.circle(self.screen, color, TARGET_CENTER, r)
        pygame.draw.circle(self.screen, (10, 10, 15), TARGET_CENTER, TARGET_R, width=3)
        for threshold, _, _ in RING_SPECS[:-1]:
            r = int(TARGET_R * threshold)
            pygame.draw.circle(self.screen, (10, 10, 15), TARGET_CENTER, r, width=1)
        # stand
        pygame.draw.rect(
            self.screen, (90, 65, 40),
            (TARGET_CENTER[0] - 6, TARGET_CENTER[1] + TARGET_R, 12, HEIGHT - (TARGET_CENTER[1] + TARGET_R) - 40),
        )

    def draw_bow(self):
        pygame.draw.arc(
            self.screen, (150, 110, 70),
            pygame.Rect(BOW_POS[0] - 10, BOW_POS[1] - 45, 30, 90),
            math.pi / 2, 3 * math.pi / 2, width=5,
        )

    def draw_playing(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)

        progress_surf = self.font_stat.render(
            f"Arrow {min(self.arrow_index + 1, ARROWS_PER_ROUND)}/{ARROWS_PER_ROUND}", True, SUBTITLE_COLOR
        )
        self.screen.blit(progress_surf, (30, 24))

        score_surf = self.font_stat.render(f"Score: {self.total_score}", True, ACCENT)
        self.screen.blit(score_surf, score_surf.get_rect(topright=(WIDTH - 170, 24)))

        wind_dir = "<--" if self.wind < 0 else "-->"
        wind_surf = self.font_stat.render(f"Wind: {wind_dir} {abs(self.wind):0.1f}", True, TEXT_COLOR)
        self.screen.blit(wind_surf, wind_surf.get_rect(center=(WIDTH // 2, 30)))

        self.draw_target()
        self.draw_bow()

        if self.sub_state in (SUB_AIMING, SUB_CHARGING):
            aim = mouse_pos
            pygame.draw.line(self.screen, (255, 255, 255, 80), (aim[0] - 14, aim[1]), (aim[0] + 14, aim[1]), 2)
            pygame.draw.line(self.screen, (255, 255, 255, 80), (aim[0], aim[1] - 14), (aim[0], aim[1] + 14), 2)
            pygame.draw.circle(self.screen, ACCENT, aim, 16, width=2)

        if self.sub_state == SUB_CHARGING:
            bar_w, bar_h = 220, 22
            bar_rect = pygame.Rect(WIDTH // 2 - bar_w // 2, HEIGHT - 40, bar_w, bar_h)
            pygame.draw.rect(self.screen, (50, 53, 72), bar_rect, border_radius=10)
            fill_rect = bar_rect.copy()
            fill_rect.width = int(bar_w * self.charge)
            fill_color = (
                int(255 * (1 - self.charge) + 100 * self.charge),
                int(100 + 120 * self.charge),
                90,
            )
            pygame.draw.rect(self.screen, fill_color, fill_rect, border_radius=10)
            pygame.draw.rect(self.screen, (250, 250, 255), bar_rect, width=2, border_radius=10)

        if self.sub_state in (SUB_FLYING, SUB_IMPACT):
            ax, ay = self.current_arrow_pos(now)
            dx = self.flight_to[0] - self.flight_from[0]
            dy = self.flight_to[1] - self.flight_from[1]
            angle = math.atan2(dy, dx)
            length = 22
            tail = (ax - math.cos(angle) * length, ay - math.sin(angle) * length)
            pygame.draw.line(self.screen, (220, 210, 190), tail, (ax, ay), 4)
            pygame.draw.circle(self.screen, (200, 60, 60), (ax, ay), 4)

        self.draw_particles(now)

        if self.sub_state == SUB_IMPACT and self.last_score is not None:
            label = "MISS" if self.short_shot else (f"+{self.last_score}" if self.last_score > 0 else "MISS")
            color = CORRECT_COLOR if self.last_score >= 6 else (WRONG_COLOR if self.last_score == 0 else TEXT_COLOR)
            bounce = math.sin(now / 90) * 4
            pop_surf = self.font_score_pop.render(label, True, color)
            pos = self.last_hit_pos or TARGET_CENTER
            self.screen.blit(pop_surf, pop_surf.get_rect(center=(pos[0], pos[1] - 40 + int(bounce))))

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

    def draw_results(self):
        now = pygame.time.get_ticks()
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        self.draw_bg_shapes(now)
        self.draw_title(now, 140, "Round Over")

        bounce = math.sin(now / 200) * 6
        max_possible = ARROWS_PER_ROUND * 10
        score_surf = self.font_big.render(f"{self.total_score} / {max_possible}", True, ACCENT)
        self.screen.blit(score_surf, score_surf.get_rect(center=(WIDTH // 2, 290 + int(bounce))))

        history_text = "  ".join(str(s) for s in self.shot_history)
        hist_surf = self.font_subtitle.render(f"Shots: {history_text}", True, SUBTITLE_COLOR)
        self.screen.blit(hist_surf, hist_surf.get_rect(center=(WIDTH // 2, 370)))

        pct = self.total_score / max_possible if max_possible else 0
        if pct >= 0.8:
            msg = "Master Archer!"
        elif pct >= 0.5:
            msg = "Solid shooting!"
        else:
            msg = "Keep practicing!"
        msg_surf = self.font_stat.render(msg, True, TEXT_COLOR)
        self.screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH // 2, 420)))

        self.replay_button.draw(self.screen, self.font_button, mouse_pos, now=now)

    def draw(self):
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_PLAYING:
            self.draw_playing()
        elif self.state == STATE_PAUSED:
            self.draw_playing()
            self.draw_paused()
        elif self.state == STATE_RESULTS:
            self.draw_results()
        pygame.display.flip()

    async def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
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
                        self.mouse_down(event.pos)
                    elif self.state == STATE_PAUSED:
                        self.handle_pause_click(event.pos)
                    elif self.state == STATE_RESULTS:
                        self.handle_results_click(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.state == STATE_PLAYING:
                        self.mouse_up(event.pos)

            self.update()
            self.draw()

            if self.quit_requested:
                running = False

            clock.tick(60)
            await asyncio.sleep(0)


async def run():
    await Game().run()


if __name__ == "__main__":
    asyncio.run(run())
