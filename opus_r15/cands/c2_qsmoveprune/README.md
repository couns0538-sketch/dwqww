# C2 QsMovePrune - quiescence move-count pruning (UNPROVEN)

Gate line: engine A = `D:\o15\cands\c2_qsmoveprune\forge_ltopgo_c2qmp.exe` + `setoption name QsMovePrune value 3`,
engine B = the lock. Exe sha256, ON bench and check results: `D:\o15\cands\INDEX.md` and `logs/RESULT.json`.
Patch: `c2_qsmoveprune.patch` (src/search.cpp only, +10), applies with `patch -p1` to git d4f4312.

## What it changes
In quiescence, out of check and once a stand-pat score exists (`best_score > -MateInMaxPly`): after `QsMovePrune`
legal moves were tried at this node, a further move is skipped unless it gives check, is a promotion, or recaptures
on the square the previous move went to. The test sits before the lock's futility and SEE tests and does not touch
`best_score`. Option `QsMovePrune` (spin 0..16, default 0 = off; ON line 3).

## Why it should gain
In quiescence the move picker orders captures by ten times the victim value plus capture history, so after the first
three tries the remaining captures are mostly low-value or doubtful, and with the stand-pat score already bounding the
node they rarely raise alpha - but each one still opens a new quiescence subtree, and quiescence nodes are usually
the larger share of all nodes. Capping the number of non-forcing captures per quiescence node saves that work at STC
and spends it on main-search depth, while the three exceptions keep the moves that decide tactics at the horizon:
checks, promotions and recaptures that finish an exchange on the last square.

## OFF identity
`QsMovePrune 0` makes the condition false at its first term: the lock's quiescence. Kit OFF node identity ALL OK,
bench d11-d22 + perft = the lock pins.

## Own review (structured self-review, NOT independent)
- `move_count` counts every legal move seen at the node, also those the lock's futility / SEE rules prune afterwards,
  so "N tries" means N legal moves in picker order (the same order the lock uses).
- In check nothing changes (the whole block is `!in_check`); so mate / stalemate detection in quiescence is untouched.
- `(ss - 1)->current_move.to` exists for every quiescence node (the stack starts at index 4); after a null move it is
  `Move::none()` (to = 0): only a recapture on a1 would then be kept by mistake - harmless.
- The TT move comes first from the picker, so it is never cut by this rule (move_count 1).
- Risk: a fourth capture that wins material on another square (a hanging piece ordered late) is no longer seen at the
  horizon; N = 3 (not smaller) and the victim-value-first order limit that. ON bench is higher at d16 / d20 than the
  lock (3,220,620 / 16,380,404): the main search changes too; node counts are not strength.
- PGO cold-path note as for every option line (profile trained with the option OFF).

## Check results (generated)

- exe `D:\o15\cands\c2_qsmoveprune\forge_ltopgo_c2qmp.exe` sha256 `ff63a706e83e2e750b19f3ba61a1b2175033624696d9982f36611e86d8ffa9a2` md5 `2b0bdecee31448565a5ead2d93b15247`; kit pc1 = pc2 `ff63a706e83e2e750b19f3ba61a1b2175033624696d9982f36611e86d8ffa9a2`
- ON bench d11 / d13 / d16 / d20 / d22: 363674 / 815943 / 3220620 / 16380404 / 35367903; OFF = the lock pins; perft 4865609 / 193690690 both ways
- cand_pack checks: patch_applies PASS, cleanroom_lint PASS, kit_build PASS, pc1_equals_pc2 PASS, kit_identity PASS, kit_vfmadd0 PASS, kit_missing_profile0 PASS, kit_on_live PASS, exe_copy_sha256 PASS, pin_off PASS, pin_on_live PASS, smoke PASS
- smoke with the fixed clock (12:37 fix): PASS - 19 games, 2365 plies, illegal 0, crashes 0, hangs 0, time losses 0
- R13 cand_checks (T1 / T4 movetime smoke with perft-1 legality, mate probe 22 positions at 3M nodes): PASS; mates OFF 19 / ON 19; strict-rule flips: none
- CI ASan+UBSan self-play: run 41628366851 success on 9fc59ea3c497 (patch sha256 = the built one)
