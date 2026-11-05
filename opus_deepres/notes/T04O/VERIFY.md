# T04O verify (adversarial pass, 2026-11-05 04:26-04:33 PC clock, board slot S1 - S2 was busy)

Scope: cards/T04O/ is empty (the research found no new card), so the targets are the 15 rows of notes/T04O/TABLE.md,
the 9 licence rows (8 in notes/T04O/licences.md plus the crippa1337 redirect), the 5 source lines, and the three
evidence rows that point at other tracks' cards (rows 1, 7, 8). Scratch: F:/odr/work/T04O-verify/ (elo.py).
Verdict in one line: nothing refuted; 2 line-range corrections; row 8 is stronger evidence than filed.

## 1. Source numbers (tools/mine_commits.py --show from the cache; Elo recomputed with elo.py)
| commit | table says | W / L / D (penta) | recomputed | note |
|---|---|---|---|---|
| 3e29e57 | +2.29 +- 2.28 n=41,474 [0,3] LLR 2.96 | 9,846 / 9,573 / 22,055 ([184, 4774, 10588, 4967, 224]) | +2.29, trinomial +-2.29, pentanomial +-1.75 | matches; the quoted +- is the trinomial figure |
| 5d4e144 | +2.89 +- 2.79 n=27,274 | 6,373 / 6,146 / 14,755 | +2.89 (penta +-2.04) | matches |
| aaa803a | +3.20 +- 4.74 n=9,444 [-4,1] LLR 2.97 | 2,214 / 2,127 / 5,103 | +3.20 (penta +-3.69) | matches |
| 98ccad4 | +4.34 +- 3.12 n=24,720 | 6,573 / 6,264 / 11,883 | +4.34 +- 3.12 | matches (no penta in the text) |
| 7120b4b | +17.16 +- 6.88 n=4,864 [0,3] | 1,329 / 1,089 / 2,446 | +17.16 +- 6.89 | matches |
| 2611b64 | +16.68 +- 6.83 n=5,024 | 1,390 / 1,149 / 2,485 | +16.68 +- 6.83 | matches |
| c34a103 | +1.54 +- 3.05 [-3,1] | 5,409 / 5,307 / 12,336 | +1.54 (penta +-2.34) | matches, n=23,052 |
| f65305c | +87.81 +- 15.43 n=998, 40+0.4, Hash 128 MB | 375 / 128 / 495 | not recomputed (net switch, no card) | TC / Hash / n confirmed |
Rows 4, 5, 6, 10, 13, 14 (1dbb625, 82509bd, 3222508, 6f1059c, d9438d8, 5b8ec0d, c85123a): numbers equal the
miner's top-15 list line for line. "15 tested commits since 2024-01-01": confirmed (15 of 44 cached carry a test).
The swehosting test pages themselves were not fetched (commit text used by both of us): listed as unverifiable.

## 2. Diffs re-read (MIT, gh api patch text)
- 3e29e571b2 (1 line): the "-1" branch becomes "TT score >= beta, or TT score <= alpha at null-allowed nodes".
  Row 1's description is exact. T04N-01's own text matches (its missing piece is the below-alpha branch).
- aaa803aef8 (+19/-6): verification only at depth >= 12, a no-null window up to ply + 3/4 of the verification
  depth, baseline returned the null score with no verification. Row 3's description is exact; the numbers are the
  source's mechanism, not a proposed Forge value (no card).
- 7120b4be24 (network.rs diff, first 70 lines, and the two net files' sizes; position.rs not read): feature table
  768 * NUM_BUCKETS with NUM_BUCKETS = 1, old and new net both 1,184,320 bytes -> same input count and same L1.

## 3. Lock greps (tools/forge_has.sh and the lock source)
- Row 2: `has_non_pawn_material(board.side_to_move())` at src/search.cpp:967 - confirmed.
- Row 3: the lock's verification is at s:986-997 (depth < 14 returns at 986, flag off 989, call 990, flag on 992,
  check 994), not s:984-990 -> corrected in TABLE.md and sources.md. `null_move_allowed` is a per-frame field that
  defaults to true (include/forge/search.hpp:277) and is only toggled on the verifying frame, so "children may null
  again" is confirmed; the researcher's PARTIAL reading stands.
