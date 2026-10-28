"""R3-2 probe: does Threads=2 really run two busy search threads? CPU vs wall for go depth on startpos / kiwipete."""
import sys
sys.path.insert(0, "F:/opus_scratch/worktrees/opus_r3_matrix/opus_r3/R3-2")
import r3_matrix as M  # noqa: E402

exe = "F:/opus_scratch/build/r3_R3-2/base.exe"
for threads in (1, 2, 2, 1):
    e = M.Engine(exe, threads, [])
    for depth in (16, 18):
        c0, y0 = M.proc_cpu(e.p)
        import time
        w0 = time.perf_counter()
        e.send("ucinewgame")
        e.send("position fen " + M.BENCH_FENS[1])
        e.send(f"go depth {depth}")
        last = None
        while True:
            m = e.wait(r"^(bestmove|info depth \d+ .* nodes (\d+))")
            if m.group(1).startswith("bestmove"):
                break
            last = int(m.group(2))
        w1 = time.perf_counter()
        c1, y1 = M.proc_cpu(e.p)
        print(f"threads {threads} depth {depth} nodes {last} wall {w1 - w0:.3f}s cpu {c1 - c0:.3f}s "
              f"cpu/wall {(c1 - c0) / (w1 - w0):.2f} cycles/wall {(y1 - y0) / (w1 - w0) / 1e9:.2f} G/s", flush=True)
    print(e.close())
