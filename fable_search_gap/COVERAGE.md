# COVERAGE: what this dossier is built on

Job: one missing search mechanism for the Forge chess engine at the combo29 lock (ideas only, no engine change).
Branch `fable52-search-gap-20261109`, base `origin/main` `5176ddf79ae15b76c08c4485d90ee5600ba30a1a`.
Snapshot frozen 2026-11-09 20:10 to 20:35 PT on grok-pc. All times in this folder are PT (America/Los_Angeles).
Terms are explained in `NO_QUALIFIED_GAP.md` section 9.

## Key points

- **The lock exe reproduces every pin on my lane.** Bench depth 11/13/16/20/22 with the net on and off, and perft 5 on the start position and kiwipete, all match (run on CPU 3-6 at Idle, record in `data/pins_combo29.json`).
- **No repo commit contains the combo29 search source.** I used the Engine QA lock pack on the PC as the source of record and name it below.
- **The folder named in the lock pointer is not the combo29 source.** `CURRENT_LOCK.json` still points its `tree` field at the older AL1 s198 tree. Its `search.cpp` has a different hash.
- **I found no game PGNs for the gates.** The mirrored gate folders hold logs and result files only, and the gate summary script itself reports "log missing: 86" of 136 finished gates. PGNs may exist in a place I did not look. Game-level claims are therefore limited to what the logs and result tables show.
- **The earlier deep-research job is the main dedupe source.** Branch `opus-deepres-20261104` holds 81 ranked idea families and a line-by-line feature diff of the lock search. It is listed in full below.

## 1. Lock identity (hashed before use)

