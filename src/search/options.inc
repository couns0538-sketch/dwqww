// Search module: storage of the runtime options (forge/search_options.hpp).
// Compiled as part of src/search.cpp (included exactly once).
// Constant-initialised namespace-scope variables: no constructor code.

namespace forge::options {

int nnue_king_buckets = 0;
bool nnue_v2 = false;
int nnue_threats = 0;   // O6 (after nnue_v2 so that the variables before it keep their addresses)
int nnue_pawn_pairs = 0;   // O7

} // namespace forge::options
