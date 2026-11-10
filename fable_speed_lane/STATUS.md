# STATUS: fable2 bit-exact speed lane on combo29

Updated 2026-11-10 10:35 Vienna. Branch `fable52-speed-lane-20261109` (base `origin/main` `5176ddf7`). Read this file first when resuming. All times are Europe/Vienna.

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

`tools/env.ps1`, `pin.ps1`, `pinguard.py`, `spd_build.ps1`, `bytecmp.py`, `spd_uci.py` (pins, cold, merge, warm, soak, perftset, abba), `tree_index.py`, `fetch_corpus.py`, `dupcheck_search.py`, `spd_rip_sampler.py`, `spd_prof_query.py`, `spd_counters.py`, `cand_step.ps1`, `make_bundle.ps1`, `check_consistency.ps1`, `qualify.ps1`, `qualify_all.ps1`. Harness: `tests/prim_dump.cpp`, `tests/build_prim.ps1`.

## Step 2: profile - DONE (09:00)

`PROFILE.md`. Largest CPU-bound target: the king shelter loop in `evaluate_king` (4.1 % net on, 4.8 % net off). `HCE_REUSE` dropped (0.12 % on its lines).

## Step 3: candidates - DONE (patches written 09:55; novelty of one of them corrected 10:20)

| Item | Novelty (DUPCHECK.md) | Patch md5 | Lines | Files | Switch 0 vs lock (debug / other bytes) | Switch 1 pins |
|---|---|---|---|---|---|---|
| `FORGE_SPD_WITNESS_NOPIN` | LISTED-UNBUILT | `ccfa6ce5be78591e8eef9f04527234dd` | +18 | `board.cpp` | 89 / 0 | 12/12 |
| `FORGE_SPD_EVADE_LEGAL` | LISTED-UNBUILT | `b5aaa89fe788edc2976376ca8760a7c4` | +32 | `board.cpp` | 89 / 0 | 12/12 |
| `FORGE_SPD_PAWN_CAPMASK` | UNLISTED | `09b2ef4ff716707675258e29b1a6adeb` | +16 | `board.cpp` | 89 / 0 | 12/12 |
| `FORGE_SPD_CHECKERS_KL` | LISTED-UNBUILT | `1b785bd3cfe7ef705f678dadc9138aef` | +24 | `board.cpp` | 89 / 0 | 12/12 |
| `BUNDLE4` (the four above) | bundle of the new candidates | `8f74ea2c6b7a04252bbd2699cf763909` | +90 | `board.cpp` | step 4 | step 4 |
| `FORGE_SPD_KING_PAWN_CACHE` | **BUILT BEFORE - not new; extra** | `d2beac0624bcb041c1779eae92d37368` | +73 | `eval.hpp`, `eval.cpp` | 89 / 0 | 12/12 |
| `BUNDLE` (all five) | extra | `21d6e2c78db2657a1c2769a8d1d2b139` | +163 | three files | 89 / 0 | 12/12 |

**Novelty correction, 10:20.** `KING_PAWN_CACHE` joined the pool after the profile, and I re-ran the duplicate search for it only at 10:15. That run found commit `928f1ff7` (2026-10-13, branch `cursor/chess-engine-elo-8295` only): the same shelter cache in the source of that date, "about 1% faster" by its message, never in the lock lineage. Ruling 1 of the plan says a candidate found built on the fetch is dropped, so it is **not counted as a new candidate**. It stays in the pack as a labelled extra with full evidence, because no combo29 version of it exists elsewhere; whether it is timed or used is the owner's and QA's call. The four new candidates have their own bundle, `BUNDLE4`.

Patches: `patches/<NAME>_after_combo29.patch` (`-p1`, `--- a/src/...`). The singles apply with plain `git apply` in the listed order and in reverse and give the same tree; each bundle patch is the diff of that tree (`tools/make_bundle.ps1`). `tools/check_consistency.ps1` re-proves at any time that snapshot + patch = work tree = the source of each build.

