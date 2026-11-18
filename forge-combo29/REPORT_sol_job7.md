# Sol — Job 7 stopped at the source gate

1. **Step 0 met on the unchanged counting executable.** The eight fresh-process pins were defaults 312866 / 862329 / 3024920 / 4865609, S14 242796 / 656517 and PC20 278024 / 587276. This was the existing Job 4 counting build, SHA-256 `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`, with its buttons unused. A history-age copy was not built after the source gate stopped the job. [Raw commands and output](sol/job7/step0-count.raw.txt)
2. **Source statement 1 met on the ordinary root path.** The iterative-deepening setup in the Job 4 counting tree resets stack fields and the killer entries. Its assignment to `ss.continuation` sets a pointer to an existing row. It leaves the histories intact. [Verbatim source excerpts](sol/job7/source-lines.txt)

   ```text
   src/search.cpp:2677  SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_info, const std::vector<Worker*>& all) {
   src/search.cpp:2893  for (SearchStack& ss : stack_) {
   src/search.cpp:2899      ss.continuation = &(*continuation_history_)[Empty][0];
   src/search.cpp:2904      ss.killers = {};
   ```

3. **Source statement 2 fails as written.** There are two direct callers of `Worker::clear()` beyond `Searcher::clear()` and the explicit alternate MultiPV clear. One is worker construction, which includes primary workers created by `Searcher::set_threads()`. The other is the Job 4 `ClearWorkers` button. The separate bench searcher also calls `Searcher::clear()` during bench.

   ```text
   src/search.cpp:1253      clear();
   src/search.cpp:3103                  alt_worker->clear();
   src/search.cpp:3261          workers_.push_back(std::make_unique<Worker>(shared_, static_cast<int>(workers_.size())));
   src/search.cpp:3272  void Searcher::clear_workers() {
   src/search.cpp:3273      for (auto& worker : workers_) worker->clear();
   src/search.cpp:3287  void Searcher::clear() {
   src/search.cpp:3289      for (auto& worker : workers_) worker->clear();
   src/uci.cpp:390              searcher.clear();
   src/uci.cpp:436              } else if (name == "ClearWorkers") {
   src/uci.cpp:437                  if (value_text.empty()) searcher.clear_workers();
   src/uci.cpp:594                          searcher.clear();
   src/uci.cpp:605                          searcher.clear();
   src/uci.cpp:787                  bench_searcher.clear();
   ```

   Neither extra direct caller runs between searches of a game in the specified warm replay. It fixes Threads at 1 and sends the options before entering the game loop. MultiPV defaults to 1. The warm loop sends one `ucinewgame` at game start followed by position and go commands for each ply. The Job 4 button is unused. The remaining source agrees with the warm-protocol inference. The explicit gate still stops the job on the source-statement discrepancy. [Verbatim source and protocol](sol/job7/source-lines.txt)

4. **Source statement 3 met.** The update clamps the bonus and applies the gravity term. Starting inside the bounds, the update stays within `[-16384, 16384]`.

   ```text
   src/search.cpp:396  constexpr int HistoryMax = 16384;
   src/search.cpp:469  void apply_history(std::int16_t& entry, int bonus) {
   src/search.cpp:470      const int clamped = std::clamp(bonus, -HistoryMax, HistoryMax);
   src/search.cpp:471      entry = static_cast<std::int16_t>(entry + clamped - entry * std::abs(clamped) / HistoryMax);
   src/search.cpp:472  }
   ```

## Build and evidence

Case A, Codex Cloud Linux x86_64, GPT-6 (Codex). PC r15 with the Job 2 counters and Job 4 buttons. GCC 14.2.0, CMake 4.2.3 Release, libstdc++ `6.0.33`, glibc 2.41, x86-64-v4, `FORGE_MATE_ALPHA_GUARD=1`. Built-in AL1 s198 evaluation, weights source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`, no external net. The Step 0 raw file records which of defaults, S14 and PC20 was sent in each fresh process. Source line numbers are from that exact Job 4 tree. [Build record](REPORT_sol_job4.md) · [Clock stamps](sol/job7/stamps.txt)

## What I did not do

No history-age patch, copy build, Job 7 replay, bridge test, prediction commit or Block D. The history-table inventory and Stockfish comparison were left unstarted at the source gate. No engine source was changed.

## What I am not sure about

The source wording could have meant only the lifetime of an existing worker between ordinary warm searches. The current source agrees with that narrower statement.

## FOR FABLE AND OPUS

Can the source gate use the narrower statement for the fixed Threads 1, MultiPV 1 warm replay? That would explicitly allow worker construction and the unused `ClearWorkers` entry point.

## Pre-commit readback

```text
M  forge-combo29/NOTES_sol.md
AM forge-combo29/REPORT_sol_job7.md
A  forge-combo29/sol/job7/source-lines.txt
A  forge-combo29/sol/job7/stamps.txt
A  forge-combo29/sol/job7/step0-count.raw.txt
A  forge-combo29/sol/job7/step0.summary.txt
?? forge-combo29/sol/job2/__pycache__/
forge-combo29/sol/job7:
source-lines.txt
stamps.txt
step0-count.raw.txt
step0.summary.txt
```
