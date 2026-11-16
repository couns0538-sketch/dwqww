# FINDINGS — seat 24 (area 4, THREADS under ThreadSanitizer), only ever added

| id | area | one sentence | file with the exact command that shows it again | NEW |
|---|---|---|---|---|
| 24-F1 | 4 | 300 random `setoption Threads`/`Hash` changes between searches (131 followed by `ucinewgame`, Threads 1/2/4/8/16 x Hash 1/4/16/64/256) give no ThreadSanitizer report, no crash and no illegal bestmove, and the planted-fault copy through the same runner is counted at 9 report blocks. | `forge-combo29/swarm/24/job2/analyse2.py` (rerun: command in REPORT_job2.md section 4) | NEW |
