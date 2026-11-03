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
| Forge tools, read-only | `F:\opus_scratchescore_d8inen2bin.exe` (self-play text -> FPOS), adapter `train_resid_nnuepytorch_v2.py` (read to find `--npt-repo` / `--npt-extra`), crew `disk_guard.log` | relabel output carries the new labels into .pos (1200/1200); item 1 adoption path; the D: dip was the self-play dedup DB, not a leak |
| own tools added | `opus_r14b/tools/cpu_users.ps1` (who uses CPUs 2-3), `opus_r14b/item2/fn_diff.py` (function-level diff), `label_stats.py` | load next to every rate; proof coverage of the post-proof code; descriptive label statistics |
