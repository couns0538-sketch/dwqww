# REPORT — seat 07, job 9: S14 known sums (validates the setoption path and my cold-start hygiene)

## What was asked / the answer / how sure

**Asked:** continue the area-7 read of the UCI loop; the specific worry being that a `setoption`
silently fails to apply, or that a harness measures warm without saying so.

**Answer:** the brief's published S14 sum for set O at depth 12 reproduces **exactly**:
**9,500,069** nodes, with the first three positions at **41,311 / 24,872 / 28,574** — all four
numbers identical to the brief. That is a joint check: it can only land on those numbers if every
one of the fourteen S14 options reached the engine through `uci.cpp`'s `setoption` path, and if
every position was searched cold.

**How sure:** very high for the sum (it is an exact integer match on four independent figures).
Moderate for the general claim that *no* option is silently ignored — I validated the path with the
options S14 uses, not with all ~50 advertised ones.

## Cold-start hygiene (response to seat 10's warning)

Seat 10 reported that two unrestricted searches in one process give 56,720 then 4,951 then 4,516
nodes, that `ucinewgame` restores cold exactly, and that `Clear Hash` does **not** (it gives a third,
deterministic value).

Audit of my own work for that trap:

| my harness | baseline used | verdict |
|---|---|---|
| job0/honesty.sh | one fresh process per check (`bench 11` … `go perft 5`) | cold, correct |
| job1/search_stress.py | one process, but `ucinewgame` + `isready` before **every** `go` | cold per position; node figures are per-search and not compared across positions |
| job2/uci_drive.py, job3, job5 | one process per case | cold |
| job4/perft_board.py, job7, job8 | one process per case / no node comparison across searches | cold |
| job9/s14_sums.py | one process per position, plus `ucinewgame` + `isready` before each `go` | cold twice over |

**I never used `Clear Hash` as a baseline**, and no table of mine compares node counts across two
searches in one warm process. The `grep` for `Clear Hash` in my folders hits only the engine's own
`uci` option list echoed into raw output files. So no result of mine needs relabelling.

## Honesty numbers

All four pins still exact on this build (job0/raw/summary.txt): 312866 / 862329 / 3024920 / 4865609.
This job's figure is a **search** sum, not a bench pin, so it is evidence about options and cold
starts rather than about node-count identity of the build itself.

## The result

    positions 200 depth 12
    SUM 9500069
      first1: nodes 41311
      first2: nodes 24872
      first3: nodes 28574

Brief's published values: O depth 12 = 9,500,069, first three 41,311 / 24,872 / 28,574. **All four
match exactly.**

Raw: job9/run_d12.log, job9/raw/sum_d12.json (per-position nodes and the last score line for every
position). Set O is `forge-combo29/tests_kimi5_job3/first200.fens` from branch
`for-fable-and-opus/kimi5-work`.

## What this does and does not prove

**Proves:** the fourteen S14 options used here — including the boolean `NonPawnCorrection`, which is
handled by a different branch of `setoption` than the spin options — all reach the search. A single
one failing to apply would change the node count and could not reproduce 9,500,069.

**Does not prove:** that every advertised option applies. Note in particular that `uci.cpp:289`
resolves tunables through a **spin** parser (`apply_spin`) over `forge::tune::parameters()`, while
the boolean `NonPawnCorrection` lives in a separate `else if` chain at `uci.cpp:403-421`. So
`NonPawnCorrection` is *not* in the tunable table; it is a check option handled by string compare.
That is consistent, but it does mean the two families of option go through different code, and only
the ones S14 touches are covered by this sum.

## Suspicions, not proven

- An option that is *advertised* but falls through to `unknown option` would be invisible to a GUI.
  My job1 edge-case run recorded no `unknown option` for any name I sent, but I did not send all ~50.
- Whether `Clear Hash`'s third value (seat 10) is a defect or simply expected, since the histories are
  not cleared: that is seat 27's S-F4 territory, which I have not checked.

## What I did NOT do

- Did not recompute the G depth-12 sum (18,466,239); set G is a different file and the run is longer.
- Did not recompute O/G at depth 14.

## Times

See job9/stamps.txt, job9/run_d12.log.
