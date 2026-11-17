# kimi5 job 17 report — port the search patches onto the PC build (6b98f217 + pc_r15)

(1) **Step 0: MET on both builds.** Plain PC build: all 8 numbers exact. PC+PcSeries build, every new
option at its default: all 8 numbers exact and unchanged. (2) **Ports finished: 5 of 6** — RfpGuards,
FailHighBlend, LmrFine, AlphaQs, MalusE; each below with sha256 and Step 1 counts. **QsSteps: NOT
finished** (reason in "What I did NOT do"). Step 1 (a): every finished port equal on **200 of 200 O**
(nodes AND best move). Step 1 (b): every finished port equal on **341 of 341** (a0)-equal G positions.
(3) Step 2 table in its section; headline: all-five-ON vs plain PC20 on G = **0.6851** [0.6435, 0.7230].

Three plain lines: I was asked to port my six search patches onto the engine the owner's PC plays
(r15), prove the ports are the same code by known-answer identities, and measure them under PC20.
Five ports are done and every identity holds position for position; the PC20 numbers are measured.
How sure: the identities are exact (node-for-node AND best-move-for-best-move on 200/200 and 341/341),
and my PC20 base/ARR-1 rows match job 18's independently written known answers to the node.

## Step 0 (raw files in `tests_kimi5_job17/step0_pc/` and `step0_pcs/`; fresh process per number)

PC build = 6b98f217 + `pc_r15.patch` (the block of swarm file 5; saved-file sha256
`d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a` — matches file 17), g++ 13.3.0,
Release, `-DFORGE_MATE_ALPHA_GUARD=1`, machine has AVX-512+BMI2 (no FORGE_PORTABLE).
PC exe sha256 `068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4`;
series exe `d9984991fd8b5fc7bf190f4124b7420bf31dbf4d87aee3e874c6c5e8d336492e` (binary changed: yes).

| settings | bench 11 | bench 13 | bench 16 | go perft 5 | build |
|---|---|---|---|---|---|
| none | 312866 ✓ | 862329 ✓ | 3024920 ✓ | 4865609 ✓ | both |
| S14 | 242796 ✓ | 656517 ✓ | – | – | both |
| PC20 | 278024 ✓ | 587276 ✓ | – | – | both |

Settings were sent exactly as named (nothing else before the command); every `setoption` line is in
`step0_*/`*`_input.log` (e.g. `step0_pc/pc20_bench11_input.log`). `pc20.opt`/`s14.opt` are committed.

## Ports (all against 6b98f217 + pc_r15; every one applies with `patch -p1 -F0`, zero fuzz — verified
on a fresh PC copy per patch)

| port | file | sha256 | Step 1 (a) O | Step 1 (b) G |
|---|---|---|---|---|
| RfpGuards | `RfpGuards.pc.patch.txt` | fb5a7572ac642bf3e363d34c64cfc1baf50b1c3c0352945d69ed4f9009e85e39 | 200/200 | 341/341 |
| FailHighBlend | `FailHighBlend.pc.patch.txt` | 27d5a1ca1ea24b4682e90a83af08926d484e15a357f15e7ec132d0190c47de8e | 200/200 | 341/341 |
| LmrFine | `LmrFine.pc.patch.txt` | 986c10e44d25f1944c2f3dd69f7e5e46b5c21e016b779f00991837b429ed5040 | 200/200 | 341/341 |
| AlphaQs | `AlphaQs.pc.patch.txt` | e6ccc2413afb66910c42cdd703cabbdd157b2c9616d3213c1b368555e3197661 | 200/200 (a1, a2) | 341/341 (a1, a2) |
| MalusE | `MalusE.pc.patch.txt` | 9e4864281b33597f4fbb5298e052899fa15d78b82b9869e5a27e2caa4a43ef04 | 200/200 | 341/341 |
| all five | `PcSeries.patch.txt` | 5a2ab0a8d9290b1b0d391d60b96c37538c1473b1e8fcc11405634f4a9347e74e | – | – |

QsSteps: not delivered (unfinished, see below).

## Step table

