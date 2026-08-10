"""Persistent per-game storage backed by real browser localStorage.

Why this exists: a game's asset folder lives on a virtual filesystem that
pygbag re-extracts from the shipped archive on *every* page load, so anything
written there is gone on reload. FruitFinder used to save high scores to a
`progress.json` in its asset folder, which meant no child's score ever
persisted - and the copy of that file bundled at build time shipped the
developer's own scores to every player.

This mirrors the approach `main.py` already uses for the hub, generalised to
an arbitrary key so each game can own its own slot.
"""

import json

try:
    import platform  # pygbag's browser bridge - real only inside the browser
except ImportError:  # pragma: no cover - desktop CPython always has stdlib platform
    platform = None


class KeyValueStore:
    """One JSON-encoded blob under one localStorage key.

    Reachability is probed once at construction. Outside a real pygbag runtime
    (plain desktop CPython, where `platform` is the stdlib module and has no
    `.window`) this degrades to an in-memory store for the current process
    instead of raising - the game still runs, it just won't persist.
    """

    def __init__(self, key):
        self.key = key
        self._window = None
        self._memory = None
        try:
            window = platform.window
            window.localStorage  # touch it now; raises if not really present
            self._window = window
        except Exception:
            self._window = None

    @property
    def reachable(self):
        return self._window is not None

    def _read_raw(self):
        if self._window is not None:
            try:
                return self._window.localStorage.getItem(self.key)
            except Exception:
                pass
        return self._memory

    def _write_raw(self, raw):
        if self._window is not None:
            try:
                self._window.localStorage.setItem(self.key, raw)
                return
            except Exception:
                pass
        self._memory = raw

    def load(self, default):
        """Return `default` updated with whatever was saved. Never raises."""
        data = dict(default)
        raw = self._read_raw()
        if raw:
            try:
                saved = json.loads(raw)
                if isinstance(saved, dict):
                    data.update(saved)
            except (ValueError, TypeError):
                pass
        return data

    def save(self, data):
        """Persist `data`. Never raises - losing a high score must not crash a game."""
        try:
            self._write_raw(json.dumps(data))
        except (TypeError, ValueError):
            pass
