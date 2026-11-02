# RELABEL_HANDOFF - for Engine NNUE (R14-B item 2; UNPROVEN as training data, the 50M run is NOT started)

## What you get
`relabel2.py` relabels self-play positions with a fixed-node search of the lock engine (R13 probe, lock source
d4f4312, state cleared before every search, 1 thread, Hash 1 MB), keeps the **original FEN** (castling, en passant,
clocks; the label is searched on exactly that FEN, which the probe echoes back and the tool checks), splits
validation **by game** (no game in both), and can be killed at any moment and resumed with the same command.
Outputs per job: `final/train.txt`, `final/val.txt` (self-play text format `FEN | new stm cp | white result`, ready
for the existing converters), `final/labels.tsv` (row id, game id, split, FEN, new and old score, result, depth,
nodes), `final/MANIFEST.json` (md5 + sha256). Exit codes: 2 bad input, 3 configuration differs, 4 integrity.

## Commands (PC rules: Idle, CPU mask, <= 2 probe workers; nothing is deleted or overwritten)
```bash
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe   # python-chess 1.11.2
R=<branch opus-r14b-relabel>/opus_r14b/item2/relabel2.py
$PY -I -B $R prepare --job D:/<new job dir> --run-id <id> --rows 50000000 \
    --selfplay D:/grok-pc-data/selfplay_out/forge_selfplay_001.txt ... [--val-ppm 10000] [--salt <salt>]
$PY -I -B $R run --job D:/<job dir> --run-id <id> --probe 'C:\o13\p5\forge_data_probe.exe' \
    --nodes 20000 --workers 2 --mask 0xC [--until "YYYY-MM-DD HH:MM"]     # same command again = resume
$PY -I -B $R assemble --job D:/<job dir> --run-id <id>
$PY -I -B $R status --job D:/<job dir>
```
Astra's filter (`filter_positions.py`, branch astra-r8-datafilter) runs before or after as Engine NNUE decides; its
normalized JSONL output is accepted with `--normalized` when the rows are in source order.

## Cost (measured 2026-11-02 on the 1M proof runs; 20,000 nodes, Hash 1 MB, 1 thread per probe)
| quantity | value | source |
|---|---|---|
| positions / hour, 1 probe worker, Idle on one CPU shared with the Idle npt trainer | **~340,000** (run A 339,856, run B 342,331 after 6 shards; 104-105 s per 10,000 rows) | proof `status.json`, shard summaries |
| R13 job1 for comparison (same probe, 20k nodes, CPU 3, Idle) | 353,917 | R13 P5 RESULTS |
| mean nodes per position / search depth | 19,996 / mostly 8-11 (7: 1.2 %, 8: 16.6 %, 9: 42.5 %, 10: 26.1 %, 11: 8.1 %, >= 12: 5.5 %) | shard 0 of run A |
| **50M rows: probe thread-hours** | **~147 h** (50,000,000 / 340,000) | |
| **50M rows: wall time** | **~147 h with 1 worker, ~74 h (3.1 days) with 2 workers** (`--workers 2`, the R14-B thread budget); resumable at any time with the same command | |
| prepare (validation with python-chess, game ids) | 1M rows: ~10 min per job at Idle next to BelowNormal training (21 min for two jobs, measured); 50M: ESTIMATE up to ~8 h of one Idle thread at that rate (an uncontended measurement follows after the proof) | `prove_resume.sh prepare` |
| disk per 1M rows | rows.tsv 86 MB + shard labels ~90 MB + final train/val text ~75 MB + final labels.tsv ~90 MB = **~340 MB**; 50M rows **~17 GB** (keep D: >= 50 GB free: plan the job folder accordingly) | proof job folder |
| lower node counts | not measured in R14-B (the proof runs used the CPU budget); the probe cost is about proportional to nodes | - |
