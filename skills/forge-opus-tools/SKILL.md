---
name: forge-opus-tools
description: Small own tools (Opus R14-B, branch opus-r14b-status, folder opus_r14b/tools/) for day-to-day Forge work on grok-pc - opus_status.sh (one read-only look at worktrees, own processes, CPUs 2-3, RAM / disks, the npt keeper), abba.py (palindromic A/B timing of ANY two commands with identity check, Student-t CI and load capture), doc_lint.py (control bytes, CRLF, mojibake, eaten Windows backslashes, broken GitHub tables, dead links), hash_sweep.py (cited hashes still match real files / commits), engine_fresh_check.sh (fresh export of an engine ref, lock-recipe build, bench / perft pins), commit_span.py (time per branch and pauses from commit times), cpu_users.ps1, pc_gate.ps1, lowrun.ps1, and test_tools.sh. Use before timing anything, before a push of documents, when checking that an engine branch still equals the lock, when a report needs time figures, or when asked what is running / how the PC looks.
---

# forge-opus-tools (Opus R14-B, `opus_r14b/tools/` on `opus-r14b-status`)

All own code (stdlib Python, bash, PowerShell); nothing here changes or stops another process. Python: the venv
`PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe` (3.10: no backslashes inside f-string braces), run
with `-I -B`. `T=<worktree>/opus_r14b/tools`. Tests: `bash $T/test_tools.sh C:/o14b/<new folder>` (14 checks, ~30 s,
must end `ALL PASS`; covers abba.py and doc_lint.py).

## opus_status.sh - what is going on (read-only, ~10 s)
`bash $T/opus_status.sh [--ci] [WORKTREE_GLOB]` (glob default `o14b-*` under `.claude/worktrees`): per worktree branch,
head, ahead / behind upstream, uncommitted files (+ the latest GitHub Actions run with `--ci`); own processes
(relabel2 / probes / loader tools / g++ / launchers) with priority, affinity, CPU seconds and a shortened command;
who uses CPUs 2-3 now (cpu_users.ps1, 3 s); RAM and C: / D: / F: free against the floors; the npt keeper STATUS head.
Edit the process regex in the script (`$pat`) when a job adds new tool names.

## abba.py - is B faster than A? (any two commands)
```bash
$PY -I -B $T/abba.py --out C:/o14b/<new> --a "CMD A" --b "CMD B" --pairs 10 \
    [--metric 'rows/h ([0-9,]+)' --higher-better] [--identity 'labels md5 ([0-9a-f]{32})' --identity-ab] \
    [--mask 0xC] [--priority Idle|BelowNormal] [--cwd DIR] [--shell bash|cmd] [--warmup 1] [--load-every 5]
```
- Slots alternate A B / B A (ABBA over every two slots: linear drift cancels). The driver pins ITSELF (mask +
  priority) before starting anything, so every child and grandchild inherits both (no race, no psutil).
- Value: wall seconds, or group 1 of the LAST `--metric` match in stdout+stderr (commas removed). Speed-up per pair
  = A/B (times) or B/A (`--higher-better`); summary = geometric mean, two-sided 95 % Student-t CI on log ratios
  (table to df 30, Cornish-Fisher above; max error vs scipy 0.0005 over df 1-2000), median, min, max.
- `--identity`: all matches of the regex must be the same in every run of one command (stops at once, exit 2);
  `--identity-ab` also A = B. Use it for bench nodes, label md5s, batch hashes - a speed number for two programs that
  do not compute the same thing is worthless.
- A/A: `--a X --b X` = the PC's noise floor right now. For exes compare byte COPIES too (per-file layout effects,
  R5B lesson); the engine-specific drivers (`opus_r5/r5b/nps_ab.py`, `opus_r12/tools/r12_speed.py`) do that for bench.
- Outputs (refused when `--out` exists): `runs.tsv`, `runs/<slot>_<arm>.txt`, `load.txt`, `summary.txt`. Exit 0 /
  1 a run exited nonzero / 2 bad arguments, identity differs, metric missing. No timeout: a hung command blocks it.
