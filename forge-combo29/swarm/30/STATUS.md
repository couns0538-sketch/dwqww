seat: 30
branch: for-fable-and-opus/swarm-30
area: 10
seed: 3001

## Mon Nov 16 09:28:46 PM UTC 2026

**Done** — STEP 1 seat 30 (area 10, seed 3001). STEP 2 build + honesty check: all four numbers match.
**Job 2 (area 10) done**: recounted deepseek6's newest report (long56). Verdict: one number contradicted by its own raw file (seqs 0 vs 2000), one vacuous (its legality check examines 0 of 2000), one unproven (no sanitizer proof), one false (no per-sequence records) — but the RESULT is true: my own runner on my own ASan+UBSan build gives 0 crashes / 0 hangs / 0 sanitizer lines / 0 illegal bestmoves out of 7,538 bestmoves actually checked, twice, identical. See REPORT_job2.md, FINDINGS.md 30-F1..F6.
**Area 10 job 1**: no candidate exists yet — I read all 49 seat branches; none has a FINDINGS.md line (all still on STEP 1/2). Re-checking every cycle.
**Next command**: `cd /agent/repos/dwqww && bash forge-combo29/swarm/30/read_board.sh /tmp/board` then, if a NEW finding appears, check it as 30-C1; otherwise start area 10 job 3 (glmflash5 match recount).

## Mon Nov 16 09:30:29 PM UTC 2026

**Check 30-C1: CONFIRMS seat 01 S-F5** (halfmove>=100 hides mate in 1) — reproduced on release AND ASan+UBSan builds with identical numbers (hm99 -> mate 1/a1a8/126 nodes; hm100 -> cp 0/f2f3/0 nodes). Beyond it: the shortcut is side-blind (black mate-in-1 at hm100 also missed) and score-blind (any hm100 position collapses to 0 nodes). Their proposed patch fixes the mate with all four honesty numbers unchanged BUT deletes the real fifty-move draw (+10 cp / 425 nodes instead of cp 0 / 0 nodes at hm120) — 30-F8. Reports: REPORT_check1.md, REPORT_job2.md.
**Next command**: `cd /agent/repos/dwqww && bash forge-combo29/swarm/30/read_board.sh /tmp/board3` then check the next NEW finding nobody took (candidates: seat 11 S-F8 setoption value-word, seat 05 S-F3 fifty-move early, seat 12 S-F1 ucinewgame reset); otherwise area 10 job 3 (glmflash5 recount).

## Mon Nov 16 09:33:01 PM UTC 2026

**Area 10 job 3 DONE**: recounted glmflash5's job-24 matches from its committed game lists. All 15 numbers exact (6 matches W-L-D/Elo/CI + 3 pools), intervals match the brief's formula to 0.01. Found what it did not say: M46/M50 and M53/M54 play identical opening sets (not independent seeds). 2 of my 6 predictions were killed and that is written into REPORT_job3.md section 7.
**Next command**: `cd /agent/repos/dwqww && bash forge-combo29/swarm/30/read_board.sh /tmp/board4` then check the next NEW unchecked finding; area 10's three jobs are all done, so the cycle from here is (a) another seat's check, or (c) area-10 job 1/2 again with a NEW seed (SEED+10 = 3011) on a fresh position set.

## Mon Nov 16 09:36:13 PM UTC 2026

**HARNESS AUDIT after seat 19's 19-F12 broadcast (deadline moved to 22:30 UTC).**
My job-2 runner closed stdin while a search was live in 772 of 2,000 sequences, so its '0 illegal bestmoves of 7,538' is NOT valid evidence — re-running now with stop-and-await. My honesty check re-verified with a synchronized harness: all four numbers exact. Check 1 and check 2 were never affected (they wait for bestmove). 30-C1/30-C2/30-F7/F8/F9 stand. FINDINGS.md now carries 30-F13/14/15 admitting the contamination in my own work.
**Next command**: `cd /agent/repos/dwqww/forge-combo29/swarm/30/job2 && python3 runner.py ~/b/asan/forge seqs56_generated.txt out_full_fixed 4` then rewrite REPORT_job2.md section 4 with the corrected counts.

## Mon Nov 16 09:42:41 PM UTC 2026

**Checkpoint.** FINDINGS.md complete as it stands. Harness audit done: job-2 runner was contaminated by 19-F12 (772/2,000 sequences) and is re-running now (out_full_fixed, 2 of 4 workers, slower because every open search is stopped and awaited). Honesty numbers re-verified with a fully synchronized harness: all four exact. All three of my checkers now hard-fail when a parsed field is missing; proven against three stub engines. My own validator initially gave a FALSE PASS by not executing the checkers — found, fixed, re-run.
**Next command**: `cat forge-combo29/swarm/30/job2/out_full_fixed/summary.json` when the run lands, then rewrite REPORT_job2.md section 4 with the corrected counts and re-push.

## Mon Nov 16 09:56:03 PM UTC 2026

**Final-push preparation.** Cold-start audit done and PASSED: no Clear Hash anywhere, one fresh process per measurement, proven by separating warm (22108/7899/4703) from cold (15572 x3) on the same board. Job-2 corrected re-run is now in flight in the background (out_full_fixed); its previous numbers remain marked INVALID in REPORT_job2.md section 7 and in 30-F13.
**Next command**: `cat forge-combo29/swarm/30/job2/out_full_fixed/summary.json` then push the corrected table.

## Mon Nov 16 10:05:29 PM UTC 2026 — 22:05 CHECKPOINT

**Complete FINDINGS.md pushed** (30-F1..F18, 30-C1..C2) with every raw job folder, patch file and this STATUS.
Corrections recorded honestly: job-2's original totals are INVALID (19-F12 contamination, 772/2,000 sequences) and are marked superseded in REPORT_job2.md; the corrected run is running now as out_full_fixed. Cold-start audit passed (no Clear Hash, fresh process per measurement, warm-vs-cold separated). Measurement-integrity audit passed (3 checkers raise on missing fields; proven against 3 stub engines; my own validator's false PASS found and fixed).
**Next command**: `cat forge-combo29/swarm/30/job2/out_full_fixed/summary.json` and push the corrected table before 22:30.

## Mon Nov 16 10:15:22 PM UTC 2026

**CORRECTED JOB-2 NUMBERS IN**: 2,000 sequences, 0 crashes / 0 hangs / 0 sanitizer lines / 0 illegal bestmoves out of 1,032 honestly-attributable bestmoves (2,902 excluded as ended-live under 19-F12). REPORT_job2.md now leads with this and keeps the invalidated numbers only as a record. Everything pushed.
**Next command**: `git log --oneline -1` and stop; all three area-10 jobs and three checks are complete and pushed.

## Mon Nov 16 10:18:46 PM UTC 2026 CONTINUE: 12 more hours, ends at Tue Nov 17 10:18:46 AM UTC 2026

