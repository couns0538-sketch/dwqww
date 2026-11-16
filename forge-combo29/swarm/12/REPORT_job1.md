# REPORT — seat 12, area 2, job 1: the two root-draw doors and their patch

## What was asked

From the coordinator, on information from seat 28 (S-F4) and seat 01 (S-F5/F7): past the
`halfmove >= 100` root check there is a second key, `board.is_repetition()` at the root, which
produces the same skip, so seat 01's patch closes only one door. Tasks: (1) reproduce both doors
under ASan+UBSan; (2) if the repetition door is real, extend the patch so a root mate-in-one is
searched regardless of either draw condition, with a matched pair (same board, only the draw
condition differing) giving node counts and bestmove; (3) state whether a genuine fifty-move or
repetition root with no mate must still return a draw score, since that must not regress.

## The answer

**Both doors are real, and both are now closed by one patch that changes 15 lines of
`src/search.cpp` and nothing else.** With the patch, all four cases of the matched pair answer
`a1a8` / `mate 1` / `144 nodes`, byte-identical to the un-drawn control; without it, the two drawn
cases answer `g1e2` / `cp 0` / `0 nodes`. Every genuine draw (fifty-move at 100 and 150,
threefold repetition of a quiet position, K v K, K+B v K) still answers `cp 0` with the same
bestmove, node count and info lines as before the patch — **0 regressions over 12 cases**.

## How sure

High. Both doors are reproduced from scratch on my own builds, the fix is measured on release and
on ASan+UBSan with identical results, the honesty pins hold on all four builds, and the draw
behaviour is checked case-by-case against the unpatched engine rather than assumed.

## Honesty numbers

| build | bench 11 | bench 13 | bench 16 | perft 5 | verdict |
|---|---|---|---|---|---|
| release, unpatched | 312866 | 862329 | 3024920 | 4865609 | PASS |
| ASan+UBSan, unpatched | 312866 | 862329 | 3024920 | 4865609 | PASS |
| **release, patched** | **312866** | **862329** | **3024920** | **4865609** | **PASS** |
| **ASan+UBSan, patched** | **312866** | **862329** | **3024920** | **4865609** | **PASS** |

exe hashes: release 6e0e9522…, asan_patched 2ac6c7af… (full lines in
`job1/reproduction/honesty_patched*.txt`). ASan build: `nm` counts `__asan_` 35, `__ubsan_` 15.

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| reproduce door 1 (halfmove 100) on ASan+UBSan | done | `job1/reproduction/doors_unpatched_asan.json` | `door1_hm99` a1a8 / mate 1 / 108 nodes vs `door1_hm100` g1e2 / cp 0 / 0 nodes |
| reproduce door 2 (repetition, halfmove 8) on ASan+UBSan | done | same file | `door2_after_moves` g1e2 / cp 0 / 0 nodes; `door2_control_fen` (same board by FEN) a1a8 / mate 1 / 108 nodes |
| write the patch over both conditions | done | `job1/two_doors_mate.patch.txt` | 15 added lines, `patch -p1 --fuzz=0` clean |
| matched pair after the patch | done | `job1/reproduction/doors_patched_release.json` | all four cases a1a8 / mate 1 / 108 nodes |
| regressions: genuine draws must still draw | done | `job1/reproduction/regression_patched_release.json` | 0/12 failing; every draw unchanged |
| same under ASan+UBSan | done | `job1/reproduction/regression_patched_asan.json` | 0/12 failing, 0 sanitizer lines |
| honesty pins on both patched builds | done | `job1/reproduction/honesty_patched*.txt` | 4/4 on each |

## The matched pair (the thing that was asked for)

Same board every time: `6k1/5ppp/8/8/8/8/8/R5NK w`, mate in one by `Ra8#`. Only the draw
condition differs.

| case | how the position is set | halfmove | repetition on board | unpatched | patched |
|---|---|---|---|---|---|
| `mate_hm99` | `position fen … - - 99 40` | 99 | no | a1a8 / mate 1 / 144 nodes | a1a8 / mate 1 / 144 |
| **`mate_hm100`** | `position fen … - - 100 40` | **100** | no | **g1e2 / cp 0 / 0** | **a1a8 / mate 1 / 144** |
| **`mate_rep3`** | `position fen <base> moves g1f3 g8h8 f3g1 h8g8 g1f3 g8h8 f3g1 h8g8` | **8** | **yes, threefold** | **g1e2 / cp 0 / 0** | **a1a8 / mate 1 / 144** |
| `mate_rep_ctrl` | `position fen 6k1/5ppp/8/8/8/8/8/R5NK w - - 8 5` | 8 | no | a1a8 / mate 1 / 144 | a1a8 / mate 1 / 144 |

