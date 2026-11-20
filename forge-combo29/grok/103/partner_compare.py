#!/usr/bin/env python3
"""Compare partner-build rows to exe B's raw transcript and to the partner's claimed nodes.

The claim file is 'index nodes' per line, as seat 003 stored O_P_on.nodes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_raw


def claim_nodes(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split()
        rows.append(int(parts[-1]))
    return rows


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: partner_compare.py B_RAW.txt PARTNER_ON.nodes MY_ON.nodes", file=sys.stderr)
        return 2
    base = compare_raw.rows(Path(sys.argv[1]))
    claim = claim_nodes(Path(sys.argv[2]))
    mine = [int(x) for x in Path(sys.argv[3]).read_text().split() if x.strip()]
    print(f"base_count={len(base)} claim_count={len(claim)} mine_count={len(mine)}")
    print(f"base_sum={sum(base)} claim_sum={sum(claim)} mine_sum={sum(mine)}")
    n = min(len(base), len(mine), len(claim))
    vs_base = [i + 1 for i in range(n) if mine[i] != base[i]]
    vs_claim = [i + 1 for i in range(n) if mine[i] != claim[i]]
    print(f"mine_vs_base differ={len(vs_base)} of {n}")
    print(f"mine_vs_partner_claim differ={len(vs_claim)} of {n}")
    if vs_claim[:20]:
        print("claim_mismatch_positions=" + ",".join(str(i) for i in vs_claim[:20]))
    if vs_base[:20]:
        print("base_mismatch_positions=" + ",".join(str(i) for i in vs_base[:20]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
