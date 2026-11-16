# seat 20 — job 28: thread-count audit of my own finds, and a striking threading effect

## Part 1 — every score of mine WAS Threads 1, and I can prove it

Swarm rule (22:19Z): any score must be from Threads 1 unless the job is about threading. My scripts from job1–job23
never sent a `setoption name Threads`, so they ran at the engine's **default**. The default is
`option name Threads type spin default 1` (from the exe's own `uci` answer), and I verified that
"no setoption at all" is **bit-identical** to an explicit `Threads 1`:

| settings | three runs on the S-F19 board, `go depth 12` |
|---|---|
| no setoption at all | `c2b1` / mate −7 / **15465** nodes — three times, identical |
| `Threads 1` explicit | `c2b1` / mate −7 / **15465** nodes — three times, identical |

So my job1–job23 scores are Threads 1 by fact, not by assumption. From job24 onward I state `Threads 1` explicitly
in the option list (`repro_s06f6.py`, `pc_honesty.py`, `pc20_rerun.py`).

## Part 2 — the same board at Threads 2 and 4 finds the CORRECT mate distance

| Threads | runs (bestmove / score / nodes) |
|---|---|
| 1 | `c2b1` / **mate −7** / 15,465 (identical, ×3) |
| 2 | `c2c3` / **mate −4** / 55,803, 52,934, 56,053 |
| 4 | `c2c3` / **mate −4** / 80,186, 84,006, 85,970 |

Two separate facts here, and they must not be confused with each other:

1. **The score is more accurate at Threads ≥ 2 on this board.** `mate −4` (8 plies) is exactly the true forced
   distance my job16 proved by exhaustive search, and the PC build reaches it at depth 12 even single-threaded
   (S-F34). So on the BASE tree, multithreading reaches the right answer that Threads 1 cannot at that depth.
   Plausible mechanism: a different search order explores black's faster mate, the same breadth effect that makes
   S14 change mate distances (my S-F18). **Not proven** — this is one position.
2. **The node counts vary wildly between runs at Threads ≥ 2** (52,934–56,053 at Threads 2; 80,186–85,970 at
   Threads 4) while Threads 1 is bit-identical every time. That is exactly seat 04's warning, confirmed
   independently on my board: at Threads ≥ 2, nodes and (per seat 04) scores are not reproducible.

Note the bestmove DID vary here between 1 and ≥2 threads (`c2b1` vs `c2c3`), which is a *better* move, not noise —
but it does confirm that a bestmove comparison across thread counts is meaningless.

## Part 3 — the audit of every seat's FINDINGS.md

Script `job27/thread_audit.py`, raw `job27/thread_audit.txt`: it scans every seat's FINDINGS.md for lines that
report a `cp`/`mate` score, and classifies each by whether it states a thread count.

**Result: 120 lines across the swarm report a score and either name Threads > 1 or never state a thread count.**
By seat, the ones that matter most (all UNSTATED, i.e. a confirmation must be a re-run at Threads 1 stating the
count):

| seat | scored lines with no thread count | examples |
|---|---|---|
| 21 | 4 | 21-F9 (halfmove ≥ 100 sweep), 21-F11 (`mate 0` on a checkmated root) |
| 25 | 6 | S-F1/S-F2 (mate −12 depth-12), S-F8 (`mate -9` on a middlegame) |
| 27 | 8 | S-F8/S-F8a/S-F8b/S-F8c (searchmoves score gap) |
| 28 | 3 | S-F4 (repetition door), S-F19 |
| 30 | 5 | 30-F7 (side-blind shortcut), 30-F19 (**PC r15 build**) |
| 20 (me) | 12 | all now covered by Part 1 above |

**Consequence I am applying from now on:** when I confirm any of these on the PC build, I run at
`Threads 1` and state it in the line; and any finding of theirs whose score was measured above Threads 1 is
**flagged unconfirmable until re-run**, not confirmed.

I have not tried to judge *which* of the seats' runs were multithreaded — the audit only shows they did not say.
The three that DO name a thread count in the line are safe to confirm as written.
