"""QUEST 1 - The Damage Formula.

Write `roll_damage` so it satisfies every rule below, then run:

    python3 dojo/check.py

Nothing here imports from anywhere else in this repository. This file is
yours, from line one.
"""


def roll_damage(attack, defense, roll):
    """Return the damage dealt by one attack, as an int.

    Rules, in no particular order - deciding the order is part of the quest:

      * Normal hit ....... damage is `attack` minus `defense`.
      * Minimum damage ... a connecting hit always deals at least 1.
      * Critical hit ..... a `roll` of exactly 20 doubles `attack` and
                           ignores `defense` completely.
      * Fumble ........... a `roll` of exactly 1 deals 0 damage.

    Args:
        attack:  attacker's power, an int >= 0
        defense: defender's armour, an int >= 0
        roll:    a d20 result, an int from 1 to 20

    Returns:
        int: the damage dealt.
    """
    # YOUR CODE HERE. Delete the line below when you start.
    raise NotImplementedError("roll_damage is not written yet")