| Item | Path | Hash | Status |
|---|---|---|---|
| Lock exe (combo29) | `C:\Users\Administrator\grok-pc\forge_push\bin\forge_clang_combo29_trial_w6.exe` | sha256 `E1284F7FC492C8FE1285797FDAE8988CF2F2926B33FCFEE7023D284D67D8802E`, 2,092,544 bytes | matches the pin; identical copy in `locks\lock_combo29_clang_trial_w6_20261108\` |
| Reference exe (trial_w6) | `...\forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe` | sha256 `4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0` | matches the pin |
| Lock pointer | `...\forge_push\locks\CURRENT_LOCK.json` (2026-11-08 00:35) | sha256 `50af2ef34087d684...` | read only; names combo29 as speed lock on top of trial_w6 |
| Probe copies | `D:\forge_jobs_20261109\fable52\out\exe\combo29_E1284F7F.exe`, `trial_w6_4181A589.exe` | same sha256 as above | my probes run these copies, never the originals |

Pin run on the combo29 copy, 2026-11-09 20:13 PT, `tools/pin.ps1` + `tools/uci_probe.py pins`, affinity mask 0x78, Idle:

| Check | Observed | Pin | Result |
|---|---|---|---|
| bench net on d11/13/16/20/22 | 312866 / 862329 / 3024920 / 12389307 / 34048354 | same | match |
| bench net off d11/13/16/20/22 | 375354 / 907205 / 2448617 / 13573040 / 24506465 | same | match |
| perft 5 start position | 4865609 | 4865609 | match |
| perft 5 kiwipete | 193690690 | 193690690 | match |

Speed on this lane was 2.1 to 2.5 million nodes per second. That number is context only, not a timing result.

## 2. Source of record

**Used:** `D:\forge-qa\pack_combo29_20261108\pc_payload\source_snapshot` (20 files).

- It matches its manifest `...\pc_payload\build\SOURCE_INPUTS.sha256` 20 of 20 (sha256 of the manifest `3389cfe3dc7bb398...`).
- `src/search.cpp`: md5 `b9f9aab051b548ebd50389c9ca9d5352`, 82,121 bytes, 1,818 lines, git blob `2ffe2556113c`. Matches the pin.
- `include/forge/search.hpp`: md5 `aab81dd8213b678c0bd7fb6656337a57`, 18,568 bytes. Matches the pin prefix `aab81dd8`.
- Engine QA's build receipt `...\pc_payload\build\RUN_RECEIPT.json` (sha256 `bc8ead3d260039e9...`) records that this source manifest produced exe sha256 `e1284f7f...8802e`. That is QA's record. I did not rebuild the lock and do not claim any tree builds it.
- The same two files also sit in `C:\Users\Administrator\grok-pc\forge_push\sdk_speedonly_20261107\native_builds\q17\source_snapshot`.
- All 20 files with md5, sha256, git blob id and repo match are in `data/lock_source_hashes.tsv`.

**Repo commit that matches: none.** I indexed every file path on 387 fetched branches (`tools/tree_index.py`) and looked up each lock file by git blob id. Six files have no blob anywhere in the fetched branches: `src/search.cpp`, `src/board.cpp`, `include/forge/search.hpp`, `include/forge/board.hpp`, `include/forge/bitboard.hpp`, `include/forge/nnue.hpp`. The other 14 do.

**Nearest repo state (recorded by others, not rebuilt by me):**

- Commit `d4f43124dde1d1e37de90e18930e374f32ea7ffa` holds the AL1 s198 source. Its `src/search.cpp` blob `74de5d37a461` equals the file in `locks\AUTOLOCK_1_gate120_e32f003rec_s198\source` (md5 `d05507b967bf4eea82642c0c9c893fd5`, 69,466 bytes).
- `opus_speed/patches/trial_w6.patch` on `origin/opus-speed-20261105` (`1ad0d295`, blob `43a485690206`) is recorded as the step from that commit to trial_w6 (`opus_smp_layout` INVENTORY, corpus file `md/2244c2ec...`).
- The step from trial_w6 to combo29 is the "clang_four" patch set in the QA pack (`...\pc_payload\patches\clang_four_vs_frozen.patch`) plus a compiler change.

**Why the search behaviour is the same across these exes.** The bench pins of AL1 s198 (`locks\AUTOLOCK_1...\BENCH_REF.txt`), trial_w6 and combo29 are the same five numbers, and I observed them on combo29. The extra 12.6 KB in the combo29 `search.cpp` are five speed switches (`FORGE_SPD_TT_NOTLS`, `FORGE_SPD_NO_ZERO_MOVELISTS`, `FORGE_SEARCH_SPEED2`, `FORGE_SPD_PREFETCH_EARLY`, `FORGE_SDK_BADCAP_PREFIX`). I did not diff the two files line by line; identical node counts at five depths, on and off the net, are the evidence.

## 3. What I read in the lock source

| File | Read | Purpose |
|---|---|---|
| `src/search.cpp` | all 1,818 lines | tunables 22-72; TT 204-418; move picker 423-768; eval and correction 811-868; draw test 904-914; history updates 938-984; `qsearch` 989-1110; `search` 1115-1499; root loop 1504-1741; thread start 1772-1816 |
| `include/forge/search.hpp` | all | TT entry and probe handle, tunable list, history table shapes, search stack, worker state |
| `include/forge/board.hpp` | all | move, undo, repetition, SEE, `key_after`, key history |
| `include/forge/eval.hpp`, `include/forge/nnue.hpp` | all | eval interface; the net is a residual on top of the hand-crafted evaluation |
| `src/uci.cpp` | all | bench set, perft, option handling; tunables are accepted as unlisted options |
| `src/board.cpp` | only the locations of `is_repetition` (1189, 1200), `key_after` (971), `has_legal_move` (696) | not read in full |
| `src/eval.cpp`, `src/nnue.cpp`, `src/bitboard.cpp`, `src/book.cpp`, `src/eval_params.cpp` | not read | outside the search question |

## 4. Repo evidence

- Remote `https://github.com/couns0538-sketch/dwqww`, public, about 7.7 GiB. Cloned blob-less (trees and commits only), then 3,754 unique text files fetched by blob id.
- **Fetched:** 387 branches. Tips are in `data/branch_tips.tsv`.
- **Not fetched:** 20 branches under `data/` and `results/` (training data and CI result dumps). Anything only on those branches is UNVERIFIED.
- **Index:** 56,163 unique (blob, path) pairs. Index sha256 `3d5c10b8ade0e742...` (local file `out\index\tree_index.tsv`, regenerate with `tools/tree_index.py`).
- **Corpus:** every `.md`, `.cpp`, `.hpp`, `.h`, `.patch`, `.diff` on the fetched branches, 3,754 files, 41.6 MB, one file per blob (local `out\corpus`, manifest sha256 `6a8ff8c3cce79072...`, regenerate with `tools/fetch_corpus.py`). Dedupe searches ran over this corpus. **It holds branch tips and these six file types only.** Work that was deleted or reverted before a branch tip is not in it, and neither is anything recorded only in `.txt`, `.json`, `.csv`, `.py`, `.ps1` or log files. For the one unowned mechanism the commit messages of the fetched branches were searched as well, after the review: 2,658 commits, no match (`data/commit_message_search.md`).

Documents read in full or searched line by line:

| Document | Branch | What it gives |
|---|---|---|
| `opus_deepres/notes/RANKING_FINAL.md` | `opus-deepres-20261104` | 81 ranked idea families: 44 search (one of them is about the gate method), 11 net, 17 speed, 9 enablers |
| `opus_deepres/notes/T04F/DIFF.md` | same | 101-row feature diff, lock search versus an MIT engine, with a verdict per row |
| `opus_deepres/notes/TRIED_GATES.md` | same | 110 gate rows as of 2026-11-04 |
| `opus_deepres/cards/T04*` (48 search cards), other `notes/T04*/TABLE.md` | same | searched by keyword, not all read in full |
| `opus_r15/cands/INDEX.md` | `opus-r15-20261103` | six built candidates plus three extra lines |
| `opus_oss_scout/CATALOG.md` | `opus-oss-scout-20261106` | tools and data only, no search mechanisms |
| `opus_smp_layout` INVENTORY (corpus `md/2244c2ec...`) | `opus-smp-layout-20261107` | lock parent chain, what is not in trial_w6 |
| `skills/forge-candidate-checks/SKILL.md`, `plugins/forge-cpp-lab/skills/*` | `qa-syzygy-gaps-fixes-20261109`, `astra-crew-skills-20261101` | crew conventions for checks, research, safe runs and gate requests |