| step | done? | evidence | result |
|---|---|---|---|
| 0 plain PC 8 numbers | done | `step0_pc/*.txt`, `step0.meta` | all exact |
| 0 series 8 numbers | done | `step0_pcs/*.txt`, `step0.meta` | all exact, unchanged |
| prediction (own commit, pre-Step 1) | done | `prediction.txt` (commit "kimi5 job 17 prediction") | see Prediction vs actual |
| ports: 5 patches + series, `-F0` proof | done | `port_j17.py`, `*.pc.patch.txt`, `PcSeries.patch.txt` | all apply `-F0`, all build |
| 1 (a0) plain PC S14 vs job-15 I2 | done | `rows/a0_{O,G}*`, `compare_i.txt` | O 200/200; G 341/353, the 12 all 3–7 pieces |
| 1 (a) each port ON on O | done | `rows/{rfp,fhb,lmr,aq1,aq2,mal}_O*`, `compare_i.txt` | 200/200 every port |
| 1 (b) each port ON on G | done | same on G; `rows/fhbr_{O,G}*` for FailHighBlend | 341/341 every port |
| 2 PC20 rows + bootstrap + bm-changes | done | `rows/p2_*`, `step2_table.txt` | table below |
| 2 series-default vs plain PC20 identity | done | `step2_table.txt` first line | O 200/200, G 353/353 exact |

## Step 1 details

(a0) plain PC, S14, Threads 1, Hash 16, `ucinewgame`+`isready` before every search, `go depth 12`
(`rows/a0_O_input.log` quotes every line sent): O equal 200/200 (sum 9,500,069 = I2 exactly);
G equal 341/353. The 12 differing G positions (index, pieces): 30(6) 37(3) 58(7) 76(4) 115(5) 123(4)
175(6) 193(6) 218(6) 236(3) 275(4) 309(5) — all 3–7 pieces, exactly the job's expectation (r15's
lone-king/endgame repairs). Full list with both node counts in `compare_i.txt`.

(a)/(b): each port ON exactly as in its own job (RfpGuards: job-14 `tallf.opt` = S14 + FailHighBlend 1
+ RfpNoTtPv 1 + RfpTtGuard 1 + RfpCorrMul 16, run on the series build — the standalone RfpGuards build
correctly REFUSED `FailHighBlend`, see `rows/rfp_O.stdout` of the first attempt and "Findings");
FailHighBlend: `fhb7.opt`; LmrFine: `i4.opt`; AlphaQs: `t_a1.opt` and `t_a2.opt`; MalusE: `t_m4.opt`).
Compared on the (a0)-equal mask only: **every port equal on 200/200 O and 341/341 G, nodes AND best
move.** Node sums equal the original jobs' sums on O (e.g. RfpGuards 9,777,431 = job 14's T_allF;
AlphaQs a1 6,360,271 = job 15). FailHighBlend had no job-12 G rows (job 12 ran fhb7 on O only): I built
plain 6b98f217 + the original patch now (`/tmp/fhbref`, its O rows equal job 12's 200/200, sum
9,466,559) and compared its fresh G rows: equal on 341/353 — the same 12 endgame positions as (a0),
so 341/341 on the mask. On the 12: the port differs where the BASE differs; that is r15, not the port.

## Step 2 — PC20, Threads 1, Hash 16, depth 12 (`rows/p2_*`; table printed by `step2_j17.py`,
bootstrap 95 % over positions, 2000 resamples, seed 12; base = plain PC build under PC20)

First line of `step2_table.txt`: the series build with all port options OFF equals the plain PC build
under PC20 on **200/200 O and 353/353 G** (sums 8,315,168 / 17,611,204 both) — the ports are
default-neutral under the full PC20 settings, not only at bench.

| run | O nodes (ratio, boot95, bm≠) | G nodes (ratio, boot95, bm≠) |
|---|---|---|
| RfpGuards (tallf set) | 8,269,886 (0.9946 [0.9408,1.0414], 65) | 17,407,603 (0.9884 [0.9388,1.0320], 97) |
| FailHighBlend 7 | 7,913,480 (0.9517 [0.8998,0.9985], 54) | 15,879,039 (0.9016 [0.8588,0.9409], 98) |
| LmrFine 1 (i4 set) | 8,315,168 (1.0000, 0) | 17,611,204 (1.0000, 0) |
| AlphaQs ARR 1 | 5,299,861 (0.6374 [0.5990,0.6688], 53) | 12,340,273 (0.7007 [0.6657,0.7329], 91) |
| MalusE QMP 4 | 7,904,628 (0.9506 [0.9020,0.9932], 55) | 17,168,276 (0.9748 [0.9285,1.0162], 82) |
| all five ON | 5,130,836 (0.6170 [0.5854,0.6449], 64) | 12,065,312 (0.6851 [0.6435,0.7230], 95) |

