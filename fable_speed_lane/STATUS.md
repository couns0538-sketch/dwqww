# STATUS: fable2 bit-exact speed lane on combo29

Updated 2026-11-10 11:15 Vienna. Branch `fable52-speed-lane-20261109` (base `origin/main` `5176ddf7`). Read this file first when resuming. All times are Europe/Vienna.

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

## Step 3: candidates - DONE (first version 09:55; novelty of one corrected 10:20; patches revised after the review, final texts 11:09)

| Item | Novelty (DUPCHECK.md) | Patch md5 (final) | Lines | Files |
|---|---|---|---|---|
| `FORGE_SPD_WITNESS_NOPIN` | LISTED-UNBUILT | `ccfa6ce5be78591e8eef9f04527234dd` | +18 | `board.cpp` |
| `FORGE_SPD_EVADE_LEGAL` | LISTED-UNBUILT | `b5aaa89fe788edc2976376ca8760a7c4` | +32 | `board.cpp` |
| `FORGE_SPD_PAWN_CAPMASK` | UNLISTED | `2a680e14744580d058f5eb6f81a15202` | +16 | `board.cpp` |
| `FORGE_SPD_CHECKERS_KL` | LISTED-UNBUILT | `c8f080ba3d10df0989036e17805cc823` | +29 | `board.cpp` |
| `BUNDLE4` (the four above) | bundle of the new candidates | `4cfedef418f02fd7f916f6b0b2db080e` | +95 | `board.cpp` |
| `FORGE_SPD_KING_PAWN_CACHE` | **BUILT BEFORE - not new; extra** | `a51e1b69ebe53bb995e819dd77af7445` | +74 | `eval.hpp`, `eval.cpp` |
| `BUNDLE` (all five) | extra | `953ee65a4380d24b51f660982ffdbe04` | +169 | three files |

Results per item (switch-0 byte compare, pins, ladder, timing, exact work counters) are in `BENCH.md`, written from the evidence files by `tools/collect_evidence.py`. This file does not repeat them.

**Novelty correction, 10:20.** `KING_PAWN_CACHE` joined the pool after the profile, and I re-ran the duplicate search for it only at 10:15. That run found commit `928f1ff7` (2026-10-13, branch `cursor/chess-engine-elo-8295` only): the same shelter cache in the source of that date, "about 1% faster" by its message, never in the lock lineage. Ruling 1 of the plan says a candidate found built on the fetch is dropped, so it is **not counted as a new candidate**. It stays in the pack as a labelled extra with full evidence, because no combo29 version of it exists elsewhere; whether it is timed or used is the owner's and QA's call. The four new candidates have their own bundle, `BUNDLE4`.

**Revisions after the review** (`REVIEW_LOG.md`). The reviewer found no correctness defect in either round. Patches were still changed:

| Patch | md5 history | What changed and why |
|---|---|---|
| `CHECKERS_KL` | `1b785bd3` (09:35) -> `beca3d00` (10:48) -> `c8f080ba` (11:09) | King moves now keep the lock's `attackers_to()`. In the first text an illegal king step next to the enemy king read as "no check" where the lock counts the king as a checker; the engine never makes that move, but the shortcut carried a precondition. Now it equals the lock for every pseudo-legal move, and the harness checks that on illegal moves too. Last revision: the comment states exactly why the engine never meets a position with the side not to move in check, and two castling flags that the king test made redundant are gone |
| `PAWN_CAPMASK` | `09b2ef4f` -> `2a680e14` (10:48) | One hunk sat in the older generator that the lock never compiles, so it had never been built. Removed; the switch now refuses that configuration with `#error` |
| `KING_PAWN_CACHE` | `d2beac06` -> `a51e1b69` (10:48) | Comment only: the switch changes a struct layout and must reach every translation unit |

