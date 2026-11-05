# SPEC_SEARCH3: implementation specs for the search cards T04C-02, T04F-01, T04N-01, T04N-02, T04P-01

Started 04:25 PC clock (`date`), planned stop 05:00. Status: COMPLETE (all five specs written by 04:37 `date`; own
review only, not independent). Layout as notes/SPEC_SEARCH2.md. Lock FD3A5190 = AL1 s198 source, read-only:
`C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/src_al1s198_clean` (`search.cpp` = `src/search.cpp`,
`search.hpp` = `include/forge/search.hpp`). Nothing here edits the engine; every Forge-side number is UNPROVEN. No web
read for this note: mechanisms come from the five cards (GPL / AGPL sources were read by the card writers as text and
logs only; the two MIT ones as message + diff; none of them was opened here), the lock source and, for T04P-01, our own
port tree. No card was edited.

## Reading record (read-only, 04:26-04:29)
- search.cpp :771-870 qsearch (in check :802-805, legality :829, move_count :830, prune block :831-839, score block
  :851-863, mated :865, bound :867, store :868); :875-1000 (depth-0 entry :880, TT probe :910-919, TT cutoff :921-926,
  eval :928-943, :952 block, NMP :964-999); :1086-1124 (singular block :1089-1111, check extension :1112-1115,
  :1116-1117); MovePicker stage choice :331-333 (MainTT / EvasionTT / QsTT first), evasion stage :413-423,
  generate_evasions :538-555; search calls with their cut_node argument :979, :990, :1018, :1095, :1148, :1151,
  :1160, :1163, :1391; alpha updates :861 (qsearch), :1183 (search); constants :18 NullMoveMinDepth 3, :23 RfpMargin
  72, :36-37 SingularDepth 7 / SingularMargin 2, :48 CheckExtensionDepth 2, :82 SingularMargin row {0,10};
  search.hpp:56-61 (Infinite 32001, MateInMaxPly = MateValue - MaxPly, ValueNone 32002, is_mate_score).
- Own port tree (T04P-01): `C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/cands/caissa_c123/forge_caissa_c123_al1s198_src`;
  `diff -rq` against the lock's src/ and include/: only src/search.cpp (26 differing lines in the diff output, old +
  new) and include/forge/search.hpp differ; grep of its options; :925-940 read; its exe and check record (below).
- Option names grepped in the lock's src/ + include/: SingularTtPvMargin, QsEvasionLimit, NegExtTtAlpha, NmpCutOnly,
  TtCutExtraMargin: no hit (TtCutExtraMargin exists only in the port tree).

## Common parts (all five)
Exactly as notes/SPEC_SEARCH2.md "Common parts" (which refers to notes/SPEC_SEARCH.md): option recipe (tune:: int +
row + extern, uci.cpp untouched, spin only; every master row admits 0 and defaults to 0, a secondary row admits its
own default and is dead at master 0 (review fix)), kit `-Expose` pc1 = pc2, OFF proof `pin_check -Full`
= the lock pins, ON-live rule (bench d13 != 862329, else d16 / d20), counter build FORGE_SPEC_COUNTERS (its bench
nodes = the plain build's), box FENs F1-F5 at `go depth 16` (0.5x-2x per-FEN stop rule, bench d22 ON within 0.7x-1.5x
of OFF), sanity FENs S1-S5 at depth 12 (mate in 1, stalemate, stalemate trap, 50-move draw, mate on the hundredth
half-move) plus the crew's mate probe set, and the crew gate line (Threads=1, UHO, SPRT [0,5] normalized Elo, alpha =
beta = 0.05, pentanomial, cap 3,000; capped = UNPROVEN / no decision, one extension if its Elo is positive; STC, LTC
after an STC H1; 8moves_v3 only as a separate confirm; 6.0-7.0 h per capped line at 430-502 games/h). Not repeated.

