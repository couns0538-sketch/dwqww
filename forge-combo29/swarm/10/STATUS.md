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

## Mon Nov 16 10:27:45 PM UTC 2026
PC-BUILD RECHECK of my finds under PC20 (Threads 1) vs base under S14 — most SURVIVE:
  10-F11 ucinewgame-after-position reset : STILL PRESENT on PC20 (eval -351 -> +38, perft1 37 -> 20)
  10-F21 repeated searches not reproducible: STILL PRESENT (21600 -> 5161)
  10-F22 ucinewgame restores cold, Clear Hash does NOT: STILL PRESENT (21600 | 21600 vs 24708)
  K1 illegal-prefix perft1=29: holds on PC20.  K2 Hash 0 message: holds on PC20.  K12 0000 on mate/stalemate: holds.
  10-F14 searchmoves-to-all-20 changes the score: STILL PRESENT, and the SIGN IS NOW POSITIVE
         (PC20 unrestricted cp 25/d2d4 vs restricted cp 29/d2d4; base was cp 30/e2e4 vs cp 23/d2d4).
  10-F19 gap with IIR off: survives on PC20.
NEW RETRACTION 10-R4: 10-F8 (go banana -> bestmove a2a3) was an EOF-abort artefact. Held open, go banana
  starts an UNLIMITED search on BOTH builds (24/22 info depth lines) and never answers without a stop command.
  What survives: garbage go lines are NOT ignored, they hang a harness. pc/raw3/go_banana.json
next: write pc/REPORT_pc_recheck.md with the full both-build table, then continue the cycle.

## Mon Nov 16 10:28:05 PM UTC 2026
REPORT_pc_recheck.md written: full both-build table for every find of mine.
New on the PC build (PC r15, PC20, Threads 1): 10-F23 warm-state defect present (21600 -> 5161);
10-F24 Clear Hash above cold on PC20 (24708 vs 21600, direction reversed from base); 10-F25 10-F14 SIGN
REVERSED (unrestricted cp25 vs restricted cp29); 10-F26 10-F11 and 10-F22 both still present.
All three PC honesty rows match file 5 exactly. next: probe the PC's FORGE_FIX_ROOT_DRAWN directly
(third-occurrence repetition root), which I flagged as the obvious next check.

## Mon Nov 16 10:28:18 PM UTC 2026
DRAWN-ROOT PROBE (the one thing file 3 says really differs). CONFIRMED with a direct test:
  third occurrence by move list : base 0 nodes / bestmove a2a3  |  PC r15 13,424 nodes / d2d4
  halfmove clock 100 via FEN    : base 0 nodes / bestmove a2a3  |  PC r15 11,542 nodes / d2d4
  second occurrence  (control)  : base 9,575 | PC 8,569   (searched on both, as file 3 says)
  halfmove 0         (control)  : base 9,575 | PC 8,569   (searched on both)
  K vs K insufficient material  : BOTH 0 nodes / h1g1        (file 3: still answered at once)
"a2a3" on the base tree is the first legal move, not a search result. 10-F27. pc/raw4/drawn_root.json
next: continue the cycle -- check other seats' newest unconfirmed finds (file 2 named 19-F1..F5, 29-F1..F2).

