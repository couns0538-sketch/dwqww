#!/usr/bin/env python3
"""R3-6: build the source tree of the SMP diagnostic ("trace") engine.

Copies <tree>/src and <tree>/include to <out> and inserts counters guarded by
FORGE_SMP_TRACE (so even the copy compiles to the normal engine without -DFORGE_SMP_TRACE=1).
The engine sources of the branch are not touched: the trace build exists only in scratch.

With -DFORGE_SMP_TRACE=1 every `go` that prints info lines also prints, after the search:
  info string smptrace search threads <n> main_done_us <t> joined_us <t> join_latency_us <t>
  info string smptrace worker <i> entry_us <t> exit_us <t> cpu_us <t> nodes <n> tt_probes <n> tt_hits <n>
      tt_cutoffs <n> aborted_depth <d> iters <depth>:<us>:<nodes>:<researches>,...
Times are microseconds since Searcher::search was entered; cpu_us is the worker thread's CPU time
(user + kernel) between its entry and exit (Windows: GetThreadTimes, ~15.6 ms granularity); iters lists every completed
iteration of that worker (its own node count when the iteration completed, and how many
aspiration re-searches it needed).

usage: make_trace_src.py <tree> <out>     (<out> must not exist)
"""
import shutil
import sys
from pathlib import Path


def patch(path, old, new, count=1):
    text = path.read_bytes().decode("utf-8")
    found = text.count(old)
    if found != count:
        raise SystemExit(f"{path}: pattern found {found} times, expected {count}:\n{old}")
    path.write_bytes(text.replace(old, new).encode("utf-8"))


