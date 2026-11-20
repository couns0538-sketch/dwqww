#!/usr/bin/env python3
"""Copy the idea sources and insert one heap read past the end, on one FEN only."""
import shutil
import subprocess
from pathlib import Path

SRC = Path("/agent/repos/work/forge-combo29")
DST = Path("/home/ubuntu/scratch-forge")
SPECIAL = "8/8/8/3k4/8/8/8/3K4 w - - 0 1"
NOTE = Path(__file__).resolve().parent / "scratch_bug.txt"

if DST.exists():
    shutil.rmtree(DST)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("build", "build-asan"))

uci = DST / "src" / "uci.cpp"
text = uci.read_text(encoding="utf-8")
fn = """__attribute__((noinline)) int scratch_read_past(int* pointer) { return pointer[4]; }

"""
old_fn = "void apply_position(forge::Board& board, std::istringstream& input) {\n"
if old_fn not in text:
    raise SystemExit("apply_position not found")
text = text.replace(old_fn, fn + old_fn, 1)
old = "        std::string error;\n        if (!candidate.set_fen(fen, &error)) {\n"
new = f"""        if (fen == "{SPECIAL}") {{
            int* heap = new int[4]();
            volatile int past = scratch_read_past(heap);
            delete[] heap;
            const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
            std::cout << "info string scratch-read " << past << std::endl;
        }}
        std::string error;
        if (!candidate.set_fen(fen, &error)) {{
"""
if old not in text:
    raise SystemExit("set_fen site not found")
text = text.replace(old, new, 1)
uci.write_text(text, encoding="utf-8")
NOTE.write_text(
    "Scratch copy only: /home/ubuntu/scratch-forge\n"
    "Not in idea.patch.txt.\n"
    f"On FEN {SPECIAL} the engine allocates int[4] on the heap and reads index 4.\n"
    "The read is in scratch_read_past, marked noinline, so the compiler keeps it.\n",
    encoding="utf-8",
)
print("scratch", DST)
print("special", SPECIAL)