- Row 5: TT prefetch at s:847 and s:1126 - confirmed.
- Row 6: correction tables are at include/forge/search.hpp:230, 257-260, 322-323 (table said 230-257) -> corrected.
- Row 8: `mirror|flip_file|king_bucket` = 0 hits in the lock - confirmed.
- Row 12: `pass(ed|er)` = 0 hits in src/search.cpp (55 hits elsewhere, all eval / bitboard) - confirmed.
- T04N-01 "LACKS": the extension chain at s:1100-1111 has `tt_score >= beta -> -2`, `cut_node -> -1`, else 0; no
  below-alpha branch - confirmed.

## 4. Licence rows (tools/licence_at.py --row at HEAD, re-run between 04:26 and 04:31, both measured)
All 9 rows reproduce with the same SHAs and tiers: Sirius 0aab371e4d and motor 033a63cf54 absent (all rights
reserved); akimbo f7dd7677d6 MIT; crippa1337/svart and feliskio/svart both 5f7d00413b absent (the redirect: gh api
returns full_name feliskio/svart, description names it a repo-takeover proof, 0 stars); 1337crisis/svart f3bf4c1ce0
MIT (32 stars, created 2023-01-10, description "UCI Chess engine written in Rust"; since 2024-01-01 exactly 2 commits,
4107d68f80 and f3bf4c1ce0, both "Update README.md"); Starzix 2a1577fb15 WTFPL; pawnocchio bd860905d3 and Tarnished
79f10476c7 GPL-3.0. Reading rule: every read beyond repo metadata was in an MIT repo (akimbo commit text and three
diffs, Svart commit titles); the five skipped repos were touched by `gh api repos/...` metadata only - clean.

## 5. Evidence rows for other cards
- Row 1 -> T04N-01: same idea, same branch, third engine overall (Ethereal, Caissa bundle, akimbo), second with a
  passed single-change [0,3] SPRT; pentanomial half-width +-1.75 makes it a cleaner pass than the quoted +-2.28.
- Row 7 -> T06-01: weak, as filed: the baseline had output buckets, so +4.34 is "material scaling instead of output
  buckets", not scaling over a plain output; the form of the scaling was not read (title + test only).
- Row 8 -> T01B-02: stronger than filed. T01B-02 says "No source isolates mirroring at an equal bucket count and L1";
  akimbo 7120b4b does exactly that on a 768-input, 1-bucket net (the lock net's shape): +17.16 +- 6.88 at STC
  8+0.08, n=4,864, [0,3] LLR 2.91, Threads=1, Hash 32 MB. Caveats: a different net file (both epoch 17, training
  recipe equality unverified), the gain includes the d/e refresh cost, n is small. Pointer for the T01B-02 owner;
  that card is outside this verifier's write scope and was not edited.

## 6. Rules check
No vendor or model-company names in notes/T04O (grep clean); no Forge Elo claim (row 3's "under +1" is labelled
UNPROVEN); no foreign constant proposed as a Forge value (no card exists); LF line endings; no duplicates possible
(0 T04O cards; the three evidence rows point at the right cards). Tried gates: UE3A / UE3A-R6K (EvalMatScale=12)
are the only matches for the row 7 family, as the TABLE says. card_lint.py: 0 card files, so it was not run on
anything (the shell passed the literal glob and the tool raised OSError) - lint not applicable, vacuously clean,
not a content pass. Cap rule: akimbo then Svart gave no card -> stop; correct.

## 7. Owner notes (not violations)
- WORKER_RULES allow commit titles, PR text and test logs for any licence tier, so Sirius, motor, Starzix,
  pawnocchio and Tarnished could have been title-mined under the ideas-only rule; the researcher read the T04O brief
  as "MIT / BSD / Apache only", which this verifier cannot see. Owner call, together with the Starzix (WTFPL) item.
- Hand-back "lint" state: not a pass, nothing to lint.

## Counts
Checked 27 (15 table rows + 9 licence rows + 3 evidence-card matches). Confirmed 24. Corrected 2 (row 3 / sources.md
line range; row 6 line range). Unverifiable 1 of the 27 (row 9: bucket kind of 2611b64, unread by both) plus the
swehosting pages and the 7120b4b recipe equality as caveats. Violations 0. Duplicates 0.
