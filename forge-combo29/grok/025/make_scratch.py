#!/usr/bin/env python3
"""Copy the patched engine and insert one heap over-read on one FEN.
The scratch tree is outside the repository. Nothing here is an engine commit.
"""
import shutil
import sys
from pathlib import Path

SPECIAL = "8/8/8/8/8/8/8/K6k w - - 0 1"
NEEDLE = """        if (!candidate.set_fen(fen, &error)) {
            { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string invalid FEN: " << error << std::endl; }
            return;
        }
"""
INSERT = NEEDLE + f"""        if (fen == "{SPECIAL}") {{
            int* heap = new int[4];
            volatile int past_end = heap[4];
            std::cout << "info string scratch past " << past_end << std::endl;
            delete[] heap;
        }}
"""


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: make_scratch.py SRC_DIR DEST_DIR", file=sys.stderr)
        return 2
    src = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest, symlinks=True)
    uci = dest / "src" / "uci.cpp"
    text = uci.read_text()
    if NEEDLE not in text:
        print("needle missing", file=sys.stderr)
        return 1
    if text.count(NEEDLE) != 1:
        print("needle not unique", file=sys.stderr)
        return 1
    uci.write_text(text.replace(NEEDLE, INSERT, 1))
    print(f"scratch {dest}")
    print(f"special_fen {SPECIAL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
