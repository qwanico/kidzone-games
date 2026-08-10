#!/usr/bin/env python3
"""Drive a VoiceQuizGame subclass through the interactions a child performs.

Eight games share one base class, so a change to that base can break all
eight at once and none of it shows up as an import error. This plays each
game headlessly - start, answer right, answer wrong, run the feedback window
out, build a streak, pause, resume - and asserts the observable results.

    tests/quiz_behaviour.py                # every quiz game
    tests/quiz_behaviour.py games.colors   # just one

Lives outside KidZoneWeb/ deliberately: pygbag packs everything under the app
directory into the browser bundle, and tests are not worth shipping to a
tablet.
"""

import os
import sys
import importlib
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "KidZoneWeb"
os.chdir(APP)
sys.path.insert(0, str(APP))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402  (must follow the driver env vars)

QUIZ_GAMES = [
    "games.colors", "games.counting", "games.feelings", "games.letters",
    "games.math_game", "games.picture_words", "games.shapes",
    "games.sight_words",
]


def check(results, label, cond):
    results.append((label, bool(cond)))


def exercise(module_name):
    results = []
    game = importlib.import_module(module_name).Game()

    check(results, "starts on the menu", game.state == "menu")
    game.handle_menu_click(game.start_button.rect.center)
    check(results, "Start begins play", game.state == "playing")
    check(results, "a round is dealt",
          game.current is not None and len(game.buttons) >= 2)

    def tap(correct):
        for button, value in zip(game.buttons, game.button_values):
            if (value == game.correct_value()) is correct:
                game.handle_click(button.rect.center)
                return

    def next_round():
        pygame.time.wait(game.FEEDBACK_MS + 60)
        game.update(16)

    tap(correct=True)
    check(results, "correct answer scores", game.score == 1 and game.streak == 1)
    check(results, "feedback window opens",
          game.feedback_until > pygame.time.get_ticks())
    check(results, "correct button is flagged",
          any(b.state == "correct" for b in game.buttons))

    scored = game.score
    tap(correct=True)
    check(results, "taps during feedback are ignored", game.score == scored)

    next_round()
    check(results, "next round is dealt",
          game.feedback_until == 0 and not game.revealed)

    tap(correct=False)
    check(results, "wrong answer resets the streak",
          game.streak == 0 and game.score == 1)
    check(results, "the right answer is still revealed",
          any(b.state == "correct" for b in game.buttons))

    game.score = game.streak = 0
    for _ in range(3):
        next_round()
        tap(correct=True)
    check(results, "milestone fires at a streak of 3",
          game.milestone_text == "3 in a row!")

    # Pausing mid-feedback must bank the remaining time, or resuming would
    # skip straight past the answer the child is still looking at.
    game.enter_pause()
    check(results, "pause enters the paused state", game.state == "paused")
    check(results, "remaining feedback time is banked",
          game._pause_remaining is not None)
    game.resume_game()
    check(results, "resume returns to play", game.state == "playing")

    scored = game.score
    game.handle_click(game.card_rect.center)
    check(results, "tapping the card replays without scoring", game.score == scored)

    game.handle_click(game.home_button.center)
    check(results, "home requests quit", game.quit_requested)

    return results


def main():
    targets = sys.argv[1:] or QUIZ_GAMES
    pygame.init()
    pygame.display.set_mode((900, 700))

    failed = []
    for name in targets:
        try:
            results = exercise(name)
        except Exception as exc:  # a game that will not even start
            print(f"{name}: ERROR {type(exc).__name__}: {exc}")
            failed.append(name)
            continue
        bad = [label for label, ok in results if not ok]
        status = "ok" if not bad else f"{len(bad)} FAILED"
        print(f"{name:24s} {len(results) - len(bad)}/{len(results)} {status}")
        for label in bad:
            print(f"    FAIL: {label}")
        if bad:
            failed.append(name)

    print("\n" + ("all quiz games behave" if not failed else f"FAILED: {failed}"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
