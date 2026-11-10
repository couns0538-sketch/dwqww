# fable_speed_lane: bit-exact speed patches on combo29

Job "Fable 2", 2026-11-10, branch `fable52-speed-lane-20261109`. For Engine QA's quiet ABBA. Times are Europe/Vienna.

**Read first:** `STATUS.md` (state, what did not run, BLOCKED items, resume commands), then `BENCH.md` (evidence tables), `DUPCHECK.md` (what is new and what is not), `QA_ABBA_PROTOCOL.md` (what to time and one check to make before trusting a timing).

## The three things to know

1. **Identity.** Four new patches, each behind a switch that defaults to 0. With the switch at 0 the build equals the lock in every code and data byte; with it at 1 every check that ran found the same nodes, moves and evaluations as the lock. `BENCH.md` section 2 shows each check per item, including the ones that did not run.
2. **Speed, measured under gate load.** `WITNESS_NOPIN` is about 1 % *slower* than the lock, and so is the four-bundle that contains it (about 0.7 % slower). The three-bundle without it (`BUNDLE3`) and the other three singles were still being timed when this file was last committed; their rows are in `BENCH.md` section 3.2 and `STATUS.md` gives the reading. These are INDICATIVE numbers from one shared CPU (`BENCH.md` section 3.2); the exact counters of removed work are in section 5. Removed work did not turn into speed here; a quiet machine may read differently, and that is the ABBA's question.
3. **A fixed pair of exe files can read several percent off.** The first timing of the four-bundle said -3.65 % over 30 tight blocks, and +0.30 % two hours later on the same two files; byte-identical copies of the lock were measured up to 6 % apart. All numbers in point 2 were therefore taken with a new copy of the exe for every arm. `BENCH.md` section 3.1 and `QA_ABBA_PROTOCOL.md` say what QA can check in a few minutes.

## What is delivered

Patches against the combo29 lock source (`patches/<NAME>_after_combo29.patch`, `git apply -p1`). Every added line sits behind a switch that defaults to 0.

| Patch | Switch | File | What it does | Novelty |
|---|---|---|---|---|
| `WITNESS_NOPIN` | `FORGE_SPD_WITNESS_NOPIN` | `src/board.cpp` | `has_legal_move`: a quiet pawn push whose pawn stands on no line through its own king is accepted without the legality test, when not in check | LISTED-UNBUILT |
| `EVADE_LEGAL` | `FORGE_SPD_EVADE_LEGAL` | `src/board.cpp` | `is_legal` in check, for non-king, non-en-passant moves: capture the single checker or block it, and respect the pin; no full king-attack test | LISTED-UNBUILT |
| `PAWN_CAPMASK` | `FORGE_SPD_PAWN_CAPMASK` | `src/board.cpp` | pawn-capture loop visits only pawns that attack an enemy piece | UNLISTED |
| `CHECKERS_KL` | `FORGE_SPD_CHECKERS_KL` | `src/board.cpp` | `make_move` reads the new checkers from the king lines when they are built and the move is an ordinary move of a piece other than the king | LISTED-UNBUILT |
| `BUNDLE4` | the four above | `src/board.cpp` | the four new candidates together (the ALL-ON bundle) | bundle |
| `BUNDLE3` | `EVADE_LEGAL`, `PAWN_CAPMASK`, `CHECKERS_KL` | `src/board.cpp` | the four-bundle without `WITNESS_NOPIN`; added after the timing | bundle |
| `KING_PAWN_CACHE` | `FORGE_SPD_KING_PAWN_CACHE` | `include/forge/eval.hpp`, `src/eval.cpp` | king shelter and king-pawn distance terms kept in the pawn-cache entry | **NOT NEW** (built before, commit `928f1ff7`); extra |
| `BUNDLE` | all five | three files | `BUNDLE4` + `KING_PAWN_CACHE` | extra |

The switches are build switches, not UCI options. `WITNESS_NOPIN`, `EVADE_LEGAL` and `CHECKERS_KL` also accept `=2`: a test-only mode that computes old and new side by side and aborts on any difference. Any subset of switches can be built from a bundle patch.

## What "bit-exact" was checked with

For each patch and each bundle (results in `BENCH.md`, section 2):

1. Switch 0: lock-recipe build compared with the lock exe byte by byte.
2. Switch 1: bench d11/13/16/20/22 net on and net off, perft 5 startpos and kiwipete (the 12 pins).
3. Harness `tests/prim_dump.cpp` over 12,000 FENs and their children, and over 24 positions aimed at single branches (`tests/targeted_fens.txt`): move lists in order, `is_legal`, `gives_check`, `see_ge`, checkers, keys, `has_legal_move`, make/unmake, null move, hand-crafted eval, traced eval, net output and static eval; the transcript must equal the lock source's. Every generated move, legal or not, is also played on a copy with king lines and the resulting checkers are compared with a direct attack test.
4. Verify builds (`=2`): the harness over the same sets, and the engine itself on the 12 pins (bundles: also over the cold set).
5. Cold: `go depth 13` on 12,000 FENs, net on and net off; every row (depth, score, nodes, best move) must equal the lock's.
6. Warm session with hash-size changes, Clear Hash, net off/on, `ucinewgame`, repeated searches; Threads 2-4 soak; six perft positions.
7. Planted mutants (`tests/mutants.ps1`): fifteen wrong versions, each in its single tree and again in a bundle tree with all switches on, each next to a control run of the unchanged tree, to show the harness notices a wrong patch.

