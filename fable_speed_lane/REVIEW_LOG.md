# REVIEW_LOG: the one review of this job

Policy: AGENTS.md "Development review and verification" (text recovered from commit `3e900941`, md5 `94169aef...`): one reviewer, read-only, reviewed files kept stable, every finding assessed, substantive fixes rechecked by the same reviewer. Times are Europe/Vienna, 2026-11-10.

## Who reviewed

One subagent of this session, fresh context, model Claude Opus 5.5 (the job itself runs on Claude Fable 5.2). It was given the patches, the lock source, the patched trees, the harness and the requirements, and was not given my analysis. Tools allowed: Read, and Grep inside the listed folders; no shell, no builds, no edits.

**How independent this is:** independent in context and in model. Not independent in organisation: same vendor, same session owner, briefed by me. It read code; it ran nothing. A second reviewer was not used (the brief allows one).

## Round 1 (10:12 to 10:36)

Reviewed: the six patch files as of commit `1677fa51` (`KING_PAWN_CACHE` `d2beac06`, `WITNESS_NOPIN` `ccfa6ce5`, `EVADE_LEGAL` `b5aaa89f`, `PAWN_CAPMASK` `09b2ef4f`, `CHECKERS_KL` `1b785bd3`, `BUNDLE` `21d6e2c7`), `tests/prim_dump.cpp`, `tests/mutants.ps1`, the lock's `board.cpp`, `eval.cpp`, `bitboard.cpp`, `uci.cpp` and headers in full, `search.cpp` lines 380-1818.

**Reviewer's verdict:** no correctness defect in any patch or in the bundle; none can change anything the search or the evaluation sees for a reachable input. Ten findings on the harness, the mutant script, contracts and build notes.

| # | Finding (reviewer's grade) | My assessment | Action |
|---|---|---|---|
| 1 | Harness: the "other call order" copy was taken from a board whose king lines were usually already built, so that order was rarely tested (CONFIRMED) | Correct. `fresh.has_legal_move()` builds the lines before the copy | Fixed: the copy is taken from `pristine` |
| 2 | Harness: moves were made only from the FEN position and its children, always after `gives_check`; never from grandchildren, the null-move child, or after `is_legal` alone (CONFIRMED, low risk) | Correct | Fixed: every generated move of every visited position is played on a copy whose king lines come from one query only (`is_legal` or `gives_check`, alternating), with a checkers check |
| 3 | `mutants.ps1`: no control run; any non-zero exit counted as CAUGHT; no bundle mutants; mutants missing for several branches (CONFIRMED) | Correct | Fixed: control per (tree, switches); CAUGHT needs a transcript difference, a CHECK FAILED report or a verify abort, anything else is ERROR; seven mutants added; `-Bundle` mode |
| 4 | Harness may be built without `FORGE_SPD_PREFETCH_EARLY` (QUESTION) | Not so: `tests/build_prim.ps1` passes the lock's six switches, that one included. The reviewer had not been given the build scripts | No change; the scripts were opened to the reviewer for the recheck |
| 5 | `CHECKERS_KL`: `make_move` gained an unwritten precondition (legal moves only once king lines are built); not reachable by the engine (CONFIRMED) | Correct, and the same limit I had measured (STATUS.md). Removing the precondition is better than documenting it | **Patch changed**: king moves keep the lock's `attackers_to()`. The result now equals the lock's for every pseudo-legal move; the harness checks exactly that, on illegal moves too |
| 6 | `KING_PAWN_CACHE`: the entry layout depends on a macro; a translation unit built without it would free over-aligned memory wrongly (QUESTION) | Both build scripts pass every `-D` to every unit, so it cannot happen with them | Comment sentence added to the patch; note in the pack's build recipe |
| 7 | Switch 0 shifts line numbers; debug info and a sample-based profile would differ (QUESTION) | True and harmless here: the lock uses instrumented PGO, and the switch-0 exe equals the lock in every code and data byte | No change |
| 8 | `WITNESS_NOPIN=2` builds king lines that mode 1 does not, so a `=2` bundle takes the `CHECKERS_KL` shortcut in a superset of the `=1` cases (CONFIRMED, informational) | Correct. The verify builds therefore check more shortcut uses than the shipped mode executes, not fewer | Noted in BENCH.md |
| 9 | `KING_PAWN_CACHE` entry: 32,768 entries, index and replacement rule unchanged; 40 to 64 bytes; aligned allocation; no memset or sizeof use (CONFIRMED, informational) | Agrees with my reading | No change |
| 10 | `PAWN_CAPMASK`: its second hunk sits in the generator the lock never compiles, so it was never built or tested (CONFIRMED) | Correct. Untested code does not belong in the patch | **Patch changed**: hunk removed; `#error` if the switch is used with that generator |

Missing checks named by the reviewer, and what was done:

| Reviewer's item | Done |
|---|---|
| Ten positions aimed at single branches | Added with thirteen more as `tests/targeted_fens.txt`; new `targeted` stage in the ladder; the mutants run on them too |
| Copy for the other call order from `pristine` | Done (finding 1) |
| Makes from grandchildren and the null-move child; makes in check after `is_legal` alone | Done (finding 2) |
| Clear the worker's caches mid-run; force pawn-cache index collisions | Caches are cleared every 997 FENs. Collisions are not forced by hand; the mutant `kpc_keepother` can only show through one (a pawn-cache slot reused for other pawns), so its verdict in BENCH.md section 4 says whether the runs meet them |
| Compare traced-evaluation coefficients between builds | Done: value, phase, scale and every coefficient are hashed into the transcript |
| Assert zero differences for illegal moves on lined copies | Done: it is a self-check of every run now |
| Control run and bundle mutants in `mutants.ps1` | Done (finding 3) |
| Fixed-node search parity between lock and each switch-1 build | Already in the ladder: warm session (`go nodes 20000`, 1,004 searches) and cold `go depth 13` over 12,000 FENs, net on and net off |

Consequence for the evidence: `CHECKERS_KL`, `PAWN_CAPMASK`, `KING_PAWN_CACHE` and both bundles got new patch files; the harness changed. Every result of a patched build obtained before 10:48 was set aside (`out\_old_v1\`) and the whole ladder was started again for all seven items. No earlier result is carried over to a changed patch. Kept, because they do not depend on any patch: the lock's own reference rows and the lock-against-lock A/A timing.

## Round 2: recheck of the changes (requested 10:52)

Pending.
