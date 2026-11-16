# S-C5 — CONFIRMS seat 07's 07-F1 (fabricated per-depth score on an empty `searchmoves` root)

Seat 07's claim: `go depth N searchmoves <a move that is not legal here>` on a board that **has**
legal moves answers a fabricated per-depth report — one `info depth D … score cp 0 nodes 0` line for
every depth up to the limit, then `bestmove 0000`, even though the engine has already diagnosed the
cause and says so in an `info string`.

**Verdict: CONFIRMS on both builds, 4/4 cases, both controls working.** My own harness
(`checks/check_07f1.py`), own builds, **Threads 1**, Hash 16, MultiPV 1, `OwnBook false`, read to
`bestmove` before quitting.

## The cases

| position | command | bestmove | depth lines | node counts | scores seen | verdict |
|---|---|---|---|---|---|---|
| startpos | `go depth 4 searchmoves e2e5` | `0000` | 4 | all **0** | `cp 0` only | **FABRICATED** |
| startpos | `go depth 6 searchmoves e2e5` | `0000` | 6 | all **0** | `cp 0` only | **FABRICATED** |
| kiwipete | `go depth 4 searchmoves e2e5` | `0000` | 4 | all **0** | `cp 0` only | **FABRICATED** |
| kiwipete | `go depth 6 searchmoves e2e5` | `0000` | 6 | all **0** | `cp 0` only | **FABRICATED** |

Every case also carries the engine's own diagnosis:
`info string searchmoves restriction has no legal root moves`.

**4 of 4, on base 6b98f217 and on PC r15** — identical.

## Why "fabricated" is the right word

A score is a claim about a position. `score cp 0` means *this position is drawn*. The engine reports
that claim at every depth while its own `nodes 0` says it did no work at all. The comparison that makes
this concrete is control C2 below: the **same board searched normally says `cp 34`**. So the fabricated
line is not merely uninformative, it asserts the opposite of the truth about the position.

## The controls (a zero must not be read as "no search" on faith)

| control | result | what it proves |
|---|---|---|
| **C1** legal `searchmoves e2e4` | `e2e4`, 6 depth lines, **max 438 nodes** | the harness does see a search when one happens |
| **C2** unrestricted `go depth 6` on the same board | `d2d4`, 6 depth lines, **max 1,703 nodes**, last score **`cp 34`** | the real value of the position, to compare the fabricated `cp 0` against |

Without C1 a zero-node result could just mean my harness cannot read node counts; without C2 there
would be no statement of what the score should have been.

## Where this overlaps with my own S-F27, said plainly

My S-F27 searchmoves check, added earlier this session, prints
`no-match 'searchmoves zzzz' -> 0000, nodes [0, 0, 0, 0, 0, 0] [ok]` — it **recorded these
zero-node lines and marked them `ok`**, because it tested only "does the no-match branch answer 0000
with zero nodes", which is the behaviour it was asked to verify.

Seat 07's framing is better: those same lines are a **fabricated score**, not a healthy zero. I have
left my check's `ok` verdict alone (it answers its own question correctly) but the two readings must be
read together — the same output is "the branch works" from a harness-sanity view and "the engine lies
about the score" from a search-correctness view. That is worth knowing for anyone reading either
document alone.

## Practical consequence (seat 07's, and I agree)

- A **GUI** is unaffected in the obvious way: it already receives `0000` and a restricted root is a
  harness construct, not a game one.
- A **harness** that tests `searchmoves` and trusts the score will record `cp 0` for a position whose
  real score is `cp 34`. Seat 07 has a 3-edit patch (`job29/job29_pc_searchmoves_empty_root.patch.txt`)
  that removes the score lines and keeps the honest `0000`; its pins were unchanged in seat 07's run.
  **I did not apply or test that patch** — confirming the defect is my job here, not the repair.

## Files

- `checks/check_07f1.py` — the harness.
- `checks/check_07f1_pc.txt`, `checks/check_07f1_base.txt` — raw runs, both builds.
- `checks/check_07f1_pc.json`, `checks/check_07f1_base.json` — raw records.
- `checks/check_07f1.meta` — exe hashes, Threads 1, settings, date.

## What I am not claiming

- Not that the score's *cause* is `restricted_root_empty` — that is seat 07's source reading
  (`search.cpp:2531` → the early branch at 2581). I confirmed the behaviour, not the code path.
- Not that the patch works; untested by me.
