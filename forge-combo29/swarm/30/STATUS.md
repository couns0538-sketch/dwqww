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
