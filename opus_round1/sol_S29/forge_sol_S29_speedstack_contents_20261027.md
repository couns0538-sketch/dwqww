# S29 speed stack: contents (2026-10-27)

One compile switch, `FORGE_SPEEDSTACK` (CMake option, default OFF; PC recipe: `-DFORGE_SPEEDSTACK=1`). With the
switch off the build is the AL1 lock code. With it on, every piece below is active; there is no UCI option, so the
UCI option list is unchanged. Patch: `forge_sol_S29_speedstack_20261027.patch` (vs the lock tree `d4f4312`).

## Pieces that went in (node-exact)
| piece | from | what it does | node identity evidence |
|---|---|---|---|
| material-key table | S11 (`opus-sol-S11`, Sol's `forge_sol_S11_material_history_key_20261026.patch`) | `material_key()` returns `matkey::table_key()`: the same 64-bit key as the Horner polynomial, from a 10 × 65 contribution table (ten loads and adds instead of ten dependent multiply-adds and a final multiply) | count-domain proof (650 single-slot vectors cover all 65^10 count vectors), 200,000 random-walk boards through the real `corrected_eval`, bench at all 5 depths (this branch and opus-sol-S11) |
| child TT prefetch | S13 (`opus-sol-S13`, Sol's `forge_sol_S13_ttprefetch_20261026.patch` cc3efc96) | prefetch the child's TT bucket after `make_null_move` and after the ProbCut `make_move` (the lock already prefetches after the main-search and quiescence makes) | a prefetch is a hint only; bench at all 5 depths (this branch and opus-sol-S13, whose probe counted 640 null-move and 217 ProbCut child prefetches) |

In the stack both pieces are unconditional under the switch: S11's runtime test of `MaterialKeyTable` and S13's
per-search `TtChildPrefetch` snapshot and announce line are not needed, because a switch-on build always runs them.

## Pieces that did not go in, and why
| candidate | from | why it is not in the stack |
|---|---|---|
| lazy accumulator updates | S12 | already in AL1 (`static_evaluate` replays dirty pieces from the nearest computed ancestor); nothing to stack |
| null-move accumulator alias | S12 (Sol's prepared patch, never compiled) | not ported or tested on AL1 (opus-sol-S12 REPORT section 5); no node-exact evidence exists |
| allocation-free MovePicker, mailbox `piece_type` | S14 | already in AL1 (opus-sol-S14: static audit of the lock exe, 0 allocation calls) |
| MovePicker zero-fill removal (3,328 B per picker) | S14 follow-up | a candidate only; not implemented or tested |
| int32 exact accumulators (Job A) | shelved | not node-exact speed work; 4-5% slower ON (opus-sol-S12) |
| O2's speed work | opus-O2 (Opus job) | not part of Sol's S11-S14 queue; it is its own job with its own options |

## Speed status
Neither piece met Sol's "+2% lower bound" eligibility rule alone (opus-sol-S11: quiet runner ON/OFF d16 +0.2%,
d20 +1.7%; opus-sol-S13: no measurable effect). The stack's NPS is measured advisory only (ABBA), as the spec says;
one [-3, 1] non-regression gate for the whole stack is QA's call.
