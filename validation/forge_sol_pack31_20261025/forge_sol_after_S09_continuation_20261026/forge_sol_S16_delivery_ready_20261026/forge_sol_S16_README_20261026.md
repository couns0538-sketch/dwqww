# Forge S16 overlap runner — 2026-10-26

This delivery finishes validation of the previously prepared v2 offline filter. Engine code, networks and trainers are unchanged. It is ready for ordered integration; this child task has not published it to GitHub.

Keep `forge_sol_datafilter_v2_20261026.py` and the unchanged dependency `forge_sol_datafilter_20261025.py` beside the runners. The dependency's SHA256 is verified before import; its existing record reader/writer is reused without duplication.

For owner-provided inputs, fill `forge_sol_S16_owner_config_example_20261026.json` and run:

```sh
sh forge_sol_S16_overlap_runner_20261026.sh owner_config.json
```

```powershell
pwsh -NoProfile -File forge_sol_S16_overlap_runner_20261026.ps1 -Config owner_config.json
```

Linux selects `python3` or `FORGE_PYTHON`; PowerShell accepts `-Python`. Paths in the config resolve relative to that file. The config must list Job D output, every sealed-shard directory, both exact 013/014 holdout filenames, matching HCE, a NEW output directory, an existing work directory, chronological text maps and owner-authoritative row-aligned game-ID maps with their provenance. No example value supplies a synthetic production default.

Production fails closed without authoritative IDs, including synchronized interleaved text that counters alone cannot identify. IDs must remain contiguous in chronological source order; a continued game may cross shard boundaries. Existing input shards are never edited, moved or overwritten. Only the run's new SQLite scratch is removed after success; failed scratch and an UNSEALED marker are retained.

The SQLite preflight begins at 300 bytes per row, with separate stem/ID/index/WAL/output/ledger reserves. The production CLI also checks available RAM. A removal JSONL identifies each excluded original row and reason. Whole-shard MD5 copies, duplicate positions and conflicting labels are accounted separately. New output files and the MD5 manifest are read-only after independent audits.

The import API defaults to diagnostic mode; the CLI requires explicit `--diagnostic-mode` to use it without production authority. Diagnostic output is not approved for training: `production_eligible`, `sealed_for_training` and `game_overlap_verified` remain false. Zero overlap with a supplied synthetic holdout does not prove zero overlap with real 013/014 or authentic games.

Run the supplied tests from this delivery directory:

```sh
FILTER_TEST_TOOL_PATH="$PWD/forge_sol_datafilter_v2_20261026.py" PYTHONDONTWRITEBYTECODE=1 \
  python3 -B -m unittest discover -s . -p '*tests*.py' -v
```

The actual Python3.12 run passed all 41 tests, including the original 21 unchanged tests. Full 200k SQLite/output runs passed OFF and twice at t300; every t300 output and its manifest was byte-identical across the two runs. See the dated report and evidence index. Python3.10 runtime, PowerShell/Windows runtime, real holdouts and owner production data remain UNVERIFIED. No training or playing-strength gain is claimed.
