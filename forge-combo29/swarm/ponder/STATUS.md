# STATUS — ponder protocol audit

**Seat:** owner-audit  
**Engine:** `forge-combo29`  
**Repo:** `couns0538-sketch/dwqww`  
**Audit base commit:** `6b98f2170a3210e71beed04bbd2553972c253ed7`  
**Branch:** `swarm/ponder`  
**Delivered:** `forge-combo29/swarm/ponder/`

---

## Verdict per item

| # | question | verdict | confidence |
|---|---|---|---|
| 1 | `ponderhit` converts to a clocked search? budget from `go` or `ponderhit`? | **Converts. Budget starts at `ponderhit`.** | strong — three independent lines |
| 2 | `go ponder` + `stop`, no `ponderhit` — bestmove? which move? | **Returns a bestmove, is never `0000`, and is the move found** (18/18) | measured |
| 3 | `go ponder wtime X btime Y` bounded? | **Unbounded — a clock does not bound it** | measured to a 45 s horizon |
| 4 | `ponderhit` with no ponder running | **Silent, engine stays responsive** | measured, with a live control |
| 5 | `Ponder` option true/false | **Only appends ` ponder <move>` to `bestmove`** | measured — identical node counts |
| 6 | output during pondering; one `bestmove`? | **info streams ~10/s; exactly one `bestmove`, nothing after** | measured across 4 command races |

## The three numbers requested

`ponderhit` → `bestmove`, fixed 2 s ponder, three clocks:

| clock | soft | hard | **hit → bestmove** |
|---|---|---|---|
| 2 000 ms | 90 | 450 | **176.2 ms** |
| 10 000 ms | 454 | 2270 | **463.0 ms** |
| 60 000 ms | 2726 | 13 630 | **1816.5 ms** |

**Which budget: from the `ponderhit` moment.** The decisive check is a ponder
*longer than the whole planned budget*: 6 s of pondering against a 225 ms hard
limit (26.7× over) still received **225.9 ms** of search afterwards — the full
fresh budget. If the budget had been measured from `go`, that search had been
exhausted 5.8 s earlier and `ponderhit` would have returned instantly. Across 16
offsets at two clocks, **zero** rows returned in ~0 ms and the worst case
exceeded the hard limit by **0.9 ms**. That is an upper bound, not an equality:
10 of 16 rows stopped below 60% of hard.

---

## Build and pin verification

Built from `6b98f217` with the trap recipe:

```
cmake -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_BUILD_TYPE=Release
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13
```

g++ 13.3.0. All four pins confirmed on the exact binary used for every
measurement (**`evidence/pins/pins.txt`**):

| pin | expected | measured |
|---|---|---|
| bench 11 (net on) | 312 866 | **312 866** |
| bench 13 (net on) | 862 329 | **862 329** |
| bench 16 (net on) | 3 024 920 | **3 024 920** |
| perft 5 startpos | 4 865 609 | **4 865 609** |

Net-off pins also matched (`375 354 / 907 205 / 2 448 617`), and the full
5-depth vectors for both nets are in the evidence file.

---

## Bounding discipline

Every probe has a deadline and **every deadline hit is reported as `CAPPED`
with the process SIGKILLed** — never inherited as a hang. **No probe in this
audit hit its cap**: all six requested items returned, so all verdicts below are
based on returns, not timeouts.

The two probes that deliberately measure absence of a return (§3's unbounded
ponder) are bounded at 20 s and 45 s and report `UNBOUNDED_NO_BESTMOVE` with the
depth curve, node count and CPU% at the cap, so "still climbing" is a
measurement rather than an assertion.

---

## What changed in understanding versus `forge-findings.md`

**1. The clocked ponder was not covered, and it is unbounded too.** Trap 3a1
documents `go ponder` *without* a clock as unbounded, which reads as though a
clock would bound it. Measured: `go ponder wtime 10000 btime 10000` is
**identical in behaviour** — no `bestmove` at 20 s (depth 28, 24.8 M nodes, 99.9%
CPU) or at 45 s (depth 32, 61.2 M nodes). The cause is the one the trap names:
`elapsed_ms()` returns 0 while `ponder_hit_ns == 0`, so the clock is never
consulted, clock present or not.

**2. "Unbounded" has two mechanisms with different costs.** A runner sees the
same silence from both:

- **RUNAWAY** (clocked or clockless `go ponder`): CPU 99.9%, depth still rising.
  Costs a core until stopped.