## 5. PC evidence (all read-only)

| Evidence | Path | Notes |
|---|---|---|
| Gate verdict table | `C:\Users\Administrator\grok-pc\forge_push\FORGE_RESULTS.md` (sha256 `70ede35dfa67e961...`) and `.csv` (`17c8bde8fbb40680...`), both 2026-11-09 16:55 | 126 rows. The table changed at 21:44 PT (127 rows, `.csv` sha256 `511cb6de4088c34c...`); the new row is reported in `EVIDENCE.md` section 2 and not counted |
| Live gate manifest | `...\forge_push\autorestart\forge_gates.json` (1.5 MB, changing) | 373 entries; read, never written |
| Gate folders | `D:\grok-pc-data\forge_push\gate*` | 71 folders, last written 2026-11-01; logs, `RESULT.md`, `RUN_INFO.json`, `TIMEWATCH.txt`; **no PGN in any of them** |
| Gate status log | `...\forge_push\autonomy\gate_results.log` | newest line: 136 finished gates, 13 H1, 6 H0 or early stop, 31 capped, **log missing 86** |
| Review receipts | `...\forge_push\CR_PASS_*` | 226 files |
| Lock folders | `...\forge_push\locks\` | AL1, ltopgo, trial_w6, combo29 |
| QA lock pack | `D:\forge-qa\pack_combo29_20261108`, `D:\forge-qa\lockproof_combo29_20261108` | source snapshot, patches, build receipt, soak logs |
| Today's candidates | `C:\Users\Administrator\grok-pc\{rsa,qmd,chsb,nshd,t12b,syzg}`, `D:\forge-runs\{tcc21,chsb,rsa,qmd,nshd,t12b}_20261109` | diffed against the lock source for dedupe |
| Gate entries prepared during this job | `C:\Users\Administrator\grok-pc\forge_deepres_stage_20261109\queue_entries_DR.json` (written 20:22 PT, read 22:21 PT) | 25 entries from the crew's deep-research cards; read for dedupe only, not touched |
| QA pull made during this job | `C:\Users\Administrator\grok-pc\qa_pull_20261109_1309PT` (created 20:11 PT) | pull of the shared-table layout job; searched for the unowned mechanism, no match |

Today's live candidates, by what their diff does (not by name):

- `rsa`: re-search depth adjustment after a reduced search fails high.
- `qmd`: quiet-move penalty that shrinks with the try index.
- `chsb`: continuation-history update that uses the sum of the plies as its base.
- `nshd`: capture history shifts the SEE pruning threshold of captures.
- `tcc21`: before a TT cutoff, look up the TT entry of the hash move's child; a contradicting child entry vetoes the cutoff. Adds a `peek` to the table and uses `key_after`.
- `t12b`: two lock bug fixes (bad-capture buffer, position parsing).
- `syzg`: Syzygy probing gaps.

## 6. Tools and connectors used

- `forge-uci` server: `pc_status` only. Its bench, perft, pin and option tools run engines on CPU 0-1, which this job may not use, so I ran my own pinned equivalents.
- `forge-o30` server: not used (nets and SPSA status were not needed).
- Linear and Notion: one read-only search each for "Forge" on 2026-11-09. Both returned nothing. No idea board exists there for this account.
- Web search (Parallel Search) for primary sources. Queries carried no project or personal details.
- GitHub through `git` and `gh` for the repo itself.

## 7. AGENTS.md

`AGENTS.md` is missing on `main` and on the six recent branches I checked. Recovered with the content of commit `3e9009413eadac5dbeae3170a131117c04aa9e11`: 4,018 bytes, md5 `94169aefef79ccb69c21f8f2c86298f0`, which equals the historical md5. Its header is scoped to another job (Astra R8). I followed its general section "Development review and verification": one read-only reviewer, findings assessed one by one, record saved in `REVIEW_LOG.md`.

## 8. Evidence I could not find (UNVERIFIED)

1. **Game PGNs of the gates.** None in the 71 mirrored gate folders. The crew's throughput notes mention gates timed from PGNs, so PGNs may exist in a place I did not look. Without them, draw types, blunder patterns, per-move scores and the split of clock time between middlegame and endgame cannot be studied.
2. **Logs of 86 finished gates**, including every gate recorded after 2026-11-01. The newest NOT CLEAN gates (time losses 5, 12 and 22) could not be opened, so I cannot say which side lost on time.
3. **A repo commit for the combo29 source.** None exists on the fetched branches.
4. **The 20 `data/` and `results/` branches.** Not fetched.
5. **`D:\forge_jobs_20261107`, `F:\ospd`, `C:\ospd_hunt`.** Banned for this job. Any candidate or note that lives only there is invisible to this dossier.
6. **Other folders on `F:`** that the deep-research notes cite (for example `F:\odr\work`). Not read; the notes themselves are in the repo and were read there.
7. **Idea boards outside the repo.** Linear and Notion were empty. Any board kept elsewhere is unknown to me.
8. **Trigger counts inside the lock search.** They need an instrumented build, which this job does not make.
