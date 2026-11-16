# REPORT_job3 — AREA 8 (THE CLOCK), seat 28

## What was asked
AREA 8 job 3: `movestogo 1, 2, 40` with `wtime 1000`: how much of the time is used.

## The answer
With `wtime 1000` and no increment, the engine uses **32 % of the clock at `movestogo 1`** (median
323 ms), **23 % at `movestogo 2`** (235 ms) and **2 % at `movestogo 40`** (20 ms), and never overran
the 1000 ms clock in 200 searches. The ordering is right and the `movestogo > 50` clamp works exactly
(`movestogo 50` and `51` give the same plan, 19/76 ms, medians 16.3 vs 16.4 ms). But the amount used at
`movestogo 1` is far below what the code plans: the planned soft limit is 495 ms and the median spend is
323 ms — the engine stops at about **65 % of its own soft limit** on the very move where using the whole
clock matters most. The largest single search does reach the planned hard limit (792.7 ms).


## Process state for every search in this report (seat 10's rule)

Every search reported here ran in **one long-lived engine process per configuration**, with
`ucinewgame` + `isready` sent and read before EACH `go` — never `Clear Hash`, and not a fresh process per
search. Seat 10 reports that warm state changes results and that `ucinewgame` restores cold while
`Clear Hash` does not. I tested that directly on my own build (`job4/state_check.py`,
`job4/state_check_out.txt`): one process with `ucinewgame` gives **bit-identical** node counts and last
depths to a fresh process per search (112,623 nodes and depth 14 on all five searches in both regimes),
while a process with nothing between searches climbs 14,15,16,17,17. So the design of every harness in
this report is sound for the quantity reported, and `ucinewgame` — not `Clear Hash` — is what makes it so.

## How sure
High on the numbers: 40 searches per value, 200 in total, one process per value, every `.meta` written,
and the `movestogo 0`/`51` clamp check behaves exactly as the code predicts (a strong sign the harness
is measuring the right thing). High that the medians are far below the soft plan and consistent across
`mtg1` and `mtg2` (both ~65 %). Medium on WHY: I read the plan and the spend, not the stopping rule,
so the cause below is marked as a suspicion.

## Honesty numbers
Same exe as jobs 1-2, `~/build/base-release/forge`, sha256 `e06310ec…16a83`, all four honesty numbers
matched (`../HONESTY.txt`). Not a sanitizer job.

## Table — pasted output of `python3 mtg_table.py out` (`mtg_table_out.txt`)

| movestogo | planned soft ms | planned hard ms | n | median ms | p99 ms | largest ms | median fraction of the 1000 ms clock | over clock |
|---|---|---|---|---|---|---|---|---|
| 1 | 495 | 792 | 40 | 323.0 | 792.7 | 792.7 | 0.323 | 0 |
| 2 | 330 | 792 | 40 | 234.8 | 699.0 | 772.5 | 0.235 | 0 |
| 40 | 24 | 96 | 40 | 20.4 | 51.2 | 53.7 | 0.020 | 0 |
| 50 | 19 | 76 | 40 | 16.3 | 44.5 | 47.6 | 0.016 | 0 |
| 51 | 19 | 76 | 40 | 16.4 | 44.2 | 47.3 | 0.016 | 0 |

Planned soft/hard are computed in `mtg_table.py` from `include/forge/clock_plan.hpp:36-44` with
`available = 1000 - 10`, increment 0.

Distribution detail for the two values that matter (`awk` over `out/mtg1.tsv` / `out/mtg2.tsv`):

| value | min | q1 | median | q3 | max | searches > 700 ms |
|---|---|---|---|---|---|---|
| movestogo 1 | 0 | 275 | 323 | 463 | 793 | 3 |
| movestogo 2 | 0 | 183 | 242 | 345 | 773 | 1 |

## The step table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction alone, before measuring | done | `prediction.txt` (own commit) | 7/10 survived |
| movestogo 1, 2, 40 at wtime 1000 | done | `out/mtg{1,2,40}.tsv` | table above |
| how much of the time is used | done | `mtg_table_out.txt` | 32 % / 23 % / 2 % |
| clamp check at 50/51 | done (extra) | `out/mtg{50,51}.tsv` | identical plan, 16.3 vs 16.4 ms |
| Opus Rule 1 for this job's zeros | done (extra) | `../job2/plant_verdict_job1.py` output reused | the timing harness catches a planted overrun 8/8 and a planted non-answer 8/8 while the real engine shows 0/200 — same code path (`timing.Engine`) that this job uses |

