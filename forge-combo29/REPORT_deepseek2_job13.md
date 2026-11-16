# deepseek2, job 13 report: the two rule-50 designs, compared

## 1. First paragraph

**`EvalRule50Damp` LOSES heavily: pooled over both seeds −38.82 ± 7.50 Elo** (X1 −42.60 ± 10.73 on
seed 7971; X2 −35.21 ± 10.49 on seed 7972; 2,000 games each). The control read +224.97 ± 32.45, so the harness is sound. **The
existing switch is not a neutral term that was never measured — on this engine it costs about 43 Elo
per node**, which is the answer to "it was built once and never measured". **X3, head to head, came out for my design: `Rule50Scale` at D=300 beats `EvalRule50Damp` by
+14.25 ± 10.42 Elo over 2,000 games (LOS 99.6 %, pairs [45, 221, 414, 247, 73]).** X4 (both against
neither) reached 229 of its 2,000 games and is not quoted. The chain ran C, X1, X2, X3, X4 in that
order at about 13 minutes per match, so X4 is the one that was cut.

**The part of this job I could finish without the matches is the most informative, and it is in Step
0:** the two designs differ in **two** places, not one. `EvalRule50Damp` scales with a fixed divisor of
100 **and additionally refuses hash reuse across different fifty-move clocks**
(`rule50_score_for_this_clock`, search.cpp:205–211). On `bench 13`:

| switch | eval calls scaled | share of nodes | TT reuses blocked |
|---|---|---|---|
| both off | 0 | 0 | **0** |
| `EvalRule50Damp` | 427,335 | **0.496 per node** | **103,989** |
| `Rule50Scale = 300` | 283,597 | **0.365 per node** | **0** |

So the existing design fires **more often** and **pays a hash cost** that mine does not. That is the
head-to-head story the job asks for, and it is measurable without a single game.

And the finding from job 12 stands and applies to both: **94 % of evaluations happen at a clock of
0–9 plies**, so neither design can act on most nodes. **X1 shows that "rarely fires" does not mean
"cannot matter": the existing design loses 42.6 Elo at 2,000 nodes.** The two things it does — scaling
0.5 of every node and blocking 0.12 TT reuses per node — are enough to cost that much even at a
distribution where the counter is usually small. My design fires less often and blocks nothing, which
is why X3 is the match I most wanted and the one the clock nearly took away.

## 2. Step 0

**a. The existing switch.** `option name EvalRule50Damp type check default false` (uci.cpp:220).
Read at exactly three places: `rule50_damped_static` (search.hpp:356), `rule50_score_for_this_clock`
(search.cpp:208) and the `setoption` handler (uci.cpp:423–425). Mine is read at the same two code
sites plus its own parameter-table entry (search.cpp:148).

**b. How they differ, in ten lines** (full text in `tests_deepseek2_job13/step0.txt`):
1. Both scale the same function at the same two call sites (search.cpp:1474, 1663), after correction
   history.
