# DUPCHECK: what is already built, closed, listed or new

Job: bit-exact speed lane on combo29 (fable2). Times are Europe/Vienna. Search run 2026-11-10 08:28 Vienna; re-run 10:15 with an item for `KING_PAWN_CACHE` (that candidate joined the pool after the profile, so the first run had no pattern for it); wider commit-message search 10:21.

**Result of the re-run that changes a status:** the mechanism of `KING_PAWN_CACHE` was built before. Commit `928f1ff7` (2026-10-13, branch `cursor/chess-engine-elo-8295` only) caches the king shelter in the pawn-cache entry in the source of that date. Under ruling 1 of the plan it is therefore **not a new candidate** of this job. Details in sections 3 and 4.

## 1. What was searched

| Source | Size | How |
|---|---|---|
| Branch-tip text corpus | 389 fetched branches (fetch 08:11), 3,788 files of type `.md .cpp .hpp .h .patch .diff`, 41.9 MB | `tools/tree_index.py`, `tools/fetch_corpus.py` |
| Commit messages | 2,669 commits on the fetched branches (2,671 at the re-run, with this job's own two) | `git log --remotes=origin`; item patterns in `tools/dupcheck_search.py`, and at 10:21 one wider pass over subjects and bodies for the words `has_legal_move`, `witness`, `pinned`, `evasion`, `check mask`, `is_legal`, `gives_check`, `checkers`, `discovered`, `pawn capture`, `capture loop`, `capture mask`, `attackers_to`, `make_move`, `shelter`, `pawn cache`, `pawn-king`, `king-pawn`, `pawn entry`: 63 commits, every subject read |
| PC folders (read-only) | 19,089 files seen, 15,236 text files up to 2 MB read | `D:\forge_qa`, `D:\forge-qa`, `D:\sdk_jobs\sdk_longjob_20261106`, `D:\grok_sdk_speed_20261107`, `D:\forge_deepres_20261109`, `D:\forge-runs`, `D:\forge_coder_checks`, five `D:\qa_*speed*` folders, and under `C:\Users\Administrator\grok-pc`: `incoming`, `forge_deepres_stage_20261109`, `crew_gates_20261107`, `coder-fuzz`, `forge_push\{qa_reports,locks,sdk_speedonly_20261107,overnight_timing_20261108}` plus the top-level files of `forge_push` |

Tool and patterns: `tools/dupcheck_search.py` (one name pattern and one mechanism pattern per item). Raw counts and example locations: `data/dupcheck_hits.tsv`.

**Not searched:** `F:\ospd`, `C:\ospd_hunt`, `D:\forge_jobs_20261107` (banned for this job); the 20 `data/` and `results/` branches; history behind branch tips other than commit messages; text files over 2 MB; folders deeper than five levels. A candidate that lives only there is invisible to this file.

The three ids in the brief are md5 prefixes of patch files on the PC, not git commits: `52597688` = `C2_MATKEY_ONCE.patch`, `8fcd0679` = `QUIET_FLAG_v1.patch`, `62acae36` = `QUIET_FLAG_v1.2.patch` (hashed by me in `D:\forge_qa\quiet_abba_e4_c2_20261109\patches\`).

## 2. Closed list of the brief (not redone)

| Item | Found at | State on record | Action |
|---|---|---|---|
| H4 `SLIDER_PDEP16` | `opus_speed/patches/h4_slider_pdep16.patch` (branch `opus-cut-nott-lmr-20261105`), 70 corpus hits | Opus hunt: bit-exact, -0.10 % vs trial_w6, NO-WIN; brief: with QA | not touched; my patches avoid `bitboard.*` |
| FT-accum / finny refresh | branch `opus-finny-cache-20261107` (`opus_finny_cache/`) | brief: at Code Review | not touched; my patches avoid `nnue.*` |
| `KING_LINES` | in the lock source (`FORGE_SPD_KING_LINES 1`), `opus_speed/W9_KING_LINES.md`, SDK B3 | in the lock | base for candidates 1-3, which change other functions |
| CorrHistPrefetch | deep-research card T05D-03, 29 corpus hits | brief: lost -1.90 % ABBA | not redone; no prefetch candidate here |
| int16 accumulators | card T05-01, SDK D4a `NNUE_INT` (neutral), branch `opus-nnue-int8-vnni-20261106` | closed | not redone |
| `MATKEY_FAST` | `opus_speed/FINAL_REPORT.md` | timing loser | not redone |
| AVX2 / AVX-512 / VNNI NNUE | `FORGE_SPD_NNUE_ZMM` in the lock; `opus_nnue_int8_vnni/` | in the lock or closed | not redone |
| Lockless TT / `nodes_` layout | branch `opus-smp-layout-20261107`; `D:\forge_qa\smp_c29_20261109` | with QA | not touched; my patches avoid `search.*` |
| C2 `MATKEY_ONCE` | `D:\forge_qa\c2_matkey_20261109` (patch md5 `52597688`) | bit-exact, waiting on the quiet ABBA | not touched |
| `QUIET_FLAG` v1 / v1.2 | `D:\forge_qa\quietflag_v12_20261109`, `incoming\quietflag_v12_20261109` | bit-exact, waiting on the quiet ABBA | not touched |
| e4gate | `D:\forge_qa\smp_c29_20261109\src_e4gate` | bit-exact, waiting on the quiet ABBA | not touched |
| SMP `NODELIMIT_D1`, `EARLYSTOP_D1` | `D:\forge_qa\smp_nodelimit_d1_20261109`, `forge_push\CR_PASS_smp_earlystop_v11.ok` | with QA | not touched |
| `PICKBEST` | card T05D-02, `opus_speed/FINAL_REPORT.md` | dropped, NO-WIN | no picker or sort change here |
| Raw-eval cache | card T05F-01 (`FORGE_EVAL_MEMO`), `forge_push\nps_abba_evalcache.ps1` | tested neutral | not redone |

## 3. Earlier speed switches that the brief does not list (treated as closed)

| Switch | Source | Result on record |
|---|---|---|
| H1 / H7 `LARGEPAGES` | Opus hunt 2026-11-05 | -0.19 % and +0.61 %, NO-WIN |
| H2 / D4d `DIRTY_INPLACE` | Opus hunt, SDK job | +0.53 % then +0.2 %, NO-WIN |
| H3 `NNUE_COLUMNS` | Opus hunt | +0.81 %, NO-WIN |
| H5 / D4b `MOVE_STORE32` | Opus hunt, SDK job | +1.21 % screening WIN on g++, then NO-WIN alone in the SDK job; not in combo29 |
| H6 `PICK_FIRST` | Opus hunt | +0.60 %, NO-WIN |
| H8 `HCE_LOCALS` | Opus hunt | -0.16 %, NO-WIN |
| H9 `PTYPE_ARITH` | Opus hunt | -0.10 %, NO-WIN |
| B4a `BADCAP_PREFIX`, B4b `PICKER_SCRATCH` | SDK job | B4a wall WIN / cpu NO-WIN; left out of combo29 by QA's all-31 ranking |
| B7a `QS_STALEMATE_LATE` | SDK job | NO-WIN; exact only up to a TT tag collision |
| B7b `LEGAL_WITNESS` | SDK job | NO-WIN (extra witness pieces tried through `is_legal`) |
| B10 `SEE_HOIST`, D4c `MOVE_EQ32` | SDK job | in the lock |
| B9e `EVASION_GEN` | SDK job, `crew_gates_20261107\inputs\B9e.patch` | not node-identical (tie order), needs a gate |
| `TT_REPLACE_CACHE` | branch `opus-tt-replace-cache-20261106` | separate job |
| `PAWN_ENTRY32`, pawn-king entry (T05B-01) | `PLAN_HUNT.md`, deep-research card `opus_deepres/cards/T05B/T05B-01-pawn-king-entry.md` (2026-11-04, proposed switch `FORGE_HCE_PKCACHE`) | listed; the card's own check found none in the lock ("Lacks it"); estimate +0.5 to +1.5 % UNPROVEN |
| Shelter cache in the pawn entry | commit `928f1ff7`, 2026-10-13, Cursor Agent, branch `cursor/chess-engine-elo-8295` only (not an ancestor of `main` or of the Opus speed branches) | **built**: shelter, storm and open-file terms cached per colour by king square, valid through the pawn-key entry; message: "Behaviour-neutral (bench signature unchanged), about 1% faster". Not in combo29 |
| Check-aware pseudo-legal generation | commit `d2b85db5`, 2026-10-12, four `cursor/*` and `opus-r8-datagen` branches | built; changed the bench signature (tie order), like B9e later |
| Legal-witness fast path | commit `82cd2c24`, 2026-10-19 (61 branches) | in the lock: this is the `has_legal_move` witness that `WITNESS_NOPIN` extends |
| Lazy MovePicker check masks, qsearch `gives_check` elision | commits `2c0c7efa`, `4e15dea0`, `3dddd864`, 2026-10-19 | `search.cpp` work; not touched here |

Sources: `opus_speed/FINAL_REPORT.md` section 9 (branch `opus-cut-nott-lmr-20261105`), `D:\sdk_jobs\sdk_longjob_20261106\{REPORT.md,PATCH_NOTES.md,QA_HANDOFF.md}`.

## 4. Pool candidates of this job

Status words: **UNLISTED** = no name or mechanism hit anywhere searched. **LISTED-UNBUILT** = the idea is written down in crew notes, and no patch, build or timing of it was found. **BUILT BEFORE** = an implementation of the mechanism exists on a fetched branch.

| Candidate | Name search | Mechanism search | Nearest prior work | Status |
|---|---|---|---|---|
| `FORGE_SPD_KING_PAWN_CACHE` | 9 corpus hits: the T05B notes, the T05B-01 card and one T06E card; 0 on the PC | 8 corpus hits (the same T05B files); **1 commit message: `928f1ff7`** | Commit `928f1ff7` (2026-10-13) is the same mechanism for the shelter loop in the source of that date; it lives on one Cursor branch and never reached the lock lineage. Card T05B-01 (2026-11-04) describes the full design this patch follows (shelter, storm, open file and king-pawn distance in a 64-byte entry). Differences of this patch: written against combo29; also caches the king-pawn distance; a record is trusted only when both stored pawn bitboards and the king square equal the position's (the October code trusts the pawn-key entry, which can differ from the lock on a 64-bit pawn-key collision). The raw-eval cache (T05F-01, tested neutral) is a different mechanism. | **BUILT BEFORE - not a new candidate** |
| `FORGE_SPD_WITNESS_NOPIN` | `HASLEGAL_FAST`: 1 corpus file, 1 PC copy of the same file | same two files | `opus_speed/PLAN_HUNT.md` queue item 2 (2026-11-05), never built in that hunt (its nine switches are H1-H9). SDK B7b tried more witness pieces through `is_legal`, a different mechanism. | LISTED-UNBUILT |
| `FORGE_SPD_EVADE_LEGAL` | "check mask" wording: 48 corpus hits, all in deep-research notes; 0 on the PC | 2 corpus files (card and table), 7 PC files that are all copies of B9e | Card T05C-01 and `notes/T05C/TABLE.md` row 1 and `BOARD_COST.md` rows 4-5 list a single-check mask inside `is_legal`. KING_LINES (W9, SDK B3) left positions in check on the full test: "positions in check keep the lock's full tests verbatim". B9e built an evasion generator, which changes the sort input and is not node-identical; it does not touch `is_legal`. | LISTED-UNBUILT |
| `FORGE_SPD_CHECKERS_KL` | "tri-state hint": 3 corpus files (the T05C notes); "incrcheck": an October JavaScript build, unrelated code | every hit is the lock's own `checkers_ = attackers_to(...)` line or a copy of it | T05C-01 row 7 proposes skipping the recompute through a caller hint. This candidate takes the answer from the board's own king lines and needs no interface change. | LISTED-UNBUILT |
| `FORGE_SPD_PAWN_CAPMASK` | none | none | none found | UNLISTED |
| `FORGE_SPD_HCE_REUSE` | 1 corpus file, 1 PC copy (`PLAN_HUNT.md` item 4) | T05B table row 5 (dropped on a static count), and `validation/pawn-span-fill-20261020/next-review/queen-rays-codegen.md` | That October note found that GCC 14.2 already reuses both queen rays, so the source duplication did not exist in the binary. | LISTED-UNBUILT; **dropped, not built** (section 5) |
| `FORGE_SPD_KL_LAZY` (reserve) | none | none | none found | UNLISTED; **not built** (section 5) |

**The new candidates of this job are four:** `PAWN_CAPMASK` (UNLISTED) and `WITNESS_NOPIN`, `EVADE_LEGAL`, `CHECKERS_KL` (LISTED-UNBUILT). Only `PAWN_CAPMASK` is new in the strict sense of "not written down anywhere searched". Their bundle is `BUNDLE4`.

**`KING_PAWN_CACHE` is carried as a labelled extra, not as a new candidate.** Ruling 1 says a candidate found built on the fetch is dropped. It was found after the patch had been written and quick-gated, because its search pattern was added late (my omission: the candidate was added to the pool after the first search and I did not re-run the search at once). The patch stays in the pack with its full identity evidence for one reason: no combo29 version of this mechanism exists anywhere else, and the October commit reports about 1 %. Whether it is timed and counted is the owner's and QA's decision, not mine. `BUNDLE` (five patches) = `BUNDLE4` + `KING_PAWN_CACHE`; both bundles get the same evidence.

## 5. Dropped during the job

| Candidate | Why | Evidence |
|---|---|---|
| `FORGE_SPD_HCE_REUSE` | No measurable target: the lines that recompute the queen's rays hold 0.12 % of the samples in the lock's control build (`PROFILE.md`), under anything a timing can show. Never built, so no identity result exists for it. | `PROFILE.md`, `out\prof\` |
| `FORGE_SPD_KL_LAZY` | Reserve only. `WITNESS_NOPIN` already removes most of the king-line builds that a lazy split would have saved, so it was not written. | plan, ruling 1 |

SEARCH/EVAL CHANGE (out of scope): none. No candidate of this job changed a node count, a best move or an evaluation in any run; a candidate that does is recorded here and dropped.
