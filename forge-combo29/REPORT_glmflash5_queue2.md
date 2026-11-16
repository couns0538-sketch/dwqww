# REPORT glmflash5 — QUEUE 2 — the deferred P@20k, then row 2 (V/C8/T1/T2/P at 2,000 nodes)

Branch `cursor/glmflash5-work-cb5c` (run A). Builds: B5S (sha b8e0d166…, for P; = deepseek5's
pinned build byte-for-byte, `exe_sha256_B5S.txt`), B10 (7621bdfb…), B_FINE (04bcba3d…). Item
minute 0 = 20:34:37Z. All six matches COMPLETE (M110's first run superseded — see §6). times:
see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: item 2 = the deferred M105 (P@20k from item 1) first, then row 2: P/V/C8/T1/T2 against
S14 at 2,000 nodes; the five POOLS for the candidates that now have enough looks (the file's
pool rule said items 4/8/…, but P's third look at both node counts arrived here — I pooled
where the counts made pools meaningful, listed per pool).

Answer: **M105 (P@20k, third look): +7.30 [−2.81, +17.41]; the P@20k pool over THREE seeds
(M24+M32+M105): +9.90 [+4.03, +15.78] — one-sided: pv1's 20,000-node gain is REAL on my tree.**
**M106 (P@2k, third look): +88.74 [+76.08, +101.40]; the P@2k pool over THREE seeds (M34+M36+
M106): +80.08 [+72.88, +87.29] — the giant 2,000-node gain is three-seed solid.** **M107 (V@2k,
sixth look): −5.39 [−17.44, +6.67] — the V@2k six-look pool drops to +4.66 [−0.21, +9.53]
(job 24's five-look +6.67 was seed-high).** **M108 (C8@2k, second look): −6.25 [−17.92, +5.41];
the C8@2k pool is −1.04 [−9.47, +7.39] — level (M53's +4.2 was seed-high).** **M109 (T1@2k,
third look): +8.86 [−3.35, +21.08]; T1@2k pool +3.13 [−3.85, +10.11].** **M110b (T2@2k, second
look, FRESH openings after the wrap fault): +1.74 [−10.52, +13.99]; T2@2k pool −5.65 [−14.23,
+2.93].**

One sentence: **at 2,000 nodes under S14 the session's standing picture is now: P (pv1) ~ +80
(3 seeds), everything else between −6 and +5 (V/C8/T1/T2) — the check-extension caps and the
fine reductions are marginal; the LMP exemption at PV nodes is the only big lever on this
tree — and it does not transfer to the PC's engine.**

How sure: B5's step 0 (pins exact; P's S14 sum 9,476,627 = my first measurement AND equal to
B6's job-16 pv1 row — two builds, one number); six probes exact (per-setting values AND the
base's explicit bare-14 verified per line); 14,000/14,000 validation rows (M110-void
included as superseded); identities + openings-slice checks printed by the committed
`queue2_stats.py`.

## 2. Step 0 — B5's pins and P's row (`queue2_rows.txt`, script `queue2_rows.py` COMMITTED)

| build | setting | first-3 nodes | sum over 200 | note |
|-------|---------|---------------|--------------|------|
| B5S | P (SoundPvArm 1 + SoundStepMask 1) | 17188, 26670, 44100 | 9,476,627 | first measurement under S14 on B5; equals B6's pv1 row (job 16) exactly |

B5S pins: 312,866 / 862,329 / 4,865,609 ✓ (`q2_b5_*`). B10/B_FINE were step-0-verified in
item 1 (unchanged binaries). Refusal lines 0.

## 3. Step 2 — six probes (`probe_M105…M110.log`; probe openings lines 6301–6322, no match uses
them; each probe's setting+options stamped)

| probe | cand received (2/2 each) | base received | refusals | go-limit |
|-------|--------------------------|---------------|----------|----------|
| M105 (P, 20k) | SoundPvArm=1, SoundStepMask=1 | its 14 ×2, no extras | 0 | all `go` nodes 20000 |
| M106 (P, 2k) | the same two | its 14 ×2 | 0 | all `go` nodes 2000 |
| M107 (V) | CED=8, GC=0, IC=0 | its 14 ×2 | 0 | nodes 2000 |
| M108 (C8) | CED=8 | its 14 ×2 | 0 | nodes 2000 |
| M109 (T1) | LmrFine=1, FineHist=1 | its 14 ×2 | 0 | nodes 2000 |
| M110/M110b (T2) | LmrFine=1, FineHist=1, RoundF=0 | its 14 ×2 | 0 | nodes 2000 |

## 4. The matches (each setting's build on both sides; S14 both; cand's lines on top; base has
NO candidate options; nodes as named; pairs colours swapped, `-pgnout` in my folder;
openings_queue2.epd by the globbing script (98 gamelist files; 89,979 distinct openings removed;
Random(41002); 5,000 lines; first line
`r2qk2r/pp2bppp/2np1n2/2p1p3/2P1P3/3P1P1P/PP4BP/RNBQK2R w KQkq - 1 8`), order sequential; M105
1–1000, M106 1001–2000, M107 2001–3000, M108 3001–4000, M109 4001–5000; M110 was MEANT for
4001–5000 (the queue's formula) — my start=5001 WRAPPED the file to lines 1–1000 (M105's
slice), so M110 is VOID and M110b reran T2 on a fresh 1,000-line file `openings_queue2b.epd`
(Random(41003); 94,979 openings removed; first line
`rnbqk2r/ppppp1b1/7p/4Bppn/2BP4/4PN2/PPP2PPP/RN1QK2R b KQkq - 4 8`), order sequential; M110b's
own `cmd_M110b.txt` written after its readbacks)

