#!/usr/bin/env python3
"""Map findings to the build identifier each one stands on.

The unit of a dependency is a ROW, not a file. A seat report is a table of findings
and one row of it is one claim; a file that mentions a build sha in its header does
not make every row depend on it. So this script splits each report into rows and
attaches the build references it finds IN THAT ROW's text, which is the same
reading discipline the findings document asks for.

Row boundaries used, in this order of preference:
  * a markdown table row:            | S-F1 | ... |
  * a heading followed by its body:  "### S-F1" / "**07-F2**"
  * a numbered/bulleted finding line

Output: evidence/finding_rows.json  -- one record per (seat, finding id, build ref).
"""
import argparse
import collections
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pathsafe

SWARM_PATH = re.compile(r"^forge-combo29/swarm/(\d+)/")

# A finding id as the seats actually write them: 27-F3, S-F3, S-C6, 08-F22, 19-F17.
FINDING_ID = re.compile(r"\b(?:S-)?(?:[FCVP]-\d+[a-z]?|\d{2}-[A-Z]?\d+[a-z]?)\b")

# Build references, split by kind. The hex list is DATA, taken from the identifier
# census (enumerate_builds.py -> evidence/identifiers.json), so a hash found anywhere
# in the corpus is searched for everywhere. A hardcoded list here would silently miss
# any hash the census discovered later -- which is exactly what happened on the first
# pass, when five binary sha256s were absent from this table.
STATIC_REFS = [
    ("named_build", re.compile(r"\bPC\s?r(\d{1,3})(?![0-9])", re.I)),
    ("settings_label", re.compile(r"\bPC( ?20)\b")),
    ("commit", re.compile(r"\b6b98f217[0-9a-f]{0,32}\b", re.I)),
    ("base_label", re.compile(r"\bbase\b", re.I)),
    ("branch_label", re.compile(r"integrate/combo29-all|handoff/fable-opus", re.I)),
    # "the owner's PC" only matters when the row is ABOUT what the PC computes with
    # its own net. A bare mention of the owner (in a sentence about policy, or a
    # sentence like "the owner's PC plays this") is not a build reference and made 31
    # findings look net-dependent when they were not. So require the NET.
    # Kept as a regex. A rewrite to a "linear" predicate was measured and DID change
    # the result (874 -> 871 findings), because the regex consumes through the first
    # "net" after an "owner" and the hand-rolled version matched a second one. A
    # warning-level lint is not worth changing the audit's answer for, so this stays
    # and CI's warning is accepted -- see STATUS.md.
    ("owner_label", re.compile(r"owner'?s?[^.\n]{0,30}\bnet\b", re.I)),
    # Prose build DESCRIPTORS. These are build identifiers in the weak sense: they
    # say which engine was measured without naming an artefact anyone can check.
    # Counted separately, because "ASan+UBSan build" cannot be resolved to bytes
    # even in principle -- the reports never record the flag set or the hash.
    ("descriptor", re.compile(r"\bASan\s*\+?\s*UBSan\b")),
    ("descriptor", re.compile(r"\bTSan\b")),
    ("descriptor", re.compile(r"-D_GLIBCXX_DEBUG\b")),
]

# "PC r115" is a line-wrap artefact of "PC r11" + "5" in one report, not a build.
NOT_A_BUILD = {"PC r115", "PC r0"}


def load_hash_refs(identifiers_path):
    """Every hex identifier the census found, as a prefix regex."""
    import json as _json

    if not os.path.exists(identifiers_path):
        return []
    data = pathsafe.load_json(identifiers_path, os.getcwd())
    seen, refs = set(), []
    for row in data["rows"]:
        tok = row["identifier"]
        if not re.fullmatch(r"[0-9a-f]{7,64}", tok or ""):
            continue
        if row["roles_hint"] if "roles_hint" in row else False:
            continue
        # Only hashes that carry hex letters. A pure-digit run is a node count, a
        # date or a line number, not an identifier -- requiring at least one [a-f]
        # is what removes `20261114` and `218150726` from the table.
        if not re.search(r"[a-f]", tok):
            continue
        if len(tok) < 8:
            continue
        key = tok[:12]
        if key in seen:
            continue
        seen.add(key)
        refs.append((row["role"], re.compile(r"\b" + tok[:12] + r"[0-9a-f]{0,52}\b", re.I)))
    return refs


BUILD_REFS = STATIC_REFS

BUILDISH_LINE = re.compile(
    r"sha256|PC\s?r\d|PC20|6b98f217|base build|on the base|e06310ec|068f0927|d6bd72c5|Build(?:s)? used|settings",
    re.I,
)


def git(*a, repo):
    return subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True, errors="replace")


