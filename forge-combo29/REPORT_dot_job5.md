# REPORT_dot_job5

## 1. Step0 PASS
PCA /tmp/forge-dot-pca-build/forge, SHA25649b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a. GNU C++14.2.0, libstdc++.so.6.0.33, glibc2.41, CMake Release with -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1. Five required fresh-process gates passed; full labeled output step0_raw.txt, committed with harness/summary in b81dd5d9b96354239ca8ddb557ddac10f8d50e28.
```json
{
  "exe_sha256": "49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a",
  "id": [
    "id name Chess Engine Forge 6.4.24 candidate"
  ],
  "options": [
    "option name FailHighBlend type spin default 0 min 0 max 7",
    "option name RfpNoTtPv type spin default 0 min 0 max 1",
    "option name RfpTtGuard type spin default 0 min 0 max 1",
    "option name RfpCorrMul type spin default 0 min 0 max 64"
  ],
  "known_answers": [
    [
      "PCA_default",
      11,
      312866
    ],
    [
      "PCA_default",
      13,
      862329
    ],
    [
      "PCA_PC20",
      11,
      278024
    ],
    [
      "PCA_PC20",
      13,
      587276
    ],
    [
      "perft",
      5,
      4865609
    ]
  ],
  "gate": "PASS"
}
```

## 2. PartA: five measured inactive settings explained by source
Committed together with PartB at0a33b67e90aa3e0b2dd5fe92fa5c100a8443b48c before PartC. Source quotes personally reopened, including promotion SEE helper. No access to the PC's running tune values.
# Job5 Part A: five inactive steps
PCA source personally reopened, including Board SEE and promotion recapture path. Actual UCI lists all45 settings; PC20 does not enable the off gates below. Source reading, not new engine result.

1. QsSeeMargin: sole runtime setting read search.cpp:1716, `if (!board.see_ge(move, -tune::QsSeeMargin)) continue;`. Gate 1709: `mate_moves_ == 0 && !in_check && best_score > -MateInMaxPly`; illegal moves already skipped1707 and futility-pruned moves continue1712-1714. Board::see_ge board.cpp:1265 onward uses SeeValue at25 `{0, 100, 300, 300, 500, 900, 0}`; promotion adjustment1284-1286 and special promotion-recapture path1271-1279 retain the same 100cp lattice. Thus -34/-40/-46 all require an exchange value >=0. Margin values0..99 are one decision plateau, first upwards boundary100 (+60 from40), no downwards boundary in permitted0..40. This is quantized, not switch-disabled. No claim that every SEE call is reached.
2. CaptureFutilityMultiplier: only read2183, `ss->static_eval + tune::CaptureFutilityBase + tune::CaptureFutilityMultiplier * lmr_depth + capture_value(board, move) + history / 8 <= alpha`. Setting read is short-circuited by2178 `tune::CaptureFutilityBase > 0`; default150 `int CaptureFutilityBase = 0;`. Entire multiplier range inert while base0, including225/275. Other gates: outer2118-2119 sound/mate/rule50/root/material/bare-king exclusions;2175 `else if (prunable)` with2148 `const bool prunable = !tt_prune_v2_ || move != tt_move;`;2178 capture, !in_check,!gives_check;2179 lmr_depth<=CaptureFutilityDepth;2180-2182 compiled MateAlphaGuard condition. Once enabled, multiplier remains algebraically irrelevant at lmr_depth0.
3. CaptureFutilityDepth: only read2179 `lmr_depth <= tune::CaptureFutilityDepth`, behind the same2178 base>0 gate. Hence5/7 and whole range inert at base0. Same outer and inner gates as previous row. Unlike multiplier, changing depth changes admission of an integer depth band when base>0.
4. AspFailHighMaxReduce: only read2796 `? std::max(1, depth - std::min(asp_fail_highs, tune::AspFailHighMaxReduce)) : depth;`, guarded2795 `(tune::AspFailHighReduce != 0 && is_main())`. Default155 `int AspFailHighReduce = 0;`; max default156=3. Thus2/4 dead at defaults/PC20. When enabled, consecutive fail-high counter starts0 at2787, increments2818, clears on fail-low2808, and outer floor1 may erase further changes. A max3->2 change only matters at least3 consecutive fail-highs and sufficient depth;3->4 needs at least4, sufficient depth. Root initial aspiration narrow gate2777 is depth>=4 and not AspArmLate/reopen.
5. EvalSwingMax: sole runtime read1907 `const int swing = std::clamp(-(ss->static_eval + parent->static_eval), -tune::EvalSwingMax, tune::EvalSwingMax);`. Gate1903 `tune::EvalSwingMult != 0 && !in_check && excluded.is_none()` and default157 `int EvalSwingMult = 0;`. Thus180/220 and whole range dead with Mult0. Additional1905-1906 gates require valid parent/current static eval, parent not in check, previous move neither none, capture nor promotion. Consumer1910 `swing * tune::EvalSwingMult / 16`; when enabled, unsaturated swing never reads a changed cap into its result, and integer division/history update can erase cap changes.



