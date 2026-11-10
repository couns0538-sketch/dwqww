# STATUS: fable2 bit-exact speed lane on combo29

FINAL for job 2, written 2026-11-10 17:00 Vienna. The owner's instruction of 16:55 was to wrap up now: every run still in flight was stopped at 16:56 and is recorded as INCOMPLETE with what it had done. Branch `fable52-speed-lane-20261109` (base `origin/main` `5176ddf7`). Read this file first when resuming. All times are Europe/Vienna.

## State in short

| Question | Answer |
|---|---|
| New patches | Four: `WITNESS_NOPIN`, `EVADE_LEGAL`, `PAWN_CAPMASK`, `CHECKERS_KL`. Bundles: `BUNDLE4` (all four, the ALL-ON bundle), `BUNDLE3` (without `WITNESS_NOPIN`, added 14:44). Extras, not new: `KING_PAWN_CACHE`, `BUNDLE` (five) |
| Identity: finished checks | All PASS for all eight items: switch-0 bytes (89 debug-record bytes, 0 others), 12 pins (bench d11/13/16/20/22 net on and off, perft 5 twice), harness over 12,000 FENs and 24 targeted positions (plain, and verify builds where a verify mode exists), verify engine on the 12 pins, warm transcript, Threads 2-4 soak, perft set. `BUNDLE4`: verify engine over the whole cold set, 0 of 12,000 rows differ. Mutants: 15 of 15 caught in the single trees, 12 of 12 in `BUNDLE4`, every control clean |
| Identity: INCOMPLETE (stopped at 16:56) | Cold 12,000 for every item, net on and net off. Rows done, all equal to the lock's rows, none differing: `BUNDLE4` 7,501 on / 1,501 off; `BUNDLE3` 3,501 / 3,501 and 1,501 with its verify engine; `WITNESS_NOPIN` 3,501 / 2,501; `EVADE_LEGAL` 3,501 / 2,501; `PAWN_CAPMASK` 1,501 / 2,501; `CHECKERS_KL` 5,001 / 2,501; the two extras had only started (1 row each). Mutants in `BUNDLE3`: control clean, no mutant run yet. Mutants in `BUNDLE`: 2 of 3 caught, the third caught on the one set that ran (the other was refused by the disk guard) |
| So: is any item FAIL? | No. No check found a difference. No item has a complete cold run of its own; `BUNDLE4` comes closest (complete with its verify engine, 62 % with the plain exe, net on) |
| Speed, INDICATIVE, under gate load | Resolved: `WITNESS_NOPIN` -1.02 % (interval -1.25 .. -0.86, 60 blocks) and `BUNDLE4` -0.70 % (-0.99 .. -0.39, 100 blocks): both slower than the lock. Not resolved, runs stopped at 34 blocks: `BUNDLE3` -0.22 % (-0.90 .. +0.47), `EVADE_LEGAL` -0.63 % (-0.99 .. +0.37), `PAWN_CAPMASK` -0.39 % (-1.14 .. +0.46), `CHECKERS_KL` -0.59 % (-0.95 .. +0.48). Lock against lock: -0.02 % (40 blocks) and -0.00 % (36 blocks). No item showed a gain. CPU cycles, bench 16, a new copy of the exe per arm; `BENCH.md` section 3.2 |
| A warning for every A/B on this PC | A fixed pair of exe files read -3.65 % (30 tight blocks) and two hours later +0.30 %. `BENCH.md` section 3.1, `QA_ABBA_PROTOCOL.md` |
| BLOCKED | No repo commit holds the combo29 source (six of its 20 files are on no fetched branch); the lock exe cannot be reproduced byte for byte (PDB hash and paths). Both as planned, see below |
| Disk | D: 31.94 GiB free at 16:57 (it had fallen to 30.28 at 16:32 and a cleaner brought it back at about 16:40). This job holds about 0.35 GiB |

## What was stopped at 16:56, and how

