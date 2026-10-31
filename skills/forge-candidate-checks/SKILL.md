---
name: forge-candidate-checks
description: The R13 per-candidate proof set for a Forge gate candidate built with QA's LTO+PGO kit - PC load/disk gate, kit pc1/pc2 wrapper (binding exe sha256 equality), OFF pins / ON-live identity, uci option list, T1/T4 movetime smoke with engine-side legality (go perft 1), mate probe OFF/ON, GitHub ASan+UBSan self-play (no python-chess), handoff README and RESULTS table. Use whenever a candidate exe is built for the crew gate or a check from the R13 list is asked for.
---

# Candidate checks (R13, 2026-10-31)

Rules: [[forge-pc-rules]]; kit facts: [[forge-ltopgo-pgo]]; porting: [[forge-lock-port]].
Tools in `opus_r13/tools/` (branch opus-r13-p1-nearmiss-ports). Python: venv `C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B`.

## Before any heavy step
`powershell -NoProfile -ExecutionPolicy Bypass -File pc_gate.ps1 [-Drive C -NeedGB 1 -MaxCpu 85 -MinRamGB 6]`: free
C:/D:/F:, total + per-CPU load, RAM; exit 0 = go. R13 PC (2026-10-31): gate on 0xFFF0 (8 engines), self-play Idle on
CPUs 4-15, trainer Idle 0x000F at ~25% -> my work on CPUs 2-3 (0xC), BelowNormal, <= 2 threads. Scratch on C:\o13 (F: < 50 GB).

## Build (binding: pc1 = pc2)
`bash kit_build.sh <scratch repo> <tag> 'N=V' 'N1=V1;N2=V2' ...` -> kit v2.3 (md5 729fe727) twice from fresh clean exports
(`C:\o13\src\<tag>_pc1|pc2`), `-Work C:\o13\w -Affinity 0xC -Expose`, OFF pins + perft pins, one -CheckOpt per gate line,
then compares the two forge_ltopgo exe sha256. ~3 min per build with 2 CheckOpts. Evidence: `<Work>\<tag>_pcN\SUMMARY.txt`,
`ident\off.compare.txt`, `ident\optN.compare.txt` (plain = LP per depth, "differs from OFF (live)"), "real missing-profile
warnings: 0", vfmadd 0.

## UCI checks
`run_pinned.py --mask 0xC -- cand_checks.py EXE OUT.json --line "N=V;..." --new-opt SWITCH --new-param NAME=DEFAULT`
- option list: switches advertised with default OFF, parameters with their original default;
- T1 + T4 `go movetime 1000` on 4 positions per line (T4 runs on the 2-CPU mask), waits for bestmove, legality via the
  engine's own `go perft 1` divide list;
- mate probe: `tools/data/mate_probe.epd` (R5D barek20 KRK/KQK + 2 mate-in-1), `go nodes 3000000`, OFF vs each line.
  Deep KRK mates (M14-M17) flip at the node horizon in both directions; re-probe a "lost" one with
  `--skip-smoke --mate-epd one.epd --mate-nodes 30000000` (packa w60: found at 30M). Report counts, not just PASS/FAIL.

## Sanitizer (GitHub, no PC CPU)
`.github/workflows/opus-r13-san.yml`: per matrix item, lock d4f4312 (`git fetch --depth 1` by sha) + `patch -p1 -F0`, g++ 13
`-fsanitize=address,undefined -fno-sanitize-recover=all -march=x86-64-v3 -DFORGE_EXPOSE_TUNABLES=1`, then
`selfplay_smoke.py` (configs: default, each gate line, max values; 4 games x <= 160 plies, `go nodes 20000`, legality via
`go perft 1`, stderr scanned for sanitizer lines). Item `lock` = unpatched control. Read results with
`gh run view <id> --log | grep -E '"config"|SELFPLAY SMOKE'` and save that to `logs/ci_san_<id>.txt`. ~5 min per run.

## Handoff + RESULTS
README per item (exe path + sha256, setoption lines, ON bench 13 precondition, check table), RESULTS.md row per check
with PASS/FAIL and the evidence path, STATUS.md line on opus-r13-status. No Elo or speed claims (UNPROVEN until a gate).
