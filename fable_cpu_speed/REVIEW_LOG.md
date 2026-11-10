# REVIEW_LOG: structured self-review (not independent)

AGENTS.md asks for a read-only reviewer subagent after each milestone. Couns's rule for this job forbids subagents under any circumstances, so no independent review took place. What follows is my own review of my own work; treat it as such. An independent review by Code Review is still owed before any of these patches is trusted.

## Patch `NNUE_FUSE_EVAL` (reviewed 16:50, source = `patches/NNUE_FUSE_EVAL.patch`, MD5 `dad1b1623e5fe215301b448195b3aaa9`)

Claim: with the flag at 1 the stored accumulator and the returned value are bit-identical to `update()` followed by `evaluate()`.

| Point checked | Finding |
|---|---|
| Which moves take the new path | Exactly the two patterns the lock's `update()` fuses: two changes (remove, add) and three changes (remove, remove, add). Everything else (castling, null move) calls the lock's `update()` and `evaluate()` unchanged. |
| Arithmetic per lane | Quiet: `(source - removed) + added`. Capture: `((source - removed0) - removed1) + added`. Same operations and order as the lock's scalar expressions; no multiply is involved, so no fused multiply-add can arise. |
| Output layer | The lock's 512-bit kernel copied term for term (clamp to [0,1], square, times the output weight, add the two sides, add to the running sum in block order), then the same ordered 16-term sum and the same conversion and clamp. |
| Memory | Accumulators are 64-byte aligned when `FORGE_SPD_NNUE_ZMM=1` (aligned loads and stores); weight columns are read with unaligned loads because the code does not guarantee their alignment; parent and child are different stack entries. The patch refuses to compile without `FORGE_SPD_NNUE_ZMM=1`. |
| Call site | Only the last replayed move (`i == 0`) is fused; earlier replay steps and the runtime piece-square update are untouched; `ss->dirty` is the change list of exactly that move; `board` is the child position, as in the lock's `evaluate` call. |
| What was run | 26 of 26 pins; flag-0 build code-and-data identical to the lock rebuild; harness 48,000 of 48,000 (children take the fused path, grandchildren with a dropped parent take one plain update and then the fused one, castling children take the fallback); release rows against the real lock exe 48,000 of 48,000. |
| Not covered | Positions outside the 12,000-position set and their children; multi-thread runs of this build; any compiler other than the lock's. |

No finding that needs a change.

## Patch `EVAL_PIPELINE` (reviewed 16:50, MD5 `6955bd19231c1ea94232115d84e3f1b7`)

Claim: same calls as the lock, grouped as "hand-crafted part first, network part second"; mode 2 adds prefetches.

| Point checked | Finding |
|---|---|
| Walk-back distance and the refresh condition | Same expressions as the lock. |
| Runtime piece-square replay | The same calls in the same order relative to each other; they do not read accumulators. |
| Network replay | The same calls in the same order; they do not read the piece-square state or the pawn cache. |
| Result | `clamp(hand_crafted + network, ...)`; integer addition, same operands. |
| Non-residual nets | The new block is skipped; the lock code runs. |
| What was run | 26 of 26 pins; flag-0 build code-and-data identical; harness 48,000 of 48,000. |

No finding. The patch is slower than the lock and is stopped.

## Patch `NNUE_WPREFETCH` (reviewed 16:50, MD5 `4cff3d338ce774e4e689d8b77caf7415`)

Adds prefetch instructions only; a prefetch changes no architectural state. 26 of 26 pins, flag-0 build code-and-data identical, harness 48,000 of 48,000. No finding. Slower than the lock; stopped.

## Patch `PREFETCH_PICK` (reviewed 17:00, MD5 `40f47e7096e50c3f6dd2dd734daa24c3`)

Claim: only the moment of the table prefetch changes.

| Point checked | Finding |
|---|---|
| What moves | The three lines of `FORGE_SPD_PREFETCH_EARLY` (`child_key`, `key_after`, prefetch) are issued right after `is_legal(move)` in both move loops. `key_after` is a const function of the board and the move; the board is unchanged between the new place and the old one (a singular-extension search in between makes and unmakes its moves). |
| The variables' later uses | The existing lines after `make_move` (`assert`, and the fallback prefetch when `key_after` declined) still see `early_key` and `child_key`; they are in the same loop body. |
| Main search, old place | One more prefetch of the same address, because a singular-extension search may have pushed the line out of the cache since the first one. |
| One lock line is edited | In `qsearch` the condition `#if FORGE_SPD_PREFETCH_EARLY` becomes `#if FORGE_SPD_PREFETCH_EARLY && !FORGE_SPD_PREFETCH_PICK`. With the flag at 0 the preprocessor result is the same; the flag-0 build is code-and-data identical to the lock rebuild. |
| Cost side | A move that is pruned after the legality test has cost one `key_after` and one unused prefetch. |
| What was run | 26 of 26 pins; flag-0 build code-and-data identical; release rows against the real lock exe (see `DONE.md`). The evaluation harness also ran (48,000 of 48,000) but does not exercise this patch: the change is in the search loops, not in the evaluation. |

No finding that needs a change.

## Tools: defects I found in my own scripts during the job

| Tool | Defect | Effect | Handling |
|---|---|---|---|
| `freeze.ps1` | `$R` and loop variable `$r` are one name in PowerShell | failed on its last step, no verdict written | renamed, re-run |
| `cand_ladder.ps1` | same trap with `$T` / `$t` | the last two steps of candidate 2 did not start | steps run by hand, script fixed before candidate 3 |
| `bytecmp.py` | judged a merged differing range as a whole and did not know `.buildid` | two logs say DIFFERENT where code and data are identical | fixed; `_r2` logs; old logs kept and named in `DONE.md` |
| `san.py` | static ASan link met a duplicate libstdc++ typeinfo | first ASan engine link failed | link flag added, fixtures re-run with the same line |
| `run_harness_set.ps1` | expected the planted network fault to show with the net off | one "UNEXPECTED" line on the console | no log is wrong; explained in `STATUS.md` |
| `bughunt.py` | the case "Threads change during search" waits for a third best move that never comes | one false NO-ANSWER flag | explained in `README.md`; the engine answered correctly |

## Checks on the checkers

`selftest_checkers.log`: the pin checker rejects a wrong expected value, an exe with no output, a timeout and a non-zero exit code; the row comparer rejects one altered row, a cut-off file and a trailer that says INCOMPLETE. The sanitizer set-up is shown by six planted faults. The harness is shown by a planted fault in the capture update.