`mate_rep3` and `mate_rep_ctrl` are the *same board* with the *same halfmove clock*; the only
difference is that one was reached by moves (so the engine's key history says "threefold") and
the other was set by FEN. python-chess confirms `is_repetition(3)` is true for the move-list
case and that `a1a8` mates in both. That isolates the repetition term exactly as the halfmove
pair isolates the counter.

## Does a genuine draw still draw? (the part that must not regress)

Yes — unchanged in every case:

| case | expected | unpatched | patched |
|---|---|---|---|
| quiet at halfmove 99 | searched normally | a2a3 / cp 14 / 4627 | a2a3 / cp 14 / 4627 |
| quiet at halfmove 100 | draw | a2a3 / cp 0 / 0 | a2a3 / cp 0 / 0 |
| quiet at halfmove 150 | draw | a2a3 / cp 0 / 0 | a2a3 / cp 0 / 0 |
| quiet threefold (Nc3-b1/Nc6-b8 shuffle) | draw | a2a3 / cp 0 / 0 | a2a3 / cp 0 / 0 |
| the same quiet board by FEN | searched | a2a4 / cp 9 / 7619 | a2a4 / cp 9 / 7619 |
| K v K | draw | e1d1 / cp 0 / 0 | e1d1 / cp 0 / 0 |
| K+B v K | draw | c1b2 / cp 0 / 0 | c1b2 / cp 0 / 0 |
| pawn race, halfmove 100, no mate | draw | e2e3 / cp 0 / 0 | e2e3 / cp 0 / 0 |

So the patch does not turn drawn roots into searches: it only overrides the adjudication when
the side to move has a mate **on the board this move**. The score, the chosen reply and the node
count of a genuine draw are identical to the unpatched engine.

## The patch

`job1/two_doors_mate.patch.txt` — unified diff against 6b98f217, applies with
`patch -p1 --fuzz=0` from the repository root. It replaces the single `root_drawn` expression
with one that first looks for an immediate mate:

```cpp
    bool root_draw_adjudicated = !legal.empty() && (board.is_repetition() ||
                                                    board.halfmove_clock() >= 100 ||
                                                    board.is_insufficient_material());
    if (root_draw_adjudicated) {
        for (const Move move : legal) {
            Board child = board;
            Undo undo;
            (void)child.make_move(move, undo);
            if (child.legal_moves().empty() && child.in_check()) {
                root_draw_adjudicated = false;      // a mate on the board outranks the claim
                break;
            }
        }
    }
    const bool root_drawn = root_draw_adjudicated;
```

Why this shape and not seat 01's deletion: seat 01 removed the halfmove term, which leaves the
repetition term (and the dead-material term, which is harmless but inconsistent) in place. Here
the adjudication is kept whole and only *withheld* when a mate exists, so nothing else about a
drawn root changes. Note it is still only a mate-in-one; a mate in two on a fifty-move root is
still adjudicated drawn (`mate_in_2_hm100` in the plan below), which is a deliberate, stated
limit of this patch rather than an oversight.

## Findings

| id | what | how to see it again |
|---|---|---|
| S-F2 | the repetition door: `is_repetition()` at the root gives the same 0-node draw adjudication as the halfmove counter, so a mate-in-one is missed with the halfmove clock at 8 | `python3 forge-combo29/swarm/12/job1/two_doors.py ~/build/asan/forge /tmp/d.json` → `door2_after_moves g1e2 0 cp 0` vs `door2_control_fen a1a8 108 mate 1` |
| S-F3 | `two_doors_mate.patch.txt` closes both doors with 0 regressions on 12 draw/mate cases, honesty pins 4/4 on release and ASan+UBSan | `python3 forge-combo29/swarm/12/job1/regression.py ~/build/release_patched/forge /tmp/r.json` → 0 failing |

## Suspicions, not proven

- A mate **in two or more** on a fifty-move or repetition root is still adjudicated drawn by
  this patch. Whether that is wrong depends on whether the engine treats the draw as a claim the
  opponent must make; the FIDE rule says a mate ends the game at once, so a forced mate in two
  arguably should also be searched. **Not fixed here, not tested beyond one case.**
- `is_insufficient_material()` is included in the same expression but no board can be both
  dead-material and have a mate, so that term is untouched and untested.

## What I did NOT do

- No mate-in-two/mate-in-three analysis beyond the single `mate_in_2_hm100` plan case.
- No test with `Threads > 1` for the patched path (area 4's ground).
- No perft or bench run of the patched engine beyond the four honesty pins.

## What I am NOT sure about

- Whether the PC build reproduces the same node counts as these cloud builds; the pins say it
  should, but I have no PC access.

## Times

See `job1/stamps.txt` (`date -u` after every part) and the commit times.

## Last command output

`git status --short` and `ls` of the job folder are in `job1/final_state.txt`.

---

## Known limit of the root-only fix: the same short-circuit fires ONE PLY DOWN

Asked by the coordinator. Answer: **yes, it can, and here is a position that shows it.**

`Worker::is_draw` (`src/search.cpp:1300-1310`) is called from inside the tree as well as at the
root (`search.cpp:1425` for the qsearch/leaf path and `search.cpp:1569` for the main recursion,
guarded by `if (!root_node)`). At a non-root node it returns a draw for

```cpp
    if (board.halfmove_clock() >= 100) {
        return !board.in_check() || board.has_legal_move();
    }
```

which is exactly the term the root patch neutralises *at the root only*. So a child node with
the counter at 100 is still scored 0 even when the side to move there has a mate.

### The position (mine, constructed for this question)

```
6k1/8/5PPP/8/8/8/8/R6K b - - 99 40
```

Black to move, so the root is **not** drawn (counter 99, no repetition) — the root patch does not
apply. Black has **exactly two** legal moves, `g8h8` and `g8f8`; both keep the counter at 100 (no
pawn moves and no captures exist), and on both children White mates at once with `Ra8#`.
python-chess confirms each child, e.g. after `g8h8`: `7k/8/5PPP/8/8/8/8/R6K w - - 100 41`, mate
`a1a8`. The truth is therefore **mate -1** (Black is lost by force).

### What the engine says — matched pair, only the counter differs

| FEN | true result | release (unpatched) | patched release | patched ASan |
|---|---|---|---|---|
| `… b - - 97 40` | mate -1 | **mate -1 / g8h8 / 63 nodes** | mate -1 / g8h8 / 63 | mate -1 / g8h8 / 63 |
| `… b - - 98 40` | mate -1 | **mate -1 / g8h8 / 63 nodes** | mate -1 / g8h8 / 63 | mate -1 / g8h8 / 63 |
| **`… b - - 99 40`** | **mate -1** | **cp 0 / g8f8 / 36 nodes** | **cp 0 / g8f8 / 36** | **cp 0 / g8f8 / 36** |
| `… b - - 100 40` | drawn root | cp 0 / 0 nodes | cp 0 / 0 nodes | cp 0 / 0 nodes |

Both counters 97 and 98 give the true `mate -1` in 63 nodes; at 99 the child node hits 100 and the
score collapses to `cp 0` in 36 nodes. **The patch does not fix this** and is not meant to: it is a
root-only fix, and this is its known limit.

### The control that keeps me honest

```
6k1/5ppp/8/8/8/8/8/R5NK b - - 99 40
```

At counter 99 this also answers `cp 0` (227 nodes) — but here it is **correct**: Black has six
pawn moves that reset the counter to 0 and keep the game going, so Black really does escape the
mate, and `cp 0` is the right evaluation. Including it stops the first position from being read as
"any hm99 position is broken".

### Why a fix belongs one level down, not at the root

The correct repair is inside `is_draw`: return a draw for `halfmove_clock() >= 100` only when the
side to move cannot mate this move — the same test as the root patch, applied where the node is
created. **I have not written or tested that patch**; it is a change on a hot path called at every
leaf, and area 2's job is to measure, not to retune the search. It is recorded here as the next
step for whoever owns the search.

### Files

- `job1/node_draw.py` — the harness (per-reply python-chess enumeration + engine search, reads to
  `bestmove` before `quit`).
- `job1/node_draw_release.txt`, `job1/node_draw_patched.txt`, `job1/node_draw_patched_asan.txt` —
  raw output on the three builds.
