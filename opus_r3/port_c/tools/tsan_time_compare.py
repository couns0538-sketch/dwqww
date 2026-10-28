"""Compare per-test CTest times of two ctest logs (e.g. the base TSan job and this branch's). usage: a.log b.log"""
import re
import sys

RX = re.compile(r"Test +#\d+: (\S+) \.*\s*(?:\*\*\*)?\w+\s+([\d.]+) sec")


def times(path):
    out = {}
    for line in open(path, encoding="utf-8", errors="replace"):
        m = RX.search(line)
        if m:
            out[m.group(1)] = float(m.group(2))
    return out


a, b = times(sys.argv[1]), times(sys.argv[2])
rows = []
for name in sorted(set(a) | set(b)):
    ta, tb = a.get(name), b.get(name)
    rows.append((name, ta, tb, (tb or 0.0) - (ta or 0.0)))
rows.sort(key=lambda r: -r[3])
print(f"{'test':34s} {'base s':>9s} {'branch s':>9s} {'diff s':>9s}")
for name, ta, tb, d in rows:
    print(f"{name:34s} {('-' if ta is None else f'{ta:.2f}'):>9s} {('-' if tb is None else f'{tb:.2f}'):>9s} {d:9.2f}")
print(f"{'TOTAL':34s} {sum(a.values()):9.2f} {sum(b.values()):9.2f} {sum(b.values()) - sum(a.values()):9.2f}")
