# Astra FEN converter — checkpoint 2026-10-30

Branch `astra-fen-convert-20261030`, base `110f0c4a819756b79a77d88a5ef525b6dafd925b`. Engine and live trainer untouched.

Implemented original 32-byte bulletformat encoder, mandatory exact-FEN/STM-score/White-result sidecar, immutable sealed chunks, hash-checked resume, source alignment through the existing A1 reader, separate `holdout-dedup` command, explicit game-ID exclusion, native Forge root filters and first-drop counts. Native bulletformat cannot preserve original STM, castling, EP or clocks by itself; the sidecar is an inseparable part of the lossless artifact. Score remains Forge STM centipawns internally; native bullet record result is STM-relative.

Verified so far:35 unit regressions PASS;13 native binpack ASan/UBSan/leak tests PASS; all1,000,000 raw003 rows roundtrip exactly through bullet32+sidecar and native binpack; official MIT bulletformat loader reads all1M with0mismatches. Native1024-row filteredpilot keeps977 (46capture,1disagreement dropped), and bothoutputs verify. Fakeholdout contains the same1000real sample rows: all1000removed,0remain. Final review inprogress; no training/parity/Elo claim.

## Restart contract

Each chunk gets new files plus an atomic, exclusive receipt. Resume verifies original input hashes, parameters, tool hashes and every sealed chunk. It reconstructs deduplication state from sealed output and ignores retained unsealed attempt directories. It does not edit or delete sources/old attempts. `COMPLETE.json` appears only after successful native shutdown and unchanged source hashes. Filesystem must support same-volume hardlinks.

## Commands

```bash
python3 tools/data2/convert_dataset.py convert --input /path/003.txt --pos /path/003.pos --out /new/run --probe /path/forge_data_probe --nodes 1024 --shard-id 003
python3 tools/data2/convert_dataset.py verify --out /new/run
python3 tools/data2/convert_dataset.py holdout-dedup --input /path/filtered.txt --holdout /private/013.pos --holdout /private/014.pos --out /new/holdout-removed
```

User clarification accepts whole-shard013/014 exclusion as the game-level split policy because rows are unordered and gameIDs unavailable. Production requires explicit `--shard-id 003` (separate flag/value), rejects013/014, and reports the accepted shardpolicy. Do not invent gameIDs. Optional authenticated `--game-ids` and one `--holdout-game-ids` perholdout perform stronger explicit exclusion when available. Missing private013/014 cannot be replaced by a claim of zero full-holdout leakage. FullQA already found281 retained A1 positions overlapping them.

For format qualification only, `--no-filters --no-dedupe --limit 1000000` explicitly bypasses filtering to compare the exact first1M original rows. Production defaults require the native probe. Never append filtered003 onto the existing training set: replace003 in an isolated ablation.

## Sources and licensing

IDEA_SOURCE: user crew contract20261030; same-project A1 format/probe; MIT `jw1912/bulletformat` ChessBoard layout at `eddd9a2d77dbc1391d68f23ba524657e91bd9a73`. New implementation is original. No GPL or AGPL code incorporated. nnue-pytorch overall is GPL but its five binpack dependency headers have their own explicit MIT notices. Exact closedMITdependency verified and externally fetched via the pinnedmanifest; originaladapter built and tested without anyGPLpart. See ASTRA_BINPACK_ADAPTER_20261030.md.

QA correction: `ASTRA_A1_WINDOWS.md` now separates actual POS and TXT directories, requires one explicitly spare logicalCPU, defaults oneworker, and warns not to rerun sealed10M. Windows execution remains UNVERIFIED.

## Recorded1M format results

All1M raw rows retained for format qualification only. Nativebinpack34,000,264bytes SHA256`db200a129194456ffbdc101e2154a5d5fd920c175fea12b69e878c38a28c9396`. Original/decodedtextSHA256`f8fb8e78cfc643bbc3a79f0384aafc848bb679e01a9e5b71ca97fd91966766be`;216,652castlingrows and35,547EProws preserved. Bulletofficialloader commit`eddd9a2d77dbc1391d68f23ba524657e91bd9a73`; all1M match its independent parser after explicitSTM→White inputscore conversion. Binpack1M uses explicitly labelled legaltransportmove fallback, never teacher-move filtering. Productionpasses actualForgeprobe quietbestmoves tobinpack. Originalevidence under validation/astra-converter-20261030.

Knownlimits: noGPUbullettraining or1epoch/export/parity run; privatefull013/014 absent (PCdedupcommand provided); Windowsnative executionUNVERIFIED. Currentbinpack decoder accepts own independent-recordchunks only. Finalreview found COMPLETEcount/chunkmetadata could escapeverification; repaired with4newregressions and35totaltestsPASS.
