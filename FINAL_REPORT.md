# Astra R13 data QC

Base: `3e9009413eadac5dbeae3170a131117c04aa9e11` (`astra-r8-datafilter`).
Delivery branch: `astra-r13-dataqc`, in the contained checkout `D:/a13`.
Repository: https://github.com/couns0538-sketch/dwqww/tree/astra-r13-dataqc

QC integrity, the scoped evidence pack, the final test suite and independent
readback are PASS. Authentic production game separation remains **UNVERIFIED**.
No training, GPU workload, engine-source edit or strength claim was made.

## Completed

- `D:/a13/p5qc/REPORT.md`: final R14-B jobA audit of 999,921 rows across 100 shards,
  compared descriptively with all 440,000 rows in the old 22-shard sealed prefix.
  Verified manifests, row ranges, final assembly bytes, original source-row joins,
  score/sidecar alignment and complete consumed-input hashes.
- `D:/a13/p5qc/mate_rows.jsonl`: 3,718 separately flagged rows at inclusive
  `abs(score_stm) >= 30000`: 2,717 new and 1,001 old. Each record retains the
  producer label object and exact input path/line. Original files were not edited.
- Score histograms and moments, White/STM WDL, side-to-move, piece count,
  material-phase proxy, split distributions, paired source-score deltas and
  exact six-field-FEN duplicate rates are recorded. Both cohorts have zero exact
  duplicate rows; this is not game-separation evidence. Non-mate descriptive
  profiles cover 997,204 new and 438,999 old rows, without creating training data.
- `D:/a13/evidence/review/independent_readback02.json`: separate CSV/FPOS code
  agrees with counts, score sums, WDL/STM, duplicates, paired deltas, all mate
  producer objects/source locations, and non-mate profile sums.
- JobB is reproducibility-only: final labels equal jobA, SHA256
  `974fb9a9ee3499227eba72c20cb47181a42d182224a33e93eba435ff7199ba10`,
  MD5 `2614e82d55bc5e9572c24d3900a8810a`. It is not counted twice.
- `D:/a13/pgnpack/runs/pack02`: fresh scoped PGN-mode evidence pack, 17 payloads.
  The inherited final PGN pack already records PASS; its protected-root checks
  were not rerun. The new pack binds successful QC/test receipts, current source
  hashes, exact per-test collection/call coverage and QC completion hashes.
- Root seals independently verified: `D:/a13/p5qc` has 18 payloads and
  `D:/a13/pgnpack` has 41. Previous runs remain retained under their original names.
- Reusable R13 tools are in `D:/a13/tools`; wrappers are
  `D:/a13/p5qc/reproduce.ps1`, `D:/a13/p5qc/test.ps1` and
  `D:/a13/pgnpack/reproduce.ps1`. Each requires a fresh run name.
- New packaged skill: `D:/a13/.agents/skills/relabel-data-qc/SKILL.md`.
  Updated copied skill: `D:/a13/.agents/skills/npt-data-holdout-check/SKILL.md`.
  Package/link validation passed. The copied legacy helper is byte-identical,
  was not executed, and no globally installed skill was changed.

## Tests and post-work review

Final suite: **603 tests and 60 subtests passed**, zero failures/skips, 134.84 seconds.
Scope is the complete inherited datafilter suite plus all R13 tests. The full log,
collection, per-test outcomes and process/source receipt are retained for commit
under `D:/a13/evidence/test_logs/full-suite06/`. Failed attempts and regressions
remain in adjacent named directories. Sixteen dependency/deprecation and inherited
scheduler-fixture warnings are retained; no optimizer/training call was added.

Post-main direct review started `2026-11-03T18:44:47Z`.
Completed 2026-11-03T19:45:52.3475514+00:00 after 3665.348 seconds of direct post-work review. Closure receipt: D:/a13/evidence/review/REVIEW_COMPLETE.json.

The 1,200-second seeded property run passed 4,098,816 legal-position cases and
41,276 PGN-format pairs. Its exact source revision is recorded in
`D:/a13/evidence/review/property01/REPORT.json`. A later narrow Windows null-sink
compatibility fix is covered by the final suite; parser/FPOS/game-hash bytes did
not change. No subagents or external review service were used.

Confirmed fixes include Windows path aliases/device names, invalid FEN text,
line limits, boolean count fields, contradictory completion totals, same-size
input mutation with restored mtime, buffered progress capture, supervisor error
cleanup, source-change refusal, exact test coverage qualification and manifests
or payloads changing during pack verification. Native deadline, source-mutation
and reparse-entry probes passed. Adversarial copied QC bytes and omitted test
results were rejected before any pack output was created.

Details and retained failures: `D:/a13/evidence/review/REVIEW_LOG.md`.

## PENDING / UNVERIFIED

- Authentic original-game bindings for selfplay001/002 and complete holdouts013/014
  were not recovered. The bounded PC/GitHub search, exclusions and rejected
  candidates are in `D:/a13/pgnpack/SEARCH.json`; this is not global absence.
  Per user instruction, recovery stopped and effort moved to QC and bug review.
