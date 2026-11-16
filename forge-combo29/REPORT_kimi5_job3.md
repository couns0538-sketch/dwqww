# REPORT_kimi5_job3 — eight search switches: prediction from code, counters, repeat test

(1) CONTROL: 200 of 200 identical nodes (off runA vs runB vs runC at d12; also identical on the pristine
    base build; total 12,573,318 nodes). Known numbers on the counter build, all switches off:
    bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all four match.
(2) My pre-measurement suspect was AspCappedReopen; the measured tree factors do NOT show its predicted
    monotone turn (d8 1.037, d12 0.979, d16 1.031, inside its kill range everywhere, loops per failed
    search 6.9 -> 8.2). The switch that DID blow through its kill range is ContHist4PlyRead: +1.4 % ->
    +4.1 % -> +10.5 % nodes at d8/d12/d16, monotone, dead at d16. For the suspect: acr factors stay in
    range (against: no depth turn); for ch4: the d16 factor 1.105 against its [0.93, 1.07] kill range
    (for: it is the depth-growing cost inside the six).
(3) Two matches asked: (a) glmflash5, built-in net, 80,000 nodes/move: ContHist4PlyRead alone vs all-off,
    600 games; (b) owner's PC, today's net, 250,000 nodes/move: the six MINUS ContHist4PlyRead vs the six,
    2,000 games. Details in section "The two matches".

How sure: sure of every counter number (three identical control runs, zero-noise floor at fixed depth,
behavior-identical rebuilds proven 200/200 twice). Tree factor is cost, not strength: the Elo reading of
a node tax is a hypothesis until the two matches run.

## Step 0 (file names of raw output)
- Base build: step0_bench11.txt, step0_bench13.txt, step0_bench16.txt, step0_perft5.txt — all four match.
- Counter build: step0ctr_bench13.txt, step0ctr_bench16.txt, step0ctr_perft5.txt (+bench 11 in the run
  log) — all four match, every switch off. Tunable build: tun_step0_*.txt — all four match at default.

## Step table

| step | done? | evidence | result |
|---|---|---|---|
| Prediction, own commit before measuring | done | tests_kimi5_job3/PREDICTION.md, commit "kimi5 job 3 prediction" | pushed before any engine run of part 2 |
| Step 0 base build | done | step0_*.txt | 312866 / 862329 / 3024920 / 4865609 |
| Counter patch + proof | done | counters.patch.txt (applies with patch -p1, --fuzz=0, byte-identical result) | same four numbers on the counter build |
| Control, off twice | done | k5_j3_off_d12_fresh_runA/runC.json (+runB from the matrix) | 200/200 identical nodes, three runs |
| d8 fresh, 10 configs | done | k5_j3_*_d8_fresh.json | table below |
| d12 fresh, 10 configs | done | k5_j3_*_d12_fresh.json | table below |
| d16 fresh | partly | off, ch4, acr, hd, smp, six only | lmrs/thr/ntv/nsv singles at d16 NOT run (time); said plainly |
| Repeat test d12, carried tables, twice | done | k5_j3_*_d12_repeat_r1/r2.json | 200/200 nodes AND bestmove for all eight |
| Pairs same-node co-fire | not done | — | global counters cannot see "same node"; suppression numbers given instead; better-way section |
| Tunable patch + proof | done | tunable_AspReopenMargin.patch.txt, tun_step0_*.txt, wiring control, 200/200 vs pristine | default 13 unchanged: known numbers + 200/200; margin 0/13/100 give 279,937/407,550/469,476 nodes on 8 positions (option wired) |

## Measured tree factors (nodes ON / nodes OFF, 200 UHO positions, empty table per search)

