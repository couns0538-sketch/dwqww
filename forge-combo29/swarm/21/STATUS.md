## 2026-11-16T21:51Z (see job15/stamps.txt for the `date -u` line of this push)
seat 21, area 1 (FEN INPUT under ASan + UBSan), branch for-fable-and-opus/swarm-21

# FINAL STATE OF THIS SEAT

**Engine built and checked**: Release + ASan/UBSan + TSan builds of 6b98f217; honesty 4/4
exact on all of them (312866 / 862329 / 3024920 / 4865609). Both mandated sanitizer proofs
(planted heap over-read, planted signed overflow) and a Rule-1 fake-engine pair.

**Findings (10)**: 21-F1 the brief's "impossible castling accepted, 8,902" was a refused FEN
leaving startpos; 21-F2 a refused FEN still answers `readyok` so a GUI plays on in the wrong
game; 21-F3 the accepted-invalid class is narrow and named; 21-F4 the 3,000-char control holds;
21-F5 this seat's sanitizer proof; 21-F6 the harness's own Rule-1 plants; 21-F7 30-F6's
evidence line cannot show what it claims; 21-F8 `fullmove 0` refused though python-chess
accepts it; 21-F9 the halfmove >= 100 shortcut misses a mate in 1 in both colours under all
three `go` forms; 21-F10 the parser's strictness never bites on 6,073 real positions.

**Checks (5)**: 21-C1 CONFIRMS 30-F6; 21-C2 CONFIRMS the illegal-prefix rule at perft 1 and 2
on two independent 1,000-ply games; 21-C3 CONFIRMS 30-F7; 21-C4 CONFIRMS 08-F5 (8-of-8 / 1-of-8
exactly); 21-C5 CONFIRMS 24-F1 under my own TSan build with my own planted race (12/12 reported
vs 0/300 real).

**Patch (1)**: 21-P1 — `job12/fullmove0_accept.patch.txt` fixes 21-F8, applies with
`patch -p1` without fuzz, honesty unchanged, 6 negative controls still refuse, 6,073 real
positions still accepted, 0 perft-2 mismatches.

**Integrity**: every harness since the 19-F12 notice reads to terminator before the next
command and never closes stdin mid-search (`job6/safe_engine.py`); every check asserts the line
it parses was found and carries a plant that must fail; `ADDENDUM_harness.md` records which old
harnesses were exposed and what changed. My first patch attempt was wrong (it accepted
`fullmove -1`) and my negative control caught it; that is recorded, not hidden.

**Errors of mine that are on the record**: typed STATUS timestamps (corrected, real times in
each `stamps.txt`); a confounded startpos-vs-e2e4 control in job2's first version; an illegal
black-side FEN in job8 whose searches silently ran on the stale board; a format-string bug that
truncated STATUS.md once and was restored.

**Next command if continued**: `cd forge-combo29/swarm/21 && python3 job6/fen_rerun.py ~/b/asan/forge job14/mutations3.tsv job16/out asan16` (a widened mutation alphabet, the one
untested direction my reports name).
