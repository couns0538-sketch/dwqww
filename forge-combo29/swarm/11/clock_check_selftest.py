#!/usr/bin/env python3
"""clock_check_selftest.py — POSITIVE CONTROL for clock_repeat_check.py.
It reports "all rows stable" or "some rows unstable" — but can it actually SEE instability?
Plant a fake engine that returns a RANDOM node count each run and a random move every other run,
and require the checker to flag it. Without this, a "stable" verdict proves nothing."""
import sys, tempfile, os, textwrap
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import clock_repeat_check as crc

fake = tempfile.NamedTemporaryFile('w', suffix='.py', delete=False)
fake.write(textwrap.dedent('''\
    #!/usr/bin/env python3
    # PLANTED: node count and (every other run) the move vary randomly.
    import sys, random
    run = random.randrange(10**9)
    for line in sys.stdin:
        s = line.strip()
        if s == "uci":
            print("id name FAKE-unstable", flush=True); print("uciok", flush=True)
        elif s == "isready":
            print("readyok", flush=True)
        elif s.startswith("position"):
            pass
        elif s.startswith("go"):
            nodes = random.randrange(1000, 90000)
            move = "g8f6" if run % 2 == 0 else "a7a6"
            print(f"info depth 5 score cp 1 nodes {nodes} time 1 pv {move}", flush=True)
            print(f"bestmove {move}", flush=True)
        elif s == "quit":
            break
'''))
fake.close(); os.chmod(fake.name, 0o755)

print("positive control for clock_repeat_check:")
print("  a fake engine whose NODE COUNT and MOVE vary randomly must be reported UNSTABLE\n")
ok = crc.check(fake.name, "PLANTED-unstable", ["go movetime 50"], 5)
os.unlink(fake.name)
print(f"\n  checker called it {'STABLE (BLIND!)' if ok else 'UNSTABLE (correctly detected)'}")
print(f"  positive control {'PASSED — a clean verdict from this tool means something' if not ok else 'FAILED — the tool cannot see instability'}")
sys.exit(0 if not ok else 1)
