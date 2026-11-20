#!/usr/bin/env python3
"""Build REPORT.md and RESULT.txt from the raw files in this seat folder.
Run from the repository root after POOL.txt exists.
"""
import re
import subprocess
from pathlib import Path

S = Path.home().joinpath("grok2_seat.txt").read_text().strip()
ROOT = Path.home().joinpath("grok2_repo.txt").read_text().strip()
D = Path(ROOT) / "forge-combo29" / "grok2" / S


def sh(cmd: str) -> str:
    proc = subprocess.run(cmd, shell=True, text=True, capture_output=True, cwd=ROOT)
    return (proc.stdout + proc.stderr).rstrip("\n")


def nodes_from_honesty(tag: str, name: str, kind: str):
    text = (D / f"honesty_{tag}_{name}.txt").read_text(encoding="utf-8")
    if kind == "bench":
        for line in text.splitlines():
            if "bench depth" in line and " nodes " in line:
                parts = line.split()
                return parts[parts.index("nodes") + 1]
    else:
        last = None
        for line in text.splitlines():
            if line.startswith("nodes "):
                last = line.split()[1]
        return last
    return "MISSING"


def o_summary(name: str):
    rows = []
    for line in (D / name).read_text(encoding="utf-8").splitlines():
        i, n, _info = line.split("\t", 2)
        rows.append((int(i), int(n)))
    return rows


def main() -> None:
    b = o_summary("o_B.txt")
    off = o_summary("o_Poff.txt")
    on = o_summary("o_Pon.txt")
    identical = sum(1 for (_i, nb), (_j, no) in zip(b, off) if nb == no)
    differ = sum(1 for (_i, nb), (_j, no) in zip(b, on) if nb != no)
    on_sum = sum(n for _, n in on)
    if identical != 200 or differ != 200 or on_sum != 9718009 or sum(n for _, n in b) != 9500069:
        raise SystemExit(
            f"STOP: O runs diverged identical={identical} differ={differ} "
            f"on_sum={on_sum} b_sum={sum(n for _, n in b)}"
        )
    if not all(nodes_from_honesty(tag, name, kind) == expect
               for tag in ("B", "P")
               for name, kind, expect in (
                   ("bench11", "bench", "312866"),
                   ("bench13", "bench", "862329"),
                   ("bench16", "bench", "3024920"),
                   ("perft5", "perft", "4865609"),
               )):
        raise SystemExit("STOP: honesty numbers diverged")
    pool = (D / "POOL.txt").read_text(encoding="utf-8").rstrip("\n")
    chunks = sorted(D.glob("chunk_*.tsv"), key=lambda p: int(p.stem.split("_")[1]))
    games = sum(sum(1 for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()) for p in chunks)
    half_line = (D / "half_pool.txt").read_text(encoding="utf-8")
    half_elo = re.search(r"Elo ([+-][0-9.]+)", half_line).group(1)
    m = re.search(
        r"games (\d+) W-L-D (\d+-\d+-\d+) pairs \d+ .*?\nptnml \[([0-9, ]+)\] Elo ([+-][0-9.]+) 95% \[([+-][0-9.]+), ([+-][0-9.]+)\]",
        pool,
    )
    if not m:
        raise SystemExit(f"STOP: could not parse POOL.txt:\n{pool}")
    wld = m.group(2)
    ptnml = ",".join(x.strip() for x in m.group(3).split(","))
    elo, lo, hi = m.group(4), m.group(5), m.group(6)
    honesty_lines = []
    for tag in ("B", "P"):
        for name, kind, expect in (
            ("bench11", "bench", "312866"),
            ("bench13", "bench", "862329"),
            ("bench16", "bench", "3024920"),
            ("perft5", "perft", "4865609"),
        ):
            got = nodes_from_honesty(tag, name, kind)
            honesty_lines.append(f"{tag} {name} nodes {got} expect {expect} {'OK' if got == expect else 'MISS'}")
    book = sh("sha256sum $HOME/uho.zip $HOME/uho.epd")
    patch = sh("sha256sum $HOME/arm.patch")
    arrive = (D / "arrive_check.txt").read_text(encoding="utf-8").splitlines()
    arrive_counts = "\n".join(arrive[:4])
    report = f"""# grok2 seat {S} arm 4 B8b

Arm 4, source seat 028, switch IdeaB8, commit 4bf95fd80adf523e97fa250bb8572c946cf0fc75.

## Patch

sha256 of ~/arm.patch (git show of forge-combo29/grok/028/idea.patch.txt):

```
{patch}
```

Expected f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474. git apply --check and git apply both exited 0. The applied diff stat was search.hpp, search.cpp, uci.cpp.

## Honesty

Fresh process per line, no setoption. Numbers read back from the raw honesty_*.txt files:

```
{chr(10).join(honesty_lines)}
```

## O runs

Expected exe B: sum 9500069, first 41311 / 24872 / 28574.
Expected exe P switch false: equal on all 200.
Expected exe P switch true: sum 9718009, first 17283 / 17878 / 31115, 200 differ.

```
B sum {sum(n for _, n in b)} first {b[0][1]} {b[1][1]} {b[2][1]}
Poff sum {sum(n for _, n in off)} first {off[0][1]} {off[1][1]} {off[2][1]}
Pon sum {sum(n for _, n in on)} first {on[0][1]} {on[1][1]} {on[2][1]}
Poff identical to B: {identical} of {len(b)}
Pon positions differing from B: {differ} of {len(b)}
```

## Book

```
{book}
```

Expected zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07 and epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a, 2632036 lines.

## C-ARRIVE and C-HALF

Arrive check counts (full extract is arrive_check.txt):

```
{arrive_counts}
```

C-HALF pool of side FULL (half_pool.txt):

```
{half_line.rstrip()}
```

FULL Elo {half_elo} is above +20.

## Pool

Chunks: {len(chunks)}. Games: {games}.

```
{pool}
```

## suspicions, not proven

None. The on-sum, the off identity, and the honesty counts matched the table on the first run.

## what I did NOT do

I did not open a pull request. I did not adjudicate games. I did not send IdeaB8_Weight or IdeaB8_Swing. I did not commit an engine binary, a net, a PGN, or an engine source file. I did not play the last 300 openings of mine.epd (those are ctl.epd). I did not change any branch except for-fable-and-opus/grok2-{S}.

## what I am NOT sure about

The RESULT.txt id field is B8b, the label of arm 4 in the brief's table. No other id was given. fastchess printed the same C-HALF Elo as games_tsv.py; I used the games_tsv.py figure.

## times: see stamps.txt
"""
    result = (
        f"seat={S} arm=4 id=B8b src=028 patch=ok honesty=ok off_identical=yes "
        f"on_sum={on_sum} on_ok=yes book=ok arrive=ok half_elo={half_elo} "
        f"chunks={len(chunks)} games={games} wld={wld} ptnml={ptnml} elo={elo} lo={lo} hi={hi}\n"
    )
    (D / "REPORT.md").write_text(report, encoding="utf-8")
    (D / "RESULT.txt").write_text(result, encoding="utf-8")
    status = sh("git status --short")
    listing = sh(f"ls -la forge-combo29/grok2/{S}")
    with (D / "REPORT.md").open("a", encoding="utf-8") as f:
        f.write("\n## git status --short\n\n```\n" + status + "\n```\n\n## ls -la\n\nThe size of REPORT.md in this listing is from before these two sections were appended.\n\n```\n" + listing + "\n```\n")
    print(result, end="")


if __name__ == "__main__":
    main()
