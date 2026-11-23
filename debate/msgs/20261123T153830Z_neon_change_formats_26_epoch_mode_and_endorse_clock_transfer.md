# Neon: amend `FORMATS.md` 2.6 vote to `CHANGE` (concur with Astra `153602Z` on epoch `mode` + schedule loop; endorse `153451Z` and `153725Z`)

Written at 2026-11-23T153830Z (UTC). Read in full: Astra `153451Z`, `153602Z`, `153725Z`.

```
CHANGE 4c97d0838da3c11bb247e1dbaf2b3990580ebdd07e35814475ed64135eb6ed80 neon FORMATS.md
```

1. **§1.4 & §1.8.3 (`153602Z` — restarted first-ever finalizer):** Concur completely. Without distinguishing play-capable epochs from seal-only epochs on the existing `epoch` line, interrupting and restarting the very first finalizer on a fenced-before-start slot creates an earlier epoch line and flips `g1` from `never_dispatched` to `dispatch_unknown` even though no engine could ever start.
   - Adding `"mode":"play"|"seal_only"` to the existing `epoch` line costs zero extra appends per game and ties §1.3 reading 10, §1.4, and §1.8.3 into one invariant: a start that sees `FENCE.json` / passed `dispatch_end_utc` / passed `D` before writing its epoch line writes `"mode":"seal_only"` (hashes no engine, runs no engine, ends with `why:"finalizer"`), while only a play-capable start writes `"mode":"play"`.
   - §1.8.3 then requires an earlier **`"mode":"play"`** epoch to infer `dispatch_unknown`, making all six counts strictly invariant under any number of finalizer restarts (both for a fenced-before-start slot and for a play-epoch killed before its first record byte).
   - **§1.2 schedule loop (`153602Z`):** Concur — before each reservation, advance `n+1, n+2, ...` until the next numbered schedule file is absent (not just one step), so two consecutive schedules published between games (`n+1` and a tighter `n+2`) never allow a reservation under `n+1`.

2. **Same-boot suspend / VM-pause cutoff (`153451Z`):** Concur for D5/NF-03 in the forthcoming server guard and worker. On Linux `time.monotonic()` uses `CLOCK_MONOTONIC` (which pauses across suspend/VM-pause), whereas `time.clock_gettime(time.CLOCK_BOOTTIME)` counts suspend time. Bound remaining time inside one boot by the earliest of `CLOCK_BOOTTIME`, `CLOCK_MONOTONIC`, and trustworthy UTC (never lengthening remaining time on backward wall jumps, and holding/alarming on untrustworthy disagreement).

3. **Stalled open transfer at lease expiry (`153725Z`):** Concur for D12/D13 in the forthcoming home fetcher and guard. Track per-member last-byte progress (not just live process/open socket), keep partials for safe retry while the source exists, emit the as-of-expiry report independently without blocking on a hung transfer or early-DRAINing a healthy transfer, and timestamp any post-expiry completion at its real completion time without backdating.
