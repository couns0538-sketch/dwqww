# R3-3 Gate proposals for every opus-r3-stack feature — DONE

(Text of the sub-agent's report, saved verbatim by the main session; the agent could not write REPORT.md.)

Branch `opus-r3-gates` = `opus-r3-stack` @ `2047348a` (fast-forward from `2432670b`, as the main session asked) + 5 R3-3 commits. These are documents, tools and logs only, all `[skip ci]`, so 0 CI runs. Head `b5d2eba3`, verified with `git ls-remote`. No engine file changed.

Deliverables: `F:\opus_scratch\r3\GATE_PROPOSALS.md` = `opus_r3/R3-3/GATE_PROPOSALS.md` (sha256 `38c76f2e…`), `SRAND_CHECK.md`, `GATE_ENTRIES.json` (the 29 manifest objects), `exe_map.json`, `tools/`, `logs/`, README.md, IDEA_SOURCE.md, FILES.txt, SHA256SUMS. **No gate was started, and nothing was written to any gate, queue or lock folder; the PC queue files were read through copies.** No Elo claim.

## Acceptance
| # | line (job R3-3) | result | evidence |
|---|---|---|---|
| 1 | One ready entry per feature: exe, UCI option in `option.Name=value` form, SPRT [0,5] a=b=0.05 normalized, 1500 games (cap stated), 10+0.1, Threads>1 for SMP, 8moves_v3 book, concurrency 8, new srand | **29 entries.** 19 can go into the r7 queue once the exe is copied to `forge_push\bin` and the CR ok flag exists (R3-15 runs only if R3-08 ends Elo ≥ 0 via `run_if`; R3-19 runs last per the A1 plan). 10 carry `HELD_…`: R3-20 NnueInt16 (CR policy needs a crew vote), R3-21..23 SMP (r7 hard-codes Threads=1/Hash=16), R3-24..29 (no trained net). The final exe sha256s of head 330237f3 are filled in. | GATE_PROPOSALS.md §1, §4, §6; GATE_ENTRIES.json; `logs/pins/validate_entries.log` (all checks pass) |
| 2 | srands: find every used one read-only, choose new ones, document | 406 srand-context and 261 seed-context values found in 221,921 files (2.39 GB): grok-pc, D:\grok-pc-data including every gate folder and the lock package, F:\forge_push, F:\opus_scratch, memory, Downloads. Plus 15,767 git blobs from 388 refs, with Sol's 17aa0cae read via `git show`. 35 new srands (29 + 6 spare), each the first SHA-256 candidate, with **0 literal occurrences** anywhere. The live manifest re-copied at the end was unchanged and still had no hit. | SRAND_CHECK.md; `logs/scan/` |
| 3 | Rank by expected gain and risk, reasons, run order | Ranked table and run-order notes. Tiers: A node-exact speed (small but safe), B search (uncertain), C SMP, D nets (blocked). Expectations are labelled as such. | GATE_PROPOSALS.md §3 |
| 4 | Exact fastchess command per entry | In r7 Build-Args form (SMP: Threads 4/Hash 64 on both sides, concurrency 2) | GATE_PROPOSALS.md §4 |
| — | Prebench pins exact | 17 runtime-option sets measured at 5 depths on a 2047348a default build (identity ALL OK). Every value that appears in a job REPORT was reproduced exactly. New: Syzygy d20/d22 11465604/31972996; NetScale 99 308948/917342/2601047/14196959/32409747. Five switch builds: FMA 0, OFF = AL1 pins, TtChildPrefetch and NnueLazyAcc ON = AL1 pins. INT16 build of ba03edf9: ON 330610/858175/2760596/9564588/21638970. On the final 330237f3 exes the sha256s recompute to the EXES.txt values, and the d11/d13 spot check matches for 23 of 23 entries. | `logs/pins/`, `logs/final/` |
| — | HardDeadline fix | The R3-13 entry states fix 5792074a; 330237f3 contains it. | GATE_PROPOSALS.md R3-13 |

## Findings
1. **SPRT [0,5] with a 1500-game cap decides almost nothing.** This comes from an approximate model (normal approximation of the GSPRT, 20,000 runs per value, `logs/model/sprt_cap_model.json`), not fastchess figures.
   - An H1 at the cap needs about +50 nElo observed; an H0 needs about −45.
   - For true values from −10 to +20 nElo, P(cap) ≥ 0.999.
   - A true −20 nElo ends H0 in 0.4% of runs, against 62% at [0,10].
   - On this PC nElo ≈ 2.06 × Elo (median of 45 ledger rows).
   - In the ledger, 23 of 24 option gates already capped at [0,10].
   - The crew held the e32c [0,5] gate for exactly this reason (r7 hard-codes the 1500 cap).
2. **The r7 runner cannot run SMP gates.** Build-Args, Static-ArgCheck and Void-Check hard-code Threads=1 and Hash=16. R3-21..23 need a runner change or a manual run while the queue is idle.
3. **No trained v2 or H512 net exists.** Every `.fnn2` on the PC is a replica, identity or CPU smoke net.
4. **Runner blind spot.** The "option did not apply" check compares against the old h256_e12 bench numbers, not AL1. It cannot catch a node-exact option that silently did nothing.
5. **Gap in the QA srand helper.** `common_autonomy.ps1` Used-Srands misses RUN_INFO files under F:\forge_push, where gate folders have lived since 2026-10-27.
6. **GATE_RULES.md asks [−3,1] for node-identical speed changes.** The speed entries use the user's [0,5] and note this.

## UNVERIFIED / left
- Five-depth ON pins were measured on the 2047348a and ba03edf9 probe builds. On the final exes only d11/d13 were checked; the runner re-benches all five depths before each gate and aborts on any mismatch.
- The SMP entries need the runner change, the net entries need GPU training, and R3-20 needs a crew vote.
- The decision rates come from the approximate model only.
- The gains are expectations; no gate was run.
- 330237f3 was not merged into opus-r3-gates (not asked). The documents reference its exes.

Machine exclusive: no.

R3-3 | opus-r3-gates | DONE (b5d2eba3) | 29 gate entries (19 queue-ready, 10 held), 35 new srands with 0 hits in 221,921 files + 15,767 git blobs, final 330237f3 exe sha256s filled and spot-checked; [0,5]/1500 expected to end at the cap almost always
