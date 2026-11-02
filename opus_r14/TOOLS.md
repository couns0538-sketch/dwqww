# R14 capability map (what I use, checked 2026-11-02; no invented commands)

| kind | name | use in R14 |
|---|---|---|
| project skills (`.claude/skills/`) | forge-pc-rules (binding), forge-candidate-checks, forge-lock-port, forge-ltopgo-pgo, forge-speed-stack, forge-engine-verify | every build / check / candidate (lock pins, kit v2.3 pc1 = pc2, proof set, ABBA) |
| project skills | forge-nnue-data, forge-nnue-pipeline, forge-nnue-pytorch-amd, forge-nnue-loader-checklist, forge-halfka-parity-test | P5 relabel data + sidecar, P4 nets / parity, GPU rules |
| project skills | forge-gate-stats, forge-spsa-tuning, forge-search-bug-hunt, forge-job-workflow | reading gate state, P3 lines, mate / TB probes, push / report workflow |
| plugin skills | superpowers: verification-before-completion, systematic-debugging, receiving-code-review, writing-skills | evidence before claims, failed checks, assessing CR notes, skill edits |
| not used | forge-subagent-brief, superpowers dispatching-parallel-agents / subagent-driven-development, code-review max/ultra, Workflow tool | Couns 2026-11-02: no sub-agents |
| CLI | gh (authenticated; repo couns0538-sketch/dwqww): run list/view, release view, api | CI ASan+UBSan results, Astra's release assets, remote heads |
| MCP | Context7 (library docs), Exa / Parallel / Firecrawl search (public papers, permissive engine code; GPL/AGPL = ideas only) | only when a design question needs it |
| MCP not used | Hugging Face, Linear, Notion, Supabase, Vercel, Postman, Claude Docs, Artifacts, Atlassian / Datadog / Slack / Sentry (unauthenticated), Unblocked (failed to connect) | no outside posts; reports live in the repo |
| local | Git Bash, PowerShell 7, MSYS2 ucrt64 g++ (`/c/msys64/ucrt64/bin`), MSVC Build Tools 18 (cargo link), cargo/rustc 1.99.1 at `F:\bullet_hip\rust\rustup\toolchains\stable-x86_64-pc-windows-msvc\bin` (read only; own CARGO_HOME `C:\o13\p4\cargo_home`) | builds |
| local | venv `C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B` (numpy, torch cpu, python-chess as run-only test oracle) | tools, parity, fits |
| local | QA kit v2.3 `...\qa_ltopgo_al1_stage\kit_v23\build_ltopgo.ps1` (md5 729fe727) | every candidate exe |
| local (R13 tools, branch opus-r13-p1-nearmiss-ports `opus_r13/tools/`) | pc_gate.ps1, run_low.ps1, run_pinned.py, kit_build.sh, cand_checks.py, selfplay_smoke.py, fresh_lock.sh, make_handoff_readme.py | load gate, priority + affinity, kit wrapper, UCI checks, handoff |
| GitHub Actions | `.github/workflows/opus-r13-san*.yml` (ASan+UBSan self-play on the lock + patch) | sanitizer smokes (no PC CPU) |

Pitfall seen 2026-11-02: MSVC link.exe leaves `VCTIP.EXE` running for minutes; `run_low.ps1` uses `Start-Process -Wait`,
which waits for the whole process tree, so a finished cargo build looked like it hung. Read the build log instead.