## Findings

**S-F9 — at `movestogo 1` with a 1 s clock the engine uses only 32 % of the clock; it stops at about
65 % of its own planned soft limit (323 ms of 495 ms planned), while the single worst search does reach
the planned 792 ms hard limit.**
Shows again: `python3 movestogo.py ~/build/base-release/forge out && python3 mtg_table.py out`
(`mtg_table_out.txt`). The plan comes from `include/forge/clock_plan.hpp:36-42`; the spend is the wall
time. Same pattern at `movestogo 2` (235 of 330 planned).

**S-F10 — `movestogo` above 50 is clamped to 50 exactly**: `movestogo 50` and `movestogo 51` give the
same planned limits (19/76 ms) and medians 16.3 vs 16.4 ms, a 0.6 % difference. This matches
`const std::int64_t mtg = moves_to_go < 50 ? moves_to_go : 50;` and is a good control that the
harness measures the engine and not itself. Evidence: `out/mtg50.tsv`, `out/mtg51.tsv`,
`mtg_table_out.txt`.

**S-F11 — no movestogo case overran the clock** (0 of 200 searches above 1000 ms; worst 792.7 ms at
`movestogo 1`). The zero is backed by the planted-fault control in `job2/plant_verdict_job1_out.txt`.

## Suspicions, not proven
- Why the median lands at 65 % of soft: a likely cause is that the search stops only when an ITERATION
  completes within the soft budget, and at 1 s/movestogo 1 the iteration lengths (~300 ms here) are
  coarse relative to the 495 ms soft limit, so stopping after the iteration that fits usually
  undershoots. I did not read the stopping code path to confirm.
- Row 4 of every value (the position `r1bqk2r/p1ppp... b kq - 5 8`, answered `e1g1`) takes 0.0 ms in
  all five runs, which suggests a book or a hash answer rather than a search. Not verified, not claimed.

## What I did NOT do
- Did not test movestogo with an increment (job 2 covered increments separately).
- Did not read or modify the stopping rule; no patch is offered.
- Not under a sanitizer.

## What I am NOT sure about
- Whether using only 32 % of the clock at movestogo 1 is a defect or a deliberate conservative choice.
  S-F9 states the measured fraction and the plan it is compared against; the judgement is the owner's.
- Whether the GUI subtracts its own overhead again on top of the engine's 10 ms, which would change the
  fraction slightly in real play.

## Prediction score (pasted, `prediction_check_job3_out.txt`)

| id | measurement | predicted | measured | kill range | verdict |
|---|---|---|---|---|---|
| P1 | movestogo 1 median | 600 ms | 323.0 ms | 400..820 | **KILLED** |
| P2 | movestogo 1 largest | 800 ms | 792.7 ms | 600..1000 | SURVIVES |
| P3 | movestogo 2 median | 380 ms | 234.8 ms | 250..820 | **KILLED** |
| P4 | movestogo 2 largest | 800 ms | 772.5 ms | 500..1000 | SURVIVES |
| P5 | movestogo 40 median | 27 ms | 20.4 ms | 10..100 | SURVIVES |
| P6 | movestogo 40 largest | 97 ms | 53.7 ms | 40..1000 | SURVIVES |
| P8 | movestogo 1 median fraction of clock | 0.60 | 0.323 | 0.40..0.82 | **KILLED** |
| P9 | any search over the 1000 ms clock | 0 n | 0 n | 0..2 | SURVIVES |
| P7 | mtg1 > mtg2 > mtg40 median | true | true | true | SURVIVES |
| P10 | mtg50 vs mtg51 differ <= 5 % | true | 16.3 vs 16.4 = 0.0 % | <=5 % | SURVIVES |

I predicted the medians would sit near the soft limit; they sit at 65 % of it. That is what S-F9
records, and it was written down before the numbers existed.

## Times: see `stamps.txt`. Last command output: `last_command.txt`.
