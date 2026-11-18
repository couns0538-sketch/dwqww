# astra5 job 3 — why Forge misses a forced mate in two

## Step 0 — both executables reproduced all 12 known answers

Each bench or perft command ran in a fresh process with the built-in evaluation. The no-setoption rows used the built-in 16 MiB bench searcher. All subsequent configured searches used Threads 1 and Hash 16. [Raw inputs, UCI listings and outputs](astra5/job3/step0)

| Build | Settings | Bench 11 | Bench 13 | Perft 5 |
|---|---|---:|---:|---:|
| PC | No setoption | 312,866 | 862,329 | 4,865,609 |
| PC | S14 | 242,796 | 656,517 | — |
| PC | PC20 | 278,024 | 587,276 | — |
| PCA | No setoption | 312,866 | 862,329 | 4,865,609 |
| PCA | PC20 | 278,024 | 587,276 | — |

PC was SHA-256 `9279d02c2ea8c42875ec83a55399aeb588b72a3ae13e8067969be2cee8219306`. PCA was `49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a`.

## Step 1 — depth ladders on P

P is `2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1`. Of 59 legal first moves, only `g3g6` guarantees mate on White’s next turn. After all 34 legal Black replies, python-chess verified at least one checkmate in one. All suggested mating replies were correct. Four replies also admit another mating move. [Exhaustive proof and alternate mates](astra5/job3/mate-proof.txt)

Both ladders use the plain PC binary. A fresh `ucinewgame` and a verified `readyok` precede each `go depth D`. The table reads the score and nodes from the final info line carrying depth and nodes, and takes the move from `bestmove`. Dot’s seven reference rows all matched in move, score and nodes. S14 first reported `g3g6` and mate 2 at depth 16 and retained it at depths 17–20. PC20 still played `f6h5` at depth 20. [Reference check](astra5/job3/step1/checks.txt) · [Raw transcripts](astra5/job3/step1)

| Depth | PC20 move | PC20 score | PC20 nodes | S14 move | S14 score | S14 nodes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | f6h5 | cp 78 | 262 | f6h5 | cp 78 | 262 |
| 2 | f6e8 | cp 89 | 408 | f6e8 | cp 89 | 408 |
| 3 | f6h5 | cp -4 | 658 | f6h5 | cp -4 | 680 |
| 4 | f6h5 | cp 220 | 961 | f6h5 | cp 220 | 975 |
| 5 | f6h5 | cp 220 | 1100 | f6h5 | cp 220 | 1115 |
| 6 | f6h5 | cp 337 | 1562 | f6h5 | cp 337 | 1570 |
| 7 | f6h5 | cp 465 | 2358 | f6h5 | cp 344 | 1996 |
| 8 | f6h5 | cp 663 | 5647 | f6e8 | cp 214 | 5500 |
| 9 | f6h5 | cp 636 | 7436 | f6h5 | cp 576 | 11019 |
| 10 | f6h5 | cp 706 | 12150 | f6h5 | cp 530 | 15707 |
| 11 | f6h5 | cp 653 | 25366 | f6h5 | cp 570 | 25059 |
| 12 | f6h5 | cp 713 | 52600 | f6h5 | cp 634 | 39758 |
| 13 | f6h5 | cp 722 | 60141 | f6h5 | cp 640 | 64611 |
| 14 | f6h5 | cp 731 | 83427 | f6h5 | cp 647 | 84524 |
| 15 | f6h5 | cp 665 | 120238 | f6h5 | cp 721 | 147253 |
| 16 | f6h5 | cp 736 | 182707 | g3g6 | mate 2 | 240516 |
| 17 | f6h5 | cp 826 | 347819 | g3g6 | mate 2 | 240693 |
| 18 | f6h5 | cp 802 | 440663 | g3g6 | mate 2 | 240899 |
| 19 | f6h5 | cp 885 | 686815 | g3g6 | mate 2 | 241079 |
| 20 | f6h5 | cp 916 | 1052250 | g3g6 | mate 2 | 241262 |

