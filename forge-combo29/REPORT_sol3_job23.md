# sol3 Job 23 — kF quiet-move and SEE assertions

## (1) Step 0 — both plain builds passed

Case A, Linux cloud. Plain r15d and kF each returned 312,866 and
862,329 nodes for default bench 11 and 13 and 4,865,609 for default
`go perft 5` from startpos. With PC20, synthetic net768, Threads 1
and Hash 16, both returned 882,074 and 4,275,906 for the same benches.
Each net bench printed `NNUE v3 active` with checksum
`30ab43b4ba5db5f3`. All ten commands ran in fresh processes.
[Plain outputs and hashes](sol3/job23/step0)

## (2) P — 2,000 positions

I deduplicated the 990 distinct W1 FENs and 464 distinct FENs from
both endpoints and every ply of the ten Job 22 AU games. The two AU
traces were byte-identical. This gave 1,444 distinct seed FENs.
I generated every legal one-ply child before discarding positions
where the side to move was in check. The union held 33,665 FENs,
with 31,401 out of check and 23,195 tagged.

| Class | All eligible | Selected P |
| --- | ---: | ---: |
| D · discovered check | 140 | 140 |
| Q · direct check | 12,827 | 1,203 |
| C · checking castle | 0 | 0 |
| P · legal quiet move along a pin | 855 | 855 |
| X · pseudo-legal quiet move by a pinned piece rejected as illegal | 1,512 | 1,025 |
| K · pseudo-legal quiet king move rejected as illegal | 16,310 | 1,025 |

P contains all 768 legal discovered-check moves from the source
pool, including 42 double-check moves at 32 FENs. Quiet means
noncapture and nonpromotion. D uses a stationary checking piece
after the move and Q uses the moved piece. C treats the castling
rook's relocation explicitly. Every qualifying row can have more
than one class.

I kept the ten highest-discovery starts, with FEN as the tie-breaker,
then filled from the least represented available class. This kept
every D and P candidate and gave equal X and K counts. A recount showed that selecting
more overlapping cases could raise both from 1,025 to 1,050
while retaining every D and P. I ran the original published P.
A second classifier reconstructed all labels, checking pieces and starting
ranks. The committed P TSV SHA-256 is
`e7100aae3c0a8ac1a9966fb8d746ec9511bbd63513ef4ecea99bd38b6255dfae`.
[P](sol3/job23/step1/positions.tsv) · [Source and selection receipt](sol3/job23/step1/receipt.json) · [Independent classification](sol3/job23/step1/audit.json) · [Balance readback](sol3/job23/step1/balance_readback.json) · [R2 starts](sol3/job23/step1/top10.tsv)

## (3) A-kF, known answer and A-wrong

Both scratch builds use the Job 22 AU recipe. GCC 14.2.0
(Debian 14.2.0-19), CMake 4.2.3, `-march=x86-64-v4`, assertions
enabled, and `-O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined
-fno-sanitize-recover=undefined`. The two unified diffs applied
with zero fuzz.

- **A1** compares each returned QuietMoves move's cached check flag
  with `Board::gives_check` after legality. **A2** checks the same
  stage's legality decision before either acceptance or rejection
  and compares it to `Board::is_legal`. Both use the requested Board
  APIs. For ordinary quiets these share the live king-line data from
  which the picker made its copy.
- **A3** compares each explicit early return of kF's `Board::see_ge`
  with the pinned r15d implementation copied verbatim after the
  method name change. Seven sites are compiled under this build's
  SEE configuration. The alternate pawn shortcut is guarded by
  the disabled branch of the compile-time hoist option. A3 covers
  both new live early exits, the empty contact/ray and empty live
  attacker cases.
- The native debug checks for a supplied key or known-no-check
  verdict in `make_move` also stay enabled.

[A-kF patch](sol3/job23/step2/A-kF.patch.txt) · [A-wrong patch](sol3/job23/step2/A-wrong.patch.txt) · [Line and coverage map](sol3/job23/step2/source_sites.txt) · [Build receipts](sol3/job23/step2/build)

A-kF matched all 200 W1 depth-9 FEN, last-info node and bestmove
labels from Job 22 AU-kF-d9. The fresh engine process used PC20
and net768 with Threads 1, Hash 16 and a reset and ready barrier
before each row. It returned all 200 bestmoves at 4,097,080 nodes,
exited 0 and wrote zero stderr bytes.
[Known run](sol3/job23/step2/known) · [Gate readback](sol3/job23/step2/gate.json)

A-wrong changed only the A1 reference to the direct-check
predicate. It stopped at A1 on its first search of P row 1
(class DQ), before bestmove, with child exit `-6` (SIGABRT) and
zero sanitizer reports. Python-chess confirmed that the move was
legal and only the stationary queen on e1 gave check. Its entire
stderr was these two lines.

```text
job23 assert A1 move e4c2 fast 1 ref 0
job23 fen 4K3/8/8/8/4b3/8/8/k3q3 b - - 19 114
```

[Control command and diagnostics](sol3/job23/step2/control)

## (4) Prediction graded

Both R1 and R2 observed zero assert stops and zero ASan or UBSan
report blocks. All four forecast cells matched their observed counts.

[Published forecast](sol3/job23/prediction.md)

## (5) Step 3 — A-kF

Both runs used PC20, net768 (active checksum
`30ab43b4ba5db5f3`), Threads 1 and Hash 16. R1 reset and waited
for `readyok` before each depth-9 root. R2 reset at each start
and used Job 20 game rules and `go softnodes 2000`.

| Run | Fixture and limit | Searches / bestmoves | Reported nodes | Engine exits | Assert stops | Checker reports |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| [R1](sol3/job23/step3/r1) | 2,000 P positions, depth 9 | 2,000 / 2,000 | 35,709,215 | 0 | 0 | 0 |
| [R2](sol3/job23/step3/r2) | 10/10 games completed, softnodes 2000 | 84 / 84 | 295,448 | 0 | 0 | 0 |

R1 totals the last `info depth` node labels. R2 totals the final
consumed-node markers. A search without a bestmove contributes
no completed-search node label to these sums. The exit column
lists each actual child process in time order.
[Independent UCI readback](sol3/job23/step3/transcript.audit.json)

Both Step 3 engine stderr streams had zero bytes. The deliberate control above was the only stop.

## Facts

The independent P audit establishes which legal or rejected moves
exist at the selected roots. The UCI audit replays the exact root
schedule and checks the legality of every completed game ply.
The ten R2 starts yielded the following termination counts.

| Termination | Games |
| --- | ---: |
| `CHECKMATE` | 8 |
| `INSUFFICIENT_MATERIAL` | 1 |
| `THREEFOLD_REPETITION` | 1 |

[Raw label rows and stream receipts](sol3/job23/step3) · [Game move lists](sol3/job23/step3/r2/games.tsv)

## Suspicions

A fault in the king-line cache builder could produce the same
wrong answer in the picker and the Board API. The two checks
exercise the copy and its use. The independent fixture labels
give chess-rule witnesses, and the runner does not bridge those
witnesses to per-node assertions.

## What I did not do

I did not modify tracked engine source or add counters to the
assert build. Full process streams are in scratch. The retained
artifacts include stream SHA-256, exact size and report-header
counts, and the bounded report excerpts.

## What I am not sure about

The searches give no dynamic counts for individual SEE exits or
for each kind of quiet move at the assertion sites. P contains
zero checking castles, and I did not measure whether any search
descendant exercised one.

## What this check cannot see

> Positions that P and the 10 games do not reach; the PC's clang 23 build with a profile and its trained net; more than one search thread.
