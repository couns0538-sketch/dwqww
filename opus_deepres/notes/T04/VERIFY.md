# T04 adversarial verify (started 23:15 PC clock; one line per check: card | claim | verdict | evidence)

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

## 4. Forge has it (tools/forge_has.sh re-run + sed of the cited lines, lock src_al1s198_clean, search.cpp 1,531 lines)
- T04-01 | 'singular_score = search' -> search.cpp:1095 passes cut_node; :1141 `if (cut_node) r += 2` | CONFIRMED | lock search.cpp:1095, :1141
- T04-02 | 'full_depth_needed' -> 1136-1159 (5 hits); `const int new_depth` at :1117; re-search at fixed new_depth (:1151, :1160) | CONFIRMED | lock search.cpp:1117, :1136-1160
- T04-03 | 'cutoff_count' -> :905 clear of (ss+1), :1145 LMR use, :1180 increment (+ include/forge/search.hpp:273 field); NMP condition at :965 `eval >= beta && ss->static_eval >= beta - 24 * depth + 180`; null_tries_/null_cutoffs_ exist (:969, :985, :995) | CONFIRMED | lock search.cpp:905, :965, :1145, :1180
- T04-05 | lock skips every capture best move in the corr update | CONFIRMED | lock search.cpp:1219 `(best_move.is_none() || !best_move.is_capture())`
- T04-04 | lock corr keys = pawn + material only | CONFIRMED | lock search.cpp:640-655