## Step 2 — what each switch changes

The source inventory and exact ordered manifest were committed before the combined control. The control uses one override per manifest entry. It includes genuine off switches, highest or lowest supported thresholds, removal of PC-specific modifiers and a mate-protective condition. Main LMR, the move picker, ordinary TT cutoffs and quiescence have no universal UCI off switch. [Full inventory with quoted guards and UCI ranges](astra5/job3/switches.txt) · [Ordered control manifest](astra5/job3/switches.tsv)

| PC option | Override | Effect in this experiment |
|---|---:|---|
| RfpDepth | 0 | Disables main-search reverse futility. |
| RazorDepth | 0 | Disables razoring. |
| FutilityDepth | 0 | Lowest gate. Reduced depth zero stays eligible. |
| CaptureFutilityDepth | 0 | Already inactive under the default CaptureFutilityBase 0. |
| HistoryPruneDepth | 0 | Lowest gate. Reduced depth zero stays eligible. |
| NullMoveMinDepth | 10 | Defers null-move pruning until internal depth 10. |
| ProbcutDepth | 20 | Defers the reduced capture search until internal depth 20. |
| SingularDepth | 20 | Defers singular verification until internal depth 20. |
| IirDepth | 20 | Defers internal iterative reduction until internal depth 20. |
| LmpBase | 20 | Raises the quiet move-count threshold. No off sentinel. |
| SeeQuietMultiplier | 200 | Relaxes quiet-move SEE. At reduced depth zero, the threshold stays zero. |
| SeeNoisyMultiplier | 1000 | Relaxes noisy-move SEE. The test remains present. |
| QsFutilityMargin | 1000 | Relaxes the quiescence futility margin. |
| QsSeeMargin | 500 | Permits larger losing exchanges in quiescence. |
| LmrQuietBase | 0 | Lowers the quiet LMR table offset. |
| LmrQuietDivisor | 500 | Reduces the quiet LMR table’s depth/move-count term. |
| LmrNoisyBase | 0 | Lowers the noisy LMR table offset. |
| LmrNoisyDivisor | 800 | Reduces the noisy LMR table’s depth/move-count term. |
| LmrCutoffThreshold | 0 | Disables only the extra reduction for child cutoffs. |
| TtPruneV2 | false | Removes the PC-specific TT, futility, RFP and IIR modifiers. |
| MateAlphaGuard | false | Removes the mate-alpha futility protection. |
| CuckooRep | false | Removes the upcoming-repetition wrapper. |
| SoundMatePruning | true | Protects the shallow pruning block on PV, in check or at mate alpha. |

The two additional PCA tests each turned on one selective RFP guard. `RfpTtGuard 1` protects nodes with a quiet TT move and `RfpNoTtPv 1` protects TT-PV nodes.

## Combined control — mate at depth 3

The committed 23 overrides together first produced `g3g6`, mate 2 at depth 3 (2,620 nodes). They reproduced it at depth 4 (2,806 nodes) and every subsequent requested depth through 20. The required positive control passed. [Complete control ladder](astra5/job3/control-readback.md) · [Ordered commands and raw engine output](astra5/job3/control/all.raw.txt)

## Prediction — both parts missed

I forecast `IirDepth 20` would recover the mate first, at depth 5. That setting showed no mate through depth 16. `SingularDepth 20` and `QsSeeMargin 500` tied at depth 16. The prediction commit followed the complete control and preceded every single-switch search. [Frozen prediction](astra5/job3/prediction.txt)

## Step 3 — individual switch results

Every ladder applied just the indicated override after PC20 and searched the same position on the named build. The earliest hits were both at the final requested depth, so neither arm yielded two consecutive hits within the ladder. All 400 rows were checked against their raw UCI transcripts. [Raw ladders and executable identities](astra5/job3/step3)