All-ON set: FailHighBlend 1 + the three guards (16) + LmrFine 1 + ARR 1 + QuietMalusPerMove 4 (the
per-port ON states combined; FHB 1 because job 14's tested guard combo ran with it).

## Hunks changed against my 6b98f217 versions, and the r15 lines that made it necessary
(line numbers in the PC tree, `/tmp/pc/src/search.cpp`; everything else applied with offsets only
and was verified by reading — AlphaQs hunk 2 and MalusE hunk 2 took fuzz 1/2 in the option table,
landing exactly right, verified):

1. RfpGuards/FailHighBlend decl+table hunks: r15 inserted the r12 option block
   (`int AspFailHighReduce` … `int PawnHistoryPvBonus`, PC lines 150–158; table lines 220–225)
   between `FailLowContinuationBonus` and `ContHist4PlyRead`. The ports anchor the new decls/entries
   at `FailLowContinuationBonus` (PC lines 148 / 219) instead of the old adjacency.
2. RfpGuards hunk 3: r15's TtPruneV2 added `rfp_worsening` (PC lines 1932–1936) and split the RFP
   condition over two lines (1937–1939). The port keeps `rfp_worsening` and adds `rfp_corr` inside the
   same margin parenthesis; `rfp_ok` gates the whole `if` (all variables in scope: `tt_move` 1804,
   `tt_capture` 1810, `ss->tt_pv` 1811, `ss->raw_eval` set at 1667/1813 region).
3. FailHighBlend hunk 7: r15's CorrHistV2 call has a fifth argument
   (`update_correction(board, depth, best_score, ss->static_eval, ss)`, PC line 2380). The port keeps
   the `ss` argument and swaps `best_score`→`raw_best` in the three guards and the call.
4. MalusE hunk 3: r15 renamed `update_quiet_history` → `update_quiet_stats` (PC line 1563) with
   PC-only pawn-history calls interleaved (`#if FORGE_PAWN_HISTORY`, PC line 1588). The port scales
   the main/threat/continuation maluses exactly as job 16; the PC-only pawn-history table keeps
   `-bonus` (compiled out by default; only relevant with PawnHistory on — see "Not sure").
5. MalusE hunk 5: r15 routes child searches through `search_child` (CuckooRep wrapper, PC line 2287)
   where the plain tree called `search`. The port sets `researched = true` at that same re-search.
6. FailHighBlend hunks 3–6 (qsearch blends, RFP return, main-search blend): applied with offsets
   only; the PC qsearch keeps `best_score > -MateInMaxPly` and the same stand-pat/TT structure, so the
   insertions are word-for-word (the `loss_floor()` variant file 18 mentions is a LATER tree, not r15).

## Findings (each with file:line and a reproducer)

- The five ports are the same code as on the plain tree: on every position where the bases agree,
  nodes and best moves are identical (`compare_i.txt`; reproduce: `python3 compare_j17.py`).
- The series patch is behaviorally invisible at defaults under PC20, not only at bench:
  `rows/p2_seriesbase_*.json` vs `rows/p2_base_*.json`, 553/553 equal.
- Cross-validation against job 18's written known answers (Opus's own r28 port): my PC20 rows
  ARR 0 O 8,315,168 [21812 26844 35173], ARR 1 O 5,299,861 [14068 11388 24787], ARR 0 G 17,611,204
  [31779 46086 84457], ARR 1 G 12,340,273 [25279 30081 45847] — all four sums and all twelve
  first-three values equal job 18's numbers to the node (`rows/p2_{base,aq1}_{O,G}.json`).