- R14-B IDs are inferred groups. Old440k and corrected1k have no recovered authentic
  game mapping. Historical PGNs have boundaries but no authenticated linkage to
  these populations. The protected archived PGN input was not opened. Every source
  disposition is listed in `D:/a13/pgnpack/REPORT.md`; authentic overlap remains null.
- Production train/holdout game-separation proof is therefore UNVERIFIED. The PGN
  helper hashes initial full position plus normalized legal mainline movetext;
  fixture success and disjoint inferred IDs cannot supply missing original bindings.
- The old source job is incomplete beyond its sealed 440k prefix. Those labels
  searched reconstructed state with lost castling/EP/clocks. The separate corrected
  1k proof at `D:/o14a/p5/job_fix1k` is neither pooled nor a repair of old labels.
- Protected historical pack checks, training readiness and engine qualification
  are not claimed. There is no strength result or requested production change.

## Inputs, containment and frozen engine reference

Main input: `D:/o14b/r2/proof/jobA`; reproduction-only input:
`D:/o14b/r2/proof/jobB`; old sealed prefix: `C:/o13/p5/job1`.
Physical new-label sources: `D:/grok-pc-data/selfplay_out/forge_selfplay_001.txt`
and `D:/grok-pc-data/selfplay_out/forge_selfplay_002.txt`.
All 446 consumed input paths have full SHA256/MD5 receipts in
`D:/a13/p5qc/INPUTS.json` and full absolute-path MD5 lines in
`D:/a13/evidence/INPUT_MD5SUMS`.

Read-only runtime: `D:/a11/runtime/python/python.exe` (Python 3.12.10), packages at
`F:/nnue_pytorch/venv/Lib/site-packages`, NPT fixture runtime at
`F:/opus_scratch/r6/nnue-pytorch-amd`. Actual jobs used Idle priority, one pinned CPU
lane, native thread limits and hidden GPU devices. All new files, Git metadata,
temporary files and caches stayed under `D:/a13`. The D: admission floor was
53,687,091,200 bytes (50 GiB) plus the next bounded allocation. Busy CPU admission
was deferred rather than overridden. The audit hook is defense in depth, not an
OS sandbox for arbitrary native code.

Selected interpreter/module/native-reader hashes captured at final review are in
`D:/a13/evidence/RUNTIME_IDENTITIES.json`; this is not a complete environment freeze.

No engine executable was run for R13. Frozen reference only: FD3A5190 SHA256
`fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072`;
bench d11=312866, d13=862329, d16=3024920, d20=12389307, d22=34048354;
perft5=4865609; kiwipete d5=193690690. No `.nnue`, engine lock, live gate,
`handoff_v7`, `C:/forge_nnue_train` or `F:/forge_push` was modified or opened.

## Full MD5s and publication

| Absolute path | MD5 |
|---|---|
| D:/a13/p5qc/REPORT.md | 5933f78bc4fa930c1eb88fb83810b9ca |
| D:/a13/p5qc/statistics.json | 062429777cecdb8e522449f0264618b4 |
| D:/a13/p5qc/INPUTS.json | 60e8911dd8cb95c8a53bee9fd9bec3d0 |
| D:/a13/p5qc/mate_rows.jsonl | aa78162b2280c51d72d12ccbb5eb3b16 |
| D:/a13/p5qc/SHA256SUMS | 31517ac969465205f57ffaef637a13a7 |
| D:/a13/p5qc/MD5SUMS | 86cc94bb44e076cccb136932020c3894 |
| D:/a13/pgnpack/REPORT.md | 9299f091866f942b93435db4c6df55bb |
| D:/a13/pgnpack/PACK_STATUS.json | 0978d80062c89992bcf9e24c6b8cdd0f |
| D:/a13/pgnpack/SHA256SUMS | e06ff9abe02c5ade7e3231cfaa28da1a |
| D:/a13/pgnpack/MD5SUMS | de5632db78aa8c46a918268591f0d013 |
| D:/a13/evidence/test_logs/full-suite06/output.log | 71016a1d168d52ac91325ded105fe485 |
| D:/a13/evidence/review/property01/REPORT.json | cea42a1ed95807adb5b98c0a89e372e4 |
| D:/a13/evidence/skill_receipt.json | 7d21564b804526b27ac1d54adc3d3dab |

Directory SHA256SUMS/MD5SUMS cover every contained payload, including retained
local run artifacts. `D:/a13/evidence/ARTIFACT_MD5SUMS` adds absolute paths/full MD5s
for delivery files, code, tests, skills, logs and this report; it excludes itself,
Git internals and scratch/cache directories. Large duplicate indexes and earlier
raw run directories stay local and ignored; the complete small pack02, scripts,
final QC outputs, manifests and full test logs are committed. Hashes certify
bytes, not provenance or readiness.

The commit and non-force remote-HEAD readback are recorded after publication in
`D:/a13/evidence/runs/publication/receipt.json`, with the exact commit also reported
in the completion message. No skip-CI marker is used.
