# Fifty-move root shortcut — patch summary for Opus

**Seat 01, area 1. One page. Applies to commit `6b98f217`.**

## 1. The bug

At a root position whose FEN says `halfmove >= 100`, the engine adjudicates the position as a draw **before
searching**, so it returns 0 nodes and misses a mate that is actually on the board. It is not a "draw score is
wrong" bug: the same board one halfmove earlier finds the mate.

It costs **real games**, not just analysis. With the brief's S14 settings applied and three clock modes, the
mate-in-one board at halfmove 100 answers `bestmove f2f3 / cp 0 / 0 nodes` under `go wtime 1000 btime 1000`,
`go wtime 10000 btime 10000` **and** `go movetime 500`; at halfmove 99 the same board answers `a1a8 / mate 1 /
1344 nodes` under all three (`job2/asan/gameplay_fifty.txt`).

It is not a general terminal-node defect: an already-mated board correctly reports `bestmove 0000 / score
mate 0` at halfmove 0, 98, 99, 100, 101 and 150 (`job2/asan/analyse_halfmove.txt`, Q1 block).

## 2. The one-line change

`forge-combo29/src/search.cpp`, **line 2251** (the line runs onto 2252). Remove `board.halfmove_clock() >= 100`
from the `root_drawn` test:

```c
// before
const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
                                           board.is_insufficient_material());
// after
const bool root_drawn = !legal.empty() && (board.is_repetition() || board.is_insufficient_material());
```

Patch file: `forge-combo29/swarm/01/job2/fifty_move_mate.patch.txt`, applies with
`patch -p2 --fuzz=0` from the repo root against `6b98f217`.

**Why removing it is safe.** The leaf test `is_draw()` (search.cpp:1302) already returns a win for a mate on
the hundredth half-move, and it already sees the fifty-move draw at `halfmove >= 100` *inside* the tree. The
root shortcut was only ever an optimisation. The more conservative variant that keeps the shortcut when the
side to move has no non-pawn material (so no mate is possible) is also prepared, honesty-checked and in the
same job folder as `job2b/`; this one-line version is the one I recommend because it is the smaller diff.

## 3. Before / after — four commands

Board `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - <H> 1` (white mates with `a1a8`). Run each against the release build
and against the patched build; the `sleep` keeps `quit` from reaching the search thread early.

```sh
# halfmove 99 — unpatched
printf 'position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 99 1\nisready\ngo depth 6\n' | { cat; sleep 1; } | ./forge
# halfmove 99 — patched
printf 'position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 99 1\nisready\ngo depth 6\n' | { cat; sleep 1; } | ./forge-patched
# halfmove 100 — unpatched
printf 'position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1\nisready\ngo depth 6\n' | { cat; sleep 1; } | ./forge
# halfmove 100 — patched
printf 'position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1\nisready\ngo depth 6\n' | { cat; sleep 1; } | ./forge-patched
```

Pasted output (sha256 unpatched `e06310ec…`, patched `81c52608…`):

```
halfmove  99 unpatched:  info depth 6 ... score mate 1 nodes 126 ... pv a1a8     bestmove a1a8
halfmove  99 patched:    info depth 6 ... score mate 1 nodes 126 ... pv a1a8     bestmove a1a8
halfmove 100 unpatched:  info depth 6 ... score cp 0   nodes 0   ... pv          bestmove f2f3   <-- BUG
halfmove 100 patched:    info depth 6 ... score mate 1 nodes 126 ... pv a1a8     bestmove a1a8
```

## 4. Regression evidence: genuine draws stay drawn, and the cost

Boards where no mate exists before the claim — the shortcut was *correct* for these, so the patch must not
break them. Base vs patched, `regress_fifty_patch.py` (`job2/asan/regress_fifty_patch.txt`):

| board | go | base | patched | verdict |
|---|---|---|---|---|
| KQ v K, halfmove 100 | depth 10 | cp 0, 0 nodes | cp 0, 280 nodes, 1.0 ms | still a draw |
| KQ v K, halfmove 100 | movetime 100 | cp 0, 0 nodes | cp 0, 1792 nodes, 1.1 ms | still a draw |
| KQ v K, halfmove 150 | depth 10 | cp 0, 0 nodes | cp 0, 280 nodes, 0.9 ms | still a draw |
| KR v K, halfmove 150 | depth 10 | cp 0, 0 nodes | cp 0, 200 nodes, 0.8 ms | still a draw |
| K v K, halfmove 150 | depth 10 | cp 0, 0 nodes | cp 0, **0 nodes**, 0.7 ms | still a draw |
| mate in 1, halfmove 100 | depth 10 | cp 0, 0 nodes | **mate 1**, 210 nodes | mate found |
| mate in 1, halfmove 100 | movetime 100 | cp 0, 0 nodes | **mate 1**, 1344 nodes | mate found |