| Build | Switch | Value(s) after PC20 | First mate depth | Score | Nodes there | First consecutive pair | Depths read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PC | rfp | RfpDepth 0 | not by 16 | — | — | — | 16 |
| PC | razor | RazorDepth 0 | not by 16 | — | — | — | 16 |
| PC | futility | FutilityDepth 0 | not by 16 | — | — | — | 16 |
| PC | cap_futility | CaptureFutilityDepth 0 | not by 16 | — | — | — | 16 |
| PC | history | HistoryPruneDepth 0 | not by 16 | — | — | — | 16 |
| PC | null | NullMoveMinDepth 10 | not by 16 | — | — | — | 16 |
| PC | probcut | ProbcutDepth 20 | not by 16 | — | — | — | 16 |
| PC | singular | SingularDepth 20 | 16 | mate 2 | 71678 | — | 16 |
| PC | iir | IirDepth 20 | not by 16 | — | — | — | 16 |
| PC | lmp | LmpBase 20 | not by 16 | — | — | — | 16 |
| PC | quiet_see | SeeQuietMultiplier 200 | not by 16 | — | — | — | 16 |
| PC | noisy_see | SeeNoisyMultiplier 1000 | not by 16 | — | — | — | 16 |
| PC | qs_futility | QsFutilityMargin 1000 | not by 16 | — | — | — | 16 |
| PC | qs_see | QsSeeMargin 500 | 16 | mate 2 | 205800 | — | 16 |
| PC | lmr_quiet_base | LmrQuietBase 0 | not by 16 | — | — | — | 16 |
| PC | lmr_quiet_divisor | LmrQuietDivisor 500 | not by 16 | — | — | — | 16 |
| PC | lmr_noisy_base | LmrNoisyBase 0 | not by 16 | — | — | — | 16 |
| PC | lmr_noisy_divisor | LmrNoisyDivisor 800 | not by 16 | — | — | — | 16 |
| PC | lmr_cutoff | LmrCutoffThreshold 0 | not by 16 | — | — | — | 16 |
| PC | tt_prune_v2 | TtPruneV2 false | not by 16 | — | — | — | 16 |
| PC | mate_alpha_guard | MateAlphaGuard false | not by 16 | — | — | — | 16 |
| PC | cuckoo | CuckooRep false | not by 16 | — | — | — | 16 |
| PC | sound_mate | SoundMatePruning true | not by 16 | — | — | — | 16 |
| PCA | RfpTtGuard | RfpTtGuard 1 | not by 16 | — | — | — | 16 |
| PCA | RfpNoTtPv | RfpNoTtPv 1 | not by 16 | — | — | — | 16 |

Earliest confirmed positive mate score with g3g6 at D16: PC singular, PC qs_see.

## Step 4 — where the depth-16 search lost the mate

**An unverified null-move cutoff after the late-move reduction hid `g3g6` in PC20’s final depth-16 iteration.** The null probe reached quiescence, which reused an upper bound from a search that could not generate the quiet mating move. The two winning settings changed the root move order and the remaining search depth enough for the null probe itself to see the threat.

| PC build, PC20 plus indicated override | Root move number for `g3g6` on first relevant pass | Reduced depth after `g3g6` | Depth after Black’s null move | What the probe returned to Black | Final depth-16 result |
|---|---:|---:|---:|---|---|
| Ordinary PC20 | 22 | 11 | 0 | −291, sufficient for a cutoff | `f6h5`, cp 736, 182,707 nodes |
| SingularDepth 20 | 4 | 14 | 2 | −31997, null cutoff rejected | `g3g6`, mate 2, 71,678 nodes |
| QsSeeMargin 500 | 4 | 14 | 2 | −31997, null cutoff rejected | `g3g6`, mate 2, 205,800 nodes |