## 3. PartB: 40 rows, fixed before runs
Actual UCI output lists all45 supplied settings; none absent. uci_options.txt/uci_45_check.txt preserve the handshake; settings_spec.txt preserves supplied starts/bounds/steps. Complete setting-name occurrences in setting_reads.txt. The original table remains unchanged in part_B_table.txt; absolute-value notation below rendered as abs() for table readability.
# Job5 Part B: 40-setting runtime-read table (before PartC)
PCA src/search.cpp unless another file named. All45 settings advertised in actual uci_options.txt; the other5 are PartA. Registration/default assignments are not runtime search decisions; complete textual occurrences in setting_reads.txt, UCI setter src/uci.cpp421-426 assigns/clamps and tune::refresh (search.cpp399) rebuilds reductions. No live PC tuning values read.

Meaning of smallest change: an allowed integer +/-1 CAN affect a reached local boundary unless stated otherwise; not a claim any corpus position changes. A changed scalar need not change move ordering, a cutoff, or final nodes. 'P' marks a plateau/gated/boundary-only step which can leave most nodes unaffected; population fractions are unmeasured, so 'most' is possibility, not an empirically established majority. No blanket claim that all40 are live in every tree.

Common gates: F=search.cpp1936-1937 !PV,!check,excluded.none,nonmate beta,mate_moves0,rule50+depth<100; plus each inner gate. M=2114-2119 sound-mate arms, !root,usable best score,nonpawn material,!bareking,mate_moves0,rule50 horizon; quiet/noisy/prunable gates2148 onward. L=2276-2278 mate_moves0,rule50 horizon,depth>=2,later move,!bareking,quiet or !ttPV or late move; final reduction depth clamp2297. All optional switches stay at PCA defaults except PC20 overrides recorded in metadata.