Games by ending FIRST — **the output of the committed `queue2_stats.py` (`queue2_stats_out.txt`
is the source of every number in this table):** (losses on time BY SIDE 0/0; illegal/disconnect/
crash 0)

| ending | M105 | M106 | M107 | M108 | M109 | M110b |
|--------|------|------|------|------|------|-------|
| White mates | 612 | 689 | 774 | 727 | 760 | 722 |
| Black mates | 454 | 677 | 623 | 661 | 661 | 694 |
| 3-fold repetition | 643 | 350 | 316 | 315 | 300 | 289 |
| fifty moves | 148 | 190 | 184 | 191 | 165 | 193 |
| insufficient material | 138 | 84 | 99 | 98 | 108 | 97 |
| stalemate | 5 | 10 | 4 | 8 | 6 | 5 |
| **identity: mates = wins+losses** | 612+454 = 554+512 = 1066 ✓ | 689+677 = 933+433 = 1366 ✓ | 774+623 = 683+714 = 1397 ✓ | 727+661 = 676+712 = 1388 ✓ | 760+661 = 736+685 = 1421 ✓ | 722+694 = 713+703 = 1416 ✓ |

| match | cand | build | nodes | seed | pairs | W-L-D | n5 | Elo, 95 % PAIR interval | complete? (duration) |
|-------|------|-------|-------|------|-------|-------|----|-------------------------|----------------------|
| M105 | P | B5S | 20000 | 40005 | 1000 | 554-512-934 | [37,252,400,254,57] | +7.30 [−2.81, +17.41] | COMPLETE (12:21) |
| M106 | P | B5S | 2000 | 40106 | 1000 | 933-433-634 | [42,142,304,298,214] | **+88.74 [+76.08, +101.40]** | COMPLETE (2:12) |
| M107 | V | B10 | 2000 | 40107 | 1000 | 683-714-603 | [107,216,383,189,105] | −5.39 [−17.44, +6.67] | COMPLETE (2:01) |
| M108 | C8 | B10 | 2000 | 40108 | 1000 | 676-712-612 | [99,222,381,212,86] | −6.25 [−17.92, +5.41] | COMPLETE (2:02) |
| M109 | T1 | B_FINE | 2000 | 40109 | 1000 | 736-685-579 | [98,205,364,214,119] | +8.86 [−3.35, +21.08] | COMPLETE (2:13) |
| M110b | T2 | B_FINE | 2000 | 40110 | 1000 | 713-703-584 | [108,208,360,214,110] | +1.74 [−10.52, +13.99] | COMPLETE (2:02) |

**The pools (the same committed script; the looks that went in are named):**

| pool | looks | pairs | n5 | Elo, 95 % pair interval |
|------|-------|-------|----|-------------------------|
| P@20,000 | M24, M32 (job 18) + M105 | 3,000 | [128, 695, 1233, 766, 178] | **+9.90 [+4.03, +15.78]** |
| P@2,000 | M34, M36 (job 19) + M106 | 3,000 | [144, 405, 1003, 844, 604] | **+80.08 [+72.88, +87.29]** |
| V@2,000 | M49, M51, M52, M55, M56 (jobs 22–24) + M107 | 6,000 | [572, 1241, 2289, 1250, 648] | +4.66 [−0.21, +9.53] |
| C8@2,000 | M53 (job 23) + M108 | 2,000 | [191, 453, 739, 411, 206] | −1.04 [−9.47, +7.39] |
| T1@2,000 | M67, M68 (job 26) + M109 | 3,000 | [301, 630, 1114, 624, 331] | +3.13 [−3.85, +10.11] |
| T2@2,000 | M69 (job 26) + M110b (the wrapped M110 VOID) | 2,000 | [227, 421, 742, 410, 200] | −5.65 [−14.23, +2.93] |

