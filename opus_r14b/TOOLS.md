# R14-B capability map (checked 2026-11-02 12:20 PC clock; no invented commands)

| kind | name | use in R14-B |
|---|---|---|
| project skills (`.claude/skills/`) | forge-pc-rules (binding), forge-job-workflow | every command, push and report |
| project skills | forge-nnue-pytorch-amd, forge-nnue-pipeline, forge-nnue-data, forge-nnue-train-cpu | item 1: npt trainer, R6 loader builds, dl_equal method, data facts, CPU training recipe; item 2: data formats, sidecar, relabel tools |
| project skills | forge-selfplay-datagen | item 2: self-play text format and game order |
| plugin skills | superpowers: verification-before-completion, systematic-debugging, test-driven-development, receiving-code-review, writing-skills | evidence before claims, equality-mismatch triage, self-tests first, review findings, skill files |
| sub-agents | at most one reviewer at a time (R14-B brief), read-only, never on files being edited | review milestones; otherwise structured self-review recorded as NOT independent |
| CLI | gh (repo couns0538-sketch/dwqww): run list / view | CI ASan+UBSan results of the item branches |
| MCP | Context7 (PyTorch / ctypes docs), Exa / Parallel / Firecrawl search (licences, public papers; GPL / AGPL = ideas only) | only when a design question needs it |
| MCP not used | Hugging Face, Linear, Notion, Supabase, Vercel, Postman, Claude Docs, Artifacts, Atlassian / Datadog / Slack / Sentry, Unblocked (failed to connect) | no outside posts; reports live in the repo |
| local | Git Bash, PowerShell 7, MSYS2 ucrt64 g++ 15.2 (`/c/msys64/ucrt64/bin`, the same toolchain as the npt "setup" loader DLL) | item 1 DLL and test builds |
| local | trainer Python `F:\nnue_pytorch\venv\Scripts\python.exe` (torch ROCm build; used CPU-only, `HIP_VISIBLE_DEVICES=-1`, no HIP next to the npt line) | item 1 equality, bench, CPU loss match |
| local | venv `C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B` (numpy, torch cpu, python-chess as test oracle) | item 2 tools and tests |
| local | `opus_r14b/tools/pc_gate.ps1` (R13, read-only load / RAM / disk gate) | before every heavy step |
| local | R13 probe `forge_data_probe` (lock source d4f4312) and Astra's converter / filter copies | item 2 labels |

