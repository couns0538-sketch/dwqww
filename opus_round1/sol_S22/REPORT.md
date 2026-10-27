# S22 TSan audit at Threads=2/4 + Lazy SMP depth sanity — COVERED by opus-O1 (no new engine work)

`SOL_LEFTOVERS_FOR_CLAUDE.md`, section 2, item 17. Section 2 says: "Skip any job already covered by an
opus-*/fable-* branch (… O1 vs S22 …) and say so in REPORT.md."

**Branch.** This branch (`opus-sol-S22`, from `d4f4312` = the AL1 s198 lock tree + baseline evidence) holds
only this report, Sol's one S22 input file and a FILES index.

**Where the work is.** Branch `opus-O1`, folder `opus_round1/O1/`. Its REPORT.md has the audit table, the bug
list with repro and fix commit per bug, TSan logs, self-play PGNs, the scaling table and the gate specs.

## Sol's spec (inventory `jobs[]` id S22, verbatim)
> Goal: tag each race (TT, history, stop flag) as benign or real. Fix real ones only, one patch each, and
> report the depth gain at T2/T4. Deliver: forge_sol_S22_tsan_<date>.md + patches + report. Pass: T1 bench
> at refs per patch; a repro or log line per race.

## Spec item -> evidence on opus-O1

| S22 item | status | evidence (all on branch `opus-O1`) |
|---|---|---|
| Tag each race (TT, history, stop flag) as benign or real | **covered** | REPORT.md "Audit" table: TT entries/torn reads (none possible: 1024 striped mutexes, copies returned), TT lifecycle, shared counters (stale between searches = real, bug 1), `all_workers_` lifetime (dangling = real, latent, bug 2), stop hand-over (benign, explained), best move across workers, `setoption Threads` resize, `ucinewgame`, `go infinite`/`ponderhit`/`isready`. History tables are per worker (ThreadData), so no race |
| Fix real ones only, one patch each | **covered** | Bug 1: commit `44b2db1` (UCI `SmpExactNodes`, default off, because it changes Threads>1 node accounting). Bug 2: commit `c994f6e` (no behaviour change) |
| A repro or log line per race | **covered** | Bug 1: `opus_round1/O1/repro_stale_nodes.py` (lock exe: 4/5 rounds of `go nodes 20000` at Threads 3 played an unsearched move; with the fix 0/5), `logs/repro_stale_nodes.log`; `tests/smp_tests.cpp` (10/10 repro). Bug 2: `tests/smp_tests.cpp` "worker list pointer cleared" (fails 2/2 before the fix). TSan: 0 reports on 200 positions x depth 12 at Threads 2/4/8 and on a 500-iteration stop/ponderhit/isready/setoption-Threads stress (CI run 40381524268, `logs/ci/tsan_full/`) |
| Depth gain at T2/T4 | **covered** | REPORT.md "Scaling": time-to-depth and NPS at Threads 1/2/4/8, 36 positions, depth 20, 5 runs each (CI run 40381524051, a 2-core / 4-thread runner): T2 1.12x speed-up in time-to-depth (1.82x NPS), T4 0.98x (2.36x NPS) |
| T1 bench at refs per patch | **covered** | bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354 after each O1 commit (PC recipe and Linux CI); both options are inert at Threads=1 (tested) |

## Sol's open observation, resolved by O1 bug 1
`sol_S22_observation_from_S10_20261026.json` (copied from Sol's branch `17aa0cae`; sha256 prefix 05188311):
- **What Sol saw.** In an S10 run at Threads 2 (WAC.003), the first `info` line reported 6231 nodes at depth 1
  and the next 252 at depth 2.
- **Sol's hypothesis** (left UNVERIFIED): "A helper worker atomic node counter may still contain prior-search
  work when the next search emits its first info, then reset at worker entry".
- **O1 bug 1 confirms it.** O1 found, reproduced and fixed exactly this mechanism. A helper publishes its count
  only from inside its own search, so the previous search's count stays visible until the helper starts. That
  inflates the first info lines, and at `go nodes N` it can stop the search before depth 1 completes.
- **Fix.** `SmpExactNodes` resets every worker's published count before the helpers start, and reports the exact
  total after they stop. It is an OFF-default option, proposed for an SMP-only gate in O1's REPORT.md.

## What is left / UNVERIFIED
- Nothing for S22 beyond O1's own open items: SMP-only gates for `SmpExactNodes` and `SmpBestThread` (QA), and
  scaling on a machine with at least 8 idle cores.
- Not re-run here: no new native run was made for this report (machine exclusive: n/a).
- Related O1-LTT (UCI `LocklessTT`, branch `opus-O1-LTT`) adds a multi-thread TT stress at Threads 2/4/8 (TSan
  clean, 0 corrupted entries in 10M operations).

## Files
`REPORT.md`, `FILES`, `sol_S22_observation_from_S10_20261026.json` (Sol's input, unchanged), `SHA256SUMS`.
