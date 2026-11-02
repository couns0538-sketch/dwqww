# R10 launcher preflight regression evidence — UNPROVEN

These are PowerShell 5.1 bootstrap tests of safety preflight functions. No engine,
training job, GPU job or fixture executable was launched. Test processes set their
own Idle priority and affinity to logical CPU 2 before filesystem work. Other
processes were not changed. The full protected-root list is preserved in the test.

- `red-001`: original installed launcher SHA256
  `6300788E7F0BDA9E54F9D751AC823F6E2A7F41FC92849478A7198B6711A62F90`.
  Reproduces rejection of C:/F: protected roots, acceptance of writes outside
  D:/a10, and acceptance of the older 32 GiB floor. New storage-budget functions
  are absent. An alternate-stream test also exposed a generic path error before
  the explicit lexical diagnostic.
- `green-001`: product fixes pass; one test-harness error remains. PowerShell's
  array-expression precedence concatenated the sibling root and F: entry. This
  was corrected by parenthesizing the sibling-root expression.
- `green-002`: all **19 preflight cases PASS**, including a real owned junction
  that is refused both by workspace enumeration and runtime ancestor checks.
  Only that temporary junction was removed; its target directory remains.

Run again with a new evidence directory:

```powershell
powershell -NoProfile -File D:\a10\wt\astra_r10\job1\safety-tests\Test-R10Safety.ps1 -Launcher D:\a10\wt\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1 -Evidence D:\a10\wt\astra_r10\job1\safety-tests\green-003
```

Each `results.json` binds the launcher hash, timestamp, own process priority and
affinity. The test report is a preflight regression result, not a native workload
qualification. Complete native capture/child execution still requires its own
reviewed safe manifest and receipt. Workspace accounting is conservative logical
file bytes, counts hard links per pathname, and rejects reparse points. A minute
between workspace rescans does not enforce a kernel quota: reviewed adapters must
honor the reserved upper bound and stop at bounded unit boundaries.
