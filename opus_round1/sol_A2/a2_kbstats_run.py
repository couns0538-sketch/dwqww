#!/usr/bin/env python3
"""A2 microbench driver: run `bench <d>` on an engine built with -DFORGE_A2_KBSTATS and keep every line.

usage: a2_kbstats_run.py <forge_a2_on.exe> <out.log> <depth> [<depth> ...]

The engine prints, after each `info string bench depth D nodes N ...` line, one `info string a2kb pos <i> ...`
block per bench position and one `info string a2kb total depth D ...` block (see the patch
forge_astra_A2_kbstats_microbench_20261027.patch). This driver sends the same options as LA/2_build/uci_check.py
(Threads 1, Hash 16, OwnBook false), waits for each total block, checks the bench node count against the AL1 s198
pins (the counters must not change the search) and writes the raw engine output to <out.log>.
Exit status 0 only if every requested depth has its total block and the node pin matches.
"""
import re
import subprocess
import sys

REF_BENCH = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}


def main() -> int:
    exe, out_path, depths = sys.argv[1], sys.argv[2], [int(d) for d in sys.argv[3:]]
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    log = open(out_path, "w", encoding="ascii", newline="\n")

    def send(s):
        log.write("> " + s + "\n")
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(pattern):
        rx = re.compile(pattern)
        for line in p.stdout:
            log.write(line)
            m = rx.search(line)
            if m:
                return m
        raise SystemExit("engine exited before matching " + pattern)

    send("uci")
    wait(r"^uciok")
    for o in ("Threads value 1", "Hash value 16", "OwnBook value false"):
        send("setoption name " + o)
    send("isready")
    wait(r"^readyok")
    ok = True
    for d in depths:
        send(f"bench {d}")
        m = wait(rf"bench depth {d} nodes (\d+)")
        nodes = int(m.group(1))
        # the total block ends with the last layout line of the total
        wait(rf"a2kb total depth {d} layout R8 ")
        ref = REF_BENCH.get(d)
        good = ref is None or nodes == ref
        ok &= good
        print(f"bench d{d} nodes {nodes} ref {ref} {'OK' if good else 'FAIL'}", flush=True)
    send("quit")
    p.wait(timeout=60)
    log.close()
    print("ALL OK" if ok else "MISMATCH")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
