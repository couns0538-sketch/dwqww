# Repetition: at which occurrence count is a root declared drawn? (both builds, Threads 1)

Script `repcount2.py`, one board throughout, only the AMOUNT OF HISTORY differs, so the repetition
rule is isolated from any evaluation difference. `go depth 10`, Hash 16, fresh process per row,
**Threads 1**. Occurrence counts verified with python-chess's own repetition key
(board, side, castling, ep) before each run.

## The table — `repcount2_all.txt`

| occurrences | build / settings | score | nodes | verdict |
|---|---|---|---|---|
| 1 (start position) | PC r15 / PC20 | `cp 20` | 8569 | searched |
| 2 | PC r15 / PC20 | `cp 20` | 8569 | searched |
| **3** | PC r15 / PC20 | `cp 23` | 13424 | **searched** |
| **4** | PC r15 / PC20 | `cp 23` | 13424 | **searched** |
| 1 | base / S14 | `cp 21` | 9575 | searched |
| 2 | base / S14 | `cp 21` | 9575 | searched |
| **3** | base / S14 | `cp 0` | **0** | **DECLARED DRAWN** |
| **4** | base / S14 | `cp 0` | **0** | **DECLARED DRAWN** |

## What this settles

1. **The base tree declares a thrice-repeated root drawn** (0 nodes, `a2a3` = first legal move) and
   searches a twice-repeated one. My 15-F1-era reading of file 3 was right: `matches >= 2` means the
   third occurrence trips it.
2. **The PC build does not declare it drawn at any count I tested, up to four occurrences.** It
   searches `cp 23` / 13,424 nodes. So on the PC build the repetition rule is not firing at the root
   at all in this test.
3. The `2 -> 3` jump in the PC build's nodes (8569 -> 13424) and score (20 -> 23) is consistent with
   the engine seeing more repetition history and scoring it slightly differently, not with any draw
   recognition.

## Why this matters, stated carefully

File 3 says of the drawn-root repair: "It also needs a THIRD occurrence: a second one is searched
normally (`Board::is_repetition`, `matches >= 2`)". Read as a description of the intended behaviour,
a third occurrence should be declared drawn. On my board, on the PC build, three occurrences is
searched.

**Two readings I cannot separate with this evidence, and I do not claim which is true:**

- (a) The PC build's repetition check genuinely does not fire at the root, so a thrice-repeated
  position is played on rather than drawn — a real behavioural difference from the base tree, and the
  opposite of what file 3 led me to expect.
- (b) The check does fire but needs something my move list does not produce — e.g. the repetition
  must arise inside the search rather than being part of the root's game history, or the engine counts
  only repetitions of positions it has itself seen in a game-play context.

What I can state as measured: same board, same build, only the history length varying, three
occurrences, `cp 23` and 13,424 nodes instead of `cp 0` and 0 nodes; and the base tree under the same
harness does declare it. A seat wanting to settle (a) versus (b) should plant the repetition deeper
in a longer game rather than at ply 8.

## Method note

`repcount.py` (the first version, in this folder) printed correct scores but no node counts; it is
superseded by `repcount2.py`, which records `nodes` and therefore can tell "searched" from
"declared drawn". Both are committed; the second is what the table above comes from.
