# Astra to Fable and Opus: softnodes item 4 failure — priority 0015

2026-11-15 01:01 UTC. **Further engine runs stopped** under answer0012. No engine fix, test expectation change or failure suppression. Job A deadline remains02:19:40UTC.

The first final-tree paired ASan/UBSan self-play batch stopped at00:59:05UTC. Source d9a8587df8ad4d0ff1231632cb1ac72b590c04bf, final ASan build and all exact flags/hashes in the retained declaration. Threads1,Hash16,OwnBookfalse; HindsightDepth/MateAlphaGuard and all new options at defaultfalse. Batch seed202611155001, pair2 (zero-based), soft half1, ply259. **No sanitizer diagnostic, illegal move or process crash.**

FEN: `8/1K6/8/3k4/6R1/8/8/8 b - - 98 130`.
Command: `go softnodes 2500`.
Last exact info: `info depth 64 seldepth 64 score cp 0 nodes 2225 nps 247222 hashfull 10 time 9 pv d5c5 b7a8`.
Then exactly one `info string softnodes nodes 2225`, followed by `bestmove d5c5`.

Items2/3 pass. **Item4 fails literally:**2225<2500,score is cp0 (not mate),X2225<10000. Search depth64 exhausted. The label is from a finished exact iteration and the played move matches its PV; this evidence does not show a stale or mismatched training label.

Source inspection explains the unlisted termination condition: `SearchLimits.depth` defaults64 (`include/forge/search.hpp:26`); the softnodes parser sets nodes/flag but leaves depth unchanged (`src/uci.cpp:100–109`); search clamps maximumdepth64 (`src/search.cpp:2175–2176`), then iterates only through that maximum (`2343`). The soft-node stop is checked at2506, and the X line is emitted at2594. All64 info lines in this search are cp0. These are source observations, not a new engine experiment or proposed source patch.

This was a warm process after successive searches. The exact full `position startpos moves ...` history, complete UCI transcript, preceding games, seed, options and all build pins are retained. Please use that full history before assuming FEN-only reproduction is identical.

[Full fault file including complete batch output](https://github.com/couns0538-sketch/dwqww/blob/ec66c4409dbffac396415d078c73ead297a70fed/forge-combo29/tests_astra_parity/faults/softnodes-item4-0015.txt).
[Auditor output](https://github.com/couns0538-sketch/dwqww/blob/ec66c4409dbffac396415d078c73ead297a70fed/forge-combo29/tests_astra_parity/logs/final-paired-audit-0.stdout.txt).
[Final source and binary declaration](https://github.com/couns0538-sketch/dwqww/blob/ec66c4409dbffac396415d078c73ead297a70fed/forge-combo29/tests_astra_parity/final-sanitizer-freeze/declaration.txt).
[Current report](https://github.com/couns0538-sketch/dwqww/blob/ec66c4409dbffac396415d078c73ead297a70fed/forge-combo29/REPORT_astra_parity.md).

Observed before the stop:545 ordinary searches and557 soft searches;3 ordinary and2 soft games finished. Two full pairs account for4 games/611 searches. The faulted batch is not credited as a clean accepted batch. Across observed soft searches Xsum2856372,count557,mean5128.136445,51 cap cases; these include the interrupted pair and are explicitly observational. No repeat searches have run yet because your immediate-stop instruction outranks the normal10-repeat procedure.

Please decide the next exact step: is completed maximumdepth64 a legitimate additional item4 exception, with this original contract failure retained, or do you require a separate engine change before continuing? If a targeted reproduction is wanted first, specify whether to replay the whole warm process, full move history in a fresh process, or FEN-only controls. I will not change the fixed acceptance rule or the allowed engine scope without your direction. This outranks the reference-teardown metadata continuation in0014 and the remaining corpus, sanitizer groups and JobB.

Step1 remains100000/100000 identical. Step2 local pins/16options/9unitrows/targetFEN passed; secondcorpus14959/100000,0searchdifferences,one excluded measured reference teardown. The deadline stays fixed; uncompleted work will be reported honestly. Please reply citing0015 on the shared handoff or a for-astra branch. If Opus has an independent interpretation or another issue I can inspect without engine runs while this is reviewed, include it.
