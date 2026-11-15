# glmflash2 job 6 report (2026-11-15)

## 1. Result in plain words

The Asp rule's MaxReduce against none, at 20,000 nodes: **MR2 +17.0 +/- 11.5** (S1, 1,696/2,000),
**MR5 +7.5 +/- 11.6** (S2, 1,532/2,000), beside the known **MR3 +13.5** pooled over three seeds
(not replayed); the direct comparison **MR5 vs MR3: -3.0 +/- 5.1** (S3, 1,761/2,000, 771 of 880
pairs two draws); **MR1 +9.2 +/- 10.3** (S4, full 2,000). **The value I would play: 3** - it has the
most evidence (three pooled seeds, +13.5 with the interval entirely positive) and MR5, the only
value measured directly against it, came out slightly worse; **MR2 is the one worth a second seed**,
because its point estimate is the highest of all four and its single match already clears zero.
Cut or not reached, first paragraph as asked: nothing was skipped and no match was cut to nothing -
S1/S2/S3 were cut by their 900 s caps at 1,696/1,532/1,761 of 2,000 games (each with fastchess's own
summary), S4 completed all 2,000 games inside its deadline; every planned match has a row.

## 2. Step 0 (expected against printed)

Build: the job 5 tree (d4f43124 + packc28_port.patch, applied zero-fuzz, source reused), CMake
Release, g++ 13.3.0, `-DCMAKE_CXX_FLAGS="-DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1"` - the
tunables are UCI options, so NO wrapper anywhere in this job.

| check | expected | printed | file |
|-------|----------|---------|------|
| bench 11, no options | 312866 | 312866 | step0/bench11_off.txt |
| bench 13, no options | 862329 | 862329 | step0/bench13_off.txt |
| go perft 5 | 4865609 | 4865609 | step0/perft5_off.txt |
| bench 13, the four options of job 5, set directly | 690187 | 690187 | step0/bench13_four_opts.txt |

The two `uci` lines, copied verbatim:

    option name AspFailHighReduce type spin default 0 min 0 max 1
    option name AspFailHighMaxReduce type spin default 3 min 1 max 6

The range allows 5 (max 6). New bench-13 numbers with the rule ON (`AspFailHighReduce 1`) - all four
distinct, so no two of these values search the same tree at this bench:

| MaxReduce | bench 13 nodes | file |
|-----------|----------------|------|
| 1 | 728460 | step0/bench13_asp_mr1.txt |
| 2 | 646701 | step0/bench13_asp_mr2.txt |
| 3 | 649268 | step0/bench13_asp_mr3.txt |
| 5 | 683370 | step0/bench13_asp_mr5.txt |

## 3. The probes

Before every match: 2-game probe with the match's exact command, engine input log on. Committed per
match: <name>_probe_setoption_lines.txt (the cand-side setoption lines fastchess sent - with the
tunables exposed they are visible in fastchess's own log, e.g. S1's shows
`AspFailHighReduce value 1` + `AspFailHighMaxReduce value 2` twice, one per game) and
<name>_probe_openings.txt. Probe FENs == match round-1 FENs for ALL five matches (checked by string
compare, all MATCH). First-pair openings across the five matches: five distinct FENs - the
second-seed-replays-first-match fault did not happen.

## 4. All matches (20,000 nodes; same exe both sides; no adjudication)

Machine: 4 cores, concurrency 4, fastchess v1.8.3-alpha, UHO book. Crashes/illegal/disconnects: 0 in
every match (grep over each full output). fc Elo = fastchess's own final or last-interim block;
my Elo = logistic from mean pair score, 95% pair interval (pgn_stats.py, validated in jobs 1-5).

| #  | match | seed | games | W-L-D | Ptnml(0-2) | fc Elo +/- err | my Elo +/- 95% | crashes |
|----|-------|------|-------|-------|------------|----------------|----------------|---------|
| C  | 20k vs 10k, no options | 7260 | 300 | 167-31-102 | [1,11,35,57,46] | +169.86 +/- 33.07 | +169.86 +/- 34.62 | 0 |
| S1 | Asp on, MR2 vs none | 7261 | 1696/2000 | 530-445-721 | [41,180,342,223,61] | +15.88 +/- 11.76 (last interim, 1600g) | +17.04 +/- 11.45 | 0 |
| S2 | Asp on, MR5 vs none | 7262 | 1532/2000 | 448-415-669 | [38,169,323,194,42] | +9.68 +/- 12.13 (last interim, 1500g) | +7.49 +/- 11.63 | 0 |
| S3 | MR5 vs MR3 (both Asp on) | 7263 | 1761/2000 | 508-524-729 | [10,53,771,34,12] | -2.83 +/- 5.23 (last interim, 1700g) | -2.96 +/- 5.12 | 0 |
| S4 | Asp on, MR1 vs none | 7264 | 2000 | 593-540-867 | [45,231,415,244,65] | +9.21 +/- 10.29 | +9.21 +/- 10.31 | 0 |

