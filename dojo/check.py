"""Quest checker. Run: python3 dojo/check.py

Runs your `roll_damage` against the rules in quest01_dice.py and awards XP.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from quest01_dice import roll_damage

# (attack, defense, roll), expected, what the case is really testing
CASES = [
    ((10, 4, 12), 6, "plain hit: attack beats defense"),
    ((7, 2, 15), 5, "plain hit: another ordinary swing"),
    ((5, 5, 10), 1, "equal stats must still deal the minimum"),
    ((3, 9, 12), 1, "heavy armour must never heal the defender"),
    ((10, 4, 20), 20, "critical doubles attack and ignores defense"),
    ((3, 99, 20), 6, "critical ignores even absurd armour"),
    ((10, 4, 1), 0, "fumble deals nothing"),
    ((99, 0, 1), 0, "fumble beats a huge attack"),
]


def main():
    passed, failed = 0, []
    for args, expected, why in CASES:
        try:
            got = roll_damage(*args)
        except NotImplementedError:
            print("roll_damage is still a stub. Open dojo/quest01_dice.py.\n")
            return 1
        except Exception as exc:
            got = f"{type(exc).__name__}: {exc}"
        if got == expected:
            passed += 1
            print(f"  PASS  roll_damage{args} -> {got}")
        else:
            failed.append((args, expected, got, why))
            print(f"  FAIL  roll_damage{args} -> {got!r}, expected {expected}")

    total = len(CASES)
    print(f"\n{passed}/{total} cases passing")

    if failed:
        print("\nWhat the failing cases are checking:")
        for args, expected, got, why in failed:
            print(f"  - {why}")
            print(f"      roll_damage{args} gave {got!r}, should give {expected}")
        print("\nNo XP yet. Fix, rerun, and remember: read the rule, then the code.")
        return 1

    print("\n*** QUEST 1 COMPLETE - +100 XP ***")
    print("Report back and I will review your code like a real pull request.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
