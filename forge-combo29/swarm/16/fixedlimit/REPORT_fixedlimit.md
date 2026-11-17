# REPORT_fixedlimit — S-F27 at a FIXED limit: my 3-of-10 was a CLOCK ARTEFACT of my own harness

**What was asked (seat 11, endorsed by the coordinator):** seat 11 ran my S-F27 start at the match clock, 20 plies,
10 games, and got **1 distinct move sequence of 10, byte-identical**. It asked me to repeat at a FIXED limit (no
clock) and report the distinct count, to settle whether my 3-of-10 was harness drift.

**The answer: at a fixed limit it is 1 of 10, at both a node budget and a fixed depth. My 3-of-10 was clock drift
in MY harness, exactly as my own S-F27 note suspected — and the headline number in S-F27 was therefore wrong.**

```
limit              games  distinct MOVE SEQUENCES  distinct FINAL positions
go nodes 20000        10              1                        1
go depth 10           10              1                        1
```

Seat 11's clock run gave 1 of 10; my fixed-limit run gives 1 of 10. **Both of us agree, and my earlier 3 of 10 is
the outlier — produced by the clock-driven arm of my ten-game study, where the clock was decremented by measured
wall time, so millisecond differences occasionally changed which depth the engine reached.**

So, precisely:
- **The engine is deterministic** at Threads 1 with fixed limits and an identical start. Ten games, one game.
- **Clock timing does not create variety** (seat 11) and neither does game length (seat 11's 20 plies gives 1).
- **My 3-of-10 was a property of my harness, not the engine.** My S-F27 note said exactly that about the *single
  diverging game* ("only because millisecond clock drift occasionally changes the depth reached") — I had the
  mechanism right and then reported the count as if it were an engine property. It was not.

**What survives of S-F27 and what does not:**

| claim in S-F27 | status |
|---|---|
| "ten self-play games from the same start produce only THREE distinct final positions" | **WRONG for a fixed limit — it is ONE.** Correct only for a clock-driven harness that reallocates a wall-time budget each move. |
| "seven of ten reach the identical position" | likewise an artefact of the same arm |
| "the engine is fully deterministic at Threads 1 with fixed limits" | **CONFIRMED**, and now measured directly at two fixed limits |
| "self-play from one fixed start re-collects the same game" | **CONFIRMED and strengthened**: at a fixed limit it is not "mostly", it is exactly one game |

And the actionable advice in S-F29 — **vary the openings** — is unaffected and if anything more strongly supported:
a fixed-limit self-play run from one start produces exactly **one** game, so variety must come from the start.

**P1 confirmed** (1 of 10 at the node limit). **P2 confirmed** (1 of 10 at the depth limit). **P3 confirmed** (my
S-F27 explanation was right, its number was not). **P4 not applicable** — with one sequence there is nothing to
compare against the three, and I am not going to claim a match without the clock arm re-run at the same plies.

**How sure:** high. 20 games, two fixed limits, PC20, Threads 1, Hash 16, one process per game, mirror of seat 11's
protocol except for the limit, and it agrees with seat 11's independent clock run.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge   PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dcded
        none 312866 / S14 242796 / PC20 278024   (all match file 5)
settings PC20 + Threads 1 + Hash 16; fixed limits `go nodes 20000` and `go depth 10`; no clock anywhere
protocol 10 games x 20 plies, one process per game, `ucinewgame` + `isready` + position resent before every move
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 10 games at `go nodes 20000` | done | `raw/fixedlimit.txt`, `run.log` | 1 distinct sequence, 1 final position |
| 10 games at `go depth 10` | done | same | 1 distinct sequence, 1 final position |
| agree with seat 11's clock run | done by comparison | seat 11's report + this run | both 1 of 10; my earlier 3 is the outlier |
| re-run my clock arm at 20 plies to reproduce the 3 | NOT done | — | would confirm the artefact directly; my 60-ply clock run is what produced 3 |

## Findings

`S-F38 | 6 | S-F27's "three distinct final positions out of ten" was a CLOCK ARTEFACT of my own harness, not an engine property: at a FIXED limit the same start gives ONE distinct move sequence in 10 of 10 games, at both `go nodes 20000` and `go depth 10` (PC20, Threads 1, Hash 16, one process per game, 20 plies) — agreeing with seat 11's independent clock run (1 of 10). The engine is deterministic at Threads 1 with fixed limits; the earlier 3 arose because my clock arm decremented the clock by measured wall time, so millisecond differences occasionally changed the depth reached. S-F29's "vary the openings" advice is unaffected and strengthened: one fixed start yields exactly one game | fixedlimit/raw/fixedlimit.txt fixedlimit/run.log (again: `python3 fixedlimit/fixedlimit.py ~/builds/bld-pc/forge /tmp/o`) | NEW |`

`S-F27 (CORRECTED) | the diversity count was wrong (3 of 10 should be 1 of 10 at a fixed limit); the determinism mechanism it described is right and is now measured directly | fixedlimit/raw/fixedlimit.txt | CORRECTED |`

## Suspicions, not proven

- That my clock arm would reproduce 3 of 10 if re-run at 20 plies. I did not re-run it; the mechanism (clock
  reallocation changing the depth reached) is what my S-F27 note already asserted and what seat 11's fixed clock
  behaviour is consistent with.

## What I did NOT do

- Did not re-run the clock arm at exactly 20 plies to reproduce the 3 directly.
- Did not test at other fixed budgets; two limits agreeing is enough to establish determinism.

## Times

`fixedlimit/stamps.txt`, every line a `date -u`.
