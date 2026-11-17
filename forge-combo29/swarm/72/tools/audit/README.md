# Targeted audit probes

These original MIT-licensed diagnostics expose both fixed and **still-unfixed** issues.
They are not passing-regression claims and are deliberately separate from CTest.
Each can be linked against the unchanged 5.6.0, unchanged 5.7.0 or candidate core:

```sh
c++ -std=c++20 -O2 -I include tools/audit/tt_public.cpp build/libforge_core.a -pthread -o /tmp/tt-probe
/tmp/tt-probe
```

- `see_and_tt_probe.cpp`: pin SEE/quiescence and direct internal TT/rule-50 context checks.
- `material_pin.cpp`: material-changing pinned recapture; baseline qscore -363, candidate +208.
- `tt_public.cpp`: public Searcher API; warm halfmove-98 root score +574 versus cold 0.
  This remains UNFIXED in the candidate. The probe prints the mismatch; do not call it a passing test.
- `extreme_clock.cpp`: maximum signed-int clock/increment. Link with an ASan/UBSan build
  and add `-fsanitize=address,undefined -fno-omit-frame-pointer` to the compiler/linker command.
  Untouched 5.6.0 trips UBSan; the existing 5.7.0 fix and candidate pass.

A separate known UCI edge can be reproduced by sending:

```text
position fen 7k/6Q1/6K1/8/8/8/8/8 b - - 100 1
go infinite
```

Both unchanged 5.7.0 and the candidate return `bestmove 0000` after completing the
64-depth loop without a `stop` command. The ordinary nonterminal infinite/stop regression
passes; it does not cover this terminal-position behavior. This is not fixed in this experiment.