- **WITHHELD** (`go ponder depth N` / `go ponder nodes N`): the search has
  *finished* — 0.1–1.5% CPU, depth flat, 0 `bestmove`. Idle, waiting forever.
  A monitor that only checks "did it return" will call a finished search hung.

Both recover with `stop` in **under 1 ms**, and that `stop` reply is the found
move.

**3. Two clocks disagree inside one search.** The `info` `time` field counts
from the `go` command; the stop decision counts from `ponderhit`. After a 3 s
ponder the engine reports `time 4140` having thought 1141 ms. The gap equals the
ponder length exactly (500/3000/3000 ms in three cells). A runner reading `time`
to check budget compliance reads a number inflated by the ponder. The engine's
budget is correct; only the label is wrong. Reproduced at a 6 s ponder against a
225 ms hard limit: `time 4174`, 226 ms of actual post-hit work.

**4. The `Ponder` option is a formatting flag, and it is off by default.** It
only appends ` ponder <move>`. Node counts identical (17 804 both arms). It does
not trigger self-pondering (3 s of silence after `bestmove`, both arms) and does
not gate the `go ponder` token. Because the default is `false`, **a runner gets
no ` ponder` hint at all unless it sets the option** — and the hint is omitted
entirely when the PV has length 1 (mate-in-one: `bestmove a1a8`, no suffix).

**5. A zero-ms `stop` reply is indistinguishable from the piped-abort artifact.**
After `go ponder` + immediate `stop` the engine answers the first legal move with
zero info lines. So does closing stdin immediately. The two make identical
predictions on both positions tested (A: `a2a3`, B: `f7f6`), so **this audit does
not decide which happened** and says so rather than picking the flattering one.
Consequence for existing corpora: a zero-info-line first-legal row is unlabelled.

**6. A runner can desync by restarting without consuming the abort's
`bestmove`.** Two `bestmove` lines appear, and without `stop` first the stale one
arrives **0.5 ms after** the new `go` — so "first bestmove after my `ponderhit`"
pairs the previous position's move with the new position. Both sequences end
correctly, so this fails silently.

---

## Reproduction

```
cd forge-combo29/swarm/ponder
python3 scripts/check_claims.py            # 39/39 pass, exit 0
python3 scripts/make_tables.py             # regenerate FINDINGS.md tables
```

Full re-measurement (needs the built binary; ~12 min total):

```
python3 scripts/probe_ponder.py            --exe <forge>   # items 1,2,3,4,5,6 + control
python3 scripts/probe_ponder2.py           --exe <forge>   # budget-origin sweep, interrupts
python3 scripts/probe_ponder3.py           --exe <forge>   # three clocks, self-ponder, time field
python3 scripts/probe_ponder4.py           --exe <forge>   # self-limited ponder, terminal root
python3 scripts/probe_ponder6_residuals.py --exe <forge>   # stop-move, time field, EOF artifact
python3 scripts/probe_ponder7_suffix.py    --exe <forge>   # suffix legality
python3 scripts/probe_ponder8_hazard.py    --exe <forge>   # RUNAWAY vs WITHHELD
python3 scripts/probe_ponder9_bound.py     --exe <forge>   # 16-offset upper bound
python3 scripts/probe_ponder5_desync.py    --exe <forge>   # runner desync
```

## Evidence index

`evidence/pins/` — compiler, configure flags, `check_pins.sh` output and the raw
engine output it parsed.  
`evidence/probe*_results.json` — every measurement, one file per probe round.  
`evidence/probe*.log` — run transcripts, including which probes were re-run
after a harness bug and why.

## Known gaps (stated, not papered over)

- **All wall-clock figures are single-sample per cell** except the 16-offset
  sweep and the 6×3 stop matrix. The same request varies by ~±100 ms because the
  stop lands on an iteration boundary. Timings are reported as a bound plus a
  typical value, never as a constant.
- **One position** for all timing work. A position whose iteration is longer than
  the whole budget could behave differently in the `iterations after hit` column.
- **`MultiPV > 1` untouched**; `Threads 2/4` spot-checked only (one `bestmove`,
  no trailing lines, hit→best 454/766 ms).
- **The desync in §6 is a protocol sequence, not an observed runner bug.**
- **`nodes` work inside an aborted iteration is invisible on the wire**, so the
  post-hit node count is not measurable directly; the budget claim rests on wall
  time and the hard-limit bound instead.
