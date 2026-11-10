# fable_speed_lane: bit-exact speed patches on combo29

Job "Fable 2", 2026-11-10, branch `fable52-speed-lane-20261109`. For Engine QA's quiet ABBA. Times are Europe/Vienna.

**Read first:** `STATUS.md` (state, BLOCKED items, resume commands), then `BENCH.md` (evidence tables), `DUPCHECK.md` (what is new and what is not).

## What is delivered

Patches against the combo29 lock source (`patches/<NAME>_after_combo29.patch`, `git apply -p1`). Every added line sits behind a switch that defaults to 0; with the switch at 0 the build equals the lock in every code and data byte.

| Patch | Switch | File | What it does | Novelty |
|---|---|---|---|---|
| `WITNESS_NOPIN` | `FORGE_SPD_WITNESS_NOPIN` | `src/board.cpp` | `has_legal_move`: a quiet pawn push whose pawn stands on no line through its own king is accepted without the legality test, when not in check | LISTED-UNBUILT |
| `EVADE_LEGAL` | `FORGE_SPD_EVADE_LEGAL` | `src/board.cpp` | `is_legal` in check, for non-king, non-en-passant moves: capture the single checker or block it, and respect the pin; no full king-attack test | LISTED-UNBUILT |
| `PAWN_CAPMASK` | `FORGE_SPD_PAWN_CAPMASK` | `src/board.cpp` | pawn-capture loop visits only pawns that attack an enemy piece | UNLISTED |
| `CHECKERS_KL` | `FORGE_SPD_CHECKERS_KL` | `src/board.cpp` | `make_move` reads the new checkers from the king lines when they are built and the move is an ordinary move of a piece other than the king | LISTED-UNBUILT |
| `BUNDLE4` | the four above | `src/board.cpp` | the four new candidates together | bundle |
| `KING_PAWN_CACHE` | `FORGE_SPD_KING_PAWN_CACHE` | `include/forge/eval.hpp`, `src/eval.cpp` | king shelter and king-pawn distance terms kept in the pawn-cache entry | **NOT NEW** (built before, commit `928f1ff7`); extra |
| `BUNDLE` | all five | three files | `BUNDLE4` + `KING_PAWN_CACHE` | extra |

The switches are build switches, not UCI options. `WITNESS_NOPIN`, `EVADE_LEGAL` and `CHECKERS_KL` also accept `=2`: a test-only mode that computes old and new side by side and aborts on any difference.

## What "bit-exact" was checked with

For each patch and each bundle (results in `BENCH.md`, section 2):

1. Switch 0: lock-recipe build compared with the lock exe byte by byte.
2. Switch 1: bench d11/13/16/20/22 net on and net off, perft 5 startpos and kiwipete (the 12 pins).
3. Harness `tests/prim_dump.cpp` over 12,000 FENs and their children, and over 23 positions aimed at single branches (`tests/targeted_fens.txt`): move lists in order, `is_legal`, `gives_check`, `see_ge`, checkers, keys, `has_legal_move`, make/unmake, null move, hand-crafted eval, traced eval, net output and static eval; the transcript must equal the lock source's. Every generated move, legal or not, is also played on a copy with king lines and the resulting checkers are compared with a direct attack test.
4. Verify builds (`=2`): the harness over the same sets, and the engine itself on the 12 pins (bundles: also over the cold set).
5. Cold: `go depth 13` on 12,000 FENs, net on and net off; every row (depth, score, nodes, best move) must equal the lock's.
6. Warm session with hash-size changes, Clear Hash, net off/on, `ucinewgame`, repeated searches; Threads 2-4 soak; six perft positions.
7. Planted mutants (`tests/mutants.ps1`): fifteen wrong versions, each in its single tree and again in a bundle tree with all switches on, each next to a control run of the unchanged tree, to show the harness notices a wrong patch.

Limits of these checks, stated plainly: a finite position set proves nothing about positions outside it; the correctness arguments are in the patch comments and were read by one reviewer (`REVIEW_LOG.md`). The Threads 2-4 soak shows no crash, hang or illegal move; it is not a node-identity proof, because multi-thread search is not deterministic in the lock either.

## Timing

`BENCH.md` section 3: INDICATIVE only (one shared CPU at Idle priority while gates ran; a single block there is worth about +/-5 % by wall clock and +/-2 % by CPU cycles). The ABBA is QA's: `QA_ABBA_PROTOCOL.md`.

`BENCH.md` section 5 is not a timing: it gives exact counters of the work each switch removes over the lock's own frozen workload (for example how many king-line builds, full king-attack tests or `attackers_to` calls disappear). Those numbers are repeatable on any machine; what they are worth in nodes per second is for the ABBA to say.

## Folder map

| Path | Content |
|---|---|
| `patches/` | the five single patches and the two bundle patches |
| `STATUS.md`, `BENCH.md`, `PROFILE.md`, `DUPCHECK.md`, `IDEA_SOURCE.md`, `REVIEW_LOG.md`, `QA_ABBA_PROTOCOL.md`, `FILES.md` | reports; `FILES.md` lists every file with md5 and sha256 |
| `tools/` | pinned launchers, lock-recipe build, byte compare, UCI driver, chain scripts |
| `tests/` | differential harness, its build script, targeted positions, mutants |
| `evidence/` | compact evidence copied from the job folder (receipts, pins, sha256 of row files, timing samples, logs) |
| `data/` | duplicate-search hits |
| `../skills/forge-bitexact-speed-lane/` | the method as a skill |

On the PC only (not on the branch; they contain engine source and the embedded net): `D:\forge_jobs_20261109\fable2\out\packs\<NAME>\` (source zip, patch, build recipe, this job's exes, checksums) and `D:\forge_jobs_20261109\fable2\out\` (builds, full row files, logs).

## How to re-run a check

```powershell
. D:\forge_jobs_20261109\fable2\repo\fable_speed_lane\tools\env.ps1
# does every patch still equal its work tree and the source of its builds?
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T\check_consistency.ps1 -Cands WITNESS_NOPIN:wit,EVADE_LEGAL:evd,PAWN_CAPMASK:cap,CHECKERS_KL:chk,KING_PAWN_CACHE:kpc,BUNDLE4:bn4,BUNDLE:bun
# one stage of the ladder for one item (CPU 3, Idle)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T\qualify.ps1 -Name BUNDLE4 -Tag bn4 -Stages cold `
  -Defs FORGE_SPD_WITNESS_NOPIN=1,FORGE_SPD_EVADE_LEGAL=1,FORGE_SPD_PAWN_CAPMASK=1,FORGE_SPD_CHECKERS_KL=1
# the whole chain (skips what chain_done.txt lists)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T\qualify_all.ps1 -Phases quick,timing,cold
```

## What this job did not do

No lock, queue, gate, net, dataset or training file was touched. No match, SPRT, tuning game or ABBA for decision was started. No process of another job was stopped. Nothing was written to C: or F: (the session's own plan file and scratch aside). No engine source and no net is committed here.
