"""Memoised text rasterisation.

Rasterising a glyph run is one of the most expensive things a pygame frame
can do, and KidZone did it from scratch every frame for text that never
changes: "Kid Zone", "Paused", every button label, every HUD caption. Across
the project that was 4-25 `.render()` calls per frame per game, all
recomputing an identical surface 60 times a second.

The fix is deliberately shaped so that *call sites do not change*. Rather
than a `render_text(font, ...)` helper that 185 call sites would have to
adopt (and that new code would forget), the cache lives on the font object
itself. Build fonts through `text.Font()` / `text.SysFont()` instead of
`pygame.font.Font()` / `pygame.font.SysFont()`, and every existing
`font.render(...)` in that file is cached from then on.

    from .common import text
    self.font_title = text.SysFont("arial", 48, bold=True)
    ...
    surf = self.font_title.render("Paused", True, (255, 255, 255))   # unchanged

IMPORTANT - the returned surface is shared. Never mutate what `render()`
hands back: `set_alpha()`, `fill()` and blitting *onto* it would corrupt the
copy every later frame receives. Call `.copy()` first, or use
`render_copy()`, which does it for you and is still far cheaper than
re-rasterising. Fading text is the usual case:

    surf = font.render_copy(msg, True, colour)
    surf.set_alpha(alpha)

Everything that affects rasterisation is part of the cache key, so changing
a font's style or size mid-run stays correct rather than silently serving a
stale surface.
"""

from collections import OrderedDict
import weakref

import pygame

# Per font, not global. Games hold a handful of fonts and draw a small set of
# distinct strings through each; the headroom is for counters ("Score: 143")
# that legitimately produce a new string every time they change.
MAX_ENTRIES = 128

_fonts = weakref.WeakSet()


class CachedFont(pygame.font.Font):
    """A Font that memoises render(). Drop-in for pygame.font.Font."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = OrderedDict()
        _fonts.add(self)

    def _key(self, text, antialias, color):
        # Style and size belong in the key: a font mutated after its first
        # render must not keep serving surfaces drawn in the old style.
        return (
            text,
            bool(antialias),
            color if type(color) is tuple else tuple(color),
            self.bold,
            self.italic,
            self.underline,
            self.strikethrough,
            self.point_size,
            self.align,
        )

    def render(self, text, antialias=True, color=(0, 0, 0), background=None):
        """Cached rasterisation. The result is SHARED - do not mutate it."""
        if background is not None:
            # Rare, and it doubles the key space for no measured gain.
            return super().render(text, antialias, color, background)
        try:
            key = self._key(text, antialias, color)
        except TypeError:
            # An unhashable colour (e.g. a list) - correctness over caching.
            return super().render(text, antialias, color)

        cache = self._cache
        surf = cache.get(key)
        if surf is not None:
            cache.move_to_end(key)
            return surf

        surf = super().render(text, antialias, color)
        cache[key] = surf
        if len(cache) > MAX_ENTRIES:
            cache.popitem(last=False)
        return surf

    def render_copy(self, text, antialias=True, color=(0, 0, 0), background=None):
        """Cached rasterisation, returned as a private copy that is safe to
        mutate. Still skips the glyph work; only the blit is repeated."""
        return self.render(text, antialias, color, background).copy()

    def clear_cache(self):
        self._cache.clear()


def Font(filename=None, size=20, **kwargs):
    """pygame.font.Font, with render() memoised."""
    return CachedFont(filename, size, **kwargs)


def SysFont(name, size, bold=False, italic=False):
    """pygame.font.SysFont, with render() memoised.

    Routed through pygame's own `constructor` hook so system-font lookup,
    fallbacks and the bold/italic synthesis behave exactly as before.
    """

    def constructor(fontpath, fontsize, fontbold, fontitalic):
        font = CachedFont(fontpath, fontsize)
        font.set_bold(fontbold)
        font.set_italic(fontitalic)
        return font

    return pygame.font.SysFont(name, size, bold, italic, constructor=constructor)


def clear_all():
    """Drop every cached surface. Worth calling after a rotation rebuild,
    where the old sizes will never be asked for again."""
    for font in list(_fonts):
        font.clear_cache()
