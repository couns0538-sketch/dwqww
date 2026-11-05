# T05 adversarial verify (start 23:20 PC clock, stop 23:45)

Format: card | claim | CONFIRMED / CORRECTED / UNVERIFIABLE / VIOLATION | evidence
Order of work: lint, licence rows, lock greps, then the 3 full cards by expected gain (T05-01, T05-03, T05-02), then
2 spot checks on the one-liner T05-04, then the notes. Edits made in cards are marked "(corrected by verify: ...)",
"(verify: ...)" or "(verify note: ...)" next to the text; no card deleted, no Status line changed (no violation found).

## Lint, licence rows, lock greps
- all | card_lint.py cards/T05/*.md | CONFIRMED (0 findings, 0 PENDING on all 4 cards; re-run clean after the verify edits) | tools/card_lint.py, 23:21 and 23:29
- licences.md | Stockfish ff7cee4244 GPL-3.0 row | CONFIRMED (re-run gives the identical row) | tools/licence_at.py official-stockfish/Stockfish ff7cee4244 --row
- licences.md | llvm-project b537630299 row (tool says MIT, hand correction to Apache-2.0 WITH LLVM-exception) | CONFIRMED (tool row identical; LICENSE.TXT and bolt/LICENSE.TXT at b53763029964 both start "The LLVM Project is under the Apache License v2.0 with LLVM Exceptions", so the hand correction is right) | gh api repos/llvm/llvm-project/contents/LICENSE.TXT?ref=b5376302...
- T05-01 | forge_has 'unique_ptr<float|/ WeightScale' = 3 hits nnue.cpp:47, :59, :61 | CONFIRMED | tools/forge_has.sh
- T05-01 | lock refresh src/nnue.cpp:84-97, update :99-157, :59 float(NnueW1) / WeightScale | CONFIRMED (WeightScale = 4096.0F at include/forge/nnue.hpp:20, so the scale is an exact 2^-12) | lock src/nnue.cpp (239 lines)
- T05-03 | forge_has 'large_page|MEM_LARGE|madvise|huge' = 0 hits | CONFIRMED | tools/forge_has.sh
- T05-02 | static_evaluate src/search.cpp:599-621, root refresh :1367, weights() src/nnue.cpp:53-68 | CONFIRMED | lock src/search.cpp (1531 lines), src/nnue.cpp
- T05-04 | lock prefetches only the child TT cluster: src/search.cpp:847, :1126 | CONFIRMED (forge_has 'prefetch' = 5 hits: search.hpp:112 comment, :125-127 TT::prefetch, search.cpp:847, :1126) | tools/forge_has.sh 'prefetch'
- T05-04 | record_move src/search.cpp:623-630, called before make_move, computes the dirty pieces | CONFIRMED (comment at 624-625, dirty_pieces at 627) | lock src/search.cpp

## T05-01 int16 first-layer store (top card by expected gain)
- T05-01 | v2p4 probe OFF 0.933, KB1 0.980, KB4 replicas 0.929, run-to-run noise ~+-3 % | CONFIRMED | D:/o30/wt/opus_30h/a/RESULTS.md:471-472
- T05-01 | bench ABBA KB4 replicas vs KB1 0.968 (CI 0.900-1.040), median 0.991 | CONFIRMED (number) | RESULTS.md:216-219
- T05-01 | premise "the post-fix probe still shows ~5 % for KB4 vs KB1" | CONFIRMED as arithmetic (0.929 / 0.980 = 0.948), but NOT significant: the source reads the 0.968 ABBA as "the table size and the king-bucket refreshes cost little; an int16 weight store ... is not worth a re-proof" (RESULTS.md:218-219) and the post-fix probe as "the v2 path now runs at its own exe's OFF speed" (RESULTS.md:471-472); 0.948 is the ratio of two single runs of ~+-3 % each and the ABBA CI includes 1.0 -> verify note added in the card's Expected gain | RESULTS.md:216-219, :467-473
- T05-01 | the 30-h job dropped int16 because the lazy root explained the in-game loss | CONFIRMED ("prepared and exact, not built, not needed - the speed loss was the lazy root, not the table size") | D:/o30/FINAL_REPORT.md:508-509
- T05-01 | lock net max |w1| 14,227 (3.47), max |b1| 6,764, per-unit |b1| + 32 largest |w1| up to 342,331 (83.6), over 32,767 on all 256 units, below 2^24 | CONFIRMED (recomputed read-only from the lock's src/nnue_weights.inc: max 342,331, min 60,586, 256 / 256 units over 32,767) | own recompute, scratchpad script, 23:24
- T05-01 | any int16 file: 33 x 32,768 < 2^24 | CONFIRMED (1,081,344 < 16,777,216) | arithmetic
- T05-01 | sizes: KB4 3.1 MB -> 1.57 MB, one bucket 393 KB, KB32 25 -> 12.6 MB, lock 786 -> 393 KB | CONFIRMED (4 x 768 x 256 x 4 B = 3,145,728 B etc.) | arithmetic
- T05-01 | Zen 5 L2 1 MB per core, 16-way | CONFIRMED by secondary sources only (web search 23:28: Wikipedia Zen 5, Hot Chips 2024 coverage; the deck itself not opened) | https://en.wikipedia.org/wiki/Zen_5
- T05-01 | v2port: AlignedFloats w1 [KB][768][256], column(), apply_columns, refresh_cached | CONFIRMED | D:/o30/wt/opus_30h/a/v2port.patch:80-97, :127, :164, :192, :215
- T05-01 | script o30_v2int16.py exists, never built | CONFIRMED (8,577 B, 2026-11-04 08:20; FINAL_REPORT:716-720 "never built") | D:/o30/wt/opus_30h/a/o30_v2int16.py
- T05-01 | packed ON benches n2L 292397 / 836621 / 2200750 | CONFIRMED | FINAL_REPORT.md:556, RESULTS.md:361
- T05-01 | Forge estimate labelled UNPROVEN | CONFIRMED | card Expected gain

## T05-03 large pages for v2 tables (second card)
- T05-03 | Stockfish PR 6359: ~1.2 % nps, 20 runs (288,644,510 -> 292,082,422), "large machine" | CONFIRMED (+1.19 %) | gh api repos/official-stockfish/Stockfish/pulls/6359 (PR text)
- T05-03 | 6359 STC SPRT [0, 2] passed, LLR 2.95, 166,272 games, W 43479 L 42993 D 79800, ~+1.0 Elo computed | CONFIRMED (score 0.50146 -> +1.02 Elo); test conditions not in the card -> added: 10+0.1, Threads 1, UHO_Lichess_4852_v1.epd, bounds in normalized Elo | https://tests.stockfishchess.org/tests/view/68e9f3c0d323fd15c04e3ba4 (api/get_run)
- T05-03 | 6359 "with 28 MB worker data only +0.3 % (noise)" (sources.md no. 6) | CONFIRMED (291,035,351 -> 291,937,367 = +0.31 %) | PR 6359 text
- T05-03 | Stockfish PR 7041: +1.04 % nps over 200 runs, paired t 3.415, p 0.0008; +1.76 % over 50 runs; needs THP madvise | CONFIRMED | gh api .../pulls/7041 (PR text)
- T05-03 | 7041 STC [0, 2] passed, LLR 3.42, 231,360 games, W 60152 L 59553, ~+0.9 Elo computed | CONFIRMED (D 111655; score 0.50129 -> +0.90 Elo; 10+0.1, Threads 1, UHO_Lichess_4852_v1.epd, nElo bounds; added to the card) | https://tests.stockfishchess.org/tests/view/6a736a122cf557d58a2e1f51 (api/get_run)
- T05-03 | own S1: x1.011-1.016 at Hash 64, x1.027-1.032 at Hash 256 | CONFIRMED (geometric means B/A recomputed from the CSVs: t2 1.0114 / 1.0304 (20 + 20 runs), t4 1.0109 / 1.0272 (20 + 20), t4r 1.0155 / 1.0319 (only 6 + 6), t3retest 1.0127 (4 + 4); the upper ends come from the small t4r run) | C:/Users/Administrator/grok-pc/forge_push/qa_s1lp_20261031/abba_t2.csv, abba_t4.csv, abba_t4r.csv, abba_t3retest.csv
- T05-03 | S1 backs the TT and the compiled-in w1 only; written from the Win32 API documentation | CONFIRMED ("ON: large pages are used for the TT ... and for the lock's own net weights ... b1 and w2 ... are not moved"; "Windows code is our own, written from the [platform] docs only") | qa_s1lp_20261031/FORGE_S1_LARGEPAGES_SRC.zip README.md
- T05-03 | v2 tables by aligned operator new (64 B), refresh caches by std::vector | CONFIRMED | v2port.patch:88 (operator new, align_val_t{64}), :110-116 (RefreshCache std::vector<Entry>)
- T05-03 | 4-KiB pages: KB4 768, KB8 1,536, KB16 3,072, KB32 6,144 | CONFIRMED | arithmetic
- T05-03 | "On 2-MiB pages the KB32 table needs 13 entries" | CORRECTED (25,165,824 B = exactly 12 x 2 MiB; 12 when the block is 2 MiB-aligned as S1's large-page blocks are, 13 only if it straddles a boundary) | arithmetic + S1 README ("Large-page memory is page aligned (2 MiB or more)")
- T05-03 | Zen 5 L1 DTLB 96 entries (fully associative, all page sizes), L2 DTLB 4K entries (Zen 4: 72 / 3,072) | CONFIRMED by secondary sources only (web search 23:28; the deck itself not opened by the worker or by verify) | https://en.wikipedia.org/wiki/Zen_5 , https://wccftech.com/amd-zen-5-core-architecture-breakdown-hot-chips-new-chapter-high-performance-computing/
- T05-03 | Forge estimate labelled UNPROVEN | CONFIRMED | card Expected gain

## T05-02 one hot eval path (third card)
- T05-02 | kit v2.3 0.71x, v2.4 -PartialTraining 0.959x, v2.5 ~1.0x on the bench | CONFIRMED (0.710 CI 0.680-0.741; 0.959 CI 0.929-0.990; v2.5 1.066 CI 0.987-1.152, median 1.085, written "~1.0x" in FINAL_REPORT:537) | RESULTS.md:85-88, FINAL_REPORT.md:537
- T05-02 | kit v2.5 OFF vs lock 0.964 (CI 0.942-0.986); without noinline 0.875 before the root fix | CONFIRMED | RESULTS.md:449-450
- T05-02 | v2p4 game positions OFF 0.933, KB1 0.980 | CONFIRMED | RESULTS.md:471
- T05-02 | BOLT README line 12 "BOLT operates on X86-64 and AArch64 ELF binaries" at b53763029964 (2026-10-20) | CONFIRMED (line 12 verbatim; commit date 2026-10-20T18:51:57Z) | https://github.com/llvm/llvm-project/blob/b53763029964ff42b806ede881612fc391344327/bolt/README.md (Apache-2.0 WITH LLVM-exception, README only)
- T05-02 | skill forge-ltopgo-pgo: MSYS2 g++ 15.2.0, -flto=1 -fprofile-generate / -fprofile-use, workload v1 never runs an option-only path | CONFIRMED (skill lines 22, 31-33, 44) | skill forge-ltopgo-pgo SKILL.md
- T05-02 | v2port: static_evaluate_v2 with section(".text.forge_v2"), noinline; [[unlikely]] branch at the top of static_evaluate; root branch | CONFIRMED | v2port.patch:589, :666, :678-681
- T05-02 | BH-8 per-file effect up to ~5 % | CONFIRMED ("may carry up to ~5 %"; byte copies differ by up to +-2.8 % in R5B) | FINAL_REPORT.md:836
- T05-02 | lock net as v2 gives the lock pins d11-d22 | CONFIRMED for KB4 replicas (RESULTS.md:469-470); the KB1 / OB1 and KB1 / OB8 cases not re-opened in the time box | RESULTS.md:469-470
- T05-02 | Forge estimate labelled UNPROVEN | CONFIRMED | card Expected gain

## T05-04 (one-liner, 2 spot checks)
- T05-04 | prefetch only at the child TT (search.cpp:847, :1126) and record_move at 623-630 | CONFIRMED (both, see the lock greps above) | tools/forge_has.sh
- T05-04 | Stockfish PR 7025 title "Prefetch continuation correction histories" (title only) | CONFIRMED (closed 2026-08-10) | gh api .../pulls/7025 (title)
- T05-04 | objdump: 2 prefetch sites in the lock exe, 3 in v2p4 | UNVERIFIABLE in the time box (exes not disassembled by verify) | -

## Notes (SPEED_LIST, V2P4_GAP, sources)
- SPEED_LIST | VPDPBUSD zmm: Zen 5 latency 3, TP 0.50, 1 uop FP01; Zen 4 latency 4, measured TP 1.00 (computed 0.50) | CONFIRMED | https://uops.info/html-instr/VPDPBUSD_ZMM_ZMM_ZMM.html
- SPEED_LIST | VPCOMPRESSD m512{k}: Zen 5 8 uops, TP 3.00 / 1.00, latency <= 46 / <= 19 / <= 18; Zen 4 144 uops, TP 72.50; Intel 4 uops, TP 2.00 | CONFIRMED | https://uops.info/html-instr/VPCOMPRESSD_M512_K_ZMM.html
- SPEED_LIST | VPCOMPRESSD register form and Agner's Zen 5 rows | UNVERIFIABLE in the time box (not re-opened) | -
- V2P4_GAP | Y8 0.8926 (CI 0.8842-0.9011, depth -0.318 SE 0.093); Z32 0.8487 (CI 0.8405-0.8571, depth -0.465 SE 0.095) | CONFIRMED | D:/o30/wt/opus_30h/a/logs/checks_gpu_w2/speed_vs_lockexe_*.txt lines 4-5
- V2P4_GAP | layout KB8 0.988, KB16 0.969, KB32 0.942 (3-4 runs, vs KB4) | CONFIRMED | FINAL_REPORT.md:287-289
- V2P4_GAP | product check 0.918 / 0.875 (probe P2) and 0.937 / 0.894 (bench P2); P4 0.972 / 0.970 / 0.952 / 0.950 | CONFIRMED (arithmetic) | own recompute
- V2P4_GAP | "measured parts explain about 60-80 % of the gap" | CONFIRMED approximately (Y8 77 % / 59 %, Z32 83 % / 70 %; the Z32 probe-P2 share is a little above 80 %) | own recompute
- V2P4_GAP | P2 = 0.948 as a measured part | CONFIRMED as arithmetic, NOT significant (see T05-01 above); P4 would grow to ~0.95 with the bench P2 - the note already gives both | RESULTS.md:216-219, :471
- sources.md | PRs 6359 / 7041 "merged 2025-10-14 / 2026-08-10" | UNVERIFIABLE as "merged" (the API shows closed on exactly those dates with merged_at null; the project usually lands PRs by direct push) | gh api .../pulls/6359, /7041

## Reading rule, constants, names
- all T05 cards and notes | links to source files of GPL / AGPL / unlicensed repos | none found (the only /blob/ link is llvm-project bolt/README.md: Apache-2.0, README) -> no VIOLATION | grep of every URL in cards/T05 and notes/T05
- all | Stockfish read as PR text and fishtest pages only; no pasted / paraphrased code; no other engine's tuned constants proposed as Forge values | CONFIRMED (the Stockfish nps / Elo figures appear only as source numbers; all Forge ranges are own) | cards T05-01..04, SPEED_LIST rows 3, 6
- all | no AI vendor / model-company names | CONFIRMED (card_lint clean on cards; on notes no name finding, only card-format findings that do not apply to notes; "grok" only in grok-pc paths; the only other hit is the job's own folder / branch names in local paths, accepted by the job's linter) | tools/card_lint.py
- all | every Forge-side estimate labelled UNPROVEN | CONFIRMED (4 / 4 cards; SPEED_LIST header "every estimate UNPROVEN"; V2P4_GAP holds records only, labelled advisory) | cards, notes

## Counts
Checked 58 (one line each above), confirmed 54 (of which 2 carry a significance caveat - T05-01 premise, V2P4_GAP P2 - and
1 is partial - T05-02 pins, KB4 case only), corrected 1 (T05-03 2-MiB entries: 12, not 13, when aligned), unverifiable 3
(T05-04 objdump counts, SPEED_LIST register-form / Agner rows, "merged" wording in sources.md), violations 0.
Card edits: T05-03 correction + fishtest conditions (10+0.1, Threads 1, UHO_Lichess_4852_v1, nElo bounds) added;
T05-01 verify note on the premise. Lint clean (cards/T05/*.md, 0 findings, re-run after the edits). Written 23:31.
