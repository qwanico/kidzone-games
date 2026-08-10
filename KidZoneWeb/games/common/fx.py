"""Shared visual effects: gradients and celebration particles.

`build_gradient` was byte-identical in 4 games; the confetti spawn/update/draw
trio existed in 8 with minor drift. Gradients are cached because they cost a
per-scanline loop and the inputs never change after startup.
"""

import math
import random

import pygame

_gradient_cache = {}


def build_gradient(width, height, top_color, bottom_color):
    """Vertical two-stop gradient. Cached - callers used to rebuild this on
    every game start, and it is a per-row Python loop."""
    key = (width, height, tuple(top_color), tuple(bottom_color))
    surf = _gradient_cache.get(key)
    if surf is not None:
        return surf
    surf = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height - 1)
        pygame.draw.line(
            surf,
            (
                int(top_color[0] + (bottom_color[0] - top_color[0]) * t),
                int(top_color[1] + (bottom_color[1] - top_color[1]) * t),
                int(top_color[2] + (bottom_color[2] - top_color[2]) * t),
            ),
            (0, y),
            (width, y),
        )
    _gradient_cache[key] = surf
    return surf


def spawn_confetti(cx, cy, colors, count=18, speed=(110, 300),
                   lift=(80, 180), life=(0.6, 1.1), size=(4, 8)):
    """Return confetti particles bursting from (cx, cy).

    Ranges are parameterised because the games were tuned individually and a
    single hard-coded feel would visibly change several of them. Time is in
    SECONDS here, matching the existing per-game implementations.
    """
    pieces = []
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        speed_px = random.uniform(*speed)
        pieces.append({
            "x": cx,
            "y": cy,
            "vx": math.cos(angle) * speed_px,
            "vy": math.sin(angle) * speed_px - random.uniform(*lift),
            "size": random.randint(*size),
            "color": random.choice(colors),
            "angle": random.uniform(0, 360),
            "spin": random.uniform(-360, 360),
            "age": 0.0,
            "life": random.uniform(*life),
        })
    return pieces


def update_confetti(pieces, dt_ms, gravity=480):
    """Advance and cull in place. dt-based, so refresh-rate independent."""
    dt = dt_ms / 1000.0
    for p in pieces:
        p["age"] += dt
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        p["vy"] += gravity * dt
        p["angle"] += p["spin"] * dt
    pieces[:] = [p for p in pieces if p["age"] < p["life"]]


def draw_confetti(surface, pieces):
    for p in pieces:
        t = p["age"] / p["life"]
        alpha = max(0, int(255 * (1 - t)))
        size = p["size"] * 2
        piece = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(piece, (*p["color"], alpha), (0, 0, size, size), border_radius=2)
        rotated = pygame.transform.rotate(piece, p["angle"])
        surface.blit(rotated, rotated.get_rect(center=(p["x"], p["y"])))


# --- Analytic particles -------------------------------------------------
# The other game family models confetti as a closed-form trajectory sampled
# from its spawn time rather than integrating each frame. Both were in the
# codebase; both are kept, because switching either family to the other's
# model visibly changes how its celebration looks.

class Particle:
    __slots__ = ("x0", "y0", "vx", "vy", "color", "size", "spawn", "life", "shape")

    def __init__(self, x, y, vx, vy, color, size, spawn, life, shape):
        self.x0 = x
        self.y0 = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.spawn = spawn
        self.life = life
        self.shape = shape

    def pos_at(self, now):
        t = (now - self.spawn) / 1000.0
        return (self.x0 + self.vx * t,
                self.y0 + self.vy * t + 0.5 * 650 * t * t)

    def alive(self, now):
        return now - self.spawn < self.life


def spawn_burst(center, now, colors, count=18, life=900):
    """Upward confetti fan from `center`, sampled analytically from `now`."""
    particles = []
    for _ in range(count):
        angle = random.uniform(-math.pi * 0.85, -math.pi * 0.15)
        speed = random.uniform(160, 380)
        particles.append(Particle(
            center[0], center[1],
            math.cos(angle) * speed, math.sin(angle) * speed,
            random.choice(colors), random.randint(5, 9), now, life,
            random.choice(["circle", "square"]),
        ))
    return particles


def draw_burst(surface, particles, now):
    for p in particles:
        x, y = p.pos_at(now)
        alpha = max(0, int(255 * (1 - (now - p.spawn) / p.life)))
        surf = pygame.Surface((p.size * 2, p.size * 2), pygame.SRCALPHA)
        if p.shape == "circle":
            pygame.draw.circle(surf, (*p.color, alpha), (p.size, p.size), p.size)
        else:
            pygame.draw.rect(surf, (*p.color, alpha), surf.get_rect())
        surface.blit(surf, (x - p.size, y - p.size))
