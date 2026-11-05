# Second vote on the round-2 top cards (independent re-check from the sources)

Started 03:59 PC clock (planned stop 04:34). Same format as notes/TOP_SECOND_VOTE.md: one line per finding,
`card id | claim | verdict | fix`. Round-1 cards are not redone. Cards (ranking order): T04D-01, T04D-02, T04C-02,
T04E-02, T04F-01, T04B-01, T04E-04, T04E-03, T04N-01, T04N-02.

Method per card: (a) the main source number re-opened once via the GitHub API (commit message or PR text only, no
diff, no source file; texts saved under F:/odr/work/VOTE2/src/all_sources.txt), Elo recomputed from W/L/D and the
pentanomial error from Ptnml (F:/odr/work/VOTE2/elo_check.txt); (b) the card's `tools/forge_has.sh` grep re-run plus
the cited lock lines printed (F:/odr/work/VOTE2/forge_has.txt, lock_lines.txt); (c) reading rule (GPL / AGPL /
unlicensed: no source read, no foreign tuned constant as a Forge value); (d) plausibility of the UNPROVEN estimate
and the crew hours under the crew gate (Threads=1, SPRT [0,5] nElo, alpha = beta = 0.05, pentanomial, cap 3,000
games, capped = UNPROVEN, one extension if positive); (e) vote KEEP / DOWNGRADE / DROP, shared code and gate order.
Tried gates re-run once: `tools/tried_gates.py --grep 'cut|Singular|null|nmp|Evasion|CaptSee|Malus|...'` -> 7 of
110 rows: 16 LmrCorrThreshold, 47 / 48 CaptSeeDiv (+3.24 / -3.94, 1,500 g), 67 HistMalusPct=125 (-7.41, 1,500 g),
P27R-AL1 QsEvasionSeeNonPv=1 (+4.63, 3,000 g, cap no decision), STB1 LmrTtCapAll (-3.01), STB2 LmrCapVictim (H0).
No row touches the singular margin, the NMP condition, the TT-cutoff condition or the cut-node LMR term: the
cards' "not tried" claims hold. Card mtimes re-checked at 04:12: none changed while this vote ran.

## Per-card findings (card id | claim | verdict | fix)

### T04D-01 one more LMR ply at cut nodes without a TT move
T04D-01 | source re-read (commit message 9cc15b30, committer 2025-02-13, text only): STC <0.00,2.00> LLR 2.93 (-2.94,2.94) N 42,304 W 11,223 L 10,892 D 20,189 = +2.72 (recomputed), Ptnml 184/4904/10669/5187/208 -> +-1.74; LTC <0.50,2.50> LLR 2.95 N 32,334 W 8,386 L 8,074 D 15,874 = +3.35 +-1.81; the message says only "somewhat similar to IIR but in LMR" and that reducing more at cut nodes scales well - the one-ply amount and the no-TT-move reading are the card's own, as it states | KEEP | none
T04D-01 | lock: `:1141 if (cut_node) r += 2;` (no TT-move term) and `:1031` IIR (--depth at PV / cut nodes without a TT move, depth >= IirDepth) re-grepped, 2 hits; `tt_move` is the node constant at `:913`; reduced depth clamped at `:1147` | KEEP | none
T04D-01 | reading rule: GPL-3.0 message only, no diff; start value 1 ply is a Forge step, not a copied constant | KEEP | none
T04D-01 | crew gate: 0 to +3 UNPROVEN and 1 crew h plausible; the card already costs the 3,000-game cap (6-7 h); a +1.5 Elo true gain cannot decide inside the cap (see ALL) | KEEP | none

