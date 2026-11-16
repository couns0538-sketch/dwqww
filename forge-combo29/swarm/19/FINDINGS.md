# FINDINGS — swarm seat 19 (area 9, SPEED)

One line per finding; only ever ADDED. Checks of other seats' findings get their own `C` line.

| id | area | finding | file with the exact command that shows it again | state |
|---|---|---|---|---|
| 19-F1 | 9 | The compiled net is a residual net (`src/nnue_weights.inc:3`), so `Worker::static_evaluate` pays both the NNUE forward pass and the whole hand-crafted term walk on every eval; the walk (`evaluate_position`, 16.51 % self) is the hottest symbol in the engine and costs more than the net (`nnue::apply_and_evaluate` 11.84 % + `nnue::update` 2.53 % = 14.37 %). | `python3 forge-combo29/swarm/19/job1/summarize.py forge-combo29/swarm/19/job1/profile` (raw: `job1/profile/perf_symbols_all.txt`) | NEW |
| 19-F2 | 9 | Inclusive cost: `qsearch` 38.44 %, `static_evaluate` 33.43 % of all search time — a third of the search is static evaluation, over a third of the tree is quiescence. | `job1/profile_cg/perf_children.txt` (rows `Worker::qsearch`, `Worker::static_evaluate`) | NEW |
| 19-F3 | 9 | Move ordering is 17.34 % self: `MovePicker::next` 6.69 %, `pick_best` 6.35 % (of which 2.00 % is `std::__introsort_loop` over `MovePicker::Scored*`), `generate_evasions` 2.26 %. | `job1/profile/perf_symbols_all.txt`, `job1/profile_cg/perf_children.txt` | NEW |
| 19-F4 | 9 | `Board::see_ge` (5.56 % self) costs nearly as much as all move generation together (`fill_pseudo_legal<0/1/2>` = 5.69 %). | table B of `forge-combo29/swarm/19/job1/summary.txt` | NEW |
| 19-F5 | 9 | Measurement trap for every seat: `bench` is a UCI command on **stdin** (`src/uci.cpp:590`; `main` at `src/uci.cpp:651` ignores argv). `perf record … -- forge bench 13` gives 468 samples of nothing useful; `printf 'bench 13\nquit\n' \| forge` gives the real `info string bench depth 13 nodes 862329`. | `printf 'quit\n' \| ~/build_rel/forge bench 13` (no output) vs `printf 'bench 13\nquit\n' \| ~/build_rel/forge` | NEW |
