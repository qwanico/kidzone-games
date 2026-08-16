"""Shared sound effects, and the global accessibility toggles.

Seven of the arcade games shipped with no audio at all - `grep mixer` returned
nothing for balloon_pop, bug_squasher, whack_a_mole, fish_catch, jumping_jack,
star_catcher and memory_match. Combined with their hazards being signalled by
colour alone (a grey rock among coloured stars, a grey can among fish, a bomb
among balloons), a child who tapped a hazard got no feedback in any modality
except a colour change and a decremented life counter. That is a real problem
for a pre-reader or a colour-blind child.

Mute and reduced motion live in the same browser localStorage blob the hub
uses, so a parent sets each once from Parent Settings and it survives a
reload - and applies everywhere, not just in whichever game was open.
"""

from pathlib import Path

import pygame

try:
    from .storage import KeyValueStore
except ImportError:  # standalone run
    from storage import KeyValueStore

SOUNDS_DIR = Path(__file__).parent / "sounds"
SETTINGS_KEY = "kidzone_settings"
DEFAULT_SETTINGS = {"muted": False, "reduced_motion": False}

_store = KeyValueStore(SETTINGS_KEY)
_settings = None
_cache = {}


def _load():
    global _settings
    if _settings is None:
        _settings = _store.load(DEFAULT_SETTINGS)
    return _settings


def is_muted():
    return bool(_load().get("muted", False))


def set_muted(value):
    """Persist the mute flag and stop anything currently playing."""
    s = _load()
    s["muted"] = bool(value)
    _store.save(s)
    if s["muted"]:
        try:
            pygame.mixer.stop()
        except Exception:
            pass


def toggle_muted():
    set_muted(not is_muted())
    return is_muted()


def is_reduced_motion():
    return bool(_load().get("reduced_motion", False))


def set_reduced_motion(value):
    s = _load()
    s["reduced_motion"] = bool(value)
    _store.save(s)


def toggle_reduced_motion():
    set_reduced_motion(not is_reduced_motion())
    return is_reduced_motion()


def _sound(name):
    snd = _cache.get(name)
    if snd is None:
        try:
            snd = pygame.mixer.Sound(str(SOUNDS_DIR / f"{name}.ogg"))
        except Exception:
            snd = False  # remember the failure; don't retry every frame
        _cache[name] = snd
    return snd or None


def play(name, volume=0.6):
    """Play a shared effect by stem name. Silent when muted; never raises -
    a missing sound file must not take a game down mid-round."""
    if is_muted():
        return
    snd = _sound(name)
    if snd is None:
        return
    try:
        snd.set_volume(volume)
        snd.play()
    except Exception:
        pass


def good(volume=0.5):
    """Positive feedback: scored, matched, caught the right thing."""
    play("correct", volume)


def bad(volume=0.6):
    """Negative feedback: hit a hazard, missed, lost a life."""
    play("wrong", volume)
