"""Shared UI widgets.

These were duplicated across the game files: `draw_home_icon` existed in 11
copies (two byte-identical clusters), `draw_speaker_icon` in 6, and `Button`
in 11. Each game keeps its own palette, so colours are passed in rather than
read from module globals - that is the only reason the copies diverged.
"""

import pygame

WHITE = (255, 255, 255)


def draw_home_icon(surface, rect, color, hovered=False, radius=12):
    """Rounded home button with a white house glyph.

    `hovered` lightens the fill; the games that lacked a hover variant simply
    never passed it.
    """
    bg = tuple(min(255, c + 15) for c in color) if hovered else color
    pygame.draw.rect(surface, bg, rect, border_radius=radius)
    pygame.draw.rect(surface, WHITE, rect, width=3, border_radius=radius)

    cx, cy = rect.center
    w, h = rect.width, rect.height

    roof_half = w * 0.30
    roof_top_y = cy - h * 0.26
    roof_base_y = cy - h * 0.02

    body_rect = pygame.Rect(0, 0, w * 0.42, h * 0.32)
    body_rect.midtop = (cx, roof_base_y)
    pygame.draw.rect(surface, WHITE, body_rect, border_radius=2)

    pygame.draw.polygon(surface, WHITE, [
        (cx - roof_half, roof_base_y),
        (cx, roof_top_y),
        (cx + roof_half, roof_base_y),
    ])


def draw_speaker_icon(surface, center, size, color, pulse=0.0):
    """Speaker glyph with two sound arcs - the 'say it again' affordance.

    `pulse` (0..1) swells the icon slightly while a clip is playing; math_game
    was the only game that had this, and it is harmless everywhere else.
    """
    size = size * (1.0 + pulse * 0.08)
    x, y = center
    body_w, body_h = size * 0.35, size * 0.5
    body_rect = pygame.Rect(0, 0, body_w, body_h)
    body_rect.center = (x - size * 0.15, y)
    pygame.draw.rect(surface, color, body_rect, border_radius=6)

    pygame.draw.polygon(surface, color, [
        (x - size * 0.15 - body_w / 2, y - size * 0.15),
        (x + size * 0.05, y - size * 0.35),
        (x + size * 0.05, y + size * 0.35),
        (x - size * 0.15 - body_w / 2, y + size * 0.15),
    ])

    for i in range(1, 3):
        radius = size * (0.18 + i * 0.14)
        rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        rect.center = (x, y)
        pygame.draw.arc(surface, color, rect, -0.5, 0.5, width=5)


class AnswerButton:
    """A labelled answer button that can flash correct/wrong.

    `palette` needs the keys: base, hover, correct, wrong.
    """

    def __init__(self, rect, label, palette, radius=24):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.palette = palette
        self.radius = radius
        self.state = "idle"

    # kept so existing call sites that read `.word` keep working
    @property
    def word(self):
        return self.label

    def color_for(self, mouse_pos):
        if self.state == "correct":
            return self.palette["correct"]
        if self.state == "wrong":
            return self.palette["wrong"]
        if self.rect.collidepoint(mouse_pos):
            return self.palette["hover"]
        return self.palette["base"]

    def draw(self, surface, font, mouse_pos):
        color = self.color_for(mouse_pos)
        pygame.draw.rect(surface, color, self.rect, border_radius=self.radius)
        pygame.draw.rect(surface, WHITE, self.rect, width=3, border_radius=self.radius)
        self.draw_face(surface, font, mouse_pos)
        self.draw_state_badge(surface)

    def draw_face(self, surface, font, mouse_pos):
        """What sits inside the button. Subclasses that answer with a picture
        rather than a word - a shape, a cluster of dots - override just this
        and keep the shared frame and its correct/wrong states."""
        text_surf = font.render(self.label, True, WHITE)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def draw_state_badge(self, surface):
        """A check or X on top of the correct/wrong fill, so the result does
        not depend on color alone - sfx.py's good()/bad() already exists for
        the same reason on the audio side (a grey rock read as just another
        star to a colorblind child), but nothing gave the visual side the
        matching fix. Badge sits in the corner rather than over the label so
        it reads as an addition, not a replacement, of what was already there.
        """
        if self.state not in ("correct", "wrong"):
            return
        size = min(self.rect.width, self.rect.height) * 0.3
        r = size * 0.6
        cx = self.rect.right - size * 0.7
        cy = self.rect.top + size * 0.7
        pygame.draw.circle(surface, WHITE, (cx, cy), r)
        color = self.palette["correct" if self.state == "correct" else "wrong"]
        pygame.draw.circle(surface, color, (cx, cy), r, width=max(2, int(r * 0.18)))
        w = max(2, int(r * 0.28))
        if self.state == "correct":
            pygame.draw.lines(surface, color, False, [
                (cx - r * 0.45, cy),
                (cx - r * 0.1, cy + r * 0.4),
                (cx + r * 0.45, cy - r * 0.35),
            ], width=w)
        else:
            pygame.draw.line(surface, color, (cx - r * 0.4, cy - r * 0.4), (cx + r * 0.4, cy + r * 0.4), width=w)
            pygame.draw.line(surface, color, (cx - r * 0.4, cy + r * 0.4), (cx + r * 0.4, cy - r * 0.4), width=w)
