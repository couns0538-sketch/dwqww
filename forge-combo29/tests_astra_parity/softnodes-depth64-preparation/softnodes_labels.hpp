#pragma once
#include <charconv>
#include <cstdint>
#include <sstream>
#include <string>
#include <vector>

// Keep the last exact score line whole; never splice fields from distinct lines.
struct LabelCheck {
    std::string bestmove, kind, pv_first, exact_line, error;
    int score = 0, depth = 0, soft_lines = 0, bestmove_lines = 0;
    std::uint64_t nodes = 0, x = 0;
    bool exact = false, has_nodes = false, has_depth = false, x_valid = false;
    bool any_score = false;
    int last_score_value = 0;
    std::string last_score_line;
    bool item2 = true, item3 = true, item4 = true;
};
inline bool decimal_nodes(const std::string& text, std::uint64_t& value) {
    if (text.empty() || text.find_first_not_of("0123456789") != std::string::npos) return false;
    const auto parsed = std::from_chars(text.data(), text.data()+text.size(), value);
    return parsed.ec == std::errc{} && parsed.ptr == text.data()+text.size();
}
inline LabelCheck check_labels(const std::vector<std::string>& lines, bool soft) {
    LabelCheck r;
    bool best_seen = false;
    for (const auto& line : lines) {
        std::istringstream in(line);
        std::string token;
        if (!(in >> token)) continue;
        if (token == "bestmove") {
            ++r.bestmove_lines;
            if (!(in >> r.bestmove)) r.error = "missing_bestmove";
            best_seen = true;
            continue;
        }
        if (token != "info" || !(in >> token)) continue;
        if (token == "string") {
            if (!(in >> token) || token != "softnodes") continue;
            ++r.soft_lines;
            std::string field, value, extra;
            bool valid = static_cast<bool>(in >> field >> value) && field == "nodes";
            valid = valid && decimal_nodes(value, r.x);
            if (valid) r.x_valid = true;
            if (in >> extra) valid = false;
            if (!valid || best_seen) r.item2 = false;
            continue;
        }
        std::string kind, bound, pv_first;
        int score = 0, depth = 0, multipv = 1;
        std::uint64_t nodes = 0;
        bool has_score = false, has_nodes = false, has_depth = false;
        do {
            if (token == "depth") has_depth = static_cast<bool>(in >> depth);
            else if (token == "score") {
                has_score = static_cast<bool>(in >> kind >> score) && (kind == "cp" || kind == "mate");
            } else if (token == "nodes") {
                std::string text;
                has_nodes = static_cast<bool>(in >> text) && decimal_nodes(text, nodes);
            }
            else if (token == "multipv") in >> multipv;
            else if (token == "lowerbound" || token == "upperbound") bound = token;
            else if (token == "pv") { in >> pv_first; break; }
        } while (in >> token);
        if (has_score && multipv == 1 && !best_seen) {
            r.any_score = true; r.last_score_value = score; r.last_score_line = line;
        }
        if (has_score && bound.empty() && multipv == 1) {
            if (best_seen) { r.error = "exact_score_after_bestmove"; continue; }
            r.exact = true; r.kind = kind; r.score = score; r.depth = depth;
            r.nodes = nodes; r.has_nodes = has_nodes; r.has_depth = has_depth;
            r.pv_first = pv_first; r.exact_line = line;
        }
    }
    if (r.bestmove_lines != 1) r.error = "bestmove_count";
    if (soft && (!r.exact || !r.has_nodes || !r.has_depth)) {
        if (r.error.empty()) r.error = "missing_complete_exact_score";
    }
    if (!soft && !r.any_score && r.error.empty()) r.error = "usual_score_not_observed";
    if (soft) {
        r.item2 = r.item2 && r.soft_lines == 1 && r.x_valid;
        r.item3 = r.exact && !r.pv_first.empty() && r.bestmove == r.pv_first;
        r.item4 = r.exact && r.has_nodes && (r.nodes >= 2500 || r.kind == "mate" || (r.has_depth && r.depth == 64) || (r.x_valid && r.x >= 10000));
    } else if (r.soft_lines != 0) r.error = "softnodes_line_on_usual_search";
    return r;
}
