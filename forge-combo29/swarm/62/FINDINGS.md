# FINDINGS -- seat 62

Each line: id | area | claim | file with the command that shows it again | status

| 62-F1 | draw rule | The root guard at search.cpp:2251 is NOT the cause: an instrumented build prints `root_drawn=0` at halfmove 98 AND 99, and only fires at 100. | `job2/CODE_PATH.md`, `job2/diag/` (`python3 job2/diag.py --exe ... --fen ... --depth 12 --out-prefix ...`) | NEW |
| 62-F2 | draw rule | The cause is the leaf rule at search.cpp:1302-1304 evaluated one ply down: at H=99 every child sits at clock exactly 100 and is not checkmate, so line 1304 returns "draw" and the child returns 0 before the mate at ply 2. 24 stderr lines `clause=halfmove>=100 ply=1 ... returns=1`. | `job2/CODE_PATH.md`, `job2/diag/hm99.stderr.txt` | NEW |
| 62-F3 | draw rule | Halfmove 98 is correct for the same board because the clock-100 node lands at ply 2 and IS checkmate: 23 lines `clause=halfmove>=100 ply=2 in_check=1 has_legal=0 returns=0`. The whole difference is one ply of offset. | `job2/diag/hm98.stderr.txt` | NEW |
| 62-F4 | depth | No depth fixes it: nodes grow exactly 3 per depth step (3/6/18/36/72/96 at depths 1/2/6/12/24/32) because both children return before expansion. cp 0 at depth 24 and 32. | `job2/CODE_PATH.md` | NEW |
| 62-F5 | band | The miss band is `H > 100 - p`, not "halfmove 98-99": a mate delivered at ply p is found iff p <= 100-H. Measured 80/80 (position,clock) pairs across p=2 and p=4; p=2 misses from H=99, p=4 misses from H=97. | `job3/BAND_TABLE.md` (`python3 job3/measure_band.py --exe /tmp/build-base/forge --fens job3/SET_p2.fens --out ...`) | NEW |
| 62-F6 | repair | Seat 12's `two_doors_mate.patch.txt` does NOT fix it and does not change a single node: byte-identical to base on 6 positions x 3 cells. It patches the root, and the root guard is not what fires here. | `job2/PATCH_TEST.md` (`python3 job2/patch_test.py`) | NEW |
| 62-F7 | repair | Seat 27's `drawn_root_reporting.patch.txt` does NOT fix it and does not change a single node: it only changes how many info lines a drawn root prints, and on this board the root guard never fires. | `job2/PATCH_TEST.md` (`python3 job2/patch_test.py`) | NEW |
| 62-F8 | control | A bare-king `cp 0` is the ROOT GUARD (0 nodes, `insuf=1`), a different code path, and is not usable as a control for this defect. Node count separates them mechanically: 0 nodes = root guard, non-zero = leaf rule. | `job3/CONTROL_CLASS.md` (`python3 job3/control_class.py --exe /tmp/build-base/forge --out control_class.json`) | NEW |
| 62-F9 | control | With a clock reset actually available the engine does NOT collapse to 0 nodes: it searches 23,099-99,692 nodes and returns real scores. So `cp 0` at ~40 nodes is the specific signature of this defect. | `job3/CONTROL_CLASS.md` | NEW |
| 62-F10 | control | A position lost to a forced mate that ALSO has a legal reset still misses: hm=0 gives `mate -4` / 48,791 nodes, hm=99 gives `cp 0` / 123 nodes. "A reset exists" is not sufficient for correctness; the reset must also be the best defence. | `job3/CONTROL_CLASS.md` | NEW |
| 62-F11 | real play | 5,689 real engine tournament games, 792,081 plies, 503 band plies with no reset: exactly 1 band position has a forced mate and it is the FOUND cell. Zero EXPOSED. | `job4/REAL_PLAY.md` (`python3 job4/scan_pgn.py --pgn-dir /tmp/base --out ...`) | NEW |
| 62-F12 | real play | Widened to the correct condition `p > 100-H` over the same corpus: 1,220 distinct FENs actually tested for a forced mate, 3 have one, 0 are in the exposed cell. | `job4/WIDE_BAND.md` (`python3 job4/scan_pgn_wide.py --pgn-dir /tmp/base --out ...`) | NEW |
| 62-F13 | real play | The 3 real positions with a mate all sit exactly ON the boundary p == j0 and are all answered correctly (`mate -3`/`mate -2`/`mate -1`). A real converter mates at the first opportunity, so it lands on the working cell by construction. The defect needs a winner that delays one ply past the crossing. | `job4/REAL_PLAY.md` | NEW |
| 62-F14 | real play | Engine self-play reaches clock >= 93 easily (11 positions in 2 games) but never with a mate available (0 of 11). | `job4/REAL_PLAY.md` | NEW |
| 62-F15 | measurement | A first scan reported 1 "hit" at H=100 that was already checkmate (`mate 0`, 0 nodes). Two filter bugs: terminal boards were not excluded, and j0=0 (the side to move can claim the draw itself) was counted. Fixed; honest count is 0. The label was wrong and measuring the hit caught it. | `job4/WIDE_BAND.md` | NEW |
| 62-F16 | settings | Under the PC's own S14 options at depth 24 the defect reproduces exactly: H=98 `mate -1`, H=99 `cp 0`. DrawJitter turns the `cp 0` into `cp -2`/`cp +1` (sign follows node count), i.e. a fabricated evaluation that looks real -- so a check must not rely on the score being exactly 0. | `job2/S14_AND_JITTER.md` | NEW |

