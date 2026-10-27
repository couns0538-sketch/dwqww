# S07fix — WAC300 lock vs real candidate (S07-1), lock repeats and the 271 vs 283 gap (S07-2) — DONE (advisory)

Branch `opus-sol-S07fix` = AL1 base `d4f4312` + CI baseline `0d99f02` (`e41596a0`) + `87de395b` (tool + evidence) + the
REPORT commit. Tool and evidence only. Every screen = one call of Sol's unchanged tool
`forge_sol_S07_screen_sweep_20261026.py wac300` (sha256 7262dcf8..., the harness of the official 271) on the unchanged
WAC300 suite (9bfb7b42...). Lock = PC h256_e12 lock exe (456743d9, bench d11 308972 = the tool's reference and the 271
run's engine source); real candidate = gate38 `cand_packa_w55` (c98ee238, NonPawnCorr=1 PawnHist=1 NonPawnCorrWeight=55,
from its RUN_INFO.json). Machine exclusive: no. A quiet box is not possible on this PC: fastchess gates (conc 8), NNUE
training, self-play and other agents ran throughout; system CPU busy 93-100% (mean 99.0%), engines at Idle priority
(checked every screen), load sampled every 5 s. All screens are advisory; no Elo or speed claim. Work and results by a
sub-agent; this report text is its hand-back.

## Acceptance

| Item | Command | Result | Evidence |
|---|---|---|---|
| S07-1 lock,cand x3 interleaved, 100 ms | `forge_sol_S07_wac_interleave_v2.py --order interleaved --reps 3 --movetimes 100,1000` | lock 250/251/246 (mean 249.0, range 5); cand 249/252/250 (250.33, range 3); diff +1.3 = within noise | `logs/s07_1_interleaved/` |
| S07-1 1000 ms | same run | lock 283/284/284 (283.67, range 1); cand 282/282/280 (281.33, range 2); diff -2.3 = within the 1-3 pt noise | `logs/s07_1_interleaved/summary.json` |
| S07-2 lock x3 at 1000 ms, load/CPU logged | `--arm lock --movetimes 1000,250 --reps 3 --order blocked` | 281/284/283; all 6 lock 1000 ms screens mean 283.17, range 3; CPU busy 97.6-99.9% per screen | `logs/s07_2_lock_only/` |
| Effort-matched lock (250 ms) | same run | 266/268/267 (mean 267.0) at median 254k nodes/position, 78M nodes total, mean depth 23.9 | `logs/analysis_table_v2.txt` |
| Sol's official 271 | his raw stdout (native evidence archive) | median 292k nodes/position, 91M total, depth 24.2, median 423k nps | `logs/analysis_v2.json` |
| Official 271 | — | unchanged | — |

## Explanation of 271 vs 283-286 (S07-2): search effort (machine speed/load), not the harness
- Same unchanged harness on the PC at 1000 ms: 281-284 (6 runs), equal to the historical lock controls 283/284 that
  came from a different harness (50-position chunks), so the harness lifecycle is not the cause.
- The PC searched ~1.1M nodes per position at 1000 ms (~330M total, ~1.45M nps); Sol's 271 run searched 292k per
  position (91M total, 423k nps; his sweep bench nps 220k-450k on one pinned nice-19 Xeon core of a shared host).
- At an effort close to his (250 ms: 78M total, depth 23.9 vs 24.2) the PC scores 266-268; interpolated to his 91M
  nodes about 269, within noise of 271. Position level: the PC 1000 ms lock always solves 10 positions his run missed
  (WAC.033 049 101 132 190 196 204 205 258 296) and never misses one he solved; at 250 ms the sets nearly coincide.
- CR 286/287 were different-net candidates (Sol's audit), not lock scores; any-PV scoring is not needed to explain it.

## Findings
- The real candidate is within noise of the lock at both movetimes; WAC300 cannot separate them (gate38 itself ended
  at the 1500-game cap, LLR 1.11). Repeat noise is up to 5 points at 100 ms, <= 3 at 1000 ms.

## Quiet-box cross-check (added by the main session, 2026-10-27)
A quiet machine exists in this round's evidence: S26fix's CI ran WAC300 at 1000 ms for the h256_e12 lock
engine on GitHub runners. That engine is S26's "B_lock" arm: bench 308972/745494/2460422/11901452/31111774 = the lock
exe's pins (S43), so the same search as this job's lock.
- **Results:** 284 (run 40505681846, v4), 282 (run 40507421791, v4) and 284 (run 40507421791, v5);
  `opus-sol-S26fix:opus_round1/sol_S26fix/closed_nets/B_lock/SUMMARY_B_lock.md`.
- **The harness differs:** it is Sol's S26 v4/v5 WAC screen, not the S07 sweep tool, so it is a cross-check, not the
  same measurement.
- **Reading:** a quiet, fast box gives 282-284, the same as the loaded PC's 281-284 and far above 271. That supports
  the explanation above: the 271 run was effort-bound (Sol's box searched about a quarter of the nodes per position),
  not a harness or engine effect.

## Left / UNVERIFIED
- The S07 sweep tool itself on a quiet box (the cross-check above uses S26's harness). The historical CR harness itself
  is missing, per Sol.
- Raw screen outputs stay in scratch: `F:/opus_scratch/sol_S07fix/s07_raw_screens.tar.gz` (3,788,395 bytes, sha256
  3b57d77b...; see `logs/raw_archive_sha256.txt`).
