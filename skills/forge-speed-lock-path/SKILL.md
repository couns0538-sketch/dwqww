---
name: forge-speed-lock-path
description: One-command speed-only lock path for Forge (speed job 2026-11-05, branch opus-speed-20261105, opus_speed/tools) - build_variants.ps1 (QA kit v2.3 lines token for token, reproduces lock FD3A5190 byte for byte; O3 / LTO / PGO / LTO+PGO, flag and PGO-workload variants, pc1 = pc2), bitexact_check.ps1 (bench net on + off, perft, 12k FENs at depth 13, clang ASan+UBSan), abba.ps1 (A B B A rounds on one CPU, fresh copies, median + t-interval + A/A band, WIN rule), abba_queue.ps1, speed_pack.ps1 (source tree in, pack + candidate file out), the CPU / disk rules and the PowerShell 5.1 pitfalls. Use for any node-identical speed change, build-flag or PGO-workload question, an nps comparison, or a lock-candidate pack for QA.
---

# Forge speed-only lock path (speed job, 2026-11-05)

A change that searches exactly the same nodes and only runs faster locks on a bench-signature match + an ABBA nps win,
no Elo gate. These tools turn a source tree into a lock-candidate exe and its proof pack. Rules first:
[[forge-pc-rules]] plus the job rules below. Kit facts: [[forge-ltopgo-pgo]]. Older speed work: [[forge-speed-stack]].

## Job rules these tools enforce
- CPUs 0-3 only: builds and checks pin themselves to 0x3 (CPUs 0-1) at Idle; timing pins itself to ONE CPU (default 2)
  at BelowNormal; CPU 3 (CPU 2's SMT sibling) gets no own work. Every script sets affinity + class on itself first
  (children inherit them from their first instruction), re-reads both and fails closed.
- Disk: scratch only under `F:\ospd` (<= 8 GB), F: >= 50 GB and C: >= 30 GB after the planned write, nothing on D:.
- Named mutex `Local\ospd_abba_timing`: one timing run at a time.

## Tools (opus_speed/tools, PowerShell 5.1, dot-sourced `uci_lib.ps1`, no nested `powershell -Command`)
| tool | what |
|---|---|
| `build_variants.ps1 -SrcDir <tree> -Tag <t> -Variant a,b [-Define N=V] [-Twice]` | fresh copy per build under `F:\ospd\builds\<t>_<v>[_pc1/_pc2]`; variants o3, lto, pgo, lp_v1 (= lock recipe), lp_z4, lp_noplt, lp_nosi, lp_af64, lp_ppt, lp_ipapta, lp_part1, lp_pvw256/512, lp_wnonet, lp_w12k, lp_wmix, custom (-Extra -Workload); checks gcda count, 0 missing-profile, vfmadd 0, LTO IR, quick pins |
| `bitexact_check.ps1 -Cand <exe> -Out <dir> [-Quick] [-SanSrc <tree> -Define ..]` | L1 bench d11-22 net on + off, L2 perft, L3 12k FENs go depth 13 (OwnBook false, ucinewgame each, 2 engines on CPUs 0/1, ref cached by sha256 in `F:\ospd\ref`), L4 clang ASan+UBSan bench 16; stops at the first FAIL |
| `abba.ps1 -A <lock> -B <cand> -Out <dir> [-Depth 20 -Rounds 10 -AaCsv ..]` | A B B A per round, fresh process per run, fresh byte copies per round, engine's own bench nps; runs.csv + summary.txt (5 lines) |
| `abba_queue.ps1 -List <name TAB exe> -AaCsv ..` | back-to-back ABBA vs the lock; identical exes are not timed; results.tsv |
| `speed_pack.ps1 -SrcDir <tree> -Name <n> [-Define N=1]` | flips switch defaults in a kit source copy, pc1 = pc2 build, full bit-exact proof, ABBA vs lock, `F:\ospd\packs\<n>` + `opus_speed/candidates/<n>.md` |
| `pgn_positions.py`, `name_lint.py` | full-FEN game positions for workloads; vendor-name lint for code files |

## Proven facts (2026-11-05)
- `build_variants lp_v1` on the exact lock source = lock exe FD3A5190 byte for byte (sha256 fd3a5190..., 1.5 min).
- The lock's net is embedded and ON by default (`UseNNUE` default true): QA's frozen v1 workload (bench 11/13/16) already
  profiles the net path; net off = `setoption name UseNNUE value false`.
- MSYS2 g++ 15.2 defaults here: stack protector off, `-fcf-protection=full` listed but the PE exe has 0 endbr64,
  `-mprefer-vector-width=none` for znver5 (the lock exe uses zmm).
- A/A on CPU 2 at d16 with fresh copies (CPUs 2-3 busy with other programs, 53-74 %): sd per round 3.8 %, 95 %
  interval [0.983, 1.038] -> d16 cannot resolve +1 %; decisions use d20 (see the job's FINAL_REPORT for its A/A).

## Pitfalls hit while building these tools
- PS 5.1 + `$ErrorActionPreference = 'Stop'`: a native tool's stderr line (`lto-wrapper: warning: using serial
  compilation`) redirected with `2>&1` becomes a terminating error. Wrap native calls in `'Continue'` (QA's kit does).
- `[ordered]@{ 11 = ... }[11]` reads by POSITION (OrderedDictionary int indexer), not by key: use string keys.
- `powershell -File x.ps1 -List a,b` delivers ONE string "a,b": split list parameters on commas yourself.
- A function that calls Write-Output and also returns a value: `$null = f` swallows the printed lines too.
- Number formatting follows the PC's culture (decimal comma): set InvariantCulture before writing CSV / summaries.
- `go` is aborted by the next UCI line: drive searches and wait for `bestmove`; bench and `go perft` are synchronous.
- OwnBook defaults to true in the lock: identity runs on FEN sets set OwnBook=false, or book hits skip the search.
