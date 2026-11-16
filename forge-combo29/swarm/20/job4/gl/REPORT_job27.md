# REPORT glmflash5 — JOB 27 — the check-extension ladder's 20,000-node pools and the CED5 rungs

Branch `cursor/glmflash5-work-cb5c` (run A). Exe = B10 (sha256
7621bdfbb3b85f5e5ea37e9a7365adf2be27423e16d55d7b470d8cb7a513a1a6; step 0 re-verified, pins
fresh in `b10j27_*.txt`). All five matches COMPLETE. times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: more looks of V (CED 8 + the two check-reduction terms off) at 20,000 nodes, a second
look of C8 (the extension alone) at 20,000, and the CED5 rungs (V5, C5) at 2,000; two pools.

Answer: **V at 20,000 over FOUR looks (M54+M59+M73+M74, 4,000 pairs): +1.30 [−3.68, +6.29] —
level; job 24's two-look +4.3 was seed-high, and this job's M73 (−7.12) pulled it back.** **C8
at 20,000 over two looks (M60+M75, 2,000 pairs): −1.39 [−8.51, +5.73] — level.** **At 2,000
nodes the CED5 rungs: M76 (V5) +14.95 [+3.15, +26.74] — one-sided UP, the biggest 2,000-node
check-family number yet; M77 (C5) +3.13 [−8.91, +15.16] — level.**

One sentence: **the extension cap's value is DEPTH-DEPENDENT and sits in the cap: at 20,000
nodes everything is level (V +1.3 over four seeds, C8 −1.4 over two); at 2,000 nodes the capped
variants gain (V +6.7 over five seeds, V5 +15.0 one-sided) — the tighter the cap, the bigger
the 2,000-node lean so far (CED 30: ~+8.7 pool; CED 8: +6.7; CED 5: +15.0, one seed).**

How sure: step 0 met (S14/V/C8 equal job 23's knowns; V5 9,163,379 and C5 9,170,430 are MY
first measurements — nearly identical tree sizes, both ~3.5 % under S14); five probes exact
(the per-setting option VALUES verified in the logs); 10,000/10,000 validation rows; identities
and openings-slice checks printed by the committed `job27_stats.py`. Five single seeds; the
20,000 pools are three- and two-seed.

## 2. Step 0 — pins and rows (`job27_rows.txt`, driver `job27_rows.py` COMMITTED)

| setting | first-3 nodes | sum over 200 | known |
|---------|---------------|--------------|-------|
| S14 | 41311, 24872, 28574 | 9,500,069 | ✓ |
| V (CED8+GC0+IC0) | 15600, 24808, 38064 | 8,565,026 | ✓ (job 23) |
| C8 (CED8) | 16647, 18396, 42443 | 9,015,167 | ✓ (job 23) |
| V5 (CED5+GC0+IC0) | 11781, 28476, 27618 | 9,163,379 | MINE — first measurement |
| C5 (CED5) | 18056, 19384, 21667 | 9,170,430 | MINE — first measurement |

Pins: 312,866 / 862,329 / 4,865,609 ✓. Refusal lines 0.

## 3. Step 2 — five probes (`probe_M73…M77.log`; probe openings lines 5001–5010 of the 5,000-line
file, no match uses them; the stamp line carries each probe's exact option list)

| probe | cand received (2/2 each) | base received | refusals | go-limit |
|-------|--------------------------|---------------|----------|----------|
| M73/M74 (V) | CheckExtensionDepth=8, LmrGiveCheck=0, LmrInCheck=0 | its 14 ×2, no extras | 0 | all `go` = nodes 20000 |
| M75 (C8) | CheckExtensionDepth=8 | its 14 ×2 | 0 | same |
| M76 (V5) | CheckExtensionDepth=5, LmrGiveCheck=0, LmrInCheck=0 | its 14 ×2 | 0 | all `go` = nodes 2000 |
| M77 (C5) | CheckExtensionDepth=5 | its 14 ×2 | 0 | same |

## 4. The matches (B10 both sides; S14 both; the candidate's lines on top; nodes as named;
Threads 1, Hash 16, OwnBook false, no adjudication, pairs colours swapped, `-pgnout` in my
folder; openings_job27.epd by the committed globbing script (89 gamelist files; 80,979 distinct
openings removed; Random(27001); 5,000 lines — the first build had 6,000 by my sed miss and was
rebuilt to the job's 5,000 before any use; first line
`r1bqk1nr/3p1ppp/ppnbp3/2p5/2P1P3/P1N2N2/1P1PBPPP/R1BQK2R w KQkq - 2 7`), order sequential;
M73 1–1000, M74 1001–2000, M75 2001–3000, M76 3001–4000, M77 4001–5000; concurrency 4; every
`cmd_<M>.txt` written after the node/start readback)

Games by ending FIRST — all from the committed `job27_stats.py` (output `job27_stats_out.txt`),
identities and openings-slice checks printed by the same command (losses on time BY SIDE 0/0;
illegal/disconnect/crash 0):

| ending | M73 (2000) | M74 (2000) | M75 (2000) | M76 (2000) | M77 (2000) |
|--------|------------|------------|------------|------------|------------|
| White mates | 630 | 580 | 577 | 721 | 740 |
| Black mates | 485 | 478 | 516 | 665 | 624 |
| 3-fold repetition | 607 | 628 | 626 | 329 | 333 |
| fifty moves | 148 | 172 | 136 | 188 | 184 |
| insufficient material | 125 | 138 | 139 | 94 | 112 |
| stalemate | 5 | 4 | 6 | 3 | 7 |
| **identity: mates = wins+losses** | 630+485 = 537+578 = 1115 ✓ | 580+478 = 540+518 = 1058 ✓ | 577+516 = 544+549 = 1093 ✓ | 721+665 = 736+650 = 1386 ✓ | 740+624 = 691+673 = 1364 ✓ |

