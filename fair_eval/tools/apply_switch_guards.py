#!/usr/bin/env python3
"""apply_switch_guards.py - JOB D (own code, 2026-11-11). Run once from forge-combo29/ after
`git apply` of int8_vnni_after_w6.patch and of the v2 port diff (D:\\o30\\repos\\v2root fe0da8d..9037f2a).

It puts every v2 line behind FORGE_NNUE_V2, adds FORGE_NNUE_INT8_DEFAULT / FORGE_NNUE_V2_HOT and the
FORGE_FAIR_DIAG commands. Every replacement must match exactly once, otherwise the script stops without
writing the file it was working on. Kept in the branch as the record of how the tree was made; the tree
itself is committed, so nobody has to run this again.
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


# ---- nnue.hpp
p = 'include/forge/nnue.hpp'
s = rd(p)
s = rep(s, '#ifndef FORGE_NNUE_INT8_VNNI\n#define FORGE_NNUE_INT8_VNNI 0\n#endif\n',
        '''#ifndef FORGE_NNUE_INT8_VNNI
#define FORGE_NNUE_INT8_VNNI 0
#endif

// JOB D build switches (fair_eval/build_fair.ps1). All default 0 = the lock code, nothing of them compiled.
//   FORGE_NNUE_INT8_DEFAULT 1  the int8 path is on at start (the UCI option's default follows it)
//   FORGE_NNUE_V2 1            compiles the v2 net path (UCI EvalFileV2, forge/nnue_v2.hpp)
//   FORGE_NNUE_V2_HOT 1        the v2 evaluation is this build's main path: no cold section / noinline / unlikely
//   FORGE_FAIR_DIAG 1          diagnostic UCI commands evalfens / evalbench (never in a measured exe)
#ifndef FORGE_NNUE_INT8_DEFAULT
#define FORGE_NNUE_INT8_DEFAULT 0
#endif
#ifndef FORGE_NNUE_V2
#define FORGE_NNUE_V2 0
#endif
#ifndef FORGE_NNUE_V2_HOT
#define FORGE_NNUE_V2_HOT 0
#endif
#ifndef FORGE_FAIR_DIAG
#define FORGE_FAIR_DIAG 0
#endif
''', 'nnue.hpp switches')
wr(p, s)

# ---- nnue.cpp
p = 'src/nnue.cpp'
s = rd(p)
s = rep(s, '#include "forge/nnue.hpp"\n#include "forge/nnue_v2.hpp"\n',
        '#include "forge/nnue.hpp"\n#if FORGE_NNUE_V2\n#include "forge/nnue_v2.hpp"\n#endif\n', 'nnue.cpp include')
s = rep(s, 'bool int8_vnni = false;', 'bool int8_vnni = FORGE_NNUE_INT8_DEFAULT != 0;', 'nnue.cpp int8 default')
marker = ('// ---------------------------------------------------------------------------\n'
          '// v2 networks (forge/nnue_v2.hpp): loading, all cold.')
s = rep(s, marker, '#if FORGE_NNUE_V2\n' + marker, 'nnue.cpp v2 block start')
if not s.endswith('} // namespace forge::nnue::v2\n'):
    sys.exit('nnue.cpp: unexpected end ' + repr(s[-60:]))
s += '#endif // FORGE_NNUE_V2\n'
wr(p, s)

# ---- search.hpp
p = 'include/forge/search.hpp'
s = rd(p)
s = rep(s,
        '    // v2 net path (UCI EvalFileV2, forge/nnue_v2.hpp); called only while a v2 net is active.\n'
        '    [[nodiscard]] int static_evaluate_v2(const Board& board, SearchStack* ss);\n',
        '#if FORGE_NNUE_V2\n'
        '    // v2 net path (UCI EvalFileV2, forge/nnue_v2.hpp); called only while a v2 net is active.\n'
        '    [[nodiscard]] int static_evaluate_v2(const Board& board, SearchStack* ss);\n'
        '#endif\n', 'search.hpp v2 decl')
s = rep(s, '    [[nodiscard]] bool is_main() const { return id_ == 0; }\n',
        '''    [[nodiscard]] bool is_main() const { return id_ == 0; }
#if FORGE_FAIR_DIAG
    // JOB D diagnostics (never in a measured exe). `ss` is a caller-owned stack entry with ply 0 whose neighbours
    // are invalid, so static_evaluate takes the search's own root path (refresh, then evaluate).
    struct DiagEval { int total = 0; int network = 0; int hce = 0; int kernel_ok = -1; };
    [[nodiscard]] DiagEval diag_static_evaluate(const Board& board, SearchStack* ss);
    [[nodiscard]] int diag_static_total(const Board& board, SearchStack* ss) { return static_evaluate(board, ss); }
#endif
''', 'search.hpp diag decl')
wr(p, s)

# ---- search.cpp
p = 'src/search.cpp'
s = rd(p)
s = rep(s, '#include "forge/search.hpp"\n#include "forge/nnue_v2.hpp"\n',
        '#include "forge/search.hpp"\n#if FORGE_NNUE_V2\n#include "forge/nnue_v2.hpp"\n#endif\n', 'search.cpp include')
s = rep(s, '// Static evaluation with a v2 network (UCI EvalFileV2; forge/nnue_v2.hpp).',
        '#if FORGE_NNUE_V2\n// Static evaluation with a v2 network (UCI EvalFileV2; forge/nnue_v2.hpp).',
        'search.cpp v2 fn start')
sig = ('__attribute__((section(".text.forge_v2"), noinline)) int Worker::static_evaluate_v2'
       '(const Board& board, SearchStack* ss) {\n')
s = rep(s, sig,
        '#if FORGE_NNUE_V2_HOT\nint Worker::static_evaluate_v2(const Board& board, SearchStack* ss) {\n#else\n'
        + sig + '#endif\n', 'search.cpp v2 attr')
s = rep(s,
        '\nint Worker::static_evaluate(const Board& board, SearchStack* ss) {\n'
        '    if (nnue::v2::active_net != nullptr) [[unlikely]] return static_evaluate_v2(board, ss);\n',
        '''#endif // FORGE_NNUE_V2

int Worker::static_evaluate(const Board& board, SearchStack* ss) {
#if FORGE_NNUE_V2
#if FORGE_NNUE_V2_HOT
    if (nnue::v2::active_net != nullptr) return static_evaluate_v2(board, ss);
#else
    if (nnue::v2::active_net != nullptr) [[unlikely]] return static_evaluate_v2(board, ss);
#endif
#endif
''', 'search.cpp branch')
old_root = '''    if (nnue::v2::active_net == nullptr && nnue::enabled && nnue::available()) {
        nnue::refresh(board, ss->accumulator);
        if (nnue::residual()) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
    } else if (nnue::v2::active_net != nullptr && nnue::enabled) [[unlikely]] {'''
if s.count(old_root) != 1:
    sys.exit('search.cpp root block not found')
i = s.find(old_root)
j = s.find('    }\n', s.find('(void)static_evaluate_v2(board, ss);', i)) + len('    }\n')
s = (s[:i] + '#if FORGE_NNUE_V2\n' + s[i:j] + '#else\n'
     '    if (nnue::enabled && nnue::available()) {\n'
     '        nnue::refresh(board, ss->accumulator);\n'
     '        if (nnue::residual()) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);\n'
     '    }\n#endif\n' + s[j:])
anchor = ('    return std::clamp(evaluator_.evaluate_runtime(board, ss->runtime_psqt) + network, '
          '-MateInMaxPly + 1, MateInMaxPly - 1);\n}\n')
k = s.rfind(anchor)
if k < 0:
    sys.exit('search.cpp static_evaluate end not found')
k += len(anchor)
diag = '''
#if FORGE_FAIR_DIAG
// JOB D diagnostic: the total is static_evaluate itself; the two terms are recomputed from the state it left.
Worker::DiagEval Worker::diag_static_evaluate(const Board& board, SearchStack* ss) {
    DiagEval out;
    out.total = static_evaluate(board, ss);
#if FORGE_NNUE_V2
    if (const nnue::v2::Net* net = nnue::v2::active(); net != nullptr && nnue::enabled) {
        out.network = nnue::v2::evaluate(*net, board, ss->accumulator);
        out.hce = net->residual ? evaluator_.evaluate_runtime(board, ss->runtime_psqt) : 0;
        return out;
    }
#endif
    if (!nnue::enabled || !nnue::available()) {
        out.hce = out.total;
        return out;
    }
    out.network = nnue::evaluate(board, ss->accumulator);
    out.hce = nnue::residual() ? evaluator_.evaluate_runtime(board, ss->runtime_psqt) : 0;
#if FORGE_NNUE_INT8_VNNI
    if (nnue::int8_vnni) {
        out.kernel_ok = nnue::int8_l1_sum(board, ss->accumulator) == nnue::int8_l1_sum_scalar(board, ss->accumulator) ? 1 : 0;
    }
#endif
    return out;
}
#endif
'''
s = s[:k] + diag + s[k:]
wr(p, s)

# ---- uci.cpp
p = 'src/uci.cpp'
s = rd(p)
s = rep(s, '#include "forge/nnue.hpp"\n#include "forge/nnue_v2.hpp"\n',
        '#include "forge/nnue.hpp"\n#if FORGE_NNUE_V2\n#include "forge/nnue_v2.hpp"\n#endif\n', 'uci include')
s = rep(s, '#include <condition_variable>\n',
        '#include <condition_variable>\n#if FORGE_FAIR_DIAG\n#include <cstdlib>\n#include <fstream>\n#include <memory>\n#endif\n',
        'uci diag includes')
s = rep(s,
        '            if (forge::nnue::available()) std::cout << "option name UseNNUE type check default true\\n";\n',
        '            if (forge::nnue::available()) std::cout << "option name UseNNUE type check default true\\n";\n'
        '#if FORGE_NNUE_V2\n'
        '            std::cout << "option name EvalFileV2 type string default <empty>\\n";\n'
        '#endif\n', 'uci v2 option')
s = rep(s, 'std::cout << "option name NnueInt8Vnni type spin default 0 min 0 max 1\\n";',
        'std::cout << "option name NnueInt8Vnni type spin default " << (FORGE_NNUE_INT8_DEFAULT ? 1 : 0) << " min 0 max 1\\n";',
        'uci int8 default')
a = s.find('            } else if (name == "EvalFileV2") {\n')
b = s.find('            } else if (name == "UseNNUE") {\n')
if a < 0 or b < a:
    sys.exit('uci EvalFileV2 block not found')
s = s[:a] + '#if FORGE_NNUE_V2\n' + s[a:b] + '#endif\n' + s[b:]
diagcmd = r'''#if FORGE_FAIR_DIAG
        } else if (command == "evalfens" || command == "evalbench") {
            // JOB D diagnostics (never in a measured exe); paths without spaces.
            //   evalfens <fen file> <out file>  one line per readable FEN: line index, total, network, hce, kernel_ok
            //                                   (the static evaluation as the search computes it at a root, in
            //                                   centipawns from the side to move; kernel_ok: int8 kernel == scalar,
            //                                   -1 = not the int8 path)
            //   evalbench <fen file> <reps>     nanoseconds per static evaluation: `root` = refresh + evaluate on
            //                                   every position, `warm` = evaluate again on a valid accumulator
            stop_search();
            std::string path, second;
            input >> path >> second;
            std::ifstream fen_file(path);
            std::vector<forge::Board> boards;
            std::vector<std::size_t> index;
            std::size_t lines = 0, bad = 0;
            for (std::string line; std::getline(fen_file, line);) {
                while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
                if (line.empty()) continue;
                forge::Board fen_board;
                if (fen_board.set_fen(line)) {
                    boards.push_back(fen_board);
                    index.push_back(lines);
                } else {
                    ++bad;
                }
                ++lines;
            }
            auto stack = std::make_unique<std::array<forge::SearchStack, 8>>();
            for (int i = 0; i < 8; ++i) (*stack)[static_cast<std::size_t>(i)].ply = i - 4;
            forge::SearchStack* ss = &(*stack)[4];
            const auto reset = [&stack] {
                for (forge::SearchStack& entry : *stack) {
                    entry.accumulator.valid = false;
                    entry.runtime_psqt.valid = false;
                }
            };
            forge::Worker& worker = searcher.main_worker();
            const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
            if (command == "evalfens") {
                std::ofstream out(second, std::ios::binary);
                std::size_t kernel_bad = 0;
                for (std::size_t i = 0; i < boards.size(); ++i) {
                    reset();
                    const forge::Worker::DiagEval e = worker.diag_static_evaluate(boards[i], ss);
                    if (e.kernel_ok == 0) ++kernel_bad;
                    out << index[i] << '\t' << e.total << '\t' << e.network << '\t' << e.hce << '\t' << e.kernel_ok << '\n';
                }
                out.flush();
                std::cout << "info string evalfens lines " << lines << " evaluated " << boards.size() << " bad " << bad
                          << " kernel_mismatch " << kernel_bad << " written " << (out.good() ? 1 : 0) << std::endl;
            } else {
                const int reps = std::max(1, std::atoi(second.c_str()));
                long long sum_root = 0, sum_warm = 0;
                const auto t0 = std::chrono::steady_clock::now();
                for (int r = 0; r < reps; ++r) {
                    for (const forge::Board& b : boards) {
                        reset();
                        sum_root += worker.diag_static_total(b, ss);
                    }
                }
                const auto t1 = std::chrono::steady_clock::now();
                for (const forge::Board& b : boards) {
                    reset();
                    sum_warm += worker.diag_static_total(b, ss);
                    for (int r = 0; r < reps; ++r) sum_warm += worker.diag_static_total(b, ss);
                }
                const auto t2 = std::chrono::steady_clock::now();
                const double n_root = static_cast<double>(boards.size()) * reps;
                const double n_warm = static_cast<double>(boards.size()) * (reps + 1);
                const double ns_root = std::chrono::duration<double, std::nano>(t1 - t0).count() / std::max(1.0, n_root);
                const double ns_warm = std::chrono::duration<double, std::nano>(t2 - t1).count() / std::max(1.0, n_warm);
                std::cout << "info string evalbench positions " << boards.size() << " reps " << reps << " root_ns " << ns_root
                          << " warm_incl_one_refresh_ns " << ns_warm << " sum_root " << sum_root << " sum_warm " << sum_warm
                          << std::endl;
            }
#endif
'''
s = rep(s, '        } else if (command == "bench") {\n', diagcmd + '        } else if (command == "bench") {\n', 'uci diag cmd')
wr(p, s)
print('guards applied')
