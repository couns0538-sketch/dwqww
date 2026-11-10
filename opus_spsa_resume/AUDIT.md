# AUDIT: existing tuners, receipts and parameter inventory (S1, revised after M1 review)

Everything here was gathered read-only. Evidence ids are git commits on github.com/couns0538-sketch/dwqww, paths on this PC, or files under `evidence/`.

**Revision note (M1).** The first version of this audit said that no gate had a `Qs*` option and that no in-flight candidate touched qsearch. Both statements were false: I had searched only for `QsFutility`/`QsSee` and only matched `CR_PASS_*combo29*`, so 24 `CR_PASS_dr_*.ok` approvals were missed. Sections 3 and 4 are corrected below, and the selection is re-argued in section 5.

## 1. combo29 identity and lineage
| Item | Value | Evidence |
|---|---|---|
| Lock exe | `forge_clang_combo29_trial_w6.exe`. MD5 c0051c99695f48bf93272d96fe7548c3. SHA256 e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e. | Identical in `forge_push\bin`, `locks\lock_combo29_clang_trial_w6_20261108`, the build output `m2use\forge_m2use.exe` and the frozen copy (`evidence/FREEZE.json`) |
| Exe ↔ source link | The link rests on QA's build records, not on a rebuild: `RUN_RECEIPT.json` (source manifest 3389cfe3 → exe e1284f7f) and `build.log` line 77 ("built … sha256 e1284f7f"). Both are recorded in FREEZE but not pinned. The binary is not byte-reproducible (CURRENT_LOCK note: embedded PDB paths). | frozen copies under `out\freeze\parent` |
| Build | clang 23.1.5 (llvm-mingw-20261104), ThinLTO, frontend instrumentation PGO. Recipe `clang_build.ps1` 1fd87517…. Workload 1d52720a…. Profdata c5d97fc7…. | `RUN_RECEIPT.json`, `build.log` |
| Source parent | `D:\grok_sdk_speed_20261107\detached1735_all31\clang\all31_m29\source_snapshot`: 20 files, manifest sha256 3389cfe3…. All 20 verified at freeze. | `evidence/FREEZE.json` |
| Lineage | AL1 s198 lock tree (git 294dbed3) → trial_w6 `D:\sdk_jobs\sdk_longjob_20261106\src_w6` (8 files differ; the six speed switches are `#define … 0` in source and set by `-D` at build) → combo29 snapshot (only `include/forge/board.hpp`, `src/board.cpp`, `src/search.cpp` differ from `src_w6`). Per QA's gate0415 `PLAN.json`, feature mask 29 = KING_LINES + SEE_HOIST + MOVE_EQ32 + Clang_PGO. | `evidence/combo29_lineage_hashes.json` (blob ids file by file). The M1 reviewer, a same-model subagent and not independent, re-derived the file-difference counts. |
| Nearest committed relative | 7ce10a05 "parent P: trial_w6 source" on `opus-finny-cache-20261107` and `opus-smp-layout-20261107`. Its `.cpp` files equal `src_w6`; the four headers differ only in the six speed-switch `#define` defaults. | `evidence/combo29_lineage_hashes.json`, `evidence/combo29_lineage_header_diffs.txt` (line diff) |
| **Git source commit of combo29** | **BLOCKED.** combo29's `search.cpp` 2ffe2556, `board.cpp` c6a2cfe5 and `board.hpp` 9a94c15f are referenced by no commit: 2853 commits on 410 refs, trees only. No blob was fetched: a ref, commit and tree fetch of origin preceded the search, with lazy blob fetching disabled. Sanity rows show the method does find existing blobs (2fffbaf2, 607adf3a). The build parent is the hash-bound snapshot. | `evidence/combo29_source_commit_search.json`; INC-01 explains why `--find-object` is not used |
| QA reference caches | The frozen `qa_refcache` TSVs and `sig_4181a589` were made with the **old trial_w6** exe. They are valid for combo29 only through QA's bit-exact proof (CURRENT_LOCK note: 12000/12000 FENs on and off, bench pins identical). This job measures combo29 directly and uses them only as a cross-check. | `evidence/FREEZE.json` (pinned:false) |

