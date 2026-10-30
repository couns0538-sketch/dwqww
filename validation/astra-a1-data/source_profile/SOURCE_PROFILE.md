# Original 10M source profile

Read-only profile of `forge_selfplay_003.pos` and its authoritative full-FEN
text sidecar, 2026-10-30. **PASS:** exactly 10,000,000 rows; all STM, original
score and White-result fields match the FPOS scalar columns. Both input SHA256
hashes were unchanged after the scan. Full board/FEN alignment is a separate
validation, not repeated here.

| Original FEN state | Positions | Share |
|---|---:|---:|
| Halfmove 0–9 | 8,694,375 | 86.94375% |
| Halfmove 10–29 | 761,556 | 7.61556% |
| Halfmove 30–49 | 227,269 | 2.27269% |
| Halfmove 50–69 | 152,296 | 1.52296% |
| Halfmove 70–89 | 117,154 | 1.17154% |
| Halfmove 90–99 | 47,350 | 0.47350% |
| Halfmove 100+ | 0 | 0% |
| Nonempty castling rights | 2,170,414 | 21.70414% |
| Nonempty en-passant target | 355,647 | 3.55647% |

Maximum halfmove clock is 99. Clocks at least 50 appear in 316,800 positions
(3.168%). Rights and EP presence are separate, potentially overlapping counts;
they do not establish that a castle or en-passant capture is currently legal.
FPOS omits all three state fields, so the values above come from original FENs.

White is to move in 5,004,851 rows; Black in 4,995,149. White-result labels are
win 4,256,710, draw 3,174,426, loss 2,568,864. These are **position-weighted
labels, not game win rates**; authoritative game IDs are unavailable. Original
STM scores range from -3000 to +3000 cp. All signed score bins and precise
fractions are recorded in `source_profile.json`.

The single-process script ran at nice 19 with bounded memory (peak RSS
40,128 KiB). Its scan plus post-scan hashes took approximately 44 seconds;
`command.json` records the complete command, wall and actual child OS CPU time.
`profile_source.py` accepts input/output paths and refuses an existing output.
`test_profile_boundaries.py` passed signed-cp and halfmove inclusive-boundary
checks on a retained synthetic 19-row fixture before the real scan.

No native search, training, new filter or engine change was performed. These
frequencies provide context for future teacher-budget/clock investigations;
they establish no defect, training gain or playing-strength improvement.

IDEA_SOURCE: original Forge dataset schema and the user's source-state profile
request. No other engine code or tuned constants were used.
