# T04D verify (adversarial pass, start 00:33, stop by 00:53 PC clock)

Method: every cited fishtest run re-fetched fresh from `api/get_run/<id>` into F:/odr/work/T04D-verify/ (14 records)
and recomputed (TC, book, threads, normalized bounds, LLR, Elo +- 95 % from the pentanomial, own script py/pent.py);
the 7 commit messages and 7 PR bodies re-read through `gh api` with a `--jq` filter that returns the message text
only (no diff, no file list, no source: the reading rule holds); the licence row re-run; every cited lock line
re-read in `src_al1s198_clean`; `tools/forge_has.sh` and `tools/tried_gates.py` re-run; our own prior code
(packb ReSearchAdjust / FiftyDamp, packa, E3, Sf26Bundle bits, R15 C1-C6 / x1 / x2b) checked for a duplicate;
all 51 other cards and the T04 / T04B / T04C tables grepped; the vendor filter run over all 8 T04D files.

| card | claim | verdict | evidence |
|---|---|---|---|
| T04D-01 | STC run 67abc9aa: 10+0.1, UHO_Lichess_4852_v1, 1 thread, [0,2] normalized, LLR 2.93, n=42,304, W/L/D 11,223/10,892/20,189, Ptnml 184/4,904/10,669/5,187/208 = +2.72 +- 1.74 | CONFIRMED | fresh API record, recomputed +2.72 +- 1.74 |
| T04D-01 | LTC run 67abcd7b: 60+0.6, same book, [0.5,2.5], LLR 2.95, n=32,334, W/L/D 8,386/8,074/15,874, Ptnml 26/3,446/8,916/3,748/31 = +3.35 +- 1.81 | CONFIRMED | recomputed +3.35 +- 1.81 |
| T04D-01 | commit 9cc15b3 "Do more reductions for cut nodes without a tt move", PR 5875, date 2025-02-13, quote "is in general good" | CONFIRMED | commit message and PR body re-read; 02-13 is the committer date (author date 02-11) |
| T04D-01 | Mechanism: "one extra ply" and "the node was never searched well, so its late moves matter less" presented as the commit's text | CORRECTED | the commit says only "do more reductions" and "somewhat similar to IIR": no amount, no rationale; marked as own reading in the card |
| T04D-01 | "the logged LTC result is indeed above the STC one" | CORRECTED (wording) | +3.35 +- 1.81 vs +2.72 +- 1.74: inside the error bars, no scaling shown; softened in the card |
| T04D-01 | lock `:1141` flat `if (cut_node) r += 2;`, `:1031` IIR for pv/cut nodes without a TT move at depth >= IirDepth, `:913` tt_move, `:1147` clamp [1, new_depth] | CONFIRMED | lines re-read; `forge_has.sh 'cut_node\) r\|tt_move.is_none\(\) && \(pv_node'` = the same 2 hits |
| T04D-01 | not in Sf26Bundle (bit 4 = LMR ply for a static-eval gap below alpha), not R15 C4 (IirShallowTt), no tried LMR gate on cut nodes | CONFIRMED | sf26bundle_v22_pc1 src_copy search.cpp:65-75 bit list re-read; D:/o15/cands/INDEX.md C1-C6 = PruneLmrHist, QsMovePrune, TtProbcut, IirShallowTt, ContHistSplit, LowPlyHist; `tried_gates.py --grep cut` = 0 rows, `--grep lmr` = LmrCorrThreshold / LmrTtCapAll / LmrCapVictim only |
| T04D-01 | "not in TtPruneV2 (its IIR rule is for an upper-bound TT move)" | UNVERIFIABLE | TtPruneV2 (R13 B1 micro-bundle) source not re-read in the time box |
| T04D-01 | own start 1 (range 0-2) for CutNoTtLmr | CONFIRMED (as own) | the source text names no amount; nothing copied |
| T04D-02 | 43e100a STC 6726357b: 10+0.1, UHO, 1 thread, [0,2], LLR 2.93, n=41,184, Ptnml 131/4,728/10,554/5,046/133 = +2.72 +- 1.72 | CONFIRMED | recomputed +2.72 +- 1.72 |
| T04D-02 | 43e100a LTC 6727326a: 60+0.6, [0.5,2.5], LLR 2.94, n=270,888, Ptnml 180/29,385/75,485/30,246/148 = +1.02 +- 0.62 | CONFIRMED | recomputed +1.02 +- 0.62 |
| T04D-02 | a4edacb STC 67ab396a: [0,2], LLR 2.96, n=83,648 = +1.63 +- 1.23; LTC 67ab9647: [0.5,2.5], LLR 2.94, n=68,160 = +1.96 +- 1.25 | CONFIRMED | recomputed +1.63 +- 1.23 and +1.96 +- 1.25; both 1 thread, UHO |
| T04D-02 | commit dates 2024-11-13 / 2025-02-13, PR 5670 text "allow TT cutoffs only if cutNode matches previous TT results", PR 5876 "no text beyond the logs" | CONFIRMED | committer dates 2024-11-13 / 2025-02-13; PR bodies re-read (5876 body = logs only) |
| T04D-02 | Mechanism: two-sided rule (fail high only at cut nodes AND fail low only at all nodes) presented as the source's | CORRECTED | the commit text states only the fail-high half ("fail high with TT only when expected cutnode"); the PR text "matches previous TT results" is ambiguous; the fail-low half is marked as the card's own reading / design |
| T04D-02 | lock `:921-926` TT cutoff with no node-type term, `cut_node` a parameter at `:875` | CONFIRMED | lines re-read; `forge_has.sh 'tt_depth >= depth &&'` = 1 hit at :921 |
| T04D-02 | T04 TABLE A4 = Caissa d39fcfb, 40+0.4 +2.11, no card; R15 x1 TtCutoffHistory and C3 TtProbcut do not touch the condition; no tried gate on the TT cutoff condition | CONFIRMED | notes/T04/TABLE.md row 4 re-read (+2.11 +- 1.55 n=48,018); INDEX.md x1 = "quiet TT move of a TT cutoff gets the history bonus"; `tried_gates.py --grep tt` = R7TtExclusive, LmrTtCapAll only |
| T04D-02 | b280d2f (notes/T04D/TABLE.md) "kept the strictly-deeper requirement for fail highs" | UNVERIFIABLE | that message was not re-fetched in the time box |
| T04D-02 | "TtPruneV2 has no TT-cutoff rule"; own start 6 (range 0-14) for TtCutNodeDepth | UNVERIFIABLE / CONFIRMED (as own) | TtPruneV2 source not re-read; the source's depth limit cannot be checked without reading its source (forbidden), the card states 6 as its own |
| T04D-03 | a016abd STC 6794c463 +3.78 +- 2.09 n=28,096 [0,2] LLR 2.95; LTC 6794ea13 +2.18 +- 1.35 n=58,086 [0.5,2.5] LLR 2.95; 1 thread, UHO | CONFIRMED | recomputed from the fresh records; commit message / PR 5823 title match |
| T04D-03 | DUPLICATE of T04E-03 (also T04C-04 / T04G-03), merged into TABLE.md row 5 | DUPLICATE (already handled) | cards/T04E/T04E-03-decaying-quiet-malus.md exists; T04C-04 and T04G-03 are MERGED markers of the same idea; TABLE.md row 5 holds the full row; the marker had no Status line, one added (MUST clause), file stays |
| T04D-04 | ced9f69 STC 694e33ff +1.29 +- 1.02 n=115,520 [0,2] LLR 2.93; LTC 6950cbe6 +2.00 +- 1.26 n=63,672 [0.5,2.5] LLR 2.95; 1 thread, UHO | CONFIRMED | recomputed from the fresh records |
| T04D-04 | commit text: main history scaled to 3/4 at the start of the ID loop, partial refresh at every new root; PR 6504 | CONFIRMED | commit message and PR body re-read |
| T04D-04 | lock: main history reset only in `Worker::clear` :575-577 via `Searcher::clear` :1493-1495 on ucinewgame (`uci.cpp:188`); bench clears the searcher before every position (`uci.cpp:401`), so the ON bench equals the pins | CONFIRMED | lines re-read; `bench_searcher.clear()` is inside the per-FEN loop; holds when the scaling runs once per `go` (not per ID iteration) |
| T04D-04 | T04 TABLE B row "history kept between moves ... already at the end of that trend" and Caissa 74a0957 50 -> 75 % STC pass / LTC not passed | CONFIRMED | notes/T04/TABLE.md lines 46 and 58 re-read |
| T04D-04 | own start 80 % (range 50-100) for MainHistKeepPct | CONFIRMED (as own) | differs from the source's 3/4 |
| T04D-05 | 836154a STC 6699d256 +1.62 +- 1.22 n=83,104 [0,2] LLR 2.93; LTC 669b3f1a +1.34 +- 0.88 n=136,098 [0.5,2.5] LLR 2.94 | CONFIRMED | recomputed from the fresh records |
| T04D-05 | 4f4f78f STC 68c954d3 +3.02 +- 1.83 n=35,872 [0,2] LLR 2.93; LTC 68ca4e4f +1.48 +- 0.98 n=107,754 [0.5,2.5] LLR 2.94; 1 thread, UHO | CONFIRMED | recomputed from the fresh records |
| T04D-05 | commit texts: "branch seems important", later commit = only for deep enough TT entries; PRs 5512 / 6324 | CONFIRMED | messages and PR bodies re-read |
| T04D-05 | lock `:1117` new_depth = depth - 1 + extension, `:1163` PV child search, `:880` depth <= 0 -> qsearch; no pre-qsearch extension anywhere | CONFIRMED | lines re-read; `forge_has.sh 'new_depth <= 0\|new_depth = 1;\|std::max\(new_depth'` = 0 hits |
| T04D-05 | "not in SingularV2 / TtPruneV2"; own start 2 (range 1-8) for PreQsTtExtDepth | UNVERIFIABLE / CONFIRMED (as own) | SingularV2 (R13 B5) is a singular-extension bundle by its README, its source not re-read; the source's depth threshold cannot be checked without its source |
| all | licence row Stockfish ff7cee4244 Copying.txt GPL-3.0 | CONFIRMED | `tools/licence_at.py official-stockfish/Stockfish ff7cee4244 --row` = identical row |
| all | reading rule: commit titles / messages / PR text / run records only | CONFIRMED | sources.md rows name no source file; the verify pass used message-only API filters |
| all | own prior code: packb ReSearchAdjust = re-search depth +-1 after an LMR fail high (T04-02's topic), FiftyDamp = eval damping by the halfmove clock, packa = NonPawnCorr / PawnHist, E3 = eval post-processing; none implements the four mechanisms | CONFIRMED | src_packb_h256/src/search.cpp:1170-1176 re-read; grep of packb for the four mechanisms = 0 hits; notes/TRIED_GATES.md |
| all | duplicates against the 51 other cards and the T04 / T04B / T04C tables | CONFIRMED none | T04B-03 / T04C B16 (LMR search one ply deeper at PV nodes) and T04-02 (deeper re-search) differ from T04D-05 (TT move at depth 1 instead of qsearch); T04B TABLE lists Stormphrax PR 195 as evidence for T04D-02, not as a card |
| all | card count 4 + merged marker (T04D-03), crew hours in all four, UNPROVEN in all four, no vendor names | CONFIRMED | novendor_filter.py idempotent on all 8 files; the same marker convention as T04C-03 / T04C-04 / T04G-03 / T05C-04 |
| all | lint | 4 cards 0 findings; marker 8 findings by construction | card_lint.py after the edits (see the hand-back) |

Violations: none found. Elo recomputation: all 14 runs reproduce to the hundredth (table above).

Lint after the edits (00:43): T04D-01 / -02 / -04 / -05 = 0 findings, 0 PENDING; the T04D-03 marker = 8 findings by construction (one Status line, no fields: it is the merge marker, the same convention as T04C-03 / T04C-04 / T04G-03 / T05C-04, and cannot be made lint-clean without becoming a fifth card). Counts: 36 claims checked, 29 confirmed, 3 corrected (wording / attribution only, no number or link changed), 4 unverifiable, 0 violations, 1 duplicate (T04D-03, already merged by the worker, now marked in its Status line).