Mutants (`tests/mutants.ps1`, log `out\id\mutants\MUTANTS.log`): eight planted wrong versions, one or more per candidate. Seven are caught as required; the eighth (`WITNESS_NOPIN` without its line test, plain build) cannot change the boolean in practice and is caught by the verify build instead. One mutant (`WITNESS_NOPIN` accepted while in check) shows only at a checkmate: the first 300 FENs miss it, the full 12,000 catch it (3 failures).

Build tags under `out\build\`: `wit`, `evd`, `cap`, `chk`, `kpc`, `bn4`, `bun`, each `_off` (switch 0), `_on` (switch 1) and, where a verify mode exists, `_v2`. Work trees: `out\work\<NAME>\{a,b}`.

### CHECKERS_KL: where it is exact, and the abort that showed the limit

The first verify-mode harness run of `CHECKERS_KL` aborted. Cause, found by instrumenting the harness (`out\id\CHECKERS_KL\rootcause\`): the harness's own legality oracle played **illegal** king moves on a board copy that carried king lines. After a king steps next to the enemy king, `attackers_to` counts the mover's king as a checker; the shortcut, like the lock's `gives_check`, says no check.

| Run (first 300 FENs, 729,299 makes on copies with king lines) | Legal makes that differ | Illegal makes that differ |
|---|---|---|
| lock source | 0 of 701,068 | 0 of 28,231 |
| `CHECKERS_KL=1` | 0 of 701,068 | 2,051, every one a king move ending next to the enemy king |

The engine never makes such a move: every `make_move` call follows `is_legal` (`search.cpp` three sites, `perft`) or takes its move from `legal_moves()` (`uci.cpp` position parsing and `go perft`, `book.cpp` decoding); `set_fen` rejects a position whose side not to move is in check; the null move is made only when not in check. So the shortcut's domain - a legal move from a position where the side not to move is not in check - is every make the engine performs. The harness oracle now plays its moves on a copy without king lines, and a measuring build (`PRIM_MAKE_ANY=1`) keeps the count above reproducible.

## Step 4: qualification - RUNNING on CPU 3 (one process at a time)

`tools/qualify_all.ps1 -Phases quick,timing,cold`; progress in `out\logs\chain.log`, finished steps in `out\logs\chain_done.txt` (a restart skips them), one result line per stage in `out\id\<NAME>\QUALIFY.log`.

| Phase | What | State at 10:35 |
|---|---|---|
| quick | harness over all 12,000 FENs (switch 1, and verify mode where it exists), verify engine on the 12 pins, warm transcript, Threads 2-4 soak, perft set; bundles also: lock-recipe builds, switch-0 byte compare, 12 pins | **PASS, every stage**, for the five singles and `BUNDLE` (10:31); `BUNDLE4` running |
| timing | INDICATIVE A/B, lock exe vs switch-1 exe, bench 20, 10 ABBA blocks, net on then net off, A/A first | not started; about 2 h |
| cold | `go depth 13` over 12,000 FENs, net on and net off: lock, `BUNDLE4` and `BUNDLE` (each also with its verify engine), five singles | not started; about 5 h |

Measured on CPU 3: 12,000 cold searches take about 19 min net on and 12 min net off per exe.

Chain restarts so far, both on purpose and without ending any process (the chain was left to finish through its own done-list): 09:58, a parameter named `$out` in `qualify.ps1` hid the global `$OUT` and the harness stages failed at once (fixed); 10:31, the chain script was extended by `BUNDLE4`.

## Next

Read `out\logs\chain.log`. While the chain runs: the one read-only review of the patches (started 10:12, `REVIEW_LOG.md` when it returns), handoff documents. Then `BENCH.md` from the chain's evidence (`tools/collect_evidence.py`), packs under `out\packs\` (`tools/make_packs.ps1`), `FILES.md`, final STATUS.

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
