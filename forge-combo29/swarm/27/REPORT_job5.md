# REPORT job 5 — area 7: the transposition table's lifecycle and the `searchmoves` root
seat 27 · branch `for-fable-and-opus/swarm-27` · base `6b98f217` · seed 2701

## What was asked / the answer / how sure

- **What was asked:** continue area 7 with a test for anything suspicious and a patch only when a fault is
  proven and the patch leaves the honesty numbers unchanged.
- **The answer:** two findings, and one prediction of mine **falsified by my own test**.
  - **S-F8 (the valuable one):** a `searchmoves`-restricted root does not just search a smaller tree — it
    reports a **different score** for the same position. Startpos, depth 12: `go depth 12` = cp 30, the same
    search restricted to the very move it plays (`searchmoves e2e4`) = cp 23. Five identical plain runs give
    cp 30 / 56720 nodes every time, so it is not noise.
  - **S-F9:** a `setoption` sent during a search truncates that search instead of queueing the change.
  - **P1 falsified:** I predicted `setoption name Hash` could resize the table under a live search and race the
    workers. It cannot: `setoption` calls `stop_search()` first (`uci.cpp:259`). My 12 tries all "finished"
    quickly because each search was being aborted, not raced — I found that out by checking, not assuming.
- **How sure:** high on both findings (each is a small table of paced, deterministic runs plus a control).
  For S-F8 I found **two of the causes and could not close it**: a partial patch is included and labelled
  partial, and S-F8 is left **OPEN**. I would rather hand over two pinned causes and an honest gap than a
  tidy claim that is wrong.

## Honesty numbers

Unchanged: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 (base `e06310ec…`).
The partial patch build also keeps all four (raw in `job5/honesty_searchmoves/`).

## Steps

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| read `probe`/`store`/`resize`/`clear`/`new_search` and the six call sites | done | this report | `resize`/`clear` take no lock, but the UCI layer serialises them |
| resize the table during a search, 12 tries under ASan | done | `job5/f1/` | 0 crashes, 0 sanitizer lines — **because the search is aborted first** (verified in f2) |
| verify what f1 actually measured | done | `job5/f2/README.txt` | `setoption` truncates: 20 depth lines alone vs 14 with a mid-search setoption |
| restricted vs plain search at the same depth | done | `job5/f3/README.txt` | S-F8: cp 23 vs cp 30, same bestmove |
| control: five identical plain runs | done | `job5/f3/README.txt` | 5/5 cp 30 / 56720 — the driver is deterministic |
| find the cause of S-F8 | **done in part** | `job5/searchmoves_PARTIAL.md` | IIR at the restricted root is one cause (23 → 26); the TT-store guard is **not** another; a third cause remains unnamed |

## Findings

### S-F8 — `searchmoves` changes the reported score, not only the tree (area 7; beyond Opus file 1's item)
Opus's file 1 already records that a restricted root "searches a different, mostly smaller tree: internal
iterative reduction fires at the root, and no hash entry is stored for a restricted root". It does **not**
record that the score itself moves. Measured, release build, startpos, **DEFAULT tuning** (CORRECTION: an earlier version of this report said
S14; these rows are default tuning — verified afterwards), Threads 1, Hash 16, paced driver:

| go line | score at depth 12 | nodes | bestmove |
|---|---|---|---|
| `go depth 12` | cp 30 | 56720 | e2e4 |
| `go depth 12 searchmoves e2e4` | cp 23 | 26329 | e2e4 |
| `go depth 12 searchmoves e2e4 d2d4` | cp 23 | 16770 | e2e4 |

Control: five fresh plain runs give cp 30 / 56720 every time. **Why it matters:** using `searchmoves` to
re-verify a single move (a natural thing for a checker or a training pipeline to do) records a score that is
7 cp away from the engine's own unrestricted answer for that move.

