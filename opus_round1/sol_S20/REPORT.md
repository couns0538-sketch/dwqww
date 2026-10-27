# S20 [Sol leftover] Relabel/rescore tool + 1M sample — DONE (CPU on the PC; sample manifest, not committed: 63.5 MB)

`SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 12; Sol's inventory `jobs[]` S20 (spec line 474; NOT_STARTED, Sol left no
S20 files).
- **Branch:** `opus-sol-S20` = `d4f4312` + `0d99f02` cherry-picked (`0d919457`) + this job.
- **Scope:** tool and evidence only (`[skip ci]`); no engine change.
- **Deliverables:** the tool `opus_rescore.py`, the 1M rescored sample (manifest `S20_SAMPLE_MANIFEST.md`), stats
  (`results/`), this report.
- **Machine exclusive:** no (fastchess gates, NNUE training, self-play and sub-agents ran throughout; every run at
  Idle, one thread).

**The spec:**
- a fixed-depth re-search with the lock (nice 19);
- WDL/score blend options compatible with the D filter;
- a 1M-position rescored sample with stats and sha256;
- pass: deterministic at a fixed depth; the output loads through both v3b loaders (RAM + mmap); the sign convention is
  checked (STM score, WHITE result);
- crew rework 10:30: blend defaults follow the f006 recipe.

## Acceptance
| item | result | evidence |
|---|---|---|
| fixed-depth re-search with the lock, nice 19 | **DONE**. `opus_rescore.py`: depth 8 (default), Threads 1, Hash 16, `ucinewgame` before every position, Idle priority. The engine is a box-recipe build of the AL1 lock sources: `uci_check --full` ALL OK (bench 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690), FMA 0, sha256 `04016f51…` | `logs/step0_engine_build.log`, `logs/step0_engine_identity.log` |
| WDL/score blend options compatible with the D filter | **DONE**. `--blend L` writes `L·score + (1−L)·result` in cp space, through the trainer's sigmoid with K = 2.25. The output keeps the D filter's text format (`FEN \| stm_cp \| white_result`); Sol's D filter ran on the pilot and on the full output without changes | `README.md`, `logs/step4_pilot_loadcheck.log`, `logs/step9_full_loadcheck.log` |
| blend defaults follow the f006 recipe | **DONE**. The default `--blend 1.0` writes the pure re-search score. f006 blends inside the trainer (blend 1.0 → 0.6 over the run), so pre-blending the labels would blend twice | `README.md` |
| 1M-position sample from self-play generated here, with stats and sha256 | **DONE**. Input: the first 1,000,000 lines of an 11,700-game lock self-play run made for this job (1,110,116 positions; `forge_selfplay.py` with a copy of the lock exe, 5000 nodes/move, Idle). Output `rescored.txt`: 1,000,000 lines, 63,544,800 B, sha256 `9b93882d…` (manifest) | `logs/step5_full_rescore.log`, `logs/step7_full_summary.log`, `results/full_summary.json`, `S20_SAMPLE_MANIFEST.md` |
| deterministic at a fixed depth | **PASS**. The first 2,000 pilot lines rescored twice into new folders gave identical output (sha256 `be13d8d0…`). The full run's chunk 0, first 10,000 lines, equals the pilot run made 2 h earlier. The input pilot equals the first 10,000 input lines | `logs/step6_determinism.log` (its first `head` used a wrong path and hashed nothing; the next lines repeat the comparison with the right path) |
| loads through both v3b loaders (RAM + mmap) | **PASS** on all 1,000,000 rows. fen2bin + hce_dump (rc 0; `.pos` 35,000,016 B sha256 `4e6ef583…`, `.hce` 2,000,016 B `11c7dd82…`); the trainer's `load_set` and `load_set_mmap` (`ast`-extracted from a renamed trainer copy; the trainer never ran) both load 1,000,000 rows, with identical boards, scores, meta and hce arrays; the loaded rows equal the text (score, STM bit, WHITE result). Supervisor "adopted running job" lines: 7 before and after | `logs/step9_full_loadcheck.log`, `results/loadcheck.json` |
| sign convention (STM score, WHITE result) | **PASS**. In decisive games the STM score's sign agrees with the side to move's result for 554,984 of 604,320 positions (91.8%; 2,131 zero scores). Material spot check: side to move up ≥ 5 points → score > 0 in 82,470 of 83,267; down ≥ 5 → < 0 in 78,830 of 79,603 | `logs/step8_full_check.log`, `results/full_check.json` |
| tests | **PASS** 7/7 (format, sign, mate/clip, blend formula, resume, refusals, determinism) | `logs/step1_tests.log` |

## Stats (1,000,000 positions; `results/full_summary.json`)
- **Run:** 20 chunks of 50,000 lines; 0 bad lines; 1,037 mate scores (written as ±3000); 22 cp scores clipped at
  ±3000. 6,194 s summed over chunks, i.e. 161 positions/s at Idle on the loaded PC (chunks 245-458 s).
- **Against the original 5000-node labels:**
  - new − old: mean +0.64 cp, mean |d| 50.5 cp, max |d| 3307 (mates);
  - on 2,000 every-500th positions: correlation 0.992, mean |d| 46.6 cp, median |d| 27 cp, sd 84.6 cp.
- **Label distribution:** 34% of the new labels are within ±100 cp, and 1,067 sit at the ±3000 bins (100 cp
  histogram in the summary).
- **Sol's D filter** (threshold 300, holdout = the data32 h000 copy) keeps 948,163 and drops 51,837: 51,183 draws with a
  large score, 333 losses with a positive score, 256 wins with a negative score.

## Findings
1. **Depth-8 labels sit close to the 5000-node labels** on this self-play: correlation 0.992 and median |d| 27 cp. The
   relabel changes noise more than bias (mean +0.15 to +0.64 cp).
2. **About 5% of the rows are "draw with a large score"**, which the D filter would drop. That is a property of the
   self-play games, not of the rescoring: the pilot had 9.4%.
3. **Throughput at Idle on the loaded PC is about 160 positions/s per process.** 1M positions take about 1.7 CPU-hours
   at depth 8. Rescoring the full 242M-row training set at this depth would take about 420 CPU-hours: a multi-core or
   overnight job, not a smoke.

## Files
- **Tools:** `opus_rescore.py` (sha256 `d2755e39…` at the full run), `opus_rescore_tests.py`,
  `opus_rescore_pilot_check.py`, `opus_rescore_loadcheck.py`, `opus_rescore_summary.py` (aggregates `progress.json`).
- **Docs:** `README.md`, `IDEA_SOURCE.md`, `REPORT.md`, `S20_SAMPLE_MANIFEST.md`.
- **Evidence:** `logs/step0`-`step9`; `results/full_summary.json`, `results/full_check.json`, `results/loadcheck.json`.
- **Index:** `FILES.txt`; checksums: `SHA256SUMS`.

## Left / UNVERIFIED
- Training on the rescored sample and any strength effect: not run (no GPU, nothing queued, no Elo claim).
- Rescoring the production shards: not done (CPU time above).
- The sample stays in `F:\opus_scratch\rescore_d8` (sha256 in the manifest).