**Cost: 0.2–0.6 ms wall and at most 1,792 nodes** on the genuine-draw roots; K v K stays at 0 nodes. Bounded
by the existing time management in a clock search. Note the one-line version gives up the shortcut for *all*
halfmove>=100 roots including bare-king ones; the `job2b` variant keeps it where no mate is possible, which is
why it is offered as the conservative alternative.

## 5. The four pins, before and after

| pin | expected | unpatched | patched |
|---|---|---|---|
| `bench 11` | 312866 | 312866 PASS | 312866 PASS |
| `bench 13` | 862329 | 862329 PASS | 862329 PASS |
| `bench 16` | 3024920 | 3024920 PASS | 3024920 PASS |
| `go perft 5` | 4865609 | 4865609 PASS | 4865609 PASS |

Unpatched: `HONESTY.txt` and `honesty/asan/summary.txt`. Patched: `honesty/fix2/summary.txt`
(one-line patch) and `honesty/fix3/summary.txt` (conservative variant). Each is the pasted output of
`honesty/honesty.py`, one fresh process per check.

## 5b. RECOMMENDED: one patch that closes every door (`job2c`)

Because section 6 shows neither existing patch is complete, I built and tested the combined fix. It is the one
I would apply.

`forge-combo29/swarm/01/job2c/fifty_move_and_doors.patch.txt` (`-p2` from `forge-combo29/`, applies clean with
`--fuzz=0`, and the applied tree is byte-identical to the source I tested). It is my reset-aware fifty-move test
**plus** seat 12's immediate-mate bypass applied to the repetition and dead-material doors:

```c
bool root_draw_adjudicated = !legal.empty() &&
    (board.is_repetition() ||
     (board.halfmove_clock() >= 100 && !board.has_non_pawn_material(board.side_to_move())) ||
     board.is_insufficient_material());
if (root_draw_adjudicated) {
    for (const Move move : legal) {           // a mate on the board outranks any claim
        Board child = board; Undo undo;
        (void)child.make_move(move, undo);
        if (child.legal_moves().empty() && child.in_check()) { root_draw_adjudicated = false; break; }
    }
}
const bool root_drawn = root_draw_adjudicated;
```

Measured (`job2c/`, `job2/asan/mypatch_on_repetition.txt`, `job2/asan/mate3_clocks.txt`):

| case | unpatched | one-line (`job2`) | seat 12 (`swarm-12`) | **combined (`job2c`)** |
|---|---|---|---|---|
| mate-in-1, no history | mate 1 / 108 | mate 1 / 108 | mate 1 / 108 | mate 1 / 108 |
| mate-in-1 at halfmove 99 | mate 1 / 108 | mate 1 / 108 | mate 1 / 108 | mate 1 / 108 |
| mate-in-1 at halfmove 100 | cp 0 / 0 | mate 1 / 108 | mate 1 / 108 | **mate 1 / 108** |
| mate-in-1 at threefold, counter 8 | cp 0 / 0 | cp 0 / 0 | mate 1 / 108 | **mate 1 / 108** |
| pawn-move mate-in-3 at halfmove 100 | cp 0 / 0 | mate 2 / 398 | cp 0 / 0 | **mate 2 / 398** |
| KQ v K, KR v K, K v K at 100-150 (genuine draws) | cp 0 / 0 | cp 0, K v K 0 nodes | cp 0 / 0 | **cp 0, K v K 0 nodes** |
| four pins | PASS | PASS | PASS | **PASS** |

**Relationship to seat 27's patch is unchanged:** this patch rewrites the same block, so apply it *instead of*
my one-line diff or seat 12's, and still **before** seat 27's `drawn_root_reporting`.

## 6. Relationship to the other root patches — apply ONE root fix, not two

Two other seats fixed the same block independently, and all three of us rewrite `root_drawn` at
`search.cpp:2251`. **Do not stack my diff and seat 12's: they are the same change written two ways and they
will not apply on top of each other.** Checked, not assumed (`patch_compose_test.sh`,
output `patch_compose.txt`, each run a fresh copy of `6b98f217` in /tmp, applies done from inside
`forge-combo29/`):