### S-F9 — a `setoption` during a search truncates it (area 7, `src/uci.cpp:259`)
`go depth 20` alone reaches 20 `info depth` lines; the same search with `setoption name Hash value 64` sent
100 ms in reaches 14 and answers from the last finished iteration. Intended-looking (an option change needs a
consistent table) but observable, and a GUI that sends a mid-search setoption loses the search.

## CURRENT STATE OF S-F8 (updated after seat 10's split — read this before the section above)

**S-F8 is TWO INDEPENDENT DEFECTS**, settled by seat 10 on branch `for-fable-and-opus/swarm-10`:

| defect | what | their id / file |
|---|---|---|
| **A. restricted root computes a wrong score with an EMPTY table** | `Clear Hash` in a fresh process still gives cp 23 against a cold unrestricted cp 30, and `Clear Hash` changes **not one node** (21,640 both ways) | **10-F17** — `swarm-10/audit/raw2/K14split/summary.json`, `audit/k14_split.py` |
| **B. a restricted search POLLUTES THE SHARED TABLE** for a later unrestricted search | restricted-then-unrestricted 36,745 nodes / cp 29 vs unrestricted-then-unrestricted 4,951 / cp 30; `ucinewgame` between restores the cold 56,720 / cp 30 | **10-F15** — `swarm-10/audit/raw2/k14_tt_summary.json`, `audit/k14_tt.py` |
| A, minimal repro | `searchmoves e2e4` gives cp 16/26/23/27 at depths 8/10/12/14 against unrestricted 26/24/30/23 | **10-F18** — `swarm-10/audit/raw2/K14split/min_repro.out` |
| A, strongest form | restricting to **all 20 legal moves** still gives cp 23 / d2d4 against cp 30 / e2e4 | **10-F14** — `swarm-10/audit/AUDIT_KNOWN.md` §K14 |

**Therefore `job5/searchmoves_iir.PARTIAL.patch.txt` addresses defect A only, and only part of it. It does not
touch defect B.** It must not be presented as a fix for S-F8.

Seat 10 also reproduced my 26,329 and 16,770 node counts to the digit from an independent harness, so the
numbers in this report are independently confirmed.

**My follow-up ablation (job7/f2) adds two results and one caution:**
- **Aspiration is ruled out** as the causing term: widening `AspirationDelta` to 200 does not shrink the gap.
- **The all-20 case is now fully explained**: stopping IIR at the restricted root *and* restoring the root TT
  store makes a restriction that excludes nothing return **exactly** the unrestricted result (cp 30 / 56,720
  nodes / e2e4). That is the mechanism for a no-op restriction, and it explains 10-F12 (a repeated restricted
  search shrinking 21,640 → 17,847).
- **But the general case is NOT closed**: on the same build, restricting to `d2d4 e2e4` still gives cp 26 vs
  cp 30 at depth 12. **S-F8 remains OPEN.**
- **Caution on 10-F18's depth table**: at depths 8 and 10 the unrestricted search plays **d2d4** while the
  restricted one plays **e2e4**, so those "gaps" compare two different moves and are not errors. The sign flip
  is confounded with the move changing; the clean like-for-like case is all-20.

## Suspicions, not proven
- The third cause of S-F8. I removed both the IIR ply and the TT-store guard and the score stayed cp 26. The
  remaining candidates (aspiration seeding, and the missing tt_move starving the picker at every re-searched
  root iteration) are **guesses without a test**, so they stay here and not in FINDINGS.
- `TranspositionTable::resize`/`clear` are unlocked and their own comments demand quiescence; the UCI layer
  honours that, but an embedder calling the C++ API directly would not.

## What I did NOT do
- Did not close S-F8.
- Did not run TSan (area 4 owns it).
- Did not patch `stop_search`-on-setoption: it is the safe design.

## What I am NOT sure about
- Whether the owner considers `searchmoves` score drift a bug at all. It is a diagnostic path; my argument for
  reporting it is that its output looks like a normal search result and is not one.

## Times
`job5/stamps.txt`.

## Last command's output
`ls job5` / `git status --short` in `job5/last_commands.txt`.
