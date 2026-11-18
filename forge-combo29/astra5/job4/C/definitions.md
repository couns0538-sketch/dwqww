# Null cutoff measurement

The base for `../null_count.patch.txt` is the PC source with `../null_floor.patch.txt` applied. Apply the count patch with `patch -p1 -F0`. Build Release with `-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`. The compiler and CMake output, executable hash and patch hash are in `build.txt`.

The counted build uses the actual post-floor child depth passed to `search_child` in `src/search.cpp:1993–1998`. Both points where a successful null probe makes this node return call the same observer, at lines 2011 and 2026. A failed verification falls through without incrementing a cutoff. The observer copies the restored parent position and makes the null move on that private board. It generates legal moves and evaluates just the quiet checks. A move must have neither capture nor promotion flags. It must leave the defender in check with zero legal replies. The first such move ends the test, giving each cutoff at most one count. See lines 1760–1780.

Slots [2] and [5] each count all accepted cutoffs. Slots [3] and [4] partition that population by actual child depth ≤0 and then immediate quiet mate. Slots [6] and [7] use actual child depth 1–2 and the same mate test. For a second possible reading of [5], the `started_1_2` TSV column records all started probes with actual child depth 1–2, including failed probes. The runner reads that number from a private per-process sidecar. The NC0 line itself carries eight integers and follows bestmove. `src/uci.cpp:728–735` writes the two outputs under one lock. Each observation is an occurrence during a search. The 353 starting G positions are distinct by the first four FEN fields.

After checking out the job tree, the following example replays one suite with the counted executable in COUNT_EXE. G_EPD points to the original G.epd at kimi5 commit 5db05e09. Run the commands from job4/C with a new results directory.

```sh
mkdir -p new-rows
python3 run_nc.py "$COUNT_EXE" "$G_EPD" 12 0 new-rows/G_F0.tsv
python3 read_null_counts.py check new-rows/G_F0.tsv --reference ../A/G_floor0.tsv
```

Use the same runner with O.epd for O_F0, a one-line EPD for P at depth 16 for P_F0, and G.epd at depth 12 and floor 1 for G_F1. To recount the committed evidence, including floor-one parity against Part D:

```sh
python3 read_null_counts.py table rows ../A --d-dir ../D
```
