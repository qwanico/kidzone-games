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

from games.common import display  # noqa: E402

# Portrait phone, the same phone rotated, a tablet, and the old fixed design
# size. The first two are what the fixed 900x700 canvas used to letterbox.
VIEWPORTS = [(390, 844), (844, 390), (820, 1180), (900, 700)]

QUIZ_GAMES = [
    "games.colors", "games.counting", "games.feelings", "games.letters",
    "games.math_game", "games.picture_words", "games.shapes",
    "games.sight_words",
]


def check(results, label, cond):
    results.append((label, bool(cond)))


def check_geometry(results, game, where):
    """Everything on screen, nothing overlapping, nothing too small to tap."""
    w, h = game.WIDTH, game.HEIGHT
    screen = pygame.Rect(0, 0, w, h)
    rects = {
        "card": game.card_rect,
        "home": game.home_button,
        "pause": game.pause_button.rect,
        **{f"button{i}": b.rect for i, b in enumerate(game.buttons)},
    }
    for name, rect in rects.items():
        check(results, f"{where}: {name} is on screen", screen.contains(rect))

    for i, button in enumerate(game.buttons):
        check(results, f"{where}: button{i} is tappable (>=44px)",
              button.rect.width >= 44 and button.rect.height >= 44)
        check(results, f"{where}: button{i} clear of the card",
              not button.rect.colliderect(game.card_rect))

    if len(game.buttons) == 2:
        check(results, f"{where}: answer buttons do not overlap",
              not game.buttons[0].rect.colliderect(game.buttons[1].rect))
    check(results, f"{where}: card clear of the header",
          game.card_rect.top >= game.home_button.bottom)

    # Rects alone would pass a game whose card is 160px tall and whose
    # reveal font is still the 160px one built for a 900x700 desktop, so
    # anything a subclass pre-sizes is checked against the card it draws in.
    card = game.card_rect
    for attr in ("font_reveal", "font_equation", "font_decor"):
        font = getattr(game, attr, None)
        if font is not None:
            check(results, f"{where}: {attr} fits the card",
                  font.get_height() <= card.height)

    picture = getattr(game, "picture_surface", None)
    if picture is not None:
        check(results, f"{where}: picture fits the card",
              picture.get_width() <= card.width and picture.get_height() <= card.height)

    animations = getattr(game, "animations", None)
    if animations:
        frame = next(iter(animations.values())).current()
        check(results, f"{where}: animation frame fits the card",
              frame.get_width() <= card.width and frame.get_height() <= card.height)

    icon = getattr(game, "fruit_icon", None)
    if icon is not None and game.buttons:
        across = icon.get_width() * 5 + 6 * 4
        check(results, f"{where}: five icons fit across a button",
              across <= game.buttons[0].rect.width)


def exercise(module_name):
    results = []
    display.set_viewport_override(None)
    game = importlib.import_module(module_name).Game()

    check(results, "starts on the menu", game.state == "menu")
    game.handle_menu_click(game.start_button.rect.center)
    check(results, "Start begins play", game.state == "playing")
    check(results, "a round is dealt",
          game.current is not None and len(game.buttons) >= 2)

    # Drawing is where the migration actually moved code - custom button
    # faces, the card, both draw_prompt branches. None of it raises until
    # something renders it, so every state gets drawn at least once below.
    def drew(label):
        try:
            game.draw()
            check(results, label, True)
        except Exception as exc:
            check(results, f"{label} ({type(exc).__name__}: {exc})", False)

    drew("draws the open question")

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

    drew("draws the revealed answer and feedback")

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
    drew("draws the milestone banner")

    # Pausing mid-feedback must bank the remaining time, or resuming would
    # skip straight past the answer the child is still looking at.
    game.enter_pause()
    check(results, "pause enters the paused state", game.state == "paused")
    check(results, "remaining feedback time is banked",
          game._pause_remaining is not None)
    drew("draws the pause overlay")
    game.resume_game()
    check(results, "resume returns to play", game.state == "playing")

    scored = game.score
    game.handle_click(game.card_rect.center)
    check(results, "tapping the card replays without scoring", game.score == scored)

    game.handle_click(game.home_button.center)
    check(results, "home requests quit", game.quit_requested)

    return results


def exercise_viewports(module_name):
    """Lay the game out at each viewport and check the result is usable.
    A fixed 900x700 canvas scaled to a portrait phone is legal geometry and
    completely unplayable, so bounds alone are not the test - touch targets
    and non-overlap are.

    layout() is driven directly rather than through set_mode(): calling
    set_mode() repeatedly with pygame.SCALED corrupts the heap under the
    dummy video driver (verified on pygame-ce 2.5.7 - a fourth call aborts
    with "corrupted size vs. prev_size", and the same loop without SCALED is
    fine). Browsers do the real set_mode on rotation and have done since
    mid-game rotation was fixed; what is worth testing here is the re-flow
    arithmetic, which is what layout() is.
    """
    results = []
    display.set_viewport_override(None)
    game = importlib.import_module(module_name).Game()
    game.start_game()

    for width, height in VIEWPORTS:
        game.layout(width, height)
        game.init_background()
        where = f"{width}x{height}"
        check(results, f"{where}: lays out at the real viewport",
              (game.WIDTH, game.HEIGHT) == (width, height))
        check_geometry(results, game, where)
        try:
            game.draw()
            check(results, f"{where}: draws", True)
        except Exception as exc:
            check(results, f"{where}: draws ({type(exc).__name__}: {exc})", False)

    # Mid-game rotation: portrait to landscape must keep the round intact.
    game.layout(390, 844)
    before = (game.current, game.score, len(game.buttons))
    game.layout(844, 390)
    game.init_background()
    check(results, "rotation keeps the round",
          (game.current, game.score, len(game.buttons)) == before)
    check_geometry(results, game, "after rotation")

    display.set_viewport_override(None)
    return results


def main():
    targets = sys.argv[1:] or QUIZ_GAMES
    pygame.init()
    pygame.display.set_mode((900, 700))

    failed = []
    for name in targets:
        try:
            results = exercise(name) + exercise_viewports(name)
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