name | all runtime reads (and downstream) | expression | decision | smallest possible change / given-step plateau | dependencies
---|---|---|---|---|---
DrawJitter | search.cpp1446-1452,1634,1791,2614-2615 (compiled-out with FORGE_FIX_ROOT_DRAWN1); set_draw_jitter3079-3082; uci.cpp347,622-623 | nodeCount%(2*span+1)-span for eligible draw leaves;0 disables | repetition/fiftymove draw scores; changing value clears TT/hist caches | +1 from0 can change eligible leaf; -1 is clamped0; same modulo result may remain0 [P] | only draw detection; insufficient/stalemate without repetition/fiftymove keep0; root old branch inactive; setter clamp0..8
LmrQuietBase |311; table reads320-323,2144,2205,2279 | floor(max(0,base/100+100*log(d)*log(m)/div)) | quiet LMR and pruning's lmr_depth | +/-1 can cross some table-cell integer boundaries; +8 changes only cells within0.08 of next integer, others same [P] | quiet/div205; table d,m capped63; M,L; final clamp, other reductions; QuietExtinction branch off normally
LmrQuietDivisor |311; same consumers | same formula denominator div/100 | quiet table reductions | +/-1 possible at some cell boundary; step12 many cells floor-identical; d1 or m1 product0 totally insensitive [P] | base93; other LMR gates/clamps
LmrNoisyBase |313; consumers320-323,2144,2279 | noisy floor(max(0,base/100+100*log(d)*log(m)/div)) | noisy reduction/lmr_depth | +/-1 can cross a cell; step6 leaves most fractional bins untouched, not a no-op globally [P] | divisor333,noisy/M/L gates; depth clamp
LmrNoisyDivisor |313; same consumers | noisy denominator | noisy reduction table | +/-1 possible at boundary; step20 can round away; d1/m1 insensitive [P] | base13,noisy/M/L gates
NullMoveMinDepth |1965; downstream1985,2005 | depth>=threshold | admits null pruning/verification | +/-1 changes only one integer depth band; step1 absent elsewhere [P] | F plus !bareking,eval>=beta,staticEval gate,null allowed,previous move,nonpawn,TT upper veto,NullThreatVerify/NullSeeVeto
NullMoveBase |1972;1985,2005 | reduction=base+depth/div+min((eval-beta)/evalDiv,3) | null/verification depth | +/-1 changes reduction1 but both resulting depths<=0 call qsearch, so many shallow decisions identical [P] | same null gates; depth/div3,evalDiv200; no floor1 before search_child
NullMoveDepthDivisor |1972;1985,2005 | depth/divisor, integer | null depth | +/-1 possible (depth3:div3->4 gives1->0); step1 often same quotient; nonpositive resulting child depths all qsearch [P] | NullMoveBase5,eval reduction,admission gates
NullMoveEvalDivisor |1973;1985,2005 | min((eval-beta)/divisor,3) | null reduction | +/-1 possible at gap200; step20 leaves small gaps quotient0 and sufficiently large gaps saturated3 [P] | eval>=beta; null gates; other reduction terms
RfpDepth |1955 | depth<=threshold | RFP admission | +/-1 only depth boundary; proposed8->9 likely sparse: added depth9 requires strong eval margin; not structurally dead [P,R] | F,!bareking,Rfp guards,margin expression,finite eval
RfpMargin |1949,1958 | worsening=margin/3 when TtPruneV2 and prev static sum>2; main margin=margin*depth-improvingTerm-worsening+corr | RFP eval threshold | +/-1 can change threshold; step6 generally moves it, but only nearby eval-beta band changes cutoff; /3 plateaus [P] | F,depth<=RfpDepth,improving,TtPruneV2,RfpCorrMul,RfpNoTtPv,RfpTtGuard
RfpImproving |1958 | -setting*improving | RFP margin | +/-1 can act when improving; entire step6 multiplies0 when not improving [P] | same RFP gates and improving definition1893-1897
RazorDepth |1939 | depth<=threshold | qsearch razor admission | +/-1 changes only band; proposed2->3 requires eval+1200<alpha at added band, likely nearly inactive on O, not dead by proof [P,R] | F,!bareking; RazorBase150,Multiplier350; qsearch result<alpha required to return
RazorBase |1939 | eval+base+mult*depth<alpha | razor eligibility | +/-1 can flip strict threshold; step20 only comparison band, no effect if gate missing [P] | F,depth<=RazorDepth,!bareking; razor verification
RazorMultiplier |1939 | eval+base+mult*depth<alpha | razor eligibility | +/-1 moves by depth; step25*depth but only band crossings act [P] | same; main positive depth
FutilityDepth |2154,2206 | lmr_depth<=threshold; tight_depth<=threshold | quiet pruning admission | +/-1 changes depth band; step1 absent other bands [P] | M,quiet,!check,!givescheck,prunable; second path QuietExtinction=true (off here),eligible quiet after prior miss
FutilityBase |2149,2158,2207 | improving extra=base/2; static+base+extra+mult*lmrDepth; tight=(base+mult*tightDepth)/2 | quiet futility threshold | +/-1 possible; /2 can erase changes in extra/tight term but primary base direct; step12 acts only comparison band [P] | TtPruneV2,improving,M,MateAlphaGuard; QuietExtinction optional second path
FutilityMultiplier |2158,2207 | mult*lmr_depth; /2 tight margin | quiet futility threshold | +/-1 possible at depth>=1; any change dead at lmr_depth0; step10 often outside cutoff band [P] | same futility gates/other terms
LmpBase |327; consumer2143 | improving ? base+depth² : (base+depth²)/2 | stop generating quiet tail once move_count>=threshold | +/-1 can act when improving, nonimproving parity makes alternating steps identical; step1 cannot affect most depth/count pairs [P] | M,quiet,!skip_quiets,improving; prior late moves may never reached
HistoryPruneDepth |2165 | lmr_depth<=threshold | quiet history prune admission | +/-1 only boundary; proposed3->4 likely sparse because large negative history required, but not structurally dead [P,R] | M,quiet,!checkmove,prunable; history < -mult*depth or3/4 form
HistoryPruneMultiplier |2151-2152;2165 | TtPruneV2&&!improving ? -mult*depth*3/4 : -mult*depth | quiet prune threshold | +/-1 can flip integer history boundary; /4 plateau; step200 irrelevant outside negative-history band or absent depth gate [P] | depth (not lmr_depth in product),TtPruneV2,improving,HistoryPruneDepth
SeeQuietMultiplier |2170 | see_ge(move,-mult*lmr_depth²) | reject quiet move by SEE | +/-1 can matter e.g lmr_depth2:24->25 crosses -96->-100; at lmr0 all settings same; at lmr1 step3 keeps -21..-27 on same100cp SEE lattice [P,Q] | M,quiet,!givescheck,prunable; Board SEE lattice board.cpp25,1265-1394
SeeNoisyMultiplier |2188-2190 | threshold=-mult*depth; bypass if cached SEE nonnegative && threshold<=0 | noisy/quietcheck SEE prune | -1 from150 can matter at depth2 (-300->-298); +1 can matter at an eligible higher boundary; step12 at depth1 stays same100cp bin [P,Q] | M,else-if prunable; cached nonnegative shortcut; Board SEE lattice; not an unconditional raw comparison
SingularDepth |2214 | depth>=threshold | singular verification admission | +/-1 changes one band; step1 does nothing if no eligible TT candidate [P] | !root,mate_moves0,ttmove,excluded.none,notUpper,usable nonmateTT,ttDepth>=depth-3
SingularMargin |2216;2223,2228-2238 | singular_beta=tt_score-margin*depth | verification window/extension outcomes | +/-1 moves by depth; step1 can act but unchanged if verification bound/outcomes stay same [P] | full singular gates; child results; double threshold24,path budget; later return/negative extension conditions
IirDepth |2055,2058 | depth>=threshold; alternate >=threshold+2 | one-ply internal reduction | +/-1 changes one band in each path; step1 absent elsewhere [P] | mate_moves0,!check; no TTmove and(PV or cut); alternative TtPruneV2,TT upper,cut,!ttPV
ProbcutDepth |2018 | depth>=threshold | ProbCut admission | +/-1 changes one band,step1 often no candidate qualifies [P] | F; usable TT veto,finite beta; captures,SEE,qsearch then reduced depth-4 search
ProbcutMargin |2017;2019,2024,2036-2046 | probcut_beta=beta+margin-50*improving | SEE filter,TT veto,search window,cutoff/store | +/-1 changes window even if SEE lattice unchanged; step15 may never cross qualifying bound [P] | F,ProbcutDepth,improving,TT gate,capture candidates
QsFutilityMargin | search.cpp1695; consumer1712-1714 | futility_base=static_eval+margin, skip nonchecking nonpromotion move if futility_base+capture_value<=alpha; also raises best_score to that bound | qsearch futility skip/bound | +/-1 can flip a boundary; step14 changes threshold directly but no effect outside its14cp band or when gate absent [P] | qsearch, mate_moves0,!in_check,best_score>-MateInMaxPly; legal move; !gives_check,!promotion; existing TT/static eval can affect standpat exit
AspirationDelta | search.cpp2772; consumers2777-2780,2814,2823,2828 | initial score +/-delta window from depth4; fail-low/high reopen with delta; delta+=delta/2+4 | root aspiration window and retries | +/-1 can change a window endpoint; step2 changes endpoints but needn't change search if no affected bounds; delta/2 integer and Infinite clipping [P] | depth>=4 initial; AspArmLate/reopen; AspCappedReopen bypasses delta-based retry endpoint but not initial window; failure loop
HistoryBonusQuadratic | search.cpp331 (all uses via history_bonus); callers1572,1604,1868,2315,2372-2376,2380,2385 | min(Max,Q*d*d+L*d-32), history bonus/malus ordering updates | history learning magnitude | +/-1 possible at d1, direct bonus changes1; step3 alters3*d*d before cap; high depths saturated => no change; /2,/4 and final gravity rounding may erase changes [P] | HistoryBonusLinear/Max; cutoff/PV/research gates; TtCutoffHistory1866 optional; Threat/Pawn/HistRework optional destinations; FailLowContinuationBonus optional caller
HistoryBonusLinear | search.cpp331; same callers as previous | min(Max,Q*d*d+L*d-32) | history learning magnitude | +/-1 possible at d1; step6 alters6*d before cap; high depths saturated; downstream /2,/4 rounding [P] | same dependencies as quadratic
HistoryBonusMax | search.cpp331; same callers | caps history bonus and ensuing malus | history reward cap | +/-1 possible when raw>=Max+1 or for decrease raw>=Max; PC20 raw at d8=1936, d9=2398 so cap2212 acts d>=9; +/-180 leaves d<=8 unchanged and d>=9 capped (at fixed d) [P] | Q=24,L=54; actual caller depth may include cutoff extra ply; gravity update334-336; optional caller gates above
LmrHistoryDivisor | search.cpp2287 | if quiet, r-=clamp(history/divisor,-2,2), then depth clamp2297 | quiet move reduction adjustment | +/-1 can change quotient at boundary history=5643 (increase to5644 loses1) or history=5642 (decrease to5642 gains1); at5643 all histories[-5642,+5642] yield0; step500 leaves entire abs(history)<5143 inner region at0 and saturated tails unchanged, quotient bands matter [P] | quiet LMR gate2276-2278; HistRework alters input history; other reduction adjustments; final clamp2297 can erase r differences; negative division toward zero
CheckExtensionDepth | search.cpp2240 | qualifying gives_check at depth>=threshold adds extension1 | one-ply check extension | +/-1 changes admitted depth1 or2 band from start2; step1 live only band, no effect elsewhere [P] | nonroot,mate_moves0,gives_check, successful nonnegative SEE2241; else-if means singular extension condition preempts
LmrCutoffThreshold | search.cpp2286 | threshold>0 && child.cutoff_count>threshold adds1 reduction | extra reduction from child cutoffs | +/-1 from3 flips cutoff_count3 (down2) or4 (up4); step1 only exact-count boundary;0 disables, cannot infer counts distribution [P] | LMR gate2276-2278, sibling child cutoff_count reset1803 and increment2342, later reduction clamps2297
MaterialCorrectionWeight | search.cpp1305-1306 and1341; total scaling1330 | adds material_table*weight/100; weight>0 also enables table learning | corrected static eval and learning enable | +/-1 can change final eval when weighted aggregate near/256 correction-unit boundary; step10 often rounded out if table small/zero or aggregate same /256 quotient; nonpositive setting disables both read/update but99/101/90/110 retain update gate [P] | learned material entry, other correction terms/NonPawnCorrection/HistRework/CorrHistV2; dead_material early-return1299; eval clamp1330; CorrectionGrain256 in search.hpp415
CaptureFutilityBase | search.cpp2178 and2183 | >0 enables capture pruning; additive margin | enable capture futility and margin | smallest +1 (negative impossible0 range end), supplied +20 opens entire formerly disabled path even though margin rises; -20 clamps0 (a complete negative integer is clamped by the parser); no claim nearly dead based solely on start0 [P] | all outer2118-2119 and2175-2184 gates including multiplier250,depth6,history/8, capture_value; MateAlphaGuardtrue can disable mate-alpha case
FailLowContinuationBonus | search.cpp2381,2385 | if enabled, history_bonus(depth)*setting/100 rewards parent's move in continuation history | continuation history reward | smallest +1 can affect depth>=2 where PC20 bonus172 =>1; at depth1 bonus46, +1/+2 round0, first+3 gives1; supplied+15 gives6 at depth1 so not structurally dead; updates after4-ply use bonus/2 too [P] | fail-low best_move.none,previous move exists,moved_piece nonempty,!capture,ply>0; note code does not exclude previous promotion; update_continuation skips previous none/null continuation and halves4-ply reward (search.cpp1561-1566)
EvalSwingMult | search.cpp1903 and1910 | enabling prior quiet move eval-swing history update, bonus=clampedSwing*mult/16 | enable/scale eval-swing history reward | smallest +1 can act if abs(clampedSwing)>=16; supplied+3 yields0 for abs(clampedSwing)<=5 and nonzero from6; cannot go below0; unrelated gate can suppress all [P] | EvalSwingMax200 cap,1905-1906 valid eval/check/previous quiet gates; history gravity334-336; !excluded,!in_check

