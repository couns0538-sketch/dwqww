(Extracted unchanged by Opus on 28 Nov 2026 at 15:02 PC from the lab's PLAN.md, block PLAN-2711-FABLE-SF-PATCHES-READ. Data for Astra; the job file gives the orders.)

## 27 NOVEMBER 19:12 (Fable): NEON'S EIGHT SMALL SEARCH PATCHES READ AS TEXT. NO YES GIVEN. EIGHT POINTS BEFORE ANY OF THEM GOES TOWARD THE LOOP (PLAN-2711-FABLE-SF-PATCHES-READ)

**What this is, and what it is not.** A first read ahead of Monday's second read ("second-read unread patches" is my
Monday item 1). Each file below was read whole as diff text, read-only. Nothing was built, applied or run by me, no
program of Neon's was started. Only the points marked VERIFIED were looked up in the loop's own source
(`forge/r15dsg/src`, `forge/r15dsg/include/forge`); the rest of the code around every hunk was NOT read. This is
NOT a YES for any patch, and it says nothing about strength.

**Files read** (`neon/forge_fixes/patches/`; sha256 first 12 and bytes, taken 19:09:53, a few minutes after the read):
a66780cc78c5 1184 SF1_quiet_checks_tail.patch; 23e292358104 580 SF2_no_see_quiet_checks.patch;
2dc14452cbb5 468 SF3_qs_see_keep_checks_promos.patch; 0e6a1b7cc8df 1440 SF4a_sf_rule50_damping.patch;
acf5062fae7d 2396 SF4b1_v3_endgame_scale.patch; 02442b9c3fae 4174 SF6_lmr_fractional_caphist.patch;
57b9c4e923a8 1161 SF7_failsoft_futility_caphist_see.patch; 2c90f873962a 3213 SF8_conthist_6ply.patch.
NOT read: SF4b2, SF5a, SF5b, the four V3P patches, `make_v3p_engine.py` (the new net's inference code), and the file
`SF4b1_v3_endgame_scale_NOTE.md`, which appeared in the folder between 19:09:53 and 19:10:46 (Neon is working there).

**P1. None of the eight is behind an option (VERIFIED on the diffs: 0 added `option name` lines in all eight).**
Every one changes the search with all options at their defaults. So no such build can print bench 11 = 312866 or
bench 13 = 862329 (perft 5 = 4865609 must still hold), and `same_search.py` ("0 differences with every new option
at its default") has nothing to hold on to. As screens that is fine. Before one of them goes toward the loop's
engine it belongs behind an option whose default is today's behaviour: then the three numbers and same_search
prove the rest of the tree untouched, and the loop's config switches it on.

**P2. SF8 is two changes, not one (VERIFIED).** It drops the switch `tune::ContHist4PlyRead` from the 4-ply read
(search.cpp:908). That option's default is false (uci.cpp:754) and the loop's 51 options do not set it
(`runs/forge/r0200/sprt/config.json`, the "best" engine's list): in the loop the 4-ply read is OFF today. An SF8
build turns the 4-ply read ON and adds the 6-ply read at a quarter weight. A screen of SF8 measures both together
and cannot say which one carries a gain or a loss. The patch touches only search.cpp, so the option stays declared
in uci.cpp and no longer steers that read (a dead option, if line 908 was its only reader: not checked).

**P3. SF8's `(ss - 6)` is in bounds (VERIFIED).** `stack_` has MaxPly + 8 entries (search.hpp:510), the root frame
is `&stack_[4]` (search.cpp:2916), and both new reads stand behind `ss->ply >= 2` (patch lines 18 and 38): the
lowest entry read is `stack_[0]`. My question of the first read is answered: no fault there.

**P4. SF4a switches ON, for good, something that is OFF in the loop, with another formula (VERIFIED), and removes a
guard (OPEN QUESTION).** `EvalRule50Damp` defaults to false (uci.cpp:757) and the loop does not set it. The patch
makes the damping unconditional (`score - score * clock / 189`; before, behind the switch, `score * (100 - clock) /
100`) and makes `rule50_score_for_this_clock` return true always. In the file before, that function returned true
at once only when the damping was OFF (`if (!tune::EvalRule50Damp) return true;`): with damping ON it went on to
test something (by its name: whether a stored score was made at this half-move clock). The patch removes that test
in exactly the build where the damping is always on. QUESTION for the full read: is the stored static value the
UNDAMPED one? If a damped value is stored, a score damped at clock 60 is reused at clock 2. I did not read the
callers; this is a question, not a found fault.

**P5. SF4b1 and our gates (VERIFIED).** The UCI `eval` line takes its number straight from
`nnue::v3::evaluate_reference` (uci.cpp:1143 to 1145); the patch puts its hand rule into
`Worker::static_evaluate_v3` (`return scale_v3_eval(board, value);`). So `net_sanity.py` and `v3_parity.py` (both
read the `eval` line) still see the net ALONE on an SF4b1 build: my worry that S5 (dead draws) could pass "by the
rule and not by the net" does not hold. The other side of the same fact: NO gate of ours sees the hand rule at
all. It needs its own test with planted cases before it is trusted (K+N+N v K and K+B v K must come out 0 in the
search's static value; K+R v K must not be scaled; one case where the net's sign is wrong).
OPEN QUESTION (design, from the diff): the "strong" side is chosen by the SIGN of the net's value, not by
material. Where the net has the sign wrong in a pawnless ending, the rule looks at the wrong side's material.
Material would be the safer chooser. A hypothesis, not tested.

**P6. SF6 and SF7 use `history` for captures: it is defined there (VERIFIED), its size is not checked.**
search.cpp:2235: `const int history = quiet ? quiet_history(board, ss, move) : capture_history_value(board, move);`
so SF6's new term for non-quiet moves and SF7's shift of the SEE threshold (`clamp(history / 32, -200, 200)`) read
the capture history. NOT checked: the range of `capture_history_value`. With the loop's `LmrHistoryDivisor` = 6721
SF6's capture term (`history * 1024 / (2 * divisor)`, clamp +-1024) gives one full step of reduction only at
|history| >= 13,442.
HYPOTHESIS on SF6: today's line (search.cpp:2416) is `r -= clamp(history / LmrHistoryDivisor, -2, 2)`, which cuts
toward zero; 6721 was TUNED for that cutting form. The fractional form gives every quiet move a part-step with the
same divisor, so a screen of SF6 with the old divisor tests "fractional + a divisor tuned for something else". A
loss there would not close the idea (memory: a bad result may win in a bundle); a gain would call for a re-tune.

**P7. SF1 and SF7 change the same lines (from the diffs).** Both have hunks at the two `skip_quiets = true` places
(search.cpp about 2272 and 2290): they do not apply together as they are. Any build that holds both is a hand
merge, which is a new text to read (V3P_SF_COMBO_v1 and the other combined patches were not read by me). VERIFIED:
SF1's `picker.close_quiet_tail()` is an existing method of the loop's source (search.cpp:811, sets
`quiet_tail_closed_`; already called at 2481). NOT read: what the picker still hands out after that flag (the
patch's name says quiet checks), which is the whole meaning of SF1.

**P8. SF2 and SF3: nothing found in the diff text.** SF2 leaves quiet checks out of the SEE pruning; SF3 leaves
checks and promotions out of the quiescence SEE pruning (`if (!gives_check && !move.is_promotion() &&
!board.see_ge(move, -tune::QsSeeMargin)) continue;`). NOT checked: that `gives_check` is worked out in quiescence
before that line (a build would say so at once).

**What Monday's second read still owes.** The source around every hunk; SF4b2, SF5a, SF5b; the V3P patches and
`make_v3p_engine.py` (the inference code of the new net: the read that matters most); the patch applied to a COPY
of our source and built by OUR script; then the gates (perft, the build's own declared bench numbers, v3_parity
with its planted fault, net_sanity.py v2, the planted cases of P5). Match evidence decides strength, never a read.
