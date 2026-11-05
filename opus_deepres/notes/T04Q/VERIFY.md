# T04Q verify (adversarial re-read of notes/T04Q/AUDIT.md against the lock source)
Verifier slot S1, start 04:08 PC clock, writing 04:16. Lock = `src_al1s198_clean` (path in WORKER_RULES). `s:` =
src/search.cpp, `h:` = include/forge/search.hpp, `b:` = src/board.cpp. Nothing built or run; no outside source read.

Verdict: the audit stands. 0 cards is the right outcome: B1b and B4b fall under the "under +1 Elo is dropped" rule,
B10 is a duplicate of T04E-01 (already labelled so in the audit). No status change, no violation.

## Task items that are N/A for this track (checked, not skipped)
- Outside sources: none (sources.md rows 1-7 are the lock and own notes) -> no Elo to recompute, no licence row owed
  (`notes/T04Q/licences.md` rightly absent), reading rule satisfied, no other engine's tuned constant proposed.
- Known items: `bash tools/forge_has.sh 'TtExclusive'` -> 0 hits (R7TtExclusive not in the lock);
  `bash tools/forge_has.sh 'bad_captures_\[bad_count_'` -> 1 hit s:361 = T12B-01 (own fix b0c3882b, card line 36).
  None of B1b / B4b / B10 touches either site.
- Vendor / model-company names: grep over notes/T04Q/*.md -> 0 hits.
- card_lint: cards/T04Q/ is empty; the tool errors on the literal unmatched glob (OSError), which is not a lint
  failure. Nothing to lint.
- Tried gates: `tools/tried_gates.py --grep 'promot|rule50|Rule50|mate'` -> only UE3C (EvalRule50Damp) and R5D-MF
  (multi-worker matefix non-regression); neither covers B1b / B4b.

## The three HITs: refutation attempts
| row | re-read | refutation attempt | verdict |
|---|---|---|---|
| B1b TT mate vs 50-move counter | h:83-86 `score_usable` = both clocks < 90 or equal; s:115-120 `score_from_tt` has no clock term; s:921-925 cutoff needs clock < 90; s:694-697 mate on the 100th half-move still wins | Exposure needs a stored mate of k plies with current clock c < 90 and c + k > 100, i.e. k >= 11 and c >= 90 - k + 1: long forced mates without a zeroing move at clock ~75-89. PV nodes take no TT cutoff, but their zero-window children do, so the score can still reach the root. Not unreachable, not guarded beyond the < 90 rule. T06B-02 (one-liner, bucket rule) exists and would narrow the window; the audit says so | CONFIRMED minor HIT; < 1 Elo claim UNPROVEN but plausible; no card is right |
| B4b quiet promotions malus-only in capture history | s:1055 `quiet = !capture && !is_promotion`; s:1187 -> captures_tried; s:754 bonus needs `is_capture()`; s:764 malus at index `piece_type(captured_piece)` = 0 for Empty (board.hpp:199); s:1197 / 1201 skip promotions; only two writes to the table (s:757, 764); reads at s:516 and s:1058 | The entry can only fall (gravity fixed point -16384). Bound on the effect: the entry is read for ordering only. In the non-quiet pruning branch capture futility needs a true `capture` (s:1075) and the LMR history term needs `quiet` (s:1146), so a quiet promotion is never pruned or reduced by this entry in the lines read. In ordering a fully malused quiet queen promotion still carries +20000 plus 10 x (Q - P) SEE units (s:162-165, 516-517), so it stays ahead of all but high-value, high-history captures; under-promotions are -5000 by design | CONFIRMED asymmetry, ordering-only; < 1 Elo claim UNPROVEN but the bound supports it; no card is right. Not in any card (T04B-01 / T04B-02 mention promotions only for SEE margin / capthist pruning) |
| B10 futility `skip_quiets` drops later quiet checks | s:1064 `quiet && !gives_check`, s:1067 `skip_quiets = true` | T04E-01 lines 27-28 name this exact site ("Quiet futility (:1064-1068) ... also sets skip_quiets") and bit 2 of its option covers it (lines 33, 55) | CONFIRMED duplicate, already labelled in the audit; nothing to add |

## NOT HIT spot-checks (11 rows re-read; task asked for 5)
| row | evidence re-read | result |
|---|---|---|
| 1 | s:1219 `(best_move.is_none() \|\| !best_move.is_capture())` guards update_correction | holds |
| 5 | b:775-777 key out, `castling_ &= CastlingMasks[from] & CastlingMasks[to]`, key in; no else-if chain | holds |
| 9 | s:359 TT move skipped, s:361 unguarded write = T12B-01, correctly not re-reported | holds |
| 11 | s:1403-1414: on abort only `ss->pv[0]` is adopted and only if `pv_length > 0`; `score = iteration_score` sits after the break | holds (Threads=1) |
| 13 | h:324 `std::array<SearchStack, MaxPly + 8>` = 136; s:1360 `ss = &stack_[4]`; s:781 / 894 guard at ply >= 128; deepest write (ss + 2) at ply 127 -> index 133 | holds; box test still the proof |
| 14 | s:157-160 bonus clamped to +-16384, `e + c - e*\|c\|/16384`: e = +-16384 maps to +-16384 for any c, int arithmetic; s:153-155 bonus capped | holds |
| 17 | uci.cpp:364-365 `from == to ? "0000"` | holds |
| 20 | s:1147 `clamp(new_depth - r, 1, new_depth)`, s:1149 re-search rule, s:1162 PV re-search. Stronger invariant than the audit states: negative extensions (s:1107-1111) apply only to `move == tt_move`, which the picker returns first (MainTT s:346) with `move_count == 1` (s:1051-1052), and LMR needs `move_count > 1` (s:1137); so the clamp never sees `new_depth <= 0` at ANY `SingularDepth` value (default 7, s:36); `new_depth <= 0` just delegates to qsearch (s:880) | holds; the SingularDepth-tuning UB worry I had is a false alarm |
| B1 | s:109-120 to / from TT at every store / probe; h:55-63 constants | holds |
| B7 | s:965-968 `null_move_allowed && !(ss-1)->current_move.is_none() && has_non_pawn_material(stm)` and the upper-bound TT veto | holds |
| B9 | s:774 and s:885 `(local_nodes_ & 1023) == 0 \|\| node_limit_specified_` before `++local_nodes_` | holds |

## Unverifiable here (no runs allowed)
Row 13 and row 21 box tests; the B1b and B4b box tests; multi-worker row 11 (R5D path, out of Threads=1 scope).

## Changes made
AUDIT.md: one pointer line under its Status line; no row changed. Nothing else written outside notes/T04Q/,
F:/odr/work/T04Q-verify/ (empty) and board slot S1.