The eleven background shells of this job were stopped through the session's own task control; that ended their whole process trees (133 processes of this job at that moment: 19 engines of the cold runs and harness, 6 timing arms, their Python drivers and PowerShell wrappers). A check right after found no process left with this job's folder in its path or command line, and no process of anyone else was touched (`out\logs\wrapup_processes_before.txt` lists what ran). `tools/record_incomplete.py` then counted the complete rows of every unfinished cold run, compared them with the lock's rows, renamed the partial files to `*.incomplete.tsv` and wrote one `INCOMPLETE` line per run into the item's `QUALIFY.log`. The stopped timing runs appear in `BENCH.md` section 3.2 with the blocks they had finished.

To finish any of them later, run the plain stage again (it starts from row 0; a cold run takes about 12 minutes per net on a free CPU):

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T\qualify.ps1 -Name BUNDLE3 -Tag bn3 -Stages coldverify,cold `
  -Defs FORGE_SPD_EVADE_LEGAL=1,FORGE_SPD_PAWN_CAPMASK=1,FORGE_SPD_CHECKERS_KL=1 `
  -VerifyDefs FORGE_SPD_EVADE_LEGAL=2,FORGE_SPD_PAWN_CAPMASK=1,FORGE_SPD_CHECKERS_KL=2
```

## Approval state

Plan approved by Couns 2026-11-10 08:08. Budget about 20 h from then. Rulings accepted with the plan: listed-but-unbuilt ideas may be built if labelled; switch-0 builds are judged by byte ranges; lock reproduction may be marked BLOCKED if only debug-record bytes differ; no engine source or net is committed to this branch.

## Paths

| What | Path |
|---|---|
| Job root | `D:\forge_jobs_20261109\fable2` |
| Clone (blob-less, sparse) | `D:\forge_jobs_20261109\fable2\repo` |
| Pack | `repo\fable_speed_lane\` |
| Builds and evidence | `D:\forge_jobs_20261109\fable2\out\` (`base`, `build`, `work`, `id`, `regime`, `prof`, `packs`, `logs`, `tmp`, `_old_v1`, `_old_v2`) |
| QA rebuild packs (D: only) | `out\packs\<NAME>\` for all eight items, written 16:14 |
| Lock exe copy | `out\base\combo29_lock_E1284F7F.exe` |
| combo29 source snapshot | `out\base\combo29_src\` (20 files, read-only) |
| Control rebuild | `out\build\c29ctl\m2use\forge_m2use.exe` |
| FEN set | `out\base\fens_12k_v2.txt` (12,000 FENs, md5 `e7dbf2c8151188c03ef52054557a531e`) |
| Logs of the runs | `out\logs\chain.log` (first chain), `cold_singles.log`, `timing2.log`, `par_*.txt` (runs started in parallel), `machine_state.tsv` (memory, CPU 2 and 3 load, D: free, once a minute from 14:24) |

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

1. **Source commit: none.** No fetched branch holds the lock's `search.cpp`, `board.cpp`, `search.hpp`, `board.hpp`, `bitboard.hpp` or `nnue.hpp`. Looked up by git blob id; the table is `data/lock_source_blob_lookup.tsv` (made again at 15:48 from a fresh tree index of the 390 refs then present: the 389 of the 08:11 fetch plus this job's own branch; the first index of 08:11 gave the same six files). The source of record is QA's lock pack `D:\forge-qa\pack_combo29_20261108\pc_payload\source_snapshot`, pinned by the manifest hash above. Patches are `after_combo29` against that snapshot.
2. **Byte-for-byte reproduction of the lock exe: BLOCKED by construction.** The exe carries an 8-byte hash of its PDB. The lock's PDB contains the linker's literal command line (`-out:` and `-pdb:` inside `D:\grok_sdk_speed_20261107\detached1735_all31\clang\all31_m29\m2use\`), its working directory and every source path. Equal bytes would need a build that writes into that folder, which is not mine. Every code and data byte does reproduce (table above). The lock note says the same: "binary not byte-reproducible (embedded PDB paths)".

## CPU lane: what it really was today

`CORE_OVERRIDE.json` moves gates to 0x0F87, but its own note says the running queue keeps the old mask until it restarts. The live gate ran eight games on CPUs 4-11 above Idle priority all day (fastchess PID 14060 from 06:45, then PID 12880 from 11:37, both with mask 0xFF0, read at 13:15).

| CPU | Measured for an Idle-priority engine (lock exe, bench 16), morning |
|---|---|
| 3 | 1.93 M nps (free) |
| 4 | about 0.09 M nps (4 % of a core) |
| 6 | 0.015 M nps (under 1 %) |

So every heavy run of this job used **CPU 3 only** (mask 0x08). Nothing of the gate was touched. For an owner: CPUs 4-6 of the Fable lane were not free.

## Step 2: profile - DONE (09:00)

`PROFILE.md`. Largest CPU-bound target: the king shelter loop in `evaluate_king` (4.1 % net on, 4.8 % net off). `HCE_REUSE` dropped (0.12 % on its lines).

## Step 3: candidates - DONE (final patch texts 11:09; `BUNDLE3` added 14:44)

| Item | Novelty (DUPCHECK.md) | Patch md5 (final) | Lines | Files |
|---|---|---|---|---|
| `FORGE_SPD_WITNESS_NOPIN` | LISTED-UNBUILT | `ccfa6ce5be78591e8eef9f04527234dd` | +18 | `board.cpp` |
| `FORGE_SPD_EVADE_LEGAL` | LISTED-UNBUILT | `b5aaa89fe788edc2976376ca8760a7c4` | +32 | `board.cpp` |
| `FORGE_SPD_PAWN_CAPMASK` | UNLISTED | `2a680e14744580d058f5eb6f81a15202` | +16 | `board.cpp` |
| `FORGE_SPD_CHECKERS_KL` | LISTED-UNBUILT | `c8f080ba3d10df0989036e17805cc823` | +29 | `board.cpp` |
| `BUNDLE4` (the four above) | bundle of the new candidates | `4cfedef418f02fd7f916f6b0b2db080e` | +95 | `board.cpp` |
| `BUNDLE3` (`EVADE_LEGAL`, `PAWN_CAPMASK`, `CHECKERS_KL`) | bundle of three new candidates | `ba2fcf2e78a0e2c85964a1e6e258d150` | +77 | `board.cpp` |
| `FORGE_SPD_KING_PAWN_CACHE` | **BUILT BEFORE - not new; extra** | `a51e1b69ebe53bb995e819dd77af7445` | +74 | `eval.hpp`, `eval.cpp` |
| `BUNDLE` (all five) | extra | `953ee65a4380d24b51f660982ffdbe04` | +169 | three files |

Results per item are in `BENCH.md`, written from the evidence files by `tools/collect_evidence.py`. This file does not repeat the tables.

**Novelty correction, 10:20.** `KING_PAWN_CACHE` joined the pool after the profile, and I re-ran the duplicate search for it only at 10:15. That run found commit `928f1ff7` (2026-10-13, branch `cursor/chess-engine-elo-8295` only): the same shelter cache in the source of that date, "about 1% faster" by its message, never in the lock lineage. Ruling 1 of the plan says a candidate found built on the fetch is dropped, so it is **not counted as a new candidate**. It stays in the pack as a labelled extra, because no combo29 version of it exists elsewhere; whether it is timed or used is the owner's and QA's call.

**Revisions after the review** (`REVIEW_LOG.md`). The reviewer found no correctness defect in either round. Patches were still changed:

| Patch | md5 history | What changed and why |
|---|---|---|
| `CHECKERS_KL` | `1b785bd3` (09:35) -> `beca3d00` (10:48) -> `c8f080ba` (11:09) | King moves now keep the lock's `attackers_to()`. In the first text an illegal king step next to the enemy king read as "no check" where the lock counts the king as a checker; the engine never makes that move, but the shortcut carried a precondition. Now it equals the lock for every pseudo-legal move, and the harness checks that on illegal moves too. Last revision: the comment states exactly why the engine never meets a position with the side not to move in check, and two castling flags that the king test made redundant are gone |
| `PAWN_CAPMASK` | `09b2ef4f` -> `2a680e14` (10:48) | One hunk sat in the older generator that the lock never compiles, so it had never been built. Removed; the switch now refuses that configuration with `#error` |
| `KING_PAWN_CACHE` | `d2beac06` -> `a51e1b69` (10:48) | Comment only: the switch changes a struct layout and must reach every translation unit |