| match | cand | nodes | seed | pairs | W-L-D | n5 | Elo, 95 % PAIR interval | complete? (duration) |
|-------|------|-------|------|-------|-------|----|-------------------------|----------------------|
| M73 | V | 20000 | 20073 | 1000 | 537-578-885 | [53,241,440,226,40] | −7.12 [−16.98, +2.74] | COMPLETE (11:26) |
| M74 | V | 20000 | 20074 | 1000 | 540-518-942 | [45,230,427,254,44] | +3.82 [−6.05, +13.69] | COMPLETE (11:42) |
| M75 | C8 | 20000 | 20075 | 1000 | 544-549-907 | [53,235,421,246,45] | −0.87 [−10.93, +9.20] | COMPLETE (11:30) |
| M76 | V5 | 2000 | 20076 | 1000 | 736-650-614 | [90,183,383,239,105] | **+14.95 [+3.15, +26.74]** | COMPLETE (1:52) |
| M77 | C5 | 2000 | 20077 | 1000 | 691-673-636 | [106,198,367,230,99] | +3.13 [−8.91, +15.16] | COMPLETE (1:50) |

**The two pools (ONE committed command):**

| pool | looks | pairs | n5 | Elo, 95 % pair interval |
|------|-------|-------|----|-------------------------|
| V@20,000 (M54+M59+M73+M74) | 4 | 4,000 | [188, 941, 1718, 959, 194] | +1.30 [−3.68, +6.29] |
| C8@20,000 (M60+M75) | 2 | 2,000 | [99, 494, 822, 494, 91] | −1.39 [−8.51, +5.73] |

predictions.txt (own commit 62907956b, 19:05:14Z): M73 +4 [−6,+14] — **CALLED WRONG** (−7.12);
M74 +4 [−6,+14] — held; M75 +2 [−8,+12] — held; M76 +7 [−5,+19] — held (+14.95 inside); M77 +5
[−7,+17] — held; pool V@20k +4 [−2,+10] — held (+1.30).

## 5. From my colleagues

- Nothing new read this job beyond file 27's own summaries (the 2-minute colleague-read rule
  fires before the NEXT job or at the 4-hour mark).
- The deviation I made and fixed: my first openings build had 6,000 lines (my sed missed the
  count); rebuilt to the job's 5,000 before any probe or match touched it — the superseded
  build is stamped.

## 6. What I did NOT do

- No CED values between 5 and 8 or 8 and 30 (three points of the cap ladder exist: 5, 8, 30).
- No V5/C5 second seeds (M76's one-sided interval is the job's finding; a second seed is the
  natural ask).
- No 2,000-node re-pool of V (its five-look pool from job 24 stands).

## 7. What I am NOT sure about

- Whether V5's +15.0 (one seed) is the cap-ladder's true slope at 2,000 or a seed draw — the
  C5 rung's +3.1 does NOT confirm a monotone "tighter is better" (C5 vs V5 differ by the two
  terms, confounded with the cap).
- Whether V@20k's four-look +1.3 hides a tiny real effect (interval ±5).
- The M73 negative (−7.1) against M74's positive (+3.8) — same setting, same node count,
  adjacent openings slices: seed noise of ±10 on 1,000 pairs is the session's standing reality.

## 8. A better way

- The cap ladder (30/8/5) at 2,000 nodes is cheap (~2 min per rung) and now has three points;
  adding CED 12 and CED 15 rungs would map the curve for the price of two matches — worth it
  before the PC spends 4,000-game blocks on a cap value.

## 9. times: see stamps.txt.

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 19:44:23Z)

```
=== git status --short (head):
 M forge-combo29/tests_glmflash5_job27/openings_job27.epd
 M forge-combo29/tests_glmflash5_job27/stamps.txt
?? forge-combo29/tests_glmflash5_job27/M73_last40.txt
=== ls tests_glmflash5_job27: (42 files)
b10j27_bench11.txt b10j27_bench13.txt b10j27_perft5.txt
cmd_M73.txt cmd_M74.txt cmd_M75.txt cmd_M76.txt cmd_M77.txt
config_M73.json config_M74.json config_M75.json config_M76.json config_M77.json
gamelist_M73.txt gamelist_M74.txt gamelist_M75.txt gamelist_M76.txt gamelist_M77.txt
job27_match.sh job27_rows.py job27_rows.txt job27_stats.py job27_stats_out.txt job27_summary.txt
M73_last40.txt M73_stdout.txt
M74_last40.txt M74_stdout.txt
M75_last40.txt M75_stdout.txt
M76_last40.txt M76_stdout.txt
M77_last40.txt M77_stdout.txt
make_openings_job27.py openings_job27.epd prediction.txt
probe_M73.log probe_M74.log probe_M75.log probe_M76.log probe_M77.log
stamps.txt
```
(the `M` lines were the openings-file rebuild and the stamps update before this commit; the
`??` files join it.)

## 11. Model name

glmflash5 (GLM, flash tier), run A on `cursor/glmflash5-work-cb5c`.
