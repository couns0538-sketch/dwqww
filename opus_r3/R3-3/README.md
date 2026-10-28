# R3-3 gate proposals: how to reproduce

Everything here is read-only on PC data. No gate is started and the gate queue is not touched; the owner appends
entries from `GATE_ENTRIES.json` (or the JSON blocks in `GATE_PROPOSALS.md`) when they decide to.

Python: `C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B` (`$PY`), run at `nice -n 19`.
Scratch: `F:\opus_scratch\r3\R3-3\` (`W` below). Tools: `opus_r3/R3-3/tools/` (copies of `W/tools/`).

## 1. Copies of the PC queue files (read-only on the source)
```
cp -p /c/Users/Administrator/grok-pc/forge_push/autorestart/{forge_queue.ps1,forge_gates.json,forge_queue_state.json,forge_queue.log} $W/pc_copies/
cp -p /c/Users/Administrator/grok-pc/forge_push/FORGE_RESULTS.{csv,md} $W/pc_copies/
$PY tools/dump_manifest.py $W/pc_copies/forge_gates.json [--fields]
```

## 2. srands
```
$PY tools/make_cands.py $W/scan/cands.json $W/scan/cands_map.json 4          # deterministic SHA-256 candidates
$PY tools/srand_scan.py fs --root C:/Users/Administrator/grok-pc --root D:/grok-pc-data --root F:/forge_push \
    --root F:/opus_scratch --root C:/Users/Administrator/.claude/projects/D--grok-pc-data-dwqww/memory \
    --depth1 C:/Users/Administrator/Downloads --exclude F:/opus_scratch/r3/R3-3 --exclude F:/opus_scratch/build/r3_R3-3 \
    --exclude F:/opus_scratch/worktrees/opus_r3_gates/opus_r3/R3-3 --cands $W/scan/cands.json --out $W/scan/fs_scan.json
git for-each-ref --format='%(refname)' refs/remotes/origin refs/heads | grep -v '/HEAD$' > $W/scan/refs.txt; echo 17aa0cae1d36 >> $W/scan/refs.txt
$PY tools/srand_scan.py git --repo <worktree> --refs-file $W/scan/refs.txt --show-only-rev 17aa0cae1d36 \
    --cands $W/scan/cands.json --out $W/scan/git_scan.json
$PY tools/summarize_scan.py $W/scan/summary_all.json $W/scan/fs_scan.json $W/scan/git_scan.json
$PY tools/choose_srands.py $W/scan/cands_map.json $W/pc_copies/forge_gates.json $W/scan/srands.json $W/scan/fs_scan.json $W/scan/git_scan.json
```

## 3. Prebench pins (runner Bench1 protocol: fresh process per depth, Threads 1, Hash 16, OwnBook false, options)
```
git -c core.autocrlf=false archive --format=tar <head> src include CMakeLists.txt | tar -x -C <src_dir>
bash /d/grok-pc-data/dwqww/.claude/worktrees/b/tools/build_pc.sh <src_dir> <exe>       # default build
bash tools/run_pins.sh <exe> $W/pins/probe_<head>                                     # identity + every runtime option
bash tools/run_switch_pins.sh <src_dir> <head>                                        # five switch builds, OFF/ON pins
```

## 4. Approx model of SPRT [0,5] with a 1500-game cap (not fastchess figures)
```
$PY tools/sprt_cap_model.py $W/pc_copies/FORGE_RESULTS.csv $W/model/sprt_cap_model.json 20000 20261027
```

## 5. Documents
```
$PY tools/render.py $W $W/out                 # GATE_PROPOSALS.md, GATE_ENTRIES.json
$PY tools/render_srand_check.py $W $W/out     # SRAND_CHECK.md
```
`exe_map.json` holds the exe names and sha256 values; fill it from the main session's final exe list and re-render.

## Big outputs (kept in scratch, not committed)
| file | bytes | sha256 |
|---|---:|---|
| `F:\opus_scratch\r3\R3-3\scan\fs_scan.json` (file-system scan: every srand/seed context with path and snippet) | 15017203 | `a0371a62c3257595f134abc9d1e4518aa6722c93a5946d1010d567b5970c343f` |
| `F:\opus_scratch\r3\R3-3\scan\git_scan.json` (git scan, Sol's blobs via `git show`) | 982997 | `87e5170018d762dc1b5a10c657082a577a9f2933b76c0a0cd4c5e35dd64354d9` |
| `F:\opus_scratch\r3\R3-3\scan\git_scan_v1_catfile_incl_sol.json` (first git scan, Sol's branch read through its remote ref with cat-file; same result: 0 candidate hits) | 992663 | `a05c370534014501f1c1b6de0fd4858a578f311a8b09eacf1c21c0204c04914f` |
| `F:\opus_scratch\r3\R3-3\pc_copies\` (read-only copies of the runner, manifest, queue state/log, ledger; sha256 in GATE_PROPOSALS.md §8) | | |

Probe exes (not committed): `F:\opus_scratch\build\r3_R3-3\forge_r3probe_2047348a.exe` (sha256 `893ea34d…`), the five
`forge_r3probe_2047348a_<switch>.exe` and `forge_r3probe_ba03edf9_int16.exe`; sha256 in `logs/pins/run_*.log`.
