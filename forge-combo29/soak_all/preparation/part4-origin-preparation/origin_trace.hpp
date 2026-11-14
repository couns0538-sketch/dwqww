#pragma once
// Scratch-only instrumentation. Include in the private search translation unit.
// No engine structure/layout changes, extra probes, or native oracle calls.
#include "forge/search.hpp"
#include <atomic>
#include <charconv>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string_view>

#if !FORGE_SPD_TT_NOTLS
#error "This first-pass tracer requires the pinned FORGE_SPD_TT_NOTLS=1 build."
#endif

namespace forge::origin_trace {
struct Config {
    bool enabled = false;
    std::uint64_t key = 0;
    std::uint64_t limit = 200000;
};
inline const Config& config() {
    static const Config cfg = [] {
        Config c;
        const char* text = std::getenv("FORGE_ORIGIN_KEY");
        if (!text) return c;
        auto parse = [](const char* s, std::uint64_t& value) {
            const std::string_view v(s);
            const auto r = std::from_chars(v.data(), v.data() + v.size(), value);
            return !v.empty() && r.ec == std::errc{} && r.ptr == v.data() + v.size();
        };
        if (!parse(text, c.key)) {
            std::cerr << "TRACE_ORIGIN_CONFIG_ERROR invalid_decimal_key\n";
            return c;
        }
        if (const char* cap = std::getenv("FORGE_ORIGIN_LIMIT")) {
            if (!parse(cap, c.limit) || c.limit == 0) {
                std::cerr << "TRACE_ORIGIN_CONFIG_ERROR invalid_positive_limit\n";
                return c;
            }
        }
        c.enabled = true;
        std::cerr << "TRACE_ORIGIN_CONFIG key=" << c.key << " limit=" << c.limit << '\n';
        return c;
    }();
    return cfg;
}
inline bool enabled() { return config().enabled; }
inline std::uint64_t target_key() { return config().key; }
inline std::atomic<std::uint64_t> events{0};
inline std::atomic<std::uint64_t> frames{0};
template <class Fill> inline void emit(const char* kind, Fill fill) {
    if (!enabled()) return;
    const auto seq = events.fetch_add(1, std::memory_order_relaxed) + 1;
    if (seq > config().limit) {
        if (seq == config().limit + 1) std::cerr << "TRACE_ORIGIN_TRUNCATED limit=" << config().limit << '\n';
        return;
    }
    std::ostringstream out;
    out << "TRACE_ORIGIN seq=" << seq << " kind=" << kind;
    fill(out);
    out << '\n';
    std::cerr << out.str();
}
inline std::string move_text(Move move) {
    const bool valid_shape = move.from < 64 && move.to < 64 &&
        (!move.is_promotion() || move.promotion < 7);
    const std::string label = move.is_none() ? "none" :
        (valid_shape ? Board::move_to_uci(move) : "invalid");
    return label + '(' + std::to_string(move.from) + ':' + std::to_string(move.to) + ':' +
        std::to_string(move.promotion) + ':' + std::to_string(move.flags) + ')';
}
struct Frame;
inline thread_local Frame* active = nullptr;
struct Frame {
    Frame* parent = nullptr;
    const Board& board;
    const SearchStack* stack;
    const std::uint64_t& nodes;
    std::uint64_t id = 0;
    std::uint64_t entry_key;
    std::uint64_t entry_nodes;
    int worker, root_depth, ply, entry_depth, alpha_in, beta_in, mate_mode;
    std::size_t root_index;
    bool cut;
    const char* function;
    const char* store_site = "none";
    const char* relation = "ROOT";
    Move incoming = Move::none();
    Move excluded;

