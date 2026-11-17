# Independent review of same-clock admission

Reviewed 2026-11-15 UTC. Read-only review; no engine executed, no source, Git or root-state change.

Source commit: `d9a8587df8ad4d0ff1231632cb1ac72b590c04bf` in `/workspace/work/dwqww-parity`. Request: retained `FABLE_ANSWER_0011.md.txt`, Step 2 and its nine-row table.

The source change conforms exactly to the requested scope. The existing capped-clock declaration moves to the start of `TTEntry::score_usable`; equality with the stored clock returns true immediately. The mate check and horizon body remain byte-for-byte unchanged. The source/CMake comparison against `c488e88fddc71a7ceadddb15270d3f62f6add8d9` names only `forge-combo29/include/forge/search.hpp`. The commit contains two added lines and one removed line, all inside this function. The pre-existing adjacent comment is now stale about the equal-clock mate exception; leaving it untouched follows the explicit one-function scope and is not a logic defect.

Let `eq = rule50_clock == min(current_clock,100)` and `rejected_mate = is_mate_score(score) && current_clock + (MateValue - abs(score)) > 100`, using the function's actual integer arithmetic. The old function returns false for `rejected_mate`, otherwise `inside_horizon || eq`. The new function returns true for `eq`, otherwise runs the old body. Therefore its Boolean result changes **if and only if `eq && rejected_mate`**, and that change is false to true. Cross-clock results are unchanged. An equal-clock ordinary score was already accepted; unit row 6 is a preservation check, while row 5 exercises newly admitted behavior. Both signs of a mate score follow the same arithmetic; this review is not an additional executable test of negative mates or clocks above 100.

`same_clock_table.cpp` exactly encodes all nine requested rows with values that fit their stored types. It calls the real function and returns nonzero on any mismatch. The existing zero-initialized bound field is irrelevant to this isolated function's contract. The retained before-edit output and after-edit output are consistent with the requested change: row 5 alone changes; expected values remain fixed.

`same_clock_position.cpp` uses a fresh UCI process, explicit Threads 1 / Hash 16 / OwnBook false, `ucinewgame`, the exact requested FEN and depth 9. Its retained actual transcript ends with an unbounded exact score `mate -5`, nodes `2566746`, bestmove `a1b2`, and normal exit with no forced signals. The assertion matches the requested score/node tuple. The raw run therefore supports the reported result.

Two non-blocking harness limitations should remain explicit: the Boolean assertion does not require `score_bound.empty()`, and does not reject nonempty engine stderr/diagnostic text. The observed transcript is exact and clean, so these omissions do not invalidate this run. For future reuse, adding those assertions to this new test would tighten it without changing any expected value. It is not an independent legality or mate-proof test; that is outside the requested tuple check and belongs to the corpus oracle or existing mate suites.

For each second-corpus difference, the minimum defensible attribution record is:

1. Preserve its original and ten fresh final/reference pairs, complete FEN, options, depth, move, score kind/value/bound, node counts, binary/source hashes and normal-exit status. Keep root-clock-under-80 cases explicitly listed.
2. Retrieve the exact same FEN's Step 1 record showing `c488...` equals the frozen reference; verify the selected corpus index/FEN rather than relying on approximate position matching. The final source change is only the proven predicate above, with the same compiler and build settings.
3. Directly compare the already-frozen Step 1 binary against the final binary on each differing FEN if stronger reproducibility confirmation is needed. This separates the one-function change from the three previously verified imports without another production edit or broad rebuild.
4. If the requirement is interpreted as needing an observed TT entry, use one private diagnostic copy only: record the first `eq && rejected_mate` admission (stored/read clocks, score, distance, depth, key and bound), then verify its final search tuple still matches the uninstrumented final binary. Do not change the published production tree or count diagnostic searches toward the original corpus. This is a proposed check, not a check performed by this reviewer.

The source proof and exact Step 1/Step 2 differential establish the narrow causal candidate. They do not by themselves prove the chess-theoretic truth of an admitted mate score, or prove that every visited TT entry was safe for every history. No such broader claim is warranted.

Commands actually inspected: `git show --format=fuller --stat --patch d9a8587... -- forge-combo29/include/forge/search.hpp`; `git diff c488... d9a8587... --name-only -- forge-combo29/src forge-combo29/include forge-combo29/CMakeLists.txt`; the two new C++ test files; the retained answer0011; the score helper/call sites and UCI transport parser; and `logs/same-clock-position-step2.stdout.txt`. No native experiment was added.
