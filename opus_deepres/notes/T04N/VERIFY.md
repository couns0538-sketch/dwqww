# T04N verify (adversarial pass, 02:08-02:2x PC, 2026-11-05)

Method: every cited commit / PR re-opened with `gh api` (text saved under F:/odr/work/T04N-verify/), Elo recomputed from
W/L/D, licence rows re-run with tools/licence_at.py --row, `bash tools/forge_has.sh 'cut_node'` re-run, every cited lock
line read in src_al1s198_clean, SingularV2 read on fable-fb2-j3, notes/TRIED_GATES.md + tools/tried_gates.py grepped,
all 91 cards grepped for the three ideas, card_lint run. Books: the plain-http OpenBench fetch returns a 178-byte redirect
stub (that is why the worker found none); over https with redirects followed all six test pages name their book, and
the three cards were corrected (Ethereal: Pohl.epd; Halogen: UHO_Lichess_4852_v1.epd).

| card | claim | verdict | evidence |
|---|---|---|---|
| T04N-01 | Ethereal f71ac4769a text: STC 10+0.1 +4.66 +- 3.19 [0,3] LLR 2.96 N 22,208 (5589/5291/11328); LTC 60+0.6 +2.44 +- 1.95 N 57,696 (13931/13526/30239); SMP 5+0.05 T8 +3.16 +- 2.96 [-1,2.5] N 25,803 | CONFIRMED | commit message verbatim (ethereal_f71ac47.txt); recomputed 4.66 / 2.44 / 3.16; author date 2023-03-17 |
| T04N-01 | Ethereal got cut nodes later: 3071b40 2023-04-23 "Introduce cutnodes, and perform IIR on them" | CONFIRMED | gh api commit date 2023-04-23T11:49Z, title verbatim |
| T04N-01 | book "not in the commit text (missing)" | CORRECTED | OpenBench 31668 / 31672 / 31682 (https, redirects followed) all list Pohl.epd; written into the card |
| T04N-01 | licence GPL-3.0 at f71ac4769a | CONFIRMED | licence_at.py --row: LICENSE GPL-3.0, api GPL-3.0 (same row as notes/T04N/licences.md) |
| T04N-01 | lock: singular test needs tt_bound != BoundUpper (s:1089); chain s:1100-1111 = +1/+2, return singular_beta, tt_score >= beta -> -2, cut_node -> -1, no below-alpha branch | CONFIRMED | lines read; forge_has 'cut_node' = 10 hits as stated |
| T04N-01 | SingularV2 (fable-fb2-j3 s:1222-1231) has multicut, -3 non-PV, -2 cut, no TT-score <= alpha branch | CONFIRMED | git show fable-fb2-j3:src/search.cpp; only tt_score <= alpha uses are TT cutoff tests at :894 / :1022 |
| T04N-01 | "notes/T04F/TABLE.md row 21 was closed as 'SingularV2 has it'" | CORRECTED | row 21 reads "DIFFERS: -2 / -1, s:1107-1111; -3 non-PV PREPARED in SingularV2 (fable-fb2-j3) / evidence for T04-06 / SingularV2, no card". It filed the Caissa bundle as evidence and made no card; it never said SingularV2 has the below-alpha branch. Card wording fixed; the point (no card covers this piece, SingularV2 lacks it) stands. The hand-back's "T04N-01 corrects an earlier note" is overstated for the same reason |
| T04N-01 | not a duplicate | CONFIRMED | T04-06 = triple extension at LTC; T04C-02 = singular ttpv margin; T04B-04 = ttpv fail-low LMR; none shortens the TT move on a below-alpha TT score |
| T04N-01 | no tried gate | CONFIRMED | tried_gates --grep 'negext|singular|cutnode' = 0 rows (grep of TRIED_GATES.md idem) |
| T04N-01 | reading rule / own constant | CONFIRMED | commit text + result blocks only; start 1 ply, range 0-2 declared own; the source's value is unknowable by rule |
| T04N-01 | UNPROVEN label, crew 1.5 h, 54 lines, lint 0 | CONFIRMED | card_lint exit 0 |
| T04N-02 | Halogen PR 808 "Apply NMP only in suspected cut nodes", merged 2025-11-14 as f00b8e3417; LTC 40+0.4 Hash 64 +1.95 +- 1.53 N 49,716 (11900/11621/26195); STC 8+0.08 Hash 8 +4.05 +- 2.64 N 20,498 (5334/5095/10069) | CONFIRMED | PR title, merged_at, merge sha and both result blocks verbatim (halogen_pr808.txt); recomputed 1.95 / 4.05 |
| T04N-02 | book "not stated in the PR (missing)" | CORRECTED | OpenBench 40369 (STC) and 40378 (LTC) list UHO_Lichess_4852_v1.epd; written into the card |
| T04N-02 | Caissa 47604ad at source | CONFIRMED | gh api: "Search: Perform Null Move Pruning only in Cut Nodes", 2025-08-02, 10+0.1 Hash 16, +1.07 +- 0.86 [0,2] LLR 2.96, N 168,198 (40165/39645/88388), furybench 1998; recomputed 1.07 |
| T04N-02 | licence GPL-3.0 at f00b8e3417 | CONFIRMED | licence_at.py --row identical to notes/T04N/licences.md |
| T04N-02 | lock: null move s:964-968 inside the !pv_node && !in_check block (s:952), no cut_node term; null_tries_ s:969; null child !cut_node s:979; verification s:990; LMR child true s:1148; re-searches !cut_node s:1151 / s:1160; ProbCut s:1018 passes !cut_node | CONFIRMED | lines read |
| T04N-02 | counter-evidence Caissa 47604ad +1.07 +- 0.86 n=168,198, dropped in notes/T04/TABLE.md row 45 | CONFIRMED | row 45 reads exactly that ("dropped, under +1 expected"); see the Caissa line below for the source re-open |
| T04N-02 | not a duplicate, no tried gate | CONFIRMED | T04-01 and T04-03 only mention "Forge's null move has no cut-node condition" as context; T04E-02 skips null move on a big TT capture (different rule); tried_gates --grep 'null|nmp' = 0 rows |
| T04N-02 | UNPROVEN label, crew 1 h, 49 lines, lint 0 | CONFIRMED | |
| T04N-03 | Halogen PR 696 "Increase RFP margin for positions with active threats that need to be resolved", merged 2025-08-01 as 50a42bca43; 8+0.08 +3.72 +- 2.44 [0,3] LLR 2.96 N 21,218 (5151/4924/11143); no LTC; no prose in the PR | CONFIRMED | PR body is the one result block (halogen_pr696.txt); recomputed 3.72 |
| T04N-03 | book "not stated" | CORRECTED | OpenBench 39906 lists UHO_Lichess_4852_v1.epd; written into the card |
| T04N-03 | licence GPL-3.0 at 50a42bca43 | CONFIRMED | licence_at.py --row identical |
| T04N-03 | lock RFP margin = RfpMargin x depth - RfpImproving x improving (s:960-961); threats only in eval (src/eval.cpp:276 evaluate_threats) | CONFIRMED | lines read |
| T04N-03 | family of notes/T04F/TABLE.md row 10 (Caissa +1.41 +- 1.44 n=106,544) | CONFIRMED | row 10 read |
| T04N-03 | tried gates | CORRECTED | the card said nothing about RFP gates; TRIED_GATES has gate62 RfpOppWorse=40 (RFP margin cut when the opponent's last move worsened its static eval, cap / no decision) and gate86 RfpReturnBlend=25 (H0). Neither tests a threat, so no duplicate; note added to the card |
| T04N-03 | own constant 40 cp per ply, range 0-120 | CONFIRMED (rule) / UNVERIFIABLE (coincidence) | declared own; the source's value cannot be compared without reading its source, which the rule forbids |
| T04N-03 | one-liner format | CONFIRMED (remark) | has an extra "Effort" field (9 fields, the rule lists 8); lint accepts it and crew hours are required by the verify brief |
| track | caps: 3 cards <= 4, 54 / 49 / 1 lines <= 60, names clean, licences.md 4 HEAD + 3 commit rows, TABLE.md 38 rows, scratch only F:/odr/work/T04N/, no source file in scratch | CONFIRMED | greps / wc / ls |
| track | source cap | REMARK | 25 Halogen PR bodies + 14 RubiChess PR bodies were read and counted as three batch "sources" (9 outside sources in all). The 15-source cap holds only under that batch count. PR text is allowed reading, so no reading-rule violation; not a card violation |
| hand-back | dead end "none move keeps the old TT move (s:294)" | CORRECTED (hand-back only) | the line is s:293 (`if (!move.is_none() || !same_position) entry->move = move;`); not in any card |

Totals: 29 claims checked, 21 CONFIRMED, 6 CORRECTED (3 books, the row-21 wording, the RFP tried-gates note, one
hand-back line number), 1 UNVERIFIABLE (whether 40 cp coincides with the source's constant: unknowable by rule),
1 REMARK (source-cap batch count). Violations: none. Duplicates: none. Lint after the edits: card_lint exit 0,
cards 55 / 49 / 1 lines. Verify ran 02:08-02:17 PC.
