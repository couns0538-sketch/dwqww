| id | area/check | one sentence | file with the command that shows it again | state |
|---|---|---|---|---|
| S-F1 | area 3 job 1 | Engine and python-chess agree on perft 1..4 for all 5,000 seed-1301 R positions (20,000 pairs, 0 differences). | job1/comparison.md ; `cd forge-combo29/swarm/13/job1 && python3 compare.py raw_engine.txt raw_ref.txt R_1301.fens /tmp/o.md && grep TOTAL /tmp/o.md` | NEW |
