# T3 samply profile of a Forge bench - exact commands

Base folder: `C:\opus_5h\oss_scout`. The session is elevated (High Mandatory Level), which samply's ETW recorder needs on
Windows. Idle priority, CPUs 2-3 (inherited).

## Tool
- samply 0.13.1 (MIT OR Apache-2.0): `dl/samply-0.13.1/samply-x86_64-pc-windows-msvc.zip` from
  https://github.com/mstange/samply/releases/tag/samply-v0.13.1.
  - zip sha256 8fed74dac18197bbb2520125b0199255e09709bed7903a7672a06225a5d7e976, equal to the release's `.sha256` file.
  - Unpacked to `dl/samply-0.13.1/x/samply.exe`; no install, no PATH change.

## Profiled programs
- `build/t2/m2use_lsx/forge_m2use_lsx.exe` + `forge_m2use_lsx.pdb`: the T2 clang 23 build (ThinLTO + IR PGO, MSYS2
  libstdc++). Node-identical to the lock (pin_check full PASS), so its hotspots stand for the lock's code. Symbols come
  from its PDB.
- `build/lock/forge_trial_w6.exe`: the lock itself (g++ LTO+PGO, no PDB). Recorded to check what samply resolves
  without a PDB.

## Commands
1. First attempt (fails here; xperf missing):
   `dl/samply-0.13.1/x/samply.exe record --save-only --unstable-presymbolicate --rate 4000 -o build/t3/m2use/profile.json.gz -- <exe> < data/bench20.txt`
   -> "Could not start xperf: Could not find an xperf installation." (`logs/samply_record_xperf_missing.log`).
2. Used instead (Git Bash; the workload `data/bench20.txt` = `bench 20` + `quit` on stdin):
```
wpr -start CPU -filemode
./build/t2/m2use_lsx/forge_m2use_lsx.exe < data/bench20.txt > build/t3/m2use_wpr/bench.out
MSYS_NO_PATHCONV=1 wpr -stop 'C:\opus_5h\oss_scout\build\t3\m2use_wpr\trace.etl'
./dl/samply-0.13.1/x/samply.exe import --save-only --unstable-presymbolicate \
  --symbol-dir C:/opus_5h/oss_scout/build/t2/m2use_lsx -o build/t3/m2use_wpr/profile.json.gz build/t3/m2use_wpr/trace.etl
```
   The trace ran 20:07:04-20:07:10 (PC clock). bench 20 gave 12389307 nodes, 2547667 nps during the trace.
3. Tables:
```
python -I -B tools/t3_samply_top.py build/t3/m2use_wpr/profile.json.gz --process forge_m2use_lsx.exe \
  --exe C:/opus_5h/oss_scout/build/t2/m2use_lsx/forge_m2use_lsx.exe --pdb C:/opus_5h/oss_scout/build/t2/m2use_lsx/forge_m2use_lsx.pdb \
  --symbolizer C:/opus_5h/oss_scout/dl/llvm-mingw-20261104/x/llvm-mingw-20261104-ucrt-x86_64/bin/llvm-symbolizer.exe --top 25
python -I -B tools/t3_samply_top.py build/t3/m2use_wpr/profile.json.gz --process forge_ltopgo_x_al1s198_trial_w6.exe \
  --exe C:/opus_5h/oss_scout/build/lock/forge_trial_w6.exe --symbolizer <same> --top 25
```
   The second table uses the lock processes of the live gate that were sampled in the same trace, symbolized from a
   byte-identical copy of the lock exe (sha256 4181a589).
