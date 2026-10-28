// Search module: runtime search options (forge/search_options.hpp); every feature is OFF by default.
// Compiled as part of src/search.cpp (included exactly once).

namespace forge::options {

bool smp_exact_nodes = false;
bool smp_best_thread = false;
bool lockless_tt = false;
int syzygy_probe_depth = 1;
bool syzygy_50_move_rule = true;
std::uint8_t corr_hist_plus = 0;
int hard_deadline_ms = 0;
std::atomic<std::uint64_t> published_moves{0};

} // namespace forge::options