Marked rows again: all40 [P] (gating/boundary insensitivity possible, not measured population frequency). Strong additional quantization [Q]: LMR bases/divisors,NullMoveDepthDivisor,NullMoveEvalDivisor,LmpBase,SeeQuietMultiplier,SeeNoisyMultiplier,HistoryBonus coefficients/Max,LmrHistoryDivisor,MaterialCorrectionWeight,FailLowContinuationBonus,EvalSwingMult. Targeted near-dead hypotheses [R]: RfpDepth8->9,RazorDepth2->3,HistoryPruneDepth3->4. None of those three is source-proven globally dead; all are in-range one-step depth-band changes. PartC will preregister counts before running. No root-depth12 reachability cutoff is assumed: extensions/researches alter effective depths.


## 4. PartC: known answer, positive control, prediction, three checks
All runs PCA SHA above, built-in evaluation, PC20 sent first and only the listed override afterward; Threads1 Hash16, O200 at kimi5 commit5db05e09 SHA256ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8. One process per setting; each position ucinewgame/isready/wait before first4 FEN fields plus0 1; go depth12; record last depth/nodes info before bestmove. Raw full transcripts, rows, adjacent rows.meta and summaries committed for all five sets. Harness run_set.py.txt stops unknown option/invalid value/ERROR.

