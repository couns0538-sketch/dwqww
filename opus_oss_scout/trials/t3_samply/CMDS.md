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
Recording, from Git Bash. The workload `data/bench20.txt` contains `bench 20` + `quit`; the engine reads it on stdin.
```
dl/samply-0.13.1/x/samply.exe record --save-only --unstable-presymbolicate --rate 4000 \
  -o build/t3/<tag>/profile.json.gz -- <exe> < data/bench20.txt
```
Hotspot table: `python -I -B tools/t3_samply_top.py build/t3/<tag>/profile.json.gz --top 30`.
