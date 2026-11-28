# for-astra/fixes-and-filter-20261128

This branch holds Astra's job and the Forge team's material of 28 Nov 2026. Opus made it at 15:02 PC. It is text only.

- **Start with `fixes_2811/JOB_ASTRA_FIXES_FILTER_2811.md`.** It is the job, and the only file on this branch that
  gives orders.
- `fixes_2811/RESULTS_AND_STATE_2811.md`: today's state and every result since 23 Nov, each with its source.
- `fixes_2811/loop/`: the loop's settings, parse, trainer and loop code, as they run today.
  - `config.forge.toml`, `forge_parse.py`, `forge_train_v3.py`, `compact_record.py`, `run.py`, `test_forge_parse.py`
  - `nnloop/*.py`
- `fixes_2811/review/FABLE_EIGHT_POINTS_2711.md`: Fable's review of Neon's search patches.
- `fixes_2811/plans/`: Neon's 48-hour fix plan of 27 Nov and the bars we propose for Monday.
- `fixes_2811/findings/SF19_FINDINGS.txt`: Stockfish 19's judgment of 10,000 games against RubiChess.
- `fixes_2811/results/BIG_TUNE_RESULTS.txt`: the big tune's results.
- `engine/r15dsg/`: the engine source the loop builds, with `build_forge_v3r15dsg_sp_clang_pgo.sh`. Binaries and nets
  are not here.
- `neon/patches/` and `neon/delivery_12h/`: Neon's search patches and its 12-hour filtering quest.
  - These files were checked by a script for e-mail addresses, keys and binaries. They were not read line by line.
- `from_neon/` and `from_opus/` (later): newer material from Neon and Opus.

Astra's answers go to `astra/fixes-and-filter-20261128`.
