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
  10-F11 ucinewgame sent AFTER position fen RESETS THE BOARD TO STARTPOS (eval -351 -> +38, perft1 38 -> 20).
    The brief's literal "ucinewgame + isready before every go" therefore measures startpos every time;
    the tell is an identical node count for every position. Correct order: ucinewgame, position, go.
  Method row added for seat 19's parse-before-compare warning; every row now names the line it parsed.
RUNNING: sums.py G d12/d14 both regimes (tmux swarm-sums2); K4 G perft 3 x353 + first 60 at perft 4.
next: G sums + K4 rows, K14 with the correct driver, then final push by 22:30.

## Mon Nov 16 09:39:05 PM UTC 2026  [AUDIT COMPLETE]
AUDIT_KNOWN.md is COMPLETE: 12 claims, 9 PASS, 2 refuted/half-refuted (K6 as stated, K14's hash clause),
1 PASS with scope correction (K10), 1 UNTESTABLE (K5 "Threads 2/4 gave 0 reports" -- no TSan two-proof
artifact is cited and I did not build TSan in this window).
All four sums EXACT under S14 (10-F12). K4 PASS 353/353 + 60/60 (10-F13). K14 "no hash entry stored" is
FALSE (21,640 -> 17,847 on repeat).
FINDINGS.md now has 10-F1..F13 and 10-C1..C5.
next: final push at/ before 22:30 with everything; then stop starting new work.

## Mon Nov 16 09:39:53 PM UTC 2026  [FINAL]
Everything pushed. Self-correction recorded: my job2 legality check was produced with a piped driver and
was close to vacuous (it legality-checked fallback moves). RE-RUN with the EOF-safe driver on the same
4,803 pairs: 4,803/4,803 legal, 0 illegal -- the conclusion stands, now on valid evidence (10-C6).
Also added the trap-is-invisible-to-legality-test observation, which is why other seats' "0 illegal
bestmoves" results from piped harnesses cannot be trusted either.
AUDIT_KNOWN.md complete: 12 claims, 9 PASS, 2 refuted/half-refuted, 1 PASS-with-scope, 1 UNTESTABLE.
Branch tip after this commit is the final state.

## Mon Nov 16 09:46:56 PM UTC 2026  [K5 SETTLED + K14 DEEP-DIVE]
K5 is no longer UNTESTABLE: PASS with both proofs on my own builds. nm __tsan_ = 21, planted race counted
(6 reports, exit 66), then 50 positions x Threads 2 and x Threads 4 = 0 reports, 0 null nodes.
RETRACTION RECORDED (10-F16): my first K5 attempt reported proof2=false because my own drv.py sent stderr
to DEVNULL -- "0 reports" was guaranteed, not measured. Same class of error as seat 19's warning, my code.
K14 is a GENUINE DEFECT, not "a smaller tree" (10-F14, 10-F15): restricting to ALL 20/20 legal moves gives
cp 23/d2d4 vs cp 30/e2e4, gap does not close with depth (d16 23 vs 35) or equal work, and a restricted
search corrupts a LATER unrestricted one (36,745 nodes cp 29 vs control 4,951 nodes cp 30), deterministically.
ucinewgame restores cold behaviour, so the pollution lives in the shared table.
next: final push before 22:30, then no new work.

## Mon Nov 16 09:47:41 PM UTC 2026  [DONE — K14 split settled + cross-referenced with seat 27]
TWO defects, settled (10-F17): with `Clear Hash` in a fresh process the restricted score is still cp 23 vs
the cold unrestricted cp 30, and Clear Hash changes not one node (21,640 both ways). So the restricted root
computes wrongly with an EMPTY table; the contamination of later searches is a separate second defect.
A fix must address the restricted root first.
Minimal repro added (10-F18): `searchmoves e2e4` alone gives cp 16/26/23/27 at depth 8/10/12/14 vs
unrestricted 26/24/30/23 -- the SIGN FLIPS with depth and Clear Hash changes nothing. Matches seat 27's
S-F8b unstable sign; the cause is iteration-dependent.
Cross-referenced 10-C7: K14 == seat 27's S-F8/S-F8a/S-F8b, one problem in three angles. My cells reproduce
their numbers exactly (26,329 and 16,770). Pointers: swarm-27 PATCHES.md, REPORT_job5.md, job7/f1_bound_sf8.py.
Nothing left open. Final push done.

## Mon Nov 16 09:50:45 PM UTC 2026  [CORRECTION after seat 27's qualification]
I WITHDRAW the "TWO SEPARATE DEFECTS" answer (10-R2) and the 10-F18 sign-flip table (10-R1).
Cause 1: my "defect A" cell is byte-identical to the cold all-20 cell (21,640 / cp 23 / d2d4), so it IS the
all-20 case, and seat 27's mechanism (extra reduced ply + skipped root store, both intentional) explains it.
Cause 2: at depths 8 and 10 unrestricted plays d2d4, so restricting to e2e4 compared different MOVES.
Still open, as ONE question (10-F19): with IirDepth 20 the score gaps SURVIVE on my build (cp 28 vs 18
single-move; cp 19 vs 18 all-20, bestmove g1f3), matching seat 27's S-F8b third-cause note.
Separate unexplained OBSERVATION (10-F20): later unrestricted searches measure differently depending on what
ran before, and IIR-off does not remove it. Not claimed as a second defect.
next: none. Everything pushed; stopping here.

## Mon Nov 16 09:51:22 PM UTC 2026  [FINAL — 10-F20 control done]
CURRENT STATE block now at the top of the K14 section; the withdrawn claims (10-F14 unsound, 10-F17 two
defects, 10-F18's move-confounded table) are named there so nobody cites them from an earlier commit.
THE CONTROL RESULT (10-F21): two IDENTICAL unrestricted searches in one process differ 56,720 -> 4,951, and
three separate processes give 56,720 three times. So 10-F20 is about PROCESS STATE, not searchmoves.
10-F22: ucinewgame restores cold exactly; Clear Hash gives a THIRD value (40,569, cp 28), deterministically.
10-R3: my own "Clear Hash does not rescue it" step used a control that does not empty the table -- retracted;
the all-20 case is settled by byte-identity to the cold all-20 cell instead.
Named next step recorded: re-run the single-move sweep with ucinewgame before each search, one fresh process
per search, to separate "genuine restriction" from "warm measurement".
STOPPING. Nothing running, everything pushed.

## Mon Nov 16 09:52:14 PM UTC 2026  [FINAL SHAPE]
1. Tie-together sentence added INSIDE the K14 CURRENT STATE block: the residual after a single-move
   restriction may be warm-state rather than the restriction, and the sweep must be re-run with ucinewgame
   or a fresh process before any defect claim. 10-F19 numbers are marked unsettled, not a fault.
2. 10-F21/10-F22 promoted to "METHOD ROW 1" at the TOP of AUDIT_KNOWN.md, above the claim table:
   cold baseline = fresh process or ucinewgame, NEVER Clear Hash; repeated searches in one process are not
   reproducible (56,720 -> 4,951 -> 4,516 vs 56,720 x3 across processes); Clear Hash gives 40,569 / cp 28.
Also cleaned the trail so no reader meets a withdrawn claim first: the primary K14 table row, the old
"genuine DEFECT" section heading and the "Settled — TWO" subsection heading are all marked superseded and
point at CURRENT STATE; Totals rewritten to the post-correction verdicts (nothing UNTESTABLE).
STOPPING. Nothing running, everything pushed.

## 2026-11-16T22:19:16Z CONTINUE: 12 more hours, ends at 2026-11-17T10:19:16Z
Seat 10 kept, branch for-fable-and-opus/swarm-10, folder forge-combo29/swarm/10.
next command: git fetch -q --depth 1 origin handoff/fable-opus-combo29-all-20261114 && git ls-tree -r --name-only FETCH_HEAD forge-combo29/soak_all/ | grep FABLE_TO_swarm

## Mon Nov 16 10:20:48 PM UTC 2026
PC BUILD (file 5) BUILT AND VERIFIED. Patch sha256 d6bd72c531f785f4... matches; 11 files, no fuzz;
built with -DFORGE_MATE_ALPHA_GUARD=1. ALL THREE known-answer rows MATCH to the digit:
  none 312866/862329/3024920/4865609, S14 242796/656517, PC20 278024/587276.
All 42 S14+PC20 option names present in the exe's uci list (92 listed), 0 bad lines. See pc/PC_BUILD.txt.
Read FABLE_TO_swarm 1..5 in full. THREAD RULE audited against my own history: every score is Threads 1
(1149 recorded "Threads value 1"; the non-1 values are K2's out-of-range probes and the job2 fuzz grammar;
k14.py/clean56_fixed.py send none and both builds default to 1). No score of mine needs retracting.
next: re-run my own finds on the PC build under PC20 (K14/K21 family first) and say build+settings per line.
