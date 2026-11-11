#!/usr/bin/env python3
"""apply_halfka_guards.py - JOB D follow-up (own code, 2026-11-11). Run once from forge-combo29/ after
`git apply --reject` of patches/halfka_r10_294dbed_bb6175b.patch (the R10 HalfKA diff of opus-r10-halfka).

Places the six rejected hunks by hand and puts every HalfKA line behind FORGE_NNUE_HALFKA (default 0), so the
eight lock units still preprocess identically to the pinned lock source. Every replacement must match exactly once.
The tree is committed; this file is the record of how it was made.
"""
import io
import sys


def rd(p):
    return io.open(p, encoding='utf-8', newline='').read()


def wr(p, s):
    io.open(p, 'w', encoding='utf-8', newline='').write(s)


def rep(s, old, new, name):
    n = s.count(old)
    if n != 1:
        sys.exit(f'{name}: expected 1 match, found {n}')
    return s.replace(old, new)


G, E = '#if FORGE_NNUE_HALFKA\n', '#endif\n'

# ---- nnue.hpp: the switch
p = 'include/forge/nnue.hpp'
s = rd(p)
s = rep(s, '#ifndef FORGE_FAIR_DIAG\n#define FORGE_FAIR_DIAG 0\n#endif\n',
        '#ifndef FORGE_FAIR_DIAG\n#define FORGE_FAIR_DIAG 0\n#endif\n'
        '//   FORGE_NNUE_HALFKA 1        compiles the R10 stand-alone net path (UCI EvalFileHalfKA, forge/nnue_halfka.hpp,\n'
        '//                              src/nnue_halfka.cpp). While such a net is loaded the evaluation is the net alone.\n'
        '#ifndef FORGE_NNUE_HALFKA\n#define FORGE_NNUE_HALFKA 0\n#endif\n', 'nnue.hpp switch')
wr(p, s)

# ---- nnue_halfka.cpp: whole unit behind the switch
p = 'src/nnue_halfka.cpp'
s = rd(p)
s = rep(s, '#include "forge/nnue_halfka.hpp"\n', '#include "forge/nnue.hpp"\n' + G + '#include "forge/nnue_halfka.hpp"\n', 'halfka.cpp head')
if not s.endswith('\n'):
    s += '\n'
s += '#endif // FORGE_NNUE_HALFKA\n'
wr(p, s)

# ---- search.hpp
p = 'include/forge/search.hpp'
s = rd(p)
s = rep(s, '#include "forge/nnue_halfka.hpp"\n', G + '#include "forge/nnue_halfka.hpp"\n' + E, 'search.hpp include')
member = ('    // R10: HalfKA (K32H3^) accumulators, one entry per stack_ entry (used only while EvalFileHalfKA is loaded)\n'
          '    halfka::AccumulatorStack halfka_acc_;\n')
s = rep(s, member, G + member + E, 'search.hpp member')
decl = '    [[nodiscard]] int static_evaluate(const Board& board, SearchStack* ss);\n'
s = rep(s, decl, decl + G + '    [[nodiscard]] int halfka_evaluate(const Board& board, SearchStack* ss);\n' + E, 'search.hpp decl')
s = rep(s, '    [[nodiscard]] int diag_static_total(const Board& board, SearchStack* ss) { return static_evaluate(board, ss); }\n',
        '    [[nodiscard]] int diag_static_total(const Board& board, SearchStack* ss);\n', 'search.hpp diag total')
wr(p, s)

# ---- search.cpp
p = 'src/search.cpp'
s = rd(p)
old = ('    const bool halfka_on = halfka::active();\n'
       '    if (!halfka_on && (!nnue::enabled || !nnue::available())) return;\n')
s = rep(s, old, G + old + '#else\n    if (!nnue::enabled || !nnue::available()) return;\n' + E, 'record_move head')
old = ('    if (halfka_on) {\n'
       '        const std::size_t entry = static_cast<std::size_t>(ss + 1 - stack_.data());\n'
       '        halfka_acc_.valid[White][entry] = halfka_acc_.valid[Black][entry] = false;\n'
       '    }\n')
s = rep(s, old, G + old + E, 'record_move tail')
old = ('    if (halfka::active()) {\n'
       '        const std::size_t entry = static_cast<std::size_t>(ss + 1 - stack_.data());\n'
       '        halfka_acc_.valid[White][entry] = halfka_acc_.valid[Black][entry] = false;\n'
       '    }\n')
