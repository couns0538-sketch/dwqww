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

## Mon Nov 16 09:30:49 PM UTC 2026
done: check4. CONFIRMS seat 21's 21-F1 — and this one MATTERS: the brief's already-known item
  "impossible-castling FEN is ACCEPTED (perft 3 8,902)" is a MISREADING on 6b98f217. The FEN is
  refused; 8,902 is startpos perft 3 of the position left in place. 5/5 predictions held.
  check4/RESULT.txt
done: job2, check1 (19-F5), check2 (S-F2), check3 (S-F5), check4 (21-F1).
next: another unchecked NEW finding, else area 10 job 3 (glmflash5 W-L-D/Elo recount).

## Mon Nov 16 09:34:53 PM UTC 2026  [CHECKPOINT]
AUDITING every "Known:" claim in the brief (coordinator request). PREDICTIONS.md K1..K14 committed alone
at a306832b6. Results so far (all on the release build, sha256 e06310ec...):
  K1 illegal-move prefix perft1=29        PASS (engine 29 == python 29)
  K2 setoption Hash 0 message            PASS (exact 'info string invalid value for option Hash')
  K3 startpos perft 5 = 4865609           PASS
  K6 honesty pins                        PARTLY REFUTED -- pins hold ONLY with DEFAULT options;
        with the brief's S14 applied bench is 242796 / 656517 / 2155620 / perft5 4865609.
        Two independent builds are bit-identical (same sha256).
  K7 portable x86-64-v3 build            PASS (same four pins as the v4 build)
  K8 consecutive digits added, '9' refused  PASS
  K9 triple check accepted, moves right   PASS
  K10 unknown command silent             PASS for plain garbage, but go banana SEARCHES (bestmove a2a3)
  K11 valueless setoption                PASS
  K12 bestmove 0000 on mate/stalemate     PASS
IN PROGRESS: E1 (EOF-trap evidence), then K4/K13 sums with an INTERACTIVE driver, K5 (TSan), K14.
HARNESS DEFECT FOUND IN MY OWN EARLIER WORK: my first drivers piped go..quit, which aborts the search
(seat 19's 19-F12, confirmed by me independently). I am re-running every affected measurement; the
job2/check1-4 results that used perft only are unaffected (perft completes before EOF).
next: finish E1, then push the audit table + re-run log.

## Mon Nov 16 09:36:26 PM UTC 2026  [PARTIAL PUSH: audit table first rows settled]
PUSHED the audit table in partial state as instructed: audit/AUDIT_KNOWN.md (K1,K2,K3,K6,K7,K8,K9,K10,K11,K12
settled; K4,K5,K13,K14 pending, K5 UNTESTABLE as written).
Headline: 10-F6 the honesty pins hold ONLY on DEFAULT options -- with the brief's S14 applied first bench is
242,796/656,517/2,155,620. 10-F7 two independent builds are bit-identical. 10-F8  really searches.
10-C5 CONFIRMS seat 19's 19-F12 (EOF aborts a search and fabricates a bestmove); my V1/V2 evidence pair is in
audit/raw_E1/. I retract nothing that used perft/bench/eval only; the two  measurements that did
use a piped driver are marked INVALID in AUDIT_KNOWN.md and are being re-run with audit/drv.py.
RUNNING NOW: sums.py (K13/K4) in tmux session swarm-sums2, EOF-safe driver.
next: K13 + K4 + K14 rows, then final push by 22:30.

## Mon Nov 16 09:37:44 PM UTC 2026  [CHECKPOINT 22:05]
AUDIT TABLE now settled for K1,K2,K3,K6,K7,K8,K9,K10,K11,K12,K13(O),K14-pending.
Big new results:
  10-F10 the four SUMS are S14-regime numbers: O d12 = 9,500,069 and O d14 = 21,812,100 EXACT (and the
    first three 41,311/24,872/28,574 exact) with S14; default gives 12,573,318 / 29,799,803.
    Together with 10-F6: PINS = default regime, SUMS = S14 regime. One harness cannot use one regime for both.
  10-F11  AFTER  RESETS THE BOARD TO STARTPOS (eval -351 -> +38, perft1 38 -> 20).
    The brief's literal "ucinewgame + isready before every go" therefore measures startpos every time;
    the tell is an identical node count for every position. Correct order: ucinewgame, position, go.
  Method row added for seat 19's parse-before-compare warning; every row now names the line it parsed.
RUNNING: sums.py G d12/d14 both regimes (tmux swarm-sums2); K4 G perft 3 x353 + first 60 at perft 4.
next: G sums + K4 rows, K14 with the correct driver, then final push by 22:30.
