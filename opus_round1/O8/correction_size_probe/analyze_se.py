"""Singular-extension statistics from the o5_hist probe: se_ext2_m[c][m] counts singular tests with
singular_score < singular_beta, by |correction| bin c (2 cp) and margin bin m = (singular_beta - singular_score)/4
(last bin = 160 cp and more). Estimates how many doubles / triples a correction-dependent rule gives."""
import sys

CB, SB = 80, 41


def load(path):
    m = {}
    rows = {}
    for line in open(path):
        f = line.split()
        if not f or f[0] == "TAG":
            continue
        if f[0] == "se_ext2_m":
            m[int(f[1])] = [int(x) for x in f[2:]]
        elif f[0] in ("se_c", "se_ext1_c", "se_ext2_c"):
            rows[f[0]] = [int(x) for x in f[1:]]
    return m, rows


for path in sys.argv[1:]:
    m, rows = load(path)
    singular = sum(sum(r) for r in m.values())
    print(f"== {path}: singular tests {sum(rows['se_c'])}, singular (ext>=1) {singular}, AL1 doubles {sum(rows['se_ext2_c'])}")
    # margin > 24 (lock double margin) regardless of pv/budget
    lock_double = sum(m[c][s] for c in range(CB) for s in range(SB) if 4 * s + 2 > 24)
    print(f"  margin > 24 (lock double rule, ignoring PV/budget): {lock_double}")
    for pct in (25, 50):
        n = 0
        for c in range(CB):
            dm = max(0, 24 - (2 * c + 1) * pct // 100)
            n += sum(m[c][s] for s in range(SB) if 4 * s + 2 > dm)
        print(f"  double margin 24 - |c|*{pct}/100: {n} ({100.0 * (n - lock_double) / max(lock_double, 1):+.1f}% doubles)")
    for tc in (16, 24, 32, 48):
        for tm in (48, 64, 100, 140):
            n = sum(m[c][s] for c in range(CB) if 2 * c >= tc for s in range(SB) if 4 * s + 2 > tm)
            print(f"  triple if |c| >= {tc} and margin > {tm}: {n} ({100.0 * n / max(singular, 1):.1f}% of singular)")
