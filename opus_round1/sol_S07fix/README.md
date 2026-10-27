# S07fix — WAC300 repeats: lock vs real candidate (S07-1), lock 3x at 1000 ms and the 271 vs 283 gap (S07-2)

No engine or harness change. Branch `opus-sol-S07fix` = AL1 base `d4f4312` + CI baseline `0d99f02` + this folder.
Every screen is one call of Sol's unchanged S07 tool in `wac300` mode (the harness of the official 271): fresh bare
`bench 11` process (must print 308972), then one UCI process, Threads 1, Hash 16, OwnBook false; per position
`ucinewgame` + `Clear Hash` + `go movetime T`; the final bestmove is scored against bm/am.

## Run (PC, Git Bash; Idle priority is inherited by the engines)

```sh
B=F:/opus_scratch/sol_S07fix/bin   # copies of forge_h256_e12.exe (lock) and forge_packa_h256.exe (gate38 candidate)
nice -n 19 python -I -B forge_sol_S07_wac_interleave_v2.py --tool forge_sol_S07_screen_sweep_20261026.py \
  --suite forge_sol_S07_wac300_20261026.epd --out NEW_DIR --arm lock=$B/forge_h256_e12.exe \
  --arm 'cand='$B'/forge_packa_h256.exe:{"NonPawnCorr": 1, "PawnHist": 1, "NonPawnCorrWeight": 55}' \
  --movetimes 100,1000 --reps 3 --order interleaved                                   # S07-1
nice -n 19 python -I -B forge_sol_S07_wac_interleave_v2.py ... --arm lock=$B/forge_h256_e12.exe \
  --movetimes 1000,250 --reps 3 --order blocked                                       # S07-2 (+ effort-matched 250 ms)
python -I -B forge_sol_S07_analyze_v2.py --runs RUN_DIR... --sol-wac-dir SOL_WAC_DIR --out analysis.json --md table.txt
```

The driver samples system CPU busy % every 5 s (GetSystemTimes) and free RAM, snapshots the top processes at each
screen start/end, records the engine's priority class during the screen, and extracts per position the last
`info` line before `bestmove` (nodes, nps, depth) from the tool's raw stdout.

## Files

- `forge_sol_S07_wac_interleave_v2.py` — driver (ordering, load log, per-screen search effort, summary).
- `forge_sol_S07_analyze_v2.py` — score vs search-effort table incl. Sol's 271 run, flips between repeats.
- `forge_sol_S07_screen_sweep_20261026.py`, `forge_sol_S07_wac300_20261026.epd` — Sol's tool and suite, unchanged.
- `logs/` — per-screen records, summaries, load samples, analysis table, Sol-run statistics, console logs.
