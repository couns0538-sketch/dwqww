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
| test_tools.sh | `bash test_tools.sh NEW_DIR` | 26 checks of abba.py, doc_lint.py, opus.sh and the bisect search (exit codes and output lines) |

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
commit_span.py, gpu_util_stats.py, test_tools.sh (26 checks, ALL PASS), and in `opus_r14b/checks/` verify_chain.sh,
fresh_checkout_checks.sh, refreeze.sh, hash_sweep_r14b.sh; lowrun.ps1 fixed. Validated on real data, not only on
fixtures: engine builds of the lock and an R12 branch (ALL OK), a real bisect and a planted-change bisect, the verify
chain and refreeze on the frozen relabel code, a 6-hour GPU baseline from the keeper's log.
What they caught on this night (each fixed): a broken GitHub table in item 2 RESULTS and the same mistake in this file
(doc_lint), two paths whose backslashes were eaten by sed (doc_lint), a launcher that reported success for a program
that never started (found while converting the 1M output), a lock export that never worked from its own folder and a
robocopy call broken by Git Bash path conversion (the verify chain's fresh-clone step).
Not built: a gate-status reader - the gate folders carry known traps (stale names, mixed opponents / concurrency, see
forge-gate-stats) and a quick reader could report wrong numbers.

### Bug hunt #5 (21:31-21:48 by the PC clock; self-review, NOT independent; item 1 findings H5-6 / H5-7 in item 1 RESULTS)
| # | finding | fix | check |
|---|---|---|---|
| H5-1 | gpu_util_stats.py: `--from` after `--to` only said "0 rows" | clear error, exit 2 | edge cases run |
| H5-2 | gpu_util_stats.py: an empty window did not say what the file covers | the header line prints the file's first and last row times | edge cases; test expects the span |
| H5-3 | my own claim "the trainer's CPU side is starved" (item 1 RESULTS, report, status, memory) went further than the data: Windows counters at 21:32 showed the trainer's CPUs 86-90 % busy with 10-14 % idle left | wording corrected everywhere to "competes for its CPUs, not purely starved"; the GPU window decides | per-CPU counters, 5 x 2 s |
| H5-4 | doc_lint did not see text right after a table, which GitHub renders as one more table row: 11 such places in the R14-B documents (incl. the new 50M runbook) | new rule (a blank line or a block start must follow a table); the 11 places fixed | test_tools.sh 26 / 26; all documents 0 findings |
| H5-5 | opus_status.sh's "own work" list did not know the tools written tonight, so it hid the overnight watcher | pattern extended (watcher, fuzz, engine tools, sweep, scratch exes under C:\o14b) | the watcher shows up |

Read and kept (no finding): fl_distribution.py (bins, chi-square dof, SE over batch means), label_stats.py (result
spellings, White's-view sign), fl_dataset_equal.py (every tensor hashed by dtype / shape / bytes, batch count
required), fl_fuzz.py's verdict logic, the 50M runbook's commands (re-read; prepare already run as written).
Exercised for the first time on real work: `abba.py` on the two relabel probes (R13 vs LTO+PGO, 500 reference positions
at 20k nodes, 6 pairs on CPU 2, the md5 of all 500 scores required equal: db2a2ce6... for both) -> **1.057x, 95% CI
1.044-1.069**, matching the dedicated probe ABBA of 17:53 (1.075x, CI 1.044-1.106); its `--warmup` and `--cwd`; `commit_span.py --until`.
Memory note and the skills forge-pc-rules / forge-npt-fast-loader brought up to date (they said 03:05 and 14 checks); hash sweep 0 unmatched.

### Check scripts added 22:35-22:59 (`opus_r14b/checks/`; self-reviewed, NOT independent)
- `make_index_r14b.sh` moved into the repo (was only in Opus's scratch): FILES.txt + SHA256SUMS of both item folders.
- `fresh_checkout_checks.sh [OUT_DIR]`: the output folder is an argument now (it was fixed to C:\o14b\fresh).
- `hash_sweep_r14b.sh`: hashes the live trainer's config.py / train.py too (read only), because item 1 H6-4 cites
  them; 0 unmatched again (22:49).
- `e2e_r8v5.sh OUT [ROWS]`: the frozen relabel2.py end to end on R8 v5 through fen2bin and hce_dump, 11 checks
  (22:53: 11 / 11, output = the first freeze's).
- `final_checks.sh OUT`: every end-of-job check in one command (~1 min), 8 steps; dry run 22:56: 8 / 8 PASS. Its
  first version printed the sub-scripts' last lines (one looked like its own end line): now PASS / FAIL counts.
- Two shell lines lost their trailing `\` when I added them with `sed 'a\'` through the Bash tool (make_index): found
  by reading the result, fixed with the Edit tool; `bash -n` cannot catch it (the broken line is still valid shell).
- Desk check (23:12, no finding): the speed statistics behind the reported ratios - abba.py and item 1's fl_abba.py
  use the two-sided 95 % Student-t quantiles for 1-30 degrees of freedom (every value equals the table, e.g. 2.262
  at 9); abba.py's Cornish-Fisher expansion above 30 gives 2.0394 at 31 (exact 2.0395); both pair the A and B run of
  the same slot (AB / BA alternating) and abba.py takes the interval on log ratios (geometric mean).
- Count sweep (23:17, the advisor's suggestion): every test / case / run count in the current-state documents
  (STATUS, FINAL_REPORT, both handoffs, GPU_REQUEST, checks README, the three skills, the memory note) grepped
  against the last measured values (suite 157, installer 25, scope 20, job_damage 35 kinds / 105 runs, test_tools
  26): one stale line (FINAL_REPORT's before / after table said 155), fixed. RESULTS files keep dated history.
- Skills' commands run as written (23:18, the advisor's suggestion; placeholders filled, nothing else changed):
  forge-relabel-job's Commands block (prepare --jobs 2 / run with the R13 probe, 2 workers, --until / assemble /
  status) on 1,500 rows of selfplay_001: every step exit 0 (23:17:43-23:17:52), then its verify_job.py line, also
  with --convert on a job whose val.txt is empty (15 games, none drawn for validation): fen2bin / hce_dump write
  header-only files, records 0 - PASS. forge-npt-fast-loader has no command blocks; its three commands ran tonight
  as written (test_scope.py in final_checks from a clone; the installer with --loader-dll and fl_acceptance.sh in
  the 22:35 fresh-clone rehearsal). forge-opus-tools: status, lint, test, time and gpu ran tonight; engine / bisect
  last ran 20:43-20:47 (builds, kept off CPUs 2-3 now).
- doc_lint at work (23:21): my own hunt #10 record got a form-feed byte from a heredoc through the Bash tool (`\f` in a Windows path); doc_lint reported `[control] bytes ['0xc']` before the commit, fixed with chr(92).

### Bug hunt #13 (01:08-01:10 by the PC clock; self-review, NOT independent): wrong or missing arguments
Scope (written 00:26, before the hunt): every `opus.sh` command called with missing or wrong arguments must end with
a nonzero exit and a clear message, no Python traceback and no work started; plus the launcher with spaces in a path.
16 calls: no arguments (help, exit 0), an unknown command (2), abba / engine / bisect without arguments (2, usage),
engine and bisect with unknown refs (2, "unknown ref", no output folder made), time with a missing option value (2)
and an unknown branch (2, git's message), gpu with a bad number or date (2), test without a folder (1, usage), lint
of a missing path (2), load with a bad seconds value (1, PowerShell's parameter message) - all fine. Two findings:
- H13-1: `opus.sh load xyz` (cpu_users.ps1 with a mask that is not hexadecimal) printed a .NET exception and an
  empty process list and exited **0** - a caller would have recorded "nobody uses these CPUs". Fixed: a mask that
  is not hexadecimal, a mask of 0 and `-Seconds` below 1 are exit 2 with one line on stderr.
- H13-2: `opus.sh status --bogus` ran a normal status: opus_status.sh took any first argument other than `--ci` as
  the worktree glob, so a misspelt `--ci` was silently ignored (the same pattern as the installer's H6-1, harmless
  here because status only reads). Fixed: an unknown option is exit 2 with the usage line.
Launcher (lowrun.ps1, used by every R14-B tool): a copy of findstr.exe as `find str.exe` in a folder with spaces,
an argument that is a quoted path with spaces, -Out / -Err files with spaces: exit 0 and the right line found; a
missing exe there: exit 127 with "cannot start ...". No finding.
Valid calls unchanged (`load 0xC 1`, `status --ci o14b-st*`). test_tools.sh: two new cases (opus-load-bad-mask,
opus-status-unknown-option) -> **28 / 28 PASS** (01:09); the count is updated in opus.sh's help, the skill, STATUS,
FINAL_REPORT and memory.

### Bug hunt #15 (02:25-02:34 by the PC clock, started early; self-review, NOT independent): files overwritten, checks that pass on failure
Scope (written 02:24, from H14-1): every place in the R14-B code on the three branches that writes a file must not
truncate or replace an existing file it was not made for; item 2's remaining scripts with missing or wrong arguments
must refuse before any probe work. Added during the hunt: check scripts whose exit code ignores a failed comparison
(the class of H14-2). Swept: every `-Out` / `-Err` caller of lowrun.ps1, every Python `open()` / copy / rename, every
shell redirection into a user-given path, on all three branches.
| # | finding | fix |
|---|---|---|
| H15-1 | **lowrun.ps1 with a bad `-Mask` (`xyz`), `0x0` or a mask beyond the PC's CPUs printed a .NET exception and then RAN THE PROGRAM ON EVERY CPU, exit 0** (shown with cmd.exe: "ran", exit 0). A caller passing a user-given mask (e.g. `probe_bench.py run --mask`) would have run the probe outside CPUs 2-3 | a mask that is not hexadecimal or names no CPU: exit 127 before anything starts; setting the priority / affinity is checked too (exit 127) |
| H15-2 | lowrun.ps1 emptied an existing `-Out` / `-Err` file before the program ran (the root of H14-1: a file holding "KEEP THIS LINE" held the program's output afterwards) | an existing redirect target is refused, exit 127 ("never overwritten: use a new name"). Every current caller writes into a fresh folder (checked: engine_bisect visits each candidate once, one folder per candidate), so none of them changes behaviour |
| H15-3 | check scripts that print a failure but exit 0: item 1 `b5_checks.sh` counted failures and always exited 0 (its 4-builder comparison was printed, never counted; the ABBA and full-epoch steps hid their exit codes behind `tail`); item 2 `prove_resume.sh finish` printed DIFFERENT with exit 0; `measure_rates.sh` printed the labels / rows.tsv hashes that "must be identical" without comparing them | each now exits 1 on a failed comparison (`measure_rates.sh`: a `same` check after the workers and prepare steps) |
| H15-4 | `measure_rates.sh` with an unknown step created BASE_DIR and wrote its 14 MB input before refusing; a killed `head` left a short `in220k.txt` that later runs reused silently | the step, python, relabel2.py, the probe and the source file are checked first; the input is written through `.part` and must hold 220,000 lines |
| H15-5 | `bridge_check.sh` with a wrong PROOF_DIR started the 1M-row prepare (minutes of CPU) before its first comparison failed | the proof job's files (rows.tsv, prepare.json, run_config.json, final/) and the tools are checked before anything runs, exit 2 |
| H15-6 | `fn_diff.py` without arguments, with a missing or unparsable file or an unknown function name: Python traceback | one line, exit 2 |

No other writer overwrites: all R14-B shell scripts refuse an existing output folder, the Python tools open their
outputs with "x", the installer refuses existing targets, relabel2.py renames only where designed (frozen, untouched).

Checks (02:28-02:33): the launcher before / after with cmd.exe as the program: masks `xyz` / `0x0` ran the program
(exit 0) before, exit 127 and not run after; `0x100000000` exit 127; `0xC` runs (exit 0); an existing `-Out` kept its
content. `test_tools.sh` **31 / 31** (3 new launcher cases); item 2 `test_helpers.py` **77 / 77** (11 new: fn_diff.py,
measure_rates.sh, bridge_check.sh, prove_resume.sh refusals - none of them starts a probe); `bash -n` on every changed
script; measure_rates.sh's `same` tested alone (identical -> 0, different -> exit 1). lowrun.ps1 is identical on the
three branches again: sha256 4f1052ba7af5f4a22408e8a1b1809181c74eebd9a346f100d1695b57dbca2a05 (was cc7f28dd..., now
in the hash sweep's allow list as the version from 20:27 to this hunt).
H15-7, found by re-running the hash sweep (02:35): two md5s cited in item 2's hunt-#10 record (c675dd5b..., 489c57ae...,
train.txt / labels.tsv of a scratch job under `C:/o14b/dir with spaces 2320/`) matched no repository file, so step 4
of final_checks.sh would have failed at the end of the job (its dry runs were before hunt #10). Recomputed from the
scratch files (equal) and added to the allow list with that reason; the sweep now reports 0 unmatched tokens.

### Final 1-hour bug hunt (04:13-05:15 by the PC clock; self-review, NOT independent)
Scope (written 03:36, before the hunt): (a) this branch's own tools with wrong arguments and broken input - the
classes hunts #13-#16 found elsewhere; (b) the adoption rehearsal from fresh clones again, since hunts #15-#16
changed lowrun.ps1 and the acceptance tools after its last run (22:35); (c) a second claims audit of the reports.

(a) 26 calls of commit_span.py, hash_sweep.py, analyze_watch.py, gpu_util_stats.py, trainer_watch.sh and pc_gate.ps1
(04:14); 12 were wrong, and reading pc_gate.ps1 found two more (a CPU that does not exist, the C: floor):
| # | finding | fix |
|---|---|---|
| F-1 | `pc_gate.ps1 -Cpus 99` (a CPU this PC does not have) gave no samples, an average of 0 and so **"ok" whatever the load**; an unknown `-Drive` or a CPU list that is not numbers gave exit 1 = "wait" forever | exit 2 with one line for a drive other than C / D / F and for any `-Cpus` entry that is not a CPU of this PC |
| F-2 | pc_gate.ps1 still applied the R13 floor C: >= 30 GB; Couns's rule for R14-B (14:40) is 50 | C: floor 50 (header and check) |
| F-3 | `trainer_watch.sh OUT abc` (or an UNTIL_EPOCH in the past) wrote the header and exited 0: a watcher that silently records nothing | exit 2 before anything is written |
| F-4 | `hash_sweep.py --files <misspelt path>` hashed nothing, so every cited hash looked unmatched (exit 1, as if the documents were wrong); a missing doc, allow file or repo: tracebacks | missing paths and a failing `git rev-list` are exit 2 with one line |
| F-5 | analyze_watch.py without arguments or with a missing file, gpu_util_stats.py with a missing CSV: tracebacks | one line, exit 2 (gpu_util_stats.py's output is unchanged: the running watcher parses it - checked with the watcher's own sed) |
| F-6 | `commit_span.py --gap -5` made every interval a "pause" | `--gap` must be >= 1 |

Kept: commit_span.py with an unknown branch or a date git cannot read ends with exit 2 and git's own message.
Valid use unchanged (04:17-04:22): the watcher's GPU columns from the fixed tool ("28.9 28.0"), analyze_watch.py on
the night log (8 regimes), the hash sweep (0 unmatched), pc_gate on C: (prints, exit 1 at 93 % total CPU while the
fresh-clone checks ran), commit_span.py (origin/opus-r14b-status: 120 commits 12:19 -> 03:36), trainer_watch.sh with a
valid end (header + one sample, exit 0). `test_tools.sh` **37 / 37** (six new cases, 04:24).

(b) `checks/fresh_checkout_checks.sh /c/o14b/fresh_0415` (04:13:51-04:17:25, BelowNormal on CPUs 2-3, the trainer on
CPUs 0-1): **0 failures** - relabel suite from the clone 157 / 0, LTO / PGO probes rebuilt = 565ddbf8... / 08299f9f...,
DLL rebuilt = b5 9eb29b7d..., forge_fastloader.py 39af47b0..., the loader self-test all passed, acceptance with the
rebuilt DLL 261 / 261 identical (old 28 s, fast 5 s), and the HANDOFF steps 1-3b on a fresh copy of the live trainer
tree: manifest 264 / 264, anchors OK, patched, both files copied with their sha256, acceptance 261 / 261 identical.
So the tools changed in hunts #15-#16 (lowrun.ps1, the strict compare) work end to end from fresh clones.

Seen during the hunt (not Opus's doing): at 04:13 D: had 48.88 GB free, under Couns's 50 GB floor (Opus's D:\o14b has
been 3.7 GB since 22:07; tonight's scratch is on C:); at 04:22 51.97 GB again. Nothing of Opus's was moved or deleted;
D: writes stayed at git commits.

(c) Claims audit, second pass (04:24-04:28): the hash sweep finds every cited hash (0 unmatched); counts, check
dates and times that changed after the first audit (23:24) were compared with the latest logs and commits. Updated:
the tool test count (37 in opus.sh's help, the skill, STATUS, FINAL_REPORT, memory), the fresh-clone and
final_checks dates in FINAL_REPORT's summary rows, the launcher row (its two new refusals), the CPU-sharing note (the
trainer has been on CPUs 0-1 since 22:59), the D: dip as a deviation and a disk owner item, HANDOFF's last live-tree
check (04:16), RELABEL_HANDOFF's suite count from a fresh clone (157 / 0, 04:13), and three stale "1-h hunt 05:00"
lines in the memory note. One more finding while reading the check scripts:
- F-7: `checks/verify_chain.sh` step 3 ran a scratch copy of the fresh-clone script (`/d/o14b/r2/fresh_checkout_checks.sh`,
  20:35, patched by a sed pattern the committed script no longer has), not the committed one next to it: a re-run
  would have tested with an old fresh-clone check, and in any other checkout it fails. Fixed: it calls the committed
  `fresh_checkout_checks.sh OUT_DIR`; `bash -n` OK; the chain itself is not re-run (minutes of CPU incl. a 1M-row
  prepare) - the called script ran at 04:13 with 0 failures. checks/README.md says so and lists the newer final
  checks (test_cli.py, test_helpers.py, dry runs 22:56 and 02:37).
- F-8 (04:28-04:31, item 1): **the installer's live-folder guard missed the `\\?\` spelling of the live trainer folder**
  (a path comparison; `os.path.samefile` sees the same folder). Shown on a stand-in: that spelling installed (exit 0,
  files patched) where the plain one was refused. Fixed with a file-identity check first; `test_installer.sh` 28 / 28.
  Details: item 1 RESULTS.md. The Bash tool turned that path's backslashes into `\?` once more while two documents
  were being edited (FINAL_REPORT, the skill); fixed with the Edit tool and checked byte by byte.
