# STATUS: fable2 bit-exact speed lane on combo29

Updated 2026-11-10 08:50 Vienna. Branch `fable52-speed-lane-20261109` (base `origin/main` `5176ddf7`). Read this file first when resuming. All times are Europe/Vienna.

## Approval state

Plan approved by Couns 2026-11-10 08:08. Budget about 20 h from then. Rulings accepted with the plan: listed-but-unbuilt ideas may be built if labelled; switch-0 builds are judged by byte ranges; lock reproduction may be marked BLOCKED if only debug-record bytes differ; no engine source or net is committed to this branch.

## Paths

| What | Path |
|---|---|
| Job root | `D:\forge_jobs_20261109\fable2` |
| Clone (blob-less, sparse) | `D:\forge_jobs_20261109\fable2\repo` |
| Pack | `repo\fable_speed_lane\` |
| Builds and evidence | `D:\forge_jobs_20261109\fable2\out\` (`base`, `build`, `id`, `prof`, `packs`, `corpus`, `index`, `logs`, `tmp`) |
| Lock exe copy | `out\base\combo29_lock_E1284F7F.exe` |
| combo29 source snapshot | `out\base\combo29_src\` (20 files, read-only) |
| Control rebuild | `out\build\c29ctl\m2use\forge_m2use.exe` |
| FEN set | `out\base\fens_12k_v2.txt` (12,000 FENs, md5 `e7dbf2c8151188c03ef52054557a531e`) |

## Step 1: inventory and freeze - DONE

| Check | Result |
|---|---|
| Lock exe | md5 `c0051c99695f48bf93272d96fe7548c3`, sha256 `e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e`, 2,092,544 B; live exe in `forge_push\bin` has the same sha256; `CURRENT_LOCK.json` sha256 `50af2ef3...`, `speed_lock = combo29` |
| Source | 20/20 files equal `SOURCE_INPUTS.sha256`; manifest sha256 `3389cfe3dc7bb3989cfebfbdc8ac13d3785b71f090257664d04a0d7c74137645` = `RUN_RECEIPT.source_manifest_sha256` of the lock |
| Recipe | `tools/spd_build.ps1`: the lock's `build.log` command lines, compiler sha256 `d05fee2c...`, workload sha256 `1d52720a...` |
| Control rebuild | sha256 `c1b483f48b863114aa6c3cc0715fc93bfaceb246726b1dd1f0cfcb4b8d979445`, md5 `6571f40308eccb2baa02da83be19c687`, 2,092,544 B |
| Control vs lock, bytes | 89 differing bytes, all in the debug record: `0x1D8` (`.buildid` virtual size), `0x1AE610` (debug directory size), `0x1AE620-627` (PDB hash), `0x1AE637-686` (PDB path). 0 other bytes differ. `out\id\c29ctl\bytecmp_lock_vs_c29ctl.json` |
| Pins, lock copy | 12/12 match (`out\id\lock\pins.json`) |
| Pins, control | 12/12 match (`out\id\c29ctl\pins.json`) |
| AGENTS.md | recovered from `3e900941`: 4,018 B, md5 `94169aefef79ccb69c21f8f2c86298f0` (equals the historical md5); copy in `out\base\AGENTS_3e900941.md` |
| Duplicate check | `DUPCHECK.md`, `data/dupcheck_hits.tsv` |

### BLOCKED items (no parent guessed)

1. **Source commit: none.** On the fresh fetch (389 branches, 08:11) no branch holds the lock's `search.cpp`, `board.cpp`, `search.hpp`, `board.hpp`, `bitboard.hpp` or `nnue.hpp` (looked up by git blob id in `out\index\tree_index.tsv`). The source of record is QA's lock pack `D:\forge-qa\pack_combo29_20261108\pc_payload\source_snapshot`, pinned by the manifest hash above. Patches are `after_combo29` against that snapshot.
2. **Byte-for-byte reproduction of the lock exe: BLOCKED by construction.** The exe carries an 8-byte hash of its PDB. The lock's PDB contains the linker's literal command line (`-out:` and `-pdb:` inside `D:\grok_sdk_speed_20261107\detached1735_all31\clang\all31_m29\m2use\`), its working directory and every source path. Equal bytes would need a build that writes into that folder, which is not mine. Every code and data byte does reproduce (table above). The lock note says the same: "binary not byte-reproducible (embedded PDB paths)".

## CPU lane: what it really is today

`CORE_OVERRIDE.json` moves gates to 0x0F87, but its own note says the running queue keeps the old mask until it restarts. The live gate (fastchess PID 14060, started 06:45) runs eight games on CPUs 4-11 above Idle priority.

| CPU | Measured for an Idle-priority engine (lock exe, bench 16) |
|---|---|
| 3 | 1.93 M nps (free) |
| 4 | about 0.09 M nps (4 % of a core) |
| 6 | 0.015 M nps (under 1 %) |

So heavy runs use **CPU 3 only** (mask 0x08), one at a time. Nothing of the gate was touched. For an owner: CPUs 4-6 of the Fable lane are not free until the queue restarts with the new mask.

## Tools written (all pinned, all write under `out\`)

`tools/env.ps1`, `pin.ps1`, `pinguard.py`, `spd_build.ps1`, `bytecmp.py`, `spd_uci.py` (pins, cold, merge, warm, soak, perftset, abba), `tree_index.py`, `fetch_corpus.py`, `dupcheck_search.py`.

## Step 2: profile - DONE (09:00)

`PROFILE.md`. Largest CPU-bound target: the king shelter loop in `evaluate_king` (4.1 % net on, 4.8 % net off). `HCE_REUSE` dropped (0.12 % on its lines).

## Step 3: candidates (state at 09:22)

Quick gate per candidate = harness RED on a planted mutant, harness GREEN on the patch (first 300 FENs so far), switch-0 lock-recipe build compared byte by byte with the lock, switch-1 build on the 12 pins. Full qualification (12k cold, warm, soak, perft set, A/B) is step 4 and is NOT done yet.

| Candidate | Patch (md5) | Files | Mutant caught | Switch 0 vs lock | Switch 1 pins | Harness, 300 FENs |
|---|---|---|---|---|---|---|
| `FORGE_SPD_KING_PAWN_CACHE` | `d2beac06...` (+73 lines) | `eval.hpp`, `eval.cpp` | yes, 16,438 failures | 89 debug-record bytes, 0 other | 12/12 | equal to base |
| `FORGE_SPD_WITNESS_NOPIN` | `ccfa6ce5...` (+18) | `board.cpp` | yes, in verify mode (abort); the plain boolean cannot see it | 89 / 0 | 12/12 | equal to base |
| `FORGE_SPD_EVADE_LEGAL` | `b5aaa89f...` (+32) | `board.cpp` | yes, transcript differs and verify mode aborts | 89 / 0 | 12/12 | equal to base |
| `FORGE_SPD_PAWN_CAPMASK` | not written yet | | | | | |
| `FORGE_SPD_CHECKERS_KL` | not written yet | | | | | |

Build tags under `out\build\`: `kpc_off/on`, `wit_off/on`, `evd_off/on`. Work trees: `out\work\<NAME>\{a,b}`.

First A/B look at `KING_PAWN_CACHE` (8 blocks, bench 16, CPU 3): too noisy to read (block ratios from -29 % to +18 %). Timing is redone in step 4 with bench 20 and cycle counts.

## Next

Write `PAWN_CAPMASK` and `CHECKERS_KL` (mutant first), then step 4.

## Resume commands

```powershell
. D:\forge_jobs_20261109\fable2\repo\fable_speed_lane\tools\env.ps1
git -C $REPO status --short; git -C $REPO log --oneline -8
# build a tree with the lock recipe (refuses to overwrite)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T\spd_build.ps1 -Tag <new> -Src <tree> [-ExtraDefs FORGE_SPD_X=1] -Mask 0x08
# pins of one exe on CPU 3
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $PIN -Exe $PY -Mask 0x08 -ArgLine "-I -B $T\spd_uci.py pins --exe <exe> --out <json>"
# byte ranges of a switch-0 build against the lock
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $PIN -Exe $PY -Mask 0x08 -ArgLine "-I -B $T\bytecmp.py $OUT\base\combo29_lock_E1284F7F.exe <exe>"
```

## Rulings taken during the work

- **Training step.** `Start-Process -RedirectStandardInput` gave the instrumented engine an empty stdin under this session's console-less host (0 bench lines). The build script now feeds the workload through `cmd.exe` redirection, byte for byte. The resulting control equals the lock in every code and data byte, so the recipe is unchanged in effect.
- **Strict-SHA attempt.** Stopped after reading the lock's PDB strings (about 5 minutes of the 45 allowed): the blocker is structural, see above.
- **No kills.** Tools never kill an engine: quit, close stdin, wait, report a survivor.
- **Plan timestamp.** The plan file says "drafted 08:30"; the clock read about 08:05 when it was written.
