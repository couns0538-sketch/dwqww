#!/usr/bin/env python3
"""Make variant source trees from the shipped one, each isolating one predicate of
TTEntry::score_usable. Patches are written to evidence/ as unified diffs so the
variant can be rebuilt from the shipped tree.

A control that silently does nothing is worse than no control (brief rule 3), so
each variant is a *removal* of exactly one conjunct, and every variant must be
shown to move a number before a clean run of the shipped build means anything.
"""
import pathlib
import re
import shutil
import subprocess
import sys

SRC = pathlib.Path(__file__).resolve().parents[3]        # forge-combo29/
OUT = pathlib.Path("/tmp/forge-variants")

SHIPPED = """    [[nodiscard]] bool score_usable(std::uint16_t current_clock) const {
        const int capped = current_clock < 100 ? static_cast<int>(current_clock) : 100;
        if (rule50_clock == capped) return true;
        if (is_mate_score(score)) {
            const int distance = MateValue - (score < 0 ? -static_cast<int>(score) : static_cast<int>(score));
            if (static_cast<int>(current_clock) + distance > 100) return false;
        }
        const int stored_clock = rule50_clock;
        const int stored_depth = depth;
        const bool inside_horizon = stored_clock + stored_depth < 100 &&
                                    static_cast<int>(current_clock) + stored_depth < 100 &&
                                    stored_clock < 90 && capped < 90;
        return inside_horizon || stored_clock == capped;
    }
"""

THRESHOLD_89 = """    [[nodiscard]] bool score_usable(std::uint16_t current_clock) const {
        const int capped = current_clock < 100 ? static_cast<int>(current_clock) : 100;
        if (rule50_clock == capped) return true;
        if (is_mate_score(score)) {
            const int distance = MateValue - (score < 0 ? -static_cast<int>(score) : static_cast<int>(score));
            if (static_cast<int>(current_clock) + distance > 100) return false;
        }
        const int stored_clock = rule50_clock;
        const int stored_depth = depth;
        const bool inside_horizon = stored_clock + stored_depth < 100 &&
                                    static_cast<int>(current_clock) + stored_depth < 100 &&
                                    stored_clock < 89 && capped < 89;
        return inside_horizon || stored_clock == capped;
    }
"""

THRESHOLD_91 = """    [[nodiscard]] bool score_usable(std::uint16_t current_clock) const {
        const int capped = current_clock < 100 ? static_cast<int>(current_clock) : 100;
        if (rule50_clock == capped) return true;
        if (is_mate_score(score)) {
            const int distance = MateValue - (score < 0 ? -static_cast<int>(score) : static_cast<int>(score));
            if (static_cast<int>(current_clock) + distance > 100) return false;
        }
        const int stored_clock = rule50_clock;
        const int stored_depth = depth;
        const bool inside_horizon = stored_clock + stored_depth < 100 &&
                                    static_cast<int>(current_clock) + stored_depth < 100 &&
                                    stored_clock < 91 && capped < 91;
        return inside_horizon || stored_clock == capped;
    }
"""

