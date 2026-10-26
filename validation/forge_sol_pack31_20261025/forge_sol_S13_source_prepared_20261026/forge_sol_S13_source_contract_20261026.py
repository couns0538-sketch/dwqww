"""Source-only contracts for the isolated S13 child-prefetch candidate.

These checks do not compile or run Forge and do not prove node parity or speed.
"""
from pathlib import Path
import re

FLAG = "FORGE_S13_TT_CHILD_PREFETCH"
OPTION = "TtChildPrefetch"
FILES = ("CMakeLists.txt", "include/forge/search.hpp", "src/search.cpp", "src/uci.cpp")


def read_sources(root):
    return {name: (Path(root) / name).read_bytes().decode("utf-8") for name in FILES}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def erase_feature(text):
    """Erase just this feature's preprocessor blocks; preserve other bytes."""
    output = []
    depth = 0
    for line in text.splitlines(keepends=True):
        if depth:
            require(not re.match(r"\s*#\s*(else|elif)\b", line),
                    "alternate feature branches need an explicit OFF-path proof")
            if re.match(r"\s*#\s*if(?:def|ndef)?\b", line):
                depth += 1
            elif re.match(r"\s*#\s*endif\b", line):
                depth -= 1
        elif line.strip() == "#ifdef " + FLAG:
            depth = 1
        else:
            output.append(line)
    require(depth == 0, "unterminated feature guard")
    result = "".join(output)
    result = re.sub(
        r'\noption\(' + FLAG + r' "[^"\n]+" OFF\)\n'
        r'if\(' + FLAG + r'\)\n'
        r'    target_compile_definitions\(forge_core PUBLIC ' + FLAG + r'=1\)\n'
        r'endif\(\)\n', "", result,
    )
    return result


def validate_source(candidate, baseline):
    c = read_sources(candidate) if not isinstance(candidate, dict) else candidate
    b = read_sources(baseline) if not isinstance(baseline, dict) else baseline
    cmake, header, search, uci = (c[k] for k in FILES)
    require(f'option({FLAG} "Build the opt-in {OPTION} experiment" OFF)' in cmake,
            "build switch must exist and default OFF")
    require("static_assert(sizeof(TTEntry) == 16);" in header and
            "static_assert(sizeof(TTCluster) == 64);" in header,
            "retain existing 16-byte entry and 64-byte bucket assertions")
    require(header.count("static_assert(sizeof(TTCluster) == 64);") == 1,
            "do not duplicate existing bucket assertion")
    require("std::atomic<bool> s13_tt_child_prefetch{false};" in header and
            "std::atomic<bool> s13_tt_child_prefetch_announced{false};" in header,
            "requested option and announcement must be atomic OFF defaults")
    require("bool s13_tt_child_prefetch = false;" in header and
            "bool s13_tt_child_prefetch_ = false;" in header,
            "limits and worker option must default false")
    load = "worker_limits.s13_tt_child_prefetch = shared_.s13_tt_child_prefetch.load(std::memory_order_relaxed);"
    require(search.count(load) == 1, "snapshot requested flag exactly once")
    require(search.index(load) < search.index("helpers.emplace_back("),
            "snapshot option before launching helpers")
    require("s13_tt_child_prefetch_ = limits.s13_tt_child_prefetch;" in search,
            "worker must read its own limits snapshot")
    require(search.count("shared_.s13_tt_child_prefetch.load(") == 1,
            "recursive worker must not read mutable requested option")
    require(search.count('"info string TtChildPrefetch active"') == 1 and
            "s13_tt_child_prefetch_announced.exchange(true, std::memory_order_relaxed)" in search,
            "announce actual ON path once")
    for anchor, continuation in [
        ("board.make_null_move(undo);", "int null_score = -search("),
        ("                (void)board.make_move(move, undo);", "int value = -qsearch("),
    ]:
        start = search.index(anchor)
        stop = search.index(continuation, start)
        region = search[start:stop]
        require("if (s13_tt_child_prefetch_) shared_.tt.prefetch(board.key());" in region,
                "new child path missing guarded prefetch: " + continuation)
        require("#ifdef " + FLAG in region, "new prefetch must have build guard")
    require(search.count("shared_.tt.prefetch(board.key());") == 4,
            "retain two existing prefetches and add exactly two")
    require('option name TtChildPrefetch type check default false\\n' in uci,
            "typed UCI option must default false")
    require('name == "TtChildPrefetch"' in uci and
            'value_text == "true" || value_text == "false"' in uci,
            "accept only valid option booleans")
    require("bench_searcher.set_s13_tt_child_prefetch(searcher.s13_tt_child_prefetch_enabled());" in uci,
            "bench searcher must inherit the selected option")
    for name in FILES:
        require(erase_feature(c[name]) == b[name],
                "feature-OFF source erasure differs from baseline: " + name)
    return {"status": "PASS_SOURCE_ONLY", "source_files": len(FILES),
            "existing_prefetch_sites": 2, "new_prefetch_sites": 2,
            "native_correctness_speed_strength": "UNVERIFIED"}
