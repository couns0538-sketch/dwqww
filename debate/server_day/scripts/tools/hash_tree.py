"""Fable 2026-11-23, W5 of FINAL_PLAN_2311.md: a hash list of a folder's files that reads the same on the PC and on
Linux (sha256, two spaces, the path with forward slashes, sorted by path). Standard library only.

    hash_tree.py <root folder> <new list file> <sub folder or file> [more ...]     write the list
    hash_tree.py <root folder> - <sub ...> == <known list file>                     compare, exit 1 on a difference

The last line of a list is `digest <sha256 of all lines before it>`: one value to quote for the whole tree.
"""
import hashlib
import sys
from pathlib import Path


def listing(root: Path, subs: list[str]) -> list[str]:
    files = []
    for s in subs:
        p = root / s
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files += [f for f in p.rglob("*") if f.is_file()]
        else:
            raise SystemExit(f"STOP: {p} is neither a file nor a folder")
    rows = []
    for f in sorted(files, key=lambda f: f.relative_to(root).as_posix()):
        rows.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(root).as_posix()}")
    rows.append("digest " + hashlib.sha256(("\n".join(rows) + "\n").encode("utf-8")).hexdigest())
    return rows


def main() -> int:
    a = sys.argv[1:]
    if len(a) < 3:
        print(__doc__)
        return 2
    root, out = Path(a[0]), a[1]
    if "==" in a:
        i = a.index("==")
        subs, known = a[2:i], Path(a[i + 1])
        got = listing(root, subs)
        want = known.read_text(encoding="utf-8").split("\n")
        want = [w.rstrip("\r") for w in want if w.strip()]
        if got == want:
            print(f"hash_tree: EQUAL to {known.name}: {len(got) - 1} files, {got[-1]}")
            return 0
        gs, ws = set(got[:-1]), set(want[:-1])
        print(f"hash_tree: DIFFERENT from {known.name}: {len(gs - ws)} lines only here, {len(ws - gs)} only in the known list")
        for x in sorted(gs - ws)[:5]:
            print("  here : " + x)
        for x in sorted(ws - gs)[:5]:
            print("  known: " + x)
        return 1
    if out == "-":
        print(__doc__)
        return 2
    o = Path(out)
    if o.exists():
        print(f"STOP: {o} exists")
        return 2
    rows = listing(root, a[2:])
    o.write_bytes(("\n".join(rows) + "\n").encode("utf-8"))
    print(f"hash_tree: {len(rows) - 1} files, {rows[-1]} -> {o.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
