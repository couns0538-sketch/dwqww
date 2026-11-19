# H51 targeted emergency-root caller validation

Completed 2026-11-19T01:55:08.258426+00:00

Four cases: cold and same-position depth4-primed TT, each White and Black to move. PC20 fixed net768/T1/Hash16, actual UCI option `setoption name Move Overhead value 100`, command `go wtime 1 btime 1`. Fresh process per case; no ucinewgame or TT clear between priming and emergency search.

All four emergency searches match unchanged r15d, unchanged kF, count22 and wrong22 in every emitted last-info field except time/nps and in legal bestmove. This is an empty-reserve test, not late elapsed-clock expiration. Priming searches logged separately and excluded from targeted aggregate.

Count22 H51:4uses/0differences. Wrong22:4uses/2differences, exactly White. Classes:White2/Black2, hit2/miss2, selected2/no_selection2,reserve_empty4/hard_expired0. No core untimed reach was claimed.

Shared scalar TT snapshot, hash/index, Move equality and root candidate list remain limitations. Singlethread snapshot/probe gap is not concurrency proof; no full TT lifecycle or arbitrary timing coverage claimed. A first Python launch failed importing python-chess before engine execution; existing /tmp/forge-dot-python package used on successful retry.

Evidence: four H51_*.classes.txt aggregate files, raw transcripts with matching H51_manifest.txt, local row and priming records.

Separate post-run QA confirmed both priming depth4 searches also match all4 engines canonically except time/nps.