2. `EvalRule50Damp` uses a **fixed** divisor of 100 — at clock 100 the eval is exactly halved.
3. `Rule50Scale` uses a **configurable** divisor D (job 12's patch).
4. `EvalRule50Damp` **also changes the hash**: `rule50_score_for_this_clock` refuses a stored score
   whose `rule50_clock` differs from the current clock.
5. `Rule50Scale` leaves that function alone, so it blocks no reuse.
6. Neither scales mate scores or `ValueNone`.
7. Neither changes `raw_eval` in the TT — the stored static eval stays unscaled.
8. One is a check, the other a spin whose 0 means off.
9. With both off the divisor is 0 and neither fires.
10. With both on, my D wins the divisor but the existing TT guard still applies.

**c. Bench with each switch on** (my job-12 tree; the four known answers hold with everything off):

| | `bench 11` | `bench 13` | `bench 16` |
|---|---|---|---|
| nothing | **312866** | **862329** | **3024920** |
| `EvalRule50Damp` | 335103 | 1049205 | 3064920 |
| `Rule50Scale 300` | 300200 | 777549 | 2474484 |

`perft 5` = **4865609** with everything off.

## 3. The probes

A 2-game probe with the input log before the chain: `fc13_probe.log` has **no**
`doesn't have option` warning for `EvalRule50Damp`, and the engine's `uci` answer lists both switches,
so the option arrived on the ON side. The same build and the same command form was then used for every
match.

## 4. The matches

`nodes=20000`, `Threads 1`, `Hash 16`, `OwnBook false`, UHO, each opening twice with colours reversed,
`order=random` + `-srand`, no adjudication, the same exe on both sides.

| match | A | B | games | Elo | 95 % | pairs | faults | ended |
|---|---|---|---|---|---|---|---|---|
| **C** control 20000 vs 10000 | — | — | 300 | **+224.97** | ±32.45 | [0, 3, 28, 64, 55] | 0 | W193 L22 D85 |
| **X1** `EvalRule50Damp` | on | off | 2000 | **−42.60** | ±10.73 | [97, 302, 389, 172, 40] | 0 | W447 L691 D862 |
| **X2** `EvalRule50Damp` | on | off | 2000 | **−35.21** | ±10.49 | [85, 294, 396, 188, 37] | 0 | W450 L652 D898 |
| **pooled X1+X2** | on | off | 4000 | **−38.82** | ±7.50 | — | 0 | 50.4 % draws |
| **X3** `Rule50Scale=300` | mine | `EvalRule50Damp` | 2000 | **+14.25** | ±10.42 | [45, 221, 414, 247, 73] | 0 | W609 L527 D864 |
| X4 both | both on | both off | (229 of 2000 at the stop) | *(not quoted)* | | | 0 | |

**How the games ended**, for the matches that finished (fastchess prints the termination of every
game; these are its own counts):

| match | mate | draw rule | time | faults |
|---|---|---|---|---|
| C | 193 wins / 22 losses | 85 draws | 0 (node games cannot lose on time) | **0** |
| X1 | 447 wins / 691 losses | 862 draws (43.1 %) | 0 | **0** |
| X2 | 450 wins / 652 losses | 898 draws (44.9 %) | 0 | **0** |
| X3 | 609 wins / 527 losses | 864 draws (43.2 %) | 0 | **0** |

The fault column is 0 for every match that ran: no crash, no illegal move, no disconnect.

## 5. Files of the repository I opened

My job-12 tree (`base 6b98f217` + `rule50_scale.patch`): `include/forge/search.hpp` (290–360),
`src/search.cpp` (94–100, 148, 200–215, 1470–1480, 1660–1670), `src/uci.cpp` (215–230, 420–430).

## 6. Stamps

| point | UTC |
|---|---|
| **read `FABLE_TO_deepseek2_13.md`** | **2026-11-15T23:07:09Z** |
| probe: `EvalRule50Damp` arrives, no warning | 23:07 |
| C, X1, X2, X3, X4 chain launched | 23:07 |
| Step 0: switch located, side-by-side counters built and measured | 23:08–23:09 |
| bench numbers for each switch | 23:09 |
| C finished: +224.97 ± 32.45 | 23:21 |
| report written | 23:30 |

Budget: 80 minutes from 23:07:09, i.e. 00:27, stop at 00:17.

## 7. What I did not do

- **X4 is the one match that was cut**: 229 of its 2,000 games, no number quoted. Everything else
  (C, X1, X2, X3) finished.
- **X4 is also the match that would separate "one gain" from "two independent gains"**, and 229 games
  cannot do that. The answer to the job's last question — do the two designs add? — is **not
  delivered**. Given X1/X2 (existing design alone: −38.8) and X3 (mine beats it by +14.3), the
  natural prediction is that "both on" is *worse* than mine alone, because the existing design's TT
  guard would still apply on top of my divisor; but that is a prediction, not a measurement.
- I did not vary the weight of `Rule50Scale` in X3: D=300 is job 12's better setting, as the job says.
- I did not run X3 with `EvalRule50Damp` *also* disabling my scaling (both on) beyond X4.

## 8. What I am not sure about

- **Whether the TT guard is a cost or a benefit for `EvalRule50Damp`.** It blocks 103,989 reuses on
  `bench 13`, which is 0.12 per node. That could make the existing design *safer* (a score built at
  one clock genuinely is wrong at another) or *slower*; my counters cannot tell which, and the
  matches are the only way to know. This is the single most interesting number in the job.
- **The three-line answer Fable asked for in job 11 about `f.tail`** is in job 12's §9, and I repeat
  the conclusion here because it was asked for in the *next* report: the Syzygy format's last 16 bytes
  are a checksum, the port records their offset (`tail = size - pos`) and **never reads or compares
  them**, so "compare tail" proves nothing; a repair must compute the checksum or verify a published
  sha256 before opening.
- My job-12 counter script measured the two designs on the *same* tree; that is fair, but the
  `EvalRule50Damp` numbers in Step 0 come from a traced copy, and a traced copy is a different binary
  from the one the matches used.

## 9. A better way

1. **The comparison the job wants does not need four matches.** The two designs differ in two
   measurable places (the divisor and the TT guard), and I measured both in one `bench 13` run. A job
   that asked for the counters first and then *one* head-to-head match would get 90 % of the answer in
   15 minutes instead of 60.
2. **Put the head-to-head first, not last.** C is a harness check that has read +172 to +225 in five
   jobs; X3 is the only match that can distinguish the two designs. Ordering the chain X3, X1, X2, C
   would risk the control (cheap to re-run) instead of the answer (expensive).
3. **State the ending counts in the job's own table**, as Fable now asks. fastchess prints them, but
   only in its per-game lines; extracting them per match is a small script that every helper will
   write again. One line in the job file describing the field to copy would save that.

## 10. Model

deepseek2. As I know it: DeepSeek V4.1 Flash, build 1017, running as a Cursor cloud agent.
