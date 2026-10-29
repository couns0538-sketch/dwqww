# Forge Opus round 5A: gate-ready singles (CorrMargins, CorrExt, CorrHistPlus variants, NetScale) — IN PROGRESS

**Status:** 00_baseline done; M1 in progress. Last push 02:00 Vienna.

Branch `opus-r5a-singles` = `origin/forge-bundle-int` b7c17722 + the commits listed per milestone. Job started 01:52 Vienna
(2026-10-29), hard stop 04:52 Vienna. No Elo claims: node counts are not strength; gates decide. Machine exclusive: no
(gates, NNUE training and self-play kept running; all my work at BelowNormal, at most 3 threads in total).

Time base: the PC clock reads PST but runs 9 h ahead of GitHub's server clock (`gh api -i rate_limit` Date header);
Vienna (CET, UTC+1) = PC "PST" time - 1 h. Every time below is Vienna.

## 00_baseline (01:52-02:00 Vienna)

Build (PC lock recipe flags from the job spec; script `tools/build_r5a.sh`, 3 parallel compiles at BelowNormal):
```
bash opus_r5/r5a/tools/build_r5a.sh "$PWD" /f/opus_scratch/r5/r5a/exe/forge_r5a_base_b7c1772.exe
# g++ 15.2 ucrt64: -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math
#                  -march=x86-64-v3 -mtune=znver5 -pthread -static
```
Exe `F:\opus_scratch\r5\r5a\exe\forge_r5a_base_b7c1772.exe`, sha256 `82d414ba9a3f670287090f11ada392e46f415df9e1da46b362324c90314b6768`
(also in `EXES.txt` here and next to the exe), 0 compiler warnings, FMA count 0.

Identity (lock `uci_check.py --full`: Threads 1, Hash 16, OwnBook false), log `logs/identity_base_b7c1772.log`:

| check | got | pin | result |
|---|---|---|---|
| bench d11 | 312866 | 312866 | OK |
| bench d13 | 862329 | 862329 | OK |
| bench d16 | 3024920 | 3024920 | OK |
| bench d20 | 12389307 | 12389307 | OK |
| bench d22 | 34048354 | 34048354 | OK |
| perft 5 startpos | 4865609 | 4865609 | OK |
| perft 5 kiwipete | 193690690 | 193690690 | OK |
| FMA instructions | 0 | 0 | OK |

PC safety note (temperature rule): `tools/cpu_temp.sh` reads the live HWiNFO64 sensor log (read-only). The rule's
"CPU hot spot" is taken as HWiNFO's **CPU IOD Hotspot** sensor (~49-50 C). HWiNFO's Tctl/Tdie (control temperature)
already read 79.8-81.1 C at 121 W package power from the PC's own load (gates + training) in the ten minutes before
my first command (01:43-01:52 Vienna), i.e. the CPU regulates at about 80 C by itself; my 3-thread build added at
most +0.5 C. If the owner meant Tctl/Tdie, every step of this job ran with Tctl at about 80 C (logged per milestone).

## Milestones
- M1 per-option audit + ON benches: in progress
- M2 effective-settings echo + conflict guards: not started
- M3 smoke stability: not started
- M4 gate pack: not started
- M5 SPSA hooks (optional): not started

## What to gate first
(filled at M4)

## What I did not finish
(filled at the end)