Limits of these checks, stated plainly: a finite position set proves nothing about positions outside it; the correctness arguments are in the patch comments and were read by one reviewer (`REVIEW_LOG.md`). The Threads 2-4 soak shows no crash, hang or illegal move; it is not a node-identity proof, because multi-thread search is not deterministic in the lock either. Not every check ran for every item: D: fell towards its 30 GiB floor in the afternoon and this job's own guard stops new runs below 30.3 GiB. `BENCH.md` says "not run" where that is so, and `STATUS.md` lists those cells.

## Timing

`BENCH.md` section 3, in three parts: 3.1 the per-file effect, 3.2 the timing with a new copy of the exe per arm (the numbers to read), 3.3 the first timing step with fixed files (kept as a record, superseded). All INDICATIVE: one shared CPU at Idle priority under gate load, from 15:11 on shared by many of this job's own runs. The ABBA is QA's: `QA_ABBA_PROTOCOL.md`.

`BENCH.md` section 5 is not a timing: it gives exact counters of the work each switch removes over the lock's own frozen workload (for example how many king-line builds, full king-attack tests or `attackers_to` calls disappear). Those numbers are repeatable on any machine; what they are worth in nodes per second is for the ABBA to say.

Why `WITNESS_NOPIN` can cost time although it removes work: a reading that fits the measurements, not a shown cause. The search asks for the child's transposition-table entry before `make_move` (a prefetch) and reads it at the top of the child, after `is_draw`, which calls `has_legal_move`. In the lock that call builds the king lines, so the build runs while the entry is on its way. `WITNESS_NOPIN` skips the build there. At a node that ends at the table probe nothing is gained as long as the entry has not arrived: the search waits instead of building. At a node that goes on, the lines are built later, after the probe, at full cost. Over the frozen workload (4.2 million nodes) the patch skips the build at 2.65 million nodes; 1.48 million of those builds are never needed, the other 1.17 million are made later, behind the probe (exact counters, `evidence/witness_counters.txt`). Under load the second number can cost more than the first saves; with the table in cache the first should win. `BENCH.md` section 3.4 holds a first test of this with table sizes of 1, 16 and 256 MB. `CHECKERS_KL` also removes work between prefetch and probe (the `attackers_to` call in `make_move`), but moves none behind the probe.

## Folder map

| Path | Content |
|---|---|
| `patches/` | the five single patches and the three bundle patches |
| `STATUS.md`, `BENCH.md`, `PROFILE.md`, `DUPCHECK.md`, `IDEA_SOURCE.md`, `REVIEW_LOG.md`, `QA_ABBA_PROTOCOL.md`, `FILES.md` | reports; `FILES.md` lists every file with md5 and sha256 |
| `tools/` | pinned launchers, lock-recipe build, byte compare, UCI driver, chain scripts, timing with a copy per arm (`timing2.ps1`), copy test (`file_effect.py`) |
| `tests/` | differential harness, its build script, targeted positions, mutants |
| `evidence/` | compact evidence copied from the job folder (receipts, pins, sha256 of row files, timing samples, logs) |
| `data/` | duplicate-search hits; lookup of the lock's source files by git blob id |
| `../skills/forge-bitexact-speed-lane/` | the method as a skill |

On the PC only (not on the branch; they contain engine source and the embedded net): `D:\forge_jobs_20261109\fable2\out\packs\<NAME>\` (source zip, patch, build recipe, this job's exes, checksums) and `D:\forge_jobs_20261109\fable2\out\` (builds, full row files, logs).

## How to re-run a check

```powershell
. D:\forge_jobs_20261109\fable2\repo\fable_speed_lane\tools\env.ps1
# does every patch still equal its work tree and the source of its builds?
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T\check_consistency.ps1 -Cands WITNESS_NOPIN:wit,EVADE_LEGAL:evd,PAWN_CAPMASK:cap,CHECKERS_KL:chk,KING_PAWN_CACHE:kpc,BUNDLE4:bn4,BUNDLE3:bn3,BUNDLE:bun
# one stage of the ladder for one item (CPU 3, Idle); -Nets on or off makes one of the two cold runs
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T\qualify.ps1 -Name BUNDLE3 -Tag bn3 -Stages cold `
  -Defs FORGE_SPD_EVADE_LEGAL=1,FORGE_SPD_PAWN_CAPMASK=1,FORGE_SPD_CHECKERS_KL=1
# timing with a new copy of the exe per arm: lock against lock, then one item
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T\timing2.ps1 -Round mine -Plan "AA_lock_vs_lock:aa:on:40;BUNDLE3:bn3:on:100"
# does one exe run alike from six files? (the copy test)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $PIN -Exe $PY -Mask 0x08 -ArgLine "-I -B $T\file_effect.py --exe $OUT\base\combo29_lock_E1284F7F.exe --out $OUT\regime\FILE_EFFECT\mine"
```

Start these from Windows PowerShell or with `& powershell.exe` from PowerShell 7. A Windows PowerShell started with `Start-Process` from PowerShell 7 inherits its module path and has no `Get-FileHash`; the scripts then stop on their first hash.

## What this job did not do

No lock, queue, gate, net, dataset or training file was touched. No match, SPRT, tuning game or ABBA for decision was started. No process of another job was stopped, and none of this job's own was killed. Nothing was written to C: or F: (the session's own plan file and scratch aside). No engine source and no net is committed here.
