// Search module: UCI "info" output. One line per completed (or revised)
// iteration, written by the emit lambda of the iterative-deepening driver
// (src/search/iterative.inc) under uci_output_mutex():
//   info depth D seldepth S score (cp X | mate M) nodes N nps R hashfull H time T pv m1 m2 ...
// Compiled as part of src/search.cpp (included exactly once).

namespace forge {
namespace {

std::string format_score(int score) {
    if (is_mate_score(score)) {
        const int distance = MateValue - std::abs(score);
        const int mate = (distance + 1) / 2;
        return "mate " + std::to_string(score > 0 ? mate : -mate);
    }
    return "cp " + std::to_string(score);
}

} // namespace
} // namespace forge
