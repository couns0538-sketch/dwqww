# R3-2 ideas and sources

## Job (verbatim from the user)
"Interaction matrix: measure NPS and bench nodes for each feature ON alone and for pairs that touch the same code
(TT: LocklessTT/TtChildPrefetch; correction: CorrHistPlus/CorrMargins/CorrExt; NNUE:
O2/Threats/PawnPairs/OutputBuckets). Flag any pair that conflicts or cancels out."

## Ideas
- **One OFF reference for every cell.** Each configuration is timed against the all-OFF exe at the same Threads,
  in its own ABBA block, so slow load drift cancels inside the block and every Δ is on the same scale; the
  interaction of a pair is then `Δ(pair) − ΣΔ(parts)` on the log scale, with the parts' and the pair's
  standard errors added in quadrature (independent blocks).
- **Node-exact parts must stay node-exact together.** For a combination the expected bench nodes follow from
  its parts: all node-exact → the lock pins; one tree-changing part → that part's nodes; two or more → a new
  tree that must differ from OFF and from each part (equal to OFF or to one part = "cancels out").
- **Leave-one-out contribution.** For each part X of a combination C, `Δ(C) − Δ(C without X)` is what X adds on
  top of the rest; a part with a clear effect alone that adds nothing on top of the rest "cancels out".
- **Function-preserving NNUE nets.** Replica nets (`forge_nnue_v2.py from-inc --replica r1/rm8`, zero threat or
  pawn-pair blocks, identical output heads) evaluate exactly like the compiled-in net, so the tree is the lock's
  and the NPS difference is the machinery's cost. The plain r1 replica with `NNUEKingBuckets 1` isolates the cost
  of the v2 path itself; for combinations of several v2 parts that cost is counted once in the prediction.
- **CPU time of the measured command only.** `GetProcessTimes` before the command and after its last output
  line, so the net loading and start-up of file-loaded nets do not bias their NPS; `QueryProcessCycleTime` gives
  the same CPU time at TSC resolution (GetProcessTimes counts in 15.6 ms ticks).
- **Threads 2 needs `go`.** `bench` builds its own `Searcher bench_searcher(16)` (one worker, 16 MB) and ignores
  the Threads option, so the SMP options (LocklessTT, SmpExactNodes, SmpBestThread) are timed on the bench
  positions with `go depth` at Threads 2.
- **Extra pairs that share code** (beyond the three named groups), found in the merge commit messages:
  CuckooRep with CorrMargins/CorrExt (one alpha-beta instance per combination of the three), HistRework with
  CorrHistPlus (joint correction in `correction_plus.inc` and `evaluation.inc`), FORGE_SPEEDSTACK with
  MaterialKeyTable (the table is unconditional under the switch) and with TtChildPrefetch (two child prefetches
  each), IntendedThreefold with CuckooRep (both put a draw-score floor at repetition nodes), NetScale with a v2 net
  (NetScale scales only the compiled-in net).

## Sources
- `opus_round1/sol_S29/nps_ab.py` (ABBA, fresh processes, CPU-time NPS, Welch interval) and
  `opus_round1/sol_SIT/nps_ab_opts.py` (per-side UCI options): adapted into `r3_matrix.py`.
- `F:\opus_scratch\r3\tools\bench_opts.py` (bench with options), `F:\opus_scratch\r3\AGENT_COMMON.md` (stack
  facts, pins), the merge commit messages (`git log --merges --first-parent 467a59b3`).
- Reports with the ON pins and option semantics: `opus_round1/C2` (CorrHistPlus bits and pins), `O5`
  (CorrMargins), `O8` (CorrExt), `C6` (CuckooRep), `sol_A1` (HistRework), `C1` (Syzygy pins with the 3-4-5
  tables), `C3` (HardDeadline), `O1` / `O1-LTT` (SMP options, LocklessTT), `sol_S13`, `sol_S14`, `sol_S11`,
  `sol_S29`, `sol_S41`, `sol_SIT`, `O2`, `C4` / `C5` / `O6` / `O7` / `O4` (v2 nets, replicas, selection and
  fail-loud rules; `O4/standalone_copy.py` for the stand-alone r1 copy).
- Engine code read for the method: `src/uci.cpp` (bench handler, `control_priority`, v2 fail-loud lambdas),
  `src/search/searcher.inc` (helpers, exclusive TT lease, SmpExactNodes), `src/search/evaluation_v2.inc`
  (`nnue_v2_problem`), `src/nnue.cpp` (`select`, O2 regions), `src/search/alphabeta.inc` (correction size used by
  CorrMargins / CorrExt).
