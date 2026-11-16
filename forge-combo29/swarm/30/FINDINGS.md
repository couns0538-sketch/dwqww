# FINDINGS — seat 30 (area 10, checking the others)

| id | area | one sentence | file with the exact command that shows it again | status |
|---|---|---|---|---|
| 30-F1 | 10 | deepseek6's long56 report claims "ZERO illegal bestmoves" but its OWN checker examines ZERO bestmoves: `pos_line` is read from the engine's OUTPUT (fuzzuci56.py:102) while the engine never prints a line starting with "position", so the whole block is skipped for all 2,000 sequences. | forge-combo29/swarm/30/job2/emulate_their_checker.py (out: emulation_out.txt) | NEW |
| 30-F2 | 10 | deepseek6's long56 raw summary contradicts its report: out/fuzz56_summary.txt holds `{'seqs': 0, ...}` (the seqs counter is never incremented) while the report states "2,000 sequences". | forge-combo29/swarm/30/job2/audit_out.txt section 1 | NEW |
| 30-F3 | 10 | deepseek6's claim "the per-sequence records are in out/" is false: out/ holds exactly two files (fuzz56_summary.txt, bad_sequences.txt) totalling 74 bytes; no per-sequence record exists. | forge-combo29/swarm/30/job2/audit_out.txt section 2 | NEW |
| 30-F4 | 10 | deepseek6's UCI fuzz has no sanitizer proof: tests_deepseek6_long56/ holds no `.meta` with an `nm __asan_` count and no planted-fault run, so its "0 sanitizer lines" is "not shown" by the brief's standard. | forge-combo29/swarm/30/job2/audit_out.txt section 3 | NEW |
| 30-F5 | 10 | The RESULT itself is true on my build: 2,000 sequences of their own generator, my own runner, my ASan+UBSan build -> 0 crashes, 0 hangs, 0 sanitizer lines, 0 illegal bestmoves out of 7,538 bestmoves actually checked (twice, identical). | forge-combo29/swarm/30/job2/out_full/summary.json and out_full_repeat/summary.json | NEW |
| 30-F6 | 10 | `ucinewgame` resets the board to the start position (src/uci.cpp:254-257), so any tester that sends `position ...` then `ucinewgame` before `go` is searching the START POSITION, not the position it set. | forge-combo29/swarm/30/job2/FACTS_job2.md F2 | NEW |
