#!/usr/bin/env python3
"""job13 Part B: plant the rule counters (candidates/gap classes/deeper/shallower/skip) in a copy of PATCHED."""
path = "/tmp/ds5_lmr_cnt/src/search.cpp"
t = open(path, encoding="utf-8").read()

first = t.index("namespace forge {")
decls = (
"namespace forge {\n"
"// job13 Part B: rule counters (candidates and the gap classes), cumulative; printed per search.\n"
"long long jc_candidates[5] = {0, 0, 0, 0, 0};\n"
"long long jc_deeper[5] = {0, 0, 0, 0, 0};\n"
"long long jc_shal_fire[5] = {0, 0, 0, 0, 0};\n"
"long long jc_shal_reran[5] = {0, 0, 0, 0, 0};\n"
"long long jc_shal_skip[5] = {0, 0, 0, 0, 0};\n"
)
t = t[:first] + decls + t[first + len("namespace forge {\n"):]

old_rule = """            if (full_depth_needed) {
                if (tune::LmrDeeperShallower) {
                    const bool do_deeper =
                        score > best_score + tune::LmrDeeperBase + tune::LmrDeeperDepthMul * new_depth;
                    const bool do_shallower =
                        score < best_score + tune::LmrShallowerBase + tune::LmrShallowerDepthMul * new_depth;
                    new_depth += static_cast<int>(do_deeper) - static_cast<int>(do_shallower);
                }"""
new_rule = """            if (full_depth_needed) {
                if (tune::LmrDeeperShallower) {
                    const bool do_deeper =
                        score > best_score + tune::LmrDeeperBase + tune::LmrDeeperDepthMul * new_depth;
                    const bool do_shallower =
                        score < best_score + tune::LmrShallowerBase + tune::LmrShallowerDepthMul * new_depth;
                    {
                        const int gap = alpha - best_score;
                        const int cls = gap <= 0 ? 0 : gap <= 50 ? 1 : gap <= 300 ? 2 : gap <= 3000 ? 3 : 4;
                        ++jc_candidates[cls];
                        if (do_deeper) ++jc_deeper[cls];
                        if (do_shallower) {
                            ++jc_shal_fire[cls];
                            const int nd2 = new_depth + static_cast<int>(do_deeper) - static_cast<int>(do_shallower);
                            if (reduced_depth < nd2) ++jc_shal_reran[cls]; else ++jc_shal_skip[cls];
                        }
                    }
                    new_depth += static_cast<int>(do_deeper) - static_cast<int>(do_shallower);
                }"""
assert old_rule in t, "the rule block not found"
t = t.replace(old_rule, new_rule, 1)

# print the counters at the end of every top-level search (before `return result;` in Searcher::search)
anchor = "    for (auto& helper : helpers) helper.join();"
i = t.index(anchor)
j = t.index("\n", i) + 1
print_line = ('    { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());\n'
              '      std::cout << "info string JC cand";\n'
              '      for (int k = 0; k < 5; ++k) std::cout << " " << jc_candidates[k];\n'
              '      std::cout << " deeper";\n'
              '      for (int k = 0; k < 5; ++k) std::cout << " " << jc_deeper[k];\n'
              '      std::cout << " sfire";\n'
              '      for (int k = 0; k < 5; ++k) std::cout << " " << jc_shal_fire[k];\n'
              '      std::cout << " sreran";\n'
              '      for (int k = 0; k < 5; ++k) std::cout << " " << jc_shal_reran[k];\n'
              '      std::cout << " sskip";\n'
              '      for (int k = 0; k < 5; ++k) std::cout << " " << jc_shal_skip[k];\n'
              '      std::cout << std::endl; }\n')
t = t[:j] + print_line + t[j:]
open(path, "w").write(t)
print("counters planted")