VARIANTS = {
    # 1. The guard is gone entirely: every stored score is reusable.
    "always_true": """    [[nodiscard]] bool score_usable(std::uint16_t current_clock) const {
        (void)current_clock;
        return true;
    }
""",    # 2. Keep the exact-clock short circuit and the mate test, drop the horizon test.
    "no_horizon": """    [[nodiscard]] bool score_usable(std::uint16_t current_clock) const {
        const int capped = current_clock < 100 ? static_cast<int>(current_clock) : 100;
        if (rule50_clock == capped) return true;
        if (is_mate_score(score)) {
            const int distance = MateValue - (score < 0 ? -static_cast<int>(score) : static_cast<int>(score));
            if (static_cast<int>(current_clock) + distance > 100) return false;
        }
        return true;
    }
""",
    # 3. Keep exact-clock and horizon, drop only the mate-distance test.
    "no_mate_test": """    [[nodiscard]] bool score_usable(std::uint16_t current_clock) const {
        const int capped = current_clock < 100 ? static_cast<int>(current_clock) : 100;
        if (rule50_clock == capped) return true;
        const int stored_clock = rule50_clock;
        const int stored_depth = depth;
        const bool inside_horizon = stored_clock + stored_depth < 100 &&
                                    static_cast<int>(current_clock) + stored_depth < 100 &&
                                    stored_clock < 90 && capped < 90;
        return inside_horizon || stored_clock == capped;
    }
""",
    # 4. Drop the two `< 90` clauses only: the horizon arithmetic stays.
    "no_90": """    [[nodiscard]] bool score_usable(std::uint16_t current_clock) const {
        const int capped = current_clock < 100 ? static_cast<int>(current_clock) : 100;
        if (rule50_clock == capped) return true;
        if (is_mate_score(score)) {
            const int distance = MateValue - (score < 0 ? -static_cast<int>(score) : static_cast<int>(score));
            if (static_cast<int>(current_clock) + distance > 100) return false;
        }
        const int stored_clock = rule50_clock;
        const int stored_depth = depth;
        const bool inside_horizon = stored_clock + stored_depth < 100 &&
                                    static_cast<int>(current_clock) + stored_depth < 100;
        return inside_horizon || stored_clock == capped;
    }
""",
    # 5. Trace build: counts each branch's verdict without changing any decision.
    "trace": """    [[nodiscard]] bool score_usable(std::uint16_t current_clock) const {
        const int capped = current_clock < 100 ? static_cast<int>(current_clock) : 100;
        if (rule50_clock == capped) {
            if (is_mate_score(score)) {
                const int d = MateValue - (score < 0 ? -static_cast<int>(score) : static_cast<int>(score));
                if (static_cast<int>(current_clock) + d > 100) ++forge::detail::tt_trace_exact_mate_far;
            }
            ++forge::detail::tt_trace_exact;
            return true;
        }
        if (is_mate_score(score)) {
            const int distance = MateValue - (score < 0 ? -static_cast<int>(score) : static_cast<int>(score));
            if (static_cast<int>(current_clock) + distance > 100) { ++forge::detail::tt_trace_mate; return false; }
        }
        const int stored_clock = rule50_clock;
        const int stored_depth = depth;
        const bool inside_horizon = stored_clock + stored_depth < 100 &&
                                    static_cast<int>(current_clock) + stored_depth < 100 &&
                                    stored_clock < 90 && capped < 90;
        if (inside_horizon || stored_clock == capped) { ++forge::detail::tt_trace_inside; return true; }
        ++forge::detail::tt_trace_outside;
        return false;
    }
""",
    # 6/7. The 90 threshold moved by one in each direction, everything else equal.
    "thr89": THRESHOLD_89,
    "thr91": THRESHOLD_91,
}

TRACE_DECL = """
namespace detail {
inline unsigned long long tt_trace_exact = 0;
inline unsigned long long tt_trace_exact_mate_far = 0;
inline unsigned long long tt_trace_mate = 0;
inline unsigned long long tt_trace_inside = 0;
inline unsigned long long tt_trace_outside = 0;
inline unsigned long long tt_trace_store = 0;
inline unsigned long long tt_trace_store_hi = 0;
inline unsigned long long tt_trace_depth_max = 0;
struct TtTraceReset {
    TtTraceReset() {
        tt_trace_exact = tt_trace_exact_mate_far = tt_trace_mate = 0;
        tt_trace_inside = tt_trace_outside = 0;
        tt_trace_store = tt_trace_store_hi = tt_trace_depth_max = 0;
    }
};
}  // namespace detail
"""

# The 90 threshold moved by one in each direction. Everything else is the shipped
# body, so a difference between thr89/thr91 and the shipped build is attributable
# to the constant and nothing else. This is the only way to answer "why 90 and not
# 89 or 91" with a measurement instead of a reading of the arithmetic.


