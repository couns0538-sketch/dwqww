# STATUS — swarm seat 70

Branch `for-fable-and-opus/swarm-70`, folder `forge-combo29/swarm/70/`.
Task: make `searchmoves` semantics exact (five questions from the assignment).

## 2026-11-17T04:00Z — build + honesty pins

Built commit `6b98f217` in `/agent/repos/base` (separate worktree, outside the
work tree), release, g++ 13.3.0, `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`.
NOTE: `/usr/bin/c++` on this machine is clang 18 and its `-lstdc++` is missing, so
CMake must be given `-DCMAKE_CXX_COMPILER=g++` or configuring fails.

| pin | got | expected | ok |
|---|---|---|---|
| `bench 11` | 312866 | 312866 | yes |
| `bench 13` | 862329 | 862329 | yes |
| `bench 16` | 3024920 | 3024920 | yes |
| `go perft 5` (startpos) | 4865609 | 4865609 | yes |

Raw: `honesty.txt`. Engine sha256 `7c4e1aee58d880afade8d8e032028cbf9b92f38e39723f0aaf154ed7fa233622`.

## 2026-11-17T04:35Z — job 1 done (why does naming all legal moves change the answer?)

Verdict: it is a **search change, not tie-reordering**, and the cause is **one
line**: `src/search.cpp:2093` suppresses the root TT store when the root is
restricted, so the next iteration's root picker has no hash move.

- `job1/order_vs_search.txt` — 120 searches, 22 changed bestmove, **0/22 kept the
  same score**, 18/22 differ by >= 10 cp. A tie account predicts 22/22 unchanged.
- `job1/causal_split.txt` — 60 positions, depth 12, four builds. Restoring the TT
  store alone (`pA`) gives **60/60** bestmoves and **60/60** scores identical to
  the plain search. Sparing IIR alone (`pB`) gives 51/60 and 7/60. Both (`pAB`)
  gives 60/60.
- `job1/ties.txt` — 52 positions whose root tie is a **PROVEN** mate in 1 for every
  tied move. 156 position-depth cases, **3/156** bestmove changes, versus 22/120 on
  ordinary positions. So the restriction *can* re-pick inside a proven tie, but
  almost never; on ordinary positions it changes the move because it changes the
  score.
- `job1/pinned_vs_intree.txt` — the pinned score of a move equals its in-tree score
  in **10/265** pairs, sd **44 cp**, **211/265** off by >= 10 cp.

Scratch patch builds live at `/tmp/patchA`, `/tmp/patchB`, `/tmp/patchAB`. No
engine source committed; the diffs are described line-by-line in FINDINGS F1.

## 2026-11-17T04:50Z — job 2 done (is the distortion a function of pin count?)

`job2/pin_count.txt`: 60 positions, depth 12, k in {1, 2, 4, 8, all}.

| k | bestmove preserved | score delta = 0 | `|delta| >= 10` | median `|delta|` |
|---|---|---|---|---|
| 1 | 60/60 | 1/60 | 48/60 | 28 |
| 2 | 54/60 | 1/60 | 47/60 | 24 |
| 4 | 54/60 | 3/60 | 45/60 | 23 |
| 8 | 51/60 | 2/60 | 44/60 | 22 |
| all | 49/60 | 1/60 | 46/60 | 26 |

**Flat in k.** One pinned move is already fully distorted, so there is no cheap
"pin just the winner" escape.

## 2026-11-17T05:15Z — job 3 done (rank order over 3 and 5 candidates)

`job3/rank_final.txt` (depth 12), `job3/rank_final_depth10.txt` (depth 10),
`job3/verifier_operation.txt`, `job3/rank_why.txt`.

References are validated before use, and the validation is printed in the file:
determinism 60/60, unrestricted MultiPV rank-1 == plain bestmove only 53/60.

| ref | k | pair comparisons | agree | 95% Wilson | exact full order |
|---|---|---|---|---|---|
| R3 | 3 | 159 | **142/159** | 0.835–0.932 | 40/53 |
| R3 | 5 | 530 | **486/530** | 0.890–0.938 | 30/53 |
| R1 | 3 | 159 | 139/159 | 0.814–0.917 | 35/53 |
| R1 | 5 | 530 | 475/530 | 0.867–0.919 | 20/53 |

Depth 10 agrees (R3 k=3 134/144, k=5 434/480). Reference-free confirmation in
`job3/verifier_operation.txt`: pinning each of the top 5 alone makes the plain
bestmove the top-scoring candidate in only **49/60**, with **11/60** positions
where some other candidate beats it.

`job3/rank_why.txt` reconciles this with the brief's 8/8: agreement is
**313/317 = 0.987** when candidates differ by >= 100 cp and **478/511 = 0.935** at
>= 10 cp. So two-candidate comparisons are sound at large gaps and not at small
ones. The 8/8 was a large-gap sample.

## 2026-11-17T05:35Z — job 4 done (empty, mixed, malformed)

`job4/degenerate.txt`, `job4/zero_move_meaning.txt`, `job4/diagnostic_placement.txt`.

- empty / all-illegal: `bestmove 0000`, `cp 0`, 0 nodes, plus
  `info string searchmoves restriction has no legal root moves`.
- **legal + illegal: silently drops the illegal token, no diagnostic at all**, and
  is byte-identical to pinning the legal move alone.
- `0000`, wrong case, zero-length: silently dropped, same string as empty.
- checkmate -> `score mate 0`; stalemate -> `score cp 0`; restriction -> info
  string. So `0000` is separable, and "always an error" is wrong for terminal roots.
- argument order irrelevant (control C2); harness can see a restriction (C1).
- CONFIRMS the coordinator's FEN-placement correction: `invalid FEN` arrives in the
  position reply before `readyok`. My driver scans both streams regardless.

## 2026-11-17T05:45Z — controls

`selftest_falsify.txt`: seven planted faults, all caught; the one thing a perft
check cannot see (a halfmove-clock edit) is named, not hidden. Exit code 0.
`power.txt`: power and 95% intervals for every discriminator, computed before the
verdicts were written, including where this audit is NOT decisive (k=2 intervals
reach 0.947–0.959, so a true 0.95 is not excluded).

## 2026-11-17T05:50Z — repository hygiene

Removed 4 committed `.pyc` binaries (the brief forbids binaries in the repo) and
added `.gitignore` for `__pycache__/` and `*.pyc`. 59 text files tracked. Verified
`gen_positions.py` regenerates all 112 fixtures byte-identically (no diff).

## Deliverables

- `FINDINGS.md` — F1..F11, each with a re-runnable command.
- `SEARCHMOVES_TABLE.md` — 20-row verdict table: sound / vacuous / wrong, each with
  its measurement.
- `STATUS.md` — this file.

## Next

Nothing outstanding from the assignment. If continued: measure whether the
one-line TT-store fix also fixes a single pinned score's value (F1 says it fixes
`<all legal>`; it does not follow that a one-move root does), and re-run job 3
under patched builds to see whether any pinned ranking becomes usable.