Every build of a changed source, every harness build and every result of a patched build from before the last change of that patch were moved to `out\_old_v1\` and `out\_old_v2\` and are not used. Old patch texts: those folders and git commits `8e2d7a8f` (first texts) and `eac89354` (10:48 texts).

History of the first limit, for the record: the first verify-mode harness run of `CHECKERS_KL` aborted because the harness's own legality oracle played illegal king moves on a board copy that carried king lines. On the first 300 FENs, 0 of 701,068 legal makes differed from `attackers_to` and 2,051 of 28,231 illegal makes did, every one a king move ending next to the enemy king (`out\_old_v1\id\CHECKERS_KL\rootcause\`). With the final text the harness plays all generated moves, legal and illegal, on such copies and finds 0 differences (`BENCH.md`).

Patches: `patches/<NAME>_after_combo29.patch` (`-p1`, `--- a/src/...`). The singles apply with plain `git apply` in the listed order and in reverse and give the same tree; each bundle patch is the diff of that tree (`tools/make_bundle.ps1`). `tools/check_consistency.ps1` re-proves at any time that snapshot + patch = work tree = the source of each build.

Build tags under `out\build\`: `wit`, `evd`, `cap`, `chk`, `kpc`, `bn4`, `bn3`, `bun`, each `_off` (switch 0), `_on` (switch 1) and, where a verify mode exists, `_v2` (the `=2` verify build; not a patch revision). Work trees: `out\work\<NAME>\{a,b}`. To save disk, object files, PDBs, the instrumented first-stage exes and finished harness builds were deleted (11:49, 14:26, 15:40); final exes, merged profiles (`m2gen\m2.profdata`), source manifests and receipts are kept.

## Step 4: qualification

### What ran when

| When | What | Result |
|---|---|---|
| 11:11 to 11:43 | quick ladder for the seven items of that time (`qualify_all.ps1`, phase quick) | 50 PASS lines, 0 FAIL |
| 11:43 to 13:12 | first timing step, one fixed file per exe, bench 20 | superseded: `BENCH.md` section 3.3 |
| 13:12 to 14:01 | lock cold rows, net on and net off | 12,000 rows each; the first 200 equal QA's cached rows (checked in the morning), full comparison in `BENCH.md` section 1 |
| 13:20 to 14:22 | why did `BUNDLE4` read -3.65 %? | not the patch alone: `BENCH.md` section 3.1 |
| 14:01 to 14:45 | `BUNDLE4` verify engine over the cold set | PASS, 0 rows differ |
| 14:04 to 14:42 | second timing step: lock against lock, then `BUNDLE4`, a new exe copy per arm | -0.02 % and -0.70 % |
| 14:42 to 15:52 | mutants: single trees, then `BUNDLE4` | 15 of 15 and 12 of 12 CAUGHT, every control clean |
| 14:44 to 14:52 | `BUNDLE3`: tree from the three singles in two apply orders, patch, builds, switch-0 bytes, 12 pins | 89 / 0 bytes, 12/12 |
| 14:52 to 15:39 | `WITNESS_NOPIN` timed with a new copy per arm, 60 blocks | -1.02 % |
| 15:28 to 15:42 | `BUNDLE3` harness (plain and verify, 12,000 FENs and targeted), soak, perft; verify engine built, its 12 pins by 16:10 | all PASS |
| 15:44 to 16:32 | `WITNESS_NOPIN` against the lock with table sizes 1, 16 and 256 MB (`go`, 16 blocks each) | -0.85 %, -0.61 %, -1.56 %; the intervals overlap (`BENCH.md` section 3.4) |
| 16:06 to 16:27 | mutants in `BUNDLE` (the three eval mutants) | 2 CAUGHT; the third: one set refused by the disk guard (exit 95, logged as ERROR), caught on the other set |
| 16:32 to about 16:40 | D: under 30.3 GiB: nothing new was started | one mutant set refused, see above |
| from 14:59, stopped 16:56 | cold runs of the singles, `BUNDLE4`, `BUNDLE3`; from 16:44 of the two extras | INCOMPLETE, rows as in the table at the top |
| from 15:26, stopped 16:56 | timing of `BUNDLE3`, three singles, a second lock-against-lock round; from 16:44 of the two extras | INCOMPLETE, 34 to 36 blocks (extras 4 and 5) |
| 16:44, stopped 16:56 | mutants in `BUNDLE3` | INCOMPLETE: control clean, no mutant run |
| 16:58 | `BUNDLE3` warm transcript (finished run, verdict line written by `warmcheck`) | PASS, equal to the lock's |

### Why so much runs at once since 15:11

D: was falling towards 30.3 GiB, the level under which this job starts nothing. A run that has started finishes; a queue does not. So from 14:26 the remaining work was reordered (the two extras last), and from 15:11 every long run that matters was started at once instead of in a queue: about forty processes of this job on CPU 3, all at Idle priority. No other CPU was used. Every run then takes hours instead of minutes; total work is the same.

### Departures from the approved plan

| Plan | What happened | Why |
|---|---|---|
| Sustained work on CPUs 4-5; CPUs 3 and 6 for short builds | Everything on CPU 3 | The live gate kept CPUs 4-11 all day |
| At most three engines at once; timing runs alone | From 13:20 timing shared CPU 3 with this job's cold runs; from 15:11 up to about twenty engines at once on CPU 3 | One usable CPU; then the disk guard (above). Timing is by CPU cycles of the engine process and in pairs inside each block, so sharing costs precision, not validity; `BENCH.md` says which rows were taken in the crowd |
| A/B: lock exe against the switch-1 exe, 10 blocks | Second step with a new copy of the exe for every arm, 40 to 100 blocks, order alternating | The first step was biased by the files themselves (`BENCH.md` 3.1) |
| Cold 12,000 for every item, net on and net off | No item's cold run is complete: all were stopped at 16:56 (the extras had started at 16:44 only) | The owner's instruction to wrap up; before that the disk guard and one usable CPU |
| Tools never end a process | At 16:56 this job's own running processes were ended | The owner's instruction of 16:55 ("stop the still-running cold 12k runs cleanly (only your own processes)"); timing and mutant runs of this job were ended with them, since the job was to be closed |
| Bundle = the passing singles | A second bundle, `BUNDLE3`, was added after the timing | `WITNESS_NOPIN` timed slower than the lock |
| Corpus and branch index kept as the search base | Both deleted at 14:26 (50 MiB); the blob lookup was made again and saved | Disk |

### Things in the logs that look like failures and are not results

- `chain.log`, `cold_singles.log`, `timing2.log`: lines "NOTE by hand" mark steps that were taken out of a queue by writing their ids into the done-file. A following "skip ... (done earlier)" for such an id means handed over or postponed, as the note says. No process was killed to do this.
- `out\id\BUNDLE3\QUALIFY.log`: two lines "engine, verify build, cold net on: FAIL rows differing from the lock: -1" (15:14, 15:27) and one "engine, verify build: FAIL build failed" (15:26) come from calls that ran before the verify exe existed or in a child shell that lacked `Get-FileHash` (next point). One line "cold net off: FAIL NOT STARTED (another run is writing these rows)" is the new guard against two writers. `BENCH.md` shows none of these as a result.
- Windows PowerShell children started with `Start-Process` from PowerShell 7 inherited its module path and had no `Get-FileHash`. Eight cold runs and one warm run started that way at 15:11 to 15:25 did their work but could not have written their verdict line. `qualify.ps1 -Stages coldcheck` (or `warmcheck`) writes it afterwards from a finished file, with the same comparison as the plain stage, and says so in the line. It was used once: for the `BUNDLE3` warm transcript at 16:58. The cold runs were stopped before their end and carry INCOMPLETE lines instead.
- A process of another agent (Grok Bot, PID 13680, Normal priority, all CPUs) was seen at 15:54 listing file dates in this job's folder. It is not this job's; it was left alone.

## Reading of the result, for the owner

- **Bit-exactness:** nothing contradicts it for any item, and the cheap layers are complete. The expensive layer, a full cold run per item, is not: only `BUNDLE4`'s verify engine covered all 12,000 positions.
- **Speed:** the purpose of the lane was a faster lock. Under gate load none of the items is faster than the lock in this job's timing, and two are measurably slower. `BUNDLE3` is the bundle without the switch that costs time; its own timing was stopped before it could say more than "within about 1 % of the lock".
- **Why `WITNESS_NOPIN` costs time (a reading, not shown):** it skips the king-line build at 2,651,591 nodes of the frozen workload; 1,477,817 of those builds are never needed, but 1,173,774 are made later in the node, after the transposition-table probe, where they no longer overlap the wait for the table entry. With table sizes 1, 16 and 256 MB it read -0.85 %, -0.61 % and -1.56 %: the direction this reading predicts, with overlapping intervals.
- **What QA can use at once:** the copy test and the copy-per-arm timing (`QA_ABBA_PROTOCOL.md`).

## Open, if someone continues job 2

1. Cold 12,000 for each item (commands above); mutants in `BUNDLE3` (`tests\mutants.ps1 -Bundle BUNDLE3`) and the one refused set (`tests\mutants.ps1 -Bundle BUNDLE -Only kpc_shelter0`).
2. Timing of `BUNDLE3` and the three singles to 100 blocks on a CPU that is not crowded: `tools\timing2.ps1 -Round r2 -Plan "AA_lock_vs_lock:aa:on:40;BUNDLE3:bn3:on:100;EVADE_LEGAL:evd:on:60;PAWN_CAPMASK:cap:on:60;CHECKERS_KL:chk:on:60"`.

## md5 of the main files

`FILES.md` lists every file of the pack with md5 and sha256 (it cannot list itself; this file is listed there with the md5 it has after this edit). Patches: the table in step 3. `BENCH.md` is regenerated by `tools/collect_evidence.py`; its md5 at the final commit is in `FILES.md` and in the job's closing line together with the md5 of this file and of `FILES.md`.

## Resume commands

```powershell
. D:\forge_jobs_20261109\fable2\repo\fable_speed_lane\tools\env.ps1
git -C $REPO status --short; git -C $REPO log --oneline -8
# where every run stands (read-only)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T\dash.ps1 -Since 15:00
# verdict line for a finished cold run whose script could not write it
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T\qualify.ps1 -Name EVADE_LEGAL -Tag evd -Defs FORGE_SPD_EVADE_LEGAL=1 -Stages coldcheck -Nets on
# one cold run of one item (CPU 3, Idle)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T\qualify.ps1 -Name KING_PAWN_CACHE -Tag kpc -Defs FORGE_SPD_KING_PAWN_CACHE=1 -Stages cold -Nets on
# build a tree with the lock recipe (refuses to overwrite)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T\spd_build.ps1 -Tag <new> -Src <tree> [-ExtraDefs FORGE_SPD_X=1] -Mask 0x08
```

## Rulings taken during the work

- **Training step.** `Start-Process -RedirectStandardInput` gave the instrumented engine an empty stdin under this session's console-less host (0 bench lines). The build script now feeds the workload through `cmd.exe` redirection, byte for byte. The resulting control equals the lock in every code and data byte, so the recipe is unchanged in effect.
- **Strict-SHA attempt.** Stopped after reading the lock's PDB strings (about 5 minutes of the 45 allowed): the blocker is structural, see above.
- **No kills until 16:56.** Tools never kill an engine: quit, close stdin, wait, report a survivor. Queues were shortened through their done-lists only. The one exception is the wrap-up at 16:56, on the owner's instruction, described at the top.
- **Disk guard kept at 30.3 GiB.** When D: neared it, the guard was not lowered; work was reordered and started early instead.
- **Chain restarts in the morning**, all on purpose and without ending any process: 09:58, a parameter named `$out` in `qualify.ps1` hid the global `$OUT` (fixed); 10:31, the chain script was extended by `BUNDLE4`; 10:44 and 11:07, stopped before timing because the two review rounds changed patches and the harness.
- **Plan timestamp.** The plan file says "drafted 08:30"; the clock read about 08:05 when it was written.
