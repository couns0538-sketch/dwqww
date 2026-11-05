# T04 adversarial verify (23:15-23:25 PC clock; one line per check: card | claim | verdict | evidence)

## 1. Source numbers (top 3 full cards; 2 one-line cards spot-checked)
- T04-01 | Caissa 1b7a871: +4.20 +- 2.23, 10+0.1, Threads=1, Hash 16 MB, SPRT [0,2], LLR 2.94, N 25044 (W 5993 L 5690 D 13361), single block (no LTC) | CONFIRMED | https://github.com/Witek902/Caissa/commit/1b7a871236e20d85fd193f07bb2a62dceb2f9e35 (gh api commit message; committer date 2025-12-29, author 2025-12-28)
- T04-01 | Caissa 6ec347d: +4.03 +- 2.19, 10+0.1, N 26636 | CONFIRMED | https://github.com/Witek902/Caissa/commit/6ec347da2fe5f60d639bab19e2c680a2ae24a391
- T04-01 | caveat: 47604ad "null move only in cut nodes" dated 2025-08-04, before 1b7a871 | CONFIRMED (committer 2025-08-04, its own gain +1.07 +- 0.86 STC n=168198) | https://github.com/Witek902/Caissa/commit/47604ad4437496bf5b83075a8f980b9c3dd92173
- T04-02 | Caissa 434bbda STC 10+0.1 N 14696 +6.93 +- 3.88 LLR 2.96 [0,2]; LTC 40+0.4 N 18914 +5.14 +- 3.35 LLR 2.95 [0,2]; 2024-01-03 | CONFIRMED (message also says "Idea from Stockfish"; idea-level only, no SF source involved) | https://github.com/Witek902/Caissa/commit/434bbda5c342501ac5de4ecb6934e85151a225fe
- T04-02 | Patricia PR 137: 8+0.08, Hash 16 MB, [0,3], N 14514 (W 2978 L 2746 D 8790) +5.55 +- 3.25 LLR 2.95, merged 2025-01-26, merge aa32588b, test 9584 | CONFIRMED | https://github.com/Adam-Kulju/Patricia/pull/137
- T04-02 | Caissa 105979c no deeper at root: +2.37 +- 1.59, 10+0.1, N 50298 | CONFIRMED | https://github.com/Witek902/Caissa/commit/105979c077840ced14e5b551707036b8588050f3
- T04-03 | Caissa e53fe6e LTC 60+0.6 Hash 128 MB [0,3] N 10918 (W 2568 L 2381 D 5969) +5.95 +- 3.14 LLR 2.95, test 6982; STC 10+0.1 Hash 16 MB [0,2] N 61474 (W 14682 L 14329 D 32463) +2.00 +- 1.41 LLR 2.95 | CONFIRMED (STC test link is https://furybench.com/test/6974/) | https://github.com/Witek902/Caissa/commit/e53fe6ebf2a48af382fd5d3355e36e3ef63aa173
- T04-03 | commit date "2025-08-05" | CORRECTED -> 2026-08-05 (committer; author 2026-08-04) | same commit page
- T04-06 (spot) | Patricia PR 147: 60+0.6 [0,3] N 24804 +3.12 +- 2.14 LLR 2.96 | CONFIRMED (Hash 128 MB, test 9933, merged 2025-02-23) | https://github.com/Adam-Kulju/Patricia/pull/147
- T04-06 (spot) | Caissa f2967c1: 80+0.8 [0,2.5] N 25260 +3.36 +- 2.07 LLR 2.97 | CONFIRMED (Hash 128 MB) | https://github.com/Witek902/Caissa/commit/f2967c12d1275a8be7b481659d036108270aad95
- T04-04 (spot) | Altair PR 189 minor: 8+0.08, 1 thread, [0,4], +7.74 +- 5.71, N 7008, LLR 2.94 | CONFIRMED (Hash 32 MB, merged 2024-10-13) | https://github.com/Alex2262/AltairChessEngine/pull/189
- T04-04 (spot) | Altair PR 188 major: +6.84 +- 5.23, N 8280, LLR 2.93, [0,4] | CONFIRMED | https://github.com/Alex2262/AltairChessEngine/pull/188
- T04-05 (extra) | Caissa 54aef4a: 10+0.1 [0,2] N 44298 (W 10682 L 10347 D 23269) +2.63 +- 1.68 LLR 2.97 | CONFIRMED | https://github.com/Witek902/Caissa/commit/54aef4aa8a5c20637425dde6850e235c509bc273
- all | W+L+D sums equal N on every quoted block (25044, 14514, 10918, 61474, 44298) | CONFIRMED | arithmetic

## 3. Licence rows (tools/licence_at.py --row re-run 23:16-23:17 PC clock)
- licences.md | Caissa 57cae7ef71 MIT; Patricia 67d83d7056 MIT; Altair b2447b825b MIT; Stockfish ff7cee4244 GPL-3.0 (Copying.txt) | CONFIRMED (all four rows byte-identical to the re-run) | tools/licence_at.py

- licences | LICENSE at the oldest commit whose diff was read: Caissa 434bbda5c3 MIT, Patricia bf655244b6 (PR 134 merge) MIT, Altair 6bddce6de2 MIT; each LICENSE file touched by one commit only (created 2021-10-25 / 2024-01-07 / 2023-05-28), so MIT at every commit read | CONFIRMED (rows appended to licences.md) | tools/licence_at.py; gh api commits?path=LICENSE

## 4. Forge has it (tools/forge_has.sh re-run + sed of the cited lines, lock src_al1s198_clean, search.cpp 1,531 lines)
- T04-01 | 'singular_score = search' -> search.cpp:1095 passes cut_node; :1141 `if (cut_node) r += 2` | CONFIRMED | lock search.cpp:1095, :1141
- T04-02 | 'full_depth_needed' -> 1136-1159 (5 hits); `const int new_depth` at :1117; re-search at fixed new_depth (:1151, :1160) | CONFIRMED | lock search.cpp:1117, :1136-1160
- T04-03 | 'cutoff_count' -> :905 clear of (ss+1), :1145 LMR use, :1180 increment (+ include/forge/search.hpp:273 field); NMP condition at :965 `eval >= beta && ss->static_eval >= beta - 24 * depth + 180`; null_tries_/null_cutoffs_ exist (:969, :985, :995) | CONFIRMED | lock search.cpp:905, :965, :1145, :1180
- T04-05 | lock skips every capture best move in the corr update | CONFIRMED | lock search.cpp:1219 `(best_move.is_none() || !best_move.is_capture())`
- T04-04 | lock corr keys = pawn + material only | CONFIRMED | lock search.cpp:640-655

## 1b. Local records cited by the cards (re-read)
- T04-01/02/03 | gate rate "about 1,000 games/h at concurrency 8 (R7 J4, 28.3 s per STC game)" | CONFIRMED | R7 status record (memory opus-r7-speed-status, line 23: "running gate 996-1002 games/h at conc 8; games are TC-bound (28.3 s)")
- T04-01 | tried gates `--grep 'singular|cutnode'` = 0 rows | CONFIRMED (0 of 110) | tools/tried_gates.py on C:/Users/Administrator/grok-pc/forge_push/FORGE_RESULTS.csv
- T04-02 | tried gates `--grep 'deeper|shallow'` = 4 rows, packd Hindsight gates 51-54, -6.3 to +4.6, 1,500 games each | CONFIRMED (-6.25 / -3.01 / +0.93 / +4.63, all "Cap with no decision") | tools/tried_gates.py
- T04-03 | tried gates `--grep 'nmp|null'` = 0 rows | CONFIRMED | tools/tried_gates.py
- T04-04 | R5A-1 CorrHistPlus=4 +4.17 and UR5A1 +1.27, 3,000 games each, no decision; no FORGE_RESULTS row for R5A-4 | CONFIRMED (grep 'R5A' shows only R5A-1/-2, UR5A1/2) | tools/tried_gates.py; R5A status record line 16 lists "4 CorrHistPlus=2"
- T04-04 | CorrHistPlus bit 2 = minor-piece key (knights, bishops, kings), bit 4 = non-pawn, bit 1 = continuation; no major key anywhere | CONFIRMED | F:/opus_scratch/r5/r5b/flake/base_src/include/forge/correction_plus.hpp:9-12, :31-33; `forge_has.sh 'major'` = 0 hits in the lock
- T04-01/T04-06 | SingularV2 (triple / PV double, multicut on the singular score, deeper negative extensions) prepared, never gated; idea not in R15 C1-C6 / x1 / x2b | CONFIRMED | D:/o15/FINAL_REPORT.md:194-196; D:/o15/cands/INDEX.md has no singular / non-cut entry
- hand-back dead end | fail-firm RFP = gate 86 RfpReturnBlend=25, -16.42, H0 | CONFIRMED (868 games) | tools/tried_gates.py --grep RfpReturn

- T04-02 / T04-03 | idea not among FB2-J3 options (CorrHistV2, SingularV2, LmrTableV2, TtPruneV2) | CONFIRMED | skill forge-fb2-workflow, section "J3 (fable-fb2-j3): search options"

## 1c. Lock-source details inside the cards
- T04-06 | "double capped at 6 per path" | CORRECTED (a double is allowed while at most 6 are inherited, so at most 7 per path) | lock search.cpp:883, :1102, :1116; note added in the card
- T04-01 | node-type flip: reduced children always searched as cut nodes, full-depth re-searches as `!cut_node` | CONFIRMED | lock search.cpp:1148, :1151, :1160
- T04-03 | (ss+1)->cutoff_count is 0 whenever null move runs (cleared at :905, nothing searched at ss+1 before :965) | CONFIRMED | lock search.cpp:905-965
- T04-03 | Caissa mechanism: clear counter two plies ahead, read (node+1) counter at NMP, threshold lowered | CONFIRMED (diff: `(node + 2)->cutoffCount = 0`, `(node + 1)->cutoffCount < NmpCutoffCountMin`) | e53fe6e diff (MIT)
- T04-03 | transfer: Caissa lowers the margin of `eval >= beta + margin` (can go below beta); the card lowers only the lock's `static_eval` term and keeps `eval >= beta` | CORRECTED (narrower change than the source; verify note added in the card) | e53fe6e diff vs lock search.cpp:965
- T04-03 | "a TC-scaling term" / "3x larger at LTC" | CORRECTED (point estimates 5.95 vs 2.00 are right; 95 % intervals overlap, 2.81-9.09 vs 0.59-3.41, and both are SPRT-stopped estimates, biased up; verify note added) | e53fe6e message
- T04-06 | Caissa f2967c1 is a bundle: triple step + removal of its per-path double-extension limit + PV nodes eligible with a large extra margin; Patricia PR 147 triples non-captures only | CORRECTED (verify note added in the card) | f2967c1 diff, Patricia PR 147 files (both MIT)
- T04-01 | rationale "verification is shallower, so the hash move is called singular more often" | UNVERIFIABLE (the Caissa commit message gives no rationale; it is the card's own reasoning; the test plan's "source reasoning" means the same; verify note added) | 1b7a871 message
- T04-02 | Caissa diff: deeper if reduced score > best + const, shallower if < best + newDepth, PV re-search uses the adjusted depth | CONFIRMED | 434bbda diff (MIT)

## 2. Reading rule and constants
- all T04 files | no /blob/, /tree/, /raw/ or raw.githubusercontent link; repos linked: Caissa 36, Patricia 14, Altair 13 (all MIT), Stockfish 11 (all /commit/ pages) | CONFIRMED (no violation) | grep of cards/T04 + notes/T04
- Stockfish (GPL-3.0) | only commit messages used; spot check b261df9 "Fix majorPieceKey Updates": STC passed <0,2> N 476160, LTC failed yellow <0.5,2.5> N 230634, then passed non-regression LTC | CONFIRMED (the "+0.71" in BUG_CHECKLIST row 3 / TABLE C is derived from the message's W/L/D: 0.71; message read with --jq .commit.message only, no diff) | https://github.com/official-stockfish/Stockfish/commit/b261df970d
- Stockfish rows | tools/mine_commits.py reads only the commits list API (`repos/{repo}/commits`, messages, no `.files` / patch) and --show reads the cached list, so no GPL diff was fetched | CONFIRMED | tools/mine_commits.py:13, :36
- nnue-pytorch | not cited anywhere in T04 | CONFIRMED | grep
- no pasted / paraphrased GPL code | BUG_CHECKLIST Stockfish rows describe symptoms + box tests from commit messages; identifiers only (majorPieceKey, MAX_PLY) | CONFIRMED | notes/T04/BUG_CHECKLIST.md rows 3, 9, 11, 13, 14, 16, 18, 19, 21
- T04-02 | own starts LmrDeeperMargin 70, LmrShallowerMargin 10 vs sources (Caissa deeper 80, shallower depth-dependent; Patricia deeper 60 + 2 x depth) | CONFIRMED not a copy (70 lies between the two sources; crew may prefer a Forge-derived start) | 434bbda diff, Patricia PR 137 files (MIT)
- T04-02 vs TABLE.md row 1 | deeper range 0-200 cp (card) vs 30-150 cp (TABLE) | CORRECTED (inconsistent; verify note added in the card, TABLE not changed) | cards/T04/T04-02 vs notes/T04/TABLE.md:12
- T04-03 | own starts NmpFewCutoffs 3 (1-6), discount 24 cp (0-72) vs Caissa NmpCutoffCountMin 2 (1-4), bonus 19 (0-60) | CONFIRMED not a copy | e53fe6e diff (MIT)
- TABLE.md row 6 | TripleExtExtra 60 cp below the double threshold vs Caissa triple margin 50, Patricia 125 below sBeta | CONFIRMED not a copy | f2967c1 diff, Patricia PR 147 files (MIT)
- TABLE.md row 7 | picker threshold clamp(capture history / 64, +-150) | UNVERIFIABLE in this pass (Patricia PR 209 patch not searched far enough to compare; MIT, so a copy would need notice, not a violation of the reading rule) | https://github.com/Adam-Kulju/Patricia/pull/209

## 5. Labels and lint
- cards/T04/*.md | card_lint.py exit 0, 0 findings, 0 PENDING (before and after the verify edits) | CONFIRMED | tools/card_lint.py
- every card | Forge estimate labelled UNPROVEN (one per card); TABLE.md states "Forge estimates are UNPROVEN" globally; no Forge Elo claim found in TABLE / BUG_CHECKLIST | CONFIRMED | grep
- vendor / model-company names | none in cards/T04 or notes/T04 (lint's list); T04-06 names the local branch fable-fb2-j3 (a branch name, passes lint) | CONFIRMED | tools/card_lint.py + grep
- hand-back summary | "top picks by Elo per build-hour are T04-02, T04-01 and T04-03" | CORRECTED (hand-back wording only, no file changed: TABLE.md ranks T04-05 3rd and T04-03 5th by that metric; T04-03 is a top pick by LTC gain, not by Elo per build-hour) | notes/T04/TABLE.md:12-16

## 6. Extra rows of TABLE.md re-opened (not tied to a card)
- TABLE A4 | Caissa d39fcfb TT cutoff needs higher depth: 40+0.4 Hash 64 MB [0,2.5] N 48018 +2.11 +- 1.55 LLR 2.95, no STC block | CONFIRMED (message also says "Idea from Stockfish/Obsidian": idea-level only) | https://github.com/Witek902/Caissa/commit/d39fcfb0d6
- TABLE C | Caissa 74a0957 history 50 -> 75 %: 8+0.08 +4.34 +- 2.27 passed; N=25000 +4.42 passed; 40+0.4 +0.81 +- 2.21 LLR 0.36 [-0.5,2.5] not passed | CONFIRMED | https://github.com/Witek902/Caissa/commit/74a0957f0b

## Scope
Re-opened: every source number of T04-01/02/03, T04-04 and T04-06 (spot), T04-05 (extra), TABLE A4 and one TABLE C
row, Stockfish b261df9. Not re-opened in this pass: the other TABLE.md / BUG_CHECKLIST.md rows not tied to a card
(e.g. 60b6639, 836ffcf, Altair PR 176 / 196, Patricia PR 209 / 155, BUG_CHECKLIST fix commits). Card edits use
"(corrected by verify: ...)" for wrong facts (T04-03 date, T04-06 cap) and "(verify note: ...)" for added
qualifications (T04-01, T04-02, T04-03, T04-06); no card deleted, no Status line changed (no violation found).
