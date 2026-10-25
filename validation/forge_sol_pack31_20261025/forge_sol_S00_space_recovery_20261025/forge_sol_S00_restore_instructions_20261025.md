# Reversible cache retention, 20261025

61 CLOSED ASan compiler/support files and one unused-library category within that count were archived with Python gzip and independently decoded by GNU gzip before replacement. Sources, data, raw evidence and main engine ELFs remain. The 61 exact entries and original byte hashes are in the restore map. The library libtorch_cpu.so is entry60; that private training environment is currently NOT import-ready until it is restored. No GPU run was touched.

Payload archives remain local under this directory; Git stores the map, commands and retention proof. Compiler products can be rebuilt from retained source/flags if an environment is replaced. No claim that Git contains these cache payloads.

Restore one entry into a NEW directory with enough disk space:

```sh
python -B forge_sol_S00_closed_cache_restore_20261025.py --map forge_sol_S00_closed_cache_restore_map_20261025.json --restore-dir NEW_DIRECTORY --only-index ENTRY_INDEX
```

The helper verifies archive SHA and decoded bytes/mode/times. Original group metadata was not recorded, so no group-identity claim is made. To reinstate a missing cache file after this check, link the restored file to its exact map path using os.link(restored, original); it refuses an existing destination. Do not overwrite an existing file. The archive map and journal retain every transition.
