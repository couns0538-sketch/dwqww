# REPORT_job4 — perft 4 at the DIVIDE level (closes my stated totals-only limit)

## What was asked
The coordinator's first new job: my S-C4 control proved a compensating error can pass a totals-only
comparison, so rather than add more positions, re-run perft 4 on 200 R positions with a
**per-divide** comparison against python-chess and report differences at the divide level.

## The answer
**Every root move agrees, on both builds and under both settings regimes.** 200 positions and
**5,182 root moves** compared per run, **0 differing** in all three runs that could be run:

| build | settings | positions | root moves compared | positions differing | missing / extra / wrong counts |
|---|---|---|---|---|---|
| base 6b98f217 | Threads 1, Hash 16 | 200 | 5,182 | **0** | 0 / 0 / 0 |
| PC r15 | Threads 1, Hash 16 | 200 | 5,182 | **0** | 0 / 0 / 0 |
| PC r15 | **PC20** | 200 | 5,182 | **0** | 0 / 0 / 0 |
| base 6b98f217 | PC20 | — | — | **not run: PC20 cannot apply** | the base build does not advertise CuckooRep/HistRework/TtPruneV2/CorrHistV2/MateAlphaGuard, so the harness refused rather than silently sending options the exe would ignore |

Two independent cross-checks also held in every run: the engine's own `nodes` total equalled the sum
of its own per-root-move counts (200/200), and the engine's total equalled python-chess's total
(200/200). Those are the weak checks my earlier jobs relied on; they now sit *underneath* a strong one.

## How sure
High, and this is the strongest evidence in my whole run, because the harness is proven able to fail:

**Rule-1 control (`CONTROL_DIVIDE.md`, run before the real measurement, through the same comparison
function):**

| plant | method | total unchanged? | caught |
|---|---|---|---|
| P0 identity | engine copy of the reference | yes | correctly **not** flagged |
| A compensating | `a2a3 +1`, `a2a4 -1` | **yes (197,281 vs 197,281)** | **CAUGHT** (`a2a3`, `a2a4`) |
| B missing move | delete `h2h4` | no | **CAUGHT** |
| C extra move | insert a move python-chess does not have | no | **CAUGHT** |

So a zero from this harness is a measurement, not an artefact of a checker that cannot see anything.

## Settings and build, stated per the rules
Threads 1 and Hash 16 are sent explicitly in every regime (the swarm's Threads-1 rule for scores).
Perft is synchronous and single-threaded, so threading cannot affect it — but it is stated anyway so
the table cannot be mistaken. Builds: base `e06310ec...` (g++ 13.3.0, x86-64-v4), PC r15
`068f0927...` (same toolchain, `-DFORGE_MATE_ALPHA_GUARD=1`). Raw per-run JSON is committed, plus the
cached engine output each run reused (`*.engine_raw.json`).

## Table of steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| Divide harness written to file | done | `divide_perft4.py` | sends Threads 1 / Hash 16, validates every option name against the exe's own `uci` list |
| Rule-1 control, before measuring | done | `control_divide.py`, `CONTROL_DIVIDE.md` | identity not flagged; compensating, missing and extra all caught |
| 200 R positions (first 200 of R_1301) | done | `R200.fens` | 200 |
| base build, no settings | done | `base_none.json`, `base_none.log` | 5,182 root moves, 0 differing |
| PC build, no settings | done | `pc_none.json`, `pc_none.log` | 5,182 root moves, 0 differing |
| PC build, PC20 | done | `pc_pc20.json`, `pc_pc20.log` | 5,182 root moves, 0 differing |
| base build, PC20 | not run (correctly refused) | `base_pc20` error: `FAIL: option 'CuckooRep' not advertised by this exe` | PC20 is a PC-build-only regime |
| perft 5 at divide level | not done | — | divide at depth 5 would be ~30x the reference cost; the totals comparison in job 3 stands as-is |

## Findings
- S-F5: at the **divide** level, the engine's perft 4 equals python-chess on 200 R positions —
  **5,182 root moves each, 0 differences** — on base (Threads 1/Hash 16), PC r15 (Threads 1/Hash 16)
  and PC r15 under PC20. The harness catches a compensating error that leaves the total exact
  (`CONTROL_DIVIDE.md`), so this is not the totals-only evidence my earlier jobs had.
  Show it again with
  `cd forge-combo29/swarm/13/job4 && python3 control_divide.py R200.fens` then
  `python3 divide_perft4.py ~/b/pc/forge R200.fens /tmp/o.json PC20` and read `positions_differing`.

## Suspicions, not proven
- None about the engine. The only fault this job produced was in my own summary code (below).

## What I did NOT do
- Depth-5 divide (cost).
- The base build under PC20 (impossible: options absent).

## What I am NOT sure about
- 200 positions is the same R sample as job 1, so it inherits that sample's bias (opening and early
  middlegame). The divide check is much stronger per position but is still a sample.
- A divide at depth 4 detects errors in the subtree counts, which is where a compensating error would
  have to hide. It does not prove anything about depth 5+ at that granularity.

## A fault in my own tooling, recorded
My first version of the summary crashed (`len()` applied to an int) **after** the engine had measured
all 200 positions, and the raw output would have been lost. I fixed the bug and changed the harness to
write the engine's raw divide to `<out>.engine_raw.json` immediately, so a later reporting error can
never discard a measurement, and to reuse that cache on a re-run. The three runs above all report
`REUSED cached engine output for 200 positions`, i.e. they were recomputed from the engine's own
committed raw output rather than re-measuring. I also briefly had two background scripts competing for
the same log files; I killed both and re-ran one instance, which is why the logs are single-writer.

## Times
See `stamps.txt`.

## Last command output

```
$ ls
base_none.json
base_none.json.engine_raw.json
CONTROL_DIVIDE.md
control_divide.py
divide_perft4.py
pc_none.json
pc_none.json.engine_raw.json
pc_none.log
pc_pc20.json
pc_pc20.json.engine_raw.json
pc_pc20.log
pcstat2.txt
pcstat.txt
R_1301.fens
R200.fens
REPORT_job4.md
stamps.txt
```
