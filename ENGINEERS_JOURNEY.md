# The Engineer's Journey

A long-form mentorship campaign run inside this repository. The codebase is the
game world: every quest touches real code that real children play.

## Character Sheet

| Field | Value |
|---|---|
| Name | Qwanico |
| Rank | **Junior Apprentice Engineer** |
| XP | 0 / 500 |
| Campaign started | 2026-09-01 |

### Rank ladder

Apprentice -> Developer -> Engineer -> Senior Engineer -> Architect ->
Principal Engineer -> Software Wizard  *(500 XP per rank)*

### Strengths observed

- Ships. 45 commits, 46,598 lines of working Python, ~40 playable games.
- Recognises duplication as a cost. The `games/common` extraction is a real
  engineering instinct, not a tutorial exercise.
- Writes honest commit messages that explain *why*, not just *what*.

### Weaknesses to attack

- **Zero automated tests** across 46,598 lines. Every regression is found by a
  child, not by a machine. This is the campaign's first dragon.
- Correctness currently rests on manual play-testing, so refactors are scary.
- Untested code cannot be safely refactored, which caps every later level.

## Quest Log

| # | Quest | Type | XP | Status |
|---|---|---|---|---|
| 1 | The Untested Kingdom | Testing | 100 | **ACTIVE** |

## Field Notes

Recorded as the campaign proceeds: concepts proven, concepts shaky, and the
dates they were last exercised.
