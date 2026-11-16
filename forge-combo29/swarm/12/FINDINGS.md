# FINDINGS — swarm seat 12 (area 2: UCI commands under ASan + UBSan)

One line per finding, only ever added. `file` is in this folder; the `again:` part is the exact
command that shows it once more.

| id | area | one sentence | file with the exact command that shows it again | status |
|---|---|---|---|---|
| S-C1 | CONFIRMS S-F2 (seat 06) | an unreachable/structurally impossible ep square is REFUSED with `info string invalid FEN: inconsistent en-passant square`, and the engine keeps the previous position; but a legitimate post-double-push ep square with no capturer is ACCEPTED, so the rule is "no pawn beside it", not "unreachable" | check1/FINDING.md, raw check1/out_release.txt + check1/out_asan.txt; again: `python3 forge-combo29/swarm/12/check1/check.py ~/build/release/forge forge-combo29/swarm/12/check1/cases.txt /tmp/o.txt` | NEW |
