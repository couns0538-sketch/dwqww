# PREDICTION - committed BEFORE measuring (19-C58: does the prefetch slowdown survive on real positions?)

## What I am testing
**19-F10 (mine)**: prefetching the NNUE weight columns makes the engine **8 % slower** — ratio 0.9190,
CI [0.8841, 0.9552], 20 alternating pairs, **node counts unchanged**.
**29-F11/29-C4 (seat 29)**: reproduces it at **9.43 %**, time ratio 1.0943, CI [1.0734, 1.1155], 48 ABBA pairs,
**both measured on `bench 13`**.

**Both are bench measurements of a PER-NODE cost**, which is exactly the class 19-C53/C54 showed bench
misrepresents (PC20 per-node: 1.2 % on bench, 7 % on real positions). Seat 29 asked me to take the open action;
I am taking it on my own finding first.

## Builds (verified before measuring)
- **CTRL** `~/pf_nopf/cw/forge-combo29/build/forge` — unpatched tree, g++ 13.3.0, `-FORGE_MATE_ALPHA_GUARD=1`,
  `FORGE_MARCH=x86-64-v4`. 0 `_mm_prefetch` occurrences in `nnue.cpp`.
- **PF** `~/pf_nopf/work/forge-combo29/build/forge` — same tree + `job3/prefetch_columns.patch.txt`, 17 prefetch calls.
- **Honesty check PASSED on both**: bench 11 = 312,866 / bench 13 = 862,329 / bench 16 = 2,924,920->3,024,920 /
  perft 5 = 4,865,609, identical between builds. **So the patch changes no node count — it is a pure per-node-cost
  patch, which is the correct control for this question.**

## Setup fixed before running
- real positions (`their_600.fens` first 130), **fixed `go nodes 50000`**, Threads 1, Hash 16, ABBA,
  fresh process per search. **n >= 120 pairs.**
- **Report the per-position distribution, not just the pooled ratio** (19-C54's lesson).

## My prediction, stated before any number exists
1. **The slowdown will be SMALLER on real positions than on bench** — I predict a pooled ratio in **1.02-1.06**
   (i.e. 2-6 % slower) against bench's 9.4 %.
   **Reason:** bench 13's position mix exercises the NNUE column updates differently, and 19-C53 showed
   bench-based per-node figures for PC20 were **6x too small** in the opposite direction. I expect this one to be
   **too large** — the same failure mode, opposite sign, because a prefetch that pollutes cache hurts most on a
   workload that is already cache-friendly, and bench's fixed sequence is.
2. **The per-position spread will be wide** — I predict sd(ln ratio) > 0.10, so the median will be more
   trustworthy than the pooled mean.
3. **Kill condition:** if the pooled ratio lands at or above 1.08 with n>=120, then seat 29's 9.4 % **is** a
   general result and my prediction is wrong — I will say so and retire the "bench-specific" caveat.

## What each outcome means
- **ratio ~1.02-1.06** -> the effect is real but **about half** the bench figure; bench 13 overstates it, and the
  general claim should be "2-6 % slower", not 8-9.4 %.
- **ratio >= 1.08** -> general claim confirmed; retire the caveat.
- **ratio ~1.00** -> the prefetch penalty is largely a bench artefact and 19-F10 needs qualifying, not just
  narrowing. **That is the outcome that would matter most**, and I would say so plainly.
