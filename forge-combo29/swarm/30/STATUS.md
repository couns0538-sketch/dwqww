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
