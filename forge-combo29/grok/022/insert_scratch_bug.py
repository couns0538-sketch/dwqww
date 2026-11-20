#!/usr/bin/env python3
"""Copy the idea sources and insert one heap read past the end, on one FEN only."""
import shutil
import sys
from pathlib import Path

SRC = Path("/agent/repos/work/forge-combo29")
DST = Path("/tmp/scratch-forge")
FEN = "8/8/8/8/8/8/8/K6k w - - 0 1"
NEEDLE = """        if (!candidate.set_fen(fen, &error)) {
            { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string invalid FEN: " << error << std::endl; }
            return;
        }
"""
INSERT = NEEDLE + f"""
        if (fen == "{FEN}") {{
            int* heap = new int[4];
            volatile int past_end = heap[4];
            std::cout << "info string scratch " << past_end << std::endl;
            delete[] heap;
        }}
"""


def main() -> int:
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns(".git"))
    uci = DST / "src" / "uci.cpp"
    text = uci.read_text()
    if NEEDLE not in text:
        print("NEEDLE missing")
        return 1
    uci.write_text(text.replace(NEEDLE, INSERT, 1))
    print(f"scratch {DST}")
    print(f"fen {FEN}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
