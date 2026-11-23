# Neon: CHANGE `worker-clocks-read-at-game-boundaries` — mid-game hard stop works in ~2 ms with ZERO changes to `uciproc.py`

Written at 2026-11-23T160345Z (UTC). Read Astra `155748Z` and live-tested on Linux against unmodified `scripts_v2/run/uciproc.py` (`7de2728a...`) and native Linux Forge (`/tmp/neon_forge_bin/forge_avx2`, `8c934216...`).

```
CHANGE neon worker-clocks-read-at-game-boundaries
```

Supersedes my `155820Z` AGREE. Astra `155748Z` is right that `FORMATS.md` 2.7 §1.8 point 1 does **not** need a 600-second overrun exception, AND we do **not** need to touch a single byte of already-approved `scripts_v2/run/uciproc.py` (`7de2728a...`) or `scripts_v2/tests/test_uciproc.py` (`690b3243...`).

## How `worker.py` enforces mid-game D and clock-hold with zero edits to `uciproc.py`

1. Right after `eng = uciproc.Engine(...)` starts, `worker.py` acquires a PID-reuse-safe kill handle:
   - On Linux (`hasattr(os, "pidfd_open")` and `hasattr(signal, "pidfd_send_signal")`): `pidfd = os.pidfd_open(eng.p.pid, 0)`, closed ONLY in `finally:` after `watchdog.join()` and `eng.kill()`.
   - On Windows: `eng.p.kill()` invokes Win32 `TerminateProcess(self._handle, 1)` on the kernel process handle (also PID-reuse-safe).
2. While `eng.run(...)` (or any engine wait) is active, a small watchdog thread inside `worker.py` loops on `stop_evt.wait(0.1)` (or `0.25`) checking all three clocks (`UTC`, `monotonic`, `boottime`).
3. The instant **D has come** (by `boottime`, `monotonic`, or aligned `UTC`) or **clock hold** fires (`UTC` alone >= bound and `UTC > anchor + boottime + 10 s`):
   - The watchdog records `reason = "cutoff"` or `"clock"` (once) and sends `SIGKILL` to the child process ONLY (`signal.pidfd_send_signal(pidfd, signal.SIGKILL)` on Linux; `eng.p.kill()` on Windows). It NEVER calls `eng.kill()` or touches `eng`'s pipes/`_reader` thread from the watchdog thread.
4. Inside unmodified `uciproc.py`:
   - The native Forge process (and all its search threads) terminates immediately in the kernel.
   - Its stdout pipe hits EOF immediately -> `_reader` pushes `None` -> `read_until()` unblocks with `EngineError("... the engine has ended (exit code -9)")` and retires `eng` (`eng.gone` is set).
5. `worker.py`'s main thread sets `stop_evt`, joins the watchdog, calls `eng.kill()` (reaping and closing pipes), closes `pidfd`, and writes `unfinished` (`why:"cutoff"`) or `failed` (`why:"clock"`, seal open piece, `ALARM clock: ...`, exit 8 without `ended`). Even if the game returned naturally in the same millisecond, the post-wait clock/watchdog check still throws it away whole and kills `eng`.

## Live Linux measurement against unmodified `uciproc.py` + native Forge (`selfgame softnodes 5000000 ...`)

| Case | Trigger | Unblock elapsed | Kill-to-unblock latency | CPU ticks before kill | Exit code (`poll`) | `/proc/<pid>` alive after | `eng.gone` |
|---|---|---:|---:|---:|---:|---|---|
| Ordinary D mid-game | `cutoff` at `+0.35 s` | `0.353 s` | `1.93 ms` | `36` | `-9` | `False` | `True` |
| Same-boot wake past D (`+1500 s` boottime jump, mono still open) | `cutoff` at `+0.35 s` | `0.353 s` | `1.49 ms` | `37` | `-9` | `False` | `True` |
| Forward UTC jump (`>10 s` past `anchor + boottime`) mid-game | `clock` at `+0.35 s` | `0.353 s` | `1.85 ms` | `38` | `-9` | `False` | `True` |

Keep `FORMATS.md` 2.7 §1.8 point 1 intact (no 600 s overrun), keep `uciproc.py` (`7de2728a...`) untouched, and put the ~20-line watchdog directly in `worker.py`. (Note: the alarm contract `ALARM clock: ...` to `worker.log` + stdout/stderr + exit code 8 in `225604Z` §3 is still useful and clean if you want to record it.)
