#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"

#include <charconv>
#include <iostream>
#include <string>
#include <string_view>

namespace {

struct Parts {
    int hce = 0;
    int network = 0;
    bool network_off = false;
    int sum = 0;
};

[[nodiscard]] bool parse_int(std::string_view text, int& value) {
    const char* end = text.data() + text.size();
    const auto parsed = std::from_chars(text.data(), end, value);
    return parsed.ec == std::errc{} && parsed.ptr == end;
}

[[nodiscard]] bool parse_report(std::string_view line, Parts& parts) {
    constexpr std::string_view prefix = "info string eval hce ";
    if (!line.starts_with(prefix)) return false;
    line.remove_prefix(prefix.size());
    const auto hce_end = line.find(' ');
    if (hce_end == std::string_view::npos || !parse_int(line.substr(0, hce_end), parts.hce)) return false;
    line.remove_prefix(hce_end + 1);
    constexpr std::string_view nnue = "nnue ";
    if (!line.starts_with(nnue)) return false;
    line.remove_prefix(nnue.size());
    const auto nnue_end = line.find(' ');
    if (nnue_end == std::string_view::npos) return false;
    const std::string_view nnue_text = line.substr(0, nnue_end);
    line.remove_prefix(nnue_end + 1);
    constexpr std::string_view sum = "sum ";
    if (!line.starts_with(sum)) return false;
    line.remove_prefix(sum.size());
    if (!parse_int(line, parts.sum)) return false;
    if (nnue_text == "off") {
        parts.network_off = true;
        parts.network = 0;
        return true;
    }
    parts.network_off = false;
    return parse_int(nnue_text, parts.network);
}

int fail(const std::string& why) {
    std::cerr << why << '\n';
    return 1;
}

} // namespace

int main() {
    if (!forge::nnue::available() || !forge::nnue::enabled) return fail("compiled-in network is not active");

    forge::Board board;
    const std::string start = forge::eval_report(board);
    Parts start_parts;
    if (!parse_report(start, start_parts)) return fail("unparsed startpos: " + start);
    if (start_parts.network_off) return fail("network reported off on startpos: " + start);
    if (start_parts.sum != start_parts.hce + start_parts.network) return fail("startpos sum is not hce + nnue: " + start);
    if (start_parts.hce != forge::Evaluator::evaluate_uncached(board)) return fail("startpos hce is not evaluate_uncached");
    forge::nnue::Accumulator accumulator;
    forge::nnue::refresh(board, accumulator);
    if (start_parts.network != forge::nnue::evaluate(board, accumulator)) return fail("startpos nnue is not nnue::evaluate");

    const auto move = board.parse_uci("e2e4");
    if (!move.has_value()) return fail("e2e4 did not parse");
    forge::Undo undo;
    if (!board.make_move(*move, undo)) return fail("e2e4 was rejected");
    if (board.side_to_move() != forge::Black) return fail("e2e4 did not leave Black to move");

    const std::string after = forge::eval_report(board);
    Parts after_parts;
    if (!parse_report(after, after_parts)) return fail("unparsed e2e4: " + after);
    if (after_parts.network_off) return fail("network reported off after e2e4: " + after);
    if (after_parts.sum != after_parts.hce + after_parts.network) return fail("e2e4 sum is not hce + nnue: " + after);
    if (after_parts.hce != forge::Evaluator::evaluate_uncached(board)) return fail("e2e4 hce is not evaluate_uncached");
    forge::nnue::Accumulator after_accumulator;
    forge::nnue::refresh(board, after_accumulator);
    if (after_parts.network != forge::nnue::evaluate(board, after_accumulator)) {
        return fail("e2e4 nnue is not nnue::evaluate");
    }

    forge::nnue::enabled = false;
    const std::string off = forge::eval_report(board);
    Parts off_parts;
    if (!parse_report(off, off_parts)) return fail("unparsed network-off line: " + off);
    if (!off_parts.network_off) return fail("expected nnue off: " + off);
    if (off_parts.sum != off_parts.hce) return fail("network-off sum is not the hand-written score: " + off);
    if (off_parts.hce != forge::Evaluator::evaluate_uncached(board)) return fail("network-off hce is not evaluate_uncached");
    forge::nnue::enabled = true;

    std::cout << start << '\n' << after << '\n' << off << '\n';
    return 0;
}
