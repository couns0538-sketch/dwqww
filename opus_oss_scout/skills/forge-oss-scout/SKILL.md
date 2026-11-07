---
name: forge-oss-scout
description: Scout and sandbox-trial open-source tools, libraries and data for Forge on grok-pc (job of 2026-11-06, branch opus-oss-scout-20261106, tools in opus_oss_scout/tools) - licence-checked catalog rows (gh api, licence_at.py, crates.io licence API for Rust dependencies, Hugging Face MCP), the PC gate script with AMD GPU counters (no nvidia-smi), a book-resolution trial (two books, fixed-node odds, pentanomial nElo + SPRT pairs), a node-identical clang build of the lock (llvm-mingw + MSYS2 libstdc++, ThinLTO + IR PGO), Windows profiling without installs (WPR + samply import + own symbolizing table), a Syzygy oracle harness (Fathom vs Forge's own reader), and a Lichess-puzzle fixed-node screen. Use for any "find / test an open-source tool for Forge" job, a new compiler or profiler trial, a book comparison, a tablebase-reader check, or a puzzle screen.
---

# Forge OSS scout (2026-11-06)

All tools live in `opus_oss_scout/tools/` on branch `opus-oss-scout-20261106`; the master copies are in
`C:\opus_5h\oss_scout\tools\`. Run Python with `-I -B`, and from Git Bash for anything that pipes UCI.

## PC facts learned (re-check them; they change)
- The GPU is an **AMD RX 7900 XT**, so there is no `nvidia-smi`. Read GPU use with
  `Get-Counter '\GPU Engine(*engtype_Compute*)\Utilization Percentage'` (per pid) and
  `'\GPU Adapter Memory(*)\Dedicated Usage'`. `tools/scout_gate.ps1` does disk / RAM / CPU 0-3 / GPU / gate counts in
  one call and appends JSON to `logs/scout_gate.jsonl`.
- The live npt trainer runs Idle with mask 0xF (CPUs 0-3) and its pid changes between runs. Own work: narrow the
  session process to 0xC (`(Get-Process -Id <session pid>).ProcessorAffinity = [IntPtr]0xC`) and keep at most 2 heavy
  threads.
- E: is a 3 GB volume; any "every drive >= N GB" rule can only mean C:, D: and F:.
- The live npt runs write ~1.4 GB checkpoints to `C:\forge_nnue_train\runs`, so C: can fall ~0.5 GB/min. Watch it.

## Catalog rows
- Metadata in one loop: `gh api repos/<owner>/<repo> --jq '[.full_name,(.license.spdx_id//"none"),.pushed_at[0:10],(.archived|tostring)]|@tsv'`.
- NOASSERTION or none: `python -I -B tools/licence_at.py OWNER/REPO` reads the LICENSE file at the commit.
- Rust tools: read `Cargo.toml` dependencies and check each crate at
  `https://crates.io/api/v1/crates/<name>` (generic User-Agent). Example: bullet links GPL-3.0 `sfbinpack` and AGPL-3.0
  `montyformat`.
- Data: Hugging Face MCP `hub_repo_search` / `hub_repo_details` (licence tag, size, parquet files).
- Re-check every row at the end: `python -I -B tools/check_catalog.py CATALOG.md --min-rows 30`.

## Book resolution (tools/t1_run.sh, tools/t1_analyze.py)
- Run: `T1_NODES_A=20000 T1_NODES_B=10000 bash tools/t1_run.sh uho|8moves <rounds> <tag>`. This is the same lock exe at
  two node limits, OwnBook=false, `-repeat`, conc 2. Fixed nodes make the result independent of the CPU load.
- Analyse: `t1_analyze.py --engine n20k A=pgn,stdout B=pgn,stdout`. It prints the pentanomial (checked against
  fastchess), nElo with a 95 % interval, the ratio between the books, and Wald pairs for SPRT [0,10] normalized.
- Lesson: at 2:1 node odds UHO resolved 13 % WORSE than 8moves. Large-gap proxies do not answer gate questions;
  measure near zero.

## Node-identical clang build of the lock (tools/t2_build.ps1)
- The installed LLVM 18 does not work with the VS 18 STL (STL1000: needs clang >= 20).
- Use llvm-mingw (portable zip). With its own libc++ the nodes differ, because the MovePicker's `std::sort` breaks ties
  in a library-specific order.
- `-LibStdCxx` adds `--sysroot=C:/msys64/ucrt64 -stdlib=libstdc++ -rtlib=libgcc -unwindlib=libgcc`, which gives the
  lock's nodes.
- Variants: `m0` (-O3), `m1` (ThinLTO), `m2gen` -> run the kit workload v1 on stdin with
  `LLVM_PROFILE_FILE=...%p.profraw` -> `llvm-profdata merge` -> `m2use -Profdata`. Then forge-uci `pin_check`
  (full = d11-d22).
- Timing: `tools/abba/abba.py` (R14-B) with `--metric 'nps (\d+)' --higher-better --identity 'bench depth 20 nodes (\d+)' --identity-ab --mask 0x4 --priority BelowNormal`,
  plus an A/A run first.

## Windows profiling without installs (T3)
- `samply record` needs xperf (Windows ADK), which is not allowed here. Instead:
  - `wpr -start CPU -filemode`, run the program, `MSYS_NO_PATHCONV=1 wpr -stop 'C:\...\trace.etl'`.
  - `samply import --save-only -o profile.json.gz trace.etl --symbol-dir <pdb dir>`.
  - `python -I -B tools/t3_samply_top.py profile.json.gz --process <exe name> --exe <exe> [--pdb <pdb>] --symbolizer <llvm-mingw>/bin/llvm-symbolizer.exe`
    (VA = 0x140000000 + RVA; pass absolute paths).
- WPR is system-wide: the same trace also profiles the gate engines (real games). Keep traces short, and disclose
  them.

## Syzygy oracle (T5)
- `t5_gen_fens.py` (stdlib random legal 3-5 piece positions) -> Forge `tb_probe` (R13 P6 tree, `t5_build_forge_probe.sh`)
  + Fathom `t5_fathom_batch` -> `t5_compare.py` (WDL exact, DTZ exact or +-1 when rounded).
- Timing: `t5_forge_wdl_timing.cpp` vs the Fathom batch's own passes.
- Tables: `D:\grok-pc-data\dwqww\.claude\worktrees\syzygy345`, read-only.

## Puzzle screen (T6)
- `t6_fetch_puzzles.py` takes a seeded sample through the public dataset-viewer API (CC0 Lichess puzzles).
- `t6_solve.py <exe> puzzles.jsonl --nodes N`: `position fen F moves m0`, `go nodes N`, bestmove == m1. Reports rating
  bands and mate themes.

## Pitfalls
- Bash heredocs turned `\\f` / `\\r` in Python strings into form feed / CR. Write such files with the Write tool,
  then grep for control bytes.
- `git archive` applies core.autocrlf: use `git -c core.autocrlf=false archive ...` for LF sources.
- Python `subprocess` on Windows needs an absolute exe path (a relative `dl/...` path gave WinError 2).
- Foreground `sleep` is blocked: wait with a background `until` loop, or with the task notification.