## T04C-02 SingularTtPvMargin (lower singular beta at former-PV nodes)
Source (card; ideas only): PlentyChess PR 286 (GPL-3.0; title and OpenBench blocks): STC 8+0.08 [0,3] +5.21 +- 3.51
n=9,938 LLR 2.13, LTC 40+0.4 +5.34 +- 3.21 n=10,536 LLR 2.50 (neither finished; book unreadable). Stockfish 4e89864
(GPL-3.0; commit message): STC +0.93 +- 1.05 n=154,953, LTC +1.83 +- 1.28 n=70,974; 1591e5a: STC +4.41 +- 2.29 n=23,296,
LTC +1.04 +- 0.64 n=235,592 (all four passed; Elo from W/D/L by the card's writer). Card estimate 0 to +3 Elo **UNPROVEN**.
- Lock lines: gate :1089-1090 (not root, depth >= SingularDepth 7, move == tt_move, no excluded move, tt_bound !=
  Upper, usable non-mate tt_score, tt_depth >= depth - 3); singular_beta :1091 = tt_score - SingularMargin * depth
  (2 cp per ply); verification :1095 (depth (depth - 1) / 2, window singular_beta - 1 / singular_beta, same frame);
  ss->tt_pv saved :1093 and restored :1096 (the verification's own probe overwrites it at :919); outcomes +1 :1101,
  +2 :1102-1103 (non-PV, singular_score < singular_beta - 24, inherited doubles <= 6), multicut return singular_beta
  :1105-1106, -2 :1107-1108 (tt_score >= beta), -1 :1109-1110 (cut_node). Former PV = `ss->tt_pv && !pv_node` at :1091
  (tt_pv = pv_node || tte.pv(), :919; every PV node has it). IIR :1031 needs no TT move, so depth here = entry depth.
- Option (spin): `SingularTtPvMargin` default 0 = off, range 0-96 in 1/16 cp per ply (card), own start 32 (= +2 cp per
  ply: the lock's margin doubled at those nodes; the card's own value).
- Change (own pseudo-steps) at :1091:
  1. base = tt_score - SingularMargin * depth (lock).
  2. If SingularTtPvMargin > 0 and ss->tt_pv and not pv_node: base -= SingularTtPvMargin * depth / 16 (integer).
  3. singular_beta = base; every later line unchanged.
  Knock-ons (they follow singular_beta, no other edit): the verification window moves down; +1 / +2 need a lower
  singular_score; the double threshold :1102 and T04-06's triple threshold move down with it; the multicut :1105 needs
  tt_score >= beta + the whole margin (fires less at the same tt_score, returns a lower value); more verifications end
  at or above the lower bound, so the chain :1107-1111 (and T04N-01's branch) is reached more often. tt_score is not a
  mate score (:1090) and the term is <= 6 x depth: no overflow, no crossing into the mate range.
- OFF node-identical: 0 -> no term -> :1091 = lock -> pins. ON live: `SingularTtPvMargin=32` bench d13 != 862329.
- Box tests (counter build, F1-F5 d16, S1-S5): singular tries per 1M nodes split former-PV / other (live share);
  outcome counts per class (+1, +2, multicut, -2, -1, 0) OFF vs ON (card's check: fewer extensions at former-PV nodes;
  the other class changes only through the tree); nodes spent inside verifications (local_nodes_ around :1095);
  F1-F5 nodes (own expectation, unproven: down).
- SPSA (after an STC H1 or a capped positive run): `SingularTtPvMargin,32,8,96,8`.
- Gate line: `setoption name SingularTtPvMargin value 32`; crew line; LTC after an STC H1 (the large-n source runs
  are LTC passes).
- Crew hours: 1 (card) + 0.5 counters.

## T04F-01 QsEvasionLimit (qsearch in check: stop after the first evasion that is not mated)
Source (card): Caissa a677c89 (MIT; message + diff read by the card writer, nothing opened here): LLR 2.95, n=25,531,
+3.3 +- 2.6 (TC, book, threads not in the message); c8a30a7 bundle +5.9 +- 4.8 n=8,606; no LTC. Stockfish 392b529 /
Stormphrax PR 203 are another rule (guard), not this one. Card estimate +1 to +3 Elo at STC **UNPROVEN**.
- Lock lines: in check there is no stand pat, best_score = -Infinite (:802-805); :829 legality, :830 ++move_count;
  the prune block :831-839 runs only out of check, so in check every legal evasion is searched and move_count =
  evasions searched; score block :851-863 (PV copy, beta break :860, alpha :861); mated only with no legal move
  :865; bound :867, store :868 (depth 0). Picker in check: TT move first (EvasionTT :331), then all moves scored once
  (:538-555): captures and promotions by 10 x victim value minus attacker value / 10 (:546-548), then quiets by quiet
  history + 12000 for a direct check (:550).
- Lock facts the card's reading misses (card not edited): (a) in-check qsearch nodes also come from the main search:
  depth <= 0 enters qsearch even in check (:880), e.g. every checking move searched at depth 1 (the check extension
  :1112 needs depth >= CheckExtensionDepth 2), and the ProbCut qsearch :1016 after a checking capture; so the live
  share is larger than "after checking captures only". (b) The first evasion is the TT move, else the best
  MVV-ordered capture / promotion (not necessarily a capture of the checker), else the best-history quiet.
- Scope (own choice, narrower than the card): non-PV nodes only. At a non-PV node (alpha = beta - 1) a score > alpha
  is >= beta and already breaks at :860, so the new stop fires only when k evasions all failed low and the best is
  not mated: the node returns that fail-low score. At PV nodes the source form could return an Exact score from k
  evasions into the PV; PV qsearch nodes are a tiny share, so leaving them out should cost little (UNPROVEN). The PV
  form is not built.
- Option (spin): `QsEvasionLimit` default 0 = off, range 0-4 (card), own start 1; value 2 only as a second line after
  line 1 ends H0 or capped <= 0 (card). Not SPSA (small integers).
- Change (own pseudo-steps), in the move loop after the score block :851-863 (before the loop end :864):
  1. If QsEvasionLimit > 0 and in_check and not pv_node and move_count >= QsEvasionLimit and best_score >
     -MateInMaxPly: break.
  2. Nothing else. :865 cannot fire after the break (move_count >= 1); :867 gives BoundUpper (best_score < beta at a
     non-PV node) and :868 stores it as the lock does after its out-of-check prunes (the stored upper bound rests on
     k evasions; qsearch's TT cutoff :794-798 has no depth test, so later qsearch visits trust it: accepted, counted).
  Mate safety: the node still returns a mated score only when every legal evasion was searched and mated (step 1
  needs best_score > -MateInMaxPly): no false mate claim. A missed escape / winning evasion is the rule's pruning loss.
- OFF node-identical: 0 -> the first term is false -> no break -> pins. ON live: `QsEvasionLimit=1` bench d13 != 862329.
- Box tests (counter build, F1-F5 d16, S1-S5): in-check qsearch nodes per 1M nodes by origin (counter build only:
  count `board.in_check()` at :880, and after make_move at :848 and :1016); share with >= 2 legal evasions (live
  share); early stops per 1M nodes and evasions skipped per stop; F2 / F4 nodes, score, move OFF vs ON. The card's
  P14 lesson: bench d22 ON within 0.7x-1.5x of OFF and WAC 300 solved at fixed nodes OFF vs ON (a drop of more than a
  few positions = stop before the gate). Mate probe OFF = ON (no new false mate, no lost mate).
- Gate lines: 1 `setoption name QsEvasionLimit value 1`; 2 (conditional, above) `value 2`. Crew line; LTC after H1.
- Crew hours: 1.5 (card 1-2) + 0.5 counters (incl. the WAC count).

## T04N-01 NegExtTtAlpha (negative extension of the TT move when the TT score is at or below alpha)
Source (card; ideas only): Ethereal f71ac47 (GPL-3.0; commit text and OpenBench blocks; book Pohl.epd per verify):
STC 10+0.1 Threads=1 [0,3] +4.66 +- 3.19 n=22,208 LLR 2.96; LTC 60+0.6 Threads=1 [0,3] +2.44 +- 1.95 n=57,696 LLR 2.95;
SMP 5+0.05 Threads=8 +3.16 +- 2.96. Measured with no cut-node negative extension in place (the lock has one). Card
estimate +0.5 to +2 Elo at STC **UNPROVEN**.
- Lock lines: chain :1100-1111 (see T04C-02); :1089 needs tt_bound != Upper, so tt_score is a lower bound or exact;
  the TT move is the picker's first stage (MainTT :333), so at the singular step alpha is the entry alpha after
  mate-distance pruning (:896; alpha moves only at :1183, after a searched move); :1116 counts only extension == 2;
  :1117 new_depth = depth - 1 + extension (depth >= 7 here, so new_depth >= 4 even at -2).
- Option (spin): `NegExtTtAlpha` default 0 = off, range 0-2 = plies taken off, own start 1 (card); 2 only as a
  separate line after 1 passes; no SPSA (two values).
- Change (own pseudo-steps), one more branch at the end of the chain:
  1. ... else if cut_node: extension = -1 (lock :1109-1110).
  2. else if NegExtTtAlpha > 0 and tt_score <= alpha: extension = -NegExtTtAlpha.
  What it covers (from the lock lines): step 2 is reached only when the verification ended >= singular_beta, no
  multicut, tt_score < beta and not cut_node. At non-PV nodes alpha = beta - 1, so tt_score < beta already means
  tt_score <= alpha: the branch fires at every non-PV non-cut node that reaches it (ON = a non-singular TT move at an
  expected all-node loses k plies). It discriminates only at PV nodes (TT score not above the entry alpha).
- OFF node-identical: 0 -> branch skipped -> the lock's extension -> pins. ON live: `NegExtTtAlpha=1` bench d13 !=
  862329.
- Box tests (counter build, F1-F5 d16, S1-S5): chain outcomes per 1M nodes (+1, +2, multicut, -2, -1, new branch)
  split PV / non-PV; for TT moves shortened by the new branch, the share that still ends as best move and the share
  that still gives the beta cutoff OFF vs ON (low = the TT move needed its depth); nodes per FEN. Mate probe OFF = ON.
- Gate line: `setoption name NegExtTtAlpha value 1`; crew line; LTC after an STC H1 (source LTC passed at about half
  its STC number).
- Crew hours: 1.5 (card) + 0.5 counters.

## T04N-02 NmpCutOnly (null move only at expected cut nodes)
Source (card; ideas only): Halogen PR 808 (GPL-3.0; PR text and OpenBench blocks; UHO_Lichess_4852_v1 per verify): STC
8+0.08 Threads=1 [0,3] +4.05 +- 2.64 n=20,498 LLR 2.95; LTC 40+0.4 Threads=1 [0,3] +1.95 +- 1.53 n=49,716 LLR 2.96.
Counter-evidence: Caissa 47604ad (MIT) +1.07 +- 0.86 n=168,198. Card estimate +0.5 to +2 Elo at STC **UNPROVEN**.
- Lock lines: NMP :964-999 inside the :952 block (non-PV, not in check, no excluded move, beta not a mate score);
  condition :965-968; null_tries_ :969; reduction :970-971; null child :979 gets !cut_node; return :986 (depth < 14)
  or verification :990 (passes false; null_move_allowed is false there). Who is a cut node: every LMR-reduced child
  (:1148 true); full-depth null-window children and LMR re-searches get !cut_node (:1160, :1151); PV children false
  (:1163); root false (:1391); null child and ProbCut child !cut_node (:979, :1018); the singular verification inherits
  (:1095).
- Option (spin, not the card's check type): `NmpCutOnly` default 0 = off, range 0-1, ON 1. Reason: the lock's options
  are tune:: int rows (search.cpp:13-103); a check type would need uci.cpp changes, which the recipe forbids. No SPSA.
- Change (own pseudo-steps): append `(NmpCutOnly == 0 or cut_node)` last to :965-968 (the place of T04E-02's term;
  term order is result-neutral, all terms are side-effect free). Nothing else: RFP :960, razoring :954, ProbCut
  :1000 and the move loop still run at all-nodes.
- OFF node-identical: 0 -> term constant true -> pins. ON live: `NmpCutOnly=1` bench d13 != 862329.
- Box tests (counter build, F1-F5 d16, S1-S5): NMP-eligible nodes (all other :965-968 terms true) split by cut_node;
  null_tries_ and null_cutoffs_ per 1M nodes OFF vs ON; the OFF cutoff rate at all-nodes = what ON gives up (high =
  useful prunes lost; own expectation, unproven: lower than at cut nodes); ProbCut tries per 1M nodes (rise ON); F3
  (zugzwang-prone) score and move class OFF = ON; bench d22 ON within 0.7x-1.5x. Mate probe OFF = ON.
- Gate line: `setoption name NmpCutOnly value 1`; crew line; LTC after an STC H1 (the large-n counter-evidence is
  +1, so a capped no-decision is a likely outcome).
- Crew hours: 1 (card) + 0.5 counters.

## T04P-01 TtCutExtraMargin (fail-high TT cutoff needs a deeper entry; own port, built, never gated)
Source (card): form B Caissa 9d566cc (MIT; message + one-line diff read by the card writer): 10+0.1 Threads=1 [0,2]
+1.35 +- 1.06 n=112,192 LLR 2.95 (B vs A); form A Caissa d39fcfb 40+0.4 +2.11 +- 1.55 n=48,018; PlentyChess PR 373
(GPL-3.0, text only): STC H0 -1.26 +- 2.03 n=29,214, LTC +1.73 +- 1.31 n=61,338. Card estimate form B 0 to +2, form A
-1 to +2 Elo **UNPROVEN**; at [0,5] with cap 3,000 most likely capped.
- Lock lines: TT cutoff :921-926 (non-PV, no excluded move, usable score, `tt_depth >= depth` for every bound,
  halfmove < 90, bound test :923-924). Non-PV: alpha = beta - 1, so an Upper entry that cuts has tt_score < beta and
  is never touched by the rule.
- Own port (spec is against it; no new code): tree above; C3 = `int TtCutExtraMargin = 0` (search.cpp:41), row
  {0,200} (:89), extern (search.hpp:217), condition :931-933 = the lock's :921 with the depth test `tt_depth >= depth
  + (TtCutExtraMargin > 0 && tt_score >= beta && tt_score < beta + TtCutExtraMargin)`: one more ply for a fail high
  inside [beta, beta + M), Exact or Lower; every other entry as the lock. The same tree carries C1 `RfpOppWorse`
  (:38, row {0,80} :88; `OppWorseMargin` row {0,200} :88, 75 per the comment :36, read only when RfpOppWorse > 0,
  :973-977) and C2 `RfpNoTtDepth` (:40, row {0,60} :89, :979), both default 0: the gate line sets only
  TtCutExtraMargin, the other two stay 0.
- Exe: `C:/Users/Administrator/grok-pc/forge_push/bin/forge_ltopgo_x_caissa_c123_al1_8924099a.exe` = the kit pc1 copy
  `C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/bin/ltopgo_v23x/caissa_c123_v23x_pc1/src_copy/forge_ltopgo_caissa_c123_v23x_pc1.exe`
  (sha256 of both starts 8924099ad4c42f45, 04:27). Record
  `C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/qa_v22_checks/xchk_caissa_c123_TtCutExtraMargin.json`:
  65 UCI options, option advertised, OFF = the five bench pins + both perft pins (all options at 0), ON at 80 =
  342592 / 879873 / 2333863 / 12556911 / 39261538 = its expected list, smoke Threads 1 / 4 legal. An nps ABBA record
  for this exe was not looked for here.
- Option: `TtCutExtraMargin` (the port's name and range), default 0, own start 72 = one step of the lock's RfpMargin
  (:23), not the source's value (the port's comment and the ON record use 80, the source's threshold).
- Change: none (built). Form A = `TtCutExtraMargin=200` on the same exe (only scores >= beta + 200 still cut at equal
  depth: an approximation); exact form A needs a range change + kit rebuild (+1.5 h, card), LTC only, after B.
- OFF node-identical: proven by the record (re-run `pin_check -Full` on the exe before the gate as routine). ON live at
  72: a new run (`pin_check -Options 'TtCutExtraMargin=72'`, d13 != 862329); its five numbers become the ON reference.
  Shape at 80: +9.5 / +2.0 / -22.8 / +1.4 / +15.3 % vs OFF at d11 / 13 / 16 / 20 / 22, inside the 0.7x-1.5x rule.
- Box tests: F1-F5 d16 and S1-S5 on the exe at 0 and 72; with a counter build (none exists for the port: one copy of
  the port tree with FORGE_SPEC_COUNTERS, +0.5 h): TT cutoffs per 1M nodes split by side of beta; refused cutoffs
  (fail high inside [beta, beta + M) at tt_depth == depth: 0 ON by construction; their OFF count = the live share);
  share of refused nodes whose search still ends >= beta (near 100 % = the rule only burns nodes). Mate probe OFF = ON.
- SPSA (after a first STC result): `TtCutExtraMargin,72,24,200,16`.
- Gate line: candidate = the 8924099a exe vs lock FD3A5190, `setoption name TtCutExtraMargin value 72` (RfpOppWorse,
  RfpNoTtDepth left at 0); crew line; form A (value 200) only at LTC and only after B. The port's comment names the
  source engine and its values: before any merge add the MIT notice (card) or strip the comment; not needed for a gate.
  The review file and the INDEX line quote 72 only, never the port's comment or its values (review fix).
- This exe is another tree than the four-option build below: merging needs a re-port of the one line (0.5 h).
- Crew hours: 0.5 (card: pin re-check, ON box at 72, smoke, INDEX line) + 0.5 counter build.

## Shared code with SPEC_SEARCH / SPEC_SEARCH2, one build, gate order
- Edit sites here: T04C-02 :1091; T04N-01 after :1110; T04N-02 :965-968 (last term); T04F-01 qsearch loop after
  :863; T04P-01 none (the port's :931-933 = lock :921). No two specs of this note edit the same line.
- Same code as the earlier specs:
  - Singular block :1089-1111: T04-01 SingularNonCut (:1095 argument), T04-06 TripleExtMargin (after :1103, :1116),
    T04C-02 (:1091), T04N-01 (after :1110). T04C-02 moves the base of T04-06's triple threshold and feeds the -2 / -1
    / T04N-01 branches (more chain entries); T04-01 changes the verification's flag, not the node's own cut_node read
    at :1109.
  - NMP condition :965-968: T04-03 NmpFewCutoffs (first two terms + :971), T04E-02 NmpTtCaptureMin (last term),
    T04N-02 (last term): independent terms, one combined build merges them in one expression. If T04N-02 is adopted,
    T04E-02 and T04-03 act only at cut nodes: re-check their ON-live bench and box counts on top before their gates.
  - TT cutoff :921-924: T04D-02 TtCutNodeDepth and T04P-01 both only remove shallow cutoffs (by node type / by side
    and margin); gate apart; a joint build ANDs both terms.
  - cut_node (other lines): T04N-02 reads it at :965, T04D-01 at :1141, T04D-02 at :921, the lock's -1 at :1109 (next
    to T04N-01), IIR :1031.
  - T04F-01: no shared line (T04E-04 is qsearch SEE :838, out of check). The tried QsEvasionSeeNonPv (P27R-AL1,
    +4.63 after 3,000 games, no decision) prunes the same node class: if re-run, gate apart, never stacked untested.
- One build for the four new options (T04C-02, T04F-01, T04N-01, T04N-02): separate tune:: ints, default 0, each behind
  its own `> 0` test; one OFF pin proof, one ON-live bench per option, one nps ABBA OFF exe vs the lock exe (as
  SPEC_SEARCH2; it may be the same exe as SPEC_SEARCH2's five, nine options, if the crew prefers one exe). T04P-01
  gates on its existing exe. Each gate line sets exactly one option family.
- Order (own reading, no Elo claim): 1 T04P-01 (no build: it can run while the four-option build is made; lowest
  expectation, likely capped); 2 T04C-02 (two engines, four passes at both TCs; before T04N-01 and T04-06 in the
  singular queue); 3 T04N-01 (alone vs the lock; if T04C-02 passed and is adopted, gate it on top with ON-live
  re-checked); 4 T04N-02 (source STC + LTC pass, large-n counter-evidence +1; before any T04E-02 / T04-03 combination);
  5 T04F-01 (one source, no LTC, tactical risk: WAC check first). Five firm STC lines = 30-35 h worst case at the cap;
  with the two conditional lines (QsEvasionLimit 2, NegExtTtAlpha 2) up to 42-49 h; plus extensions and LTC runs after
  H1. Against SPEC_SEARCH2's queue any interleaving works, since each line runs alone vs the lock; the coupling rules
  above decide only combinations.
- Crew hours total: 8 summed per spec incl. counters (1.5 + 2 + 2 + 1.5 + 1), before any gate time.
