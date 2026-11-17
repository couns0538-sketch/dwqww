#!/usr/bin/env python3
"""Build a variant with the PRE-d9a8587df branch order, so the shipped
short-circuit can be compared against the order it replaced.

d9a8587df "Accept identical capped rule-50 clocks before cross-clock TT checks"
moved the exact-clock test above the mate-distance test. Its title says it is
about clocks that cap equal (99 vs 100, 100 vs 120), but moving the test also
changes every exactly-equal clock where the mate cannot land -- a different and
larger set. The two orders differ only on cells where
    stored == capped  AND  current + distance > 100,
so this variant isolates that.
"""
import pathlib
import shutil
import subprocess
import sys

SRC = pathlib.Path(__file__).resolve().parents[3]
OUT = pathlib.Path("/tmp/forge-variants") / "mate_first"

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

# The order before d9a8587df: the mate test runs first, so an exactly-matching
# clock does NOT rescue a mate that cannot land inside the remaining counter.
PRE = """    [[nodiscard]] bool score_usable(std::uint16_t current_clock) const {
        if (is_mate_score(score)) {
            const int distance = MateValue - (score < 0 ? -static_cast<int>(score) : static_cast<int>(score));
            if (static_cast<int>(current_clock) + distance > 100) return false;
        }
        const int capped = current_clock < 100 ? static_cast<int>(current_clock) : 100;
        const int stored_clock = rule50_clock;
        const int stored_depth = depth;
        const bool inside_horizon = stored_clock + stored_depth < 100 &&
                                    static_cast<int>(current_clock) + stored_depth < 100 &&
                                    stored_clock < 90 && capped < 90;
        return inside_horizon || stored_clock == capped;
    }
"""


def build(dst):
    env = {"LIBRARY_PATH": "/usr/lib/gcc/x86_64-linux-gnu/13", "PATH": "/usr/bin:/bin:/usr/local/bin"}
    bd = dst / "build"
    for cmd in (["cmake", "-S", str(dst), "-B", str(bd), "-DCMAKE_BUILD_TYPE=Release",
                 "-DCMAKE_CXX_COMPILER=/usr/bin/g++", "-DFORGE_MARCH=x86-64-v4"],
                ["cmake", "--build", str(bd), "-j4"]):
        r = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if r.returncode:
            print(r.stdout[-2000:], r.stderr[-2000:])
            raise SystemExit("build failed")
    return bd / "forge"


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / "src").mkdir()
    shutil.copytree(SRC / "include", OUT / "include")
    for f in (SRC / "src").glob("*"):
        if f.is_file():
            shutil.copy2(f, OUT / "src" / f.name)
    shutil.copy2(SRC / "CMakeLists.txt", OUT / "CMakeLists.txt")
    hpp = OUT / "include/forge/search.hpp"
    text = hpp.read_text()
    if SHIPPED not in text:
        raise SystemExit("shipped body not found")
    hpp.write_text(text.replace(SHIPPED, PRE))
    print(build(OUT))


if __name__ == "__main__":
    main()
