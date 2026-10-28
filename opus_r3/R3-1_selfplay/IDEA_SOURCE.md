# R3-1 self-play checker — ideas and sources

- **Requirement** (user, R3-1 test line): "each option ON alone and all ON together: no crash, no illegal move,
  no double bestmove over 500 fast self-games with an illegal-move checker". Commands, openings, ending rules,
  parallelism and the per-config preflight follow the coordinator's brief for this job.
- **UCI protocol** (S. Meyer-Kahlen, UCI specification, April 2006): exactly one `bestmove` answers each `go`;
  `go infinite` and `go ponder` must not answer before `stop` / `ponderhit`; `isready` must be answered at once,
  also while searching, without stopping the search; `ponderhit` turns the ponder search into a normal one;
  `stop` after a ponder miss gets a bestmove the GUI ignores; `info` keys (depth, seldepth, time, nodes, pv,
  multipv, score cp|mate [lowerbound|upperbound], currmove, currmovenumber, hashfull, nps, tbhits, cpuload,
  string, wdl).
- **Barrier after `position`**: Forge's UCI loop joins the previous search thread (and the HardDeadline watchdog's
  claim on that search) before it handles `position` (`stop_search()` in src/uci.cpp), so `isready` -> `readyok`
  after every `position` is a clean fence: any second or unsolicited bestmove of the previous search must show up
  before that readyok. The HardDeadline single-answer claim (`SearchRun::answered`) is what the hard_deadline10
  and all-ON configs exercise under load.
- **Legality**: python-chess 1.11.2 (venv) checks every bestmove, ponder move, currmove and pv move from the
  root. Ponder emulation without a second thread: a ponder hit is `go ponder` on the real position + `ponderhit`
  (identical to the engine's view of a correct prediction); a ponder miss is `go ponder` on another legal
  opponent move + `stop`, the answer checked in that position.
- **Fault injection** (harness self-test): the planted-bug practice of forge-engine-verify applied to the checker
  itself: a proxy that breaks the protocol once per fault (illegal bestmove/ponder/pv/currmove, double, late and
  unsolicited bestmove, early answer to infinite, hang, crash, bad exit status, malformed info, stderr, missing
  readyok, error string, missing option, rejected move, late search output).
- **Existing repo tools** (read for ideas, not reused): `tools/uci_regression.py`, `tools/ponder_regression.py`,
  `tools/hard_deadline_regression.py` (C3: watchdog races with single short searches); this job adds full games
  with every option and switch.
- **Nets**: function-preserving lock replicas from `tools/nnue/forge_nnue_v2.py` (C4 r1/rm8, C5 identical heads,
  O6/O7 zero threat / pawn-pair blocks); PureNnue uses O4's material-trained stand-alone smoke net
  (`F:\opus_scratch\o4\r4\o4_cpu_material\epoch004-step000000780.fnn2`, fnv1a 1544ea643b9cd9a7, opus_round1/O4/
  REPORT.md) and, for the all-ON PureNnue variant, the same function written as rm8 + 8 heads + zero threat and
  pawn-pair blocks (bench d11/d13 450072/1280779 = O4's pins for that net).
- **Profile output** (S08fix `Profile=true`): src/profile.cpp `write_snapshot` format, checked line by line
  (schema line, then one counter line per counter, same layout every time; "pct unknown" only with 0
  opportunities or overflow).
