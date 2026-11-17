#!/usr/bin/env python3
"""Self-test for the exit-drain: a fake engine that reports AFTER `quit`.

The audit brief warns that a sanitizer reporting at exit cannot be read to
`bestmove`.  The first version of this seat's driver had exactly that bug: it
sent `quit`, called wait(), and never read the pipe again -- so anything
written at exit was lost, and a run would be called clean without ever having
observed its own exit.

This proves the fixed driver catches post-quit output, by comparing it against
a deliberately naive driver that reads only to bestmove.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

FAKE = r'''#!/usr/bin/env python3
import sys
for line in sys.stdin:
    line = line.strip()
    if line == "uci":
        print("uciok", flush=True)
    elif line == "isready":
        print("readyok", flush=True)
    elif line.startswith("go"):
        print("info depth 1 score cp 0 nodes 10", flush=True)
        print("bestmove e2e4", flush=True)
    elif line == "quit":
        # The exit-time report. A driver that stops at bestmove loses this.
        print("WARNING: ThreadSanitizer: data race (pid=1)", flush=True)
        print("SUMMARY: ThreadSanitizer: data race exit_time.cpp:1 in at_exit()", flush=True)
        break
'''

naive = r'''import subprocess
p = subprocess.Popen([sys.argv[1]], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, text=True, bufsize=1)
def send(c):
    p.stdin.write(c + "\n"); p.stdin.flush()
seen = []
send("uci"); seen.append(p.stdout.readline().rstrip())
send("isready"); seen.append(p.stdout.readline().rstrip())
send("go depth 1")
while True:
    l = p.stdout.readline()
    if not l: break
    seen.append(l.rstrip())
    if l.startswith("bestmove"): break
send("quit")
p.wait()                      # <-- the bug: never drains after quit
print(len([x for x in seen if "ThreadSanitizer" in x]))
'''


def main():
    # Write the fake engine into a private temp dir the program creates itself,
    # not into the scripts folder: owner-only and unpredictable, so the 0o755
    # below cannot be aimed at a pre-existing file.
    tmpdir = tempfile.mkdtemp(prefix="tsan-drain-selftest-")
    fake = os.path.join(tmpdir, "fake_engine_exit_report.py")
    with open(fake, "w", encoding="utf-8") as f:
        f.write(FAKE)
    os.chmod(fake, 0o755)

    sys.path.insert(0, HERE)
    from tsan_driver import Engine, races

    print("== fixed driver (drains to EOF) ==")
    e = Engine(fake)
    e.sync()
    e.go("go depth 1", 30)
    log = e.close()
    got = races(log)
    print("  race reports seen:", len(got))
    print("  drained_to_eof:", getattr(e, "drained_to_eof", None))
    print("  exit_code:", getattr(e, "exit_code", None))
    fixed_ok = len(got) == 1

    print("== naive driver (stops at bestmove, never drains) ==")
    naive_py = os.path.join(tmpdir, "naive_driver.py")
    with open(naive_py, "w", encoding="utf-8") as f:
        f.write("import sys\n" + naive)
    out = subprocess.run([sys.executable, naive_py, fake],
                         capture_output=True, text=True, timeout=60)
    naive_count = int(out.stdout.strip() or 0)
    print("  race reports seen:", naive_count)
    naive_ok = naive_count == 0

    shutil.rmtree(tmpdir, ignore_errors=True)

    print()
    if fixed_ok and naive_ok:
        print("DRAIN_SELFTEST_PASS: fixed driver caught the exit report, "
              "the naive driver lost it")
        return 0
    print("DRAIN_SELFTEST_FAIL: fixed=%s naive=%s" % (fixed_ok, naive_ok))
    return 1


if __name__ == "__main__":
    sys.exit(main())
