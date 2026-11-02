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