## Mon Nov 16 10:29:27 PM UTC 2026
INDEPENDENT PROFILE of the base build with gprof (perf is UNUSABLE here: no linux-tools for kernel
6.12.113+, that is method note 10-N1). 4.5 s of samples, 4x bench 16, Threads 1, Hash 16:
  evaluate_position<false> 21.24 % self  (#1)   nnue apply_and_evaluate 13.94 + update 3.32 = 17.26 %
  see_ge 6.86 % vs all fill_pseudo_legal 5.53 %    MovePicker::next 6.42 + pick_best 5.75 + evasions 1.11
CONFIRMS the ORDER (not the percentages) of 19-F1/29-F2 (10-C8), 19-F4 (10-C9) and 19-F3 (10-C10).
gprof inflates small functions, so absolute shares are not comparable to perf; only rank is.
next: file 2's rule 2 says only NON-evaluation work can help the owner's PC -- record that in the audit and
then continue the cycle.

## Mon Nov 16 10:29:53 PM UTC 2026
FILE 2 RULE 2 PINNED with its exact scope (10-C11). The rule "evaluation cost is worth nothing on the PC"
holds ONLY when the PC has loaded its own v3 net: nnue_v3.hpp:158 active() = requested && loaded(), and
search.cpp:1184 branches to static_evaluate_v3 only then. With NO net (our situation -- the net is not
shared) the PC build still spends 21.51 % self in evaluate_position, i.e. identical to the base tree's 21.24 %.
So: evaluation is worthless on the OWNER'S PC, first-class on OUR builds. Neither statement generalises.
next: cycle -- look for the newest unconfirmed find that I can actually test with both builds.

## Mon Nov 16 10:30:34 PM UTC 2026
CHECK of seat 30's 30-F22 -> CONFIRMS (10-C12), 6 of 6 predictions held, both builds, Threads 1.
  FEN 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1
  FINISHED search : bestmove a1a8, score mate 1 (12 info lines)   <- the only mate in 1
  stdin closed    : bestmove f2f3, no score, 0 info lines         <- fabricated, LEGAL, strictly worse
A legality checker cannot catch this (f2f3 is legal) and a score check cannot either (there is no score).
10-F28: sending quit as a word does the same as EOF, so only "read to bestmove, send nothing" is safe.
next: continue the cycle.

## Mon Nov 16 10:30:55 PM UTC 2026
CHECK of seat 30's 30-F23 -> phenomenon CONFIRMED, numbers differ (10-C13). Three regimes (10-F29):
  <=20 ms : 0 info lines, bestmove a2a3, NO score    (finished search is d2d4 cp 24) -- loudly wrong
  30 ms   : d2d4, cp 18                               -- SILENTLY wrong, 6 cp off, looks finished
  >=40 ms : d2d4, cp 24                               -- identical to finished
Seat 30 measured 6-11 info lines at 1-20 ms; I measure 0, and the intermediate band at 30 ms. Machine
specific, so I record both rather than overwriting theirs.
next: continue the cycle.

## Mon Nov 16 10:31:31 PM UTC 2026
MIDDLE REGIME MAPPED (10-F30, 10-F31, 10-F32), 4 positions x 11 delays x 2 builds, Threads 1, depth 12:
  worst score error is base **53 cp** (not the 6 cp I first reported) and PC 30 cp.
  boundary (largest delay that still differs from finished) is POSITION DEPENDENT: 30-50 ms; 50 ms on G_black_mid.
  <=25 ms: 0 info lines, fabricated move, no score. Middle band: real move, wrong score, looks normal.
  ALL THREE REGIMES ARE ON THE BASE BUILD TOO -> the owner's training loop IS exposed if anything interrupts.
10-N2: named the control-failure pattern (a control that passes for the wrong reason), covering
  10-R3, 10-R4, 10-C5 and 10-F16.
next: continue the cycle.

## Mon Nov 16 10:32:27 PM UTC 2026
THE MIDDLE BAND IS DETECTABLE (10-F33, 10-F34, 10-F35) — this is the actionable answer:
  RULE R1: a record is UNFINISHED iff its LAST info depth < the requested depth.
  Measured 4 positions x 2 builds x 7 delays x 2 reps at depth 12: 90 genuinely truncated records,
  R1 caught ALL 90, with 0 false alarms on the 19 records identical to a finished search.
  The 19 that reached depth 12 were NOT truncations -- the search had finished before the quit landed
  (identical nodes/pv/score), so there is no undetectable middle band.
  Checker committed: regimes/is_unfinished.py FILE --requested-depth N  (exit 1 if any unfinished).
  It also flags "bestmove with ZERO info lines" (the <=20 ms regime, invisible to the depth test).
  Without a recorded requested depth: R2 "depth < file max" works if the file has >=1 completed search.
  Measured dead ends: a bestmove line (109/112 truncated records have one), pv length, nodes==0.
next: continue the cycle.

## Mon Nov 16 10:33:45 PM UTC 2026
WHEN-IT-MATTERS JOB DONE (10-F36..F39):
  checker run over the WHOLE REPOSITORY: 3,192 files, 8,672 records, **0 unfinished in the repo's own data**
  (2,932 non-mine files / 8,410 records / 0 flagged). The 257 flags are all in ONE place: my own DISCARDED
  first sums run, which the checker re-detected independently -- a good sign for the rule.
  585 of 2,932 non-mine files have no recorded requested depth, so R1 is inapplicable there (R2 covers them
  when the file holds at least one completed search).
  Corrected sums run re-verified clean: 0 null nodes, four totals still exact (10-F37).
  ONE-PAGE RULE for a person: regimes/rule-r1-unfinished-searches.md (10-F38).
  "64 info lines" CORRECTION kept prominent (10-F39): the count is the requested depth capped at 64
  (depth 5 -> 5 lines, depth 64 and 70 -> 64), never a constant. Seat 25's mechanism stands, its number was the cap.
next: cycle.

## Mon Nov 16 10:35:33 PM UTC 2026
THE 585-FILE GAP CLOSED AS A MEASUREMENT (10-F40, 10-R5, 10-F41):
  of 17,085 recorded searches in the repository: 8,672 judgeable -> 0 unfinished in the owner's data;
  8,413 unjudgeable -> 3 files using go nodes/softnodes (8,292 records) + 585 files with no go echo (121).
  R2 flags 8,235 of the 8,292 node-budget records -- a 99 % false-alarm rate, i.e. an INVALID reference.
  QUALIFIES 10-F35: R2 is only sound when the file's searches share a DEPTH TARGET; I stated it too broadly.
  The 41 inspectable gap flags are ALL legitimate (clock searches stopping at varying depths by design).
  What a parser needs: log the go line, or record the node/time budget for non-depth searches.
next: continue confirming other seats' findings (area 10's remaining work).

