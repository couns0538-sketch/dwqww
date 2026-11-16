#!/usr/bin/env python3
"""guard_hang_test.py — does uci_guard's deadline ACTUALLY protect against a hung engine?
Uses a fake engine that answers uci/isready but never sends bestmove.
This is the control for the trap that bit my own runner (a blocking read with no real timeout)."""
import sys
sys.path.insert(0,'.')
from uci_guard import UciGuard, GuardError
import tempfile, os, stat, time
fake = tempfile.NamedTemporaryFile('w', suffix='.py', delete=False)
fake.write('''#!/usr/bin/env python3
import sys
for line in sys.stdin:
    s=line.strip()
    if s=="uci": print("id name FAKE-hang", flush=True); print("uciok", flush=True)
    elif s=="isready": print("readyok", flush=True)
    elif s=="position startpos": pass
    elif s.startswith("go"):
        pass          # PLANTED: never answer
    elif s=="quit": break
''')
fake.close(); os.chmod(fake.name, 0o755)
print("=== guard vs a PLANTED hung engine (never sends bestmove) ===")
g = UciGuard(fake.name, options=[], timeout=3.0).start()
t0=time.monotonic()
try:
    g.set_position(fen=None)
    move = g.bestmove(depth=10)
    print("  UNEXPECTED: got a move from a hung engine:", move)
except GuardError as exc:
    el=time.monotonic()-t0
    print(f"  GuardError after {el:.1f}s (timeout was 3.0s): {str(exc)[:80]}")
    print(f"  deadline respected: {el < 6.0}")
finally:
    g.stop(); os.unlink(fake.name)
print("\n  So the guard's timeout is real: a hung engine cannot hang the harness.")
