# Astra A1: Forge training-data work, 2026-10-30

**Current status: tools and bounded native experiments complete; full 10M filtering is RUNNING.**
Final full-data removal rates and output acceptance remain pending. No engine strength, label-quality improvement or Elo gain is claimed.

## Source and data identity

- Branch: `astra-a1-data`; starting checkpoint `e0d76ce8a6450573b503852aeca12b929bf4a17a`.
- Engine source: unchanged from `926c55f33227bc4a030d7ce5b1140528aeba75af`; no change to the trainer, accepted net, main or Opus branches.
- Fresh Release engine SHA256: `8733bcb06e2ba0d7ecb9b2e29de9fcedb870db71cca8ad50bfeea015cbbd9bbc`.
- Native data probe SHA256: `ddf8713016863512ffd6227c5b3f623d53a87e9964f0bbb8c94c146525d58ff3`. A fresh standalone build reproduced it byte-for-byte.
- [User-supplied release](https://github.com/couns0538-sketch/dwqww/releases/tag/data-sample-10m-20261030): archive SHA256 `1d6160dd859740fe617c8dc6c6e6ad8fbcdd0ba40b59ee9cee84342f9202cca5`, matching both the published digest and downloaded bytes.
- `forge_selfplay_003.pos`: 10,000,000 records, SHA256 `d322089c80c8c753bf9eb744d50b530af6d33a5f06bdd3aa5b86a51b61febb10`.
- Matching original `.txt`: SHA256 `ccab2719f8b59ce2853af7f26f18b15876c5f6160867370983d147760af086f7`.

All **10,000,000 rows** passed exact board/STM/score/White-result/order/count comparison against the full-FEN sidecar. Source hashes remained unchanged. This verifies the supplied shard, not all 305M historical positions. FEN preserves current castling, en-passant and clocks; it does not encode prior repetition history.

A separate read-only 10M profile found castling rights in **21.70414%** of rows
and an EP target in **3.55647%**, reinforcing why reconstruction would lose real
state. Halfmove clocks are at least 50 in **3.168%** and 90–99 in **0.4735%**;
none reach 100. Original stored scores span **−3000..3000 cp**. Newly relabeled
native scores retain mate-band values, so raw cp differences can include a
different clipping convention; they are not label-quality measurements.
The original profile, scalar-column crosscheck and hash receipts are in
`validation/astra-a1-data/source_profile`.

## Job 1: filter and 10M measurement

`tools/data/filter_positions.py` creates new FPOS, matching current-engine FHCE, full-FEN sidecar, original native IPC, row provenance and an audited decision waterfall. It never rewrites input shards. It preserves original scores/results; deeper labels are a separate job.

The frozen full-run protocol uses 1,024 nodes, one search thread and 1 MB Hash per cold probe; three worker processes; batch 256. Ordered first-drop rules are supplied holdout → result disagreement → exact duplicate → near duplicate → in check → terminal → insufficient teacher budget → capture bestmove → promotion bestmove. Rates are conditional on that order, not independent marginal frequencies.

- Decisive outcome disagreement: at least 400 cp in the opposite STM direction. Draw disagreement: abs(score) at least 800 cp. These are original starting hypotheses.
- Exact identity: board32 plus STM; SHA256 with stored full-key collision checks. Only retained rows seed duplicate rejection.
- Near identity: a retained row within 64 original input indices, same STM/result/castling/EP/pawn and king placements/piece inventory; one nonpawn/nonking relocation and source scores within 25 cp. Clocks are ignored for this explicit sampling heuristic; no positional-equivalence claim.
- Native errors abort. A valid search that completes no iteration has an explicit `insufficient_budget` response and is counted separately; it never receives a made-up label.
- Known holdout input: verified 1.5M-row 013 head, with 1,499,915 unique feature identities. Complete 013, 014 and authenticated game IDs are unavailable. Only exclusion against the supplied head can be certified.

The first 10k pilot retained 9,274 rows: 455 capture-best-move, 2 promotion, 268 near-duplicate and 1 disagreement drops. Those figures are **pilot-only**. Full attempt 1 stopped safely at original row 27772 because 1,024 nodes completed no iteration; its partial data and error are preserved. Full attempt 2 uses the explicit insufficient-budget exclusion. Its exact loaded source is archived in `validation/astra-a1-data/filter_full10m_v2_protocol`.

Current tools add tested summary-last publication hardening after that run started; filtering policy is unchanged. The completed full run must pass the independent bundle checker before acceptance. A path containing `.pos` alone is not a seal.

## Job 2: real fixed-node relabeling

`tools/data/relabel_positions.py` preserves board, STM, White result and full FEN; writes the current native score and `Evaluator::evaluate_uncached` HCE. Deterministic slice: 256 rows, start 0, stride 39062, from the supplied 10M shard. All four budgets completed and have original responses, new paired files and CPU receipts.

| Nodes/position | Median completed depth | Pipeline CPU seconds | Positions/core-hour | Capture/quiet changes vs 65536 |
|---|---:|---:|---:|---:|
| 1,024 | 5 | 4.164 | 221,314 | 15 |
| 4,096 | 7 | 6.955 | 132,500 | 14 |
| 16,384 | 9 | 9.987 | 92,279 | 7 |
| 65,536 | 12 | 21.189 | 43,494 | 0 |

CPU accounting includes the entire input hash/sidecar-count scan and owned child CPU, so these small-slice numbers are not steady-state full-corpus estimates. Query-only CPU is also retained in `budget_sweep_256.json`. Windows throughput is unverified.

Complete portable sealed copies are under
`validation/astra-a1-data/sealed_bundle_copies/relabel_256_<budget>`; all four
pass the full-record bundle checker. Earlier sibling folders retain the original
console logs alongside their manifests and are evidence assemblies, not seal
roots. The packaging boundary was corrected without altering original outputs
or deleting those earlier copies.

At 1,024 versus 65,536 nodes, 10 capture choices became quiet and 5 quiet choices became captures. Median absolute score difference was 55.5 cp; mate-band outliers are preserved. Higher budget is a sensitivity reference, not ground truth. The full 10M filter is therefore a **budget-specific screening cohort**, pending training/strength evaluation. The original teacher's budget is unknown.

A native/UCI crosscheck matched all 32 completed scores and returned bestmoves. Two UCI abort messages report attempted depth 6 while `SearchInfo.depth` remains completed depth 5; another root emits an initial cp0 placeholder without completing an iteration. Initial comparison failures and the source-grounded explanation are retained. The probe correctly leaves the latter unlabeled. A public SearchInfo tuple may contain a partial-iteration bestmove alongside its previous completed score/depth; it is not a newly proven completed PV.

Reconstruction is opt-in and never counted as exact. A derived FEN-only sidecar requires an explicit origin, and known reconstructed provenance cannot silently upgrade to original state.

## Job 3: opening variety

`tools/data/generate_openings.py` uses deterministic random legal early moves, checking every selected position against the declared teacher's ±150 cp band. The recommended **standard R8 book** additionally requires final abs(score) at least 25 cp:

- 64 unique positions from 338 attempts; final abs(score) 25–148 cp, mean 67.578125; White/Black advantages 32/32.
- Fresh native audit: 562 legal plies, 626 score/depth/node checks, zero mismatches.
- Book: `validation/astra-a1-data/openings-unbalanced-25/standard-one/openings.moves`.
- Book SHA256: `7237efd96cb0b9b60a0717679d867e5ce04eddd2d46e56234cef77820066ee81`.

The min-zero control was generated twice with identical book/metadata bytes; its combined standard/optional-FEN audit covered 707 plies and 787 comparisons. Sixteen no-castling Chess960-style FENs were also produced. They are **not true Chess960 and cannot be loaded by unchanged R8**. Standard books match R8's exact move-only contract at `5dd3a57d6f286f09b8881671ba8a368f6d34f717`. Windows R8 execution is unverified. A second min-25 generation using the current helper reproduced the book, settings and generation-statistics bytes; metadata differed only in its 64 helper-SHA fields. Full comparison and original IPC are in `validation/astra-a1-data/openings-currenthelper-repeat`.

Opening generation and its native audits used the earlier helper SHA256
`ad2fa25e384d71fc30bf5c22108da0336675d93a21fd9b11604964acb771c498`.
The full filter and relabel receipts instead identify the later `ddf871…`
helper listed above; their original evidence retains these distinct identities.

## Job 4: trainer compatibility and experiment plan

[ASTRA_A1_BLEND_PLAN.md](ASTRA_A1_BLEND_PLAN.md) gives exact commands and matched two-seed controls: lambda 1→1, 1→0.8, 1→0.6, followed by separate filter/deeper-label/variety ablations. Lambda is teacher weight; the current trainer blends **linearly in optimizer steps**, despite its misleading “cosine blend” message. Only its learning rate uses cosine decay. No GPU or live trainer was touched.

The unchanged trainer's mmap reader matched all board/score/meta/HCE values in both initial 256-row relabel outputs, plus board/score/meta for 256 strided original rows. Real CPU smoke: 512 train and 512 heldout rows, four updates, initialization check PASS, train MSE 0.004578, holdout teacher MSE 0.005856420306372456. Training positions had zero overlap with the supplied 013 head and the chosen smoke holdout. This proves format/finite-loss compatibility only; the smoke export is not an engine candidate.

## Correctness and raw benchmarks

Fresh GCC 14.2 Release: H256, `-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off`; all Forge build options OFF. Full helper executable FMA count: **0**.

| Depth | OFF nodes | Status | Observed NPS (contended; not comparable) |
|---|---:|---|---:|
| 11 | 312866 | PASS | 1012511 |
| 13 | 862329 | PASS | 865792 |
| 16 | 3024920 | PASS | 876280 |
| 20 | 12389307 | PASS | 720601 |
| 22 | 34048354 | PASS | 747067 |

Startpos perft5 **4865609**; kiwipete perft4 **4085603** and perft5 **193690690**. The first extra perft5 harness used an unsupported bare command; its empty result and corrected `go perft 5` run are both retained. Native probe tests: 9/9. ASan/UBSan with leak detection: 9 tests plus all 256 real-FEN responses equal to Release excluding timing, no diagnostics. Initial sandbox/ptrace failures are retained; the successful run used the supported untraced path. Existing core compiler warnings remain recorded, not silently removed. The complete pre-existing engine ctest suite was not rerun for this tool-only change; no claim that its historical failures were repaired here.

Python policy, format, process, publication and manifest tests: **129 pass**. Discovery reports 130 cases with one explicit native-fixture skip; its standalone **9-test** invocation also passes. Latest full-discovery log: `validation/astra-a1-data/all_unit_final_transport.log`. Original earlier runs remain preserved. The archive namespace regression failed before the correction and passes afterward, including under `python -O`; failed implementations and experiments remain alongside their corrected tests.

The independent review took 24.3 minutes in total: the 19.6-minute main review
in [ASTRA_A1_FINAL_REVIEW.md](ASTRA_A1_FINAL_REVIEW.md), plus a 4.8-minute
[recovery-command addendum](../validation/astra-a1-data/final_review_addendum/REVIEW.md)
(rounding explains the displayed sum). It found and rechecked
one Windows archive file/directory collision repair; independently replayed
1,024 saved relabel rows and 5,998 opening requests; and verified four
no-overwrite boundaries. The addendum repaired direct-download setup, enforced checksum comparison and
outside-seal verification logging. Ten independent auditor regression tests
also pass, including corrupt native evidence and original holdout coverage.
No concrete finding remained open. Final full-data
acceptance and transport publication are separate checks performed after the
active filter exits.

## Reproduce and review

Use [ASTRA_A1_WINDOWS.md](ASTRA_A1_WINDOWS.md) for exact PowerShell/MSYS2 build and data commands at Idle priority on explicitly chosen spare logical CPUs. Windows runtime remains **UNVERIFIED**; no hard Windows memory cap is claimed. Linux tools use Python standard-library orchestration; PyTorch is needed only for optional trainer checks.

```bash
python3 tools/data/build_probe.py --output /NEW/probe-build --cxx g++-14 --jobs 1
python3 tools/data/verify_sidecar.py --pos /DATA/forge_selfplay_003.pos --sidecar /DATA/forge_selfplay_003.txt --out /NEW/sidecar-check
python3 tools/data/filter_positions.py --pos /DATA/forge_selfplay_003.pos --sidecar /DATA/forge_selfplay_003.txt --probe /NEW/probe-build/forge_data_probe --out /NEW/filter --probe-nodes 1024 --probe-workers 3 --hash-mb 1 --batch-size 256 --disagreement-cp 400 --draw-disagreement-cp 800 --near-window 64 --near-score-delta 25 --holdout /DATA/forge_selfplay_013_head.txt
python3 tools/data/check_data_bundle.py /NEW/filter --full-records > /NEW/filter-verification.json
python3 tools/data/relabel_positions.py --pos /DATA/forge_selfplay_003.pos --sidecar /DATA/forge_selfplay_003.txt --probe /NEW/probe-build/forge_data_probe --out /NEW/relabel --nodes 65536 --workers 1 --count 256 --stride 39062
python3 tools/data/check_data_bundle.py /NEW/relabel --full-records > /NEW/relabel-verification.json
```

All output folders must be new. Keep verification receipts outside sealed folders. Full position/game holdout clearance, production training gains, equal-time matches and Elo remain unverified. GitHub contains source and compact original evidence; final full-run artifact publication is pending.

Existing coordinator/validation/engine-development skills were reused. [The skill addendum](ASTRA_A1_SKILL_ADDENDUM.md) improves the existing validation workflow without duplication; it is **proposed, not installed** because a provider editor/skill-creator is unavailable. GitHub CLI/Git and native tools were usable; optional connector failures were not pursued.

## Next action / continuation

Finish and independently verify the active 10M run; publish its original evidence and output hashes; replace the RUNNING status with measured full-data rates. Current run directory `/tmp/astra-a1-filter-full-10m-v2`, original probe frozen at the SHA above. A supervisor verifies branch/engine-change guards and pushes checkpoints about every ten minutes. Do not restart this completed preprocessing or replace the engine base with an older lock.

Then review the complete 013/014/game-ID coverage and choose a teacher budget using the saved sensitivity experiment before the matched training ablations. No data or smoke network is automatically installed into training or the engine.

If no historical game-ID mapping or source PGNs were retained, flat position
files cannot prove whole-game isolation retrospectively. Future generation
should retain game identifiers before splitting holdouts. A separate candidate
data ablation could examine high halfmove clocks because the NNUE feature input
omits that context; the measured clock frequencies above motivate investigation,
not an additional filter or a claimed gain in this run.

Earlier checkpoints are retained in [ASTRA_A1_CHECKPOINT_HISTORY.md](ASTRA_A1_CHECKPOINT_HISTORY.md) and Git history. IDEA_SOURCE: user's data task, same-project FPOS/FHCE/native search/trainer/R8 contracts; original implementations and thresholds, no other-engine code or tuned constants.

Checkpoint 20261030T031548Z: full10M status RUNNING, processed 2868992, kept 2641524. Final independent bundle verification is still required. No Elo claim.

Checkpoint 20261030T032550Z: full10M status RUNNING, processed 3499520, kept 3222140. Final independent bundle verification is still required. No Elo claim.

Checkpoint 20261030T033552Z: full10M status RUNNING, processed 4167424, kept 3835087. Final independent bundle verification is still required. No Elo claim.

Checkpoint 20261030T034554Z: full10M status RUNNING, processed 4805120, kept 4421349. Final independent bundle verification is still required. No Elo claim.

Checkpoint 20261030T035557Z: full10M status RUNNING, processed 5398528, kept 4967198. Final independent bundle verification is still required. No Elo claim.

Checkpoint 20261030T040600Z: full10M status RUNNING, processed 5920512, kept 5446810. Final independent bundle verification is still required. No Elo claim.

Checkpoint 20261030T041603Z: full10M status RUNNING, processed 6424832, kept 5911136. Final independent bundle verification is still required. No Elo claim.

Checkpoint 20261030T042605Z: full10M status RUNNING, processed 7004416, kept 6445540. Final independent bundle verification is still required. No Elo claim.

Checkpoint 20261030T043607Z: full10M status RUNNING, processed 7613696, kept 7007403. Final independent bundle verification is still required. No Elo claim.

Checkpoint 20261030T044611Z: full10M status RUNNING, processed 8239616, kept 7584637. Final independent bundle verification is still required. No Elo claim.

Checkpoint 20261030T045615Z: full10M status RUNNING, processed 8883456, kept 8177804. Final independent bundle verification is still required. No Elo claim.

Checkpoint 20261030T050617Z: full10M status RUNNING, processed 9486848, kept 8733885. Final independent bundle verification is still required. No Elo claim.
