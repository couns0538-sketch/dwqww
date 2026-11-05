# T04U verify (adversarial pass on cards/T04U, started 06:16, clock at writing 06:20 (measured))
Scope: 1 card (T04U-01), notes/T04U/TABLE.md rows 1-8, sources.md, licences.md. Scratch: F:/odr/work/T04U-verify/
(pr281.json, test702.html, test704.html, pa702.html, elo_recompute.txt). No source file, diff or compare page opened
by the verifier either: PR metadata by gh api, the two OpenBench test pages, the lock's own search.cpp.

## Source re-opened (PR #281 and both test pages)
| claim in card | re-check | result |
|---|---|---|
| title "Move check extensions into LMR", merged 2025-10-09, merge 305e45878f, 0 comments / 0 review comments, body = 2 test blocks + "Bench: 11073468" | gh api pulls/281 | CONFIRMED (merged_at 2025-10-09T23:20:08Z; head sha 9187d970, head_ref check-ext-lmr) |
| STC 8+0.08 Hash 16 MB, Threads=1, +5.82 +- 3.96, n=9,724, LLR 3.09 (-2.94, 2.94) [0,5], penta [92,1125,2287,1244,114] | ob.cwchess.org/test/702 settings + stat block | CONFIRMED; W 2339 L 2176 D 5209 -> score 0.508381 -> +5.82 Elo recomputed |
| LTC 40+0.4 Hash 64 MB, +3.35 +- 2.61, n=19,922, LLR 3.04 [0,5], penta [119,2314,4936,2440,152] | ob.cwchess.org/test/704 | CONFIRMED; W 4486 L 4294 D 11142 -> 0.504819 -> +3.35 recomputed |
| own nElo +10.2 +- 6.9 (STC), +6.2 +- 4.8 (LTC) | own recomputation from the pentas (sigma_pg = sqrt(2 var_pair), 95 % = 1.96 nt / sqrt(2 pairs)) | CONFIRMED: +10.17 +- 6.91, +6.19 +- 4.82 |
| book UHO_Lichess_4852_v1.epd, win adj movecount=5 score=600, draw adj movenumber=40 movecount=8 score=5 | both pages | CONFIRMED (identical on 702 and 704) |
| tested dev 277b0cc44f vs base a0ceb385d6; bench 17,351,435 -> 11,595,447 (-33 %) | both pages | CONFIRMED, -33.17 %. Both Dev Source and Base Source on the pages are the author's fork Yoshie2000/Clockwork (branch check-ext-lmr vs main); 277b0cc44f also exists upstream (gh api commits: 2025-10-09T11:19:50Z, title "Bench: 11595447") and a0ceb385d6 upstream = "formatting perfect (#275)". Head of the PR (9187d970) is later than the tested commit, so the merged code is not provably the tested code (the card's TABLE row already says this). |
| pythonanywhere links dead (hosting placeholder) | curl, 2,957 bytes | CONFIRMED: title "Coming Soon: PythonAnywhere" |

## Reading rule and constants
- Researcher's scratch F:/odr/work/T04U/: PR JSON, PR-list JSONL pages, test HTML, own parse scripts; no diff, patch or raw
  source content (grep for diff markers = 0; the one `/compare/` hit in cw281.json is the API's `compare_url` template field).
  sources.md names PR text + test logs only. No violation found.
- Constants: the PR body has no mechanism text, so no Clockwork constant could be and none was carried over. CheckLmrExtra
  default 1 is the researcher's own ("the ply taken from the extension"), range 0-2 own. OK.

## Licence rows re-run (tools/licence_at.py --row)
- official-clockwork/Clockwork 305e45878f: AGPL-3.0 (matches licences.md). Bobingstern/Tarnished 79f10476c7: GPL-3.0 (matches).
- Added by verify: Yoshie2000/Clockwork 277b0cc44f (the fork the tests actually ran from): AGPL-3.0, same tier; row appended
  to licences.md.

## Forge-has greps re-run and the lock code read (src/search.cpp 1086-1170)
- `gives_check`: :1112-1115 extension (else-branch of the singular block :1089-1111, depth >= CheckExtensionDepth, !root,
  SEE >= 0 via picker.last_move_see_nonnegative() or see_ge), :1143 `r -= 1`, :1147 clamp(new_depth - r, 1, new_depth);
  CheckExtensionDepth = 2 at :48, range 1-30 at :90; CheckExtDepthCap 0 hits. All as the card says.
- Mechanism algebra checked: today reduced = clamp(depth - r, 1, depth); with the option reduced' = clamp(depth - r, 1,
  depth - 1): identical unless r <= 0, where it is one ply lower. The non-reduced searches (first move / PV / noisy checks at
  ttpv nodes with move_count <= 4 per :1137 / the re-search at :1151 and :1160) lose one ply. Card's description is right.
- Consequence worth stating plainly (not a correction): on the lock the option is in effect "remove the check extension
  outside LMR" plus a one-ply cut for r <= 0 checks; the LMR relief itself buys nothing extra under whole-ply reductions.
  The card's own 0 to +3 UNPROVEN range already prices this in.

## Tried gates and duplicates
- tools/tried_gates.py --grep 'Check|LmrCheck|CheckExt': gate 59 CheckExtDepthCap=8: 1,500 games, -1.85 Elo, -4.12 nElo,
  LLR -1.13, cap no decision (card numbers CONFIRMED); gate 65 CheckOrderSee (ordering, not this idea).
- grep over all cards for check-extension ideas: none besides T04U-01. Neighbours only: T04B-03 (upper clamp new_depth + 1
  for negative r at PV/ttpv nodes: touches the same :1147 clamp, so the two options would interact if both ON; note for the
  crew, not a duplicate), T04E-01 (LMP keeps quiet checks), T04B-02 (capture-history pruning, `!gives_check` guard).
- Cross-references resolve: notes/T04T/TABLE.md row 5 (#281, PENDING -> this card), notes/T04F/TABLE.md row 23 (Caissa
  607753e non-reg), notes/T04B/TABLE.md line 66 (SP 67 in the removals row; "row 66" in the card is the line number),
  notes/T04N/TABLE.md row 37 (RubiChess #457 +1.32).
- TABLE context rows 2-8 spot-checked against the researcher's saved parses (tests_cw_p4.txt, tests_tn_p2.txt): #83
  +14.94 +- 8.24 n=4,492; #91 +6.02 +- 4.54 n=14,556; #118 +6.39 +- 4.71 n=12,288; #113 +4.28 +- 3.41 n=22,162; #115
  +5.85 +- 4.37 n=14,028; Tarnished #57 +5.84 +- 3.98 n=9,156; #41 +16.91 +- 7.28 n=2,406; #40 +4.28 +- 3.20 n=13,158;
  #47 +2.68 +- 3.79 n=9,596 [-5,0]. All match.

## Corrections made to the card
- None needed: every number re-derived equals the card's. Card left at 60 lines (the cap), lint clean.

## Unverifiable (left as the card states them)
- Which commit of the tested branch produced the 33 % bench-node drop (branch commit list not read; PR head bench
  11,073,468 differs from the tested 11,595,447).
- Clockwork's pre-#281 check-extension rule (SEE filter or not): the PR has no mechanism text, source not readable.

## Violations / duplicates
- None found. Status line of T04U-01 unchanged (COMPLETE).

## Lint
- `tools/card_lint.py cards/T04U/*.md`: 0 findings, 0 PENDING fields; 60 lines.
