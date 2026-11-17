#!/usr/bin/env python3
"""analyse_loneking.py  -- read the JSON from loneking11.py for two builds and ask
whether the reduction counters separate the counter-cases.

Usage: analyse_loneking.py ON.json OFF.json [--label ON OFF]
"""
import argparse
import json
import sys


def g(block, key, default=0):
    if not block:
        return default
    try:
        return int(block.get(key, default))
    except (TypeError, ValueError):
        return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("on")
    ap.add_argument("off")
    ap.add_argument("--label", nargs=2, default=["capON", "capOFF"])
    a = ap.parse_args()
    on = json.load(open(a.on))
    off = json.load(open(a.off))
    if len(on) != len(off):
        sys.exit(f"row count differs: {len(on)} vs {len(off)}")
    lon, loff = a.label

    hdr = (f"{'board':44s} {'cls':4s} {'dNodes':>7s} {'dAppl':>7s} "
           f"{'applON':>6s} {'applOFF':>7s} {'rmeanON':>7s} {'rmeanOFF':>8s} "
           f"{'gate':>6s} {'clamp':>6s} {'clamp%':>6s} {'capRmean':>8s} "
           f"{'rejON':>6s} {'rejOFF':>6s} {'resON':>6s} {'resOFF':>6s} {'sep?':>5s}")
    print(hdr)
    print("-" * len(hdr))

    rows = []
    for r_on, r_off in zip(on, off):
        fen = r_on["fen"]
        cls = r_on["cls"]
        dn = (r_on["nodes"] or 0) - (r_off["nodes"] or 0)
        ton, toff = r_on["lmr_total"] or {}, r_off["lmr_total"] or {}
        aon, aoff = g(ton, "applied"), g(toff, "applied")
        rmon = float(ton.get("rmean", 0) or 0)
        rmoff = float(toff.get("rmean", 0) or 0)
        gate = g(ton, "cap_gate")
        clamp = g(ton, "cap_clamp")
        capr = float(ton.get("cap_rmean", 0) or 0)
        share = (100.0 * clamp / gate) if gate else 0.0
        # "consistent" = the reduction count moves the same way as the node count,
        # comparing the two variants: cap-off applies more reductions IFF it visits
        # more nodes.
        consistent = (dn > 0) == (aoff > aon)
        rows.append({
            "fen": fen, "cls": cls, "dn": dn, "aon": aon, "aoff": aoff,
            "rmon": rmon, "rmoff": rmoff, "gate": gate, "clamp": clamp,
            "share": share, "capr": capr,
            "rejon": g(ton, "rej"), "rejoff": g(toff, "rej"),
            "reson": g(ton, "research"), "resoff": g(toff, "research"),
            "consistent": consistent,
        })
        print(f"{fen:44s} {cls:4s} {dn:>+7d} {aoff - aon:>+7d} {aon:>6d} {aoff:>7d} "
              f"{rmon:>7.2f} {rmoff:>8.2f} {gate:>6d} {clamp:>6d} {share:>5.1f}% {capr:>8.2f} "
              f"{g(ton,'rej'):>6d} {g(toff,'rej'):>6d} {g(ton,'research'):>6d} {g(toff,'research'):>6d} "
              f"{'yes' if consistent else 'NO':>5s}")

    print()
    cntr = [r for r in rows if r["cls"] == "CNTR"]
    pred = [r for r in rows if r["cls"] == "pred"]
    print("share of nodes where the cap actually lowered r (clamp/gate):")
    for name, grp in (("predicted (cap-off fewer nodes)", pred), ("counter-case (cap-off MORE nodes)", cntr)):
        shares = [r["share"] for r in grp]
        capr = [r["capr"] for r in grp]
        print(f"  {name:36s} n={len(grp)}  clamp% median {sorted(shares)[len(shares)//2]:.1f} "
              f"min {min(shares):.1f} max {max(shares):.1f} | cap_rmean median "
              f"{sorted(capr)[len(capr)//2]:.2f} min {min(capr):.2f} max {max(capr):.2f}")

    print()
    print("does the clamped-reduction SHARE separate the two classes?")
    ps = [r["share"] for r in pred]
    cs = [r["share"] for r in cntr]
    overlap = [c for c in cs if min(ps) <= c <= max(ps)]
    print(f"  counter-case shares {['%.1f%%' % c for c in cs]} vs predicted range "
          f"[{min(ps):.1f}%, {max(ps):.1f}%]")
    print(f"  counter-cases falling INSIDE the predicted range: {len(overlap)} of {len(cs)}")

    print()
    print("does the reduction COUNT move with the node count?")
    bad = [r for r in rows if not r["consistent"]]
    print(f"  consistent on {len(rows) - len(bad)} of {len(rows)}; "
          f"inconsistent: {[r['fen'] + ' (' + r['cls'] + ')' for r in bad]}")
    for r in bad:
        print(f"    {r['fen']}: nodes {'+' if r['dn']>0 else ''}{r['dn']}, "
              f"applied {r['aon']}->{r['aoff']} ({r['aoff']-r['aon']:+d})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