## Used so far (updated 16:20)
| tool | used for | result |
|---|---|---|
| gh (GitHub CLI) | CI runs of `ffl-sanitize` (ASan+UBSan, TSan) on opus-r14b-fast-loader | runs 41441092765, 41446915233 PASS |
| Context7 MCP (`/websites/pytorch/2.11`) | PyTorch reproducibility notes: only `torch.manual_seed()` controls the generator; no fixed default seed is promised | cited in item 1's seeding finding |
| Parallel Search MCP | GCC docs on `-fprofile-dir` / `-fprofile-generate`: .gcda names follow the output file when sources are compiled and linked directly | fixed a silent non-PGO trap in `build_probe_opt.sh` before running it |
| advisor (stronger reviewer, sees the transcript) | plan check at 14:40 | frozen-code rule for the proof, D:/F: path fixes in two documents, 2-worker estimate marked |
| one read-only reviewer sub-agent (13:00-13:45, before Couns ruled them out) | item 1 review R14B-I1-1 | 1 hang + 1 overflow + fail-open spots fixed |
| plugin skills | superpowers:verification-before-completion (before each "done"), systematic-debugging (when a check fails) | - |
| project skills | forge-pc-rules, forge-nnue-pytorch-amd, forge-nnue-data, forge-ltopgo-pgo, forge-job-workflow; new forge-npt-fast-loader | updated at the end with R14-B lessons |
| advisor, second call (16:00) | check of the post-proof plan | finish with the frozen code before promotion; function-level diff to tie the 1M proof to the shipped code; separate contended / uncontended rates; thread-budget note; memory refresh |
| Monitor / background waits | kill #2 aftermath, end of the proof runs, test runs | one notification per event instead of polling |
| Forge tools, read-only | `F:\opus_scratch\rescore_d8\bin\fen2bin.exe` (self-play text -> FPOS), adapter `train_resid_nnuepytorch_v2.py` (read to find `--npt-repo` / `--npt-extra`), crew `disk_guard.log` | relabel output carries the new labels into .pos (1200/1200); item 1 adoption path; the D: dip was the self-play dedup DB, not a leak |
| own tools added | `opus_r14b/tools/cpu_users.ps1` (who uses CPUs 2-3), `opus_r14b/item2/fn_diff.py` (function-level diff), `label_stats.py` | load next to every rate; proof coverage of the post-proof code; descriptive label statistics |
| Windows API via Python ctypes (GetLogicalProcessorInformation) | CPU topology | CPUs 2-3 are one physical core (SMT siblings): every rate re-read per core, skill + memory updated |
| more own tools (18:00-18:50) | `item1/tools/fl_acceptance.sh` (one-command CPU acceptance check), `item2/label_stats.py`, `measure_rates.sh`, `bridge_check.sh`, `build_probe_opt.sh` + `probe_bench.py` | 261/261 acceptance; measured cost table; PGO probe proven same labels |
| new skill | forge-relabel-job (commands, input rules, checks, measured costs, pitfalls); updates to forge-pc-rules, forge-ltopgo-pgo, forge-npt-fast-loader, forge-nnue-data, forge-nnue-pytorch-amd, forge-job-workflow | mirrored into `.claude/skills/` |

