#!/usr/bin/env python3
"""Insert one heap read past the end into a scratch copy of uci.cpp.

The read runs only when the position FEN is the special one below.
Usage: insert_asan_bug.py PATH_TO_uci.cpp
"""
import pathlib
import sys

SPECIAL = "8/8/8/8/8/8/8/K6k w - - 0 1"
NEEDLE = """        if (!candidate.set_fen(fen, &error)) {
            { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string invalid FEN: " << error << std::endl; }
            return;
        }
"""
INSERT = NEEDLE + f"""        if (fen == "{SPECIAL}") {{
            std::vector<int> hole(4);
            volatile int sink = hole.data()[8];
            std::cout << "info string sink " << sink << std::endl;
        }}
"""


def main() -> None:
    path = pathlib.Path(sys.argv[1])
    text = path.read_text()
    if NEEDLE not in text:
        raise SystemExit("needle not found")
    if text.count(NEEDLE) != 1:
        raise SystemExit("needle not unique")
    path.write_text(text.replace(NEEDLE, INSERT, 1))
    print(f"inserted bug for fen {SPECIAL}")


if __name__ == "__main__":
    main()
