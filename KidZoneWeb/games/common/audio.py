"""Shared voice playback.

Nine games each carried their own copy of this: reserve channel 0, keep a
{path: Sound} cache, stop before playing so a new clue cuts off the last one.
The copies were byte-identical apart from the parameter name.

Two hard-won rules are encoded here:
  * never use `pygame.mixer.music` for short repeated clips - under pygbag's
    WebAudio backend it silently fails to play after the first few times;
  * always stop the voice channel when the game exits, or a spoken clue keeps
    playing over the hub menu.
"""

import pygame

_initialised = False


class VoicePlayer:
    """A reserved channel plus a lazily-filled Sound cache."""

    def __init__(self, voice_dir, channel_index=0):
        global _initialised
        self.voice_dir = voice_dir
        self.cache = {}
        if not _initialised:
            # Reserve the channel so music and effects, which get auto-assigned
            # channels, can never land on it and cut the voice off.
            pygame.mixer.set_reserved(channel_index + 1)
            _initialised = True
        self.channel = pygame.mixer.Channel(channel_index)

    def sound_for(self, name):
        path = str(self.voice_dir / f"{name}.ogg")
        sound = self.cache.get(path)
        if sound is None:
            sound = pygame.mixer.Sound(path)
            self.cache[path] = sound
        return sound

    def say(self, name):
        """Play a clip, cutting off whatever was speaking. Never raises - a
        missing voice file must not take the game down mid-round."""
        try:
            sound = self.sound_for(name)
        except Exception:
            return None
        self.channel.stop()
        self.channel.play(sound)
        return sound

    def pause(self):
        try:
            self.channel.pause()
        except Exception:
            pass

    def unpause(self):
        try:
            self.channel.unpause()
        except Exception:
            pass

    def stop(self):
        """Call on every exit path. See the module docstring."""
        try:
            self.channel.stop()
        except Exception:
            pass


def available_voices(voice_dir):
    """Voice-clip stems on disk, minus pygbag's transcoded duplicates."""
    return sorted(
        p.stem for p in voice_dir.glob("*.ogg") if not p.stem.endswith("-pygbag")
    )