## Recommended for Forge engine work (asked by Couns at 19:40; what exists here today, what to connect, what to install)
| kind | name | state on this PC (2026-11-02) | what it would do for the engine work |
|---|---|---|---|
| CLI | GitHub CLI `gh` | connected | CI results (the loader's ASan / UBSan / TSan runs), PRs |
| MCP | Context7 | connected | library docs (PyTorch, ctypes, CMake, GCC) - gave the torch seeding fact behind the `--seed` finding |
| MCP | Parallel Search, Exa, Firecrawl (incl. its arXiv / paper tools) | connected | docs, forums, papers on NNUE / search; found the GCC .gcda naming rule that protected the probe PGO build |
| MCP | Hugging Face | connected | paper search; optionally private, versioned storage of nets and datasets |
| model | advisor | available | second opinion at checkpoints (today: stale claims, code-freeze plan) |
| MCP | Unblocked | FAILED: "account isn't part of any team yet" | join / create a team: context search over this repo's 2,000+ commits and many branches |
| MCP (engineering plugin) | Linear / Notion / Slack / Atlassian / Datadog | need sign-in | job and owner-item tracking, GPU-window requests, alerts on long runs - only if outside messages are allowed (the R14-B rules forbid them) |
| MCP | Postman, Supabase, Vercel, Sentry | connected / sign-in | not useful for the engine (web / backend tooling) |
| skills | superpowers: verification-before-completion, systematic-debugging, test-driven-development, receiving-code-review, writing-skills | installed | evidence before claims, failure triage, tests first, review handling, skill files |
| skills | engineering: code-review, testing-strategy, tech-debt, documentation | installed | structured reviews and test plans |
| skills | dataviz | installed | SPRT / Elo / NPS charts |
| skills | project forge-* (22, incl. forge-relabel-job and forge-npt-fast-loader from today) | in `.claude/skills/` | the PC rules and every proven recipe |
| app | AMD uProf | not installed | Zen 5 profiling (hot spots, cache / branch misses) for NPS work and PGO decisions |
| app | ROCm profiler (rocprof) / Radeon GPU Profiler | not checked | GPU use of the npt trainer (item 1's open question) |
| app | Windows Performance Toolkit (WPR / WPA) | not installed | CPU scheduling view (would have shown today's Idle starvation directly) |
| app | sccache or ccache | not installed | faster engine / probe rebuilds |
| CI | a GitHub Actions Windows runner | not used | MinGW builds + CTest on Windows (CI is Linux-only today) |
| app | OpenBench, Ordo | not installed | Fishtest-style distributed SPRT, Elo from PGNs, if more than fastchess is wanted |
Check every licence before installing (R14-B rule: no network installs of GPL tools; many chess tools are GPL).

## Own tools for Couns and Opus (Couns 19:46: "create tools scripts that you and i can use"; `opus_r14b/tools/`)
Skill `forge-opus-tools` has the full usage. All read-only towards other processes; outputs only in new folders.

| tool | one command | why |
|---|---|---|
| opus.sh | `bash opus_r14b/tools/opus.sh help` | one entry point: status, lint, abba, engine, time, load, test |
| opus_status.sh | `bash opus_r14b/tools/opus_status.sh [--ci]` | worktrees (head, ahead / behind, dirty, CI), own processes with priority / affinity, who uses CPUs 2-3, RAM / disks vs floors, npt keeper head - in ~10 s |
| abba.py | `python -I -B abba.py --out NEW --a "CMD" --b "CMD" --pairs 10 [--metric RX --higher-better] [--identity RX --identity-ab]` | palindromic A/B of any two commands (loader, probe, prepare, builds); stops when outputs differ; t-CI on log ratios; load next to the number |
| doc_lint.py | `python -I -B doc_lint.py opus_r14b skills` | control bytes, CRLF, mojibake, eaten Windows backslashes, broken GitHub tables, dead relative links |
| hash_sweep.py | `python -I -B hash_sweep.py --docs ... --files ... --repo ... --allow hash_sweep_allow.txt` | every cited hash still matches a real file or commit |
| engine_fresh_check.sh | `bash engine_fresh_check.sh REF NEW_DIR [--quick]` | clean export of an engine ref, lock-recipe build pinned low, exe sha256 + FMA count, bench / perft pins via the lock package's uci_check.py |
| gpu_util_stats.py | `python -I -B gpu_util_stats.py [--hours 6 \| --from T --to T] [--by-hour]` | GPU utilisation of the live trainer from the keeper's HWiNFO log (read-only); baseline 2026-11-02: mean 45.7 %, >= 90 % in 4 % of samples |
| commit_span.py | `python -I -B commit_span.py --repo REPO --since "..." origin/<branch>...` | time per branch and pauses from commit times (for reports; no guessed hours) |
| cpu_users.ps1, pc_gate.ps1, lowrun.ps1 | see the skill | load sample, load / RAM / disk gate, run one program pinned at low priority |
| engine_bisect.sh | `bash engine_bisect.sh GOOD BAD NEW_DIR [--depth 13]` | first commit that changed bench nodes (fresh export + lock-recipe build per candidate; skips failed builds; any predicate with --test) |
| test_tools.sh | `bash test_tools.sh NEW_DIR` | 25 checks of abba.py, doc_lint.py, opus.sh and the bisect search (exit codes and output lines) |

### Review R14B-T-1 (20:00-20:05 PC clock; structured self-review, NOT independent; no sub-agents)
Reviewed: abba.py, doc_lint.py, engine_fresh_check.sh, commit_span.py, opus_status.sh at opus-r14b-status 6fc27230.
Findings and fixes (000182d7): abba.py crashed with a traceback on a non-hex `--mask`, a mask beyond the PC's 16 CPUs
(after creating the output folder) and a metric group that is not a number - now clean exit-2 messages, the driver
pins itself before it creates anything; doc_lint.py skipped GitHub tables written with one dash per delimiter cell,
reported URL-encoded relative links (`a%20b.md`) as dead, and scanned bytes in a Python loop - fixed (C-speed scan);
opus_status.sh labelled the load sample "CPUs 2-3" although it lists processes ALLOWED there - label made exact.
Documented, not changed: wall times include the shell start (use --metric for short commands); `--shell cmd`
cannot take inner double quotes. Checks after the fixes: test_tools.sh 14/14 PASS (3 new), doc_lint over all branch
folders and skills 0 findings. Next: engine_fresh_check.sh build path on the lock and an engine branch once CPUs 2-3
are free.

### Launcher fix (20:24-20:27): `lowrun.ps1` reported success for a program that never started
Found while converting the full 1M relabel output: Start-Process errors (missing program) ended with exit 0, and a
redirect into a missing folder ran the program with an invalid handle. Now exit 127 with a message (missing program,
missing stdout / stderr folder, missing stdin file); the program's exit code otherwise. Same file (sha256
cc7f28dd...) on all three branches; engine_fresh_check.sh and engine_bisect.sh rely on it for the build exit code.

### Engine tools on real builds (20:43-20:47; the advisor's open point: they had only been tested on arguments)
- `engine_fresh_check.sh d4f4312`: 20 files, build 13 s (BelowNormal, CPUs 2-3), exe sha256 bf0a09f9..., FMA 0,
  bench d11 / 13 / 16 / 20 / 22 and both perft pins OK -> **ALL OK** (check 30 s).
- `engine_fresh_check.sh origin/opus-r12-pgo-net` (56cf4844, 22 files incl. the HalfKA unit): build 16 s, FMA 0,
  **ALL OK** (options off = the lock's tree).
- `engine_bisect.sh d4f4312 origin/opus-r12-pgo-net --depth 11`: both ends 312,866 nodes -> "nothing to find" (exit 1,
  34 s).
- Planted change in a scratch clone (`C:\o14b\bis_mut_repo`, local commits only, never pushed): A comment, B
  `RfpMargin 72 -> 73`, C comment -> `engine_bisect.sh` found **B** (312,866 -> 294,685 nodes at d11; 4 builds, 65 s).
- Estimates in the tool headers corrected from "2-4 min per build" (a guess) to the measured ~15 s.

### Bug hunt #4, tools part (21:04-21:11; self-review, NOT independent)
- H4-T1: `engine_bisect.sh` walked BAD's first-parent line but only checked that GOOD is an ancestor: a GOOD on a merged
  side branch would leave the line's commits before the merge untested and could name the wrong commit. Now exit 2
  unless GOOD is on that line. Tests: a merge fixture, GOOD on the side branch -> exit 2, GOOD on the line -> searched
  (test_tools.sh 23 / 23 PASS, twice).
- `refreeze.sh` (never run before) on the frozen relabel2.py: 0 failures in 5.5 min - suites 150 / 0 in the worktree
  and a fresh clone, bridge PASS, labelling functions identical, sha256 88454db6... unchanged.
- `opus_status.sh --ci` (never run before): the CI line works (the loader branch's last sanitizer run; "no runs" for
  branches with only [skip ci] commits).

### Tools block result (Couns 19:46: "focus 2h on that"; 19:47-21:17 by the commit times, then back to the deliverables)
Built and tested: opus.sh (entry point), opus_status.sh, abba.py, doc_lint.py, engine_fresh_check.sh, engine_bisect.sh,
commit_span.py, gpu_util_stats.py, test_tools.sh (25 checks, ALL PASS), and in `opus_r14b/checks/` verify_chain.sh,
fresh_checkout_checks.sh, refreeze.sh, hash_sweep_r14b.sh; lowrun.ps1 fixed. Validated on real data, not only on
fixtures: engine builds of the lock and an R12 branch (ALL OK), a real bisect and a planted-change bisect, the verify
chain and refreeze on the frozen relabel code, a 6-hour GPU baseline from the keeper's log.
What they caught on this night (each fixed): a broken GitHub table in item 2 RESULTS and the same mistake in this file
(doc_lint), two paths whose backslashes were eaten by sed (doc_lint), a launcher that reported success for a program
that never started (found while converting the 1M output), a lock export that never worked from its own folder and a
robocopy call broken by Git Bash path conversion (the verify chain's fresh-clone step).
Not built: a gate-status reader - the gate folders carry known traps (stale names, mixed opponents / concurrency, see
forge-gate-stats) and a quick reader could report wrong numbers.
