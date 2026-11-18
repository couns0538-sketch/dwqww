# sol3 Job 19 — Speed stack with a loaded net

## (1) Step 0 and Step 0b — known pins reproduced

Linux cloud, Case A. The retained r15d and kF binaries and the
synthetic net matched their pinned SHA-256 values. Every pin had
its own engine process. The default runs used the embedded evaluation
with no options sent. The net768 pins used PC20, one thread,
Hash 16, and the standalone synthetic net.

| Build | Default bench 11 nodes | Default bench 13 nodes | Startpos perft 5 nodes | PC20 + net768 bench 11 nodes | PC20 + net768 bench 13 nodes |
| --- | ---: | ---: | ---: | ---: | ---: |
| r15d | 312,866 | 862,329 | 4,865,609 | 882,074 | 4,275,906 |
| kF | 312,866 | 862,329 | 4,865,609 | 882,074 | 4,275,906 |
| kF0 | — | — | — | 882,074 | 4,275,906 |

- r15d SHA-256 `bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6`.
- kF SHA-256 `340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea`.
- kF0 SHA-256 `ff0c49dcafb26968619982a056a76e89bf76f0f62ba7bb631d9a10bc8fdbccae`.
- net768 SHA-256 `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`.
  Every net-loaded pin printed `info string NNUE v3 active:` and
  `checksum 30ab43b4ba5db5f3`, plus `kernel avx512`.

The kF compile line and preprocessor say `FORGE_SPD_NNUE_ZMM=1`.
On the identical kF sources, I changed only that effective define to
0 for kF0. CMake still supplies its earlier target definition of 1,
and GCC uses the final compile argument 0. Both used CMake 4.2.3
Release, GCC 14.2.0, `-march=x86-64-v4`, libstdc++ 14.2.0-19 and
glibc 2.41-12+deb13u4. [Step 0](sol3/job19/stage0) · [Step 0b](sol3/job19/stage0b) · [Exact kF compile line](sol3/job19/stage0/kF_nnue_compile_line.txt)

## (2) K — F1k fixture and move coverage

Python-chess 1.11.2 replayed the pinned F1k PGN from each game's
FEN tag. I sampled every fifth mainline ply, skipping terminal
positions with the default draw-claim policy. The first 1,000
samples came from 41 games. The extraction and expected SHA-256
both equal
`3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521`.
Both endpoint FENs matched.
[PGN pin](sol3/job19/F1k.provenance.txt) · [Extractor receipt](sol3/job19/K.txt) · [Positions](sol3/job19/positions.txt)

| At least one legal move of this kind | Observed positions | Expected |
| --- | ---: | ---: |
| King | 984 | 984 |
| Castling | 40 | 40 |
| En passant | 1 | 1 |
| Promotion | 25 | 25 |

802 roots offer a legal move that changes the moving side's king
bucket ID, 405 White-to-move and 397 Black-to-move. The fixture has
2,199 such legal moves. I read the pinned net header with the format
used by kF `src/nnue_v3.cpp:585–588,621–626` (king map bytes 48–111).
`include/forge/nnue_v3.hpp:176–181` indexes White's square directly and
Black's with `square ^ 56`, then computes a separate horizontal
mirror flag. The full `KingKey` equality at `75–78` includes both.
852 positions can change the full key, including 50 where only
the mirror component can change. `src/search.cpp:3897–3911` uses
full-key equality in the parent-valid dispatch. These counts are legal
root opportunities. [Per-root coverage](sol3/job19/coverage.tsv)

## (3) Prediction graded

The [prediction](sol3/job19/prediction.md) was committed alone at
`7bf1329` and pushed before the workloads. All seven predictions
were inside their stated mismatch ranges. W1, the cross-build
W2 comparison, both W3 comparisons, and the supplemental scalar
comparison had zero mismatches. The literal W2 final search differed
from all 20 fresh original-FEN searches per build and matched all 20
fresh startpos controls per build.
[Checkpoint order](sol3/job19/stamps.txt)

## (4) Workload comparisons

All runs began with PC20, Threads 1, Hash 16 and the pinned
net768. W2 then deliberately changed the evaluation and Hash as
specified. Each W1 and W3 search row compares last-info nodes and
bestmove. W2 strips only numeric time, nps and hashfull from info
lines, retaining all stable fields, PV, net diagnostics and bestmove.
The table counts aligned comparisons.

| Workload | Rows or lines compared | Equal | Differ | First difference |
| --- | ---: | ---: | ---: | --- |
| [W1 r15d vs kF, depth 9](sol3/job19/W1/comparison.json) | 1,000 rows | 1,000 | 0 | — |
| [W2 r15d vs kF, 20 × 6 depth-10 searches](sol3/job19/W2/comparison.json) | 1,380 workload lines | 1,380 | 0 | — |
| [W2 r15d vs kF including startup](sol3/job19/W2/comparison.json) | 1,480 stdout lines | 1,480 | 0 | — |
| [W2 literal final vs fresh original FEN, each build](sol3/job19/W2/comparison.json) | 220 lines per build | 0 | 220 per build | Input 1, first depth-info line below |
| [W2 literal final vs fresh startpos, each build](sol3/job19/W2/comparison.json) | 220 lines per build | 220 per build | 0 | — |
| [W2 restored FEN vs fresh original FEN, each build](sol3/job19/W2/restored/comparison.json) | 220 lines per build | 220 per build | 0 | — |
| [W3 kF vs kF0, depth 9](sol3/job19/W3_depth/comparison.json) | 300 rows | 300 | 0 | — |
| [W3 kF vs kF0, eval](sol3/job19/W3_eval/comparison.json) | 1,000 eval lines | 1,000 | 0 | — |
| [W3 eval including startup and ready replies](sol3/job19/W3_eval/full_comparison.txt) | 3,100 stdout lines | 3,100 | 0 | — |
| [Supplemental kF AVX-512 vs kFscalar, depth 9](sol3/job19/scalar/comparison.json) | 300 rows | 300 | 0 | — |