## 2. Existing tuners and match runners
| Tool | Where | What it does | Tuning evidence | Disposition here |
|---|---|---|---|---|
| R9 `r9_spsa.py` + report, SVG, sim test | `opus-r9-spsa` 73eb280a `opus_r9/tuner/` | Fishtest-style SPSA counted in game pairs. Stateless `seed:k` ±1 deltas. Clamp and round plus/minus; fastchess `-repeat` pairs. Append-only `iterations.jsonl`. Resumes after the last complete record. Load governor. | stc1: 832 pairs at 8+0.08, 16 params, 0 of 16 beyond 2σ. Sanity runs on LmrQuietDivisor and LmrQuietBase. | **Base of this pack**: imported verbatim; `spsa/space.py` replays R9's saved runs bit-exactly |
| O30 `tune_spsa.py` + `.ps1` | `opus-30h-20261103` 32bb47cb | Port of R9 with CPU pinning, disk floors and a stop event. Review nit E-006 (rounded plus equal to minus). | stc8_main: 184 of 1800 pairs, 8 params; never gated | Ideas only; E-006 fixed here |
| R3 `tools/spsa` (30 tests) | `opus-r3-spsa` a5f4f696 | Offline SPSA with a UCI value check before each session and time-loss counting. | **No real session.** Dry runs only: 3 × 1 pair at 0.5+0.005 on LmrQuietBase, NullMoveMarginBase and RfpMargin. It found the QsSeeMargin plateau. | Evidence only |
| 6.x experiment loop | release 6.3.0, 4e1fbcb7 `validation/release-6.0.0/EXPERIMENTS.md` | SPRT/fixed-node experiments on tunables (items 21–35). | See section 4; copy in `evidence/release630_EXPERIMENTS_4e1fbcb7.md` | Evidence only |
| `tools/match` (`run_match.py`, `run_hourly_sprt.py`, `pgn_stats.py` pentanomial cross-check, `windows_validate.py`) | AL1 lineage, e.g. 73eb280a | Reproducible fastchess match and SPRT support for CI. | Not a tuner | Not on this branch; the confirmation runner's own LLR is deliberately separate code (IDEA_SOURCE) |
| **QA gate runner `forge_queue.ps1`** | Two copies were read: `forge_deepres_stage_20261109\forge_queue.live.ps1` (125,725 B) and `forge_push\autorestart\forge_queue.ps1` (126,811 B, newer, next to the live gate config). Which one is installed cannot be told read-only. | QA's authoritative SPRT gate driver: queue entries, book allow-list (`8moves_v3`, `uho_lichess_v1`), `order=random` + `openings_start` + `-srand`, prebench pins, advertised-option check. | Runs all gates | The confirmation protocol targets "QA's installed forge_queue.ps1, QA to confirm" (`confirm/PROPOSED_QA_ENTRY.json`); this job never touches queues |

## 3. Gate and tuning receipts (corrected)
- **Qsearch mechanism gates exist, but none tunes QsFutilityMargin or QsSeeMargin.**
  - `FORGE_RESULTS.md` gate 58: `QsQueenPromoOnly=1`, capped with no decision.
  - P27R-AL1: `QsEvasionSeeNonPv=1`, 3000 games, nElo +10.53, LLR 1.37, capped, `longer_tc_confirm_if_h1`.
  - 6.x item 13 `qschecks`: not adopted.
- **No gate or experiment ever set a `Razor*` value.** The only razoring item is the `opus-sol-S10fix` "improving_razor" mechanism, rejected at screening.
- **In-flight on combo29** (`CR_PASS_dr_*.ok`, `queue_entries_DR.json`; all `option.X` switches against E1284F7F, QA conventions 10+0.1, `uho_lichess_v1`, SPRT [0,5], cap 5000):

  | Area | Candidates |
  |---|---|
  | TT | DRX2 TtBestBonus, DRX3 TtCutChildDepth, DR05 TtPvStoreBonus, DR08 TtPvHistPlies, DR11 TtPvFailLowLmr, DR22 TtPvFailLowDepth |
  | Ordering / history | DRX1 PriorRefutePenalty, DR02 KillerNullSlot2, DR13 MainHistKeepPct, DR16 ContHistCheckShort, DR17 FullUpdateAlphaRaised, DR19 KillerHistOrder, ContHistSumBase, QuietMalusDecay |
  | Correction | DR03 CorrBadCapture, DR21 MinorCorrectionWeight |
  | Eval | DR01 EvalRule50Damp, DR15 EvalGrain |
  | **Qsearch (and what feeds it)** | **DR04 PreQsTtExtDepth, DR06 QsSeeHistDiv/Clamp, DR12 QsFailFirm/Keep** (stand-pat and post-loop fail-high firmness), **DR14 TwofoldNonPv** (rewrites the qsearch draw line), **DR01 EvalRule50Damp and DR15 EvalGrain** (rewrite the corrected-static-eval line used by search's razor `eval` and by qsearch's `futility_base`) |
  | Noisy pruning | DR07 NoisyHistPrune, NoisySeeHistDiv |
  | Extensions | DR09 TripleExtMargin, DR10 LmrPvExt |
  | Other | DR14 TwofoldNonPv, DR18 NmpFewCutoffs, DR20 RfpThreatMargin, ReSearchAdjust, Syzygy |
