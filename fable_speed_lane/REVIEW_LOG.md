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
| Ten positions aimed at single branches | Added with thirteen more (and a 24th from round 2) as `tests/targeted_fens.txt`; new `targeted` stage in the ladder; the mutants run on them too |
| Copy for the other call order from `pristine` | Done (finding 1) |
| Makes from grandchildren and the null-move child; makes in check after `is_legal` alone | Done (finding 2) |
| Clear the worker's caches mid-run; force pawn-cache index collisions | Caches are cleared every 997 FENs. Collisions are not forced by hand; the mutant `kpc_keepother` can only show through one (a pawn-cache slot reused for other pawns), so its verdict in BENCH.md section 4 says whether the runs meet them |
| Compare traced-evaluation coefficients between builds | Done: value, phase, scale and every coefficient are hashed into the transcript |
| Assert zero differences for illegal moves on lined copies | Done: it is a self-check of every run now |
| Control run and bundle mutants in `mutants.ps1` | Done (finding 3) |
| Fixed-node search parity between lock and each switch-1 build | Already in the ladder: warm session (`go nodes 20000`, 1,004 searches) and cold `go depth 13` over 12,000 FENs, net on and net off |

Consequence for the evidence: `CHECKERS_KL`, `PAWN_CAPMASK`, `KING_PAWN_CACHE` and both bundles got new patch files; the harness changed. Every result of a patched build obtained before 10:48 was set aside (`out\_old_v1\`) and the whole ladder was started again for all seven items. No earlier result is carried over to a changed patch. Kept, because they do not depend on any patch: the lock's own reference rows and the lock-against-lock A/A timing.

## Round 2: recheck of the changes (10:52 to 11:06)

Same reviewer, same rules; it was also given the build and run scripts (`tests/`, `tools/`). Rechecked: `CHECKERS_KL` v2 (`beca3d00`), `PAWN_CAPMASK` v2 (`2a680e14`), `KING_PAWN_CACHE` v2 (`a51e1b69`), `BUNDLE4` (`46253516`), `BUNDLE` (`ae84ec65`), harness, targeted positions, mutant script.

**Reviewer's verdict:** the new `CHECKERS_KL` claim is true ("I could not break it with any pseudo-legal non-king move"); no new defect in any patch; first-round findings 4 and 6 closed by reading the build scripts. Seven findings:

| # | Finding (reviewer's grade) | My assessment | Action |
|---|---|---|---|
| 1 | The mutant `chk_wrongking` would probably be MISSED: no targeted position has a discoverer moving along a line through its own king (PLAUSIBLE) | Correct | Targeted row 24 added (the reviewer's position) |
| 2 | The harness header promised "key_after equals the key after make", but nothing compared them (CONFIRMED) | Correct | Self-check added for every generated move |
| 3 | The cache clear came first at the 500th FEN, so the targeted set and the 300-FEN runs never met it (CONFIRMED) | Correct | First clear before the 8th FEN, then every 997 |
| 4 | `CHECKERS_KL` comment: "(set_fen() admits no other)" is incomplete; an illegal move or a null move made in check also gives a position whose side not to move is in check, and from there the shortcut is wrong (as the lock's `gives_check` is). Neither occurs in the engine (CONFIRMED, low) | Correct | **Patch comment rewritten**: the engine reaches no such position because `set_fen` refuses it, only legal moves are made, and the null move is not made in check |
| 5 | Targeted row 13 does not test the en-passant exclusion; only row 23 does (CONFIRMED, informational) | Correct | Row 13's description corrected |
| 6 | The castling flags in the `CHECKERS_KL` condition are redundant now that king moves are excluded (INFO) | Correct | **Removed from the patch** (`(EnPassant \| Promotion)` remains) |
| 7 | Build notes: the engine recipe is `-O3` with ThinLTO and PGO, the harness `-O2` without, so the harness proves parity of the source, not of the shipped binary; is switch-0 identity judged by the exe sha256?; `mutants.ps1` reused a harness exe without checking its source (INFO / QUESTION) | All true. Binary parity rests on the pins, the cold rows, the warm session and the verify engines, which use the lock recipe. Switch-0 identity is judged by byte ranges, not by sha256 (STATUS.md) | `mutants.ps1` builds its own base harness each run; `qualify.ps1` rebuilds a harness exe whose recorded source hash differs from `tests/prim_dump.cpp`, and reruns the base transcript when harness or FEN file changed |

Also noted by the reviewer and accepted: the "other call order" self-check is inert in the lock, because one function builds all king lines; it stays as a guard for a patch that would build them in parts, and the harness header now says so.

**Changes made after the recheck and not seen by the reviewer** (patch `CHECKERS_KL` v3, md5 `c8f080ba`; `BUNDLE4` `4cfedef4`; `BUNDLE` `953ee65a`): the comment rewrite of finding 4 and the removal of the two redundant castling flags of finding 6. The second is a code change of one constant. It is covered by the ladder, which was restarted from the builds on for `CHECKERS_KL` and both bundles: transcript equality on 12,000 FENs and the 24 targeted positions (row 12 is castling with check), the `=2` verify builds in the harness and in the engine, and the mutants. A third review round was not asked for: one constant, proposed by the reviewer itself.

## After the review (not seen by the reviewer)

No patch text changed after the texts named above (md5 in STATUS.md). What came later:

| Item | What | Why no further review round |
|---|---|---|
| `BUNDLE3` (14:44) | `EVADE_LEGAL` + `PAWN_CAPMASK` + `CHECKERS_KL` applied together; patch md5 `ba2fcf2e78a0e2c85964a1e6e258d150`, +77 lines | It holds no line that is not in the three reviewed singles; both apply orders give the same tree (`tools/make_bundle.ps1`). It went through the same ladder as the other bundles as far as the afternoon allowed (STATUS.md) |
| Timing tools | `spd_uci.py abba` options `--recopy`, `--alternate`, `--hash`, `--fixed-base`; `timing2.ps1`, `file_effect.py`, `pos_cycles.py`, `abba_spread.py`, `regime_abba.ps1`, `regime_pos.ps1`, `prof_diff.py` | They measure, they do not decide identity. The one review the brief allows was spent on the patches and the harness |
| Chain tools | `qualify.ps1`: `-Nets`, the check that two runs never write one row file, the stages `coldcheck` and `warmcheck` (verdict line for a finished run whose script instance could not write it); `pin.ps1`: a refused start now says NOT STARTED in the output file; `cold_singles.ps1`, `cold_extra.ps1`; `collect_evidence.py`: timing sections, "not run (held)" cells | Written under time pressure on 2026-11-10 afternoon when D: neared its floor. None changes what a check compares: `coldcheck` uses the same row comparison as the stage `cold`. A reader who wants to distrust them can re-run the plain stage `cold` for any item |

The row on pawn-cache index collisions in the "missing checks" table of round 1 left open whether the runs meet a reused pawn-cache slot. They do: the mutant `kpc_keepother`, which can only show through such a slot, was CAUGHT (`BENCH.md` section 4).

## State of the review

No open finding. No finding rejected without a stated reason. The reviewed property is "no reachable input can make switch 1 differ from switch 0 in anything the search or evaluation sees"; the reviewer read the code and proofs, I ran the checks. Neither is a formal proof. The review covers the patches and the harness as they were at 11:06; the table above lists what it does not cover.
