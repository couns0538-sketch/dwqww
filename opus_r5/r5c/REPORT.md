# Forge Opus R5C: v4 NNUE (J7 L2=16) engine support + N3 Syzygy / IntendedThreefold / HardDeadline hardening — IN PROGRESS

**Status:** 00_baseline done; M1 in progress. Last push: see the head commit time (pushes every 10 min).

Branch `opus-r5c-netv4` = `origin/forge-bundle-int` b7c1772 + R5C commits. Job folder `opus_r5/r5c/`, scratch
`F:\opus_scratch\r5\r5c\` (exes in `exe\`, sha256 in `EXES.txt`). Machine exclusive: no (live gates, NNUE training
and self-play the whole time). Every build, test and bench at BelowNormal (Git Bash `nice -n 10`), at most 3 threads
in total, engine runs with Threads <= 3 (1 unless a test says otherwise). No Elo claims; no gate run by me.

Time base: the PC clock reads PST but runs 9 h ahead of GitHub's server clock (`gh api -i rate_limit` Date header,
08:19 GMT at 09:20 Vienna); Vienna (CET, UTC+1) = PC "PST" time - 1 h. Every time below is Vienna.
Job start 09:20 Vienna (3 h cap: 12:20 Vienna).

## 00_baseline

Build (job-spec flags, R5B script `tools/build_r5c.sh`, RECIPE=v3: MSYS2 ucrt64 g++ 15.2, 8 units in parallel with
JOBS <= 3 at BelowNormal, static link):
```
RECIPE=v3 bash opus_r5/r5c/tools/build_r5c.sh "$PWD" /f/opus_scratch/r5/r5c/exe/<name>.exe [-D switches]
# g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -mtune=znver5 -pthread -static
```
Check: lock `2_build/uci_check.py <exe> --full` (fresh process, Threads 1, Hash 16, OwnBook false).

## OFF identity after every milestone (rule 7)

| after | exe (F:\opus_scratch\r5\r5c\exe) | sha256 | bench d11 / d13 / d16 / d20 / d22 | perft 5 | kiwipete 5 | FMA | result |
|---|---|---|---|---|---|---|---|
| 00 baseline | forge_r5c_off_v3_b7c1772.exe | 01aed2d9... | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK (`logs/identity_off_v3_b7c1772.log`) |

## M1: N3 hardening (pending)

## M2: N3 gate pack (pending)

## M3: v4 format + engine inference (pending)

## M4: exporter + parity (pending)

## M5: handoff (pending)

## What to gate first (pending)

## What I did not finish (pending)
