import shutil, os
root = '<repo>/'
for d in ('src', 'include'):
    if os.path.exists(d):
        shutil.rmtree(d)
    shutil.copytree(root + d, d)
p = 'src/search/evaluation_v2.inc'
s = open(p, newline='').read()
s = s.replace('namespace forge {\n\nFORGE_SEARCH_V2 int Worker::static_evaluate_v2', r'''#include <cstdio>
namespace forge { namespace stat { long long evals, invalid, fullref, replays, plies, key_changes;
struct Dump { ~Dump() { std::fprintf(stderr, "evals %lld invalid %lld fullref %lld replays %lld plies %lld key_changes %lld refresh_calls %lld diff_terms %lld\n", evals, invalid, fullref, replays, plies, key_changes, nnue::v2::stat_refresh_calls, nnue::v2::stat_diff_terms); } } dump; } }
namespace forge {

FORGE_SEARCH_V2 int Worker::static_evaluate_v2''', 1)
s = s.replace('    const nnue::v2::Net& net = *active;\n', '    const nnue::v2::Net& net = *active;\n    ++stat::evals;\n', 1)
s = s.replace('        int back = 0;\n', '        ++stat::invalid;\n        int back = 0;\n', 1)
s = s.replace('            nnue::v2::RefreshCache& cache = nnue::v2::cache(net, id_);\n            const nnue::v2::Pieces pieces',
              '            ++stat::fullref;\n            nnue::v2::RefreshCache& cache = nnue::v2::cache(net, id_);\n            const nnue::v2::Pieces pieces', 1)
s = s.replace('            for (int i = back; i >= 0; --i) {\n', '            ++stat::replays; stat::plies += back + 1;\n            for (int i = back; i >= 0; --i) {\n', 1)
s = s.replace('                            key[c] = moved;\n', '                            key[c] = moved; ++stat::key_changes;\n', 1)
open(p, 'w', newline='').write(s)
p = 'include/forge/nnue_v2.hpp'
s = open(p, newline='').read()
s = s.replace('namespace forge::nnue::v2 {\n', 'namespace forge::nnue::v2 {\ninline long long stat_refresh_calls = 0, stat_diff_terms = 0;\n', 1)
s = s.replace('    constexpr int Chunk = 64;\n', '    ++stat_refresh_calls; stat_diff_terms += subs + adds;\n    constexpr int Chunk = 64;\n', 1)
open(p, 'w', newline='').write(s)
print('ok')