def main():
    tree, out = Path(sys.argv[1]), Path(sys.argv[2])
    if out.exists():
        raise SystemExit(f"{out} exists (use a fresh folder)")
    out.mkdir(parents=True)
    shutil.copytree(tree / "src", out / "src")
    shutil.copytree(tree / "include", out / "include")

    # Per-worker trace state (last members of ThreadData: nothing above moves).
    patch(out / "include/forge/thread_data.hpp",
          "    std::array<hist_rework::LesserThreats, MaxPly + 8> threat_maps_{};\n",
          "    std::array<hist_rework::LesserThreats, MaxPly + 8> threat_maps_{};\n"
          "#ifdef FORGE_SMP_TRACE\n"
          "    struct SmpTraceIter { int depth; std::int64_t at_us; std::uint64_t nodes; int researches; };\n"
          "    std::vector<SmpTraceIter> smp_iters_;\n"
          "    std::chrono::steady_clock::time_point smp_entry_{};\n"
          "    std::chrono::steady_clock::time_point smp_exit_{};\n"
          "    int smp_aborted_depth_ = 0;\n"
          "    std::uint64_t smp_tt_probes_ = 0;\n"
          "    std::uint64_t smp_tt_hits_ = 0;\n"
          "    std::uint64_t smp_tt_cutoffs_ = 0;\n"
          "    std::int64_t smp_cpu_entry_us_ = 0;\n"
          "    std::int64_t smp_cpu_exit_us_ = 0;\n"
          "#endif\n")
    # CPU time of the calling thread (defined at the end of search.cpp, after <windows.h>).
    patch(out / "include/forge/thread_data.hpp",
          "namespace forge {\n\nstruct SearchStack {",
          "namespace forge {\n\n"
          "#ifdef FORGE_SMP_TRACE\n"
          "std::int64_t smp_thread_cpu_us();\n"
          "#endif\n\n"
          "struct SearchStack {")
    with open(out / "src/search.cpp", "ab") as fh:
        fh.write(b"\n#ifdef FORGE_SMP_TRACE\n"
                 b"// R3-6 trace build: CPU time of the calling thread in microseconds.\n"
                 b"#if !defined(_WIN32)\n#include <time.h>\n#endif\n"
                 b"namespace forge {\n"
                 b"std::int64_t smp_thread_cpu_us() {\n"
                 b"#if defined(_WIN32)\n"
                 b"    FILETIME c, e, k, u;\n"
                 b"    if (!GetThreadTimes(GetCurrentThread(), &c, &e, &k, &u)) return -1;\n"
                 b"    auto v = [](const FILETIME& f) {\n"
                 b"        return static_cast<std::int64_t>((static_cast<std::uint64_t>(f.dwHighDateTime) << 32U) | f.dwLowDateTime);\n"
                 b"    };\n"
                 b"    return (v(k) + v(u)) / 10;\n"
                 b"#else\n"
                 b"    timespec ts{};\n"
                 b"    clock_gettime(CLOCK_THREAD_CPUTIME_ID, &ts);\n"
                 b"    return static_cast<std::int64_t>(ts.tv_sec) * 1000000 + ts.tv_nsec / 1000;\n"
                 b"#endif\n"
                 b"}\n"
                 b"} // namespace forge\n"
                 b"#endif\n")

    # Public print hook on Worker.
    patch(out / "include/forge/search.hpp",
          "    void end_search() { all_workers_ = nullptr; }\n",
          "    void end_search() { all_workers_ = nullptr; }\n"
          "#ifdef FORGE_SMP_TRACE\n"
          "    void smp_trace_print(std::chrono::steady_clock::time_point origin) const;\n"
          "#endif\n")

    it = out / "src/search/iterative.inc"
    patch(it,
          "    local_nodes_ = 0;\n    nodes_.store(0, std::memory_order_relaxed);\n    all_workers_ = &all;\n",
          "    local_nodes_ = 0;\n    nodes_.store(0, std::memory_order_relaxed);\n    all_workers_ = &all;\n"
          "#ifdef FORGE_SMP_TRACE\n"
          "    smp_iters_.clear();\n"
          "    smp_entry_ = smp_exit_ = std::chrono::steady_clock::now();\n"
          "    smp_aborted_depth_ = 0;\n"
          "    smp_tt_probes_ = smp_tt_hits_ = smp_tt_cutoffs_ = 0;\n"
          "    smp_cpu_entry_us_ = smp_cpu_exit_us_ = smp_thread_cpu_us();\n"
          "#endif\n")
    patch(it,
          "        int iteration_score = score;\n        while (true) {\n            ss->ply = 0;\n",
          "        int iteration_score = score;\n"
          "#ifdef FORGE_SMP_TRACE\n"
          "        int smp_researches = -1;\n"
          "#endif\n"
          "        while (true) {\n"
          "#ifdef FORGE_SMP_TRACE\n"
          "            ++smp_researches;\n"
          "#endif\n"
          "            ss->ply = 0;\n")
    patch(it,
          "        if (aborted_) {\n            // A partially searched iteration",
          "        if (aborted_) {\n"
          "#ifdef FORGE_SMP_TRACE\n"
          "            smp_aborted_depth_ = depth;\n"
          "#endif\n"
          "            // A partially searched iteration")
    # Every completed iteration (also those past a depth limit, UCI SmpHelpersPastDepth).
    patch(it,
          "        score = iteration_score;\n",
          "        score = iteration_score;\n"
          "#ifdef FORGE_SMP_TRACE\n"
          "        smp_iters_.push_back({depth, std::chrono::duration_cast<std::chrono::microseconds>(\n"
          "            std::chrono::steady_clock::now() - smp_entry_).count(), local_nodes_, smp_researches});\n"
          "#endif\n")
    patch(it,
          "    nodes_.store(local_nodes_, std::memory_order_relaxed);\n    result.nodes = total_nodes();\n"
          "    result.seldepth = std::max(result.seldepth, seldepth_);\n",
          "#ifdef FORGE_SMP_TRACE\n"
          "    smp_exit_ = std::chrono::steady_clock::now();\n"
          "    smp_cpu_exit_us_ = smp_thread_cpu_us();\n"
          "#endif\n"
          "    nodes_.store(local_nodes_, std::memory_order_relaxed);\n    result.nodes = total_nodes();\n"
          "    result.seldepth = std::max(result.seldepth, seldepth_);\n")

    # TT probe / hit / cutoff counters (every search and qsearch instance).
    cut = ("         (tt_bound == BoundUpper && tt_score <= alpha))) {\n        return tt_score;\n    }\n")
    cut_new = ("         (tt_bound == BoundUpper && tt_score <= alpha))) {\n"
               "#ifdef FORGE_SMP_TRACE\n        ++smp_tt_cutoffs_;\n#endif\n"
               "        return tt_score;\n    }\n")
    hit = "    const bool tt_hit = tt_probe.hit;\n"
    hit_new = hit + "#ifdef FORGE_SMP_TRACE\n    ++smp_tt_probes_;\n    smp_tt_hits_ += tt_hit ? 1U : 0U;\n#endif\n"
    for name in ("alphabeta.inc", "qsearch.inc"):
        patch(out / "src/search" / name, cut, cut_new)
        patch(out / "src/search" / name, hit, hit_new)

    se = out / "src/search/searcher.inc"
    patch(se,
          "SearchInfo Searcher::search(Board board, const SearchLimits& limits, bool emit_info, TTAccess table_access) {\n",
          "#ifdef FORGE_SMP_TRACE\n"
          "void Worker::smp_trace_print(std::chrono::steady_clock::time_point origin) const {\n"
          "    auto us = [origin](std::chrono::steady_clock::time_point t) {\n"
          "        return std::chrono::duration_cast<std::chrono::microseconds>(t - origin).count();\n"
          "    };\n"
          "    std::cout << \"info string smptrace worker \" << id_ << \" entry_us \" << us(smp_entry_) << \" exit_us \"\n"
          "              << us(smp_exit_) << \" cpu_us \" << smp_cpu_exit_us_ - smp_cpu_entry_us_\n"
          "              << \" nodes \" << local_nodes_ << \" tt_probes \" << smp_tt_probes_\n"
          "              << \" tt_hits \" << smp_tt_hits_ << \" tt_cutoffs \" << smp_tt_cutoffs_ << \" aborted_depth \"\n"
          "              << smp_aborted_depth_ << \" iters \";\n"
          "    const std::int64_t shift = us(smp_entry_);\n"
          "    for (std::size_t i = 0; i < smp_iters_.size(); ++i) {\n"
          "        const auto& e = smp_iters_[i];\n"
          "        std::cout << (i ? \",\" : \"\") << e.depth << ':' << e.at_us + shift << ':' << e.nodes << ':' << e.researches;\n"
          "    }\n"
          "    std::cout << '\\n';\n"
          "}\n"
          "#endif\n\n"
          "SearchInfo Searcher::search(Board board, const SearchLimits& limits, bool emit_info, TTAccess table_access) {\n"
          "#ifdef FORGE_SMP_TRACE\n"
          "    const auto smp_t0 = std::chrono::steady_clock::now();\n"
          "#endif\n")
    patch(se,
          "    SearchInfo result = workers_.front()->search(board, worker_limits, emit_info, all);\n",
          "    SearchInfo result = workers_.front()->search(board, worker_limits, emit_info, all);\n"
          "#ifdef FORGE_SMP_TRACE\n"
          "    const auto smp_main_done = std::chrono::steady_clock::now();\n"
          "#endif\n")
    patch(se,
          "    for (auto& helper : helpers) helper.join();\n",
          "    for (auto& helper : helpers) helper.join();\n"
          "#ifdef FORGE_SMP_TRACE\n"
          "    const auto smp_joined = std::chrono::steady_clock::now();\n"
          "#endif\n")
    patch(se,
          "        if (options::smp_best_thread) select_best_thread(result, helper_results, emit_info);\n"
          "    }\n",
          "        if (options::smp_best_thread) select_best_thread(result, helper_results, emit_info);\n"
          "    }\n"
          "#ifdef FORGE_SMP_TRACE\n"
          "    if (emit_info) {\n"
          "        auto us = [smp_t0](std::chrono::steady_clock::time_point t) {\n"
          "            return std::chrono::duration_cast<std::chrono::microseconds>(t - smp_t0).count();\n"
          "        };\n"
          "        const std::lock_guard<std::mutex> output_lock(uci_output_mutex());\n"
          "        std::cout << \"info string smptrace search threads \" << workers_.size() << \" main_done_us \"\n"
          "                  << us(smp_main_done) << \" joined_us \" << us(smp_joined) << \" join_latency_us \"\n"
          "                  << us(smp_joined) - us(smp_main_done) << '\\n';\n"
          "        for (auto& worker : workers_) worker->smp_trace_print(smp_t0);\n"
          "        std::cout << std::flush;\n"
          "    }\n"
          "#endif\n")
    print(f"trace source written to {out}")


if __name__ == "__main__":
    main()
