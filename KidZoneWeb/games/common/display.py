"""Keep a game's SCALED presentation correct when the device rotates.

pygame.SCALED fixes an internal logical-to-output scale at set_mode() time.
Rotating the device changes the canvas, but SDL keeps the old scale, so the
game renders zoomed and cropped. Only a fresh set_mode() rebuilds it, and it
has to happen inside the running game's own loop - the hub's loop is not
executing while a game is up.

Note deliberately NOT solved in JavaScript: a page-level resize handler
calling pygbag's window_resize() fixes the canvas *box* but not SDL's scale,
and when both ran the JS call landed after set_mode() and undid it, leaving
the game zoomed again. The Python side owns this.

Usage, once per frame after presenting:

    surface = display.maintain(WIDTH, HEIGHT)
    if surface is not None:
        screen = surface          # or self.screen = surface

Games keep their fixed logical size; only the presentation is rebuilt.
"""

import pygame

try:
    import platform  # pygbag's browser bridge - real only in-browser
except ImportError:  # pragma: no cover
    platform = None

_last_viewport = None
_pending = None


def viewport():
    """Real browser viewport, or None outside pygbag."""
    if platform is None or not hasattr(platform, "window"):
        return None
    try:
        w = int(platform.window.innerWidth)
        h = int(platform.window.innerHeight)
    except Exception:
        return None
    if w < 50 or h < 50:
        return None
    return w, h


def reset():
    """Forget the cached viewport, so the next call establishes a baseline
    instead of inheriting the previous game's."""
    global _last_viewport, _pending
    _last_viewport = viewport()
    _pending = None


def maintain(width, height, flags=None):
    """Re-create the display if the viewport changed. Returns the new surface,
    or None when nothing needed doing - the overwhelmingly common case, so
    this stays cheap enough to call every frame.

    A change must persist across two calls before acting: mobile browsers
    report a transient intermediate size mid-rotation, and rebuilding against
    that just means rebuilding again a frame later. Height-only changes under
    140px are ignored entirely - that is the URL bar hiding on scroll, not a
    rotation.
    """
    global _last_viewport, _pending

    vp = viewport()
    if vp is None:
        return None
    if _last_viewport is None:
        _last_viewport = vp
        return None
    if vp == _last_viewport:
        _pending = None
        return None

    dw = abs(vp[0] - _last_viewport[0])
    dh = abs(vp[1] - _last_viewport[1])
    if dw <= 8 and dh <= 140:
        return None

    if _pending != vp:
        _pending = vp
        return None

    _last_viewport = vp
    _pending = None
    if flags is None:
        flags = pygame.SCALED | pygame.RESIZABLE
    try:
        surface = pygame.display.set_mode((width, height), flags)
    except Exception:
        return None
    if platform is not None and hasattr(platform, "window"):
        try:
            platform.window.window_resize()
        except Exception:
            pass
    return surface
