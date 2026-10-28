#!/usr/bin/env bash
# Finalise the fable-review-buffix regression fixture with the engine's own census of <fen>, build the fixed test
# (bounds-checked) and the unfixed (64-entry) mutant test, run both: the fixed one must pass, the mutant must abort.
# usage: fable_nnue_buffix_prove.sh "<fen>"
set -u
FEN=$1
B=/f/opus_scratch/fable_review/buffix64; W=/f/opus_scratch/worktrees/fable_review_buffix
export PATH=/c/msys64/ucrt64/bin:$PATH
cd "$B"
echo "# buffix proof $(date)  fen: $FEN"
# 1. census tool with promotion count (new name: the old exe may still be in use by the search)
cat > fable_census2.cpp <<'EOF'
#include "forge/board.hpp"
#include <iostream>
#include <string>
int main() {
    using namespace forge;
    std::string line;
    while (std::getline(std::cin, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty()) continue;
        Board board; std::string error;
        if (!board.set_fen(line, &error)) { std::cout << "invalid " << error << '\n'; continue; }
        const MoveList noisy = board.pseudo_legal_moves(true);
        int losing = 0, legal_losing = 0, promotions = 0;
        for (const Move move : noisy) {
            if (move.is_promotion()) ++promotions;
            if (!board.see_ge(move, 0)) { ++losing; if (board.is_legal(move)) ++legal_losing; }
        }
        std::cout << "ok " << noisy.size() << ' ' << losing << ' ' << legal_losing << ' ' << (board.in_check() ? 1 : 0) << ' ' << promotions << '\n';
    }
}
EOF
nice -n 19 g++ -std=c++20 -O2 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -static -I "$W/include" fable_census2.cpp "$W/src/board.cpp" "$W/src/bitboard.cpp" -o fable_census2.exe || { echo "census2 build failed"; exit 1; }
read -r ok noisy losing legal in_check promotions <<< "$(echo "$FEN" | ./fable_census2.exe)"
echo "engine census: $ok noisy=$noisy losing=$losing legal_losing=$legal in_check=$in_check promotions=$promotions"
[ "$ok" = ok ] && [ "$losing" -gt 64 ] && [ "$in_check" = 0 ] || { echo "position not usable"; exit 1; }
# 2. the fixture
python -I -B finalize_fixture.py "$FEN" "$noisy" "$promotions" "$losing" || exit 1
# 3. fixed build (bounds checks on) + run
bash fable_nnue_build_test.sh "$W" "$B/cmake_fixed" forge_bad_capture_tests || exit 1
nice -n 19 ./cmake_fixed/forge_bad_capture_tests.exe > final_fixed.log 2>&1; echo "fixed test exit $?" | tee -a final_fixed.log
grep -E "many-losing|accepted=|failures" final_fixed.log
# 4. mutant (64-entry) build with bounds checks + run
python -I -B make_mutant_tree.py || exit 1
bash fable_nnue_build_test.sh "$B/mutant_src" "$B/cmake_mutant" forge_bad_capture_tests || exit 1
nice -n 19 ./cmake_mutant/forge_bad_capture_tests.exe > final_mutant.log 2>&1; rc=$?; echo "mutant test exit $rc" | tee -a final_mutant.log
grep -E "many-losing|accepted=|failures|assert|Assertion|abort|out of range|operator\[\]" final_mutant.log | head -8
echo "# done $(date)"
