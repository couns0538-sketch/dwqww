---
name: forge-speed-lock-path
description: One-command speed-only lock path for Forge (speed job 2026-11-05, branch opus-speed-20261105, opus_speed/tools) - build_variants.ps1 (QA kit v2.3 lines token for token, reproduces lock FD3A5190 byte for byte; O3 / LTO / PGO / LTO+PGO, flag and PGO-workload variants, pc1 = pc2, fail-closed pins), bitexact_check.ps1 (bench net on + off, perft, 12k six-field FENs at depth 13, MSVC ASan vs the MSVC build of the lock + g++ UBSan trap, -ResumeFrom), abba.ps1 (ABBA/BAAB rounds on one CPU, fresh copies, wall = protocol verdict, CPU time advisory, A/A band, WIN rule), speed_pack.ps1 (source tree in, pack + verified candidate file out, -ReuseBuildDirs / -PriorBitexact), make_stack.sh, pack_table.py, the day's results (stack +11 %), the CPU / disk rules and the PowerShell 5.1 pitfalls. Use for any node-identical speed change, build-flag or PGO-workload question, an nps comparison, a stack of speed switches, or a lock-candidate pack for QA.
---

# Forge speed-only lock path (speed job, 2026-11-05)

A change that searches exactly the same nodes and only runs faster needs no Elo gate, but **BIT-EXACT + an ABBA nps
win is NOT a lock**: every bitexact_check level runs on a cold table at Threads 1. The lock path is (1) bitexact_check
BIT-EXACT (L1-L4, full 12k L3), (2) **L3b warm-table identity** vs the lock (`warm_identity.py`: no ucinewgame, Hash /
Clear Hash / UseNNUE changes), (3) a **Threads 2-4 go-movetime smoke** (`patchrev_qa.py soak`: no crash, every bestmove
legal, Threads 1 tail = the lock's reference; soak only), (4) the ABBA WIN (wall), then (5) QA's own re-time. A stack
handed to QA also carries the patch review's QA tests (`patchrev_qa.py replay / protocol / extreme`,
`tests/test_stack_poison.ps1`, `tests/test_stack_mutants.ps1`). bitexact_check prints a `LOCK PROOF INCOMPLETE` line
after every BIT-EXACT verdict to say so. These tools turn a source tree into a lock-candidate exe and its proof pack.
Rules first:
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
| `bitexact_check.ps1 -Cand <exe> -Out <dir> [-Quick] [-SanSrc <tree>] [-ResumeFrom <dir>] [-SkipSan]` | L1 bench d11-22 net on + off, L2 perft, L3 `data\fens_12k_v2.txt` at go depth 13 (OwnBook false, ucinewgame each, 2 engines on CPUs 0/1, reference cached per lock sha256 in `F:\ospd\ref` under a named mutex; -Quick = first 2,000), L4 MSVC ASan (port copy, compared with the MSVC ASan build of the lock source) + g++ UBSan trap (compared with the candidate's own d16); stops at the first FAIL; exit 0 / 3 / 1; **not a lock by itself** (cold table, Threads 1): after BIT-EXACT it prints `LOCK PROOF INCOMPLETE: ...` (a line that does not start with VERDICT, so speed_pack / pack_table keep parsing the verdict alone) |
| `abba.ps1 -A <lock> -B <cand> -Out <dir> [-Depth 20 -Rounds 10 -AaCsv ..] [-Order ABBA]` | ABBA/BAAB alternating rounds, fresh process + fresh byte copies per round, engine's bench nps (PROTOCOL verdict) and the process CPU time of the bench window (advisory); summary_<run id>.txt + runs.csv + history log |
| `abba_queue.ps1 -List <name TAB exe> -AaCsv ..` | back-to-back ABBA vs the lock; identical exes are not timed; results.tsv |
| `speed_pack.ps1 -SrcDir <tree> -Name <n> [-Define SW=1,..] [-Quick] [-ReuseBuildDirs a,b] [-PriorBitexact dir]` | flips switch defaults in a kit source copy (`src_kit`), pc1 = pc2, bit-exact proof, ABBA vs lock, `F:\ospd\packs\<n>` + `opus_speed/candidates/<n>.md` (patch verified against the source, branch head, bench signature) |
| `make_stack.sh <name> <p1.patch> ..` | patches on a fresh lock copy, no fuzz, switch defaults checked, stacked patch written (never overwritten) |
| `pack_table.py`, `abba_table.py` | markdown tables from pack folders / ABBA folders (sorted by the wall median) |
| `abba_recheck.py <dir>.. / --pool <dir> <dir>..` | recomputes summaries from runs.csv with the exact t quantile (independent of abba.ps1's series); `--pool` joins a borderline run and its re-time so the decision uses all rounds, never the re-time alone |
| `warm_identity.py <lock> <cand> <fens> <out> --n 1000 --nodes 20000` | **L3b, required for a lock**: warm-table identity: `go nodes` over N FENs without ucinewgame, Hash / Clear Hash / UseNNUE changes every 25 FENs, `bench 1` + `go perft 1` first, `bench 13` last; transcripts compared without nps / time |
| `patchrev_qa.py replay\|protocol\|soak\|extreme --out <new dir> [--mask 0xC] [--stacks a,b]` | the patch review's QA tests, lock vs each stack through the identical script (venv python with python-chess; sets and re-reads its own mask + Idle, fails closed; never kills, reports survivors): **replay** = one gate game ply by ply at go depth 10 without ucinewgame, 2nd pass on the aged table with option changes, transcripts = lock; **protocol** = go infinite / ponder -> stop / ponderhit, go mate 3, 20 x movetime 100, legal bestmove + ponder move; **soak** (`--mask 0xF`, = the lock path's Threads 2-4 smoke) = 60 x movetime 300 at Threads 2/3/4 with Hash changes, Threads 1 tail = the lock's cached L3 rows, bench 13; **extreme** = `data/extreme_fens.tsv` at go depth 8 + perft 3 on kit, UBSan and MSVC ASan exes, rejected FENs keep the position |
| `make_poison.py <src_kit> <dst>`, `tests/test_stack_poison.ps1`, `tests/test_stack_mutants.ps1` | poison copy (the authors' 0xA5 fills of every array that lost its zero fill) -> o3 build -> bitexact -Quick must stay BIT-EXACT; mutant (pick_best `>=`) of each stack's own LF source + defines -> speed_pack must exit 3 before any ABBA. Verify builds only |
| `commit_push.sh <msg>` | gated commit + push (code-name lint, control bytes, PS 5.1 parse) |
| `pgn_positions.py`, `name_lint.py`, `ctrl_char_check.py`, `ps_parse_check.ps1` | game positions with provenance, vendor-name lint, control bytes, PS 5.1 parse |

## Proven facts (2026-11-05)
- `build_variants lp_v1` on the exact lock source = lock exe FD3A5190 byte for byte (sha256 fd3a5190..., 1.5 min).
- The lock's net is embedded and ON by default (`UseNNUE` default true): QA's frozen v1 workload (bench 11/13/16) already
  profiles the net path; net off = `setoption name UseNNUE value false`.
- MSYS2 g++ 15.2 defaults here: stack protector off, `-fcf-protection=full` listed but the PE exe has 0 endbr64,
  `-mprefer-vector-width=none` for znver5 (the lock exe uses zmm).
- A/A on CPU 2 at d16 with fresh copies (CPUs 2-3 busy with other programs, 53-74 %): sd per round 3.8 %, 95 %
  interval [0.983, 1.038] -> d16 cannot resolve +1 %; decisions use d20. Balanced ABBA/BAAB A/A at d20: wall 1.0066
  [0.9968, 1.0111] sd 0.99 %, cpu 1.0050 [0.9940, 1.0087] (aa_lock_d20_s3). Per-run noise varies with the load
  (sd 1-5.6 %/round): re-time borderline results with 16 rounds instead of believing one run.
- The lock's 12k reference is deterministic (a byte copy reproduces 12,000 / 12,000) and has 12,000 distinct rows.
- Results vs the lock (d20, wall = protocol): no build flag / mode beats LTO+PGO v1; PGO trained with the net OFF
  -29 %; NO_ZERO_MOVELISTS=2 +3.6 %, SPEED2 +3.2 % (10 rounds); TT_NOTLS +2.9 %, SLIDER_PEXT +1.5 % (pooled 26
  rounds; TT's first noisy run said +4.2 %); stack NZM2 + SPEED2 +7.3 %, + TT_NOTLS +11.5 % wall / +11.3 % cpu,
  bit-exact incl. the full 12k; switch-0 builds = FD3A5190 byte for byte; QA's own kit (with `-Kit`) rebuilds the
  stack exes byte for byte.
- QA kit v2.3 under Windows PowerShell 5.1: always pass `-Kit <kit folder>` (its `$PSScriptRoot` default is empty
  there; the preflight hash checks are then skipped and the run fails only at training).
- SPEED2 and NO_ZERO_MOVELISTS both rewrite MovePicker::generate_quiets: stack them with `r14_speed2_after_nzm.patch`
  (hand-merged), not the plain SPEED2 patch.

## Pitfalls hit while building these tools
- PS 5.1 + `$ErrorActionPreference = 'Stop'`: a native tool's stderr line (`lto-wrapper: warning: using serial
  compilation`) redirected with `2>&1` becomes a terminating error. Wrap native calls in `'Continue'` (QA's kit does).
- `[ordered]@{ 11 = ... }[11]` reads by POSITION (OrderedDictionary int indexer), not by key: use string keys.
- `powershell -File x.ps1 -List a,b` delivers ONE string "a,b": split list parameters on commas yourself.
- A function that calls Write-Output and also returns a value: `$null = f` swallows the printed lines too.
- Number formatting follows the PC's culture (decimal comma): set InvariantCulture before writing CSV / summaries.
- `go` is aborted by the next UCI line: drive searches and wait for `bestmove`; bench and `go perft` are synchronous.
- OwnBook defaults to true in the lock: identity runs on FEN sets set OwnBook=false, or book hits skip the search.
- The lock REJECTS placement-only FENs (`info string invalid FEN: FEN must contain six fields`) and keeps searching
  its previous position: `opus_r10/parity/fens_12k.txt` is placement-only, so an L3 on it compared ONE position 2,000
  times (withdrawn). Use `fens_12k_v2.txt` (md5 e7dbf2c8) or `ConvertTo-OspdFen`, fail on any `invalid` info string,
  and refuse a degenerate result set (< n/10 distinct rows).
- Inside a PowerShell function, anything written to the output stream (Write-Output in a log helper) becomes part of
  the return value: `Build-One` returned [log lines..., object] and `-Twice` never saw two builds. Log helpers inside
  functions write with `[Console]::Out.WriteLine`.
- `Start-Process -RedirectStandardInput <file>` opens the file exclusively: two builds training from QA's one
  workload file at the same moment collide. Copy the workload into each build folder first (sha256-checked).
- Bash heredocs collapse `\\`: a Windows path `F:\\ospd\\abba` written from a heredoc into a file became
  `F:\ospd<BEL>bba`. Write files with the Write / Edit tools; `tools/ctrl_char_check.py` finds such bytes.
- A fresh session process after an application restart runs at 0xFFFF / Normal: pin it to 0x3 Idle first.
- MSVC never defines `__BMI2__`, so a source that guards PEXT code with `#if !defined(__BMI2__) #error` cannot build
  for the ASan run: bitexact_check adds `/D__BMI2__=1` for such sources only (the lock source never mentions it).
- Re-timing a borderline result until it says WIN is optional stopping: every borderline single gets ONE 16-round
  re-time and the decision uses the pooled rounds (`abba_recheck.py --pool first second`); report both runs.
- In this Bash tool `"F:\\ospd\\packs\\$p\\x.exe"` loses the variable (`packs$p`): write paths with forward slashes.
  The same collapse turns `\b` inside a Python heredoc into a backspace byte: write such scripts with the Write tool
  (commit_push's control-byte gate caught two of them).
- The engine prints bench results as `info string bench depth D nodes N ...` in a UCI session: match `bench depth`
  anywhere in the line. An interactive driver must read through a thread + queue with a timeout; a bare readline
  waiting for a line that never comes blocks for good (and the no-kill rule then leaves the processes running).
- ABBA on this PC: plain A B B A showed slot-position effects of ~1-2 % in A/A runs; alternate ABBA / BAAB (default)
  and read the process CPU time of the bench window as a second metric (preemption by other programs is not counted).
  Noise depends on the moment's load: per-round sd 1 % (quiet) to 5.6 % (builds on the other core).
