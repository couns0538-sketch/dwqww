vacuity test for deepseek6 long56's illegal-bestmove classifier
  original runner: original_fuzzuci56.py.txt (copied VERBATIM from
                   for-fable-and-opus/deepseek6-work:forge-combo29/tests_deepseek6_long56/fuzzuci56.py)
  fake engine:     ../../planted_engine.py  (every `go` -> "bestmove a1a8", illegal for startpos)
  sequences:       ../seqs_planted.txt (2 sequences, both `position startpos` + `go depth 3`)
  command:         python3 test_runner_vacuous.py ../../planted_engine.py . ../seqs_planted.txt
  result:          planted_summary.txt = {'seqs': 0, ..., 'illegal': 0, 'ok': 2}
  -> the runner answered illegal 0 for an engine that ALWAYS answers an illegal move.
     Its illegal-bestmove check therefore never runs; "illegal bestmoves 0" is vacuous.
  also visible: 'seqs': 0 despite ok 2  (the summary's seqs key is never assigned).