- Position 193 of G (deepseek6's long-65 flag): the PC build's depth-12 best move is c2b1 — the move
  deepseek6's depth-20 re-search called the right one. r15's repair agrees with the deeper search
  here (`compare_i.txt` line for pos 193).
- The option-refusal guard works on the PC builds: the standalone RfpGuards exe refused
  `setoption name FailHighBlend` with `info string unknown option FailHighBlend` and the run stopped
  (first `rows/rfp_O` attempt, its `.stdout`); rerun on the series exe per job 14's ON state.

Suspicions, not proven: none beyond the "Not sure" list.

## From my colleagues

- deepseek6 notes (branch for-fable-and-opus/deepseek6-work): the withdrawn S14-threads line (already
  corrected in file 17); the LAST `Threads`/`Hash` lines count — my runner sends each once, quoted in
  every `*_input.log`; the mate/PV-length lesson (long 65) and position 193 — applied above as a
  finding; the colour-symmetry result (long 66) — not needed here. glmflash5: no such branch on the
  remote (nearest: glmflash4-work; its NOTES file absent/empty at that path) — said here per the rule.
- deepseek5 notes: the stand5 self-play protocol — not needed for identities (no games this job).

## Prediction vs actual

5 of 6 ports finished — CORRECT (QsSteps unfinished, as predicted). (a0) 200/200 and 341/353 —
CORRECT. (b) 0 differ per port on the mask — CORRECT (predicted ≤4; LmrFine 0 as predicted). Step 2
all-ON G 0.6851 [0.6435, 0.7230] — inside the predicted 0.60–0.72, kill range [0.50, 0.85] not hit.

## What I did NOT do

- QsSteps: not ported. It is a 666-line observe-only counters patch keyed to the plain tree's qsearch
  call sites (its site table names plain-tree line numbers); r15 restructured quiescence
  (`qsearch_child`/`qsearch_cuckoo`, HistRework threat maps, TT-cutoff history). A correct port means
  re-pinning every counter site, plus a second (counting) build for its ON state — more than the
  remaining budget after the five behavioral ports, and it has no UCI option (compile-time only), so
  it cannot be one of the PC's play options. Listed unfinished per the job's rule, never delivered half.
  The file-17 order put it third; I did LmrFine/AlphaQs/MalusE before it — decided because they are
  behavioral (the PC can play them), job 18 builds on the AlphaQs port, and QsSteps is observe-only.
- Step 2 for AlphaRaiseReduce 2 and the Stockfish-like ARR 2 + MaxDepth 16: job 18's own step list.
- No games played (identities only), no sanitizer runs.

## What I am NOT sure about

- MalusE + HistRework 2 (PC20): the threat-keyed twin keeps the full `-bonus` malus where the
  butterfly table gets `-malus` (finding 4). Behaviorally visible only in PC20 runs, not in Step 1.
  If the twin should learn the scaled malus too, `update_rework_history` needs a split bonus/malus
  argument. The Step 2 MalusE row is measured WITH this choice.
- The 12 (a0)-differing G positions are attributed to r15's lone-king/endgame repairs by piece count
  and the job's own expectation, not by bisecting the r15 switches.
- `tallf.opt`'s `RfpCorrMul 16` (job 14's file) vs `z4_all.opt`'s 32: I used tallf, the run job 14's
  own T_allF rows came from.

## A better way

The (a)/(b) identities reuse rows from six different old jobs, each with its own opt-file quirks
(job 14's ON state silently includes FailHighBlend 1 — found only by the refusal). A single committed
`IDENTITIES.md` per patch (ON set, reference rows path, expected sums) would make the next port a
pure checklist. Checkable: it exists and the next port's report references it instead of rediscovering
the ON state from a refusal line.

## UTC stamps (from `date -u`; full detail in `tests_kimi5_job17/stamps.txt`)

run start 06:05:03 · claim 06:05:30 · colleagues read 06:06:1x · PC patch sha256 verified 06:05:5x ·
PC build 06:06:12 · Step 0 PC 06:11:41 · ports+series 06:13:42 · Step 0 series 06:14:00 · prediction
commit 06:15:11 · Step 1 queue 06:15:2x–06:16:4x · Step 2 queue 06:16:5x–06:17:2x · fhb reference
06:17:3x · comparisons 06:17:41 · report written 06:18:5x.

## Model

Kimi K3 (runtime model name: kimi-k3).
