---
name: forge-r15-candidates
description: One-command workflow (Opus R15, branch opus-r15-20261103) from a search idea to a gate-ready Forge candidate on the lock FD3A5190 source - fresh LF lock copy, patch as an OFF-by-default tune:: option, plain node check, cand_pack.ps1 (kit v2.3 -Expose pc1 = pc2, pin_check OFF/ON, 2-minute smoke, clean-room lint, RESULT.json, INDEX.md), CI sanitizer row, index_check before handing to the crew. Use whenever a new engine option / Elo candidate is built for the crew gate, an INDEX entry is needed, or pin / smoke / clean-room checks of any exe are asked for.
---

# Forge candidate workflow (R15 tools, 2026-11-03)

Tools: `D:\o15\wt\opus_r15\tools\` (branch `opus-r15-20261103`; README.md there lists every tool and its self-test).
Rules first: forge-pc-rules (latest round section) - own work on CPUs 0-1 (0x3) at Idle, <= 4 threads, D: >= 50 GB,
C: >= 30 GB, no sub-agents, never delete / kill, commit + push about every 10 minutes.

## Facts
- Lock = `forge_ltopgo_x_al1s198_v23.exe` sha256 fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072;
  source git d4f43124dde1d1e37de90e18930e374f32ea7ffa (= `grok-pc\forge_push\qa_ltopgo_al1_stage\src_al1s198_clean`).
  Pins: bench d11 312866, d13 862329, d16 3024920, d20 12389307, d22 34048354; perft 5 startpos 4865609, kiwipete
  193690690. (273845 / 718758 / 3028212 are the P7 option build - never use them.)
- Kit v2.3 `-Expose` on an unpatched fresh export reproduces FD3A5190 byte for byte (re-verified 2026-11-03 11:38).
- New options: an `int` in `namespace tune` of src/search.cpp, default 0, appended to `tune::parameters()` -> advertised
  by `uci` under -Expose (the crew's runner checks that), uci.cpp untouched (its `id author` must stay).
- Clean-room: ideas only; no other engine's code, constants, tables or weights; no vendor / model-company / engine
  names or licence headers in patches, comments or commit messages (cleanroom_lint.py checks; the commit trailer that
  names a model company is left out in R15 by Couns's rule).

## Steps
1. `bash tools/fresh_lock.sh D:/o15/cands_src/<x>`; edit with the Edit tool (LF files); commit in the scratch repo;
   `git diff HEAD~1 HEAD > opus_r15/cands/<name>/<name>.patch`.
2. Quick check: `bash tools/plain_build_r15.sh <repo> D:/o15/plain/<x>`, then `pin_check.ps1 -Exe ... -Full` (PASS) and
   `-Options 'Name=V'` (LIVE). Try 2-3 ON values only to see they are live; pick the ON value from Forge's own constants.
3. `powershell -NoProfile -ExecutionPolicy Bypass -File tools/cand_pack.ps1 -Name <name> -Tag <short> -Patch <p>
   -Option <Name> -On <V> -Idea '<one line>'` (~8 min: 2 kit builds, pins, 120 s smoke). One pack at a time (they share
   CPUs 0-1); chain several with a private bash script outside the worktree (never edit a running bash script).
4. CI: add a matrix row (default / on / edge / max) to `.github/workflows/opus-r15-san.yml` in the same commit as the
   patch; after the green run write `D:\o15\cands\<name>\ci.json` ({run, conclusion, commit}) and re-run make_index.py.
5. `python -I -B tools/index_check.py` before handing `D:\o15\cands\INDEX.md` to the crew. README.md per candidate:
   mechanism, one paragraph "why it should gain", OFF identity, own review (NOT independent). No Elo claims.

## Pitfalls (all hit on 2026-11-03)
- g++ by absolute path needs `C:\msys64\ucrt64\bin` on PATH or it exits 1 silently.
- Do not set MSYS_NO_PATHCONV around bash scripts that call native git with `/d/...` paths.
- PowerShell 5.1: `[ordered]` dict indexed by an int = by position; `>>` is UTF-16; native stderr + `2>&1` + 'Stop'
  throws; empty-string arguments vanish; variable names ignore case (`$on` = `$On`).
- pc_gate `-Cpus 0,1 -MaxMyCpu 60` also waits for your OWN pin checks / smokes on 0-1: they slow the pack chain.
- A failed pack leaves RESULT.json + src_pack/<tag>: rename them (`*_attempt1_failed`), never delete, then re-run.
- The kit profile is trained with the option OFF (frozen workload v1): ON code is cold-optimised. Say so in reviews.
