# seat 20 — check of seat 28's S-F4 (the repetition door of the same 0-node root adjudication)

Verdict: **CONFIRMS seat 28's S-F4**, and I add the missing piece: **seat 01's patch fixes the halfmove door and
does NOT fix the repetition door**, proved on a patched build.

Raw: `check_s28f4_base.json`, `check_s28f4_patched.json`, `halfmove_control_out.txt` (pasted).
Scripts: `check_s28f4.py` (the test), `patch_copy.sh` (patch + build in a scratch copy), `halfmove_control.py`
(the control), `rerun.sh` (everything, in order).

## The construction (mine, not theirs)

Board `6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1`, mate in one by `d1d8` (proved with python-chess: it is the only
mate-in-1 move). I found a 4-ply reversible cycle with python-chess — `g1h1 g8h8 h1g1 h8g8` — so the same board
recurs:

| ply | can_claim_threefold (python-chess) | is_repetition(3) | halfmove |
|---|---|---|---|
| 0 | False | False | 0 |
| 4 | False | False | 4 |
| 8 | **True** | **True** | **8** |

So the third occurrence is a genuine threefold **at halfmove 8** — this cannot be the halfmove door (S-F5).

## The result

| case | command | bestmove | score | nodes |
|---|---|---|---|---|
| A: the board given by `position fen` | `position fen <board>` | d1d8 | mate 1 | 168 |
| B: SECOND occurrence | `position fen <board> moves g1h1 g8h8 h1g1 h8g8` | d1d8 | mate 1 | 168 |
| C: THIRD occurrence | `position fen <board> moves <cycle twice>` | **f2f3** | **cp 0** | **0** |

`f2f3` is the first legal move; 0 nodes; cp 0. The identical board with no repetition history finds the mate.
The only difference between B and C is the repetition flag.

## The part that matters for the repair

I applied seat 01's committed patch (`job7/seat01.patch.txt`, taken from seat 01's branch; applies with
`patch -p2 --fuzz=0`) to a scratch copy and rebuilt:

- Pins with the patch applied: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 —
  **all four unchanged**, so the patch is honest.
- **Halfmove door: FIXED by the patch** (control, interactive driver):

| build | hm 0 | hm 99 | hm 100 | hm 101 | hm 150 |
|---|---|---|---|---|---|
| base | mate 1 / 168 n | mate 1 / 168 n | **cp 0 / 0 n** | cp 0 / 0 n | cp 0 / 0 n |
| patched | mate 1 / 168 n | mate 1 / 168 n | mate 1 / 168 n | mate 1 / 168 n | mate 1 / 168 n |

- **Repetition door: NOT fixed by the patch.** On the patched build the three cases are
  A d1d8/mate 1/168, B d1d8/mate 1/168, **C f2f3/cp 0/0** — identical to the base build.

So seat 01's patch is necessary and not sufficient: the same `root_drawn` expression still contains
`board.is_repetition()`.

## The source, quoted (src/search.cpp:2250-2253, 6b98f217)
```
    // Terminal or adjudicated roots: report without searching.
    const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
                                               board.is_insufficient_material());
    if (root_candidates.empty() || root_drawn) {
```
The two doors are on the same line, which is why a one-term patch closes one and leaves the other.

## Correction to my own method (recorded, not hidden)
My first "control" for the patched build piped `go` and `quit` together, which lets `quit` cancel the search; it
reported `bestmove f2f3` for the patched build and I briefly believed the patch did nothing. An interactive driver
(`halfmove_control.py`) shows the patch works. The piped result was my harness's fault, not the patch's. This is
the same trap as in my job 3 and it is recorded in FINDINGS as S-F12-adjacent.

## Commands that show it again
```
python3 check_s28f4.py /agent/repos/build-base/forge . base        # A/B/C on the base build
bash patch_copy.sh                                                  # patch -p2 --fuzz=0, rebuild, pins
python3 check_s28f4.py /agent/repos/scratch-patch01/build/forge . patched
python3 halfmove_control.py <base> <patched>                        # the halfmove control
bash rerun.sh                                                       # all of the above
```
