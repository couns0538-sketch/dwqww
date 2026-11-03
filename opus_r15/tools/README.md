# R15 tools (opus_r15/tools) - re-runnable, each with a self-test

Python = the read-only venv `C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe` run with `-I -B` (3.10,
standard library only for every R15 tool). PowerShell scripts run under Windows PowerShell 5.1
(`powershell -NoProfile -ExecutionPolicy Bypass -File ...`). Own work: CPUs 0-1 (mask 0x3), Idle (the kit sets
BelowNormal on itself), scratch and outputs under `D:\o15`. Never overwrite: every tool refuses an existing output.

| tool | what it does | self-test (last result) |
|---|---|---|
| `pin_check.ps1` | any exe vs the lock pins: bench d11/d13/d16 (`-Full` + d20/d22), perft 5 startpos + kiwipete -> PASS / FAIL; `-Options 'N=V'` = ON line (advertised, in range, accepted, live, perft = pins -> LIVE); `-Expect 'd11=..'` = exact nodes; `-Json` record | `bash test_pin_check.sh OUT` - 12 / 12 (test_logs/test_pin_check_1.log) |
| `cand_pack.ps1` | patch -> gate-ready candidate: fresh LF lock copy, patch -p1 -F0 (dry run), cleanroom_lint, kit v2.3 `-Expose` pc1 + pc2 with `-CheckOpt`, pc1 = pc2, kit identity / vfmadd / missing-profile / ON-live, exe copy, pin_check OFF + ON, smoke2m ON, RESULT.json, INDEX.md (+ branch copies); `-NoPatch` = base re-verify | `bash test_cand_pack.sh OUT` - 9 / 9 refusals and early stops (bad tag / name, missing patch, two options, existing record / tag, lint FAIL before the kit, patch not applying); full runs = C1-C5 (D:\o15\cands\*\pack.log) |
| `kit_build_r15.sh` | QA kit v2.3 wrapper (R14 kit_build_r14.sh with D:\o15 paths, CPUs 0-1, TMP on D:, the FIXED pc_gate, R15 disk floors D: 50 / C: 30) | base re-verify: unpatched lock -> sha256 fd3a5190... = the lock (opus_r15/base/) |
| `smoke2m.py` | timed ON-vs-ON self-play at a real clock (Threads 2, Hash 16, 2000+20), every bestmove against the engine's own `go perft 1` list; illegal / crash / hang / time loss (beyond fastchess's 1000 ms margin) fail it | `bash test_smoke2m.sh OUT` - 11 / 11 + 5 count checks (stub engines: illegal, crash, hang, stderr, slow) |
| `cleanroom_lint.py` | patches and commit messages: no vendor / model-company / other-engine names (list stored base64), no licence headers, uci.cpp `id author` / tools/openings / LICENSE untouched, LF + ASCII added lines | `python test_cleanroom_lint.py OUT` - 15 / 15 |
| `make_index.py` | INDEX.md from every RESULT.json (+ ci.json), regenerated as a whole, sorted; extras and base runs in their own sections | used by cand_pack on every run |
| `index_check.py` | before queueing: exe sha256 / md5 = record, record checks all PASS, patch sha256, CI success, option advertised by the exe with default 0 and the ON value in range | `python test_index_check.py OUT` - 8 / 8 |
| `gate_summary.py` | fastchess gate folder(s) or `--all ROOT`: W/D/L, pentanomial, Elo +/- , nElo, exact GSPRT LLR, time forfeits / illegal / disconnects (PGN + log), games/h, and a check that the log games reproduce the printed block; `--watch` = games per 10 min + mean depth / s per move per engine (is the gate at normal speed?); `--html OUT` = one self-contained sortable page of all gates | `bash test_gate_summary.sh OUT` - 8 / 8 + 2; full sweep of F:\forge_push: 62 / 62 gates with a PGN reproduce W/D/L, Ptnml, Elo, error and LLR exactly (test_logs/gate_summary_all_F.txt) |
| `extra_check.py` | an EXISTING exe whose option was never gated alone (no build): copy + sha256, pin_check OFF / ON, smoke, RESULT.json kind "extra", INDEX section | its runs x1 / x2 (D:\o15\cands\x*\RESULT.json) |
| `ci_record.py` | ties a green opus-r15-san run to the exact built patches (patch sha256 at the run's commit = the record's) and writes each candidate's ci.json + the evidence file | `python test_ci_record.py OUT` - 4 / 4 (tampered sha, patch not in the commit, cancelled run) |
| `plain_build_r15.sh` | quick plain build (the lock g++ line + Expose) of a scratch repo, Idle on 0x3 - node checks only, never a gate exe | used for C1-C5 first checks |
| `fresh_lock.sh`, `export_src.sh` | fresh LF lock copy with a scratch git repo (base commit = the lock) / clean export for the kit | R13 tools, used by every build |
| copied unchanged (sha256 in opus_r15/STATUS.md) | `lowrun.ps1`, `pc_gate.ps1` (R14-B fixed copy), `cpu_users.ps1`, `doc_lint.py`, `hash_sweep.py`, `commit_span.py` (R14-B), `selfplay_smoke.py`, `run_pinned.py` (R13) | their own R14-B / R13 tests |

## Typical use
```
# a new candidate: write the patch on a fresh lock copy, quick node check, then the full pack
bash opus_r15/tools/fresh_lock.sh D:/o15/cands_src/x          # edit, commit in the scratch repo, git diff HEAD~1 > x.patch
bash opus_r15/tools/plain_build_r15.sh D:/o15/cands_src/x D:/o15/plain/x
powershell -NoProfile -ExecutionPolicy Bypass -File opus_r15/tools/pin_check.ps1 -Exe D:\o15\plain\x\forge_plain.exe -Full
powershell -NoProfile -ExecutionPolicy Bypass -File opus_r15/tools/pin_check.ps1 -Exe D:\o15\plain\x\forge_plain.exe -Options 'MyOption=1'
powershell -NoProfile -ExecutionPolicy Bypass -File opus_r15/tools/cand_pack.ps1 -Name c9_x -Tag c9x -Patch x.patch -Option MyOption -On 1 -Idea '...'
python -I -B opus_r15/tools/index_check.py            # before handing D:\o15\cands\INDEX.md to the crew
# a gate: summary, or the speed of a running gate
python -I -B opus_r15/tools/gate_summary.py F:\forge_push\gate_X
python -I -B opus_r15/tools/gate_summary.py F:\forge_push\gate_running --watch --last-min 60
```

## Pitfalls met while writing them (2026-11-03)
- g++ started by an absolute path exits 1 with no message unless `C:\msys64\ucrt64\bin` is on PATH (plain_build_r15.sh sets it).
- `MSYS_NO_PATHCONV=1` must NOT be set around bash scripts that call native git with `/d/...` paths (fresh_lock failed).
- PowerShell 5.1: an `[ordered]` dictionary indexed with an int reads by POSITION; `>>` writes UTF-16; native stderr with
  `2>&1` under `$ErrorActionPreference='Stop'` throws; an empty string argument to a native program is dropped; `$on`
  and `$On` are the same variable. All four bit once and are handled in pin_check.ps1 / cand_pack.ps1.
- fastchess's printed numbers: W/D/L and Games count COMPLETE pairs only; empty pentanomial cells count 1e-3 in the
  LLR; the MLE starts from the uniform pdf with at most 10 steps; the PGN's write order is not the printing order (use
  the log's "Finished game" lines before the printed block).
