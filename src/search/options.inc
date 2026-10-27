// Search module: runtime search options (forge/search_options.hpp), all OFF.
// Compiled as part of src/search.cpp (included exactly once).

namespace forge::options {

int hard_deadline_ms = 0;
std::atomic<std::uint64_t> published_moves{0};

} // namespace forge::options
