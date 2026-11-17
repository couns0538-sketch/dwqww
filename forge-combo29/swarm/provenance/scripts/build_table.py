#!/usr/bin/env python3
"""Aggregate finding rows into canonical BUILD identities and rank them.

Input : evidence/finding_rows.json  (from map_finding_rows.py)
Output: evidence/build_table.json   (the table in FINDINGS.md)

A "finding" is (seat, finding-id). One finding can name more than one build (the
usual shape is "PC r15 under PC20 versus base under S14"), so it is counted once
against each build it actually names, and the table says so.
"""
import argparse
import collections
import json
import os

# Canonicalise the many spellings of the same artefact down to one identity.
CANON = [
    # order matters: most specific first
    ("binary e06310ec (base, Release g++13)", ("e06310ec",)),
    ("binary 068f0927 (PC r15, Release g++13)", ("068f0927",)),
    ("patch d6bd72c5 (FABLE_TO_swarm_5 r15 patch text)", ("d6bd72c5",)),
    ("binary 227aae56 (r15 + -DFORGE_NNUE_V3=1)", ("227aae56",)),
    ("binary b109a0a5 (base, ASan/UBSan)", ("b109a0a5",)),
    ("binary 7c4e1aee (/tmp/build-base, variant)", ("7c4e1aee",)),
    ("binary 6e0e9522 (seat 12 build)", ("6e0e9522",)),
    ("binary 81c52608 (seat 01 'mine' build)", ("81c52608",)),
    ("binary 1a9460d6 (seat 28 planted build)", ("1a9460d6",)),
    ("binary 0dceb07e (seat 28 planted build)", ("0dceb07e",)),
    ("binary 571e7c83 (seat 27 SAN build)", ("571e7c83",)),
    ("binary ae1a49b6 (PC r15 ASan+UBSan)", ("ae1a49b6",)),
    ("binary 581159a4 (seat 01 -D_GLIBCXX_DEBUG)", ("581159a4",)),
    ("binary 698d2d9b (PC r15 TSan)", ("698d2d9b",)),
    ("NET file 1db8525e (v3 test net, built by make_v3_testnet.py)", ("1db8525e", "fdff70de")),
    ("dataset digest e6beb5f9 (bench SUM over 200 positions)", ("e6beb5f9", "2337b0d1")),
    ("commit 6b98f217 (audit base) / 'base'", ("6b98f217", "base (6b98f217)")),
    ("named PC r15 (label)", ("PC r15",)),
    ("branch integrate/combo29-all", ("integrate/combo29-all",)),
    ("branch handoff/fable-opus-combo29-all", ("handoff/fable-opus",)),
    ("\"the owner's PC\" (net not shared)", ("owner's pc", "owner's build")),
    ("settings PC20 (a settings block, NOT a build)", ("PC20 (settings, not a build)",)),
    ("descriptor: ASan+UBSan build (flags never recorded)", ("asan",)),
    ("descriptor: TSan build (flags never recorded)", ("tsan",)),
    ("descriptor: -D_GLIBCXX_DEBUG build (flags never recorded)", ("-d_glibcxx_debug", "_glibcxx_debug")),
]


def canon(ref):
    """Exact-prefix match on the hex/label, never a loose substring.

    A loose `in` test here silently dropped every short binary hash, because
    '1a9460d6' is a substring of nothing but '6b98f217' is a prefix of several
    spellings -- and the failure was invisible: the table simply did not list them.
    So: a token matches a canonical entry only if the entry's key is a PREFIX of
    the token (or equal), which is the same rule git uses for short shas.
    """
    r = ref.lower().strip()
    for name, keys in CANON:
        for k in keys:
            kl = k.lower()
            if r == kl or r.startswith(kl) or kl.startswith(r):
                return name
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default="evidence/finding_rows.json")
    ap.add_argument("--verdicts", default="evidence/build_verdicts.json")
    ap.add_argument("--out", default="evidence/build_table.json")
    args = ap.parse_args()

    rows = json.load(open(args.rows))
    verdicts = json.load(open(args.verdicts)) if os.path.exists(args.verdicts) else {}

    findings = collections.defaultdict(set)   # build -> {(seat, finding)}
    rowcount = collections.Counter()
    for r in rows:
        seen = set()
        for ref in r["build_refs"]:
            c = canon(ref)
            if not c or c in seen:
                continue
            seen.add(c)
            findings[c].add((r["seat"], r["finding"]))
            rowcount[c] += 1

    table = []
    for build, fset in findings.items():
        v = verdicts.get(build, {"verdict": "UNCLASSIFIED", "why": ""})
        table.append(
            {
                "build": build,
                "verdict": v["verdict"],
                "why": v["why"],
                "findings": len(fset),
                "rows": rowcount[build],
                "seats": sorted({s for s, _ in fset}),
                # Finding ids are written two ways across seats: "S-F3" (seat implied by the
                # file) and "24-F3" (seat already in the id). Prefixing the seat onto an
                # id that already carries it produced "04-04-C4", so check first.
                "sample_findings": sorted(
                    {
                        f if (f.startswith("S-") or f.split("-")[0] == s) else f"{s}-{f}"
                        for s, f in fset
                    }
                )[:12],
            }
        )
    # sort: unresolved first, then by how many findings ride on it
    order = {"UNRESOLVED": 0, "PARTIAL": 1, "RESOLVED": 2, "NOT-A-BUILD": 3, "SETTINGS": 4, "UNCLASSIFIED": 5}
    table.sort(key=lambda t: (order.get(t["verdict"], 9), -t["findings"]))
    json.dump(table, open(args.out, "w"), indent=1)

    for t in table:
        print(f"{t['verdict']:14s} findings={t['findings']:4d} seats={len(t['seats']):2d}  {t['build']}")
    tot = sum(t["findings"] for t in table if t["verdict"] != "SETTINGS")
    unres = sum(t["findings"] for t in table if t["verdict"] in ("UNRESOLVED", "PARTIAL"))
    print(f"\nfindings naming some build: {tot};  riding on an unresolved build: {unres}")


if __name__ == "__main__":
    main()