- **Line-level check of all 34 deepres `search.cpp` trees** in `D:\forge_deepres_20261109\tree` (read-only, this audit):
  - **No tree changes any razoring line** (the `depth <= RazorDepth && eval + RazorBase + RazorMultiplier*depth < alpha` test, the `qsearch(alpha-1, alpha)` call, the return).
  - **No tree changes the qsearch futility lines** (`futility_base = static_eval + QsFutilityMargin`, the futility skip and its best-score update), nor the stand-pat return line.
  - **Only T04E-04 (DR06) rewrites the QsSeeMargin line.**
  - Inputs and neighbours of both families do change:
    - T06-05 (DR01) and T06-04 (DR15) rewrite `eval = ss->static_eval = corrected_eval(...)`, which feeds both the razor test's `eval` and `futility_base`.
    - T04F-03 (DR14) rewrites qsearch's draw line.
    - T04C-01 (DR12) and T04D-05 (DR04) add option-gated qsearch behaviour: fail-high firmness, and a TT extension before qsearch.
  - The scan checks whether each baseline line is still present; it was re-run for these trees in the M1 recheck.

## 4. Parameter inventory (combo29 `forge::tune`, 51 scalars, all UCI options because the lock is built with `FORGE_EXPOSE_TUNABLES=1`)
Status key: **T** = values tuned by SPSA or SPRT games (merged or not), **t** = family partly tested, **U** = values never tuned, **F** = an in-flight CR candidate edits the same mechanism, **D** = dead at lock values, **X** = excluded (time manager / timing job).
| Family | Scalars (lock value) | Status | Evidence |
|---|---|---|---|
| LMR | LmrQuietBase 85, LmrQuietDivisor 220, LmrNoisyBase 10, LmrNoisyDivisor 340, LmrHistoryDivisor 6000, LmrCutoffThreshold 3 | T + F | R9, O30; 6.x items 21 (adopted), 31; ReSearchAdjust, DR11 |
| Null move | NullMoveMinDepth 3, NullMoveBase 3, NullMoveDepthDivisor 3, NullMoveEvalDivisor 200 | t + F | 6.x item 23 (MinDepth 2 rejected); R9/O30 NmpEvalBase; DR18 |
| RFP | RfpDepth 8, RfpMargin 72, RfpImproving 40 | T + F | R9, O30, 6.x item 32; DR20 |
| **Razoring** | **RazorDepth 2, RazorBase 150, RazorMultiplier 350** | **U** | none anywhere (6.x, R3, R9, O30, gates, 24 DRs); S10 was a rejected mechanism |
| Quiet futility | FutilityDepth 7, FutilityBase 100, FutilityMultiplier 110 | T | R9 |
| LMP | LmpBase 4 | **T** (6.3.0 adopted LmpBase=4 by SPRT) | 6.x items 33, 35; gate 60 LmpOffKP |
| History pruning | HistoryPruneDepth 3, HistoryPruneMultiplier 2048 | U, but its threshold scales with history magnitudes changed by DR13, QuietMalusDecay and ContHistSumBase; sibling DR07 | none |
| SEE quiet / noisy | SeeQuietMultiplier 24 / SeeNoisyMultiplier 150 | T / U+F | R9, O30 / NoisySeeHistDiv, DR07 |
| Singular | SingularDepth 7, SingularMargin 2 | t + F | 6.x item 28; R9/O30 double margin; DR09 |
| IIR | IirDepth 4 | U | none |
| ProbCut | ProbcutDepth 5, ProbcutMargin 180 | T | 6.x item 30; R9 |
| **Qsearch pruning** | **QsFutilityMargin 160, QsSeeMargin 40** | **U** (values never tuned) **+ F** (DR06 rewrites the QsSeeMargin line; DR04 and DR12 change neighbouring qsearch behaviour; the futility lines are untouched) | 6.x, R3 (advertised only), R9, O30, gates, DR line scan |
| Aspiration | AspirationDelta 18 | T | R9 |
| History bonus | HistoryBonusQuadratic 20, HistoryBonusLinear 48, HistoryBonusMax 2048 | **T** (6.3.0 adopted Max 2048 / Quadratic 20) + F | 6.x items 34, 35; QuietMalusDecay, ContHistSumBase |
| Check extension | CheckExtensionDepth 2 | U | none |
| Correction | MaterialCorrectionWeight 100 | adopted without proof (6.x item 22, LLR 0.60) + F | DR03, DR21 |
| Capture futility | CaptureFutilityBase 0, CaptureFutilityMultiplier 250, CaptureFutilityDepth 6 | t (6.x item 25, base 300 not adopted) + D (base 0 disables the branch) | `search.cpp:1335` |
| Fail-low continuation | FailLowContinuationBonus 0 | t (6.x item 26) + D | `search.cpp:1475` |
| Time manager | Tm* (10 scalars) | X | 6.x item 27; FORGE_RESULTS timepack, TmOppClock, TmScoreLoss |

