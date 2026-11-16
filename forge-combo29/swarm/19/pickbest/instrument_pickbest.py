"""instrument_pickbest.py : scratch-only counters inside MovePicker::pick_best and its callers.

Counts, for one run:
  P_CALLS        every call to pick_best()
  P_SEEDED       calls that returned the pre-computed seed (the cheap "previous good move" path)
  P_PARTIAL      calls that took the partial-selection branch (index_ - list_start_ < 4)
  P_SORT         calls that took the std::sort branch
  P_SCANNED      total candidate elements compared across the partial-selection loops
  P_ROOT         calls reached from the root (ss_ == nullptr or ss_->ply == 0)
  N_SCORE        calls to QuietScorer::score (the history/scalar scoring, to test whether it belongs to
                 pick_best at all)
Prints them on stderr at exit. Nothing here is committed as a patch; it is a measurement build.
"""

p = "src/search.cpp"
s = open(p).read()

# counters, at file scope inside namespace forge
s = s.replace("""class MovePicker {""",
"""struct PickBestCounters {
    std::uint64_t calls = 0, seeded = 0, partial = 0, sort = 0, scanned = 0, root = 0, score = 0;
};
inline PickBestCounters& pick_counters() {
    static PickBestCounters c;
    return c;
}

class MovePicker {""", 1)

# count the call and the branch taken
s = s.replace("""    [[nodiscard]] Move pick_best() {
        if (!sorted_) {
            if (index_ - list_start_ < 4) {
                if (seeded_ && index_ == list_start_) {""",
"""    [[nodiscard]] Move pick_best() {
        PickBestCounters& pc = pick_counters();
        ++pc.calls;
        if (ss_ == nullptr || ss_->ply == 0) ++pc.root;
        if (!sorted_) {
            if (index_ - list_start_ < 4) {
                ++pc.partial;
                if (seeded_ && index_ == list_start_) {
                    ++pc.seeded;""", 1)

# count scanned elements: the loop advances i from index_+1 to n
s = s.replace("""                for (; i < n; ++i) {
                    const int score = moves_[i].score;
                    if (score > best_score) {
                        best_score = score;
                        best = i;
                    }
                }""",
"""                pc.scanned += (n - (index_ + 1));
                for (; i < n; ++i) {
                    const int score = moves_[i].score;
                    if (score > best_score) {
                        best_score = score;
                        best = i;
                    }
                }""", 1)

s = s.replace("""            } else {
                std::sort(moves_.begin() + static_cast<std::ptrdiff_t>(index_),""",
"""            } else {
                ++pc.sort;
                std::sort(moves_.begin() + static_cast<std::ptrdiff_t>(index_),""", 1)

# count QuietScorer::score calls
s = s.replace("""        [[nodiscard]] int score(Move move, const std::array<Bitboard, 7>& check_squares) const {
            const Piece piece = board.piece_at(move.from);""",
"""        [[nodiscard]] int score(Move move, const std::array<Bitboard, 7>& check_squares) const {
            ++pick_counters().score;
            const Piece piece = board.piece_at(move.from);""", 1)

s = s.replace("#include <algorithm>", "#include <algorithm>\n#include <cstdio>", 1)

s += """
namespace forge {
void dump_pick_counters() {
    const PickBestCounters& c = pick_counters();
    std::fprintf(stderr,
                 "PICKBEST calls=%llu seeded=%llu partial=%llu sort=%llu scanned=%llu root=%llu quiet_score=%llu\\n",
                 (unsigned long long)c.calls, (unsigned long long)c.seeded,
                 (unsigned long long)c.partial, (unsigned long long)c.sort,
                 (unsigned long long)c.scanned, (unsigned long long)c.root,
                 (unsigned long long)c.score);
}
} // namespace forge
"""
open(p, "w").write(s)

# the picker sits in an anonymous namespace, so QuietScorer needs the counter visible: move the struct out
print("instrument_pickbest applied")
