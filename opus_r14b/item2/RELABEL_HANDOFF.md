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

## Cost (measured; filled in from the 1M proof runs)
| quantity | value | source |
|---|---|---|
| positions / hour, 1 probe worker, 20k nodes, Idle on one CPU shared with the Idle npt trainer | TBD | proof run A status.json |
| 50M rows: probe thread-hours | TBD | 50,000,000 / rate |
| 50M rows: wall time at 1 / 2 workers | TBD | |
| prepare (validation of 1M rows) | TBD | prepare timing |
| disk per 1M rows: rows.tsv + shard labels + final files | TBD | job folder size |
