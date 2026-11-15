#!/usr/bin/env python3
# Apply the CorrMargin feature to one engine tree (job 6). Edit set:
#   1. tune int CorrMargin = 0 (default off) + extern + parameters() table entry
#   2. SearchStack::corr_size beside static_eval
#   3. corrected_eval gains int* corr_size_out = nullptr; sets abs(correction / CorrectionGrain)
#   4. every static_eval assignment site records corr_size (0 where ValueNone)
#   5. RFP margin and quiet-futility margin grow by corr_size * CorrMargin / 64 (0 when off)
# Traced mode adds P1 counters (RFP histogram + cutoff/skip counters) printed at exit.
import re
import sys

def patch_search_hpp(text, traced=False):
    # stack field beside static_eval
    text = text.replace("    int static_eval = ValueNone;\n",
                        "    int static_eval = ValueNone;\n    int corr_size = 0;  // |correction| in centipawns behind static_eval (CorrMargin)\n", 1)
    # extern beside RfpMargin's extern
    text = text.replace("extern int RfpMargin;\n",
                        "extern int RfpMargin;\nextern int CorrMargin;  // correction-size widening of prune margins (0 = off; else K of size*K/64)\n", 1)
    # corrected_eval declaration gains the out-param
    text = re.sub(r"\[\[nodiscard\]\] int corrected_eval\(const Board& board, int raw_eval\) const;",
                  "[[nodiscard]] int corrected_eval(const Board& board, int raw_eval, int* corr_size_out = nullptr) const;",
                  text)
    return text

def patch_search_cpp(text, traced=False):
    # tune int definition after RfpImproving
    text = text.replace("int RfpImproving = 40;\n",
                        "int RfpImproving = 40;\nint CorrMargin = 0;\n", 1)
    # parameters() table entry next to RfpMargin's
    text = text.replace('{"RfpImproving", &RfpImproving, 0, 200},',
                        '{"RfpImproving", &RfpImproving, 0, 200},         {"CorrMargin", &CorrMargin, 0, 64},', 1)
    # corrected_eval body: out-param + size record
    text = text.replace(
        "int Worker::corrected_eval(const Board& board, int raw_eval) const {",
        "int Worker::corrected_eval(const Board& board, int raw_eval, int* corr_size_out) const {", 1)
    text = text.replace(
        "    return std::clamp(raw_eval + correction / CorrectionGrain, -MateInMaxPly + 1, MateInMaxPly - 1);\n}",
        "    if (corr_size_out != nullptr) *corr_size_out = std::abs(correction / CorrectionGrain);\n"
        "    return std::clamp(raw_eval + correction / CorrectionGrain, -MateInMaxPly + 1, MateInMaxPly - 1);\n}", 1)
    # static_eval sites: recorded through corrected_eval's out-param; zeroed where ValueNone
    n_value_none = 0
    def zero_at_value_none(m):
        nonlocal n_value_none
        n_value_none += 1
        return m.group(0) + "\n        ss->corr_size = 0;"
    # search in-check site (ss->static_eval = ss->raw_eval = ValueNone;) and qsearch's (= ValueNone;)
    text = re.sub(r"ss->static_eval = ss->raw_eval = ValueNone;", zero_at_value_none, text)
    text = re.sub(r"ss->static_eval = ValueNone;", zero_at_value_none, text)
    # the two corrected_eval call sites that define static_eval
    text = text.replace("eval = ss->static_eval = corrected_eval(board, ss->raw_eval);",
                        "eval = ss->static_eval = corrected_eval(board, ss->raw_eval, &ss->corr_size);")
    # any other static_eval = ValueNone spellings (e.g. ss.static_eval on a reference)
    text = text.replace("ss.static_eval = ValueNone;", "ss.static_eval = ValueNone;\n        ss.corr_size = 0;")
    # RFP margin. Plain: grow the margin inside the condition (works on both trees).
    # Traced: replace the WHOLE if-statement with a same-tree counting block.
    rfp_cond = r"eval - \(tune::RfpMargin \* depth - tune::RfpImproving \* improving\) >= beta &&\n(\s+)eval < MateInMaxPly\) \{\n\s+return eval;\n\s+\}"
    m = re.search(r"if \((!bare_king_mode && )?depth <= tune::RfpDepth && " + re.escape("eval - (tune::RfpMargin * depth - tune::RfpImproving * improving)"), text)
    assert m, "RFP site not found"
    if not traced:
        old_rfp = "depth <= tune::RfpDepth && eval - (tune::RfpMargin * depth - tune::RfpImproving * improving) >= beta &&"
        new_rfp = ("depth <= tune::RfpDepth && eval - (tune::RfpMargin * depth - tune::RfpImproving * improving + "
                   "ss->corr_size * tune::CorrMargin / 64) >= beta &&")
        assert old_rfp in text, "RFP plain form not found"
        text = text.replace(old_rfp, new_rfp, 1)
    else:
        prefix = m.group(1) or ""
        stmt = re.search(r"if \(" + re.escape(prefix) + r"depth <= tune::RfpDepth && " + rfp_cond, text)
        assert stmt, "RFP full statement not found"
        indent = "        "
        block = (
            f"if ({prefix}depth <= tune::RfpDepth) {{\n"
            f"{indent}    ++tune::rfp_tested;\n"
            f"{indent}    ++tune::rfp_hist[tune::bucket_of(ss->corr_size)];\n"
            f"{indent}    const int corr_term = ss->corr_size * tune::CorrMargin / 64;\n"
            f"{indent}    if (eval - (tune::RfpMargin * depth - tune::RfpImproving * improving) >= beta && eval < MateInMaxPly) ++tune::rfp_off_cut;\n"
            f"{indent}    if (eval - (tune::RfpMargin * depth - tune::RfpImproving * improving + corr_term) >= beta && eval < MateInMaxPly) {{\n"
            f"{indent}        ++tune::rfp_cutoff;\n"
            f"{indent}        return eval;\n"
            f"{indent}    }}\n"
            f"{indent}}}"
        )
        text = text[:stmt.start()] + block + text[stmt.end():]
    # quiet futility margin
    old_fut = "ss->static_eval + tune::FutilityBase + tune::FutilityMultiplier * lmr_depth <= alpha"
    assert old_fut in text, "futility site not found"
    new_fut = ("ss->static_eval + tune::FutilityBase + tune::FutilityMultiplier * lmr_depth + "
               "ss->corr_size * tune::CorrMargin / 64 <= alpha")
    text = text.replace(old_fut, new_fut, 1)
    if traced:
        # count quiet futility skips on the same tree: OFF-margin decision vs actual skip
        old_fut_blk = (
            "                if (!in_check && lmr_depth <= tune::FutilityDepth &&\n"
            "                    " + new_fut + ") {\n"
            "                    skip_quiets = true;\n"
            "                    continue;\n"
            "                }")
        new_fut_blk = (
            "                if (!in_check && lmr_depth <= tune::FutilityDepth) {\n"
            "                    if (ss->static_eval + tune::FutilityBase + tune::FutilityMultiplier * lmr_depth <= alpha) ++tune::fut_off_skip;\n"
            "                    if (" + new_fut + ") {\n"
            "                        ++tune::fut_skips;\n"
            "                        skip_quiets = true;\n"
            "                        continue;\n"
            "                    }\n"
            "                }")
        assert old_fut_blk in text, "futility traced block not found"
        text = text.replace(old_fut_blk, new_fut_blk, 1)
        # counters + atexit dump
        text = text.replace("int CorrMargin = 0;\n",
            "int CorrMargin = 0;\n"
            "// P1 trace counters (job 6, traced copy only): same-tree OFF-vs-K decisions\n"
            "static long rfp_tested = 0, rfp_cutoff = 0, fut_skips = 0, rfp_off_cut = 0, fut_off_skip = 0;\n"
            "static long rfp_hist[5] = {0, 0, 0, 0, 0};\n"
            "static int bucket_of(int size) { return size == 0 ? 0 : size <= 4 ? 1 : size <= 15 ? 2 : size <= 40 ? 3 : 4; }\n"
            "struct CorrTraceDump { ~CorrTraceDump() { std::fprintf(stderr, \"TRACE rfp_tested %ld rfp_off_cut %ld rfp_cutoff %ld fut_off_skip %ld fut_skips %ld hist %ld %ld %ld %ld %ld\\n\", rfp_tested, rfp_off_cut, rfp_cutoff, fut_off_skip, fut_skips, rfp_hist[0], rfp_hist[1], rfp_hist[2], rfp_hist[3], rfp_hist[4]); } };\n"
            "static CorrTraceDump corr_trace_dump_instance;\n", 1)
        if "#include <cstdio>" not in text:
            text = text.replace("#include <algorithm>", "#include <algorithm>\n#include <cstdio>", 1)
    return text

