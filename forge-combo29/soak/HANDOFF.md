# Engine-work handoff

The actionable finding is a two-thread failure to report a mate score at depth 14 in positions where one-thread search reports mate. It occurs in both the unchanged lock (`16833ecc03b425586f91f4c8834dea8807bf4c22`) and integration (`bf5574ee654a773f0ef3d06878707056b90cdad7`). These observations do not establish a regression caused by the four integration fixes or a root cause.

Across 40 selected KRK roots and ten fresh-hash searches per root/build, the lock missed the mate score in **58/400** runs and integration in **53/400**. No mate-losing move was detected by the documented KRK checks. There are 27 affected root/build records, each containing all ten search transcripts and the observed frequency.

## Strong reproducer

FEN: `7k/8/3K4/8/8/8/8/5R2 w - - 0 1`

With Threads 1, depth 14, Hash 16 and OwnBook false, both builds reported `bestmove f1f7`, `score mate 7`, and 38,129 nodes during selection. With Threads 2, both builds missed the mate score in **10/10** trials. The returned moves were legal and did not lose the forced win under the KRK checks.

Use the normal UCI handshake, set these options, and wait for `readyok` after `isready`:

```text
setoption name Threads value 2
setoption name Hash value 16
setoption name OwnBook value false
ucinewgame
isready
position fen 7k/8/3K4/8/8/8/8/5R2 w - - 0 1
go depth 14
```

Wait for `bestmove` before starting another trial. Repeat from `ucinewgame` for fresh state. For the one-thread comparison, set Threads to 1 and use the same sequence. Leave other options at their defaults, including the compiled-in NNUE network.

- [Integration: ten full trials](faults/026.txt)
- [Lock: ten full trials](faults/027.txt)
- [One-thread selection evidence](batches/G-0070.txt)
- [All two-thread results](batches/G-0071.txt)
- [Fault-frequency audit and index](preparation/G-fault-audit.txt)

Investigate and implement any proposed engine fix on a separate branch. This soak branch preserves test programs and evidence; engine sources, headers and existing tests remain unchanged. The observed mate-score failure is a search-behavior finding. A data race has not been established by it.

## Other completed checks

The 129,793 one-thread depth-9 comparison positions had identical best move, score and reported node count between builds. The 4,200 official-fastchess games at 20,000 nodes per move had no crashes, illegal moves, disconnects or aborted games. Network consistency covered 1,228,600,000 position visits without a mismatch. See [SOAK_REPORT.md](SOAK_REPORT.md) for the final sanitizer coverage, all conditions, wall time and limitations, and [CHANGES.md](CHANGES.md) for the detailed branch changes. No Elo or speed conclusion is drawn.