### W2 board reset

Both warm runs captured the exact six-search sequence for all
20 inputs. A single process per build kept the loaded net and applied
the disable, re-enable, same-file reload and Hash changes in order.
There were no added `isready` barriers in that sequence. The
transcripts include an initial 768-hidden activation and matching
checksum, plus every subsequent load and enable diagnostic. Cross-build
identity includes all 120 last-depth labels and both empty stderr files.
[Protocol notes](sol3/job19/W2/protocol_notes.txt)

The final `ucinewgame` sets the board to startpos in both sources,
at r15d `src/uci.cpp:490–497` and kF `src/uci.cpp:574–581`.
Both literal warm arms diverged from their fresh original-FEN
control starting on input 1.

```text
input FEN r1bq1rk1/1p1nbppp/p3pn2/3pN3/2pP1B2/2P1P2P/PP1NBPP1/R2Q1RK1 b - - 0 11
actual warm final FEN rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
warm final    info depth 1 seldepth 1 score cp 319 nodes 27 pv g2g4
fresh input   info depth 1 seldepth 2 score cp 6 nodes 38 pv d8a5
```

For that input, the depth-10 warm final result was `b2b4 cp 184`
with 33,596 nodes and the fresh sampled-FEN result was `d8e8 cp -12`
with 14,301 nodes. All 20 literal finals had identical stable output
and labels to the fresh startpos process in each build. In a separate
warm replay I inserted only `position fen <original FEN>` after the
final `ucinewgame` for each input. That restored all 20 fresh-FEN
results per build, including all normalized info and bestmove lines.
[Literal warm commands](sol3/job19/W2/r15d/warm/engine.commands.txt) · [Fresh input 1](sol3/job19/W2/r15d/fresh/001/engine.stdout.txt) · [Restored runs](sol3/job19/W2/restored)

### What W3 exercised

The requested ZMM switch acts in the embedded float evaluator
at kF `src/nnue.cpp:325–377,451–472`. With net768 active,
`src/search.cpp:1755–1759` selects the standalone v3 evaluator.
`src/nnue_v3.cpp:14–26,551–553,773–780` selects that kernel
via compiler ISA macros. With both kF and kF0 built for
`x86-64-v4`, the active marker named `kernel avx512` in both.
Also, `src/uci.cpp:901–911` implements `eval` through the scalar
`evaluate_reference` path. W3 verifies loaded-path isolation from
the embedded switch and equality of reference eval output.

For a direct v3 kernel comparison I recompiled only kF's
`nnue_v3.cpp` in scratch with
`-mno-avx512f -mno-avx2 -fno-tree-vectorize` and relinked it with
all other original kF objects. The resulting kFscalar SHA-256 is
`c397e59ecd008a3cd13f1ef252ddf398909f425f0bfaa88981cfa40c4a84db2d`.
Its activation said `kernel scalar` and the same checksum.
Its PC20 + net768 benches matched at 882,074 and 4,275,906 nodes,
and its first 300 depth-9 rows matched kF's AVX-512 search.
[Scalar compile and link](sol3/job19/scalar/build_scalar.txt) · [Scalar pins](sol3/job19/scalar/pins.stdout.txt)

### Facts

- The independent readback reconstructed W1 and W3 rows from the
  raw commands and output. It found the same W1/W3 and scalar
  comparison results. Every net-enabled process logged the active
  marker and file checksum. The W2 `NNUEArch=false` searches
  deliberately used embedded evaluation inside the net-loaded
  sequence. [Readback outputs](sol3/job19/audit)
- The initial W1 preflight refused to launch because the runner's
  helper digest targeted an older copy. I checked that the full
  `EngineRun` transport and refusal predicate were byte-identical
  and pinned the shared copy shipped with this job. The failed
  preflight and subsequent measurement are both recorded.
  [Preflight receipt](sol3/job19/W1/preflight/receipt.txt)

### Suspicions

The observed W2 original-FEN difference is explained by the board
reset. Both the direct fresh startpos comparison and the restored-FEN
comparison isolate that cause. The equal cross-build traces support
equivalence for these reload and resize sequences. They cannot test
shared behavior that would require a different oracle.

### What I did not do

I measured deterministic outputs. Time, nps and hash occupancy remain
in the raw files and were excluded from the stable W2 comparisons.
All binary and net files stayed in scratch.

### What I am not sure about

The tested legal-move coverage does not measure how often each
incremental branch executed. Dot's raw results remain a separate
independent measurement to reconcile.

### Limits of this check

The PC's own net (a different file of the same kind), its compiler and processor; more than one search thread; inputs you did not think of.
