seat 10, model DeepSeek V4.1 Flash, 2026-11-16T21:06:36Z, token 300082526017344

branch for-fable-and-opus/swarm-10
area 10 (CHECKING THE OTHERS)
SEED 1001
folder forge-combo29/swarm/10/

## Mon Nov 16 09:14:24 PM UTC 2026
done: seat claimed, engine built (release, out of tree), all four honesty pins MATCH (HONESTY.txt).
done: area 10 job 2 (recount deepseek6's newest report = long56). Report: REPORT_job2.md.
  F1 raw summary says seqs:0 vs report 2000. F2 its illegal-bestmove check is dead code (proved with a
  planted fake engine). F3 "per-sequence records in out/" false (2 files). F4 no sanitizer proof committed,
  but number is TRUE: my own ASan+UBSan build + planted fault (3 lines counted), 2000 seqs = 0 lines.
  F5 4,803 (position,go) pairs replayed cleanly = 0 illegal bestmoves.
next: commit+push this, then THE CYCLE step 1 (read board). No seat has written a FINDINGS.md yet, so
  area 10 job 1 (confirm another seat's NEW finding) has no candidate; next candidate is job 3 (glmflash5).
runs: nothing in background.

## Mon Nov 16 09:15:54 PM UTC 2026
done: area 10 job 1 (first check). CONFIRMS 19-F5 (bench is a stdin command; main ignores argv) — check1/RESULT.txt.
  5 of 5 predictions held, including both source line numbers (uci.cpp:590, :651).
next: another check of an unchecked NEW finding, or area 10 job 3 (glmflash5 recount) if none is left.
note: there is no perf on this machine, so 19-F1..F4 and 29-F1/F2 (profiler shares) cannot be reproduced here.

## Mon Nov 16 09:16:41 PM UTC 2026
done: check2. CONFIRMS seat 01's S-F2 (side to move in check from two pieces: accepted, perft 2 = 64,
  divide identical to python-chess's). check2/RESULT.txt. Note: python-chess does not refuse the FEN,
  it only sets STATUS_IMPOSSIBLE_CHECK, so the comparison is like-for-like.
done so far: job2 (recount deepseek6 long56, 5 findings), job1/check1 (CONFIRMS 19-F5), check2 (CONFIRMS S-F2).
next: another unchecked NEW finding (seat 01 S-F1/S-F3/S-F4, seat 06 S-F1/F2, 11's S-F1/S-F4) or area 10 job 3.

## Mon Nov 16 09:30:14 PM UTC 2026
done: check3. CONFIRMS seat 06's S-F5 (total = clamp(hce+nnue); 3 of 753 with total unchanged while both
  components moved, re-measured identically in fresh processes). check3/RESULT.txt.
  Beyond it: the clamp bound is 31871 and the largest |hce+nnue| seen is 176, so the clamp never bites;
  the equality is plain hce+nnue arithmetic, not a clamp effect.
done: job2, check1 (CONFIRMS 19-F5), check2 (CONFIRMS seat01 S-F2), check3 (CONFIRMS seat06 S-F5).
next: another unchecked NEW finding, else area 10 job 3 (glmflash5 W-L-D/Elo recount).
