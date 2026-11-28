# RESULTS_AND_STATE_2811: Forge on 28 Nov 2026, and every result since the debate branches of 23 Nov

Written by Opus at 15:02 PC on 28 Nov 2026. Each result names its source, a block marker in our lab's PLAN.md. The raw
game files stay on the owner's PC. "Recounted" means Opus counted the raw PGN itself.

## Why the debate branches are out of date
The debate branches of 23 Nov (`debate/forge-plan-20261123`, `debate/server-plan-20261123`, commit df6a734) lack
today's state. VERIFIED 28 Nov 14:51 PC by a script comparing them with the live loop:
- Their `loop/LOOP_OPTIONS.txt` is the 23 Nov state:
  - 11 of its 24 values differ from today's tuned ones (LmrQuietBase is 93 there, 132 today);
  - 27 of today's 45 values are missing.
- Only the server package's `workloads/MANIFEST.json` there carries all 45 of today's values.
- Their `source/` is the loop's tree r15dsg plus the Forge 6.5 switch (65 and 16 added lines, nothing else).
- None of the results below are on them.

## The loop today
- The NNUE training loop is STOPPED on purpose until the fixes are placed. It has trained 202 rounds.
- The best net is still round 67's (r0067): 134 rounds without a new best.
  - That stall sent us to look at the data, the filter and the net, not at more rounds.
  - r0202 against r0067 at 250k: -4.86 [-16.64, +6.90] (PLAN-2811-OPUS-R0202-AND-KEEP-NOISY).
- **The engine:** the r15dsg tree (`engine/r15dsg/`), built with clang and PGO by the script beside it, with a
  768-input NNUE (our "v3" net).
  - Its options are `v3_uci_options` in `fixes_2811/loop/config.forge.toml`: 45 values, the big tune's, placed
    24 Nov.
- **The data:** self-play positions are parsed by `forge_parse.py` and trained by `forge_train_v3.py`.
  - The parse drops marked and in-check positions.
  - Today the loop trains WITH `--keep-noisy`, so positions whose best move is a capture, en passant or a promotion
    are kept.

## Results
- Notation: Elo with a 95 % range, from the pentanomial pair statistic.
- "250k" means 250,000 nodes a move. "Clock" means 6 s + 0.06 s a game.
- SPRT bounds are normalized Elo with alpha = beta = 0.05.

| What | Result | Conditions | Verdict | Source |
|---|---|---|---|---|
| The big tune's 40 values against the earlier loop settings | +19.7 [+14.0, +25.5] at 250k; about +50 at 20k, +33 to +37 at 50k | same exe, net r0067 | PLACED 24 Nov | `fixes_2811/results/BIG_TUNE_RESULTS.txt` |
| Training without `--keep-noisy`, seed 1 (R1-skip vs R1-keep) | +15.49 [+6.12, +24.88]; 1,526 games, W 399 D 796 L 331, ptnml [9,154,368,224,8] | 250k, SPRT [0,10], H1; same runner, seed and window r0178..r0202; only the flag differs | proven | PLAN-2811-OPUS-R1-SKIP-NOISY-WINS (recounted) |
| The same, seed 2 | +12.57 [+4.28, +20.88]; 2,019 games, W 518 D 1,056 L 445, ptnml [11,218,484,279,17] | 250k, SPRT [0,10], H1 | proven twice; placed only after Fable's read on Monday | PLAN-2811-OPUS-SEED2-H1 (recounted) |
| The R1-skip net against r0067 (the loop's best) | +30.65 [+18.59, +42.79]; W 277 D 534 L 189, ptnml [4,90,237,152,17] | 250k, 1,000 games | strong at 250k | PLAN-2811-OPUS-R1-SKIP-BEATS-R0067 (recounted) |
| The R1-skip net against r0067 at the clock | running, 2,000 games | clock | pending; result on `from_opus/` | - |
| AspFailHighReduce = 1 | +10.95 [+5.23, +16.67] | 250k | not placed; Fable checks it Monday | PLAN-2711-OPUS-AFH-STAGE3-PASS-R1 |
| The G3 net against r0067 | +22.03 at 250k (probably high; over three 250k matches G3 minus r0067 is about +10.9 +/- 12.5) | 250k | not placed | PLAN-2711-OPUS-G3-250K-AND-GATE-DEPTH, PLAN-2811-OPUS-R0202-AND-KEEP-NOISY |
| The G3 net against r0067 at the clock | -0.35 [-8.35, +7.65] | clock | not placed | PLAN-2811-OPUS-BUNDLE-ARM-A-RECOUNTED |
| The owner's bundle, arm A: SF13 + SF8 + proto_1_corrhist_minor + LmrDeeperShallower, with G3, against live with r0067 | -7.47 [-15.49, +0.54]; W 449 D 1059 L 492 | clock, 2,000 games | not placed | PLAN-2811-OPUS-BUNDLE-ARM-A-RECOUNTED (recounted) |
| Arm B: the same fixes, r0067 on both sides | +3.82 [-3.94, +11.59]; W 439 D 1144 L 417 | clock, 2,000 games | unproven; not placed | PLAN-2811-OPUS-BUNDLE-ARM-B-RECOUNTED (recounted) |
| SF13 alone | -7.28 [-15.62, +1.04]; 1,908 games, H0 | 250k, SPRT [0,10] | rejected | PLAN-2811-OPUS-SF13-ALONE-H0 (recounted) |
| Four single search fixes at 50k nodes (+8.3, +4.9, +7.6, +8.3) | did not carry to the clock (arms A and B) | 50k | a 50k gain is no proof | PLAN-2811-OPUS-BUNDLE-ARM-A-RECOUNTED |

## Where each fix stands
### The net
- Training without `--keep-noisy` is proven twice. It waits for Fable's read and its placement on Monday.
- The net's optimism (SF19 findings 1 and 2; net_sanity S1 and S2) has no known fix.

### The search
- Neon's patches (`neon/patches/`) are not yet behind options, and Fable's eight points are open.
- SF13 is rejected.
- SF8 stays out of bundles until it wins alone at the clock.
- LmrDeeperShallower joins the next bundle.
- Speed cost of the owner's bundle: 0.934x NPS with r0067, 0.821x with G3 (Neon's clean NPS).

### The filter
- Neon's 12-hour quest is in `neon/delivery_12h/`.
- Neon's table of every filter fault, with its measured size and state, is due 18:00 PC today. It will be pushed under
  `from_neon/`.

## The bars we propose for "very good"
They are in `fixes_2811/plans/MONDAY_BARS_2811.md`, and are agreed on Monday before the tests start.
