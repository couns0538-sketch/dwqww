"""Scratch analysis of the o5_hist instrumentation (|correction| = |static_eval - raw_eval| in cp, 2 cp bins)."""
import sys

CB, SB = 80, 41


def load(path):
    rows, mats = {}, {}
    for line in open(path):
        f = line.split()
        if not f or f[0] == "TAG":
            continue
        name = f[0]
        if name in ("rfp_fire_cs", "fut_fire_cs", "nmp_pass_cs", "se_ext2_m", "lmr_r"):
            mats.setdefault(name, {})[int(f[1])] = [int(x) for x in f[2:]]
        else:
            rows[name] = [int(x) for x in f[1:]]
    return rows, mats


def pct(a, b):
    return 100.0 * a / b if b else 0.0


def quantiles(hist, qs):
    tot = sum(hist)
    out, acc, k = [], 0, 0
    for i, h in enumerate(hist):
        acc += h
        while k < len(qs) and acc >= qs[k] * tot:
            out.append(2 * i)
            k += 1
    return out


def main():
    for path in sys.argv[1:]:
        rows, mats = load(path)
        print("==", path)
        n = rows["nodes_c"]
        tot = sum(n)
        print(f"non-check nodes {tot}; |corr| quantiles 50/75/90/95/99%: {quantiles(n, [0.5, 0.75, 0.9, 0.95, 0.99])} cp; "
              f"zero-bin (0-1cp) {pct(n[0], tot):.1f}%  >=16cp {pct(sum(n[8:]), tot):.1f}% >=32cp {pct(sum(n[16:]), tot):.1f}%")
        for site, ev, fire, mat in (("RFP", "rfp_eval_c", "rfp_fire_c", "rfp_fire_cs"),
                                    ("FUT", "fut_eval_c", "fut_fire_c", "fut_fire_cs")):
            e, fi = rows[ev], rows[fire]
            print(f"{site}: evaluated {sum(e)}, fired {sum(fi)} ({pct(sum(fi), sum(e)):.1f}%); |corr| quantiles at fires "
                  f"50/90/99: {quantiles(fi, [0.5, 0.9, 0.99])}")
            for p in (25, 50, 75, 100, 150, 200):
                blocked = 0
                for c in range(CB):
                    extra = (2 * c + 1) * p // 100  # bin centre
                    row = mats[mat][c]
                    for s in range(SB):
                        if 4 * s + 2 < extra:
                            blocked += row[s]
                print(f"   extra = |corr|*{p}/100: ~blocked fires {blocked} ({pct(blocked, sum(fi)):.1f}% of fires)")
        e = rows["nmp_eval_c"]
        m = mats["nmp_pass_cs"]
        print(f"NMP: tries {sum(e)}; |corr| quantiles 50/90/99: {quantiles(e, [0.5, 0.9, 0.99])}")
        for p in (25, 50, 100, 200):
            blocked = 0
            for c in range(CB):
                extra = (2 * c + 1) * p // 100
                for s in range(SB):
                    if 4 * s + 2 < extra:
                        blocked += m[c][s]
            print(f"   extra = |corr|*{p}/100: ~blocked tries {blocked} ({pct(blocked, sum(e)):.1f}%)")
        l = rows["lmr_c"]
        lr = mats["lmr_r"]
        print(f"LMR: reduced moves {sum(l)}; |corr| quantiles 50/90/99: {quantiles(l, [0.5, 0.9, 0.99])}")
        rdist = [sum(lr[c][r] for c in range(CB)) for r in range(16)]
        print("   r distribution 0..15:", rdist)
        for thr in (20, 30, 40):
            hit = sum(l[thr // 2:])
            print(f"   whole-ply relief at |corr|>={thr}: {pct(hit, sum(l)):.1f}% of reduced moves")
        for p in (25, 50, 100):
            hit = 0
            for c in range(CB):
                for r in range(16):
                    if r * (2 * c + 1) * p // 6400 >= 1:
                        hit += lr[c][r]
            print(f"   relief = r*|corr|*{p}/6400 >= 1 ply: {pct(hit, sum(l)):.1f}% of reduced moves")
        s = rows["se_c"]
        print(f"SE: singular tests {sum(s)}, ext>=1 {sum(rows['se_ext1_c'])}, ext2 {sum(rows['se_ext2_c'])}; "
              f"|corr| quantiles at tests 50/90/99: {quantiles(s, [0.5, 0.9, 0.99])}")


if __name__ == "__main__":
    main()