### Known answer and positive control
```
START known answer PASS8315168 first3[21812,26844,35173]; PCA49b56941 PC20 T1 H16 O200 depth12 built-in eval.
CONTROL LmrQuietBase101: changed node counts 200 of200; sum 8233404 first3 [12969, 15525, 26362]
first changed index 0
start {"index": 0, "fen": "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 0 1", "nodes": 21812, "bestmove": "f1e2", "last_info": "info depth 12 seldepth 19 score cp 62 nodes 21812 nps 1090600 hashfull 10 time 20 pv f1e2 g8f6 g1f3 e5d6 d2d4 e7e6 c3b5 d6b6 c2c4 f8e7 c4c5"}
control {"index": 0, "fen": "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 0 1", "nodes": 12969, "bestmove": "f1e2", "last_info": "info depth 12 seldepth 18 score cp 100 nodes 12969 nps 1441000 hashfull 4 time 9 pv f1e2 e5a5 g1f3 g8f6 e1g1 e7e6 d2d4 b8d7 a2a3 a7a6 f1e1 b7b5"}
```
Baseline matches required sum/first3. LmrQuietBase93->101 positive control changes all200 positions, so gate passes. It is not a strength comparison.

### Prediction committed ALONE before the three runs
6122ca6dbd53c4b3d3bbf363671c52b97a2f71a7:
```
2026-11-18T15:11:24Z Job5 recovery prediction, committed alone before three experimental runs. PCA49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a; PC20 first, Threads1 Hash16, built-in evaluation, O200 inputca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8, go depth12 per-position reset. PartB0a33b67e already fixed these near-dead hypotheses. Start8315168 first3[21812,26844,35173] passed; control LmrQuietBase101 changed200/200 (8233404 total).
1. RazorDepth2->3, step+1: expect0..10 of200 positions to change nodes; added depth3 gate needs eval+150+350*3<alpha, a severe deficit. Not structurally impossible.
2. RfpDepth8->9, step+1: expect0..15 changed positions; added depth9 RFP needs unusually large eval surplus after margin. Not structurally impossible.
3. HistoryPruneDepth3->4, step+1: expect0..25 changed positions; new lmr_depth4 admission still requires strongly negative history. Not structurally impossible.
No experimental results for these settings have been run or read. Ranges are predictions of corpus rarity, not proven dead settings; any miss will be reported as failure. Job6 explicitly grants20min to finish this delayed Job5 after publication tool stall.
```
### Observed results and first differing rows
```
PCA49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a; PC20 first T1 H16 built-in evaluation O200 depth12; adjacent metadata gives ordered settings.
C_start nodes 8315168 first3 [21812, 26844, 35173] changed 0 range None grade control/baseline
C_control nodes 8233404 first3 [12969, 15525, 26362] changed 200 range None grade control/baseline
first_difference {"index": 0, "start": {"index": 0, "fen": "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 0 1", "nodes": 21812, "bestmove": "f1e2", "last_info": "info depth 12 seldepth 19 score cp 62 nodes 21812 nps 1090600 hashfull 10 time 20 pv f1e2 g8f6 g1f3 e5d6 d2d4 e7e6 c3b5 d6b6 c2c4 f8e7 c4c5"}, "changed": {"index": 0, "fen": "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 0 1", "nodes": 12969, "bestmove": "f1e2", "last_info": "info depth 12 seldepth 18 score cp 100 nodes 12969 nps 1441000 hashfull 4 time 9 pv f1e2 e5a5 g1f3 g8f6 e1g1 e7e6 d2d4 b8d7 a2a3 a7a6 f1e1 b7b5"}}
C_RazorDepth3 nodes 8400962 first3 [21812, 26844, 35168] changed 122 range (0, 10) grade FAIL
first_difference {"index": 2, "start": {"index": 2, "fen": "rnbqk1nr/pppp1ppp/3b4/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 1", "nodes": 35173, "bestmove": "e5d4", "last_info": "info depth 12 seldepth 19 score cp -20 nodes 35173 nps 1034500 hashfull 21 time 34 pv e5d4 f3d4 g8e7 c2c3 e8g8 g2g3 e7g6 f1g2 f8e8 f2f4"}, "changed": {"index": 2, "fen": "rnbqk1nr/pppp1ppp/3b4/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 1", "nodes": 35168, "bestmove": "e5d4", "last_info": "info depth 12 seldepth 19 score cp -20 nodes 35168 nps 976888 hashfull 21 time 36 pv e5d4 f3d4 g8e7 c2c3 e8g8 g2g3 e7g6 f1g2 f8e8 f2f4"}}
C_RfpDepth9 nodes 8325342 first3 [21812, 26844, 35166] changed 60 range (0, 15) grade FAIL
first_difference {"index": 2, "start": {"index": 2, "fen": "rnbqk1nr/pppp1ppp/3b4/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 1", "nodes": 35173, "bestmove": "e5d4", "last_info": "info depth 12 seldepth 19 score cp -20 nodes 35173 nps 1034500 hashfull 21 time 34 pv e5d4 f3d4 g8e7 c2c3 e8g8 g2g3 e7g6 f1g2 f8e8 f2f4"}, "changed": {"index": 2, "fen": "rnbqk1nr/pppp1ppp/3b4/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 1", "nodes": 35166, "bestmove": "e5d4", "last_info": "info depth 12 seldepth 19 score cp -20 nodes 35166 nps 1255928 hashfull 21 time 28 pv e5d4 f3d4 g8e7 c2c3 e8g8 g2g3 e7g6 f1g2 f8e8 f2f4"}}
C_HistoryPruneDepth4 nodes 8315166 first3 [21812, 26844, 35173] changed 2 range (0, 25) grade PASS
first_difference {"index": 3, "start": {"index": 3, "fen": "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 0 1", "nodes": 38996, "bestmove": "e1g1", "last_info": "info depth 12 seldepth 20 score cp 43 nodes 38996 nps 1181696 hashfull 15 time 33 pv e1g1 e8g8 c1f4 h7h6 a1d1 c8e6 h2h3 f8e8 e4e5 d6e5"}, "changed": {"index": 3, "fen": "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 0 1", "nodes": 38995, "bestmove": "e1g1", "last_info": "info depth 12 seldepth 20 score cp 43 nodes 38995 nps 1181666 hashfull 15 time 33 pv e1g1 e8g8 c1f4 h7h6 a1d1 c8e6 h2h3 f8e8 e4e5 d6e5"}}
Rarity predictions are corpus observations, not structural deadness or strength. No retuning of ranges after results.
```
**Two rarity predictions failed, one passed.** RazorDepth3 and RfpDepth9 are not nearly dead by the predicted changed-position ranges on this corpus. Their large local margins did not justify predicting only a few affected positions: a rare node event can occur somewhere in many searches. HistoryPruneDepth4 changes only two node totals here, each by one node, but is not globally dead. No fitted ranges or replacement predictions after results. The PartB [R] entries remain visible as the hypotheses these runs tested, not confirmed conclusions.

