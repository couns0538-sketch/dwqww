# deepseek6 long 65 — PREDICTION (written before the first PV-collecting run)

Item (file 16, long 65): **PV LEGALITY.** Every search of a rows run on O and G at depth 12, S14: keep the LAST
`info ... pv` line. python-chess plays the whole PV from the position: every move legal? If the score is `mate N`,
does the PV end in checkmate after exactly 2N-1 plies (N>0) or 2|N| plies (N<0)? If the PV ends in checkmate, is
the score a mate score? Table: set | searches | PVs fully legal | first illegal ply | mate scores | mate scores
whose PV ends in mate at the stated length. Planted control: one PV with its last move replaced by an illegal one
must be caught.

Model: DeepSeek V4.1 Flash 1017, chat 1794862262. Time: `stamps.txt`, first line is the claim.

## Fixed now

- Build: plain 6b98f217 release, `/tmp/ds6/build-release/forge`, sha256 `7c4e1aee…33622`; the four pins are
  re-run before the first counted search.
- **553 searches**: all 200 of O and all 353 of G, depth 12, S14, Threads 1, Hash 16, OwnBook false, fresh process
  per position (the same `rows.py` path that produced every other rows file of mine), **plus** one extra pass that
  keeps the last `info ... pv` line per search. I will write a `pvrows.py` that records `index|nodes|bestmove|score|
  pv` so the PV itself is committed, not just a verdict.
- **The mate arithmetic, stated precisely so it cannot drift:** for a score `mate N` with N > 0 the PV must end in
  checkmate after **2N-1** plies; for N < 0 after **2|N|** plies; `mate 0` should not occur (if it does, it is a
  finding). A PV that ends in checkmate while the score is a plain centipawn score is also a finding.
- **The planted control**: one PV from the real run with its last move replaced by an illegal one, fed to the same
  checker, which must report exactly that PV as illegal at that ply.

## Predictions, each with the range that kills it

**P1 — every PV is fully legal: 553 of 553.** Kill range: any PV with an illegal ply — headline, with the position
and the ply named.

**P2 — there are mate scores, and they are rare: between 1 and 40 of 553.** Kill range: zero mate scores (then the
mate half of the item has nothing to say and I say that), or more than 100 (which would mean the score reporting
is inverted somewhere).

**P3 — every mate score's PV ends in checkmate at exactly the stated length.** Kill range: any mismatch — that is a
real defect and the position and both lengths get committed.

**P4 — no PV ends in checkmate with a non-mate score.** Kill range: any such PV.

**P5 — the PV lengths are reasonable: at least 90 % of PVs have at least 4 plies and no PV is longer than 64
plies.** A one-move PV at depth 12 would suggest the PV is being truncated; a 64+ ply PV would suggest a loop.
Kill range: more than 10 % of PVs under 4 plies, or any PV over 64.

**P6 — budget.** Two collection runs (O and G) at depth 12: about 6–10 minutes. Kill range: over 25 minutes I
report the set done and name the other as not done.

## What would make me report "not done"
A build that fails a pin, a run I cannot finish, or a PV line I cannot parse (then the count of unparsed lines is
reported beside the table and no global "all legal" is claimed).