## Mon Nov 16 10:35:46 PM UTC 2026
CHECK of seat 07's 07-F1 -> CONFIRMS (10-C15), 6/6 predictions. searchmoves a1a1 (or searchmoves with
no move) on startpos: 8 info depth lines, all nodes 0, all cp 0, then bestmove 0000 -- on base S14 AND PC20,
while python-chess confirms startpos has 20 legal moves. Control (searchmoves e2e4) does a real search.
GUARD FOUND (10-F42): the engine prints 'info string searchmoves restriction has no legal root
moves' on both builds, so a consumer can detect the false-0000 without parsing scores.
next: continue confirming other seats' findings.

## Mon Nov 16 10:36:11 PM UTC 2026
SCOPE GUARD (10-F43): rule-r1-unfinished-searches.md now opens with a "Scope of each rule" paragraph --
R1 unconditional; R2 requires a DEPTH TARGET in every search of the file; node/clock/softnode files need the
budget recorded instead -- and is_unfinished.py now ENFORCES it: on the repo's go-nodes file the old behaviour
flagged 8,235/8,292 records, the guarded version reports 0 unfinished and 8,292 UNKNOWN with the reason.
next: confirm the two live PC defects (fifty-move score band; MultiPV with large Hash collapse).

## Mon Nov 16 10:37:23 PM UTC 2026
TWO CHECKS, both CONFIRMS:
  10-C16 seat 20's S-F16: same board, depth 10 -- cp 0 at hm 91 with 13,791,896 nodes + 6-move pv (HORIZON)
    vs cp 0 at hm 100 with 0 nodes + empty pv (ROOT). Factor ~14 million in nodes, so a score-only checker
    cannot separate them (10-F45). Corrections: horizon starts at hm 91 on this board; at hm 100 the PC build
    gives 200 nodes/1-ply pv where base gives 0/empty (PC root repair, agrees with seats 08 and 20).
  10-C17 seat 02's S-F7c: MultiPV 1 safe at every Hash (depth 18-19); at MultiPV 8 the depth falls
    MONOTONICALLY in Hash: 16->12, 64->12/11, 256->2, 2048->1. Stricter edge: at H2048 MultiPV 2 is already
    broken. 10-F44: monotone in Hash = per-line cost proportional to table size (the tt.clear walk).