## Facts
- Five PartA inactive-step mechanisms identified; QsSeeMargin's100cp SEE lattice explains its0..99 plateau rather than an off switch.
- All45 UCI names present; PartB40 rows committed before any PartC run.
- LmrHistoryDivisor5643 zero quotient for histories[-5642,+5642] confirmed from exact integer expression.
- Required baseline and positive control passed. Three experimental sets completed15:12:08UTC after prediction-only commit; grades above follow original ranges.
- No repository source modified, no PR; only own branch text evidence. No engine rebuild/change for this job.

## Suspicions
Many supplied steps can be silent at individual nodes through gates, integer rounding or unchanged branch outcomes. Population rates cannot be inferred from source alone; the failed rarity predictions demonstrate that limitation.

## What I did not do
No PC net or PC executable, no inspection of live tune values, no games/strength analysis, no exhaustive corpus sensitivity for all40 settings, no direct dynamic test of the five PartA settings, no other depths. The analytically read SEE plateau is not presented as a newly run all-moves property test.

## What I am not sure about
Frequency of each local threshold on the PC's actual workload, effect sizes at other steps, interactions between simultaneously tuned parameters, or strength. 'P' denotes possibility of gated/plateau silence, not a measured claim most nodes are silent for that option.

The PC's own net and its exe (r15d with carbon2's speed work; the search decisions are meant to be the same), other depths, games. A setting that changes nothing at one step may still act at a larger change.

