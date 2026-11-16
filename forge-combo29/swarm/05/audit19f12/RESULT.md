# 19-F12 harness audit — seat 05 (area 5)

Seat 19's finding 19-F12 (as broadcast): *if a harness pipes `quit`, or closes stdin, while a search is running,
this build answers a FABRICATED `bestmove` with 0 nodes.* The broadcast asked every seat to audit its own harness
and to re-run anything recorded with a pipelined `position / go / quit` pattern.

## 1. Does 19-F12 reproduce on my build?

Yes, exactly as described. `audit_19f12.py`, release build sha256 `e06310ec...a83`, `go depth 12`, S14:

| pattern | startpos | middlegame FEN |
|---|---|---|
| P1 whole script piped with a trailing `quit` | **`bestmove a2a3`, 0 info lines** | **`bestmove a2a3`, 0 info lines** |
| P2 live process, `go` then `quit` immediately | **`bestmove a2a3`, 0 info lines** | **`bestmove a2a3`, 0 info lines** |
| P3 live process, `go`, wait 2 s, `quit` | `bestmove e2e4`, 12 info lines, 56,720 nodes | `bestmove e1g1`, 12 info lines, 70,292 nodes |
| P4 read stdout to `bestmove`, then `quit` | `bestmove e2e4`, 12 info lines, **56,720 nodes** | `bestmove e1g1`, 12 info lines, **70,292 nodes** |

P3 and P4 agree to the node, so reading to `bestmove` is equivalent to letting the search finish.
Raw: `raw_audit.txt`. This is seat 19's finding, not mine — I do not add it to my FINDINGS as a new finding.

## 2. Which of my harnesses were exposed

I grepped my own folder for every place stdin is closed or `quit` is piped:

| file | pattern | exposure |
|---|---|---|
| `job0/honesty.sh` | `printf '%s\nquit\n' \| "$EXE"` for the four honesty lines | **EXPOSED** — this is exactly the P1 pattern |
| `job1/run_rows.py` | `subprocess.run(input="uci\nquit\n")` | harmless: only used to read `id name`, no search |
| `job2/run_job2.py`, `job3/run_job3.py` | same `uci\nquit` probe for `id name` in the `.meta` | harmless, same reason |
| `job1/run_rows.py` main loop | reads until `bestmove` before `quit` | **CLEAN** (P4 pattern) |
| `job2/run_job2.py` main loop | reads until `bestmove`/`readyok` before `quit` | **CLEAN** |
| `job3/run_job3.py` main loop | reads until `bestmove` before `quit`; also kills on a 30 s hang | **CLEAN** |
| `job1/mate_repeat.py`, `mate_depth_probe.py`, `uci_drive.py`, `sf_mate.py` | live process, read to `bestmove` first | **CLEAN** — I hit and fixed this exact bug in `uci_drive.py` earlier (the `(no pv)` rows in `out/probe_pos306.txt` were this bug) |
| `job2/threshold_probe.py`, `job3/terminal_root_probe.py` | live process, read to `bestmove` | **CLEAN** |

## 3. Is the job1 result invalid?

**No — job1's numbers are sound, and this is provable rather than argued.** A fabricated `bestmove` carries
**0 nodes and no `info` line**, so a rows run infected by 19-F12 could never reproduce the brief's published
node sums. My `out/O.d12.raw.txt` and `out/G.d12.raw.txt` reproduce them exactly:

| set | positions | sum of last depth-12 `nodes` | brief's known sum | match |
|---|---|---|---|---|
| O | 200 | 9,500,069 | 9,500,069 | yes |
| G | 353 | 18,466,239 | 18,466,239 | yes |

and O's first three are 41,311 / 24,872 / 28,574 against the brief's 41,311 / 24,872 / 28,574, with **0 zero-node
positions** anywhere in either file (`job1/out/harness_audit_sums.txt`). Every one of the 553 positions also
yielded a PV line, which a fabricated answer cannot produce.

## 4. The one harness I did re-run

`job0/honesty.sh` used the P1 pattern, so the four honesty numbers were re-measured with
`honesty_safe.py` (live process, `bench`/`go` followed by a queued `isready`, quitting only after the `readyok`
that follows the command's output — `bench` prints no `bestmove`, so the readyok is the correct terminator):

| name | command | expected | got | verdict |
|---|---|---|---|---|
| bench11 | `bench 11` | 312866 | 312866 | OK |
| bench13 | `bench 13` | 862329 | 862329 | OK |
| bench16 | `bench 16` | 3024920 | 3024920 | OK |
| perft5 | `go perft 5` | 4865609 | 4865609 | OK |

**HONESTY RECHECK PASS 4/4** (`out/recheck.txt`, raw per line in `out/*.raw.txt`). So the build still passes and
`HONESTY.txt` stands; the numbers did not depend on the risky pattern.

## 5. Job 2 and job 3 — exposure and confidence

- **job3** ran entirely through the read-to-`bestmove` runner; its 60 runs all returned `bestmove 0000` at
  terminal roots, where `0000` is the correct answer and 0 nodes is the correct node count. A fabricated answer
  would have been indistinguishable there, which is why I did **not** rely on job3's `bestmove` values for any
  claim — the claims I made from job3 are only "0 sanitizer lines, 0 crashes, 0 hangs", and the sanitizer proof
  (planted fault counted through the same runner) does not depend on which `bestmove` came back.
- **job2** used the same read-to-`bestmove` loop. Its fifty-move and threefold results report node counts
  (0 for the terminal/dead cases, hundreds to millions for the searched ones), and `threshold_probe.py` — the
  source of the S-F3 cliff — is a live read-to-`bestmove` harness, so S-F3 is not affected.
- **One caveat I must state:** job3's harness reads to `bestmove`, but at a *terminal* root the engine may emit
  `bestmove` before any search has been attempted, and 19-F12 lives in that same code path. I therefore cannot
  rule out that job3's `bestmove 0000` is fabricated rather than computed. It does not matter for the job3 claims
  (sanitizer silence), but it would matter if anyone cited job3 for the *value* of the bestmove, and I do not.

## 6. What I changed
- `honesty_safe.py` added and used; `honesty.sh`'s numbers re-confirmed through it.
- No other harness needed changing: the grep above shows every other search-driving harness already read to
  `bestmove` or to a queued `readyok` before quitting.
