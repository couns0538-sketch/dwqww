# T04P table - fail-high TT cutoff that needs a deeper entry (one idea, carrier T04P-01)
Status: COMPLETE (5 rows; 4 outside sources re-opened once each, numbers from the logs, no source of a GPL repo read)

| # | rule | source | licence | source number (TC, bounds, games, LLR) | lock | verdict |
|---|---|---|---|---|---|---|
| 1 | form B: one extra ply only for beta <= TT score < beta + M | own caissa_c123 `TtCutExtraMargin` (spin 0-200, 0 = off), exe forge_ltopgo_x_caissa_c123_al1_8924099a.exe, CR PASS-notes 2026-10-30 | own code (port of MIT, notice owed) | never gated (`tried_gates.py`: 0 rows); box at 80 recorded (xchk json) | LACKS (:921) | carried by T04P-01: gate the built exe by setoption, own start 72 |
| 2 | form A: one extra ply for every TT score >= beta, non-PV | [Caissa d39fcfb](https://github.com/Witek902/Caissa/commit/d39fcfb0d6) | MIT | 40+0.4 Threads=1 [0.00, 2.50] LLR 2.95, N 48,018 W 11,008 L 10,717 D 26,293, +2.11 +- 1.55; no STC logged | LACKS | evidence for T04P-01 (form A) |
| 3 | form A (same rule, idea credited to two other engines) | [PlentyChess PR 373](https://github.com/Yoshie2000/PlentyChess/pull/373) (9c520de) | GPL-3.0 ideas only | STC 8+0.08 [0.00, 2.50] LLR -2.25 = H0, N 29,214, -1.26 +- 2.03; LTC 40+0.4 LLR 3.02 passed, N 61,338, +1.73 +- 1.31 | LACKS | evidence for T04P-01; STC FAILED - form A is TC-dependent |
| 4 | form B vs form A (margin 80 in the source; not used as a Forge value) | [Caissa 9d566cc](https://github.com/Witek902/Caissa/commit/9d566ccbd5) | MIT | 10+0.1 Threads=1 [0.00, 2.00] LLR 2.95, N 112,192 W 26,924 L 26,487 D 58,781, +1.35 +- 1.06 | LACKS | evidence for T04P-01 (form B); the only STC pass, measured against form A, not against the lock's rule |
| 5 | fail lows allowed at equal depth (from "strictly deeper for every cutoff") | [Stockfish b280d2f](https://github.com/official-stockfish/Stockfish/commit/b280d2f065), PR 5314 | GPL-3.0 ideas only | STC 10+0.1 UHO_Lichess_4852_v1 normalized [0,2] LLR 2.93, 26,592 games (+3.91); LTC 60+0.6 [0.5,2.5] LLR 2.96, 142,572 games (+1.31) | HAS that side (equal depth for every bound) | NOT evidence for the fail-high rule (CRITIC2 line 16 cites it as such); shows the source's end state only |

## Notes for the coordinator (no other track's file was edited)
- Pointers: notes/T04/TABLE.md row 4 (A4), notes/T04D/TABLE.md rows 22 + 54, notes/T04F/TABLE.md row 7 (+ DIFF.md row 9),
  notes/T04H/TABLE.md row 25 are all evidence for T04P-01 now (CRITIC2 section 1 line 16 asked for one carrier).
- Missed own code: T04D-02's Forge fit, T04 TABLE A4 and CRITIC2 line 16 do not name the own caissa_c123 port, whose
  `TtCutExtraMargin` IS form B on the lock base (CR PASS-notes 2026-10-30, exe built, never gated). T04N VERIFY:40 lists the
  option but not as this rule's implementation.
- T04 TABLE A4's option sketch (`TtCutLowerExtraDepth`, lower-bound entries only) is narrower than every source: the
  sources decide by the TT score's side of beta, so an exact entry above beta also needs the extra ply.
- CRITIC2 line 16 calls b280d2f's "STC +3.91" evidence for this idea; its PR text says the patch ALLOWED equal-depth
  cutoffs for TT value <= beta starting from "strictly deeper for every cutoff" (row 5). Weaker evidence, stated in the
  card's Status line.
- Not read (cap / advice): Obsidian f90784d (credited idea origin in rows 2 and 3), the own CR note
  CR_CAISSA_C123_AL1_20261030.md (not found within depth 4 of forge_push or the dwqww folder; quoted from the .ok file).
