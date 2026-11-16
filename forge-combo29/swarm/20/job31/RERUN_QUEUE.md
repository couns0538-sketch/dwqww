> **STATUS NOTE (seat 20, S-F41) — read before using this list.** Entry 1 (seat 30's 30-C4) has now been
> **CONFIRMED at Threads 1** by me (S-C17, `job33/CHECK_30C4.md`): every number of theirs reproduces exactly on
> both builds. **And that line was a FALSE POSITIVE of my audit** — it does state "Threads 1/S14" and
> "Threads 1/PC20"; my pattern missed the "Threads 1/S14" form. So treat this list as *"lines whose wording does
> not make the thread count obvious"*, not as *"lines that are defective"*, and check the line itself before
> re-running. The method (state count + build, re-run at Threads 1) is what matters.

# RE-RUN QUEUE — findings that report a score without stating Threads 1

Owner-requested, built by seat 20 (`job27/thread_audit.py`, `job31/build_queue.py`, `job31/build_queue2.py`).

**Swarm rule (22:19Z):** a score must be from Threads 1 unless the job is about threading. Seat 04
measured the PC build at Threads 4 on one position and got four distinct scores (+2576, mate 13,
mate 18, mate 16; nodes 5.0M–31.4M), while Threads 1 gave +2207 four times with identical nodes 75,311.

**These lines are not wrong.** They are *unconfirmable as written*: nobody can reproduce a score without
knowing the thread count, and a confirmation must use the same build AND the same settings as the find.
A re-runner should send `setoption name Threads value 1`, state it in the confirmation line, and name the
build (`base 6b98f217` or `PC r15`) and the settings (`none`, `S14`, `PC20`).

**Total flagged: 122 lines across 16 seats.**

## The short list — 8 lines worth re-running first, with the reason

Hand-picked, because nobody can re-run 120. Each is a score claim whose answer changes either a repair
decision or a currently-**live** finding. Chosen on consequence, not on suspicion.

### 1. seat 30 — 30-F19

**Why:** The only line in the queue already measured on the PC r15 build. If its score holds at Threads 1 it is the first third-party confirmation of PC-build behaviour; if it does not, every 'on the PC build' claim needs a thread count before it is quoted.

**How to re-run:** PC r15 exe, PC20, Threads 1 explicit, the line's `quiet_hm100` board, `go depth 10`, 5 fresh runs

### 2. seat 25 — S-F1 / S-F2

**Why:** The mate-distance claim that first exposed this whole area, and the one my own S-F22 independently proved (true distance 8 plies). A Threads-1 re-run on their board either reproduces `mate -12` (making it a solid independent confirmation of the depth-limited miss) or does not.

**How to re-run:** base exe, S14, Threads 1 explicit, `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1`, `go depth 12`, 5 fresh runs

### 3. seat 28 — S-F4

**Why:** The repetition door — the one door seat 01's patch leaves open on the base tree. I confirmed it (S-C4) at Threads 1, but a second confirmation from a seat that states Threads 1 would close it properly.

**How to re-run:** base exe, S14 or none (state it), Threads 1 explicit, their third-occurrence board, `go depth 6`

### 4. seat 21 — 21-F9

**Why:** The halfmove >= 100 sweep (100, 150, 9999, 65536, up to 2147483648). The sweep is the kind of claim whose SCORES are the whole content, so a thread count decides whether it is evidence or noise.

**How to re-run:** base exe, their settings, Threads 1 explicit, the counters they list, `go depth 5`

### 5. seat 21 — 21-F11

**Why:** `mate 0` on a checkmated root. A one-position claim with a decisive answer — cheap to re-run, and if it holds at Threads 1 nobody needs to look at it again.

**How to re-run:** base exe, Threads 1 explicit, `4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60`, `go depth 1`, 3 fresh runs

### 6. seat 27 — S-F8 / S-F8a / S-F8b / S-F8c

**Why:** A four-part chain about `searchmoves` changing the SCORE, with a bounded-but-unsolved conclusion. Four score claims in a chain: if any of them was measured above Threads 1 the chain needs rebuilding, and the chain is what seat 10's and seat 12's findings are being separated with.

**How to re-run:** base exe, their builds (build-release / build-sm / build-sm2 named in their files), Threads 1 explicit, startpos and their 20 positions, `go depth 12` and the depths they name

### 7. seat 01 — S-F19 / S-F22 / S-F23

**Why:** The seat that produced the patch everyone else is testing has a three-line correction chain about a halfmove-100 board whose mate is 3 plies away, and whether it is discriminating. Threads 1 must be stated before any patch recommendation rests on it.

**How to re-run:** unpatched base exe, S14, Threads 1 explicit, `8/8/8/8/2K4Q/8/8/1k6 w - - 100 1` and `8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1`, `go depth 5`

### 8. seat 28 — S-F21 / S-F19

**Why:** One of THREE competing drawn-root fixes exists in this seat's folder (they say only one may be applied). The regression numbers that justify choosing between them are scores; a thread count decides if they mean anything.

**How to re-run:** base exe patched and unpatched, S14, Threads 1 explicit, the boards their lines name, `go depth 5..6`

## The full queue, grouped by seat

### seat 01 — 17 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| S-F5 | UNSTATED (no thread count) | `(not named in the line)` | 1 / With `halfmove >= 100` in the FEN the engine adjudicates the root as a draw and searches 0 nodes, so a mate-in-one is MISSED (`bestmove f2f3`, `sc |
| S-F6 | UNSTATED (no thread count) | `(not named in the line)` | 1 / The shortcut is not blind to checkmate: an already-mated board reports `bestmove 0000` / `score mate 0` at halfmove 0, 98, 99, 100, 101 and 150, s |
| S-C2 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS S-F3 (seat 05) on its numbers, REFUTES its "applied about 9 plies early" framing / checks/CHECK_s05f3.md, raw checks/s05f3/check_s05f3.txt an |
| S-F16 | UNSTATED (no thread count) | `(not named in the line)` | 1 / The fifty-move patch (S-F7) is REGRESSION-TESTED, closing the "cost not measured" caveat: on four genuine-draw boards at halfmove 100/150 the patc |
| S-F17 | UNSTATED (no thread count) | `(not named in the line)` | 1 / S-F5 fires in REAL GAME PLAY, not only in `go depth`: with the brief's S14 settings applied (`setoption` + `isready` before every search) the mate |
| S-C3 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS S-F1 (seat 17): the OBSERVABLE only / checks/CHECK_2640_RESOLVED.md, raw checks/s17f1/check_s17f1.txt (again: `python3 checks/check_s17f1.py  |
| S-F18 | UNSTATED (no thread count) | `(not named in the line)` | 1 / The conservative variant of the fix (keep the shortcut only when the side to move has no non-pawn material) is regression-tested and equal to the  |
| S-F19 | UNSTATED (no thread count) | `8/8/8/8/2K4Q/8/8/1k6 w - - 100 1` | 1 / A limit that applies to EVERY root fix proposed so far: on a halfmove-100 board whose mate is 3 plies away (`8/8/8/8/2K4Q/8/8/1k6 w - - 100 1`) my |
| S-F22 | UNSTATED (no thread count) | `8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1` | 1 / **CORRECTION of my own S-F19.** On a halfmove-100 board whose forced mate is 3 plies away AND whose first mating move is a PAWN move (so the fifty |
| S-F23 | UNSTATED (no thread count) | `8/8/8/8/2K4Q/8/8/1k6 w - - 100 1` | 1 / **S-F19's board was not discriminating and its conclusion was wrong.** On `8/8/8/8/2K4Q/8/8/1k6 w - - 100 1` every White mating move is QUIET, so  |
| S-F24 | UNSTATED (no thread count) | `(not named in the line)` | 1 / The clock path does NOT lose the counter-resetting mate differently from the depth path: on the discriminating board at halfmove 100 the unpatched |
| S-F25 | UNSTATED (no thread count) | `(not named in the line)` | 1 / My attempt to test seat 12's claimed repetition advantage MEASURED NOTHING and I am not claiming a result: the setup put a knight shuffle after a  |
| S-F26 | UNSTATED (no thread count) | `(not named in the line)` | 1 / **THE DECIDING TEST: my patch does NOT fix the repetition door, so the two patches are COMPLEMENTARY, not ranked.** On seat 12's own case (board ` |
| S-F28 | UNSTATED (no thread count) | `(not named in the line)` | 1 / Seat 21's verification of seat 12's repetition door is CONFIRMED from the other side: on seat 12's case the patched build answers `mate 1` in 108  |
| S-F29 | UNSTATED (no thread count) | `(not named in the line)` | 1 / A COMBINED root fix (my reset-aware fifty-move test + seat 12's immediate-mate bypass for the repetition and dead-material doors) closes ALL FOUR  |
| S-F31 | UNSTATED (no thread count) | `(not named in the line)` | 1 / The combined patch's immediate-mate bypass is REDUNDANT on the fifty-move door and has been removed there: a scoped build whose bypass guards ONLY |
| S-F32 | UNSTATED (no thread count) | `4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60` | 1 / **Seat 21's FOURTH door, reproduced by me and NOT closed by any patch in this folder:** a checkmated root answers `info depth N ... score mate 0 . |

### seat 20 — 17 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| S-C1 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS S-F5 (seat 01) / forge-combo29/swarm/20/job1/CHECK_s01F5.md, raw job1/check_s01f5.txt + job1/check_s01f5.json (again: `python3 forge-combo29/ |
| S-F7 | UNSTATED (no thread count) | `6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 100 60` | area 10 / A correction to MY OWN S-C1 wording: the drawn-root shortcut is not silent — it emits `info depth 1..max_depth seldepth 1 score cp 0 nodes 0 |
| S-C4 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS S-F4 (seat 28) / forge-combo29/swarm/20/job7/CHECK_s28F4.md, raw job7/check_s28f4_base.json + job7/check_s28f4_patched.json (again: `python3  |
| S-F13 | UNSTATED (no thread count) | `(not named in the line)` | area 10 / seat 01's patch (remove `halfmove_clock() >= 100` from `root_drawn`) is NECESSARY BUT NOT SUFFICIENT: applied to a scratch copy with `patch  |
| S-C8 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS S-F3 (seat 05) / forge-combo29/swarm/20/job11/CHECK_s05F3.md, raw job11/out_check.txt + job11/check_s05f3.json (again: `python3 forge-combo29 |
| S-F16 | UNSTATED (no thread count) | `(not named in the line)` | area 10 / Two different mechanisms produce "cp 0" and must not be confused: the root shortcut fires at exactly halfmove 100 with 0 NODES and an EMPTY  |
| S-C9 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS S-F1 (seat 05) and S-F1 (seat 25) / forge-combo29/swarm/20/job12/CHECK_s05F1_s25F1.md, raw job12/out_check_s14.txt + job12/check_mate_pv_s14. |
| S-F17 | UNSTATED (no thread count) | `(not named in the line)` | area 10 / The mate-distance instability is tuning-dependent, not general: DEFAULT settings converge consistently (depth 16 proves mate -4 = 8 plies wi |
| S-F18 | UNSTATED (no thread count) | `(not named in the line)` | area 10 / The S14 mate-distance error is NOT any single option and not any pair: tested alone on the job12 board at depth 12, only THREE of the fourte |
| S-F19 | UNSTATED (no thread count) | `(not named in the line)` | area 10 / `setoption name LmpBase value 8` ALONE (default 4) turns a mate-in-14 position into `cp -3114` at depth 12, losing the mate score entirely - |
| S-F20 | UNSTATED (no thread count) | `(not named in the line)` | area 10 / The `LmpBase=8` mate loss is a DELAY, not breakage, and it is narrow: on a mate-in-1 board LmpBase=8 changes nothing at depths 8-14 (mate 1, |
| S-F21 | UNSTATED (no thread count) | `(not named in the line)` | area 10 / WITHDRAWN — see job15/WITHDRAWN_s21.md. I wrongly claimed the engine misses a mate in 3 on 6k1/6pp/8/8/8/8/5PPP/R5K1 w. There is NO forced m |
| S-F22 | UNSTATED (no thread count) | `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1` | area 10 / On 8/8/1p6/8/p3p3/8/2Kpk3/8 w the TRUE forced mate distance is exactly 8 plies (mate -4), proved both ways with my own exact predicate (True |
| S-C11 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS S-F1 (seat 17) / forge-combo29/swarm/20/job18/CHECK_s17F1.md, raw job18/check_s17f1.json (again: `python3 forge-combo29/swarm/20/job18/check_ |
| S-C13 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS S-F6 (seat 06), rate NOT reproduced / forge-combo29/swarm/20/job19/CHECK_s06F6.md, raw job19/check_s06f6.json (again: `python3 forge-combo29/ |
| S-F27 | UNSTATED (no thread count) | `(not named in the line)` | area 10 / Limitation of the UCI protocol for the whole swarm, measured: on a lone-king position all 3 legal moves score `cp 0` and the engine returns  |
| S-F34a | UNSTATED (no thread count) | `(not named in the line)` | area 10 / CORRECTION to my own S-F34: "the mate-distance defect is FIXED on the PC build" was too broad. Measured precisely: with PC20 (which includes |

### seat 05 — 13 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| S-F1 | UNSTATED (no thread count) | `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1` | 5 / At depth 12 on G/192 the engine reports `score mate -12` (a promise of mate in 24 plies) but its own PV is 18 plies and does not end in checkmate; |
| S-C1 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS S-F9 (seat 06) / check_s06f9/RESULT.md, raw check_s06f9/raw/check_s06f9.txt + raw/pv_arithmetic.txt (again: `python3 check_s06f9/check_s06f9. |
| S-F3 | UNSTATED (no thread count) | `1K6/8/8/3R4/8/8/8/k7 w - - 0 1` | 5 / The fifty-move draw is applied about 9 plies early: `1K6/8/8/3R4/8/8/8/k7 w - - H 1` at `go depth 10` scores `cp 472` for H=0..75, `cp 314` at H=9 |
| S-F4 | UNSTATED (no thread count) | `(not named in the line)` | 5 / The same 20 K+Q/K+R-versus-lone-king boards score +470..+1259 cp at halfmove 0 but exactly `cp 0` in all 20 at halfmove 98 and all 20 at 99, so th |
| S-F5 | UNSTATED (no thread count) | `(not named in the line)` | 5 / Repetition detection is correct: 20 genuine 3-fold positions reached only by `position startpos moves` all answer `cp 0` with 0 nodes and an empty |
| S-F6 | UNSTATED (no thread count) | `(not named in the line)` | 5 / Draw-score baseline at depth 10: K v K, KN v K and KB v K are `cp 0` with 0 nodes in 20/20 each, KNN v K is non-zero `cp` (159..354) in 20/20 with |
| S-F9 | UNSTATED (no thread count) | `(not named in the line)` | 5 / The S-F1 truncation is a GENERAL behaviour, not a G/192 curiosity: on a brand-new 200-position set (R, seed 511, random play, never searched befor |
| S-F11 | UNSTATED (no thread count) | `1K6/8/8/3R4/8/8/8/k7 w - - 0 1` | 5 / **CORRECTED — see S-F14.** On the bare endgames I tested (K+R, K+Q) the lowest counter scoring cp 0 tracks `counter + search_depth` at 100-101 (d6 |
| S-C5 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS 15-F3 (seat 15) / check_15f3/RESULT.md, raw check_15f3/raw/check_15f3.txt (again: `python3 check_15f3/check_15f3.py /tmp/build-rel/forge`) /  |
| S-F12 | UNSTATED (no thread count) | `(not named in the line)` | 5 / `DeadMaterial true` is a pure material key for EXACTLY two knights and is correct about three: 8 of 8 KNNk positions across eight different placem |
| S-C6 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS 15-F4 (seat 15) / check_15f4/RESULT.md, raw check_15f4/raw/check_15f4.txt, plus my own exposure audit job2/out/empty_pv_audit_job2.txt + job1 |
| S-F14 | UNSTATED (no thread count) | `(not named in the line)` | 5 / The fifty-move boundary is POSITION-dependent, not one rule: three bare endgames (K+R, K+Q, K+B+B vs K) drop to cp 0 at counter+depth ~100-101 (bo |
| S-C8 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS 15-F5 (seat 15) / job3b/out_asan_b/table.txt, job3b/out_predictions.txt, job3/out_answer_summary.txt (my own harness `job3b/run_job3b.py`, fr |

### seat 15 — 11 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| 15-F1 | UNSTATED (no thread count) | `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1` | 5 / Search reports `score mate -12` at depth 12 S14 on 8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1 where the true distance is mate in 8 plies (mate -4); its PV |
| 15-F2 | UNSTATED (no thread count) | `(not named in the line)` | 5 / In 553 positions at depth 12 S14, 9 of 10 mate scores obey the brief's PV-length rule and 1 violates it (idx 392, mate -12 with an 18-ply PV); no  |
| 15-F3 | UNSTATED (no thread count) | `(not named in the line)` | 5 / With S14 (DeadMaterial off) the engine scores KNN v K as a win — 19 of 20 such positions at depth 10 report cp 147…309 — although KNN v K cannot b |
| 15-F4 | UNSTATED (no thread count) | `(not named in the line)` | 5 / K v K, KN v K, KB v K and threefold-repetition roots all score exactly cp 0 at depth 10 S14, but they answer with an EMPTY PV (`... time 0 pv`) an |
| 15-F5 | UNSTATED (no thread count) | `(not named in the line)` | 5 / A terminal root (checkmate or stalemate) is reported as `score mate 0` (checkmate) or `cp 0` (stalemate) with `nodes 0`, and the engine walks the  |
| 15-C2 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS 07-F1 / check_s07f1/check_s07f1_release.txt / a root with no legal move answers `info depth N ... score cp 0 nodes 0 ...` + `bestmove 0000`,  |
| 15-C4 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS 05-F1 / check_s05f1/RESULT.md (raw: job1/evidence/mate392/, job1/evidence/mate392/verify_safe.txt) / reproduced on my own harness (probe2.py, |
| 15-F9 | UNSTATED (no thread count) | `k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1` | 5 / A SECOND independent mate-distance fault at depth 14 on G: `k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1` reports `mate -9` (18 plies) with a 15-ply PV tha |
| 15-F11 | UNSTATED (no thread count) | `(not named in the line)` | 5 / The 15-F9 fault self-corrects one iteration later and is not a difficulty effect: on `k7/6R1/5N2/p4K1P/P7/8/8/8 b` depth 14 says `mate -9` (18 pli |
| 15-F13 | UNSTATED (no thread count) | `(not named in the line)` | 5 / **WITHDRAWN by 15-R1 — do not use.** I claimed `score mate 0` at a checkmated root was a defect and that terminal score kinds read inverted; both  |
| 15-R1 | UNSTATED (no thread count) | `(not named in the line)` | 5 / RETRACTION of 15-F13, with the measurement that refutes it: `score mate 0` at a checkmated root is CORRECT — python-chess's own parser turns the e |

### seat 10 — 9 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| 10-F14 | UNSTATED (no thread count) | `(not named in the line)` | 10 / A `searchmoves` root restricted to ALL 20 of 20 legal moves is not merely a smaller tree, it is UNSOUND: depth 12 gives cp 23 / d2d4 where unrest |
| 10-F15 | UNSTATED (no thread count) | `(not named in the line)` | 10 / A `searchmoves`-restricted search CORRUPTS A LATER UNRESTRICTED SEARCH in the same process: restricted-then-unrestricted gives 36,745 nodes at cp |
| 10-F17 | UNSTATED (no thread count) | `(not named in the line)` | 10 / The restricted-root unsoundness and the table contamination are TWO INDEPENDENT DEFECTS, settled: with `Clear Hash` in a fresh process the restri |
| 10-F18 | UNSTATED (no thread count) | `(not named in the line)` | 10 / Minimal repro of the restricted-root score defect needing NO restricted set: `searchmoves e2e4` (the move the unrestricted search already plays)  |
| 10-C7 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS S-F8, S-F8a, S-F8b (seat 27) / audit/AUDIT_KNOWN.md §"K14 is ONE problem, seen from three angles"; my cells D and E of k14_split.py / seat 27 |
| 10-R2 | UNSTATED (no thread count) | `(not named in the line)` | 10 / **RETRACTION of 10-F14's "unsound" and of 10-F17's "two defects".** Seat 27 reproduced the all-20 case and found the mechanism: stopping IIR at t |
| 10-F19 | UNSTATED (no thread count) | `(not named in the line)` | 10 / What actually remains open, ONE question not two: with `IirDepth 20` (IIR cannot fire at depth 12) the score gaps SURVIVE on my build (single-mov |
| 10-F20 | UNSTATED (no thread count) | `(not named in the line)` | 10 / A separate OBSERVATION whose mechanism I have NOT identified: a later unrestricted search measures differently depending on what ran before it, a |
| 10-F22 | UNSTATED (no thread count) | `(not named in the line)` | 10 / `ucinewgame` is the cold-start control; `Clear Hash` is NOT. `ucinewgame` restores the cold 56,720 exactly, while `Clear Hash` yields a THIRD dis |

### seat 27 — 9 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| S-C3 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS 01-F5 and 01-F8 (and 25-F3) / forge-combo29/swarm/27/job3/f3/table.txt (again: `python3 forge-combo29/swarm/27/job3/f3_halfmove_cap.py /agent |
| S-F8 | UNSTATED (no thread count) | `(not named in the line)` | area 7 / Beyond Opus file 1s searchmoves item (which lists only the smaller tree, IIR at the root and no TT store): the restriction also changes the S |
| S-F8a | UNSTATED (no thread count) | `(not named in the line)` | area 7 / The IIR part of S-F8 is now pinned: skipping internal iterative reduction at a `searchmoves`-restricted root recovers the node count (26329 - |
| S-F4a | UNSTATED (no thread count) | `(not named in the line)` | area 7 / The S-F4 drift has a ten-second reproduction: three identical `go depth 10` searches of kiwipete each preceded by `setoption name Clear Hash` |
| S-F11 | UNSTATED (no thread count) | `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 60` | area 7/10 / **CORRECTED by seat 12** — my original line said the two patches compose in one order only and that the reverse fails with `1 out of 1 hun |
| S-F8b | UNSTATED (no thread count) | `(not named in the line)` | area 7 / S-F8 is BOUNDED, not solved: with `IirDepth 20` (IIR cannot fire at depth 12) the restricted search still reports cp 26 against cp 34 unrestr |
| S-C4 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS 10-F17 and 10-F14, and ADDS the mechanism / forge-combo29/swarm/27/job7/f2/SUMMARY.txt and the all-20 table in the store note `internal/swarm |
| S-F8c | UNSTATED (no thread count) | `(not named in the line)` | area 7 / CAUTION on 10-F18: its depth sign flip is confounded with the move changing. At depths 8 and 10 the unrestricted search plays d2d4 and the re |
| S-C5 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS 10-F17/10-F15 separation with a committed script / forge-combo29/swarm/27/job7/f3_all20_mechanism.py (again: run it on build-release, build-s |

### seat 07 — 8 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| 07-P1 | UNSTATED (no thread count) | `(not named in the line)` | 7 / **READ THE PAIR 07-F1 + 07-R1 TOGETHER.** 07-R1 withdraws my earlier UB claim: there is no empty-container read at search.cpp:2640. 07-F1 is still |
| 07-F1 | UNSTATED (no thread count) | `(not named in the line)` | 7 / `position` + `go depth N searchmoves <no legal root move>` answers `info depth N ... score cp 0 nodes 0` plus `bestmove 0000`, i.e. it presents an |
| no legal root move | UNSTATED (no thread count) | `7k/5Q2/6K1/8/8/8/8/8 b - - 0 1` | `position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1` + `go depth 3 searchmoves a1a2` / `0000` / `info depth 3 seldepth 3 score cp 0 nodes 0 nps 0 hashfull 0  |
| one legal root move | UNSTATED (no thread count) | `(not named in the line)` | `position startpos` + `go depth 6 searchmoves e2e4` / `e2e4` / `info depth 6 seldepth 6 score cp -1 nodes 438 ... pv e2e4 c7c5 d2d3 e7e6 c2c3` / 438 |
| two named, one legal | UNSTATED (no thread count) | `(not named in the line)` | `position startpos` + `go depth 6 searchmoves e2e4 e2e5` / `e2e4` / `info depth 6 ... score cp -1 nodes 438 ... pv e2e4 c7c5 ...` / 438 |
| empty list | UNSTATED (no thread count) | `(not named in the line)` | `position startpos` + `go depth 4 searchmoves` / `0000` / `info depth 4 ... score cp 0 nodes 0 ...` / 0 |
| 07-C1 | UNSTATED (no thread count) | `(not named in the line)` | REFUTES 17-S-F2 (and CONFIRMS the symptom of 17-S-F1) / job3/reach_2640.py + job3/check_17SF2.py, raw in job3/raw_reach2/ and job3/raw_dbg/ / REFUTES: |
| 07-C18 | UNSTATED (no thread count) | `(not named in the line)` | RE-CONFIRMS 07-F1 on a fresh build, and confirms the patch still applies cleanly with no fuzz / job2/cases_searchmoves.txt re-run into job2/raw_reveri |

### seat 11 — 8 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| S-C7 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS S-F3 (seat 05) — threshold only / The fifty-move draw takes effect at halfmove clock H=91, nine plies before 100: KRvK `1K6/8/8/3R4/8/8/8/k7  |
| S-F10 | UNSTATED (no thread count) | `(not named in the line)` | area 1/5 boundary / The 9-ply-early fifty-move draw is NOT a universal offset. At `go depth 10` with OwnBook off, the first `cp 0` is at H=**91** for  |
| S-F11 | UNSTATED (no thread count) | `(not named in the line)` | area 1/5 boundary / The early fifty-move draw is a SEARCH-HORIZON effect, not a fixed rule offset — this goes beyond seat 05's S-F3. KRvK `1K6/8/8/3R4 |
| S-F12 | UNSTATED (no thread count) | `(not named in the line)` | area 1/5 boundary / MY OWN S-F11 PREDICTION FAILED, and the correction matters. From the depth 4/6/8/10/12 flips (96/95/92/91/89) I predicted depth 14 |
| S-C9 | UNSTATED (no thread count) | `6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 99 1` | CONFIRMS 21-F9 (seat 21) — and this is the most consequential defect I have checked / At halfmove clock 100 the root is adjudicated drawn at **0 nodes |
| S-F18 | UNSTATED (no thread count) | `(not named in the line)` | area 1/5 boundary / The mate-throwing adjudication has a SHARP boundary at exactly halfmove **100**: `6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - H 1` at `go de |
| S-F19 | UNSTATED (no thread count) | `(not named in the line)` | area 1/5 (nails S-C9/21-F9 to code) / The mate-loss is a ROOT-LEVEL adjudication that omits the mate exception the leaf test has. `Worker::is_draw` (s |
| S-P1 | UNSTATED (no thread count) | `(not named in the line)` | area 1/5 TEXT PATCH / Fix for S-F19 / S-C9 / 21-F9: `patches/fifty_mate_root.patch.txt` adds a mate-on-board guard so a halfmove>=100 root is only adj |

### seat 25 — 7 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| S-F1 | UNSTATED (no thread count) | `(not named in the line)` | 5 / A depth-12 S14 search of 8/8/1p6/8/p3p3/8/2Kpk3/8 w reports `score mate -12` but plain minimax proves white is mated in exactly 4 moves (and not 3 |
| S-F2 | UNSTATED (no thread count) | `(not named in the line)` | 5 / The same root's mate score is unstable across depth in the direction of the truth: mate -12 (d12-16), -5 (d18), -4 (d22-28), where -4 is the prove |
| S-F3 | UNSTATED (no thread count) | `(not named in the line)` | 5 / At halfmove clock 99 the engine reports `score cp 0` at every depth 1..16 and at `go nodes 50000`, and plays a NON-clock-resetting shuffle, on boa |
| S-F6 | UNSTATED (no thread count) | `8/8/Q7/8/8/K7/8/k1Q5 b - - 0 1` | 5 / A checkmated root is reported as `score mate 0` (a mate score of zero plies, which is not a legal claim: mate is either not present in this positi |
| S-F7 | UNSTATED (no thread count) | `(not named in the line)` | 5 / On a terminal root, `go nodes 100` and `go movetime 50` emit 64 info lines (depths 1..64) at zero nodes each, instead of one line and a stop: the  |
| S-F8 | UNSTATED (no thread count) | `2b2knr/2qpp3/1r2n1pb/p4pP1/4PPQp/3P3P/PP1KB3/1qB3NR w - - 0 22` | 5 / PROVEN SCORE_WRONG, not just a short PV: on a middlegame position (2b2knr/2qpp3/1r2n1pb/p4pP1/4PPQp/3P3P/PP1KB3/1qB3NR w - - 0 22) depth 12 report |
| S-F10 | UNSTATED (no thread count) | `(not named in the line)` | 5 / The wrong mate score is not a state artefact and survives a correct deeper search in the same process: on both proven positions a FRESH process wi |

### seat 30 — 5 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| 30-C1 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS S-F5 (seat 01) / check1/check_s01f5.py + out_rel/results.json + out_asan/results.json (again: `python3 check1/check_s01f5.py ~/b/rel/forge /t |
| 30-F7 | UNSTATED (no thread count) | `(not named in the line)` | 10 / BEYOND seat 01's S-F5: the halfmove>=100 root shortcut is side-blind and mate-blind — a BLACK mate-in-1 at halfmove 100 is missed the same way (` |
| 30-F8 | UNSTATED (no thread count) | `(not named in the line)` | 10 / Seat 01's proposed fix (delete the `board.halfmove_clock() >= 100` term from root_drawn) DOES fix every mate case at every counter with bench 11/ |
| 30-C2 | UNSTATED (no thread count) | `(not named in the line)` | REFUTES S-F3 (seat 05) AS AN INTERPRETATION — its numbers reproduce exactly / check2/check_s05f3.py + check2/out/results.json (again: `python3 check2/ |
| 30-F19 | UNSTATED (no thread count) | `(not named in the line)` | 10 / On the PC r15 build the fifty-move draw is still adjudicated at a huge counter WITHOUT the base tree's side-blind collapse: `quiet_hm100` (no mat |

### seat 17 — 4 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| S-C2 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS 07-F1 / reproduced on my build with my own driver: the five info lines are literally `score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv` (empty p |
| S-C3 | UNSTATED (no thread count) | `(not named in the line)` | 07-F1 vs my S-F1 / note, not a refutation: S-F1 and 07-F1 describe the same engine behaviour from two seats. 07-F1 adds the `score cp 0 nodes 0` prese |
| S-C11 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS 21-F9 (sharply) / reproduced with a clean boundary: one board with a mate in 1 for White (`6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - <hm> 1`). At half |
| S-C11 (halfmove 100 misses a mate in 1) | UNSTATED (no thread count) | `(not named in the line)` | `f2f3`, `cp 0 nodes 0` / **`a1a8`, `score mate 1`, nodes 84/105** / **REPAIRED on the PC build** (FORGE_FIX_ROOT_DRAWN) |

### seat 21 — 4 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| 21-F9 | UNSTATED (no thread count) | `(not named in the line)` | 1 / The halfmove ≥ 100 root shortcut fires for EVERY counter at or above 100 — 100, 150, 9999, 65536, seed-drawn values up to 2147483648 all give `inf |
| 21-C3 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS 30-F7 / On boards I chose: a black mate-in-1 and a white mate-in-1 are both missed at halfmove 100 (`cp 0`, 0 nodes, non-mating move) by `go  |
| 21-F11 | UNSTATED (no thread count) | `4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60` | 1 / A CHECKMATED root is scored `score mate 0` — `4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60` (python-chess: checkmate, 0 legal moves) answers `info depth |
| 21-C6 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS seat 12's two_doors_mate patch / Third independent verification: on the unpatched ASan build the fifty-move door AND the threefold-repetition |

### seat 28 — 4 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| S-C1 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS S01-F5 / forge-combo29/swarm/28/checks/CHECK_s01f5.md + check_s01f5_out.txt (again: `python3 check_s01f5.py ~/build/base-release/forge /tmp/o |
| S-F4 | UNSTATED (no thread count) | `(not named in the line)` | 8 / The same 0-node root adjudication also fires on `board.is_repetition()` (src/search.cpp:2250-2252): a mate-in-one board reached a third time by le |
| S-F19 | UNSTATED (no thread count) | `8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1` | 8 / My patch is one of THREE competing fixes for the same two drawn-root doors (seat 01 one-line, seat 01 job2c combined, seat 12 bypass, mine); only  |
| S-F24 | UNSTATED (no thread count) | `(not named in the line)` | 8 / Decision file for the drawn-root doors: `DRAWN_ROOT_DOORS.md` gives per-door base-vs-PC20 behaviour with node counts and states at the top that NO |

### seat 12 — 3 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| S-F2 | UNSTATED (no thread count) | `(not named in the line)` | 2 / the REPETITION door of the root draw adjudication: a mate-in-one on a threefold-repeated position (halfmove clock 8) is skipped exactly like the h |
| S-F4 | UNSTATED (no thread count) | `6k1/8/5PPP/8/8/8/8/R6K b - - 99 40` | 2 / the root-draw short-circuit ALSO fires one ply down: `Worker::is_draw` returns 0 at any node with halfmove>=100, so on `6k1/8/5PPP/8/8/8/8/R6K b - |
| S-F5 | UNSTATED (no thread count) | `6k1/5ppp/8/8/8/8/8/R5NK b - - 99 40` | 2 / control for S-F4: `6k1/5ppp/8/8/8/8/8/R5NK b - - 99 40` also answers `cp 0` at hm99, but CORRECTLY — black has six counter-resetting pawn moves, s |

### seat 06 — 2 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| S-F9 | UNSTATED (no thread count) | `(not named in the line)` | 6 / SUSPICION not proven: on G index 196 (5Q2/1k6/3pK1PP/3P4/8/4N3/8/8 w) the engine reports `cp 4402` while its colour mirror reports `mate 14`; inde |
| S-F11 | UNSTATED (no thread count) | `5Q2/1k6/3pK1PP/3P4/8/4N3/8/8 w - - 0 1` | 6 / FOLLOW-UP that CLOSES S-F9: cp 4402 vs mate 14 is a depth artefact, not a bug - 5Q2/1k6/3pK1PP/3P4/8/4N3/8/8 w gives cp 4009/4177/4412/mate 8/mate |

### seat 02 — 1 lines

| finding | flag | board named in the line | what the line claims |
|---|---|---|---|
| S-C4 | UNSTATED (no thread count) | `(not named in the line)` | CONFIRMS S-F20 (seat 20) / forge-combo29/swarm/02/check_s20f20/RESULT.md, out/table.json, out/checks.json; again: `cd forge-combo29/swarm/02/check_s20 |