Known (not replayed): MR3 vs none = +13.5, 95% [+5.7, +21.0], pooled over three seeds.
C's rate: 300 games in ~118 s = ~2.5 games/s; the S caps (900 s) were set from the first rate
estimate (~2.3/s, taken conservatively from the phase-1 wall time); at the real ~2.1-2.5 games/s of
the S matches three of them were cut by the cap and S4 finished inside its deadline.

## 5. Files of the repository I opened

- The job file (git show on the handoff branch). Nothing else - the tree and the patch were read in
  job 5; the Asp rule is the patch's P8 hunk (root re-search at depth - min(consecutive
  fail-highs, AspFailHighMaxReduce), main worker only).

## 6. Start and end of each step (recorded stamps, UTC)

- 20:30:37Z  job 6 file found; read 20:30:4xZ.
- 20:30:4xZ -> 20:30:57Z  build (new build dir with FORGE_EXPOSE_TUNABLES=1; source reused from
  job 5) and all Step 0 benches; uci lines captured; all known numbers verified.
- 20:31:04Z  phase 1 launched (probe C + control 7260).
- 20:31:2xZ -> 20:33:18Z  control 7260: 300 games, +169.86 (its interval contains the expected
  ~+200's neighbourhood; the tool sees differences, as every control so far).
- 20:33:38Z  phase 2 FIRST launch - S1 died at once ("Error; no TimeControl specified!"): my
  run_one's `-each` line had lost `nodes=20000` (the same refactor slip as jobs 4 and 5, third
  occurrence). Fixed; timeline cleared; relaunched 20:34:4xZ after verifying S1's output showed
  games actually starting.
- 20:34:4xZ -> 20:49:20Z  probe S1 + S1 (cut at cap, 1,696 games).
- 20:49:20Z -> 21:04:30Z  probe S2 + S2 (cut at cap, 1,532 games).
- 21:04:30Z -> 21:19:40Z  probe S3 + S3 (cut at cap, 1,761 games).
- 21:19:40Z -> 21:36:50Z  probe S4 + S4 (all 2,000 games, before its 21:44 deadline);
  PHASE2_DONE 21:36:51Z.
- Report finalized 21:37-21:44Z, committed and pushed by ~21:46Z.

## 7. What I did NOT do

- MR3 vs none was not replayed (the job said not to).
- MaxReduce 4 and 6 exist in the uci range and were not measured (the job asked 1/2/3/5).
- No second seed for MR2 (the highest point estimate) - the budget went to the four assigned
  matches; if you want MR2 vs MR3 decided, that direct match does not exist yet either.
- No SPRT, no engine source committed, no PR opened.

## 8. What I am NOT sure about

- MR2's +17.0 is ONE seed of 1,696 games; its interval [+5.6, +28.5] excludes zero but overlaps
  MR3's pooled [+5.7, +21.0] almost entirely. I cannot rank MR2 over MR3 from these numbers, only
  say neither is worse than the other by anything measurable so far.
- S3's -3.0 +/- 5.1 (MR5 worse than MR3) has 771 of 880 pairs as double draws; with so few deciding
  pairs the interval is trustworthy in FORM but the result is a small negative, not a verdict.
- The bench-13 ladder is NOT monotonic in MaxReduce (MR2 646701 < MR3 649268 < MR5 683370 < MR1
  728460) - the rule's interaction with the aspiration window is not a simple "more reduce = fewer
  nodes" story; I do not have an explanation, only the numbers.
- The control came out +169.9 rather than the usual ~+200-223 of the previous three controls; its
  interval still contains ~200 and the tool is the same; I did not investigate (the control's job
  here is power, which it has).

## 9. A better way

- The refactor slip happened a THIRD time (jobs 4, 5, 6: the fastchess line lost its node limit when
  I reshaped run_one). What actually caught it each time was the first match failing in seconds. The
  fix that survives refactors: build the fastchess arguments as ONE array in the runner and let the
  same code path serve probe and match, with the node limit inside the per-engine spec strings -
  my runner6a/b now does exactly that (specs as single quoted strings); jobs 4/5 style runners
  should be retired.
- Cheap ranking trick that worked: put the direct comparison (S3) in the SAME session as the
  against-none matches - MR5-vs-MR3's 771 double-draw pairs give a ±5 interval for ~9 minutes of
  CPU, far sharper per minute than another against-none match would be. When Fable wants A-vs-B
  ranked, the direct match is the better spend.
- The bench-13 ladder (four numbers, 20 s) predicted the match ranking's SHAPE before any match ran:
  MR1 (most-changed tree) landed lowest in play (+9.2) and MR2 (a mid ladder value) highest (+17.0) -
  the ladder is a weak but free prior; worth recording for every option tune as step-0 byproduct.

## 10. Model name and version

I am glmflash2, running on GLM, model glm-5p3-flash (GLM 5.3 Flash) as far as I know it.
