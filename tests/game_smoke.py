#!/usr/bin/env python3
"""Broad, shallow crash coverage for every game that isn't one of the eight
VoiceQuizGame games (those have deep behavioural coverage in
quiz_behaviour.py - this is deliberately its opposite: does each of the
other 31 games import, boot, and run its first few frames without raising,
not whether its gameplay is correct).

Before this, those 31 games - including every file this project's session
touched for the RESIZABLE canvas-corruption fix - had zero automated
coverage of any kind. A broken import or a crash on the very first frame
would only ever have surfaced when a child actually opened that game.

Each game is run in its own subprocess rather than in-process one after
another. Two independent reasons converge on the same answer:

  * every game calls pygame.display.set_mode() itself, expecting to own the
    display outright - there is no shared harness to drive instead the way
    quiz_behaviour.py drives layout() directly.
  * quiz_behaviour.py already documents that repeated pygame.SCALED
    set_mode() calls under SDL's dummy driver corrupt the heap after about
    four calls (pygame-ce 2.5.7, "corrupted size vs. prev_size"). 31 games
    in one process would hit that well before the end of the list.

A subprocess per game sidesteps both: a crash in one game cannot corrupt or
take down the process running the next 30, and each game gets the clean
display state it assumes.

Every game handles Escape identically (`if event.key == K_ESCAPE:
running = False`, unconditional on any menu/paused state), so each
subprocess posts an Escape keydown before starting the game and lets it
exit on its own. Games that do not consume it within the timeout are
reported separately from actual failures - a longer intro animation
eating the first frame's events is not a crash.

    tests/game_smoke.py                 # every non-quiz game
    tests/game_smoke.py games.snake     # just one, by its module name
"""

import asyncio
import importlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TIMEOUT_S = 4

# (app_dir, module, entry) - entry matches the "entry" field each app's own
# hub registry (main.py) uses to launch it, so this list is exactly the set
# of games a child can actually reach that the quiz suite does not cover.
GAMES = [
    ("KidZoneWeb", "games.fruit_finder", "function"),
    ("KidZoneWeb", "games.whack_a_mole", "function"),
    ("KidZoneWeb", "games.balloon_pop", "function"),
    ("KidZoneWeb", "games.bug_squasher", "function"),
    ("KidZoneWeb", "games.fish_catch", "function"),
    ("KidZoneWeb", "games.star_catcher", "function"),
    ("KidZoneWeb", "games.memory_match", "function"),
    ("KidZoneWeb", "games.jumping_jack", "function"),
    ("KidZoneWeb", "games.maze", "class"),
    ("KidZoneWeb", "games.simon_pattern", "class"),
    ("KidZoneWeb", "games.planets", "class"),
    ("ArcadeWeb", "games.snake", "function"),
    ("ArcadeWeb", "games.breakout", "function"),
    ("ArcadeWeb", "games.flappy_bird", "function"),
    ("ArcadeWeb", "games.game_2048", "function"),
    ("ArcadeWeb", "games.tic_tac_toe", "function"),
    ("ArcadeWeb", "games.reaction_timer", "function"),
    ("ArcadeWeb", "games.rock_paper_scissors", "function"),
    ("ArcadeWeb", "games.air_hockey", "function"),
    ("ArcadeWeb", "games.word_scramble", "function"),
    ("ArcadeWeb", "games.color_switch", "function"),
    ("ArcadeWeb", "games.pong", "function"),
    ("ArcadeWeb", "games.space_invaders", "function"),
    ("ArcadeWeb", "games.asteroids", "function"),
    ("ArcadeWeb", "games.tetris", "function"),
    ("ArcadeWeb", "games.connect_four", "function"),
    ("ArcadeWeb", "games.minesweeper", "function"),
    ("ArcadeWeb", "games.pinball", "function"),
    ("ArcadeWeb", "games.typing_test", "function"),
    ("ArcadeWeb", "games.archery", "function"),
    ("ArcadeWeb", "games.trivia", "function"),
]


def _run_one(app_dir, module_name, entry):
    """Runs inside the child subprocess for exactly one game."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    app_path = ROOT / app_dir
    os.chdir(app_path)
    sys.path.insert(0, str(app_path))

    import pygame
    pygame.init()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

    module = importlib.import_module(module_name)

    async def drive():
        coro = module.Game().run() if entry == "class" else module.run()
        try:
            await asyncio.wait_for(coro, timeout=TIMEOUT_S)
            print("SMOKE_RESULT=exited")
        except asyncio.TimeoutError:
            print("SMOKE_RESULT=timeout")

    asyncio.run(drive())


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    games = [g for g in GAMES if only in (None, g[1])]
    if only and not games:
        print(f"no game matches {only!r}", file=sys.stderr)
        sys.exit(2)

    failures = []
    timeouts = []
    for app_dir, module_name, entry in games:
        label = f"{app_dir}/{module_name}"
        try:
            proc = subprocess.run(
                [sys.executable, __file__, "--child", app_dir, module_name, entry],
                capture_output=True, text=True, timeout=TIMEOUT_S + 15,
            )
        except subprocess.TimeoutExpired:
            failures.append(label)
            print(f"FAIL {label}: subprocess did not exit even after the internal timeout")
            continue

        if proc.returncode != 0:
            failures.append(label)
            print(f"FAIL {label}")
            print(proc.stderr[-2500:])
        elif "SMOKE_RESULT=timeout" in proc.stdout:
            timeouts.append(label)
            print(f"ok (did not act on Escape within {TIMEOUT_S}s) {label}")
        else:
            print(f"ok {label}")

    print()
    print(f"{len(games) - len(failures)}/{len(games)} games start and run without crashing")
    if timeouts:
        print(f"{len(timeouts)} did not exit on Escape within {TIMEOUT_S}s "
              f"(not necessarily a bug - see notes above): {', '.join(timeouts)}")
    if failures:
        print(f"FAILED: {failures}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        _run_one(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        main()
