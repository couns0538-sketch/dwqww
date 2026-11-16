# PREDICTION — seat 07, area 7, job 1 (read src/search.cpp, 2753 lines, at 6b98f217)

Written before reading src/search.cpp beyond `wc -l` and before any measuring command of this job.
Falsifiers in brackets; a number outside its range kills that prediction and is reported as such.

1. Suspicious lines worth a FINDINGS line: 3 to 9. [0-2 or >=10 kills it]
2. Suspicious lines I can turn into a TEST with a demonstrable command (a position + UCI line, or a sanitizer
   report): 1 to 4. [0 or >=5 kills it]
3. Of those tested, at least one is in the time manager or in the `go`-parameter parsing path rather than in
   alpha-beta pruning proper. [none there kills it]
4. A TEXT PATCH (unified diff, `patch -p1`, no fuzz) is produced for at least one fault, and with the patch applied
   all four honesty numbers stay equal (312866 / 862329 / 3024920 / 4865609). [a changed number or a non-applying
   patch kills it]
5. The patch changes no node count on any of the three benches. [any delta kills it]

Predicted (guess, not a result): the NNUE accumulator update path is the likeliest place for an uninitialised read,
because refresh-vs-incremental has to agree exactly; the time manager is the likeliest place for an overflow when the
clock is tiny.

stamp of writing: see stamps.txt line 1 (date -u, written by the script that follows this commit).