    Frame(const Board& b, const SearchStack* ss, const std::uint64_t& n, int w,
          int rd, int depth, int alpha, int beta, int mate, std::size_t ri,
          bool is_cut, const char* fn)
        : board(b), stack(ss), nodes(n), entry_key(b.key()), entry_nodes(n),
          worker(w), root_depth(rd), ply(ss->ply), entry_depth(depth), alpha_in(alpha),
          beta_in(beta), mate_mode(mate), root_index(ri), cut(is_cut), function(fn),
          excluded(ss->excluded_move) {
        if (!enabled()) return;
        id = frames.fetch_add(1, std::memory_order_relaxed) + 1;
        parent = active;
        if (parent) {
            if (ply == parent->ply) relation = "SAME_PLY";
            else if (ply == parent->ply + 1) {
                incoming = parent->stack->current_move;
                relation = incoming.is_none() ? "NULL_EDGE" : "MOVE_EDGE";
            } else relation = "OTHER_PLY";
        }
        active = this;
        if (watched()) emit("FRAME_ENTER", [&](auto& out) { append(out); });
    }
    Frame(const Frame&) = delete;
    Frame& operator=(const Frame&) = delete;
    ~Frame() {
        if (!id) return;
        if (watched()) emit("FRAME_LEAVE", [&](auto& out) { append(out); });
        active = parent;
    }
    bool watched() const { return id != 0 && entry_key == target_key(); }
    void append(std::ostream& out) const {
        out << " frame=" << id << " parent=" << (parent ? parent->id : 0)
            << " fn=" << function << " worker=" << worker << " root_depth=" << root_depth
            << " ply=" << ply << " entry_depth=" << entry_depth << " alpha_in=" << alpha_in
            << " beta_in=" << beta_in << " cut=" << cut << " mate_mode=" << mate_mode
            << " key=" << entry_key << " current_key=" << board.key()
            << " entry_nodes=" << entry_nodes << " nodes_now=" << nodes
            << " root_index=" << root_index << " store_site=" << store_site
            << " entry_excluded=" << move_text(excluded) << " relation=" << relation
            << " incoming=" << move_text(incoming) << " fen=" << std::quoted(board.fen());
        out << " history=[";
        bool first = true;
        for (const auto key : board.key_history()) { if (!first) out << ','; first = false; out << key; }
        out << "] ancestry=[";
        for (const Frame* f = this; f; f = f->parent) {
            if (f != this) out << ',';
            out << f->id << ':' << f->ply << ':' << f->relation << ':' << move_text(f->incoming);
        }
        out << ']';
    }
};
inline void context(std::ostream& out) {
    if (active) active->append(out); else out << " frame=0";
}
inline void slots(std::ostream& out, const TTCluster& cluster) {
    out << " slots=[";
    for (std::size_t i = 0; i < cluster.entries.size(); ++i) {
        const TTEntry& e = cluster.entries[i];
        if (i) out << ';';
        out << i << ',' << e.key32 << ',' << e.score << ',' << e.eval << ',' << move_text(e.move)
            << ',' << static_cast<unsigned>(e.depth) << ',' << static_cast<unsigned>(e.gen_bound)
            << ',' << static_cast<unsigned>(e.rule50_clock) << ',' << e.occupied();
    }
    out << ']';
}
inline void probe_event(const char* kind, const void* table, std::uint64_t epoch,
                        unsigned generation, std::size_t index, std::uint64_t key,
                        int slot, bool hit, bool locked, const TTCluster& cluster) {
    emit(kind, [&](auto& out) {
        out << " table=" << table << " epoch=" << epoch << " generation=" << generation
            << " cluster=" << index << " requested_key=" << key << " slot=" << slot
            << " hit=" << hit << " locked_route=" << locked;
        context(out); slots(out, cluster);
    });
}
inline void store_event(const char* kind, const void* table, std::uint64_t epoch,
                        unsigned generation, std::size_t index, unsigned slot,
                        std::uint64_t key, int score, int eval, Move move, int depth,
                        Bound bound, bool pv, unsigned clock, bool locked,
                        bool admitted, const TTCluster& cluster) {
    emit(kind, [&](auto& out) {
        out << " table=" << table << " epoch=" << epoch << " generation=" << generation
            << " cluster=" << index << " slot=" << slot << " requested_key=" << key
            << " raw=" << score << " eval=" << eval << " move=" << move_text(move)
            << " depth=" << depth << " bound=" << static_cast<unsigned>(bound)
            << " pv=" << pv << " clock=" << clock << " locked_route=" << locked
            << " admitted=" << admitted;
        context(out); slots(out, cluster);
    });
}
inline void store_attempt(Frame& f, const char* site, int score, int raw, int eval,
                           Move move, int depth, Bound bound, bool pv, int alpha, int beta) {
    f.store_site = site;
    if (!f.watched()) return;
    emit("STORE_CALL", [&](auto& out) {
        f.append(out);
        out << " returned=" << score << " raw=" << raw << " eval=" << eval
            << " move=" << move_text(move) << " depth=" << depth
            << " bound=" << static_cast<unsigned>(bound) << " pv=" << pv
            << " alpha=" << alpha << " beta=" << beta;
    });
}
inline void worker_probe(Frame& f, bool hit, const TTEntry& e, int score, int alpha, int beta) {
    if (!f.watched()) return;
    emit("WORKER_PROBE", [&](auto& out) {
        f.append(out);
        out << " hit=" << hit << " raw=" << e.score << " adjusted=" << score
            << " bound=" << static_cast<unsigned>(e.bound()) << " depth=" << unsigned(e.depth)
            << " stored_clock=" << unsigned(e.rule50_clock)
            << " score_usable=" << (hit && e.score_usable(f.board.halfmove_clock()))
            << " alpha=" << alpha << " beta=" << beta;
    });
}
inline void substitution(Frame& f, int prior, int score, Bound bound, int alpha, int beta) {
    if (!f.watched()) return;
    emit("TT_SUBSTITUTION", [&](auto& out) {
        f.append(out);
        out << " prior_eval=" << prior << " adjusted=" << score
            << " bound=" << static_cast<unsigned>(bound) << " alpha=" << alpha << " beta=" << beta;
    });
}
inline int result(Frame& f, const char* reason, int value, int alpha, int beta) {
    if (f.watched()) emit("RETURN", [&](auto& out) {
        f.append(out);
        out << " reason=" << reason << " value=" << value << " alpha=" << alpha
            << " beta=" << beta << " pv_length=" << f.stack->pv_length;
    });
    return value;
}
} // namespace forge::origin_trace