## 5. Selection rule and the alternatives considered
- **Hard requirement: the values must be untuned.** Families with tuned or tested values (T, t) are "merely unmerged" or old and are excluded: LMR, null move, RFP, quiet futility, LMP, SEE, singular, ProbCut, aspiration, history bonus, capture futility, fail-low continuation.
- **Selector: direct code-level coupling between the two families.** Scalar count is not a criterion; the earlier "single scalar" labels are withdrawn.
- **Disclosed risk, not an exclusion: in-flight work on the same mechanism or its inputs.** The config's identity pin on E1284F7F enforces this mechanically. If DR01, DR04, DR06, DR12, DR14, DR15 or any other change to razoring, qsearch or the static eval becomes the lock, the pin fails and the tuning must be redone against the new parent.
- **F1 = razoring.** U; no in-flight edit of its lines. Its `eval` input is rewritten by DR01/DR15, and it consumes qsearch's result, which DR04/DR12/DR14 change. Those are indirect dependencies.
- **F2 = qsearch pruning, tuned scalar QsFutilityMargin.** U; its futility lines are untouched by every DR. `futility_base`'s static-eval input is rewritten by DR01/DR15, and neighbouring qsearch behaviour by DR04/DR12/DR14. **QsSeeMargin is frozen at 40** because DR06 rewrites its line and its effect is a plateau in steps of 100 (sensitivity table below). It is offered only as a later discrete A/B, never inside SPSA.
- **Why not the others** (every untuned alternative fails the coupling selector; in-flight work is mentioned only as a disclosed risk):
  - IIR, check extension and quiet history pruning are untuned but have no direct code-level coupling to razoring. History pruning's thresholds would also move with the history scales that in-flight candidates change (a disclosed risk, not the reason).
  - Correction's weight was adopted without proof. It is a mechanism adoption, not tuned values, but it has no coupling to razoring, and DR03/DR21 are in flight.
  - LMP is tuned (6.3.0), so it fails the hard requirement.
- **The joint SPSA vector is three continuous scalars:** RazorBase, RazorMultiplier, QsFutilityMargin. RazorDepth and QsSeeMargin stay at their lock values.

## 6. Sensitivity and interaction probes on combo29 itself (bench nodes; not games, not Elo)
Measured on the frozen lock exe at Idle on CPUs 12–15. Raw output in `evidence/sensitivity_combo29_lock_d13_d16.json`, `evidence/combo29_lock_interaction2x2_d13_d16.json` and `evidence/combo29_lock_control2x2_lmrhist_d13_d16.json`.

| Setting | d13 nodes (Δ%) | d16 nodes (Δ%) |
|---|---|---|
| defaults | 862329 (pin) | 3024920 (pin) |
| RazorBase 135 / 165 | 900054 (+4.37) / 791308 (−8.24) | 3540287 (+17.04) / 2737869 (−9.49) |
| RazorMultiplier 315 / 385 | 903506 (+4.78) / 763968 (−11.41) | 3306008 (+9.29) / 2521661 (−16.64) |
| QsFutilityMargin 144 / 176 | 793331 (−8.00) / 877190 (+1.72) | 2713052 (−10.31) / 3071864 (+1.55) |
| QsSeeMargin 0 / 99 / 100 / 199 / 200 | 862329 / 862329 / 824643 / 824643 / 1075589 | 3024920 / 3024920 / 3287728 / 3287728 / 3452465 |
| RazorDepth 1 / 3 | 772683 (−10.40) / 938799 (+8.87) | 2743991 (−9.29) / 3062325 (+1.24) |

- The d13 values for RazorBase, RazorMultiplier, QsFutilityMargin and QsSeeMargin equal R3's AL1 measurements. R3 never measured RazorDepth.
- **2×2 probes.** The interaction contrast is N(++) − N(+−) − N(−+) + N(−−), in % of the pin.
  - RazorBase × QsFutilityMargin: 13.9% (d13), 5.8% (d16).
  - RazorMultiplier × QsFutilityMargin: −9.9%, 5.4%.
  - Control pairs with an unrelated mechanism: QsFutilityMargin × LmrHistoryDivisor is at least as non-additive as the family pairs (20.5% and 21.4%); RazorBase × LmrHistoryDivisor is nearly additive (2.7% and −0.2%).
  - **Fixed-depth node counts are chaotic, so these probes cannot evidence an interaction.** The razoring–qsearch coupling claimed in PLAN.md is code-level only. Whether it matters for strength is **UNPROVEN**.