**Ordinary PC20.** In the last root pass, `f6h5` had set White’s alpha to +736. Forge tried `g3g6` as move 22 and searched Black’s reply at reduced depth 11, in a window of [−737, −736]. Black’s raw static evaluation was −57 and its corrected search evaluation was −106. The null-move reduction then sent the search to depth 0. White’s quiescence probe found a depth-zero TT upper bound of +291 in a [736, 737] window. It returned immediately. From Black’s perspective −291 cleared beta −736, and internal depth 11 allowed the cutoff without verification. From the root, +291 failed to beat +736, so LMR did not trigger a full-depth re-search. Neither `f7g6` nor `c6e5` was visited on that call. The UCI maximum `NullMoveMinDepth 10` still permits a null move at internal depth 11. The null cutoff is at PC `src/search.cpp:1943–1976` and the root re-search predicate is at `src/search.cpp:2275–2287`. [PC20 events, lines 477–492](astra5/job3/step4/rows/trace-pc20.events.txt#L477)

**Where +291 came from.** In iteration 11 of the same depth-16 search, the same position after `g3g6` and a null move entered quiescence outside check, with no TT hit. Quiescence exhausted its moves and returned +291 below alpha +354. The quiet move `g6h7#` is absent from the non-check quiescence move picker. Its capture-generation path is in PC `src/search.cpp:666–672,751–761`. The qsearch return stores a depth-zero upper bound here, and `src/search.cpp:1653–1657` allows that bound to cut the later probe. The trace shows the earlier search and the later matching entry. It does not record the entire TT replacement history between them. [Earlier quiescence visit](astra5/job3/step4/rows/trace-pc20.events.txt#L253)

**Both winning arms.** The root reached `g3g6` fourth, with 14 plies remaining after LMR. The first null probe reached depth 2. Main search required sufficient TT depth for a cutoff (`src/search.cpp:1847–1851`), so the depth-zero upper bound did not terminate the search. White searched `g6h7#` and returned a mate score. Black’s null cutoff failed and Forge searched real replies. Both `g3g6 c6e5 g6h7#` and `g3g6 f7g6 e5g6#` appear in each winning trace. [SingularDepth 20](astra5/job3/step4/singular-iteration16.txt) · [QsSeeMargin 500](astra5/job3/step4/qs_see-iteration16.txt)

The observer reproduced all 52 uninstrumented ladder rows across ordinary PC20 and the two tied arms. With tracing enabled, all three depth-16 rows again matched in move, score and nodes. Each event carries a call ID, iteration, path, remaining depth, window and evaluation. `search_static=NA` means the engine returned before assigning a corrected static evaluation on that call. `raw_static` is an independent diagnostic evaluation. The rows and trace patch are plain text. [Parity checks](astra5/job3/step4/rows/trace-parity.txt) · [Trace patch](astra5/job3/step4/trace_on_pc.patch.txt)

## Facts

The combined control recovered the forced mate at depth 3. Among the 25 tested single changes, only SingularDepth 20 and QsSeeMargin 500 recovered it by depth 16. Both won at the last depth tested. On ordinary PC20 the immediate missed line is explained by root move order, LMR, the depth-zero null probe, the quiescence TT cutoff and the failed root re-search.

## Suspicions

An earlier change to history or TT state may account for `g3g6` moving from 22nd to fourth in the two winning runs. The traces cover selected paths and show different windows before the final iteration. They do not identify the first causative change elsewhere in the tree. In particular, the ProbCut SEE rejection of `e5g6` in a winning arm was followed by ordinary search of that same move.

## What I did not do

I did not change the repository engine, tune an option for play, run games, or trace every branch of the tree. I did not search for a minimal combination of options that reproduces the depth-3 control.

## What I am not sure about

This measurement explains a specific failure of PC20 with the built-in evaluation on P. It does not establish which individual option first changed the root ordering or how often this happens on other positions or networks. Both single-switch wins occurred at depth 16. Their persistence at greater depths was outside the requested ladder.

## Pre-commit working tree and evidence files

```text
$ git status --short && ls -R forge-combo29/astra5/job3
 A forge-combo29/REPORT_astra5_job3.md
M  forge-combo29/astra5/job3/stamps.txt
forge-combo29/astra5/job3:
control
control-readback.md
ladder.py
mate-proof.txt
prediction.txt
prove_mate.py
read_ladders.py
run_switches.py
stamps.txt
step0
step0-pc.txt
step0-pca.txt
step1
step1-readback.md
step3
step3-readback.md
step4
switches.tsv
switches.txt

forge-combo29/astra5/job3/control:
all.meta
all.raw.txt
all.tsv

forge-combo29/astra5/job3/step0:
pc-PC20-bench-11.txt
pc-PC20-bench-13.txt
pc-S14-bench-11.txt
pc-S14-bench-13.txt
pc-no-setoption-bench-11.txt
pc-no-setoption-bench-13.txt
pc-no-setoption-go-perft-5.txt
pc-uci.txt
pca-PC20-bench-11.txt
pca-PC20-bench-13.txt
pca-no-setoption-bench-11.txt
pca-no-setoption-bench-13.txt
pca-no-setoption-go-perft-5.txt
pca-uci.txt

forge-combo29/astra5/job3/step1:
PC20.meta
PC20.raw.txt
PC20.tsv
S14.meta
S14.raw.txt
S14.tsv
checks.txt

forge-combo29/astra5/job3/step3:
RfpNoTtPv.meta
RfpNoTtPv.raw.txt
RfpNoTtPv.tsv
RfpTtGuard.meta
RfpTtGuard.raw.txt
RfpTtGuard.tsv
cap_futility.meta
cap_futility.raw.txt
cap_futility.tsv
cuckoo.meta
cuckoo.raw.txt
cuckoo.tsv
futility.meta
futility.raw.txt
futility.tsv
history.meta
history.raw.txt
history.tsv
iir.meta
iir.raw.txt
iir.tsv
lmp.meta
lmp.raw.txt
lmp.tsv
lmr_cutoff.meta
lmr_cutoff.raw.txt
lmr_cutoff.tsv
lmr_noisy_base.meta
lmr_noisy_base.raw.txt
lmr_noisy_base.tsv
lmr_noisy_divisor.meta
lmr_noisy_divisor.raw.txt
lmr_noisy_divisor.tsv
lmr_quiet_base.meta
lmr_quiet_base.raw.txt
lmr_quiet_base.tsv
lmr_quiet_divisor.meta
lmr_quiet_divisor.raw.txt
lmr_quiet_divisor.tsv
mate_alpha_guard.meta
mate_alpha_guard.raw.txt
mate_alpha_guard.tsv
noisy_see.meta
noisy_see.raw.txt
noisy_see.tsv
null.meta
null.raw.txt
null.tsv
probcut.meta
probcut.raw.txt
probcut.tsv
qs_futility.meta
qs_futility.raw.txt
qs_futility.tsv
qs_see.meta
qs_see.raw.txt
qs_see.tsv
quiet_see.meta
quiet_see.raw.txt
quiet_see.tsv
razor.meta
razor.raw.txt
razor.tsv
rfp.meta
rfp.raw.txt
rfp.tsv
singular.meta
singular.raw.txt
singular.tsv
sound_mate.meta
sound_mate.raw.txt
sound_mate.tsv
tt_prune_v2.meta
tt_prune_v2.raw.txt
tt_prune_v2.tsv

forge-combo29/astra5/job3/step4:
build.txt
inspect_trace.py
pc20-iteration16.txt
qs_see-iteration16.txt
readback.md
rows
singular-iteration16.txt
trace_check.py
trace_on_pc.patch.txt

forge-combo29/astra5/job3/step4/rows:
parity-pc20.meta
parity-pc20.raw.txt
parity-pc20.tsv
parity-qs_see.meta
parity-qs_see.raw.txt
parity-qs_see.tsv
parity-singular.meta
parity-singular.raw.txt
parity-singular.tsv
trace-parity.txt
trace-pc20.events.txt
trace-pc20.meta
trace-pc20.raw.txt
trace-pc20.tsv
trace-qs_see.events.txt
trace-qs_see.meta
trace-qs_see.raw.txt
trace-qs_see.tsv
trace-singular.events.txt
trace-singular.meta
trace-singular.raw.txt
trace-singular.tsv
```
