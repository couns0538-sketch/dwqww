"""R7 J4: how long does fastchess take to load an opening book before the first game starts?
usage: python -I -B book_load_time.py <fastchess.exe> <engine.exe> <out_dir> <book> <pgn|epd> [repeats=3]
Starts fastchess (2 games, concurrency 1, tc 0.5+0.01, order=random like the gates) and times, from process start,
the first 'Started game' line on stdout and the process exit. Writes nothing outside <out_dir> (fastchess's
config.json and the PGN land there). Prints one line per repeat and the medians."""
import os
import statistics
import subprocess
import sys
import time

fc, eng, out, book, fmt = sys.argv[1:6]
rep = int(sys.argv[6]) if len(sys.argv) > 6 else 3
os.makedirs(out, exist_ok=True)
firsts, totals = [], []
for r in range(rep):
    pgn = os.path.join(out, f"games_{fmt}_{r}.pgn")
    cmd = [fc, "-engine", "name=a", f"cmd={eng}", "option.Hash=16", "option.OwnBook=false",
           "-engine", "name=b", f"cmd={eng}", "option.Hash=16", "option.OwnBook=false",
           "-each", "tc=0.5+0.01", "proto=uci", "-openings", f"file={book}", f"format={fmt}", "order=random",
           "-srand", "1100276691", "-games", "2", "-rounds", "1", "-concurrency", "1", "-pgnout", f"file={pgn}"]
    t0 = time.perf_counter()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=out,
                         creationflags=0x00004000)  # BELOW_NORMAL_PRIORITY_CLASS
    first = None
    for line in p.stdout:
        if first is None and line.startswith("Started game"):
            first = time.perf_counter() - t0
    p.wait()
    total = time.perf_counter() - t0
    firsts.append(first if first is not None else float("nan"))
    totals.append(total)
    print(f"{fmt} run {r + 1}: first game started after {firsts[-1]:.3f} s, exit after {total:.3f} s", flush=True)
print(f"{fmt} median: first game {statistics.median(firsts):.3f} s, total {statistics.median(totals):.3f} s "
      f"({os.path.getsize(book)} bytes book)")