| switch | d8 | d12 | d16 | verdict per prediction (dead/alive, those words) |
|---|---|---|---|---|
| LmrDeeperShallower | 0.964 | 0.895 | — | alive, alive (d16 not measured) |
| ThreatHistory | 1.027 | 1.034 | — | alive, alive (direction wrong: grows, not saves) |
| NullThreatVerify | 1.000 | 0.997 | — | alive, alive; FIRE prediction dead (0.004 %/0.019 % of nodes vs kill floor 0.05 %) |
| NullSeeVeto | 1.002 | 0.989 | — | alive, alive; FIRE prediction dead (0.021 %/0.073 % vs kill floor 0.1 %) |
| ContHist4PlyRead | 1.014 | 1.041 | 1.105 | alive, alive, DEAD (above [0.93,1.07]) — the depth-growing cost |
| AspCappedReopen | 1.037 | 0.979 | 1.031 | alive all three; FIRE prediction dead (90-96 % of searches vs [5 %,70 %]) |
| HindsightDepth | 0.996 | 1.039 | 1.056 | alive all three; fire alive (1.9/2.5/2.8 % inside [0.2 %,5 %]) |
| SoundMatePruning | 1.097 | 0.999 | 1.037 | DEAD at d8 (above [0.97,1.06]), alive d12, alive d16 |
| six-bundle | 1.023 | 0.986 | 0.994 | alive all three |

Fire rates (counter sums per 1000 nodes; k5_j3_*.json, per-position deltas in the records):
- lmrs: deeper 2.6/3.3/3.8 (d16 in six), shallower 0.8/0.7/0.6 — shallower dominates the saved re-searches.
- thr: reads 5572/5409/5357, nonzero 2487/3906/4452 — the table fills with depth as predicted; read share
  with nonzero bonus 45 %/72 %/83 % (my fire prediction was a NODE share, not exactly measurable with
  global counters; on the read-share reading it sits inside [8 %,80 %]: alive).
- ntv: gates 0.04/0.19/0.03 — essentially never fires at d8/d12 on these positions; verification cost ~0.
- nsv: calls 6.7/13.5/19.1, vetoes 0.21/0.73/1.40 — vetoes ~5 % of calls.
- ch4: adds 334/522/563 per 1000 nodes (33 %/52 %/56 % of nodes; kill [20 %,90 %]: alive all three).
- acr: searches with >=1 capped reopen 181/192/193 of 200; reopens per search 4.8/6.7/8.0 (max 35/37/48);
  per failed search 5.3/6.9/8.2.
- hd: considered 234/243/246 per 1000 nodes (a quarter of all nodes are children of reduced moves!),
  minus 16/20/21, plus 2.5/5.0/6.9, tt-blocked 6.9/4.3/3.6 — the minus arm outweighs plus ~4:1.
- smp: arm move-iterations 312/178/107 per 1000 nodes (counter unit = move-loop iterations under an arm,
  not nodes; divided by ~4 iterations/node gives ~8 %/4 %/3 %, inside [0.8 %,10 %]: alive, unit stated).

## Findings (file and line; command to see it again)

