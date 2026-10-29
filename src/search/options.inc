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
int nnue_king_buckets = 0;
int nnue_output_buckets = 0;
bool nnue_v2 = false;
int nnue_threats = 0;   // O6 (after nnue_v2 so that the variables before it keep their addresses)
int nnue_pawn_pairs = 0;   // O7
bool pure_nnue = false;   // O4 (after nnue_v2 so that the variables before it keep their addresses)
std::uint8_t corr_margins = 0;
std::uint8_t corr_ext = 0;
bool cuckoo_rep = false;
bool material_key_table = false;
bool intended_threefold = false;   // S-IT (UCI IntendedThreefold)
bool smp_helpers_past_depth = false;   // R3-6 (UCI SmpHelpersPastDepth; last, so the variables above keep their addresses)
bool r7_tt_exclusive = false;   // R7 J3 (UCI R7TtExclusive; after the others, which keep their addresses)
bool r7_quiet_gen = false;      // R7 J3 (UCI R7QuietGen)
bool r7_eval_prefetch = false;  // R7 J3 (UCI R7EvalPrefetch)

} // namespace forge::options