Every build of a changed source, every harness build and every result of a patched build from before the last change of that patch were moved to `out\_old_v1\` and `out\_old_v2\` and are not used. Old patch texts: those folders and git commits `8e2d7a8f` (first texts) and `eac89354` (10:48 texts).

History of the first limit, for the record: the first verify-mode harness run of `CHECKERS_KL` aborted because the harness's own legality oracle played illegal king moves on a board copy that carried king lines. On the first 300 FENs, 0 of 701,068 legal makes differed from `attackers_to` and 2,051 of 28,231 illegal makes did, every one a king move ending next to the enemy king (`out\_old_v1\id\CHECKERS_KL\rootcause\`). With the final text the harness plays all 729,299 generated moves of those 300 FENs, legal and illegal, on such copies and finds 0 differences (full set: `BENCH.md`).

Patches: `patches/<NAME>_after_combo29.patch` (`-p1`, `--- a/src/...`). The singles apply with plain `git apply` in the listed order and in reverse and give the same tree; each bundle patch is the diff of that tree (`tools/make_bundle.ps1`). `tools/check_consistency.ps1` re-proves at any time that snapshot + patch = work tree = the source of each build.

Build tags under `out\build\`: `wit`, `evd`, `cap`, `chk`, `kpc`, `bn4`, `bun`, each `_off` (switch 0), `_on` (switch 1) and, where a verify mode exists, `_v2` (the `=2` verify build; not a patch revision). Work trees: `out\work\<NAME>\{a,b}`.

## Step 4: qualification - RUNNING on CPU 3 (one process at a time), restarted 11:11 for the final patch texts

`tools/qualify_all.ps1 -Phases quick,timing,cold`; progress in `out\logs\chain.log`, finished steps in `out\logs\chain_done.txt` (a restart skips them), one result line per stage in `out\id\<NAME>\QUALIFY.log`.

| Phase | What | Estimate |
|---|---|---|
| quick | per item: lock-recipe builds, switch-0 byte compare, 12 pins, harness over 12,000 FENs and over 24 targeted positions (switch 1, and verify mode where it exists), verify engine on the 12 pins, warm transcript, Threads 2-4 soak, perft set; then consistency check and planted mutants (singles, `BUNDLE4`, eval mutants in `BUNDLE`) | until about 12:40 |
| timing | INDICATIVE A/B, lock exe vs switch-1 exe, bench 20, ABBA blocks (30 for the bundles with the net on, 10 otherwise), A/A first | about 1.7 h |
| cold | `go depth 13` over 12,000 FENs, net on and net off: lock, `BUNDLE4` and `BUNDLE` (each also with its verify engine), five singles | about 4.8 h |

Known from the set-aside runs of the earlier patch texts (history only, not evidence for the final texts): every stage of the quick ladder passed for all five singles and both bundles with the first texts, and again for `WITNESS_NOPIN`, `EVADE_LEGAL` and `PAWN_CAPMASK` with the 10:48 texts.

A/A timing, lock against itself (kept, it does not depend on a patch; 10 blocks, bench 20, net on): wall median +1.41 % (block range -5.59 .. +7.00), CPU cycles median +0.25 % (block range -1.99 .. +2.33). So on this CPU a single block is worth about +/-5 % by wall clock and +/-2 % by cycles: the singles cannot be resolved here. `BENCH.md` section 5 therefore also gives exact work counters per build, which do not depend on load.

Measured on CPU 3: 12,000 cold searches take about 19 min net on and 12 min net off per exe.

Chain restarts so far, all on purpose and without ending any process (the chain was left to finish through its own done-list): 09:58, a parameter named `$out` in `qualify.ps1` hid the global `$OUT` and the harness stages failed at once (fixed); 10:31, the chain script was extended by `BUNDLE4`; 10:44 and 11:07, stopped before timing because the two review rounds changed patches and the harness.

## Next

Read `out\logs\chain.log`. After the chain: `BENCH.md` (`tools/collect_evidence.py`), packs under `out\packs\` (`tools/make_packs.ps1`), `FILES.md` (`tools/make_files_md.py`), final STATUS.

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
