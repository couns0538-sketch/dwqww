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