### T04D-02 low-depth TT cutoff only when its direction matches the node type
T04D-02 | source re-read (43e100ae, committer 2024-11-13, message only): "At low enough depths, fail high with TT only when expected cutnode"; STC <0,2> LLR 2.93 N 41,184 W 10,873 L 10,551 D 19,760 = +2.72 +-1.72; LTC <0.5,2.5> LLR 2.94 N 270,888 W 69,040 L 68,243 D 133,605 = +1.02 +-0.62 (recomputed, both match); follow-up a4edacb not re-opened | KEEP | none
T04D-02 | design stricter than the source: the message states only the fail-high half; the card's ON rule "(stored score >= beta) must equal cut_node" ALSO refuses upper-bound cutoffs at expected cut nodes, a half the source never tested (the card's own text admits the two-sided reading is its own) | KEEP-WITH-FIX | make the option two-valued: 1 = source form (at depth <= N a fail-high cutoff needs cut_node; fail-low cutoffs unchanged), 2 = the two-sided form; gate 1 first
T04D-02 | lock `:921-926` re-grepped (1 hit): non-PV, no excluded move, usable score, tt_depth >= depth, clock < 90, bound in the right direction, no node-type term; `cut_node` is the `search` parameter at `:875` | KEEP | none
T04D-02 | reading rule: GPL-3.0 messages only; depth limit 6 is an own start (the source's limit was not read) | KEEP | none
T04D-02 | crew gate: 0 to +3 UNPROVEN at STC plausible, but the source's own LTC gain is +1.0 at 271k games, so expect the smaller end at LTC; 1 crew h plausible; card already costs the 3,000 cap | KEEP | say "LTC gain in the source +1.0" in the estimate line

### T04C-02 lower singular beta at former-PV (tt_pv) non-PV nodes
T04C-02 | source re-read (PR 286 body, merged 2024-11-19 as 9b8517d0): STC 8+0.08 T1 16 MB Elo 5.21 +-3.51, LLR 2.13 (-2.25, 2.89) [0,3], N 9,938 W 2,334 L 2,185 D 5,419 = +5.21 (recomputed); LTC 40+0.4 64 MB 5.34 +-3.21, LLR 2.50, N 10,536 W 2,577 L 2,415 D 5,544 = +5.34; neither LLR reached 2.89 (merged unfinished, as the card says); book not in the PR body. Better evidence re-read, 1591e5ac message (2022-09-11, "bigger extension offset in case of non-pv node having a pv" = this rule): STC <0,2> N 23,296 W 6,404 L 6,108 D 10,784 = +4.41 +-2.29, LTC <0.5,2.5> N 235,592 = +1.04 +-0.64 (both match) | KEEP | none
T04C-02 | lock `:1091 singular_beta = tt_score - tune::SingularMargin * depth` (2 cp per ply, tunable `:37/:82`), `:919 ss->tt_pv = pv_node || (tt_hit && tte.pv())`, LMR use `:1139`; also `:1093-1096` save / restore ss->tt_pv around the singular search (harmless for the card) | KEEP | none
T04C-02 | reading rule: PlentyChess and Stockfish GPL-3.0, PR text / messages only; 32/16 = +2 cp per ply is an own start | KEEP | none
T04C-02 | crew gate: 0 to +3 UNPROVEN plausible but the direct evidence is the weakest of the ten (two unfinished beta-0.10 SPRTs at n ~10k); the three large-n Stockfish runs put the LTC gain near +1 to +1.8; 1 crew h plausible; CPU line still says 6.6k games / 13-15 h (cap 12k): see ALL | KEEP-WITH-FIX | CPU line to the crew cap; rank it below N-01 on the same chain

### T04E-02 no null move when the hash move captures a valuable piece
T04E-02 | source re-read (commit 845f49d3 message, 2026-01-14, "Guard NMP on valuable piece TT captures (#671)", credits a Seer commit, not read): STC 8+0.08 T1 16 MB 3.43 +-2.31, LLR 2.92 (-2.25, 2.89) [0,3], N 22,374 W 5,700 L 5,479 D 11,195 = +3.43 (recomputed); LTC 40+0.4 64 MB 3.67 +-2.27, LLR 3.17, N 20,816 W 5,169 L 4,949 D 10,698 = +3.67; book not in the message (card: UHO from the logs, not re-opened); Viridithas log not re-opened | KEEP | add the (-2.25, 2.89) bounds to the source line
T04E-02 | lock `tt_capture` 2 hits (`:918` defined, `:1142` LMR only); NMP condition `:965-968` = depth, eval >= beta, static margin, null allowed, previous move not null, non-pawn material, upper-bound TT guard - no hash-move term; matches the card | KEEP | none
T04E-02 | reading rule: unlicensed at the merge commit / AGPL later: text and logs only; victim >= rook or SEE 300 are own starts | KEEP | none
T04E-02 | crew gate: +1 to +3 UNPROVEN plausible (two engines, two LTC passes); 1-2 crew h plausible; CPU line "12k cap, 13-25 h" is pre-decision: see ALL | KEEP-WITH-FIX | CPU line to the crew cap

### T04F-01 qsearch in check: stop after the first evasion that is not mated
T04F-01 | source re-read (a677c890 message, 2023-08-23): cutechess block "Caissa 1.11.15 vs 1.11.14: 5052 - 4810 - 15669 [0.505] 25531, Elo 3.3 +/- 2.6, SPRT llr 2.95 lbound -2.94 ubound 2.94, H1 accepted" = +3.29 recomputed (trinomial error); no TC, book, thread count or Elo bounds in the message - a version-pair test, as the card says; no LTC | KEEP | none
T04F-01 | lock: in-check qsearch `:801-805` best = -Infinite (no stand pat), futility + SEE only under `!in_check && best_score > -MateInMaxPly` (`:831-839`), mated only with move_count 0 (`:865`); `generate_evasions` `:414/:538` - all as cited | KEEP | none
T04F-01 | reading rule: Caissa MIT (diff allowed, nothing copied); the Forge rule differs (keeps searching inside the mated range); Stockfish / Stormphrax GPL text only | KEEP | none
T04F-01 | crew gate: +1 to +3 UNPROVEN is the thinnest estimate of the ten (one engine, no LTC, no TC); the nearest tried line P27R-AL1 QsEvasionSeeNonPv=1 sits at +4.63 (3,000 g, cap, no decision) and under the crew rule that positive capped run gets the one extension first; the P14 d22 node blow-up is the real risk and the card's WAC / d22 check covers it; CPU "6,000 games 12-14 h" = cap + extension | KEEP (lowest of the full cards) | queue it after P27R's extension result, not beside it; CPU line to the crew cap

### T04B-01 capture history in the noisy-move SEE pruning threshold
T04B-01 | source re-read (PR 269 body, merged 2025-11-20 as a5807f3a): STC 8+0.08 T1 16 MB 3.08 +-2.21, LLR 2.95 (-2.25, 2.89) [0,3], N 28,964 W 6,991 L 6,734 D 15,239 = +3.08 (recomputed, penta +-2.20); LTC 40+0.4 128 MB 6.48 +-3.34, LLR 2.93, N 10,130 W 2,245 L 2,056 D 5,829 = +6.48; no formula and no book in the PR body (the DFRC book comes from the OpenBench pages, not re-opened) | KEEP | add the (-2.25, 2.89) bounds
T04B-01 | lock `see_threshold` `:1081-1083` (-SeeNoisyMultiplier x depth, shortcut when the picker's SEE was non-negative and threshold <= 0), `history` at `:1058` = capture history for non-quiet moves - as cited; with cap 150 and 150 cp per ply the shifted threshold stays <= 0 at every depth >= 1, so the `:1082` shortcut stays valid (the card's "positive threshold must call SEE" is a safe generality) | KEEP | none
T04B-01 | reading rule: GPL-3.0 PR text only; divisor 96 / cap 150 own | KEEP | none
T04B-01 | crew gate: +1 to +4 UNPROVEN plausible as a range (the +6.5 LTC is n=10k, +-3.3, DFRC); 2 crew h plausible; CPU "3-6k games 6-14 h" already equals cap + extension | KEEP | none

### T04E-04 qsearch SEE threshold shifted by capture history (one-liner)
T04E-04 | source re-read (d6603046 message, 2026-07-30, "Adjust qsearch SEE margin using quiet/noisy history (#1113)"): STC 8+0.08 T1 16 MB 4.53 +-2.72, LLR 3.01 (-2.25, 2.89) [0,3], N 16,626 W 4,310 L 4,093 D 8,223 = +4.53 (recomputed); LTC 40+0.4 64 MB 3.61 +-2.32, LLR 3.00, N 20,184 W 5,095 L 4,885 D 10,204 = +3.62; the title's "quiet/noisy history" supports the card's note that the source rule also covers quiet qsearch moves | KEEP | none
T04E-04 | lock `QsSeeMargin` 4 hits: default 40 (`:42`), tunable 0-500 (`:85`), test `:838 see_ge(move, -QsSeeMargin)` inside the `!in_check && best_score > -MateInMaxPly` block - as cited | KEEP | none
T04E-04 | reading rule: AGPL text only; divisor 64 / clamp 100 own | KEEP | none
T04E-04 | crew gate: +1 to +3 UNPROVEN plausible (UHO book, both TCs); ~2 crew h plausible; CPU "13-25 h" pre-decision: see ALL; one-liner format is right (4th card of T04E) | KEEP | CPU line to the crew cap

### T04E-03 quiet-move malus decaying along the tried list (one-liner)
T04E-03 | source re-read (5e669a65 message, 2026-05-22, "Apply decay to quiet move malus (#1038)"): STC 8+0.08 T1 16 MB 4.67 +-2.78, LLR 2.98 (-2.25, 2.89) [0,3], N 15,778 W 4,085 L 3,873 D 7,820 = +4.67 (recomputed); LTC 40+0.4 64 MB 5.18 +-2.88, LLR 2.96, N 12,682 W 3,185 L 2,996 D 6,501 = +5.18; no rule text in the message (the card says so); the three other engines' numbers not re-opened (second-hand from T04D-03 / T04G-03 / T04C TABLE) | KEEP | none
T04E-03 | lock `-bonus` 3 hits: `:747-748` flat malus on every tried quiet in main + continuation history, `:764` capture malus - as cited | KEEP | none
T04E-03 | reading rule: AGPL text only; start 100 % / step 8 % / floor 40 % own (the MIT form seen via T04G-03 may be copied with notice anyway) | KEEP | none
T04E-03 | crew gate: +1 to +3 UNPROVEN plausible (four engines); ~2 crew h plausible; CPU line pre-decision: see ALL; its counter-evidence gate 67 (-7.41, 1,500 g) has a +-8 Elo bar, so it is itself inside noise - say so | KEEP | CPU line; "gate 67 is 1,500 games, +-8" when citing it [last round, coordinator, unverified]: the vote stands - the tried-gates row's -15.55 / -2.54 are nElo and LLR, not an interval; from its pentanomial 7/157/456/121/9 the 95 % interval is -15.8 .. +1.0 Elo, which includes 0, so cite "1,500 games, -7.41, 95 % -15.8 .. +1.0"

### T04N-01 negative extension of the TT move when the TT score is at or below alpha
T04N-01 | source re-read (f71ac476 message, 2023-03-17): STC 10+0.1 T1 8 MB 4.66 +-3.19, LLR 2.96 (-2.94, 2.94) [0,3], N 22,208 W 5,589 L 5,291 D 11,328 = +4.66 (recomputed); LTC 60+0.6 64 MB 2.44 +-1.95, LLR 2.95, N 57,696 W 13,931 L 13,526 D 30,239 = +2.44; SMP 5+0.05 T8 3.16 +-2.96 [-1,2.5] N 25,803; alpha = beta = 0.05 bounds (tighter than the OpenBench default); book not in the message (card: Pohl.epd from the pages) | KEEP | none
T04N-01 | lock chain `:1100-1111` exactly as cited (+1 / +2 singular, `singular_beta >= beta` return, `tt_score >= beta` -2, `cut_node` -1, else 0); `:1089 tt_bound != BoundUpper`; at non-PV nodes the new branch is the whole remaining else case (every non-cut node with tt_score < beta), which the card states | KEEP | none
T04N-01 | reading rule: GPL-3.0 message only; 1 ply own | KEEP | none
T04N-01 | crew gate: +0.5 to +2 UNPROVEN plausible (the lock already takes -1 at cut nodes, which the source lacked); 1.5 crew h plausible; CPU "6.6k games 13-15 h" pre-decision: see ALL | KEEP-WITH-FIX | CPU line to the crew cap

### T04N-02 null-move pruning only at expected cut nodes
T04N-02 | source re-read (PR 808 body, merged 2025-11-14 as f00b8e34): LTC 40+0.4 T1 64 MB 1.95 +-1.53, LLR 2.96 (-2.94, 2.94) [0,3], N 49,716 W 11,900 L 11,621 D 26,195 = +1.95 (recomputed); STC 8+0.08 8 MB 4.05 +-2.64, LLR 2.95, N 20,498 W 5,334 L 5,095 D 10,069 = +4.05; book not in the PR body | KEEP | none
T04N-02 | lock: `cut_node` 10 hits, none in `:965-968`; null child gets `!cut_node` at `:979`; `null_tries_` counted at `:969` - as cited | KEEP | none
T04N-02 | reading rule: GPL-3.0 PR text only; boolean, no constant | KEEP | none
T04N-02 | crew gate: the tightest number for this idea is the card's own counter-evidence, Caissa 47604ad +1.07 +-0.86 at 168k games (MIT, round-1 TABLE row 45), i.e. at the "+1 expected" drop line; Halogen's LTC +1.95 +-1.53 is consistent with ~+1; a +1 Elo true gain is invisible under the cap (+-5.9 at 3,000 g) | DOWNGRADE | one-liner behind T04E-02 on the same NMP line; gate it only on top of E-02 if E-02's single is positive, not as its own 3,000-game run

## ALL (apply once)
ALL | bounds: every OpenBench source here except Ethereal and Halogen ran (-2.25, 2.89) = beta 0.10 and stopped early (Reckless E-02 / E-04 / E-03, Stormphrax B-01, PlentyChess C-02): the point estimates carry stopping-rule inflation, as round 1 said for T04-04; Ethereal, Halogen and the Stockfish runs are alpha = beta = 0.05 | KEEP-WITH-FIX | write "(-2.25, 2.89), early stop" once in each of those five source lines
ALL | CPU lines of C-02, E-02, E-04, E-03, N-01, N-02 (and F-01's 6,000) still cost 6.6k / 12k games; the crew decision (before 02:37) caps every run at 3,000 games (+ one 3,000 extension if positive): 6-7 h per run at 430-502 games/h, 12-14 h worst case at STC, about 6x that per 3,000 games at 60+0.6; D-01, D-02 and B-01 already say so | KEEP-WITH-FIX | one sentence per card
ALL | what the cap can decide (approximate, Gaussian SPRT arithmetic, F:/odr/work/VOTE2/elo_check.py; sigma from the P27R-AL1 row +4.63 with a 5.90 half-width at 3,000 g, cross-checked by the 0.46-0.52 Elo per nElo ratio of the Stockfish runs): 95 % half-width +-5.9 Elo at 3,000 games, +-4.2 at 6,000; [0,5] nElo is about [0, 2.4] Elo at the crew's draw rate; the mean run length to LLR 2.944 at the H1 bound is ~28k games, nearly 10x the cap; a true gain of +2.5 Elo would reach H1 inside 3,000 games with probability ~0 and inside 6,000 with ~2 %; +6 would need ~7k games on average (35 % inside 6,000); only a stack worth roughly +10 Elo or more decides inside the cap. So all ten singles will log UNPROVEN at the cap by construction: the cap is a screen (point estimate +-5.9) for the one extension and for stacking, not a test of +1 to +4 Elo ideas | FLAG (no redesign proposed) | the estimates stay UNPROVEN; rank by LTC evidence x simplicity, then stack positives by site group
ALL | reading rule: all ten cards read text and logs only for GPL / AGPL / unlicensed sources (this vote did the same: commit messages and PR bodies via the GitHub API, no diff); every proposed start value is an own value or a structural one (1 ply, boolean, first evasion); no vendor or model-company name in any card | KEEP | none
ALL | OFF = lock pins: all ten add a term, branch or option that evaluates to the lock expression at default 0 / false (D-02's new condition is not evaluated at 0, N-01's branch is skipped, E-03's scale is 100 % everywhere); none grows a table or the stack | KEEP | none

## Shared code and gate order (second vote)
- NMP condition `src/search.cpp:965-968`: T04E-02 first (two engines, two LTC passes), T04N-02 only on top of it (one-liner).
- Singular / extension chain `:1091` and `:1100-1111`: T04N-01 first (single-change source, finished LTC at 58k), T04C-02 second (unfinished SPRTs, ~+1 at LTC in the large-n runs); both must be re-based if SingularV2 or the T04-06 triple step is adopted (same chain); C-02 lowers singular_beta at tt_pv non-PV nodes, so it changes how often N-01's branch fires - gate singles, then the pair.
- `cut_node` readers on separate lines: T04D-01 (`:1141`, LMR) before T04D-02 (`:921`, TT cutoff; source LTC +1.0); no shared line, but D-02 changes which low-depth nodes are searched at all, so stack D-02 on D-01, not the reverse.
- SEE threshold + capture history: T04B-01 (`:1081-1083`) and T04E-04 (`:838`) as separate singles with one shared clamp helper (same table, same clamp); T04B-02 (same site as B-01) after B-01; if both singles are positive, gate the pair.
- History update `:744-749`: T04E-03 alone and at the base of any stack (it changes every quiet-history consumer: ordering and the LMR term `:1146`).
- qsearch in check `:801-865`: T04F-01 alone, after the P27R-AL1 extension result (same node class); no line shared with E-04 (out of check), but both change qsearch node counts: redo the d22 / WAC check for any stack holding both.
- Suggested single-run queue (3,000 g each, ~6-7 h, 55-65 h of gate PC for the nine singles): E-03, E-02, D-01, E-04, B-01, N-01, D-02, F-01, C-02; N-02 only stacked.

## Summary table
| card | main source (recomputed) | lock grep | reading rule | estimate / hours under the cap | vote |
|---|---|---|---|---|---|
| T04D-01 | SF 9cc15b3 STC +2.72 +-1.74 (42,304 g), LTC +3.35 +-1.81 (32,334 g) - match | :1031 / :1141 ok | ok (message only) | 0 to +3 UNPROVEN, 1 h ok, cap costed | KEEP |
| T04D-02 | SF 43e100a STC +2.72 +-1.72 (41,184 g), LTC +1.02 +-0.62 (270,888 g) - match | :921 ok | ok | 0 to +3 UNPROVEN at STC (+1 at LTC in the source), 1 h ok | KEEP-WITH-FIX (source one-sided form = value 1) |
| T04C-02 | PlentyChess 286 STC +5.21 +-3.51 / LTC +5.34 +-3.21, LLR 2.13 / 2.50 of 2.89 unfinished; SF 1591e5a +4.41 / LTC +1.04 at 236k - match | :1091 / :919 ok | ok | 0 to +3 UNPROVEN (weakest direct evidence), 1 h ok, CPU line stale | KEEP-WITH-FIX (CPU line; after N-01) |
| T04E-02 | Reckless 671 STC +3.43 +-2.31 (22,374 g), LTC +3.67 +-2.27 (20,816 g) - match | :918 / :965-968 ok | ok | +1 to +3 UNPROVEN, 1-2 h ok, CPU line stale | KEEP-WITH-FIX (CPU line, bounds) |
| T04F-01 | Caissa a677c89 +3.29 +-2.6 (25,531 g), version pair, no TC / book / LTC - match | :801-865 ok | ok (MIT) | +1 to +3 UNPROVEN thin; 1-2 h ok | KEEP, lowest full card; after P27R's extension |
| T04B-01 | Stormphrax 269 STC +3.08 +-2.21 (28,964 g), LTC +6.48 +-3.34 (10,130 g), DFRC - match | :1081-1083 / :1058 ok | ok | +1 to +4 UNPROVEN, 2 h ok, cap costed | KEEP (add bounds) |
| T04E-04 | Reckless 1113 STC +4.53 +-2.72 (16,626 g), LTC +3.62 +-2.32 (20,184 g) - match | :838 / :42 ok | ok | +1 to +3 UNPROVEN, 2 h ok, CPU line stale | KEEP (one-liner) |
| T04E-03 | Reckless 1038 STC +4.67 +-2.78 (15,778 g), LTC +5.18 +-2.88 (12,682 g) - match | :747-748 ok | ok | +1 to +3 UNPROVEN, 2 h ok, CPU line stale | KEEP (one-liner; base of any stack) |
| T04N-01 | Ethereal f71ac47 STC +4.66 +-3.19 (22,208 g), LTC +2.44 +-1.95 (57,696 g) - match | :1100-1111 / :1089 ok | ok | +0.5 to +2 UNPROVEN, 1.5 h ok, CPU line stale | KEEP-WITH-FIX (CPU line) |
| T04N-02 | Halogen 808 LTC +1.95 +-1.53 (49,716 g), STC +4.05 +-2.64 (20,498 g) - match; Caissa +1.07 +-0.86 at 168k | :965-968 / :979 ok | ok | ~+1 UNPROVEN = drop line, invisible at the cap; 1 h ok | DOWNGRADE (one-liner behind E-02, stacked only) |

Votes: 5 KEEP (D-01, F-01, B-01, E-04, E-03), 4 KEEP-WITH-FIX (D-02 design, C-02, E-02, N-01), 1 DOWNGRADE (N-02), 0 DROP.
All 21 source numbers recomputed from W/L/D match the cards; all 10 lock greps match. Sources re-opened: 11 (10 main +
SF 1591e5a), all via the GitHub API, messages / PR bodies only. Nothing left PENDING.
Note on the tally: KEEP = the card's own text is right; its only fixes are the ALL lines (bounds / CPU line). The beta-0.10 bounds line covers exactly the five OpenBench runs; Caissa's F-01 run was also (-2.94, 2.94).
Time span of this vote: 03:59 to 04:17 PC clock (2026-11-05).