def patch_uci(text, traced=False):
    # declare the spin option in the uci reply, before the Clear Hash line (both trees)
    anchor_decl = '            std::cout << "option name Clear Hash type button\\n"'
    assert anchor_decl in text, "uci declare anchor not found"
    text = text.replace(anchor_decl,
        '            std::cout << "option name CorrMargin type spin default 0 min 0 max 64\\n";\n' + anchor_decl, 1)
    # set branch before the Hash branch in the setoption ladder (both trees)
    anchor_set = '} else if (name == "Hash") {'
    assert anchor_set in text, "uci set anchor not found"
    branch = (
        '} else if (name == "CorrMargin") {\n'
        '                int value = 0;\n'
        '                const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);\n'
        '                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {\n'
        '                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());\n'
        '                    std::cout << "info string invalid value for option " << name << std::endl;\n'
        '                } else {\n'
        '                    forge::tune::CorrMargin = std::clamp(value, 0, 64);\n'
        '                }\n'
        '            ')
    text = text.replace(anchor_set, branch + anchor_set, 1)
    return text

def main():
    root, traced = sys.argv[1], len(sys.argv) > 2 and sys.argv[2] == "traced"
    hpp_path = f"{root}/include/forge/search.hpp"
    cpp_path = f"{root}/src/search.cpp"
    uci_path = f"{root}/src/uci.cpp"
    hpp = open(hpp_path, encoding="utf-8").read()
    cpp = open(cpp_path, encoding="utf-8").read()
    uci = open(uci_path, encoding="utf-8").read()
    hpp2 = patch_search_hpp(hpp, traced)
    cpp2 = patch_search_cpp(cpp, traced)
    uci2 = patch_uci(uci, traced)
    open(hpp_path, "w", encoding="utf-8").write(hpp2)
    open(cpp_path, "w", encoding="utf-8").write(cpp2)
    open(uci_path, "w", encoding="utf-8").write(uci2)
    print("patched", root, "traced" if traced else "plain")

if __name__ == "__main__":
    main()