next: continue the cycle.

## Mon Nov 16 10:38:04 PM UTC 2026
cp0 CLASSIFICATION, and I caught my own bad threshold before it spread (10-F46, 10-R6):
  I first wrote "cp 0 with nodes > ~10,000 = horizon". MEASURED WRONG: across four bare endgames the horizon's
  cp 0 records carry only 200/230/280/541/629/793 nodes with 1-2 move pvs; a 10,000-node cut misclassifies
  6 of 6. The correct discriminator is the PV: EMPTY pv + 0 nodes = ROOT SHORTCUT; NON-EMPTY pv = HORIZON at
  any node count. Rule file corrected with the wrong threshold kept as a worked counter-example.
  Classifier committed: regimes/classify_cp0.py (6 horizon / 4 root on the evidence, 0 ambiguous).
next: continue confirmations.

## Mon Nov 16 10:38:35 PM UTC 2026
CAPSTONE (10-F47): regimes/measurement-rules-a-future-swarm-must-apply.md — 13 measurement rules, one line
each with the case that taught it, most of them from my own retractions (10-R1..R6). Every number in it was
re-read from the raw files before writing: U2 [56720, 4951]; PC20 clearhash 24708 vs cold 21600; horizon cp0
node counts [200,230,280,541,629,793]. Ends with the three sentences to carry forward.
next: continue confirmations until the window closes at 10:19 UTC.

## Mon Nov 16 10:39:23 PM UTC 2026
CAPSTONE STRENGTHENED (10-F48): the three thinnest rules each now carry a "go straight to the raw data" line.
  rule 2 Threads 1 -> seat 04's job1/table_threads.md (T1 79,980 nodes x10 vs T4 up to 1.25e9) + 04-F9
  rule 5 control must fail -> my two K5 summaries side by side (proof2 false vs 6 reports exit 66)
  rule 12 rule holds in its configuration -> two gprof flats 21.24 % vs 21.51 % + nnue_v3.hpp:158
All six cited paths verified to exist (including the cross-branch one) before pushing.
next: third confirmation of the MultiPV x Hash collapse (the one with only two); fifty-move already has many.