Seat kept: 30 (from ~/swarm_seat.txt), branch for-fable-and-opus/swarm-30, folder forge-combo29/swarm/30/. No new seat taken.
**Now**: reading FABLE_TO_swarm_5.md (the owner's PC engine) before the next step, per TEXT 2, then building it in a separate copy with -DFORGE_MATE_ALPHA_GUARD=1 and checking its known bench numbers. Then continuing with BOTH builds (base 6b98f217 + PC build) under PC20 where a job needs settings.
**Next command**: `cd /agent/repos/dwqww && git fetch -q --depth 1 origin handoff/fable-opus-combo29-all-20261114 && git ls-tree -r --name-only FETCH_HEAD | grep FABLE_TO_swarm`

## Mon Nov 16 10:20:31 PM UTC 2026

**PC r15 BUILD WORKS.** Patch extracted from FABLE_TO_swarm_5.md, sha256 starts d6bd72c531f785f4 (exactly as file 5 states), applied with patch -p1 (11 files, rc=0), built with -DFORGE_MATE_ALPHA_GUARD=1. ALL EIGHT known answers match: none 312866/862329/3024920/4865609; S14 242796/656517; PC20 278024/587276. Threads 1 + Hash 16 now set explicitly in every harness (owner's rule). No recorded result of mine ever used Threads > 1 (the only mentions are check3's deliberate setoption-parsing probes, which never contributed a score).
**Next command**: `python3 check1/check_s01f5.py ~/b/pc/forge out_pc` — re-run my own findings 30-C1/30-F7/F8 on the PC build under PC20.

## Mon Nov 16 10:24:25 PM UTC 2026

**PC r15 built and verified** (patch sha256 d6bd72c5..., 8/8 known answers: none 312866/862329/3024920/4865609, S14 242796/656517, PC20 278024/587276). BOTH builds now used; Threads 1 everywhere.
**Findings this stretch**: 30-C4 my halfmove-mate find is REPAIRED on the PC (all counters find the mate, draw still handled); 30-C5/30-F20 the fifty-move horizon + 7.25M-node spike PERSIST on the PC; 30-F21/22 stdin-close fabrication is on the PC too; 30-C6 CORRECTS my own F21/F22 — the window is only 0 ms, not all searches; 30-F23 intermediate answers differ (1-20 ms); 30-C7/30-F24 REFUTE my own clock worry — clock stop is faithful to its node budget 20/20.
**Next command**: `cd pc && python3 clock_vs_nodes.py out_clocknodes_pc 20` on the PC build, then re-run my area-10 job-2 UCI sequences on PC r15 under PC20.

## Mon Nov 16 10:39:25 PM UTC 2026

**Big find (30-F25)**: the BASE tree HANGS on a malformed  line — , ,  each still searching after 120 s at **207,603,225 / 168,212,008 / 207,603,225 nodes** with no bestmove, Threads 1, fresh process. Controls clean (, ,  all answer). Repaired on the PC build (FORGE_FIX_GO_PARSE): all three answer in 0.01 s. Also 30-F26 (7/12 go lines differ stably, 3x each build) and 30-F27 (PC20 fuzz clean, 4,673 bestmoves verified).
**Next command**: `cd pc && python3 go_nodes_hang.py out_gohang_s14 120` to see whether S14/PC20 change the hang, then re-check whether any other seat has taken 30-F25.

## Mon Nov 16 11:01:38 PM UTC 2026

**New findings**: 30-C8 refined my own F25/F28 (malformed go nodes = unbounded search, stop recovers it; 207M nodes in 120s, still true, wording fixed). 30-F29/F30: in lone-king endings BOTH builds score a python-chess-proven mate in <=5 plies as cp at depth 12, Threads 1 — base 6/16, PC r15 9/16 report mate; the moves still win, so it is a SCORE defect (matters for time management and adjudication).
**Builds/settings in every line**: build named (base 6b98f217 / PC r15), settings named (defaults, S14 or PC20), Threads 1 stated.
**Next command**: `cd pc && python3 bare_king_mates.py out_bareking20 20 12` for a larger sample, then check the board for a seat able to confirm 30-F29.

## Mon Nov 16 11:04:28 PM UTC 2026

**Completed a full defect->repair chain (30-F33/F34)**: 6 of 40 lone-king boards where python-chess proves mate in <=5 plies still read as centipawns on the BASE tree at depth 24 (5 of the 6 are KRvK); the PC r15 build reports a mate on **6/6, twice each**. Deterministic, Threads 1, fresh process per search. Also 30-C10 (the one board, sharpened) and 30-C9 (most cases are only depth, corrected honestly).
**Next command**: `cd pc && python3 go_parse_diff.py out_goparse2` — no: next is to re-check my check1/check2 findings under PC20 for the fifty-move spike on the PC at depth 12 with a smaller node budget, then push.

## Mon Nov 16 11:04:51 PM UTC 2026

**30-F35 (practical)**: the fifty-move draw is INVISIBLE below depth 9 on the PC build under PC20 — H=90 and H=91 score identically at go nodes 2000/20000/200000/2000000 and depth 4-8; only depth 9 (4,848,748 nodes) or depth 10 (7,251,835) shows cp 0. 2,000-node self-play (glmflash5's effort) cannot see a fifty-move draw at all.
**Counts so far**: 48 lines in FINDINGS.md — 30-F1..F35, 30-C1..C10, incl. 5 self-corrections (C6, C7, C8, C9, C10) and 2 withdrawn-strength claims rewritten in place.
**Next command**: `cd pc && python3 bare_king_mates.py out_bareking_pc20 20 12` with PC20 to see if the PC20 switches change the lone-king mate rate (30-F31 was measured with defaults).

## Mon Nov 16 11:05:58 PM UTC 2026

**Method fix + confirmation (30-C11)**: my earlier PC20 instability was MY harness (burst setoptions with 4ms sleeps, no readyok), not the engine. With a strict harness (every setoption read to readyok, every search awaited) the engine is deterministic: same score AND same nodes 5/5 and PC20 repeats 8/8. Confirmatory rates unchanged: base 16/40, PC defaults 27/40, PC PC20 23/40 report a python-chess-provable mate at depth 12, Threads 1.
**Rule I now follow everywhere**: no burst setoptions; readyok after each one.
**Next command**: `cd pc && python3 mate_rate_strict.py out_strict40 20 14` at depth 14 to see whether PC20's deficit disappears with depth.

## Mon Nov 16 11:06:34 PM UTC 2026

**30-C13 (methodology, with the control the brief demands)**: ucinewgame restores cold EXACTLY on both builds, proven three ways — fresh process, one process WITH ucinewgame (identical nodes), one process WITHOUT (diverges from the 2nd position). That is a zero with a planted failure beside it, not an unbacked claim. 30-F37: PC20 switches carry no state across ucinewgame, so a match may reuse one process.
**Totals**: 51 lines in FINDINGS.md (30-F1..F37, 30-C1..C13), including self-corrections C6-C13.
**Next command**: `cd pc && python3 - <<'PY' ... search 30-F33's six boards under S14 (not just defaults) ` — to state which settings the KRvK failure needs.

## Mon Nov 16 11:07:21 PM UTC 2026

**30-C14 CONFIRMS seat 08's 08-F18**: the reserve-empty emergency path survives on the PC r15 build under PC20 — wtime 10/1/0 all answer from a depth-1 search (startpos 26 nodes, G0 67 nodes, ~2.1 ms), identical on both builds with OwnBook false. **30-F39**: the trap that can make this look like a 0-node answer — with OwnBook at its default TRUE the base tree answers startpos from the BOOK (, zero info-depth lines), which is indistinguishable from an emergency answer unless the book is turned off. My own first pass fell into it and the finding records that.
**Next command**: `cd pc && python3 mate_rate_strict.py out_strict16 20 16` — depth 16 on both builds to see how far the base tree's mate blindness extends.

## Mon Nov 16 11:09:31 PM UTC 2026

**Second confirmation of another seat's finding**: 30-C15 CONFIRMS seat 24's 24-F14 on BOTH builds — at checkmate and stalemate roots all six bounded go forms answer bestmove 0000 in 0.00s, while go infinite / go ponder give nothing in 8s; my control shows a normal board's go infinite DOES answer after stop, so the wait is specific to terminal roots. Earlier this session 30-C14 confirmed seat 08's 08-F18.
**Also this stretch**: 30-F40 — the base tree's mate blindness plateaus (21/40 at depth 16) while PC holds 31/40, so it is not a depth shortage.
**Next command**: verify seat 24's 24-F16 claim that its patch applies to the PC tree and keeps the three bench numbers, with my own build.

## Mon Nov 16 11:10:13 PM UTC 2026

**30-C16: seat 24's terminal-root patch INDEPENDENTLY VERIFIED on my own build.** Applied to a clean PC r15 copy (patch -p1 --fuzz=0, rc=0, same 154-line offset seat 24 reports), built with -DFORGE_MATE_ALPHA_GUARD=1: checkmate and stalemate roots now answer bestmove 0000 in 0.00s for go infinite AND go ponder (nothing in 8s before), all six bounded forms still answer, and a NORMAL board's go infinite still waits for stop (control). Honesty gate unchanged: 312866 / 862329 / 3024920 / 4865609.
**Next command**: `cd /agent/repos/dwqww && bash forge-combo29/swarm/30/read_board.sh /tmp/board8` to find the next unchecked finding.

## Mon Nov 16 11:12:32 PM UTC 2026

**Root-caused a major owner-facing issue (S-F50 family)**: the MultiPV+large-Hash collapse is NOT the search — 30-F41 proves at FIXED depth the MultiPV-3/Hash-2048 cell searches MORE (143,794 vs 52,591 nodes) and at fixed nodes it is normal; only the CLOCK path collapses (67-220 nodes). 30-F42 adds the mechanism: 67 nodes in 1,210 ms = ~18 ms PER NODE, warm or cold, so the TT is being touched across its full extent per search. A user setting MultiPV 3 + 2 GB hash gets a depth-1 move plus a second-long hitch every move.
**Honest gaps**: I could NOT reproduce seat 20's literal 0-node answer (0 in 70 runs, idle); I record the collapse instead of the 0.
**Next command**: `cd check6 && python3 check_s20f50.py out_under_load 5` with three CPU hogs running, to test whether load converts the collapse into a true 0-node answer.

## Mon Nov 16 11:13:50 PM UTC 2026

**30-C18: seat 20's S-F50 zero-node answer CONFIRMED at last** — under three CPU hogs, P1 / Hash 2048 / MultiPV 3 gave 1 zero-node answer in 4 runs with moves b8a8 AND d5d4: the same cell and one of the same two moves seat 20 published. It is rare even under load (1/16 of the 2048-MB probes) but real. Chain is now complete: 30-F41 (clock-only collapse, fixed depth searches MORE), 30-F42 (~18 ms per node warm or cold), 30-C18 (load turns it into a literal 0-node answer).
**Next command**: `cd check6 && python3 check_s20f50.py out_load2 6` for a second load run to state the rate honestly.

## Mon Nov 16 11:16:17 PM UTC 2026

**30-F43 — the owner-facing answer, measured**: MultiPV 1 is SAFE at every Hash size — Hash 16/64/256/512/1024/2048 MB all give depth 16 and EXACTLY 266,687 nodes (132-164 ms) on the same position. The risk is entirely MultiPV > 1 + large Hash: at MPV 3 the tree is identical (229,977 nodes) but wall time grows ~65 % per Hash doubling (242 -> 305 -> 399 ms) and ends in the 67-node collapse at 2048 MB. At MPV 8 the tree is larger (374,431 nodes). Recommendation: keep MultiPV 1 at any Hash; if MultiPV > 1 is needed for analysis, keep Hash small.
**Also fixed**: 30-F41's row had an inline table whose pipes broke the markdown — repaired and validated (no malformed rows).
**Next command**: `cd check6` and measure whether the MPV>1 slowdown at small Hash is the SAME memory path (per-node cost) — to name the code site for the owner.

## Mon Nov 16 11:16:44 PM UTC 2026

**Completed a full root-cause chain on the MultiPV/large-Hash fault** (30-F41, F42, F43, F44, C20): the tree is byte-identical (16,642 nodes at go depth 8) but per-node cost at MultiPV 3 goes 2.0 us (Hash 16) -> 4.7 -> 17.2 -> 117.5 -> **203.9 us** (Hash 2048), while at MultiPV 1 it is FLAT 0.8 us/node at every Hash. So the 100x overhead exists only on the MultiPV>1 path and scales with table size — a specific place for a repair to look. Owner-facing: MultiPV 1 is safe at any Hash; MultiPV>1 with a big Hash can return a depth-1 (occasionally 0-node) move.
**Next command**: write REPORT_pc_multipv.md consolidating the chain, then continue the cycle.

## Mon Nov 16 11:18:04 PM UTC 2026

**Two new confirmations of other seats, both owner-actionable**: 30-C21 CONFIRMS 15-F24 — the shipped PC build finds the halfmove-100 mate BUT searches a thrice-repeated root the base tree correctly draws (cp 0, 0 nodes); I proved the repetition with python-chess (3 occurrences, can_claim_threefold). 30-C22 CONFIRMS 15-F25 — seat 15's one-line split of $root_drawn$ gives BOTH behaviours on my own build (mate 1/126 nodes at halfmove 100 AND cp 0/0 nodes on the thrice-repeated root), twice-repeated still searched, and the honesty gate is unchanged (312866/862329/3024920/4865609). Patch text kept in check7/.
**Next command**: continue the cycle — read the board for the next unconfirmed finding, else re-run an earlier job with a new seed per the brief.

## Mon Nov 16 11:18:21 PM UTC 2026

**REPORT_pc_repairs.md written and pushed** — consolidates both verified repairs with build sha256s, the settings tables, and the honest limits (I verify patches apply/build/pass the honesty gate; I did NOT run matches for strength). 30-C23 added: both the regression and the split fix hold under S14 AND PC20, so the repair does not depend on the option set. Patch provenance in check7/PATCH_UNDER_TEST.txt (split build sha256 ff5e50cb..., patch sha256 ef1d1df3...).
**Status totals**: 68 finding lines in FINDINGS.md; 3 of my own findings confirmed by other seats (F6, F7, F35 and more); 4 confirmations issued by me this session (08-F18, 24-F14, 24-F16, 15-F24, 15-F25).
**Next command**: `cd /agent/repos/dwqww && bash forge-combo29/swarm/30/read_board.sh /tmp/board10` for the next unconfirmed finding.

## Mon Nov 16 11:18:51 PM UTC 2026

**30-C24 CONFIRMS 15-F30**: with my own harness on 5 boards x 3 budgets x 3 reps (PC r15 + PC20, Threads 1): `go nodes` exceeded its budget in **0 of 15** cells (largest -0.4%), `go softnodes` in **14 of 15**, up to **+118.8%**; all cells deterministic. Plus 30-F45: the documented 4x hard-stop was never approached (worst 2.2x), so budget with ~2.2x not 4x.
**Confirmations issued by me this session: 6** (08-F18, 24-F14, 24-F16, 15-F24, 15-F25, 15-F30), each with its own harness, its own raw files and the build+settings named.
**Next command**: `cd /agent/repos/dwqww && bash forge-combo29/swarm/30/read_board.sh /tmp/board11` for the next unconfirmed finding.

## Mon Nov 16 11:21 UTC 2026 — FINAL (early block; the run continues to 2026-11-17 10:18 UTC)

### HEADLINE — the per-node price of MultiPV with a large Hash

The cleanest number in my area, and the one to decide a setting by: **at MultiPV 1 the per-node cost
is FLAT at 0.8 microseconds at EVERY Hash size**, while at MultiPV 3 it climbs to **203.9
microseconds per node** with a 2 GB Hash — about **a 255x price increase for a byte-identical search
tree**.

| `go depth 8`, Threads 1, same position, same 16,642 nodes | Hash 16 | Hash 64 | Hash 256 | Hash 1024 | Hash 2048 |
|---|---|---|---|---|---|
| **MultiPV 3** — us per node | 2.0 | 4.7 | 17.2 | 117.5 | **203.9** |
| **MultiPV 1** — us per node (5,024 nodes, 4 ms) | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 |

The node counts are byte-identical at every Hash size, so this is pure per-node overhead that scales
with the table: the MultiPV > 1 path appears to touch the whole transposition table per node. With a
5 s clock budget that means one depth-1 move instead of depth 16 (266,687 nodes at MultiPV 1). Under
CPU load it occasionally returns a **0-node** move (3 of 36 probes, all at Hash 2048 / MultiPV 3).
**Use MultiPV 1 at any Hash; if MultiPV > 1 is needed, keep Hash at 16-64 MB.**
Evidence: `check6/`, `REPORT_pc_multipv.md`, findings 30-F41, F42, F43, F44, C18, C19, C20.

### My finds, with state

Each line: id — claim — **state** — build and settings used.

1. **30-F25/F26/F28 + C25** — a malformed `go nodes` line (`-1`, `xyz`, `nodes depth 5`) is treated as **no node limit**: 207,603,225 nodes and no move after 120 s; repaired on the PC build, where all three answer in 0.00 s under FULL PC20. **Open for confirmation by another seat; verified on both builds by me, twice.** Base 6b98f217 under S14 and defaults, and PC r15 under PC20, Threads 1. See `NOTE_go_nodes_budget.md`.
2. **30-F41/F42/F43/F44/C20** — the MultiPV/large-Hash per-node table above. **Open.** PC r15, PC20, Threads 1, Hash swept.
2b. **30-C43/F52/F53 + NOTE_two_silent_runaways.md** — TWO SILENT RUNAWAYS of identical shape, measured in one run with controls passing: an unvalidated `go nodes` value (207,603,225 nodes, no move; repaired on the PC build) and a one-sided clock (26,264,563 nodes on PC r15 / 41,641,416 on base, with `wtime 0` and `wtime 1000` giving IDENTICAL counts). Lead sentence: **a one-sided clock is not a short clock, it is no clock.** Both are harness traps, not engine defects; a harness must validate its budget, send BOTH clocks, and always run under a wall-clock guard that reports RUNAWAY.
3. **30-C18/C19** — the 0-node answer seat 20 found: **CONFIRMED** (3/36 probes under load, Hash 2048/MPV 3, same cell and moves). PC r15, PC20, Threads 1, three CPU hogs.
4. **30-C1/F7/F8** (halfmove-100 mate missed; side-blind) — **CONFIRMED by seat 21 (21-C3)** on its own boards; **repaired on the PC build** (30-C4). Base 6b98f217/S14 and PC r15/PC20, Threads 1.
5. **30-F33/F34/F38** — six lone-king boards never find a python-chess-provable mate even at depth 24 on the base tree (5 of 6 are KRvK); the PC build finds all six, twice each. **Partly CONFIRMED** (a seat's S-C13 on two of the six). Base/S14+defaults and PC/S14+PC20, Threads 1.
6. **30-F29/F30/F31/F36/F40** — the mate-REPORTING rates: base 16/40 at depth 12 rising only to 21/40 at depth 16 (a plateau), PC 27/40 -> 31/40; PC20 slightly lower at depth 12, equal at depth 14. **Open.** Threads 1, strict harness.
7. **30-F35/F43** — the fifty-move draw is invisible below depth 9 (4.85 M nodes). **CONFIRMED by seat 17 (S-C15).** PC r15, PC20, Threads 1.
8. **30-F13/14/15/17/F27/C11/C13** — methodology: my original job-2 numbers were contaminated by 19-F12 and are **retracted and superseded**; the honesty check and checks 1-2 were never affected; `ucinewgame` restores cold exactly (three-way control on both builds); one process reproduces fresh node counts under PC20.
9. **30-F1..F5, F10..F12** — the two helper recounts: deepseek6's long56 report contradicts its own raw file and its legality check is dead code (its RESULT is nonetheless true); glmflash5's 15 numbers are exact and two of its matches share identical opening sets. **Open** (mine alone).

### My confirmations of other seats (each with my own harness and raw files)

**08-F18** (reserve-empty path, plus the OwnBook trap that can hide it, 30-F39) · **24-F14** and
**24-F16** (terminal-root unbounded `go`; I applied and built seat 24's patch) · **15-F24** (the PC
build's FORGE_FIX_ROOT_DRAWN conflates two repairs) · **15-F25** (its one-line split fix — I built it
and verified both behaviours under S14 and PC20 with the honesty gate unchanged) · **15-F30**
(`go nodes` a hard ceiling 0/15, `go softnodes` overshoots 14/15 up to +118.8 %). Reports:
`REPORT_job2.md`, `REPORT_job3.md`, `REPORT_check1.md`, `REPORT_check2.md`, `REPORT_pc_multipv.md`,
`REPORT_pc_repairs.md`, `NOTE_go_nodes_budget.md`.

## Mon Nov 16 11:21:55 PM UTC 2026

**30-C26: seat 23's budget-sensitivity phenomenon CONFIRMED, at 18.3 % (11/60) on MY OWN quiet positions** (seed 3011, random-game mid-games with >=8 quiet moves), vs their 27-30 % on their own selection. Same direction and same character (quiet, near-tied; 30-F46: where the move changes, both candidates score within a few cp), but a lower rate — binomial interval on 18.3 % at n=60 is ~10-30 %, so it overlaps theirs only at the edge. Reported as a rate difference, not a refutation.
**Also pushed**: NOTE_go_nodes_budget.md (the malformed `go nodes` item, re-verified on the PC build under full PC20) and the early FINAL block with the MultiPV per-node table as its headline.
**Next command**: `cd /agent/repos/dwqww && bash forge-combo29/swarm/30/read_board.sh /tmp/board12` then the next unconfirmed finding.

## Mon Nov 16 11:22:16 PM UTC 2026

**30-C27 — my headline number is now confirmed on a SECOND position**, so it is not position-specific: on a normal middlegame (`r1bqk2r/...`), PC r15 + PC20, Threads 1, go depth 8: MultiPV 3 gives 8,806 nodes at every Hash with **3.7 / 33.3 / 187.1 / 366.3 us per node** (Hash 16/256/1024/2048) while MultiPV 1 gives 4,515 nodes with **0.9 / 0.9 / 1.8 / 0.9** — flat. At 2 GB the MultiPV-3 price is 366 us/node here vs 204 us on P1, i.e. the penalty is if anything larger on a middlegame.
**Next command**: `cd /agent/repos/dwqww && bash forge-combo29/swarm/30/read_board.sh /tmp/board12` then the next unconfirmed finding.

## Mon Nov 16 11:23:07 PM UTC 2026

**30-F47 + 30-C28: the MultiPV fault is now ROOT-CAUSED AND PROVEN.** Cause: src/search.cpp:2879 calls $alt_shared->tt.clear()$ inside the per-line loop at :2851, once per extra PV line per depth, and $clear()$ walks every cluster in the table. Proof: at Hash 1024 MB, ms per table-clear stays in **95-141 across 8 cells** (MPV2/MPV3 x depths 6/8/10/12) — i.e. one 1 GB zeroing per call, independent of depth and line count. us/node falls with depth (415 -> 36) because nodes grow faster than the fixed per-depth cost. Harm at depth 12: MPV1 18.5 ms/21,877 nodes vs MPV3 2,274 ms/62,578 nodes = **123x slower**. Repair path: the function already keeps $generation_$/$epoch_$, so bumping a generation instead of writing every cluster removes the cost.
**Next command**: `cd /agent/repos/dwqww && bash forge-combo29/swarm/30/read_board.sh /tmp/board12` then the next unconfirmed finding.

## Mon Nov 16 11:24:01 PM UTC 2026

**30-C29/30-C30: the generation-bump variant built and measured at the coordinator's request.** Payoff **2.1x-4.9x** on the same 8 cells (MPV3 depth 12: 2,274.4 ms -> 461.1 ms) and the per-depth growth is GONE (flat ~400-460 ms). **BUT bench 16 moved: 3,030,186 vs the required 3,024,920 (+5,266 nodes)** — so per instruction I stopped and did not tune; it is reported as a measured experiment, not a repair. Reason it moved (30-C30): the generation field is 5 bits and $new_search()$ already bumps it; $clear()$'s extra job is making entries UNPROBEABLE, which a bump cannot express. Patch text at check6/ttclear_gen_bump.patch.txt.
**Next command**: write the real FINAL block at the 10:18 UTC close.

## Mon Nov 16 11:25 UTC 2026 — FINAL (see the note at the top: the run continues to 2026-11-17 10:18 UTC; this is the block for tonight's close, and a fresh FINAL will be written at the real deadline)

### HEADLINE — the per-node price of MultiPV, and the one-line repair that removes it

At **MultiPV 1** the per-node cost is **FLAT at 0.8 microseconds at every Hash size**. At **MultiPV 3**
it climbs with the table and reaches **203.9 us/node** on a 2 GB hash (366 us on a second position) —
**for a byte-identical search tree**. Cause: `src/search.cpp:2879` calls `alt_shared->tt.clear()`
inside the per-PV-line loop opened at `:2851`, so the **whole table is zeroed once per extra line per
depth**, and `TranspositionTable::clear()` walks every cluster. Proof: wall time per clear is
**95–141 ms across eight cells** (MultiPV 2/3 x depths 6/8/10/12), independent of depth and line
count — what a full-table zeroing predicts and a search-side slowdown cannot.

| `go depth 8`, Threads 1, same 16,642 nodes | Hash 16 | 64 | 256 | 1024 | 2048 |
|---|---|---|---|---|---|
| MultiPV 3 — us/node | 2.0 | 4.7 | 17.2 | 117.5 | **203.9** |
| MultiPV 1 — us/node | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 |

**THE DESIGN NOTE (the actionable repair, as measured — not the one-liner, which I ruled out).**
Stop the MultiPV loop calling `clear()` at all, and let each alternative line keep its own table
handle: the alternative lines **already own a separate table** (`alt_shared = make_unique<SharedSearchState>(hash_mb)` at `src/search.cpp:2730`), and every search already calls `tt.new_search()`,
which bumps the generation. The per-line `clear()` is therefore redundant full-table work. I built
exactly that — delete the single statement at `:2879` — and it **keeps all four honesty pins**
(312866 / 862329 / 3024920 / 4865609) while making the same eight cells **2.0x–4.2x faster**
(MultiPV 3, depth 12: 2,274.4 ms → 542.6 ms; the per-depth growth is gone, flat ~400–540 ms), and
MultiPV still returns **three distinct, legal lines** (the `search_moves` narrowing at `:2871` is what
keeps them distinct, not the clear). Patch: `check6/ttclear_no_alt_clear.patch.txt`.
**The one-line alternative I rejected:** replacing `clear()`'s body with a generation bump is
2.1x–4.9x faster but moves **bench 16 to 3,030,186** (+5,266 nodes) — a generation bump makes entries
*old*, not *unprobeable*, which a 5-bit generation cannot express; recorded as an experiment, not a
repair (`30-C29`, `30-C30`).

### My finds, with state

1. **30-C31/C32 + F47/C28** — the MultiPV fault and its adoptable repair, above. **Open** (needs a seat to confirm the patch).
2. **30-F25/F26/F28 + C25** — a malformed `go nodes` line (`-1`, `xyz`, `nodes depth 5`) is treated as **no node limit**: 207,603,225 nodes, no move after 120 s; repaired on the PC build, all three answering in 0.00 s under FULL PC20. **Open for independent confirmation.** `NOTE_go_nodes_budget.md` states the rule: never send a node budget not validated as a positive integer.
3. **30-C18/C19** — seat 20's 0-node answer: **CONFIRMED** (3/36 under load, Hash 2048/MPV 3, same moves).
4. **30-C1/F7/F8** — halfmove-100 mate missed, side-blind: **CONFIRMED by seat 21 (21-C3)**; repaired on the PC build (30-C4).
5. **30-F33/F34/F38** — six lone-king boards never find a provable mate at depth 24 on the base tree (5 of 6 KRvK); the PC build finds all six, twice each. **Partly confirmed** (a seat's S-C13, two of six).
6. **30-F29/F31/F36/F40** — mate-reporting rates: base 16/40 (d12) → 21/40 (d16), a plateau; PC 27/40 → 31/40. **Open.**
7. **30-F35/F43** — the fifty-move draw is invisible below depth 9 (4.85 M nodes). **CONFIRMED by seat 17 (S-C15).**
8. **30-C26/F46** — seat 23's budget sensitivity: **phenomenon confirmed**, 11/60 = 18.3 % on my own quiet positions (theirs 27–30 %).
9. **30-F13/14/15/17/F27/C11/C13** — methodology: my original job-2 numbers were contaminated by 19-F12 and are **retracted and superseded**; honesty and checks 1–2 unaffected; `ucinewgame` restores cold exactly (three-way control, both builds).
10. **30-F1..F5, F10..F12** — helper recounts: deepseek6's long56 report contradicts its own raw file and its legality check is dead code (its result is nonetheless true); glmflash5's 15 numbers exact, two matches share identical opening sets.

### My confirmations of other seats (each with my own harness, raw files, build and settings named)
**08-F18** (+ the OwnBook trap, 30-F39) · **24-F14**, **24-F16** (I applied and built the patch) ·
**15-F24**, **15-F25** (built the split fix; verified under S14 and PC20 with pins unchanged) ·
**15-F30** (`nodes` a hard ceiling 0/15, `softnodes` overshoots 14/15 to +118.8 %).

Reports: `REPORT_job2.md`, `REPORT_job3.md`, `REPORT_check1.md`, `REPORT_check2.md`,
`REPORT_pc_multipv.md`, `REPORT_pc_repairs.md`, `NOTE_go_nodes_budget.md`.

## Mon Nov 16 11:25:54 PM UTC 2026

**30-C33: patch packaged for review.** `ttclear_no_alt_clear.patch.txt` (sha256 50cc86d3...) now carries a header stating the reviewer check — all four honesty pins unchanged, MultiPV 3 emitting three distinct legal first moves, tie-order being pre-existing std::sort behaviour, and no other tt.clear() call site touched — plus the measured payoff. Re-verified after the rewrite: `patch -p1 --fuzz=0` rc=0 on a clean PC r15 copy, and the remaining call sites at :3048/:3060 are untouched.
**Next command**: build the patched tree and check ONE thing my measurements do not cover — that MultiPV 3 at a real match budget (go nodes 2000) now reaches a sensible depth instead of depth 1, and that MultiPV 1 results are unchanged.

## Mon Nov 16 11:26:50 PM UTC 2026

**Important qualification, found after the patch was packaged (30-F48/F49)**: the repair fixes the per-depth COST but NOT the clock symptom. At Hash 2048 / MPV 3, `go wtime 5000` is depth 1 on both builds. The real owner-facing number is a Hash THRESHOLD: under a clock at MPV 3, Hash 16 MB -> depth 14 / 280,100 nodes, 256 MB -> depth 7, **512 MB -> depth 1 / 220 nodes** while wall time RISES (276 -> 535 -> 1,310 ms) with 10.5 GB free — table work, not memory pressure. Rule: **at MultiPV > 1 keep Hash at 256 MB or below** (holds on shipped and patched). 30-C34/30-C35 also record that both MultiPV 1 controls are provably identical between builds (3 repeats).
**Next command**: `cd /agent/repos/dwqww && bash forge-combo29/swarm/30/read_board.sh /tmp/board13` for the next unconfirmed finding.

## Mon Nov 16 11:28 UTC 2026 — FINAL (tonight's close; the run continues to 2026-11-17 10:18 UTC and a fresh FINAL will be written then)

### HEADLINE — the Hash setting that decides whether MultiPV analysis works at all

**This is the table to look at before an analysis session.** PC r15, MultiPV 3, `go wtime 5000`,
Threads 1, one middlegame, **5 fresh processes per cell** (every setoption confirmed by `readyok`):

| Hash | SHIPPED build: depth | nodes (5 runs) | wall ms | PATCHED build: depth | nodes | wall ms |
|---|---|---|---|---|---|---|
| 16 MB | **14, 14, 14** | 280,100 flat | 268–273 | 14, 14, 14 | 157,966 flat | 169–170 |
| 256 MB | **depth varies run to run** ({7, 11} over 8 runs; {7, 5, 10} over 3) | 5,395 – 47,818 (**8.9x spread**) | 239–346 | **13, 13, 13, 13, 13, 13, 13, 13** | 106,863 flat, 8 of 8 | 215–226 |
| 512 MB | **1, 1, 1, 1, 1** | 220 flat | 267–274 | **12, 12, 12, 12, 12** | 71,070 flat | 271–274 |
| 2048 MB | **1, 1, 1, 1, 1** | 143–220 | 1310 | 1, 1, 1, 1, 1 | 202 flat | ~390 |

Read it this way: on the **shipped** build, MultiPV 3 loses **13 plies** between 256 MB and 512 MB
and never recovers, while the **wall time RISES** as the node count collapses (268 ms at depth 14,
1,310 ms at depth 1) with 10.5 GB free — it is time burned zeroing the table, not memory pressure.
**Practical rule for the shipped engine: at MultiPV > 1 keep Hash at 256 MB or below** (and expect
instability right at 256: the depth varies run to run and the node count by up to ~9x on
identical runs). **On the patched build the ceiling rises
to 512 MB (depth 12, stable)** and above it MultiPV > 1 still collapses on a clock.

### REPRODUCIBILITY — the gain that matters more than the speed

Near the collapse boundary the shipped engine is **not reproducible on identical runs**, and the patch
fixes that. 8 fresh processes per cell, MultiPV 3, `go wtime 5000`, Threads 1, PC20:

| Hash | SHIPPED build | PATCHED build |
|---|---|---|
| 256 MB | depths **{7, 11}** across 8 identical runs; nodes **5,395 to 47,818 = 8.9x spread** (5, 7, 10 and 11 were all seen at this Hash) | **depth 13, exactly 106,863 nodes, 8 of 8 runs** |
| 512 MB | depth 1, 220 nodes — consistently bad | **depth 12, exactly 71,070 nodes, 8 of 8** |
| 2048 MB | nodes 143–220 (1.5x) at depth 1 | 202 flat at depth 1 |

Two identical searches on the shipped build at 256 MB can differ by **nine times the work and several
plies of depth**. For a match, an analysis run or a regression test at those settings, **exact
reproducibility is worth more than the 2–4x speed**: a result you cannot repeat is not a measurement.
That is the strongest argument for the patch, and it is independent of the timing win.

### THE PATCH — worth shipping on its measured merits, with its scope stated

One statement deleted at `src/search.cpp:2879`: the per-PV-line `alt_shared->tt.clear()`, which walked
every cluster once per extra line per depth. It is redundant because the alternative lines already own
a separate table (`alt_shared = make_unique<SharedSearchState>(hash_mb)` at `:2730`) and every search
calls `tt.new_search()`.
- **Passes the full honesty gate:** bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all unchanged.
- **Measured speed:** the same eight cells at Hash 1024 are **2.0x–4.2x** faster (MultiPV 3, depth 12: 2,274.4 ms → 542.6 ms), with the per-depth growth gone.
- **Raises the usable Hash ceiling** from ~256 MB to 512 MB (30-C36).
- **Leaves MultiPV 1 provably untouched:** identical score/nodes/bestmove, 3 repeats (30-C35).
- **Correctness:** MultiPV still returns three distinct, legal first moves (30-C32).
- **Not claimed:** it does not make MultiPV > 1 usable at 2 GB under a clock (still depth 1).
- Patch text with a reviewer checklist in its header: `check6/ttclear_no_alt_clear.patch.txt` (`patch -p1 --fuzz=0`, rc=0 verified).
- **Ruled out:** the tempting one-liner (replace `clear()`'s body with a generation bump) is 2.1x–4.9x faster but **moves bench 16 to 3,030,186** — a generation bump makes entries *old*, not *unprobeable*, which a 5-bit generation cannot express (30-C29/C30).

### My finds, with state
1. **30-F48/C36/C37/C50 + F47/C28/C31/C32 + C44/F54** — the MultiPV/Hash item above. **NECESSITY CONFIRMED, SUFFICIENCY REFUTED** by another seat on the PC r15 tree (pins unchanged): direction right, magnitude short — Hash 64 goes 9 plies @183 nodes/ms -> 13 plies @583 (3.2x, depth restored), Hash 256 goes 4 plies @2 -> 7 plies @29 (14x, three plies recovered), but 583 falls to 29 at 256 and 0 at 1024, never reaching MultiPV 1's ~1,500. I then tested the obvious residual suspect and RULED IT OUT: removing the per-line `alt_worker->clear()` too (pins still unchanged) gains only ~7 % at Hash 16 and is slightly worse at 64/256 (30-C44). The residual is **proportional to the table at byte-identical node counts** — `go nodes 20000` gives 10,877 nodes at every Hash while wall time runs 21.7/40.7/108.9/577.8/967.8 ms = 2.0 to 89.0 us/node (30-F54) — so at least one more whole-table pass per search remains, not page faults (warm-up does not help) and not hashfull() (samples 1,000 clusters). Needs a profiler. Repair now **INDEPENDENTLY CONFIRMED by seat 20 (S-C35, 30-N2)**: its own builds and harness reproduced my figures **to the node** (71,070 and 106,863), the same instability at 256 MB, all four pins unchanged, and MultiPV 1 byte-identical (depth 17 / 288,912, 3 of 3). PC r15, PC20, Threads 1.
2. **30-F25/F26/F28 + C25** — malformed `go nodes` line = **no node limit** (207,603,225 nodes, no move); repaired on the PC build, all three answering in 0.00 s under full PC20. **Open.** `NOTE_go_nodes_budget.md`: a harness must never send a node budget not validated as a positive integer.
3. **30-C18/C19** — seat 20's 0-node answer: **CONFIRMED** (3/36 under load, Hash 2048/MPV 3).
4. **30-C1/F7/F8** — halfmove-100 mate missed, side-blind: **CONFIRMED by seat 21 (21-C3)**; repaired on the PC build.
5. **30-F33/F34/F38** — six lone-king boards never find a provable mate at depth 24 (5 of 6 KRvK); the PC build finds all six. **Partly confirmed** (a seat's S-C13).
6. **30-F29/F31/F36/F40** — mate-reporting rates: base plateaus 16/40 → 21/40; PC 27/40 → 31/40. **Open.**
7. **30-F35/F43** — the fifty-move draw is invisible below depth 9. **CONFIRMED by seat 17 (S-C15).**
8. **30-C26/F46** — seat 23's budget sensitivity: confirmed, 11/60 = 18.3 % on my own positions (theirs 27–30 %).
9. **30-F13/14/15/17/F27/C11/C13** — methodology: my job-2 numbers were contaminated by 19-F12 and are **retracted and superseded**; `ucinewgame` restores cold exactly (three-way control).
10. **30-F1..F5, F10..F12** — helper recounts: deepseek6's long56 report contradicts its own raw file and its legality check is dead code (result nonetheless true); glmflash5's 15 numbers exact.

### My confirmations of other seats
**08-F18** (+the OwnBook trap) · **24-F14**, **24-F16** (applied and built the patch) · **15-F24**, **15-F25** (built the split fix, both settings, pins unchanged) · **15-F30** (`nodes` hard ceiling 0/15, `softnodes` overshoots 14/15).
Reports: `REPORT_job2.md`, `REPORT_job3.md`, `REPORT_check1.md`, `REPORT_check2.md`,
`REPORT_pc_multipv.md`, `REPORT_pc_repairs.md`, `NOTE_go_nodes_budget.md`.

## Mon Nov 16 11:29:39 PM UTC 2026

**30-F50/C38: reproducibility stated separately and prominently**, now its own section in the FINAL ahead of the patch section and in the patch header. 8 fresh processes per cell: at Hash 256 the SHIPPED build gives depths **{7,11}** with nodes **5,395..47,818 (8.9x spread)** across identical runs, while the PATCHED build gives **depth 13 / exactly 106,863 nodes on 8 of 8**; at Hash 512 shipped is depth 1 (5/5) vs patched depth 12 / 71,070 (8/8). Two identical searches differing by 9x in work cannot be a measurement — that is the strongest argument for the patch and it is independent of the speed. Patch re-verified `patch -p1 --fuzz=0` rc=0 after the header edit (sha256 updated).
**Next command**: continue the cycle toward 10:18 UTC; next is the board read for an unconfirmed finding of another seat.

## Mon Nov 16 11:30:23 PM UTC 2026 — CLOSE

**30-C39: the narrowed reproducibility claim now reads identically everywhere** — FINDINGS 30-C37/30-F50, the FINAL table and its reproducibility section, and the patch header. Verified by grep that no "14x"/"fourteenfold" figure survives anywhere in my folder, so the vivid number cannot be quoted back as exact. The claim: on identical runs the shipped build's DEPTH VARIES and node count varies up to ~9x (Hash 256 MB, 8 runs: depths {7,11}, nodes 5,395-47,818; 3-run sample {7,5,10}; union {5,7,10,11}), while the patched build gives depth 13 / exactly 106,863 nodes on 8 of 8.

**Where the thread landed**: defect found and proved (95-141 ms per table clear, constant across 8 cells), tempting one-liner ruled out on the honesty gate, real one-statement fix measured (2.0-4.2x, raises the Hash ceiling 256 MB -> 512 MB, MultiPV 1 provably untouched), scope corrected twice, and reproducibility — the number that decides whether any measurement at those settings is valid — stated ahead of speed.

## Mon Nov 16 11:37:34 PM UTC 2026

**30-N2: the MultiPV repair is INDEPENDENTLY CONFIRMED — seat 20's S-C35**, its own builds (both with -DFORGE_MATE_ALPHA_GUARD=1) and its own harness, 5 fresh processes per cell. It reproduced my figures **to the node**: Hash 512 patched depth 12 / **71,070** nodes 5/5 (shipped depth 1 / 220); Hash 256 shipped depths **[11,11,11,7,11]** / nodes **[47,818x3, 5,395, 47,818]** — the same instability and the same range — vs patched depth 13 / **106,863** 5/5; all four honesty pins unchanged; and the control that matters, **MultiPV 1 byte-identical (depth 17 / 288,912, 3 of 3 each)**. I read its evidence file before recording it, and the confirmation (with its path) is now in the patch header. The FINDINGS item therefore moves from OPEN to CONFIRMED — it meets the brief's rule that a find counts when another seat confirms it with its own harness.

**Next command**: continue the cycle toward 10:18 UTC — next board read for another seat's unconfirmed finding.

## Mon Nov 16 11:43:53 PM UTC 2026

**New thread checked and the answer is more interesting than a simple confirm/refute.** Seat 27's S-F12 said the clock is ignored when Black is to move. My first pass REFUTED it: on its own position the clock is obeyed monotonically (wtime 0 -> depth 1/39 nodes; wtime 3000 -> depth 22/178,324), and on 12 positions x 4 clocks x 2 builds, 0 had all clocks agreeing. But then I tested the variants, found the real cause, and PARTLY VINDICATED it: **with `btime` omitted, `go wtime 0` and `go wtime 1000` are byte-identical — depth 45, 45,481,815 nodes, 30 s, no stop — on BOTH builds.** A one-sided clock is not a short clock, it is NO clock. So seat 27 measured a real and dangerous behaviour with the wrong explanation. 30-C40 corrected in place (its BLACK-ness discriminator is what fails), 30-C41/C42/F53 carry the mechanism and the rule: a harness must always send BOTH clocks.
**Two harness rules now on record, same shape**: never send a node budget that is not a validated positive integer (NOTE_go_nodes_budget.md), and never send a `go` line with only one side's clock (30-F52/F53). Both produce a 30-180 s runaway instead of a move.
**Next command**: continue the cycle toward 10:18 UTC; next is another board read.

## Mon Nov 16 11:47:00 PM UTC 2026

**Both requested items done.** (1) The one-sided-clock finding now LEADS with the sentence: "A one-sided clock is not a short clock, it is no clock" — in 30-F52 and in 30-C42. (2) New shared page `NOTE_two_silent_runaways.md` pairs both traps with a side-by-side table, the identical-node-count evidence (`wtime 0` and `wtime 1000` both 26,264,563 on PC r15 / 41,641,416 on base), a 'why they belong together' table, and the rule that both are harness traps with the fix in the driver. It is also now item 2b in the FINAL inventory.
**One script reproduces both**: `python3 check11/runaway_traps.py out_traps 20` — 8 rows, both builds, all three controls answering.
**Next command**: continue toward 10:18 UTC; next board read for an unconfirmed finding.

## Mon Nov 16 11:48:52 PM UTC 2026

**Residual tested and the obvious suspect RULED OUT.** Built the C31 tree also without `alt_worker->clear()` (C44): pins all unchanged (312866/862329/3024920/4865609) but it gains only ~7% at Hash 16 and is slightly WORSE at 64/256 (C31 615/393/149/40 vs C44 658/358/128/23 nodes/ms). So the hypothesis now in the patch note was wrong and is corrected there. **What the residual actually is (30-F54)**: at `go nodes 20000` the tree is byte-identical — 10,877 nodes at EVERY Hash — while wall time runs 21.7/40.7/108.9/577.8/967.8 ms for Hash 16/64/256/1024/2048 = **2.0 to 89.0 us/node**. So there is at least one more whole-table pass per search; not page faults (warm-up in the same process does not help) and not hashfull() (samples 1,000 clusters). Needs a profiler, which I cannot finish in this window.
**Scopes now recorded**: patch = NECESSARY, NOT SUFFICIENT; pins hold; patches for both the C31 and C44 variants are text files in check6/; patch re-verified `patch -p1 --fuzz=0` rc=0 (sha256 76dce421...).

## Mon Nov 16 11:49:41 PM UTC 2026

**Both requested items held, and made durable in the files themselves (30-C45).** C31 is labelled "PATCH — SHIP THIS ONE" and cross-links its paired negative control; C44 is labelled "EXPERIMENT ONLY — DO NOT SHIP THIS PATCH" and states that it refuted its own motivation (pins held, ~7% gain at Hash 16, worse at 64/256), naming C31 as what to ship instead. I also found the third patch (the rejected generation-bump) had no label and absolute paths, so it now reads "REJECTED — DO NOT SHIP (it fails the honesty gate)" with bench 16 = 3,030,186 named. All three use repo-relative labels and each was re-tested `patch -p1 --fuzz=0` rc=0; C44 was confirmed to apply on top of C31 and to leave its call commented out.
**The bound stays a bound**: 30-F54 says at least one more whole-table pass per search, proven by byte-identical node counts (10,877 at every Hash) with wall time 21.7 -> 967.8 ms, page faults and hashfull() eliminated, and explicitly NOT attributed to a named suspect. Needs a profiler.

## Mon Nov 16 11:51:35 PM UTC 2026

**Reconciled with seat 27's withdrawal (30-C46).** It retracted its "clock swap" claim and attributed its own anomaly to `OwnBook` being left on — that retraction is correct and I agree with it. But the runaway I found is a DIFFERENT fact and survives with `OwnBook false` explicitly set: on its Black-to-move board, `go wtime 0` -> no bestmove, depth 42, **27,302,675 nodes**, and `go wtime 1000` -> the SAME 27,302,675 nodes, while Black's OWN clock is obeyed properly (`go btime 0` -> depth 1/39 nodes/4.1 ms; `go btime 1000` -> depth 12/27,183 nodes/24.4 ms). So the precise rule is: **omit the mover's own clock and the search is unbounded** — a malformed `go` line, not a clock bug. NOTE_two_silent_runaways.md updated with this precision and the reconciliation note (both of us were caught by harness details, which is the page's point).
**Next command**: continue at cadence; next board read.

## Mon Nov 16 11:53:02 PM UTC 2026

**Two confirmations of seat 13 plus one owner-actionable consequence.** 30-C47 CONFIRMS 13-F19: clock allocation is depth-step quantised on BOTH builds — PC `wtime 8000` and `10000` give the SAME 854,603 nodes, `15000` and `20000` the SAME 1,425,298, and the fraction of clock used FALLS from 6.3% at 8 s to 4.1% at 20 s; the base tree gives identical searches for 8000/10000/12000/15000. 30-C48 CONFIRMS the `movestogo 0` anomaly (32% vs 2.2% with it omitted) and shows `movestogo 40` is the smallest allocation. **30-F55 is the practical one: at the owner's own match clock, `movestogo 0` quadruples the time spent — 2,023 ms of a 6,060 ms budget versus 498 ms — 3/3 identical. The safe match line at his control is `go wtime 6000 btime 6000 winc 60 binc 60` with NO movestogo.**

## Mon Nov 16 11:54:15 PM UTC 2026

**Requested item 2 done, and item 1 exposed an error in my own rule.** The runaways page now OPENS with the two rules as two lines. But while verifying the combined safe line I found my "always send both clocks" phrasing was too broad: on a WHITE-to-move board `go wtime 6000` alone is the mover's OWN clock and works normally (depth 16 / 223,639 nodes / 136 ms), while on a BLACK-to-move board `go wtime 6000` alone (wrong side) runs to **26,264,563 nodes with no bestmove** and `go btime 6000` alone works (depth 26 / 328,863 / 160 ms). So the precise rule is **never send the wrong side's clock ALONE** — recorded as 30-C49 and corrected in the page, which now also carries `movestogo 0` as a third trap with the owner-clock numbers (498 ms -> 2,023 ms of a 6,060 ms budget).
**Item 1 also satisfied**: the depth-step plateau is confirmed on PC r15 AND on the base tree (8000/10000/12000/15000 all give identical 675,454 nodes there), so it is a property of the allocator, not of the new switches.

## Mon Nov 16 11:54:56 PM UTC 2026

**New confirmation plus a methodological consequence for the match data.** 30-C51 CONFIRMS 16-F27/16-F29 and strengthens it: at a FIXED depth with NO clock, 5 self-play games from startpos are **byte-identical** (1 distinct game, not 3-of-10), while 5 different starts give 5 distinct games — so the duplication is purely the fixed starting point and the advice "vary the openings" is exactly right. **30-F56 is the consequence**: a game from a given start is reproducible ACROSS PROCESSES (identical move-list SHA twice each), so a 2,000-game fixed-depth match built as 1,000 openings x 2 colours contains **1,000 independent games observed twice**, not 2,000 independent samples — valid as a paired design, but any interval treating n = 2,000 as independent is too narrow, and re-running the same match adds no information. That applies to glmflash5's 1,000 pairs / 2,000 games figure I recounted in job 3.

## Mon Nov 16 11:55:23 PM UTC 2026

**Item 1 done and verified, not just asserted.** 30-F56 now carries a bold paragraph inside the finding: "THIS DOES NOT INVALIDATE THE PUBLISHED INTERVALS" — the pooled pair-score intervals I recounted are computed over PAIRS by the brief's formula, the pair is the independent unit, so those numbers stand unchanged; the only correction is that "2,000" is not 2,000 independent observations, and the honest phrasing is "1,000 independent pairs (2,000 games)". **30-C52 proves it**: recomputing M55 both ways gives, over 1,000 pairs, Elo +16.52 / sd 6.061 / CI **[+4.64, +28.40]** — exactly the published figure — while treating 2,000 games as independent would give CI [+3.80, +29.23], a different interval. So the reports already use the correct unit and nothing is retracted.

## Mon Nov 16 11:56:20 PM UTC 2026

**30-C53: 16-F28 CONFIRMED, and the inconsistency is worse than reported.** One process, startpos, Threads 1, PC20, both clocks always present, clock debited after each move: **12 moves, 0 overruns**, clock falling 6000 -> 3394 ms — but per-move search time ranged **92.5 to 509.9 ms, a 5.51x ratio** (seat 16 measured 2.51x) with nodes 170,304 to 896,277. The engine's own `time` field matches my wall clock within 2 ms on every move (90-508 vs 92.5-509.9), so it is not a measurement artefact. Practical reading: **"a 6 s clock" buys between 1.5% and 8.5% of the clock depending on the move** — consistent with the depth-step quantisation in 30-C47, where the allocation moves in whole-iteration steps rather than tracking the clock.

## Tue Nov 17 12:04:08 AM UTC 2026

**30-C54: 19-F59 CONFIRMED, and a one-ply disagreement between us resolved in its favour.** Position `6k1/8/5K2/8/6r1/8/8/8 w`, PC r15 + PC20, Threads 1: depth 12/16/20 all give **`f6e7` cp -490** (the faster death), depth 24 gives **`f6f5`** — the longest defence — exactly as it says. It published `mate -15`, I first measured **`mate -16`** at depth 24. I repeated depth 24 three times (identical, 5,923,619 nodes) and went deeper: **depth 26 -> `mate -15`, depth 28 -> `mate -15`**. So my -16 is a horizon artefact of depth 24 and its -15 is the correct value; both measurements are consistent, its number is the more accurate, and mine identifies the depth at which it becomes accurate. Recorded that way.

## Tue Nov 17 12:04:26 AM UTC 2026

**Item 1 recorded as 30-F57** — a check that CONFIRMS a number more precisely than its author did is itself a result, not a null outcome, with 30-C54 as the exemplar: seat 19 published `mate -15`, I first got `-16`; repeating its depth (3/3 identical at 5,923,619 nodes) then searching deeper (26, 28 -> `-15`) shows it was right and my figure had the horizon. What the check added is the boundary neither of us had: **the horizon at which the wrong value appears (depth 24) and the depth that must be passed to see the right one** — worth stating for Opus, because a confirmation giving a claim's precise boundary is more useful than a bare CONFIRMS.
**Item 2**: the complete sentence is now in 30-C54 verbatim — "-16 at depth 24 is a horizon artefact, -15 is correct, and the search needs to pass depth 24 to see it."

## Tue Nov 17 12:05:12 AM UTC 2026

**30-C55: 29-F44 CONFIRMED out of sample.** PC r15, depth 10, Threads 1, Hash 16, 40 mid-game positions from random games (SEED 3011 — a different source from theirs): **S14 and PC20 chose the same bestmove in 36 of 40 = 90.0%**, against their 83/100 = 83.0%. Both are small-sample binomial estimates with comfortably overlapping intervals, so confirmation rather than discrepancy — the four switches change the move about a tenth of the time. **30-F58 is the honest caveat**: the 4 disagreements had score gaps of 87, 19, 203 and 15 cp (median 87), so two are clear near-ties but ONE is 203 cp at a +1744/+1541 winning score — "PC20 only changes near-tied moves" is not supportable from my sample; adjudicating that one would need a deeper reference search, which I did not run.

## Tue Nov 17 12:14:10 AM UTC 2026 — RETRACTION

**30-C57: my 'PC20 picks f3g3' result was MY HARNESS BUG and seat 20 was right.** Provenance it asked for: exe sha256 **068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4 — IDENTICAL to seat 20's**, `id name Chess Engine Forge 6.4.24 candidate`, Hash 64 MB (not the variable: `f3g3` reproduces at Hash 16/32/64 alike), FEN `.../RN2KB2 w Q - 0 18` (the `RN2KB1` in my line was a typo, now fixed). **The bug**: `settle_pos29.py` takes a settings LIST; I passed `PC20EXTRA` — the six extra switches — alone, so my 'PC20 arm' was six switches on top of DEFAULTS, never S14. Three-way proof on position 29 d12: six-over-defaults -> `f3g3` cp 1627 (what I published); S14 -> `f3g2` cp 1838; **TRUE PC20 -> `f3g2` cp 1790** (what seat 20 measured). **Withdrawn**: "PC20 prefers f3g3 and needs depth 18". **Stands**: `f3g2` outscores `f3g3` by ~200 cp in isolation, so the move-quality conclusion holds. REPORT_check17.md is marked partly withdrawn; 30-F60 records the method lesson; **30-C58 adds an arm-sanity guard** that now REFUSES a PC20 arm built from the six switches alone, tested both directions.

## Tue Nov 17 12:21:18 AM UTC 2026

**check18 re-run correctly (check18b) and two more of my own faults caught.** The corrected run prints provenance (sha256 068f0927…, `id name Chess Engine Forge 6.4.24 candidate`, **S14 arm 16 options / PC20 arm 22 options**, asserted in code). Two faults in the re-run itself: (a) I had copied MY OWN `RN2KB1` typo into the CASES list, so position 29's FEN was invalid, the engine REFUSED it and it scored `cp 0` everywhere — which my classifier read as a perfect near-tie; (b) my new FEN gate crashed on `LegalMoveGenerator has no len()`, i.e. the gate refused to run rather than emitting numbers. **Answers to the coordinator's question with true arms**: pos 13 MIXED (leader flips, genuinely unresolved), pos 24 NEAR-TIE (45 cp), **pos 29 `f3g2` leads in ALL 8 cells by 100-239 cp**, pos 35 MIXED (19-204). So the disagreement is **not typical and not unique**: one genuine, one near-tie, two unresolved. **30-C60**: my classifier labelled pos 29 'MIXED' only because my threshold was '>100' and the minimum gap is exactly 100 — the leader never changes, and I record both the label and the data rather than re-labelling silently.
**30-F61 adopts seat 20's framing**: a config wrong by construction looks exactly like a config that is right, so finding lines now name the construction and the option count, not the regime name.

## Tue Nov 17 12:21:56 AM UTC 2026

**30-F62 — the sharpest harness fault of the night, with the exact symptom.** A REFUSED FEN is silently turned into a "perfect tie" by `searchmoves`: `position fen <INVALID>` answers `info string invalid FEN: invalid FEN rank`, KEEPS the previous (empty) board, and then `go depth 12 searchmoves f3g2` emits `info depth 1 seldepth 1 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv` + `bestmove 0000` — **byte-identical to a real drawn-position evaluation**, which is exactly how check18 scored position 29 as cp 0 everywhere. With plain `go depth` there is no `info depth` line at all (visibly empty). Control: the valid FEN gives `info depth 12 ... bestmove d2d3`. **Rules**: grep for `invalid FEN` and abort; treat `cp 0` + `nodes 0` as an UNSEARCHED ROOT, not an evaluation. **30-C61**: trap 4 is on NOTE_two_silent_runaways.md with the transcript, and I verified the gate by reintroducing the bad FEN — it now refuses with "expected 8 columns per row". **30-C60** still records both my threshold label and the eight rows rather than re-labelling.

## Tue Nov 17 12:22:34 AM UTC 2026

**30-F63: my own gate verification nearly gave a FALSE PASS — the same class of fault I was writing up.** First attempt ran the gate test from /tmp, so it exited 1 with `FileNotFoundError: .../check17/settle_pos29.py` — a relative-path failure, NOT the gate. "Exit non-zero" would have looked like success to a careless reader; I caught it only because the message named a file instead of a FEN, and re-ran in place where it correctly refused with "expected 8 columns per row". **The trustworthy signal is not the exit code but the message naming the specific planted fault.** Recorded on the shared page as a short section, "How to know a guard actually fired", beside the trap it verifies.
**Both requested items are on the page**: trap 4 with the verbatim transcript and the control, and the two rules (grep for `invalid FEN` and abort; treat `cp 0` + `nodes 0` as an unsearched root).

## Tue Nov 17 12:23:28 AM UTC 2026

**30-C62/F64 REFUTES 28-F43, and 30-C63 explains why seat 28 and I differ.** Same position and clock: **solo -> `d2d3` depth 18 / 854,603 nodes** (3/3 identical) versus **under 4 busy processes -> `e1g1` depth 15 / 205,048 nodes** (3/3 identical, wall time FALLING to ~200 ms because fewer iterations fit). So a loaded machine plays DIFFERENT CHESS, not merely slower. **The gradient is the key**: 0, 1 and 2 hogs change NOTHING (identical nodes), and only **4 hogs on a 4-core box** flips it — a threshold at full saturation. That is why seat 28's busy loop saw stability: if theirs was a single process, my 1-hog cell shows no change either. Practical rule: a light load is safe; a fully saturated box silently weakens the engine by three plies.

## Tue Nov 17 12:23:48 AM UTC 2026

**Both requested items applied.** 30-F64 now LEADS with **"A depth-limited engine under saturation is WEAKER, not just slower"** and carries the full hog-count ladder with BOTH runs per cell: 0 hogs -> `d2d3` d18 / 854,603 / 505.6 and 497.5 ms; 1 hog -> identical; 2 hogs -> identical; **4 hogs -> `e1g1` d15 / 205,048 / 170.1 and 244.5 ms**. 30-C63 carries the same lead sentence so the threshold and the conclusion read together.

## Tue Nov 17 12:34:50 AM UTC 2026

**Both items recorded.** 30-F67 gives the piped-`quit` pattern its own line with **all five sightings tonight, every one of them mine**, each tied to its file: check1's first version (a "missed mate" at every counter including 0, exposed by disagreeing with seat 01's hm-0 row), the job-2 runner (772/2,000 sequences), 30 of 30 probes in pc/quit_fabrication.py (29 with a DIFFERENT move), the 0 ms-only window in pc/quit_timing.py, and today's `bestmove e7a3` with no score line on seat 10's board. **The common signature is "no info line before the bestmove", not "0 nodes"** — and in the mate-in-1 case the fabricated move was the LOSING one. **30-C65** handles the `mate 10` exactly as you describe: the PV is truncated (16 plies, legal, not ending in checkmate, while mate 10 needs 19 — seat 06's S-F10), the claim is confirmed instead by replaying the PV's FINAL position interactively, which gives `score mate 2 ... pv e5f6 h8g8 e7g7`, a real 3-ply mate.

## Tue Nov 17 12:40:36 AM UTC 2026

**30-C66: 13-F24 (corrected) CONFIRMED on both halves.** 16 G positions, **fresh process per search**, 2000 vs 60000 ms, PC20/Threads 1/Hash 16: **exactly 1 of 16 changed its move** (reproducing its corrected figure), median depth **14 at 2 s and 23 at 60 s** (its 15/23 — same shape). **And the warm-state mechanism it blames is confirmed**: three identical `go depth 12` in ONE process gave `cp -293/-278/-283` and `cp -258/-304/-249` — **up to 55 cp of drift on an identical request**, same move each time. So its withdrawn "5 of 16" was indeed contamination. **30-F68**: shared-process harnesses are unsafe for SCORE comparisons (drift up to 55 cp) but can be safe for MOVE-only comparisons — and the drift being smaller than a given gap explains why the manufactured change appeared only sometimes.

## Tue Nov 17 12:42:49 AM UTC 2026

**30-C67: a third data point settles the 3-of-10 vs 1-of-10 discrepancy — and it is not the clock.** Same start, **match clock** (6s+0.06 with the increment carried forward), 20 plies, 10 games, PC20/Threads 1/Hash 16, one process per game: **1 distinct sequence out of 10**, all ten identical (hash `fa86c567`). So seat 25's 1-of-10 reproduces exactly at the match clock, and seat 16's 3-of-10 is NOT explained by clock variation as seat 25 hypothesised — nor by game length, since 20 plies gives 1. **30-F69**: self-play variety comes ONLY from the starting position, now confirmed three times independently (fixed depth 40 plies, match clock 20 plies, seat 25's own 1-of-10). N games from one opening are N copies of one game.

## Tue Nov 17 12:43:08 AM UTC 2026

**Both kept, and made operational as 30-F70.** (1) 30-C67 states plainly that the remaining explanation for the 3-of-10 must be in seat 16's harness, and names its own drift note as the thing to test (the note says one game diverged through "millisecond clock drift occasionally changing the depth reached" — testable by re-running at a fixed limit). (2) 30-F70 pairs 30-F69 with 30-F56: determinism fixes the SAMPLE SIZE of every match — 1,000 openings x 2 colours = **1,000 independent games observed twice, not 2,000** — so (a) "2,000 games" as a sample size overstates independence 2x and the honest form is "1,000 independent pairs (2,000 games)"; (b) re-running the same openings adds NO information; (c) the published pair-score intervals stand unchanged, as proved in 30-C52 (pair CI [+4.64,+28.40] matches; games-as-independent would give [+3.80,+29.23]).

## Tue Nov 17 12:43:32 AM UTC 2026

**Item 1 applied**: 30-F70's third consequence now CARRIES the M55 proof inline instead of pointing at 30-C52 — "over 1,000 PAIRS -> Elo +16.52, sd 6.061, CI [+4.64,+28.40] = exactly the published +16.52 [+4.63,+28.40]; over 2,000 games treated as independent -> sd 6.488, CI [+3.80,+29.23], a different and wrongly narrow interval". So the reader sees the proof and the consequence in one sentence, and the conclusion "nothing needs recomputing" follows from it directly. 139 finding lines; branch pushed.

## Tue Nov 17 12:46:17 AM UTC 2026

**30-C68 — seat 23 is right and I withdrew my gloss.** My 30-C41 said "the larger of the two clocks decides"; seat 23 showed that padding the OPPONENT's clock has NO effect, and I reproduced it exactly: white to move, `go btime 6000000` -> no bestmove, depth 28, **13,775,851 nodes, 12.0 s**, and `go btime 6000` -> **identical depth 28, identical 13,775,851 nodes, 12.0 s**; control `go wtime 6000 btime 6000` -> `e1g1` d16 / 223,639 / 0.1 s. So "send the opponent a big number" is NOT a workaround; **the remedy is an engine-side diagnostic plus a bounded default**. The main finding (a clock line naming only the OPPONENT leaves the search unbounded and silent) stands, now confirmed by three seats. **30-F71** adopts seat 23's meta-lesson: in a restatement, mark each clause MEASURED or ASSERTED-UNTESTED — my C41 merged two measured rows with an untested gloss, and the gloss was the wrong part. **30-C69** also reproduces 19-C23 to the NODE on all nine cells (7,608,471 / 15,702,225 = 2.06x; depth-20 inert at 232,803; counter 99 cp 0 at 120 nodes), confirming its depth qualifier.

## Tue Nov 17 12:46:55 AM UTC 2026

**Both edits applied.** (1) 30-C68 now LEADS with the identical-node pair: **`go btime 6000000` and `go btime 6000` produce an IDENTICAL search — depth 28, 13,775,851 nodes, 12.0 s, no bestmove either way** — before the control row, so the withdrawal rests on the cleanest fact first. (2) 30-F72 is now stated as a RULE rather than a note: **"the halfmove and fullmove counters are part of a position's IDENTITY — a FEN quoted without them does not identify a search"**, with the five-mate-value spread (mate -16 / -16 / -15 / -19 / cp 0) and the 2.06x node swing between two same-score counters as the supporting detail. 143 finding lines; pushed.

## Tue Nov 17 12:47:22 AM UTC 2026

**Both requested, in one place.** 30-F72 now states the counter-as-identity RULE ONCE with its **three independent supports named**: (1) my own sweep — five answer values across counters 0/1/12/50/99 at depth 24 plus a 2.06x node swing between two same-score counters; (2) seat 19's depth qualifier, reproduced to the node (inert at depth 20 at exactly 232,803 nodes, active at 24); (3) seat 25's original sweep. It also closes the 10-F64 confusion explicitly as **a CITATION GAP, not a contradiction**: seat 27's 599,407,784 at depth 14 on counter 80 (which I reproduced to the node) versus seat 10's 23,174,968 matching NO depth of counter 80 — two different questions, and a node-count table without the counters beside the FEN is under-specified. 143 finding lines; pushed.

## Tue Nov 17 12:48:15 AM UTC 2026

**30-C70: verified another seat's Rule 1 finding and supplied the missing plant.** 19-C28 says 08-F31's "0 of 60" has no planted case; I confirmed it directly — `grep -inE "plant|control|fake|bogus|assert"` on seat 08's `volatility_rate.py` returns only the word "control" describing the owner's time control, and its report has 0 hits. **So I built the plant that harness needs**, in three rows: synthetic `cp 40` vs `cp 400` -> **flagged**; real queen-up `4k3/8/8/8/8/8/8/QK6 w` = **cp 1267** vs K-v-K = **cp 0** -> **flagged different**; negative control (same position twice, cp 1267 vs cp 1267) -> **NOT flagged**. The comparison sees a real difference and does not invent one. This does not make 08-F31 wrong — it makes its zero **plantable**: seat 08 can run these three rows in its own harness and the zero becomes a Rule 1 zero.

## Tue Nov 17 12:48:38 AM UTC 2026

**30-C71: the gap is closed TWICE, and I recorded the two closures as different things.** **(A) Seat 08's own plant — the stronger:** `pc20/plant_check.py` exercises **the SAME code path** as the zero and includes a **PV replay requiring checkmate**, so it fails if the harness cannot see a deep mate; its board `8/8/6k1/Q7/1P4PP/1K3P2/8/8 b` scores **cp -4161** on the clocked search at depth 16. That is the closure that validates the actual 0-of-60. **(B) My plant (30-C70) — weaker but portable:** three rows proving a comparison of this shape can see a difference and does not invent one, but NOT through seat 08's harness, so it establishes the DESIGN rather than that harness. Both are true and answer different questions; neither is redundant. **The difference between a gap reported and a gap closed is this: someone ran the plant through the harness that made the claim.**

## Tue Nov 17 12:49:00 AM UTC 2026

**Both items kept.** (1) The sentence stays in 30-C71 verbatim: **"the difference between a gap reported and a gap closed is this: someone ran the plant through the harness that made the claim"** — verified present. (2) The pattern is now its own line, **30-F73**, recording the best-case cross-check loop with its evidence at each step: seat 19 grepped and found no plant, I re-grepped and confirmed, I supplied a portable plant, and seat 08 built its own through the same code path with a PV replay and credited the grep in writing. Properties worth copying: **the gap was stated as a coverage gap, not a wrong result** (easy to accept), **the fix ran through the harness that made the claim** (the zero became valid rather than defended), **credit was given in writing** (repeatable). Contrasted with the failure mode seen elsewhere tonight: a claim defended instead of a gap closed. 146 finding lines; pushed.

## Tue Nov 17 01:06:50 AM UTC 2026 — RETRACTION 2

**30-C72: I WITHDRAW 30-F66 AND 30-C64. My 599,407,784 run was NOT under PC20.** The bug: my `p.sh` sent options as `setoption name LmrQuietBase 93` — **value inside the name, no `value` keyword** — so the engine answered `info string unknown option LmrQuietBase 93` for all 22 of them and ran with DEFAULT options. Verified directly: `setoption name Hash 16` -> `unknown option Hash 16`; `setoption name Hash value 16` -> accepted. **So seat 10 was right all along (23,174,968 at depth 14 on the true PC20 build)**, seat 07's 07-C72 is correct that the cause is BUILD/SETTINGS, and seat 27's 599M (now withdrawn on its side too) came from the same mistake. My "third independent run" was not independent — it reproduced the same misconfiguration. **30-C73**: this is the third instance of one fault class tonight and the one I should have caught: a `setoption` whose output I never read. **30-F74** records the meta-lesson the coordinator flagged: seat agreement is NOT independent evidence when a settings error can be shared — seat 27 and I "agreed to the node" while both measuring defaults. **30-F75**: the rule — read every `setoption` reply, abort on `unknown option`, and print the applied option count beside the result.

## Tue Nov 17 01:07:26 AM UTC 2026

**30-C74: I AUDITED ALL 25 OF MY CONFIRMATION LINES AGAINST THE STANDARD THAT JUST EXPOSED MY OWN ERROR.** Result: **they survive, except the one already withdrawn.** (1) No Python script of mine ever used the broken `setoption name X Y` form — grep returns nothing; the broken form existed ONLY in `check20/p.sh`, the shell script behind the 599M run. (2) Three scripts send the correct form but never abort on refusal (check5, check12, check16); I verified empirically they still applied their options by running `bench 11` after S14 through the same code shape: **242,796, the S14 pin, not the 312,866 default**. (3) My four newest harnesses (check18b/19/21/22) abort on refusal AND assert the applied option count (22 for PC20), so they are immune by construction. **The only confirmation that fails this audit is 30-F66/C64, already withdrawn — and it is the only one whose harness was a shell script.**

## Tue Nov 17 01:07:53 AM UTC 2026

**Both items, and the sentence is now VERIFIED rather than asserted.** 30-C74 carries: **"the only confirmation that fails this audit is the one whose harness was a shell script"** — and I checked it: every surviving confirmation (check1, 2, 5, 7, 8, 12, 16, 21, 22) is driven by a `.py`; the only `.sh` files are `check20/p.sh` (the withdrawn run), `check1/honesty_and_consequence.sh` (**zero** setoptions, cited by no CONFIRMS line), and `build_san.sh`/`honesty.sh`/`read_board.sh` (no setoptions). So the condition named is the real one: **a shell script that applies options without reading the engine's replies.** Item 1 also stands: the three non-aborting Python scripts keep their confirmations because the regime PINS (bench 11 = 242,796, not the 312,866 default) prove their options took effect — no harness rewrite needed.

## Tue Nov 17 01:08:21 AM UTC 2026

**30-F76 records the pin-check method generally.** When you cannot be sure a harness applied its options, do not rewrite it — apply the same list through the same code shape and search for a number that ONLY the intended regime produces. Here `bench 11` is **312,866 default / 242,796 under S14**; getting 242,796 proved the options took effect, and 312,866 would have proved they did not. Record the discriminating number beside the result. Cheaper and more honest than adding assertions, and decisive where code reading is not. **Settings thread closed** as you said — nothing further owed on it; 152 finding lines; continuing at cadence.

## Tue Nov 17 01:09:00 AM UTC 2026

**30-C75: the 3-of-10 question is now RESOLVED, and my prediction was right.** Seat 16 has withdrawn its own "3 distinct positions of 10" as a **clock artefact of its own harness**: at a FIXED limit the same start gives **1 distinct sequence in 10 of 10** games at both `go nodes 20000` and `go depth 10` — exactly my 30-C67 result — and it names the cause as its clock arm decrementing by measured wall time so millisecond differences occasionally changed the depth reached. That is the mechanism I predicted in 30-C67. **Three independent confirmations now agree on 1-of-10**: mine at a fixed depth AND at the match clock, seat 25's, and seat 16's fixed-limit re-run. And this is 30-F73's best-case loop running a second time — the owning seat tested its own claim and withdrew it given a specific prediction about where the fault lay.
