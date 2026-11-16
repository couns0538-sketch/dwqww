# Harness bug found and fixed before any result was reported

The first version of `timing.py` opened the engine with
`subprocess.Popen(..., text=True, bufsize=1)` and read with `select.select([self.p.stdout], ...)`
followed by `self.p.stdout.readline()`. That is wrong: the `TextIOWrapper` does its own buffering, so
after the first `readline()` the kernel fd is empty while complete lines sit inside the Python
wrapper. `select()` then reports "not ready" and `readline()` is never called again, so the harness
waits forever even though the engine has answered.

Evidence that it was the harness and not the engine:

- `out_quiet/mt50.txt` (the discarded first run) shows `status=NORESP` at wall 60000 ms for searches
  3, 72 and 131, with `engine_time_ms` 39 and 40 present in rows 72 and 131 — the engine had printed
  `info ... time 39`, so it was running normally.
- The same three positions in a fresh process each answer `bestmove` in well under a second:
  `bash repro_hang.sh ~/build/base-release/forge 5` prints five `bestmove` lines, exit 0.
- After rewriting `Engine` to read the **raw fd** with `os.read(self.fd, 65536)` and split lines in a
  byte buffer (no wrapper, `bufsize=0`), the same 200 positions at `go movetime 50` produced
  200/200 `status=ok`, wall 0.4 .. 41.6 ms.

No result in this job uses the buggy run. `out_quiet/` is deleted; the numbers quoted above are from
the preserved transcript of that run, kept in this file so the false trail is documented rather than
silently dropped.

Lesson recorded for the honest-report rule: a timeout in a harness is a claim about the harness until
a fresh process on the same input contradicts it.
