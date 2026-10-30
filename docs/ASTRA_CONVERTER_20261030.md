# Astra FEN converter — checkpoint 2026-10-30

Branch `astra-fen-convert-20261030`, base `110f0c4a819756b79a77d88a5ef525b6dafd925b`. Engine and live trainer untouched.

Implemented original 32-byte bulletformat encoder, mandatory exact-FEN/STM-score/White-result sidecar, immutable sealed chunks, hash-checked resume, source alignment through the existing A1 reader, separate `holdout-dedup` command, explicit game-ID exclusion, native Forge root filters and first-drop counts. Native bulletformat cannot preserve original STM, castling, EP or clocks by itself; the sidecar is an inseparable part of the lossless artifact. Score remains Forge STM centipawns internally; native bullet record result is STM-relative.

Initial16 unit regressions PASS (raw log under `validation/astra-converter-20261030`). Actual1M roundtrip, native pilot, independent bullet loader, binpack and final review are pending; no training, parity or speed claim.

## Restart contract

Each chunk gets new files plus an atomic, exclusive receipt. Resume verifies original input hashes, parameters, tool hashes and every sealed chunk. It reconstructs deduplication state from sealed output and ignores retained unsealed attempt directories. It does not edit or delete sources/old attempts. `COMPLETE.json` appears only after successful native shutdown and unchanged source hashes. Filesystem must support same-volume hardlinks.

## Commands

```bash
python3 tools/data2/convert_dataset.py convert --input /path/003.txt --pos /path/003.pos --out /new/run --probe /path/forge_data_probe --nodes 1024
python3 tools/data2/convert_dataset.py verify --out /new/run
python3 tools/data2/convert_dataset.py holdout-dedup --input /path/filtered.txt --holdout /private/013.pos --holdout /private/014.pos --out /new/holdout-removed
```

Use `--game-ids` and one `--holdout-game-ids` perholdout plus `--require-game-clearance` when authentic IDs exist. No game IDs means `UNVERIFIED_NO_AUTHENTICATED_GAME_IDS`; FENs do not establish game identity. Missing private013/014 cannot be replaced by a claim of zero full-holdout leakage. FullQA already found281 retained A1 positions overlapping them.

For format qualification only, `--no-filters --no-dedupe --limit 1000000` explicitly bypasses filtering to compare the exact first1M original rows. Production defaults require the native probe. Never append filtered003 onto the existing training set: replace003 in an isolated ablation.

## Sources and licensing

IDEA_SOURCE: user crew contract20261030; same-project A1 format/probe; MIT `jw1912/bulletformat` ChessBoard layout at `eddd9a2d77dbc1391d68f23ba524657e91bd9a73`. New implementation is original. No GPL or AGPL code incorporated. nnue-pytorch overall is GPL but its five binpack dependency headers have their own explicit MIT notices; license closure and external adapter are being checked separately before use.

QA correction: `ASTRA_A1_WINDOWS.md` now separates actual POS and TXT directories, requires one explicitly spare logicalCPU, defaults oneworker, and warns not to rerun sealed10M. Windows execution remains UNVERIFIED.
