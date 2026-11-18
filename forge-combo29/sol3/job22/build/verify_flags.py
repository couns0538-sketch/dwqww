"""Assert the generated flags preserve the locked build aside from the sanitizer overlay."""

import argparse
from collections import Counter
from pathlib import Path
import shlex

AU = "-O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=undefined"
T = "-O1 -g -fsanitize=thread"


def flags(path):
    return {
        key.rstrip(): shlex.split(value.strip())
        for line in path.read_text().splitlines()
        if line.startswith("CXX") and "=" in line
        for key, value in [line.split("=", 1)]
    }


def require_equal(wanted, actual, label):
    left, right = Counter(wanted), Counter(actual)
    if left != right:
        raise SystemExit(f"{label}: missing {list((left - right).elements())}, extra {list((right - left).elements())}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family", choices=("AU", "T"))
    parser.add_argument("base", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    make_flags = Path("CMakeFiles/forge.dir/flags.make")
    baseline, sanitized = flags(args.base / make_flags), flags(args.target / make_flags)
    require_equal([flag for flag in baseline["CXX_DEFINES"] if flag != "-DNDEBUG"],
                  sanitized["CXX_DEFINES"], "target definitions")
    preserve = [flag for flag in baseline["CXX_FLAGS"] if flag not in ("-DNDEBUG", "-O3")]
    overlay = shlex.split(AU if args.family == "AU" else T)
    require_equal([*preserve, *overlay], sanitized["CXX_FLAGS"], "compiler flags")
    if sanitized["CXX_FLAGS"][-len(overlay):] != overlay:
        raise SystemExit("sanitizer overlay is not last on the compile command")
    link = shlex.split((args.target / "CMakeFiles/forge.dir/link.txt").read_text())
    expected_link = "-fsanitize=address,undefined" if args.family == "AU" else "-fsanitize=thread"
    if link.count(expected_link) != 1 or "-DNDEBUG" in link or "-O3" in link:
        raise SystemExit("sanitizer runtime or release flags changed at link")
    print("Effective compile definitions match retained baseline with NDEBUG removed.")
    print("All other effective compiler flags match besides -O3 removal and the requested sanitizer overlay.")
    print("Verified compiler flags:", shlex.join(sanitized["CXX_FLAGS"]))
    print("Verified linker sanitizer:", expected_link)


if __name__ == "__main__":
    main()