- Always quote the load lines from summary.txt next to the number; Idle work on CPUs 2-3 yields to crew BelowNormal
  jobs (Astra's profile_corpus.py with affinity 0xFFFF starved R14-B runs for minutes). CPUs 2-3 = ONE physical core.

## doc_lint.py - text files that would mislead or break
`$PY -I -B $T/doc_lint.py PATH... [--include-logs] [--quiet]` -> `file:line: [check] message`, exit 0 clean / 1 findings
/ 2 bad args. Checks: `control` (bytes < 0x20 except TAB/LF, lone CR), `crlf` (in .sh .py .ps1 .cpp .md .yml .tsv
.sha256), `utf8` (not UTF-8, U+FFFD, BOM before .sh/.py), `drive` (a drive letter glued to a name: eaten
backslashes), `conflict` (merge markers), `table` (GitHub table rows with more / fewer cells than the header: a `|`
inside `code` still splits a cell unless written `\|`), `link` (relative Markdown links to missing files). A line
containing `doc_lint: ignore` skips the drive / U+FFFD / link checks. logs/ folders are skipped unless asked.
Run it on every branch folder and on `.claude/skills` before a push of documents (it found a broken RESULTS table
on its first run, 2026-11-02).

## hash_sweep.py - do cited hashes still exist?
`$PY -I -B $T/hash_sweep.py --docs <md files> --files <files or dirs> --repo <repo> --allow $T/hash_sweep_allow.txt`:
every 8-64 hex token with a letter must prefix the sha256 / md5 of a given file, a commit, or be allow-listed with a
reason. Run after a code freeze and before the final report (catches a stale sha256 after a late fix).

## engine_fresh_check.sh - does an engine ref still search the lock's tree?
`bash $T/engine_fresh_check.sh REF C:/o14b/<new> [--quick] [extra g++ flags]`: `git archive REF src include` (LF, no
worktree, REF needs a top-level src/), lock-recipe direct g++ build (ucrt64 g++, -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256
-ffp-contract=off -fno-fast-math -march=znver5 -static -pthread, all src/*.cpp or `FORGE_UNITS`) on CPUs 2-3 at
BelowNormal via lowrun.ps1, exe sha256 + FMA count (0 for the lock recipe), then the lock package's `uci_check.py`
(`UCI_CHECK` overrides the path): bench d11/13/16/20/22 = 312866 / 862329 / 3024920 / 12389307 / 34048354, perft 5
startpos 4865609, kiwipete 193690690 (`--quick`: d11/13/16 + perft). Exit 0 ALL OK / 1 differs / 2 usage / 3 build.
This is the "options OFF = lock" identity only; ON behaviour, CTest, sanitizers and LTO+PGO builds stay with
forge-engine-verify, forge-candidate-checks and forge-ltopgo-pgo.

## Small helpers
- `commit_span.py --repo D:/grok-pc-data/dwqww --since "2026-11-02 12:00" origin/<b1> origin/<b2> ...`: commits,
  first / last commit and span per branch, then one merged timeline with every pause > `--gap` minutes and commits per
  hour - the time figures for a report come from here, never from memory (memory rule "measure time from commits").
- `cpu_users.ps1 -Mask 0xC -Seconds 5`: processes that used CPUs of the mask in the window, busiest first.
- `pc_gate.ps1` (R13): load / RAM / disk gate before a heavy step.
- `lowrun.ps1 -Mask 0xC -Priority BelowNormal|Idle -Exe <prog> -ArgLine "<args>" [-In/-Out/-Err files]`: run one
  program (and its children) pinned at low priority; exit code = the program's.

## Pitfalls met while building these (2026-11-02)
- The Write tool turns `\uXXXX` in file content into the real character: write `chr(0xFFFD)` in code instead.
- Python 3.10 (the venv) rejects backslashes inside f-string braces: compute such values first.
- `sed` replacements containing `|` and backticks are easy to get wrong: use the Edit tool for exact text, then
  re-run doc_lint / the tests.
- A tool that checks for a pattern contains that pattern: mark fixture lines `doc_lint: ignore` or write the regex so
  it does not match itself (`C:[o]14b`).
- The PC thread budget (<= 2 own threads) includes running checks: do not start a build or bench while own probes run.