def patch_tree(name, body, hpp_text):
    dst = OUT / name
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Only what CMakeLists.txt globs: src/ plus include/. The tree's other
    # directories are evidence from earlier seats and total several gigabytes.
    dst.mkdir(parents=True)
    (dst / "src").mkdir()
    shutil.copytree(SRC / "include", dst / "include")
    for f in (SRC / "src").glob("*"):
        if f.is_file():
            shutil.copy2(f, dst / "src" / f.name)
    shutil.copy2(SRC / "CMakeLists.txt", dst / "CMakeLists.txt")
    hpp = dst / "include/forge/search.hpp"
    text = hpp.read_text()
    if SHIPPED not in text:
        raise SystemExit(f"{name}: shipped score_usable not found verbatim")
    new = text.replace(SHIPPED, body)
    if name == "trace":
        new = new.replace("struct TTEntry {", TRACE_DECL + "\nstruct TTEntry {", 1)
        cpp = dst / "src/search.cpp"
        c = cpp.read_text()
        # Count accepted stores, so "the bail stored nothing" can be shown by a
        # counter that is proven to move on a search that does store.
        store_anchor = "    const bool same_position = entry->key32 == key32 && entry->occupied();"
        if store_anchor not in c:
            raise SystemExit("trace: store anchor not found in search.cpp")
        c = c.replace(store_anchor,
                      "    const bool same_position = entry->key32 == key32 && entry->occupied();\n"
                      "    ++forge::detail::tt_trace_store;\n"
                      "    if (halfmove_clock >= 90) ++forge::detail::tt_trace_store_hi;\n"
                      "    if (depth > static_cast<int>(forge::detail::tt_trace_depth_max))\n"
                      "        forge::detail::tt_trace_depth_max = static_cast<unsigned long long>(depth);",
                      1)
        # print the counters once per search, on the main worker
        anchor = "        result.nodes = total_nodes();\n        if (alt_worker"
        if anchor not in c:
            raise SystemExit("trace: anchor not found in search.cpp")
        trace_print = (
            "        {\n"
            "            std::cout << \"info string tt_trace exact \" << forge::detail::tt_trace_exact\n"
            "                      << \" exact_mate_far \" << forge::detail::tt_trace_exact_mate_far\n"
            "                      << \" mate \" << forge::detail::tt_trace_mate\n"
            "                      << \" inside \" << forge::detail::tt_trace_inside\n"
            "                      << \" outside \" << forge::detail::tt_trace_outside\n"
            "                      << \" stores \" << forge::detail::tt_trace_store\n"
            "                      << \" stores_hi \" << forge::detail::tt_trace_store_hi\n"
            "                      << \" depthmax \" << forge::detail::tt_trace_depth_max << std::endl;\n"
            "        }\n"
        )
        inject = (
            "        result.nodes = total_nodes();\n"
            + trace_print +
            "        if (alt_worker"
        )
        c = c.replace(anchor, inject, 1)
        # The drawn-root bail returns before that point, so it needs its own print
        # or a bail is indistinguishable from "the counters were never installed".
        bail_anchor = "        result.nodes = total_nodes();\n        nodes_.store(local_nodes_, std::memory_order_relaxed);"
        if bail_anchor not in c:
            raise SystemExit("trace: bail anchor not found in search.cpp")
        c = c.replace(bail_anchor,
                      "        result.nodes = total_nodes();\n" + trace_print +
                      "        nodes_.store(local_nodes_, std::memory_order_relaxed);",
                      1)
        # The counters are per-search: reset where the table is aged.
        reset_anchor = "    shared_.tt.new_search();"
        if reset_anchor not in c:
            raise SystemExit("trace: new_search anchor not found")
        c = c.replace(reset_anchor,
                      "    shared_.tt.new_search();\n"
                      "    forge::detail::TtTraceReset trace_reset;",
                      1)
        cpp.write_text(c)
    hpp.write_text(new)
    return dst


def build(dst):
    env = {"LIBRARY_PATH": "/usr/lib/gcc/x86_64-linux-gnu/13", "PATH": "/usr/bin:/bin:/usr/local/bin"}
    bd = dst / "build"
    r = subprocess.run(["cmake", "-S", str(dst), "-B", str(bd), "-DCMAKE_BUILD_TYPE=Release",
                        "-DCMAKE_CXX_COMPILER=/usr/bin/g++", "-DFORGE_MARCH=x86-64-v4"],
                       capture_output=True, text=True, env=env)
    if r.returncode:
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit("cmake failed")
    r = subprocess.run(["cmake", "--build", str(bd), "-j4"], capture_output=True, text=True, env=env)
    if r.returncode:
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit("build failed")
    return bd / "forge"


if __name__ == "__main__":
    only = sys.argv[1:] or list(VARIANTS)
    for name in only:
        dst = patch_tree(name, VARIANTS[name], None)
        exe = build(dst)
        print(f"{name:14} {exe}")