- F1. ContHist4PlyRead's cost GROWS with depth: +1.4 %/+4.1 %/+10.5 % (d8/d12/d16), dead at d16.
  Read site: search.cpp:1330-1341 (the FORGE_SEARCH_SPEED2 branch passes the cont4 pointer; weight 1/2 at
  the #else twin, search.cpp:1346-1349). It feeds the SAME history score that sets LMR r
  (search.cpp:2002) and the history-prune threshold (search.cpp:1880, threshold scales with depth).
  Command: `python3 k5_j3.py /tmp/k5cb/forge first200.fens ch4 16 fresh 200`, compare nodes with off.
  Suspicion, not proven: the turn comes from the depth-scaled history-prune line crossing more moves when
  the cont4 term is added; counters cannot see move quality.
- F2. The six-bundle is strongly SUB-ADDITIVE: measured d16 factor 0.994 while the two costliest members
  alone measure 1.105 (ch4) and 1.031 (acr). The bundle is NOT the product of its singles (product of the
  measured d16 singles is >= 1.14). lmrs's d12 saving (-10.5 %) and pair overlaps suppress it.
  Evidence: analysis_summary.txt d16 table.
- F3. NullThreatVerify and NullSeeVeto almost never act on UHO openings at d8-d12 (gates 0.004-0.019 %,
  vetoes 0.02-0.07 % of nodes): their measured match results, good or bad, are decided by a few hundred
  nodes per million. Suppression in the bundle: ntv gates fall 0.19 -> 0.03 per 1000 from single to six
  (the veto and the other switches steal gate cases: the pair overlap of prediction (a)1, seen as sums).
- F4. HindsightDepth adjusts the depth of 1.9-2.8 % of all nodes, minus:plus ~4:1, and its tree cost
  GROWS with depth (0.996/1.039/1.056): the plus arm's extra plies get more expensive. Not in the six, so
  it cannot explain the bundle's 250k result — but its own matches should expect a node tax at depth.
- F5. SoundMatePruning's d8 factor 1.097 killed my d8 reading; d12 0.999, d16 1.037. Non-monotone: the
  arm share falls with depth (prediction held) while subtree sizes grow (cost held); the two cross.
- F6. Aspiration windows fail far more often than I predicted: 90-96 % of searches have >=1 capped reopen
  (predicted 20-40 %, dead). UHO openings are sharp and the window is +/-18 (search.cpp:2405-2409,
  AspirationDelta 18 at search.cpp:70). Reopens per failed search grow 5.3 -> 6.9 -> 8.2 with depth.
- F7. REPEAT TEST: 200/200 identical nodes AND identical bestmove for every one of the eight switches,
  tables carried, one process per run, two runs. On THIS tree all eight are deterministic functions of
  position + limits + carried state — prediction (c) confirmed; the old agent's mismatches are more
  likely in its replay than in this code (see "answers to A/B/C" for what the code ruled out).
- F8 (method). A counter placed in the `#else` twin of an `#if FORGE_SEARCH_SPEED2` function is dead code
  in the release build (CMakeLists.txt:34 sets FORGE_SEARCH_SPEED2=1): my first ch4 counter measured
  exactly 0 while the option was on. Caught because zero was implausible and tested directly. The fixed
  counter build is behavior-identical (200/200 on all five reruns) — counters did not change behavior.

## Suspicions, not proven
- S1. ch4's turn comes via the depth-scaled history-prune threshold (search.cpp:1880) and the LMR clamp
  (search.cpp:2002): plausible mechanism, not measured directly.
- S2. The six-bundle's d16 suppression may be mostly LmrDeeperShallower's d16 saving — its d16 single is
  unmeasured (not done, time). If lmrs-d16 saves ~-10 %, the bundle arithmetic roughly closes.
- S3. ThreatHistory's +3 % growth with a filling table (nonzero reads 45->83 %) hints its ordering noise
  costs nodes at depth on fresh histories; in a game the table is warm, so the fixed-depth empty-table
  measurement may overstate its cost. Not proven either way.

## The two matches asked (Part 3.1)
Best explanation for "positive at 20,000, negative in the bundle at 250,000": ContHist4PlyRead — the only
switch inside the six whose measured cost grows monotonically with depth and leaves its kill range at
d16 (+10.5 % nodes). At fixed nodes that tax is paid in reached depth. How sure: the cost growth is
counter-proven; that it explains the ELO sign is a hypothesis (tree factor is not Elo), and F2 says the
bundle suppresses singles, so ch4's guilt inside the bundle is exactly what match (b) tests.
1. glmflash5, built-in net, 80,000 nodes/move, Threads 1, Hash 16: side A `setoption name ContHist4PlyRead
   value true`, side B all defaults. 600 games (= 300 opening pairs), count how every game ENDED first,
   95 % interval over pairs. Question: does ch4 still hold at 80k nodes?
2. Owner's PC, today's net, 250,000 nodes/move: side A = the six (lmrs+thr+ntv+nsv+ch4+acr on), side B =
   the same five WITHOUT ch4. 2,000 games. If five-of-six beats six, ch4 is the depth poison in the bundle.
What my counters can NOT tell: node counts measure COST only. A smaller tree is not a stronger tree
(lmrs saves 10.5 % at d12 — if it saves by re-searching the wrong moves, it loses Elo while "winning" the
factor table), and a bigger tree is not weaker per Elo if the extra nodes are well spent. The exchange
rate between tree size and move quality is set by matches, not counters.

## Part 3.2 — the tunable patch
tunable_AspReopenMargin.patch.txt: makes the capped-reopen margin (search.cpp anonymous-namespace
constexpr 13) a UCI spin `AspReopenMargin`, default 13, min 0, max 400. Proof at default: bench 11/13/16
and perft 5 = the four known numbers (tun_step0_*.txt); 200/200 identical nodes vs the pristine build at
d12 (k5_j3_off_d12_fresh_tunablebuild.json vs ..._basebuild.json). Wiring control: with AspCappedReopen
on, margin 0/13/100 give 279,937/407,550/469,476 nodes on the same 8 positions (the option arrives and
acts). HONEST POSTSCRIPT: this was Part 1's nominated constant; Part 2 refuted the mechanism that
nominated it (no monotone acr turn). The constant the MEASURED data points at is the cont4 weight 1/2
(search.cpp:1348), which does not scale with depth while the cost it causes does — naming it; a second
tunable was not built (time; the one asked for was delivered and proven).

## From my colleagues
- deepseek5 (notes through job 5, REPORT_deepseek5_job5.md read): P1 (an illegal token inside
  `position ... moves ...` flips the side; uci.cpp position handler applies it without a legality check)
  — my harness legality-checks every bestmove with python-chess (0 illegal in 14,000+ searches this job),
  and B21/B27 (`infinite` overrides depth) noted; neither bit this job (no infinite, no illegal tokens).
  Its job-4 lesson (a harness that cannot see what it reports as absent) is why the wiring control exists.
- glmflash5 (notes through job 4 on cursor/glmflash5-work-cb5c, REPORT_glmflash5_job4.md read): check the
  `uci` option list for every name BEFORE trusting a run — done: all eight option handlers verified in
  uci.cpp (403-417, 431, 439) and every input log shows the setoption lines (k5_j3_*_input.log).
  MateAlphaGuard stays compile-gated: not needed here.
- glmflash5's branch is NOT for-fable-and-opus/glmflash5-work (that ref does not exist); it is
  cursor/glmflash5-work-cb5c. Said here because the run instructions name the first.

## What I did NOT do
- d16 singles for lmrs, thr, ntv, nsv (only off, ch4, acr, hd, smp, six at d16): time.
- Same-node pair co-fire counts (needs a per-node pair counter; named in "a better way").
- A second tunable patch (the cont4 weight 1/2): named, not built.
- Any game, any Elo, any wall-clock claim: fixed-depth node counts only, by design.

## What I am NOT sure about
- Whether ch4's +10.5 % at d16 is paid back by ordering quality in games (the whole point of match 1).
- Whether the six-bundle's d16 suppression closes arithmetically once lmrs-d16 is measured (S2).
- Whether the repeat test's 200/200 extends to the old agent's exact replay loop (different runner,
  possibly wall-clock elements): my determinism claim covers THIS tree, THIS harness.

## A better way
- A per-node PAIR counter (one uint64 incremented when two named switches both fired at the same node)
  answers the job's "both fired at the same node" directly; global sums cannot. Cost: one more field per
  pair, same patch shape.
- The ch4 dead-counter fault (F8) generalizes: every counter should ship with a "must be nonzero" smoke
  assertion on one position before a matrix runs — 30 seconds, catches dead-code placement at once.

## Answers to A, B, C (job file's corrections to jobs 1/2)
- A. AGREE. clock_plan.hpp: `hard = std::min(available * hard_percent / 100, soft * hard_soft_multiple)`
  is computed while soft is still 0 (two lines before `soft = std::max<std::int64_t>(1, ...)`), so with
  no increment hard = min(6, 0) = 0 -> raised to 1: hard is 1 ms for T 11..31, "no search reached its
  hard limit" is false at T=20, and W1's soft floor does nothing there. My TIME_MODEL.md line 39 was wrong.
- B. AGREE that 720 was a miscount. My raw files hold 7x300 (uho300) + 7x20 (worst20) records; the six
  clocked runs per file (3 clocks x 2 thread counts) give 1,800 + 120 = 1,920 — Fable's number. 720
  matches no subset of the raw records.
- C. No. I had not opened REPORT_r3_15.md, REPORT_r3_16.md, tests_r3fu_15/ or tests_r3fu_16/ before the
  job 2 prediction was pushed (learned of them from the job 3 file).

## times: stamps.txt
## Model
kimi5 — Kimi K3 (the model serving this cloud-agent run).
