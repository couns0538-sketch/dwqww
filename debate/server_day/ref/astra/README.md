# Independent home rules replay

This review candidate implements the rules check in server-day stage a2 for the frozen game command
`selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8`.
It runs on the home computer with Python 3.10+ and the import `chess` version 1.11.2. Use an existing environment with that dependency. The programs use the standard library otherwise, run offline, and create their output in a new directory supplied by the caller.

From this directory, with a new working directory whose parent already exists:

```text
python -I -B test_rules.py --work-dir "path/to/new test folder"
python -I -B rules_replay.py --raw "path/to/a sealed plain piece" --root-seed SEED --work-dir "path/to/new rules folder"
```

For an explicitly frozen opening list, replace `--root-seed SEED` with `--fixed-openings FILE`. The fixed table contains one UCI move sequence per line. One-based game counter selects a line cyclically, as in the native rehearsal worker. For an independent opening the home board orders its legal moves and draws from `SHA256(root_seed|game_id|ply)`. The rules check verifies the reservation, sent position, every row and legally played move, end state, search/row/move counts and adjudication sequence. A pending draw-adjudication decision is checked for legality on the final board. A terminal search scored by the engine has a signed result but no emitted score to recompute.

The input adapter reads the ASCII/LF game envelope used by the pinned reference worker. Its bind field is framing here. The integrated receiver must separately check the decoded piece digest and every binding against its approved transport and record format. The standalone report contains rules results only. Duplicate ownership, tablebase rescoring, filtering and durable C4 belong to subsequent components. The adapter rejects an incomplete final record. A failed pass may retain a private `rules.inprogress` in the new work folder and publishes no `rules.jsonl`. An empty piece is refused. A changed game policy needs a separately qualified reference.

The frozen inputs hold 13 authentic native game records totalling 1,139 rows. The first six are the N12 workload, with row counts 86, 101, 0, 127, 81 and 67. The remaining fixtures cover mate on the eighth reserved ply, stalemate, insufficient material, the fifty-move rule, the ply limit, a one-search mate score with zero rows, and an opening ending before eight plies. Two separate seeded runs deliberately share a logical ID and differ in their independent root seed; each is a separate test. The test needs no engine, tables, system temporary directory or network. Fixture provenance includes per-record hashes and original seal hashes where available. Run the test again on the PC and measure the entire approved a2 there under its intended load. Each executable needs three exact-byte votes before day use.
