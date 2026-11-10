# DUPCHECK: what was already tried and is out of scope

Job fable4cpu, written 2026-11-10 16:15 Vienna, before any candidate code. **This is not a complete duplication check.** This job may not fetch other branches, so git history beyond the one cloned commit is not available; everything below marked UNVERIFIED rests on local copies of reports or on my job-2/job-3 notes, not on the commits themselves.

## 1. What I could and could not inspect

| Source | State | How |
|---|---|---|
| Local report copies of the Opus speed hunt | inspected | `C:\Users\Administrator\grok-pc\forge_push\qa_md_1208PT\STATUS_opus_speed.md` and the copy under `forge_push\qa_reports\job4_preserve_0948\` (tables of switches H1-H9 with results) |
| SDK long job | inspected | `D:\sdk_jobs\sdk_longjob_20261106\{REPORT.md,PATCH_NOTES.md,patches\}` |
| My job 2 (`fable_speed_lane`) and job 3 (`fable_movegen_proof`) | inspected | `D:\forge_jobs_20261109\fable2\repo\` (read only), including job 2's `DUPCHECK.md`, which searched 389 fetched branch tips and 2,669 commit messages on 2026-11-10 08:11 |
| QA folders | searched by pattern | `D:\forge_qa`, `D:\sdk_jobs`, `C:\Users\Administrator\grok-pc\forge_push` (`*.md`, `*.patch`, `*.diff`, `*.txt`), patterns for the NNUE switches, weight-column prefetch, update/output fusion, Finny |
| Lock source at `16833ecc` | inspected | `forge-combo29/` in this clone |
| Git history of any branch, including `opus-speed-20261105` up to `c845d886`, the Finny branches and `ba2fcf2e` | **not available** | download rule; no fetch was made |
| `F:\ospd`, `C:\ospd_hunt`, `C:\forge_nnue_train` | not opened | protected |

## 2. The sources named in the brief

| Named source | Commit or path | What I know | State |
|---|---|---|---|
| Opus speed branch up to `c845d886` (`opus-speed-20261105`) | local report copies above; the commit itself is not local | Nine switches, all bit-exact: H1/H7 `LARGEPAGES` (table in 2 MB pages; mode 2 adds the weight table and worker tables; -0.19 % and +0.61 %, NO-WIN), H2 `DIRTY_INPLACE` (+0.53 %, NO-WIN), H3 `NNUE_COLUMNS` (+0.81 %, NO-WIN), H4 `SLIDER_PDEP16` (-0.10 %, NO-WIN), H5 `MOVE_STORE32` (+1.21 %, screening WIN), H6 `PICK_FIRST` (+0.60 %, NO-WIN), H8 `HCE_LOCALS` (-0.16 %, NO-WIN), H9 `PTYPE_ARITH` (-0.10 %, NO-WIN) | reports inspected; anything committed between those report copies and `c845d886` is **UNVERIFIED** |
| Finny / `opus_smp_finny` | job 2 recorded the branches `opus-finny-cache-20261107` (`opus_finny_cache/`) and `opus-smp-layout-20261107`; no local copy found by name under the searched folders | refresh cache and SMP layout work, at Code Review per the earlier brief | **UNVERIFIED** (not inspected in this job). Not touched: this net has no king buckets, a refresh ran 24 times in 4.2 million nodes, and no candidate here changes refresh or thread layout |
| BUNDLE3 (source `ba2fcf2e`: `EVADE_LEGAL`, `PAWN_CAPMASK` v2, `CHECKERS_KL` v3) | `D:\forge_jobs_20261109\fable2\repo\fable_movegen_proof\` (my job 3); the commit id is not resolvable here without git history | three move-legality patches in `src/board.cpp` | inspected as files; out of scope: no candidate here touches `board.cpp` |
| My job-2 speed lane | `D:\forge_jobs_20261109\fable2\repo\fable_speed_lane\` | `WITNESS_NOPIN`, `EVADE_LEGAL`, `PAWN_CAPMASK`, `CHECKERS_KL`, `KING_PAWN_CACHE`, bundles | inspected; out of scope |
| My job-3 candidates | `...\fable_movegen_proof\` | EVL, PCM v2, CKL v3, WNP, KPC v2, BUN | inspected; out of scope |

## 3. Closed work on the two paths this job looks at

| Item | Where recorded | Result |
|---|---|---|
| AVX-512 output layer `FORGE_SPD_NNUE_ZMM` | in the lock (`nnue.cpp`) | in the lock |
| Fused accumulator update loops (one pass for quiet moves and for captures) | in the lock (`nnue.cpp` lines 110-155); skill note "Exact-order accumulator loop fusion", `validation/nnue-update-fusion-20261019/` | in the lock |
| Lazy accumulator update | in the lock (`search.cpp` `static_evaluate`); earlier switch `FORGE_NNUE_LAZY_ACC` (S12) | in the lock |
| Integer accumulator, `int16` weights read in place (`NNUE_INT`, D4a `373cfb69`) | `D:\sdk_jobs\sdk_longjob_20261106\REPORT.md` | exact, timed neutral; closed |
| `NNUE_COLUMNS` (H3) | Opus report | +0.81 %, NO-WIN |
| `DIRTY_INPLACE` (H2, D4d) | Opus report, SDK job | NO-WIN twice |
| Large pages for table and weights (H1, H7) | Opus report | NO-WIN |
| Early table prefetch `FORGE_SPD_PREFETCH_EARLY`, child prefetch (S13) | in the lock | in the lock |
| `CorrHistPrefetch` | job 2 notes | lost -1.90 % in the ABBA |
| Lockless table, node-counter layout | job 2 notes (`opus-smp-layout-20261107`, `D:\forge_qa\smp_c29_20261109`) | with QA |
| Raw-eval cache | job 2 notes (card T05F-01) | tested neutral |

## 4. Candidates of this job

"Not found" means: no name or mechanism hit in the sources of section 1 marked inspected or searched. It does not cover the unavailable history.

| Candidate | Name search | Mechanism search | Nearest prior work | Status |
|---|---|---|---|---|
| `FORGE_SPD_NNUE_WPREFETCH`: when a move is recorded, prefetch the weight columns its accumulator update will read | not found | pattern "prefetch" near "nnue / w1 / weight / column / accumulator / feature": only table prefetches and unrelated lines | H7 put the weight table in large pages (NO-WIN); table prefetches are in the lock | not found locally; **UNVERIFIED** against unavailable history |
| `FORGE_SPD_NNUE_FUSE_EVAL`: compute the output layer in the same pass as the last accumulator update | not found | "fusion" hits are the update-loop fusion that is already in the lock | update-loop fusion (in the lock) | not found locally; **UNVERIFIED** against unavailable history |
| Explicit AVX-512 code for the update loops | - | - | - | **dropped before any code**: the lock's machine code for both update loops is already 16 straight-line 512-bit subtract/add/store groups per side with no overlap checks (`PROFILE.md`, section "Machine code") |
| A table-access change | - | - | large pages, early prefetch, alignment, lockless: all tried or in the lock | **no candidate opened**: clusters are 64 bytes and 64-byte aligned (`search.hpp` line 95), the prefetch is issued before `make_move`, and the remaining cost is the memory latency of one cluster load |

This file is re-checked whenever a candidate is added.
