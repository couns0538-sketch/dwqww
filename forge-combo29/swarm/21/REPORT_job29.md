# REPORT job29 — 21-F9 WITHDRAWN under handoff file 6's rule

**What was asked.** Handoff file 6 gives the standard for judging a `cp 0` at a high halfmove
counter: it is a defect **only** when a forced mate exists that ends no later than the 100th
half-move, i.e. when `2N - 1 <= 100 - counter`, where N comes from the same board at counter 0 and
`go depth 20`+. Both numbers must be in the finding line.

**The answer.** Under that rule **my 21-F9 is not a defect and I withdraw it.** At counter 100 with
a mate in 1 the mate would land at half-move 101, past the 100 limit, so `cp 0` is correct. And in
the window where the rule *does* bite — counters 98 and 99 with a mate in 1, where `2N-1 = 1 <=
100-counter` — the **base build already finds the mate** (`mate 1` at both depth 6 and depth 20).
So there is no case in this family where the base engine both should find a mate and does not.

**How sure.** High. Both builds, both depths, the inequality printed per case, and the raw output
committed per case.

## Table (pasted from `job29/out/summary.md`)

| build | board | counter | N (counter 0, d20) | 2N−1 | 100−counter | defect? | real score d20 | real score d6 |
|---|---|---|---|---|---|---|---|---|
| base | mate1 | 99 | 1 | 1 | 1 | YES | `mate 1` | `mate 1` |
| base | mate1 | 98 | 1 | 1 | 2 | YES | `mate 1` | `mate 1` |
| base | mate1 | 100 | 1 | 1 | 0 | no | `cp 0` | `cp 0` |
| base | mate3 | 95 | *no mate* (`cp 271`) | – | – | cannot judge | – | – |
| base | mate3 | 96 | *no mate* (`cp 271`) | – | – | cannot judge | – | – |
| pc | mate1 | 99 | 1 | 1 | 1 | YES | `mate 1` | `mate 1` |
| pc | mate1 | 98 | 1 | 1 | 2 | YES | `mate 1` | `mate 1` |
| pc | mate1 | 100 | 1 | 1 | 0 | no | `mate 1` | `mate 1` |
| pc | mate3 | 95 | *no mate* (`cp 271`) | – | – | cannot judge | – | – |
| pc | mate3 | 96 | *no mate* (`cp 271`) | – | – | cannot judge | – | – |

Cases where file 6's rule says a DEFECT and the engine still answers `cp 0`: **none**.

## What this corrects

- **21-F9 is WITHDRAWN.** Its headline case was counter 100 with a mate in 1, which file 6's
  inequality shows is correct behaviour (`1 > 0`). The genuine window (counters 98–99 here) was
  already handled correctly by the base build. My error was judging the engine against "a mate
  exists on the board" instead of "a mate exists that can still be delivered before the match
  program ends the game".
- **21-F13 is withdrawn with it.** It described the PC build's node counts varying with the counter
  (293 at 100, 155 at 150+). That is not a defect under file 6 either — no mate can land by
  half-move 100 from those counters — and it was a shape observation, not a fault.
- **21-F9b** (which said F9 was "repaired on the PC build") becomes moot: there was no defect to
  repair. The PC build does find the mate at counter 100, which is *better than required*, not a fix
  of a bug.
- **21-C6** (my third verification of seat 12's two-door patch) is unaffected as a measurement, but
  its significance changes: file 6 says seat 12's claimable-draw patch is **not to be pursued**, and
  my A/B confirms what that patch does — it makes the mate at counter 100 found, which is a
  behaviour change beyond what the rules require. I record that; I do not recommend the patch.
- **21-C10** (CONFIRMS 15-F5's ladder walk) stands: the walk is ~3 ms of extra `info depth` lines, a
  real quirk, and it does not depend on the draw question.

## The mate-3 board was unusable

My "mate in 3" board (`6k1/5qpp/.../3R2K1`) is not a mate in 3 at all — at counter 0 it scores
`cp 271` with no mate. So the mate-3 rows test nothing about the inequality. I report them as
"cannot judge" rather than dropping them, because the table is the script's output.

## Suspicions, not proven

- Whether some counter/mate combination *does* trigger a missed mate in the base tree. My one
  mate-in-1 board covers counters 98–100 and is handled. A broader sweep (many mate distances ×
  counters near the limit) is the honest way to look for it, and I did not run one here.

## What I did NOT do

- Did not sweep mate distances 1..10 against counters such that `2N-1 <= 100-counter`. That is the
  right next job under file 6 and I am starting it.
- Did not finish job28 (KNN v K); it was killed mid-run and produced no output, so it is reported as
  "not done" rather than guessed at.

## Times

see `job29/stamps.txt`.