def split_rows(text):
    """Yield (finding_id_or_None, row_text) for each finding-shaped row."""
    rows = []
    # markdown table rows with a leading id cell
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and FINDING_ID.fullmatch(cells[0].replace("*", "").strip()):
                rows.append((cells[0].replace("*", "").strip(), " | ".join(cells)))
    if rows:
        return rows
    # fallback: heading/paragraph split
    cur_id, buf = None, []
    for line in text.splitlines():
        m = re.match(r"^\s*(?:#{1,6}\s*)?\*{0,2}((?:S-)?(?:[FCVP]-\d+[a-z]?|\d{2}-[A-Z]?\d+[a-z]?))\*{0,2}", line)
        if m:
            if cur_id:
                rows.append((cur_id, "\n".join(buf)))
            cur_id, buf = m.group(1), [line]
        elif cur_id:
            buf.append(line)
    if cur_id:
        rows.append((cur_id, "\n".join(buf)))
    return rows


def refs_in(text, refs=BUILD_REFS):
    found = []
    for kind, rx in refs:
        for m in rx.finditer(text):
            g = m.group(0).lower()
            if kind == "named_build":
                found.append(("PC r" + m.group(1), kind))
            elif kind == "descriptor":
                found.append((g, kind))
            elif kind == "settings_label":
                found.append(("PC20 (settings, not a build)", kind))
            elif kind == "base_label":
                found.append(("base (6b98f217)", kind))
            else:
                found.append((g, kind))
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/agent/repos/dwqww")
    ap.add_argument(
        "--cache",
        default=None,
        help="scratch dir for extracted blobs (default: a fresh private temp dir)",
    )
    ap.add_argument("--out", default="evidence")
    ap.add_argument("--identifiers", default="evidence/identifiers.json")
    args = ap.parse_args()

    listing = git("rev-list", "--all", "--objects", repo=args.repo).stdout.splitlines()
    pairs = []
    for line in listing:
        p = line.split(maxsplit=1)
        if len(p) == 2 and p[1].startswith("forge-combo29/swarm/"):
            pairs.append((p[0], p[1]))
    blobs = sorted({p[0] for p in pairs})

    # read texts
    texts = {}
    for s in range(0, len(blobs), 400):
        part = blobs[s : s + 400]
        out = subprocess.run(
            ["git", "cat-file", "--batch"], cwd=args.repo,
            input="\n".join(part).encode(), capture_output=True,
        ).stdout
        i = 0
        while i < len(out):
            nl = out.index(b"\n", i)
            f = out[i:nl].decode().split()
            if len(f) < 3:
                i = nl + 1
                continue
            sha, size = f[0], int(f[2])
            data = out[nl + 1 : nl + 1 + size]
            i = nl + 1 + size + 1
            if b"\x00" not in data[:8192]:
                texts[sha] = data.decode("utf-8", errors="replace")

    # keep the newest blob per path so a superseded file is not counted twice
    newest = {}
    for blob, path in pairs:
        newest.setdefault(path, []).append(blob)

    all_refs = STATIC_REFS + load_hash_refs(args.identifiers)
    row_records = []
    seen = set()
    for path, cands in newest.items():
        m = SWARM_PATH.match(path)
        if not m:
            continue
        seat = m.group(1)
        if not re.search(r"FINDINGS|REPORT|STATUS|SUMMARY|HEADLINE", path):
            continue
        best = None
        for b in cands:
            t = texts.get(b)
            if t and (best is None or len(t) > len(best[1])):
                best = (b, t)
        if not best:
            continue
        for fid, rowtext in split_rows(best[1]):
            refs = [r for r in refs_in(rowtext, all_refs) if r[0] not in NOT_A_BUILD]
            if not refs:
                continue
            key = (seat, fid, path)
            if key in seen:
                continue
            seen.add(key)
            row_records.append(
                {
                    "seat": seat,
                    "finding": fid,
                    "path": path,
                    "build_refs": sorted({r[0] for r in refs}),
                    "ref_kinds": sorted({r[1] for r in refs}),
                    "row_excerpt": rowtext[:4000],
                }
            )

    out_path = pathsafe.checked_path(args.out, os.getcwd(), create=True)
    pathsafe.dump_json(row_records, "finding_rows.json", out_path)

    by_build = collections.Counter()
    for r in row_records:
        for b in r["build_refs"]:
            by_build[b] += 1
    print(f"finding rows with a build reference: {len(row_records)}")
    print(f"distinct build refs in rows: {len(by_build)}")
    for b, n in by_build.most_common(25):
        print(f"  {b:46s} rows={n}")


if __name__ == "__main__":
    main()
