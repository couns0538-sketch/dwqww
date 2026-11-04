# tune_spsa - SPSA tuning of Forge search constants (Opus 30-h job, Item B)

Own code (a port of R9's tuner). Tunes Forge search constants exposed as UCI options by playing fastchess game pairs
at a short time control, unattended: it resumes after a crash or a reboot, keeps to a thread cap and a CPU mask, waits
while a running gate uses its CPUs, stops at a deadline, and logs every iteration to CSV. No Elo claim: the crew gates
the result (UHO [0,5] SPRT + 8moves_v3 confirm).

## Files
| file | what |
|---|---|
| `tune_spsa.py` | the tuner (`run`, `stop`, `status`) |
| `tune_spsa.ps1` | re-runnable entry point: a new run, or a resume when the run folder exists |
| `selftest_10min.ps1` | 10-minute dry run (deadline, stop event, max pairs, state checks) |
| `configs/stc8.json` + `configs/stc8.csv` | the main session: 8 parameters, 8+0.08, UHO, the 22-option exe |
| `configs/selftest.json` + `configs/selftest.csv` | 2 lock parameters, 1+0.01, the lock exe |
| `o30_expose.py`, `expose22.patch` | 22 more search constants as UCI options (defaults = the lock's literals) |

## Parameter list (CSV)
`name,start,min,max,c,a` per row: `name` = a UCI spin option the engine advertises, `start` = its starting value,
`min` / `max` = the range kept by every perturbation and update, `c` = the perturbation size at the end of the run
(c_end), `a` = the learning rate at the end of the run (r_end). With N = pairs_planned, A = A_ratio * N:
c_i = c_end * N^gamma, a_i = r_end * c_end^2 * (A + N)^alpha; at pair count k: c_k = c_i / (k+1)^gamma,
a_k = a_i / (k+1+A)^alpha. Each batch plays pairs_per_batch pairs of plus = theta + c_k*delta against
minus = theta - c_k*delta (delta = +-1 per parameter, seeded by k; the same opening with both colours), R = wins - losses
of plus, and theta += a_k / c_k * R * delta (clamped). alpha 0.602, gamma 0.101, A_ratio 0.1 by default.

## Run
```
powershell -NoProfile -ExecutionPolicy Bypass -File tune_spsa.ps1 -Config configs\stc8.json -RunDir D:\o30\spsa\stc8_main -Until '2026-11-04 12:00' -Threads 2 -Cpus '0,1'
powershell -NoProfile -ExecutionPolicy Bypass -File tune_spsa.ps1 -RunDir D:\o30\spsa\stc8_main -Status
powershell -NoProfile -ExecutionPolicy Bypass -File tune_spsa.ps1 -RunDir D:\o30\spsa\stc8_main -Stop
```
The same first command resumes after a crash or a reboot (the run folder's own config / params copies are used;
only threads / cpus may change). Outputs in the run folder: `iterations.jsonl` (one fsynced record per batch: delta,
c_k, a_k / c_k, both value sets, W / L / D, terminations, theta before / after, CPU busy share), `history.csv` (theta
after every batch), `tuner.log`, `games/b<batch>_a<attempt>.{pgn,out,config.json}`.

## CPU rules built in
The tuner pins itself (Idle) to the CPU list; fastchess and every engine inherit both. Before every batch it waits
while a fastchess it did not start has an affinity overlapping its CPUs (a running gate), while free RAM < 6 GB, and
while none of its CPUs is at most `max_busy_percent` (default 80) busy over 3 s; then it plays one game per free CPU,
never more than the thread cap (8 at most). It never stops a game and never kills anything. Any other fastchess on its
CPUs counts as a gate, own sanity matches included: give those CPUs outside the tuner's list (a resume may change
`-Cpus` / `-Threads`). The busy test counts every process, own trainers included. Stopping = the deadline,
`-MaxPairs` / `-TotalPairs`, `-Stop` (a named event the tuner holds; no STOP files), or free space below the job's
floors (C: 30 GB, D: 51 GB) before a batch - the log says which; the same command resumes once space is back.

## Self-test (10 minutes)
```
powershell -NoProfile -ExecutionPolicy Bypass -File selftest_10min.ps1 -Out D:\o30\spsa\selftest_<tag> [-Cpus 1 -Threads 1]
```
Session 1 = a new run with a 5-minute deadline; session 2 = resumed and stopped with `-Stop` after 60 s; session 3 =
resumed for at most 2 pairs (3-minute deadline). Checks: every session exits 0; records = history rows; pair count and
batch numbers continue across sessions; every theta inside its range; only normal game terminations; the config /
params copies exist. Result on 2026-11-03 (`D:\o30\spsa\selftest_2`): 19 batches, 38 pairs, 3 sessions, SELFTEST PASS.