## Timing, interruption and recovery
Claim13:56:41UTC. Step0 completed13:56:51; PartA/B committed before baseline/control, which ended14:03:24. A bulk evidence-tree tool call then stalled and returned 'aborted by user after3999.1s'. No experiment was running during that wait, and no ref update after that prospective tree was executed. Job6 explicitly authorized finishing delayed Job5 PartC/report within20minutes before Job6. Recovery began15:10:56UTC; retained baseline/control were not rerun. Prediction15:11 and three runs15:12; publication now uses individual bounded file writes only. Step stamps and original raw evidence preserved; original60minute window exceeded because of tool stall, not hidden as on-time completion.
Job5 was detected at13:56:05UTC on handoff0fb5848f883c5351782b9b3cccc00a02bf097046, following Job4 report8431b4c and polling from13:50:05. Job6 is already present and will be the next job, not an expired polling wait. Job2 full bulk logs remain local; this job does not claim they were all uploaded.

## Last command before report commit
`git status --short; ls -R forge-combo29/dot/job5` output follows. Local checkout is stale relative to connector commits and preserves untracked evidence; no source modification hidden.

```
 M forge-combo29/dot/job2/stamps.txt
?? forge-combo29/dot/job2/K1_base_count_search_extract.txt
?? forge-combo29/dot/job2/K1_base_diagnostic_gate.raw.txt
?? forge-combo29/dot/job2/K1_base_plain_search_extract.txt
?? forge-combo29/dot/job2/K1_matrix.py.txt
?? forge-combo29/dot/job2/K1_matrix_console.txt
?? forge-combo29/dot/job2/K1_pc_count_search_extract.txt
?? forge-combo29/dot/job2/K1_pc_diagnostic_gate.raw.txt
?? forge-combo29/dot/job2/K1_pc_plain_search_extract.txt
?? forge-combo29/dot/job2/K1_summary.json.txt
?? forge-combo29/dot/job2/K2_analysis.txt
?? forge-combo29/dot/job2/K2_base_raw.txt
?? forge-combo29/dot/job2/K2_base_search_extract.txt
?? forge-combo29/dot/job2/K2_cap.py.txt
?? forge-combo29/dot/job2/K2_console.txt
?? forge-combo29/dot/job2/K2_fault_replay.py.txt
?? forge-combo29/dot/job2/K2_fault_result.txt
?? forge-combo29/dot/job2/K2_pc_raw.txt
?? forge-combo29/dot/job2/K2_pc_search_extract.txt
?? forge-combo29/dot/job2/K2_replay_count.raw.txt
?? forge-combo29/dot/job2/K2_replay_fault.raw.txt
?? forge-combo29/dot/job2/K2_replay_plain.raw.txt
?? forge-combo29/dot/job2/K2_summary.json.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/base_count_only.patch.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/manifest.sha256.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_count_only.patch.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_planted_overrun.patch.txt
?? forge-combo29/dot/job3/
?? forge-combo29/dot/job4/
?? forge-combo29/dot/job5/
forge-combo29/dot/job5:
C_HistoryPruneDepth4.raw.txt
C_HistoryPruneDepth4.rows.txt
C_HistoryPruneDepth4.rows.txt.meta.txt
C_HistoryPruneDepth4.summary.txt
C_RazorDepth3.raw.txt
C_RazorDepth3.rows.txt
C_RazorDepth3.rows.txt.meta.txt
C_RazorDepth3.summary.txt
C_RfpDepth9.raw.txt
C_RfpDepth9.rows.txt
C_RfpDepth9.rows.txt.meta.txt
C_RfpDepth9.summary.txt
C_control.raw.txt
C_control.rows.txt
C_control.rows.txt.meta.txt
C_control.summary.txt
C_gate.txt
C_results.txt
C_start.raw.txt
C_start.rows.txt
C_start.rows.txt.meta.txt
C_start.summary.txt
part_A_reading.txt
part_B_early.txt
part_B_table.txt
prediction.txt
run_set.py.txt
setting_reads.txt
settings_spec.txt
stamps.txt
step0_gate.py.txt
step0_raw.txt
step0_summary.txt
uci_45_check.txt
uci_options.txt

```