predictions.txt (own commit cd16ea4a8, 20:34:53Z): M105 +8 [−4,+20] — held (+7.30); M106 +70
[+50,+90] — **CALLED WRONG** (+88.74 — the gain grew again); M107 +5 [−7,+17] — held (−5.39);
M108 +3 [−9,+15] — held (−6.25); M109 0 [−10,+10] — **CALLED WRONG** (+8.86); M110 −8 [−20,+4]
— held (M110b +1.74).

## 5. From my colleagues

- Nothing new read this item (the 2-minute rule fires before item 3).

## 6. What I did NOT do / faults owned

- **The wrapped-M110 fault**: I assigned M110 start=5001 on a 5,000-line file; fastchess wrapped
  to lines 1–1000 (M105's slice). The run is VOID (superseded by M110b on fresh openings); both
  runs' files are committed (`M110_void_stdout.txt`, `M110_void_last40.txt`). The queue's own
  formula (1000(i−1)+1) is what I should have applied — the driver takes `start` from the job
  text's formula from now on, never hand-typed.
- Also learned and recorded: the wrapped M110's games DIFFERED from M105's despite identical
  openings+settings-different (702/2000 same results) — so under concurrency a seed-only change
  is NOT a reliable replay device either way; the only safe design is disjoint openings per
  match, which the wrapped run broke and M110b restored.
- No PV-2k second seeds beyond the three the pools now hold.

## 7. What I am NOT sure about

- Whether P@2k's +80 is the ceiling (three seeds: 75.3, 76.3, 88.7 — the third is the highest;
  the pool's +80 could still drift with a fourth).
- Whether V@2k's pool (+4.66, six looks) is a real small gain (its interval now just touches
  zero).
- The mechanism behind M106-vs-M110's divergence on identical openings (unresolved; noted for
  kimi5/Opus — it matters for every "replay" argument).

## 8. A better way

- The queue formula (1000(i−1)+1) belongs IN the driver: pass `i` and the item number, let the
  script compute start and assert it against the file's line count — my hand-typed 5001 was the
  fault.

## 9. times: see stamps.txt.

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 21:01:06Z)

```
=== git status --short (head):
 M forge-combo29/tests_glmflash5_queue2/stamps.txt
?? forge-combo29/REPORT_glmflash5_queue2.md
?? forge-combo29/tests_glmflash5_queue2/M105_stdout.txt
?? forge-combo29/tests_glmflash5_queue2/M106_stdout.txt
?? forge-combo29/tests_glmflash5_queue2/M107_stdout.txt
?? forge-combo29/tests_glmflash5_queue2/M108_stdout.txt
?? forge-combo29/tests_glmflash5_queue2/M109_stdout.txt
?? forge-combo29/tests_glmflash5_queue2/M110_stdout.txt
=== ls tests_glmflash5_queue2:
cmd_M105.txt
cmd_M106.txt
cmd_M107.txt
cmd_M108.txt
cmd_M109.txt
cmd_M110b.txt
cmd_M110.txt
config_M110b.json
exe_sha256_B5S.txt
gamelist_M105.txt
gamelist_M106.txt
gamelist_M107.txt
gamelist_M108.txt
gamelist_M109.txt
gamelist_M110b.txt
gamelist_M110.txt
M105_stdout.txt
M106_stdout.txt
M107_stdout.txt
M108_stdout.txt
M109_stdout.txt
M110b_last40.txt
M110b_stdout.txt
M110_stdout.txt
M110_void_last40.txt
M110_void_stdout.txt
make_openings_queue2.py
openings_queue2b.epd
openings_queue2.epd
prediction.txt
probe_M105.log
probe_M106.log
probe_M107.log
probe_M108.log
probe_M109.log
probe_M110.log
q2_b5_bench11.txt
q2_b5_bench13.txt
q2_b5_perft5.txt
queue2_match.sh
queue2_rows.txt
queue2_stats_out.txt
queue2_stats.py
queue2_summary.txt
stamps.txt
```
(the listing was taken mid-work: the *_last40/config/gamelist files for M105–M109 were already
copied and are in the commit; the `??`/`M` lines are the pre-commit state.)

## 11. Model name

glmflash5 (GLM, flash tier), run A on `cursor/glmflash5-work-cb5c`.