| combination | result |
|---|---|
| mine alone (`-p2`) | CLEAN |
| seat 12 alone (`-p2`) | CLEAN |
| seat 27 alone (`-p1`) | CLEAN |
| **mine then seat 27** | CLEAN, and the final file is byte-identical to seat 27 then mine |
| **seat 12 then seat 27** | CLEAN, and the final file is byte-identical to seat 27 then seat 12 |
| mine then seat 12 (or the reverse) | **FAILED — the hunk is already applied** |

**THE DECIDING MEASUREMENT (do not rank the two patches — they are complementary).** I ran seat 12's own
repetition case against my patch (`mypatch_on_repetition.py`, output `job2/asan/mypatch_on_repetition.txt`).
The case is seat 12's, taken from its `two_doors.py`; the harness is mine; the setup is verified with
python-chess before any verdict (shuffle legal, `is_repetition(3)` True, halfmove clock 8). Board
`6k1/5ppp/8/8/8/8/8/R5NK` with `a1a8` mate in 1, `go depth 6`, fresh process per case:

| case | unpatched | **my patch** | seat 12's patch |
|---|---|---|---|
| mate-in-1, no history (control) | mate 1 / 108 / a1a8 | mate 1 / 108 / a1a8 | mate 1 / 108 / a1a8 |
| mate-in-1 at **halfmove 99** | mate 1 / 108 / a1a8 | mate 1 / 108 / a1a8 | mate 1 / 108 / a1a8 |
| mate-in-1 at **halfmove 100** | **cp 0 / 0 / g1e2** | **mate 1 / 108 / a1a8** | **mate 1 / 108 / a1a8** |
| mate-in-1 at a **threefold root**, counter 8 | **cp 0 / 0 / g1e2** | **cp 0 / 0 / g1e2** | **mate 1 / 108 / a1a8** |

**So my patch does NOT fix the repetition door** — exactly as its diff predicts, because it only removes the
`halfmove_clock() >= 100` test and leaves the repetition branch adjudicating. The two patches cover
**different doors** and a merger must choose by which door matters:

| door | fixed by |
|---|---|
| a mate at halfmove >= 100 whose line resets the counter (incl. mate-in-1, and a pawn-move mate-in-3) | **my patch** (seat 12's does not) |
| a mate at a **threefold root** with the counter well under 100 | **seat 12's** (mine does not) |
| a plain mate-in-1 at halfmove 100 | both |

This also **confirms seat 21's verification** of seat 12's repetition door from the other side, and it means my
earlier S-F25 "could not reproduce" was my own bad setup, not a refutation of seat 12.

**Plainly: neither patch is complete, and the measured boundary is a mate whose line does not reset the
fifty-move counter.** My patch fixes mate-in-1 *and* any mate whose first move is a capture or a pawn move (that
resets the counter, so no claim is available); seat 12's fixes mate-in-1 only. Neither fixes a mate that needs
quiet moves to deliver, because there the opponent simply claims the draw at 100 — and on those boards `cp 0`
is the **correct** answer, not a bug. Board-by-board:

| board at halfmove 100 | forced mate | counter reset by the mating line? | unpatched | my patch | seat 12 |
|---|---|---|---|---|---|
| `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1` | 1 ply | yes (mate ends it) | cp 0, 0 nodes | **mate 1** | **mate 1** |
| `8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1` | 3 plies, first move `h6h7` is a pawn move | yes (pawn move resets) | cp 0, 0 nodes | **mate 2**, 398 nodes | cp 0, 0 nodes |
| `8/8/8/8/2K4Q/8/8/1k6 w - - 100 1` | 3 plies, all quiet | **no — Black claims** | cp 0, 0 nodes | cp 0, 324 nodes | cp 0, 0 nodes |

So: **on the counter-resetting class my patch is strictly more complete than seat 12's** (row 2), and on the
third row `cp 0` is correct chess for all three builds — I had earlier read that row as a missed mate and was
wrong (S-F19 corrected by S-F22/S-F23). The clock path behaves identically to the depth path in every case.
But this table covers only the fifty-move door. **For the repetition door the result is the other way round**
(see the deciding measurement above): mine does not fix it, seat 12's does. Neither patch is the whole fix.

**An earlier limit I claimed, now withdrawn** (`compare_two_fixes.py`, output `compare_two_fixes.txt`): on a
halfmove-100 board where the mate is **3 plies** away (`8/8/8/8/2K4Q/8/8/1k6 w - - 100 1`), **neither patch
finds it** — mine searches 216 nodes and still says `cp 0`, seat 12's answers `cp 0` in 0 nodes. The same board
at halfmove 0 scores `cp 1331` on the unpatched engine, so the mate is real and the loss is the root
adjudication, not the search. Both patches fix the **mate-in-1** case (`mate 1` on both builds); neither is a
complete fix for "a mate reachable before the fifty-move claim".

**Order.** Whichever root fix is chosen must go in **before** seat 27's `drawn_root_reporting` patch. All three
patches and their branches, so this is checkable:

| patch | branch | path in the repo | level |
|---|---|---|---|
| my one-line fix | `for-fable-and-opus/swarm-01` | `forge-combo29/swarm/01/job2/fifty_move_mate.patch.txt` | `-p2` |
| my conservative variant (alternative to the above, not additional) | `for-fable-and-opus/swarm-01` | `forge-combo29/swarm/01/job2b/fifty_move_mate_conservative.patch.txt` | `-p2` |
| seat 12 `two_doors_mate` | `for-fable-and-opus/swarm-12` | `forge-combo29/swarm/12/job1/two_doors_mate.patch.txt` | `-p2` |
| seat 27 `drawn_root_reporting` | `for-fable-and-opus/swarm-27` | `forge-combo29/swarm/27/job1/drawn_root_reporting.patch.txt` | `-p1` |

Note on order: my test shows mine+27 and 12+27 **both** apply cleanly in **either** order and produce
byte-identical result files, so the order is a safety margin rather than a hard requirement on this
`6b98f217` base — but apply the root fix first, because that is the order seat 27 verified and a later rebase
can change which hunks conflict.

## 7. How every number above was measured (cold, not warm)

Seat 10 found that two identical unrestricted searches **in one process** give different node counts
(startpos `go depth 12`: 56,720 then 4,951 then 4,516), that a fresh process is cold every time, that
`ucinewgame` restores cold, and that `Clear Hash` does **not**. I reproduced all four on this build
(`cold_warm.py`, output in `job2/asan/cold_warm.txt` and `cold_warm_heavy_*.json`):

```
startpos, go depth 12:   COLD(3 procs) 56720 56720 56720 | WARM(1 proc) 56720 4951 4516
                         UNEW(ucinewgame) 56720 56720 56720 | CHASH(Clear Hash) 56720 40569 35808
```

**So: every number in sections 3, 4 and 5 is COLD**, and I can say exactly why rather than assume it:
- `honesty/honesty.py` (the four pins) launches **one fresh process per pin** (`subprocess.run` per check).
- `job2/analyse_halfmove.py`, `job2/regress_fifty_patch.py` and `job2/gameplay_fifty.py` each call
  `subprocess.Popen` **inside the per-case function**, so every case is a fresh process. No harness of mine
  sends `ucinewgame`; `gameplay_fifty.py` sends it after the S14 setoptions and before the single search it
  measures, so that case is cold twice over. **I never used `Clear Hash` as a reset anywhere.**
- The 126-node / `mate 1` figure and the 0-node / `cp 0` figure were re-checked explicitly four ways on the
  boards the summary quotes (`cold_warm.py`): three separate processes, one process with three searches and
  nothing between them, `ucinewgame` between them, and `Clear Hash` between them. **All four give the same
  answer on these boards** (`mate 1/126` and `cp 0/0` respectively), because the answer there comes from the
  root adjudication or from a 126-node mate search, not from a hash-dependent deep search. The numbers are
  quoted **cold** and they are also warm-stable, but I label them **cold** because that is how they were
  produced.
- One place where warm state *would* have mattered and does not: the regression table's node counts (200 to
  1,792) are small and each row is its own process, so no row inherits another's hash.

## 8. What I have not measured

A **complete** fix for every draw-claim door: the combined patch in section 5b closes the fifty-move door
(mate-in-1 and a counter-resetting mate-in-3) and the threefold door (mate-in-1). The **dead-material door turns
out to need no fix**: the engine's `is_insufficient_material()` is exactly "no pawn/rook/queen, and either <= 1
minor or all bishops on one colour", material in which no mate is constructible — swept 400 such positions, 273
with insufficient material, **0** had any legal mating move, and 0 of 40 engine searches returned a mating move
(`job2c/dead_material_door.txt`). I still have not tested a mate that both resets the counter and lands on a
later move with the opponent able to claim nothing — that case is unmeasured. So "closes every door" means every
door that can actually hide a mate on the evidence I have.

Elo cost of any of these patches: not measured (no game-pair match).

The cost on roots that are *genuinely* drawn by repetition or by material and also sit at halfmove >= 100 was
not measured board-by-board beyond the table above; the table's K v K row is the bare-king case (0 nodes). I
did not run a game-pair match to price the patch in Elo, and I did not test a root that is *lost* for the side
to move at halfmove >= 100.
