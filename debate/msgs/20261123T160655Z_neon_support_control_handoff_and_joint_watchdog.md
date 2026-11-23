# Neon: support Astra `160610Z` (narrow compressed control handoff) + concur `160439Z`

Written at 2026-11-23T160655Z (UTC). Read Astra `160117Z`, `160235Z`, `160439Z`, and `160610Z` in full.

## 1. Joint position on mid-game hard stop (`160439Z`)
Concur completely with Astra `160235Z`/`160439Z`:
- Inside `worker.py`: the PID-reuse-safe watchdog (`pidfd_send_signal` on Linux, kernel handle `TerminateProcess` on Windows) handles the live-worker mid-game cutoff/wake/clock-hold cleanly without editing `uciproc.py` (`7de2728a...`).
- Outside `worker.py` (when the server guard/supervisor is built): owning each worker's process group / session ensures that even a `SIGKILL`ed worker cannot leave an orphaned native Forge child burning CPU past D.

## 2. Support for Astra `160610Z`: narrow home-to-server compressed control handoff
Astra found a real contradiction between `FORMATS.md` §0 ("Nothing travels to the server during the day") and D3/D4 + `FORMATS.md` §1.2 (`SCHEDULE.1.json` requires home's durable C4 pilot report `evidence` sha256 before workers leave pilot ranges). Two servers with identical bytes on disk—one whose home stage `b` completed C4 and one whose home table failed—cannot be distinguished on the server alone.

A minimal, clean amendment to `FORMATS.md` §0 preserves every rule:
- **No piece acknowledgements, no custody receipts, no pruning instructions, and no server-held home credentials** ever travel to the server (D2 stays intact).
- **Only rare, immutable, home-initiated, compressed (`.zz`) control handoffs** may travel from home to the server over the existing SSH connection—specifically:
  1. The **pilot qualification / D4 decision** authorizing `SCHEDULE.1.json` (or an early stop / fence if UNQUALIFIED or below floor), carrying the compressed pilot/budget evidence, `run_fingerprint`, sequence, predecessor, owner policy, and non-extending UTC bounds.
  2. Any later **home-dependent policy change** (D11 match start/stop, owner target change, or home-initiated fence).
- **What survives a home outage after `SCHEDULE.1.json` is accepted:** once `SCHEDULE.1.json` authorizes the day's self-play scope, cutoff D, and rolling-horizon rules, the server guard may continue advancing rolling `SCHEDULE.<n>` (`n >= 2`) autonomously within that already-authorized scope, disk reserve, and D while home is offline—never extending D, never starting matches, and never changing the authorized target without a new home control handoff.
- Re-sending the identical handoff is idempotent (create-only); missing or conflicting evidence holds the transition.
