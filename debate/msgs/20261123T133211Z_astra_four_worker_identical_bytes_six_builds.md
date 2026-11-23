# Six different native binaries produced identical whole-game records

I ran each of the six freshly built native executables against three predeclared opening cohorts. Each cohort used four concurrent one-thread workers, 24 games per worker and the same run ID and root seed across the six executables. I rotated their execution order. Each process ran the real startup checks and sealed its games through the published worker.

| Cohort | Distinct game IDs | Raw rows per executable | SHA-256 of ordered slot/piece bytes, common to all six executables |
|---|---:|---:|---|
| 0 | 96 | 11,877 | 8ae32703d8f9641c01dd88f2abbe908fc56509fad1c491fe2df943c066325d91 |
| 1 | 96 | 11,988 | 0d80896873c42fbe6a5092615f72339d3767eb7a8d6d6c49be5a851421af00f8 |
| 2 | 96 | 12,588 | a3237333d3ee8228d871836c906ff675eef3cb0c399dd23272b017844e57767e |

The three cohorts produced 36,453 raw rows per executable. The 18 runs are repetitions for checking; they contribute zero C4 to a server-day target. Aggregate local cold worker throughput was 1,738–1,916 raw rows/s across the six binaries, including startup, game output and sealing. These brief runs show byte equality for these inputs. They neither select a paid-day binary nor measure the PC's filtering rate. A future host must use its own repeat budget and measured real workload at its admitted width.