s = rep(s, old, G + old + E, 'record_null_move')
a = s.find('#ifdef FORGE_HALFKA_VERIFY\nnamespace {\n')
f = s.find('int Worker::halfka_evaluate(const Board& board, SearchStack* ss) {\n')
if a < 0 or f < a or s.count('int Worker::halfka_evaluate(') != 1:
    sys.exit('search.cpp: halfka_evaluate not found')
a = s.rfind('\n', 0, a) + 1
z = s.find('\n}\n', f) + len('\n}\n')
s = s[:a] + G + s[a:z] + E + s[z:]
branch = '    if (!nnue::enabled || !nnue::available()) return evaluator_.evaluate(board);\n    const bool residual = nnue::residual();\n'
s = rep(s, branch, G + '    if (halfka::active()) return halfka_evaluate(board, ss);\n' + E + branch, 'static_evaluate branch')
root = '\n    Move previous_best = Move::none();\n    int stable_iterations = 0;\n'
s = rep(s, root, G + '    if (halfka::active()) halfka_acc_.ensure(static_cast<int>(stack_.size()));\n' + E + root, 'root ensure')
old = ('Worker::DiagEval Worker::diag_static_evaluate(const Board& board, SearchStack* ss) {\n'
       '    DiagEval out;\n'
       '    out.total = static_evaluate(board, ss);\n')
new = ('int Worker::diag_static_total(const Board& board, SearchStack* ss) {\n'
       '#if FORGE_NNUE_HALFKA\n'
       '    if (halfka::active()) return diag_static_evaluate(board, ss).total;\n'
       '#endif\n'
       '    return static_evaluate(board, ss);\n'
       '}\n\n'
       'Worker::DiagEval Worker::diag_static_evaluate(const Board& board, SearchStack* ss) {\n'
       '    DiagEval out;\n'
       '#if FORGE_NNUE_HALFKA\n'
       '    if (halfka::active()) {\n'
       '        // The HalfKA rows are indexed by the position of `ss` in this worker\'s own stack, so the root entry of\n'
       '        // that stack is used here; the net is the whole evaluation (no hand-crafted term).\n'
       '        halfka_acc_.ensure(static_cast<int>(stack_.size()));\n'
       '        for (std::size_t entry = 0; entry <= 4; ++entry) halfka_acc_.valid[White][entry] = halfka_acc_.valid[Black][entry] = false;\n'
       '        out.total = static_evaluate(board, &stack_[4]);\n'
       '        out.network = out.total;\n'
       '        return out;\n'
       '    }\n'
       '#endif\n'
       '    out.total = static_evaluate(board, ss);\n')
s = rep(s, old, new, 'diag')
wr(p, s)

# ---- uci.cpp
p = 'src/uci.cpp'
s = rd(p)
s = rep(s, '#include "forge/nnue.hpp"\n', '#include "forge/nnue.hpp"\n' + G + '#include "forge/nnue_halfka.hpp"\n' + E, 'uci include')
opt = '#if FORGE_NNUE_V2\n            std::cout << "option name EvalFileV2 type string default <empty>\\n";\n#endif\n'
s = rep(s, opt, opt + G +
        '            // R10: a K32H3^ (HalfKAv2_hm family) .nnue from the nnue-pytorch trainer; empty = off (the lock\'s eval)\n'
        '            std::cout << "option name EvalFileHalfKA type string default <empty>\\n";\n' + E, 'uci option')
block = '''            } else if (name == "EvalFileHalfKA") {
                std::string rest;
                std::getline(input, rest);
                std::string path = value_text + rest;
                while (!path.empty() && (path.back() == ' ' || path.back() == '\\r')) path.pop_back();
                const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                if (path.empty() || path == "<empty>") {
                    forge::halfka::unload();
                    std::cout << "info string EvalFileHalfKA off" << std::endl;
                } else {
                    std::string error;
                    if (forge::halfka::load(path, error)) {
                        std::cout << "info string EvalFileHalfKA loaded " << forge::halfka::description() << std::endl;
                    } else {
                        forge::halfka::unload();
                        std::cout << "info string ERROR EvalFileHalfKA: " << error << " (HalfKA eval off)" << std::endl;
                    }
                }
                searcher.clear_hash();
'''
anchor = '#if FORGE_NNUE_V2\n            } else if (name == "EvalFileV2") {\n'
s = rep(s, anchor, G + block + E + anchor, 'uci setoption')
wr(p, s)
print('halfka guards applied')