---

# The four questions, answered

## 1. Which path produces cp 0 at halfmove 99, and why no depth fixes it

NOT the root guard (`search.cpp:2251`) -- measured, `root_drawn=0` at H=99. It is
the leaf rule at `search.cpp:1302-1304`, reached one ply down. At H=99 every child
sits at clock exactly 100, is not checkmate, and `!in_check() || has_legal_move()`
returns true, so the child returns 0 and ply 2 (where `Ra8#` lives) is never
generated. Depth cannot help because both children return before expansion:
nodes grow by exactly 3 per depth step, and depth 24 and 32 both still say cp 0.

## 2. Blast radius

80 (position, clock) pairs measured, prediction matched 80/80. The exposed cell is
`H > 100 - p`, not "98-99":

| mate length | first clock missed | boundary clock (found) |
|---|---|---|
| p=2 (mate in 1 against loser) | H=99 | H=98 |
| p=4 (mate in 2 against loser) | H=97 | H=96 |
| p=6 (mate in 3 against loser) | H=95 (derived) | H=94 |

Misses reproduced: 8/8 at p=2, 24/24 at p=4. Control class: a bare-king cp 0 is
the ROOT GUARD (0 nodes) and proves nothing here; the real control (a drawn
position with a reset available) searches 23k-99k nodes and returns a real score,
which is the contrast that makes `cp 0` at ~40 nodes diagnostic.

## 3. Is it reachable in real play?

Not observed. 5,689 real tournament games, 792,081 plies, 1,220 distinct FENs
tested: **0 exposed**. The 3 real positions that did have a mate all sit exactly
on the working boundary cell (`p == j0`) and are all answered correctly -- because
a real converter mates at the first opportunity. The defect needs a winner that
delays the mate by exactly one ply past the clock crossing.

## 4. Do the existing repairs fix it?

No, and not partially either. Seat 12 `two_doors_mate` and seat 27
`drawn_root_reporting` are **node-for-node identical to base** on all 18 cells
measured, at both mate lengths. Both pass all four honesty pins. The comparison
harness is proven live: `--plant-fault` produces 9 mismatches and exit 1.

Seat 12 patches the root, and the root guard is not what fires. Seat 27 changes
how many info lines a drawn root prints, and on this board the root guard does not
fire at all. The line that must change is 1304: it asks "is this node checkmate?"
when the rule needs "can the side to move deliver mate now?".