## Mon Nov 16 10:40:47 PM UTC 2026
READ FABLE_TO_swarm_6. It changes two verdicts that touch my record: a cp 0 draw at a high counter is NOT a
defect (the match program ends the game at the 3rd occurrence / 100th half-move), so my fifty-move and K14
work is DOCUMENTATION not a defect claim; and score spread above Threads 1 is NOT a defect (shared-hash
MT design). I will annotate those findings accordingly.
NEW AREA DONE — go softnodes N (the owner's self-play command), 10-F49..F51:
  SOUND: deterministic 16/16 cells (80 searches), every cell ends on a FINISHED depth, overshoot 1.00-2.06x N
  and never under, monotone in N. go nodes stops under budget one depth earlier; softnodes one depth further.
  CAVEAT (10-F51): bestmove changes with N (startpos d2d4 at N<=50000, e2e4 at N=250000), so mixing N values
  in a training set mixes two different players.
next: annotate the two reframed findings, then continue.

## ANNOTATIONS after file 6
ANNOTATED the two reframed findings (10-A1, 10-A2), NOT retracted:
  fifty-move / cp 0 work is DOCUMENTATION under file 6 (the match program ends the game), still an accurate
  description of HOW the engine reports those positions; the one surviving defect form is the narrow
  forced-mate inequality 2N-1 <= 100-counter, which I have NOT tested and say so.
  "Threads 1 for every score" stands as measurement discipline; the spread itself is not a bug.
Mon Nov 16 10:40:57 PM UTC 2026
Mon Nov 16 10:41:05 PM UTC 2026

## MultiPV third confirmation
10-C18: THIRD confirmation of 02-F7c on an independent measure (NODES in a 3 s clock): at MultiPV 8,
H16 = 1,109,211 nodes vs H2048 = 133 -> 8,339.9x collapse; at MultiPV 1 only 1.3x. Correction: NOT monotone
in Hash (H=256 = 882,366 > H=64 = 336,805), so it is a cliff between 256 and 2048 MB.
10-F52: mechanism MEASURED -- one Clear Hash costs 0.0085/0.0297/0.1104/**0.8621** s at Hash 16/64/256/2048,
paid once per extra PV line: ~6 s of clearing inside a 3 s budget at MultiPV 8. That is the whole effect.

## Budget-change number (the owner's training-data question)
10-F53: 100 G positions x 3 owner budgets, PC20 Threads 1: **19/100 change bestmove**, 17/100 between
20000 and 250000, 8/100 between 50000 and 250000, all three agree on 81/100. Median cross-budget score gap
52 cp (max 218); same-budget median gap 34 cp (max 279); **2 positions where the small budget's choice is
>=200 cp worse by the engine's own evaluation**. 0 illegal moves in 300 searches.
10-F54: record the budget with the data and never mix budgets; or filter to the 81% that agree; 50000 is the
cheapest single safe budget (92/100 agreement with 250000).
Mon Nov 16 10:42:12 PM UTC 2026

## Worst cases + rule 14
10-F55: the two >=200 cp budget cases share a SCORING property, not a position one -- shallow OPTIMISM about
its own move: i=12 calls b6e6 +222 while a deep search of b6e6 gives +85 (137 too hopeful); i=99 calls b5b6
-1665 while a deep search gives -2100 (435 too hopeful). The two largest optimisms in the set.
Different in position type, depth, node count and second-move closeness.
10-F56: honesty limit -- optimism picks the extremes but Spearman rank correlation with real damage is only
0.27, so it is NOT a usable predictor of which positions hurt.
10-F57: the bad move is undetectable from the record (legal move, normal-looking score) -> DISCIPLINE not a
filter. Rule 14 added to the capstone page with the one-line operational rule.
Mon Nov 16 10:42:49 PM UTC 2026

## Surviving defect form tested
10-F58: EMPTY in my sample. Three boards with exhaustively-verified forced mates (1/3/4 moves), PC20 Threads 1,
depth 22, counters 0..99: every case where 2N-1 <= 100-counter the engine reports the MATE; every case where
it does not fit reports cp 0 (correct per file 6). 10-F59 records my P5 prediction FAILING -- I expected a
mate claimed too far away and found none. 10-N3 states the scope: 3 boards, 9 counters, constructed
positions -- a real-game boundary test is still open.
Mon Nov 16 10:45:22 PM UTC 2026

## Caught my own bad-FEN error before publishing (10-R7, 10-F60)
My first hidden-mate run was measuring STARTPOS: the K+Q FENs I built are illegal
(`invalid FEN: side that moved left its king in check`), so the engine kept the previous position and every
row showed a startpos move (e2e4 on a board with no pawns -- the tell). Fixed with legal FENs plus a mandatory
assertion that BOTH python-chess accepts the FEN and the engine does not print `invalid FEN`; the harness now
aborts instead of recording. check11's three boards were separately verified legal, so 10-F58 stands.
Mon Nov 16 11:02:55 PM UTC 2026
