#!/usr/bin/env python3
"""Enumerate every build identifier in the swarm seat reports and resolve each one.

Mechanical, re-runnable. Reads the whole swarm corpus out of git (not the worktree),
classifies each identifier by ROLE, then resolves it against the object database.

  python3 enumerate_builds.py --repo /agent/repos/dwqww --out ../evidence

Design rules this script obeys (they are the point of the audit):
  * A negative claim about a branch must name a command that ENUMERATES it. Every
    "does not exist" below comes from `git rev-list --all` over every ref, and the
    ref count and commit count are printed beside it.
  * Both refs/remotes/origin/* and refs/tags are enumerated, and that is stated.
  * A binary sha256 is NOT resolved by finding it in git. It is resolved only if a
    rebuild is recorded AND that rebuild is run. "Reproduced" and "recorded" are
    different verdicts and the report keeps them apart.
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

# ---------------------------------------------------------------- git plumbing


def git(*args, repo):
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, errors="replace"
    )


def enumerate_commits(repo):
    """Every commit reachable from every ref, plus the ref census that produced it."""
    rev = git("rev-list", "--all", repo=repo)
    if rev.returncode != 0:
        sys.exit("git rev-list --all failed: " + rev.stderr)
    commits = rev.stdout.split()
    refs = git("for-each-ref", "--format=%(refname)", repo=repo).stdout.split()
    by_kind = collections.Counter()
    for r in refs:
        if r.startswith("refs/remotes/origin/"):
            by_kind["refs/remotes/origin/*"] += 1
        elif r.startswith("refs/tags/"):
            by_kind["refs/tags/*"] += 1
        elif r.startswith("refs/heads/"):
            by_kind["refs/heads/*"] += 1
        else:
            by_kind["other"] += 1
    return commits, refs, by_kind


# ------------------------------------------------------- corpus out of git

SWARM_PATH = re.compile(r"^forge-combo29/swarm/(\d+)/")


def seat_of(path):
    m = SWARM_PATH.match(path)
    return m.group(1) if m else None


def build_corpus(repo, cache_dir):
    """Materialise every text blob that ever lived under forge-combo29/swarm/.

    Uses the full object list, not branch tips, so files deleted from a tip are
    still audited -- a withdrawn report is still a report that made a claim.
    """
    listing = git("rev-list", "--all", "--objects", repo=repo).stdout.splitlines()
    pairs = []
    for line in listing:
        parts = line.split(maxsplit=1)
        if len(parts) == 2 and parts[1].startswith("forge-combo29/swarm/"):
            pairs.append((parts[0], parts[1]))
    ids = sorted({p[0] for p in pairs})
    info = git("cat-file", "--batch-check", repo=repo)
    # batch-check needs stdin; redo with communicate
    proc = subprocess.run(
        ["git", "cat-file", "--batch-check"],
        cwd=repo,
        input="\n".join(ids).encode(),
        capture_output=True,
    )
    kinds = {}
    for line in proc.stdout.decode().splitlines():
        f = line.split()
        if len(f) == 3:
            kinds[f[0]] = (f[1], int(f[2]))
    blobs = [i for i in ids if kinds.get(i, ("", 0))[0] == "blob"]

    pathsafe.checked_path(cache_dir, os.getcwd(), create=True, allow_outside=True)
    texts = {}
    chunk = 400
    for s in range(0, len(blobs), chunk):
        part = blobs[s : s + chunk]
        out = subprocess.run(
            ["git", "cat-file", "--batch"],
            cwd=repo,
            input="\n".join(part).encode(),
            capture_output=True,
        ).stdout
        i = 0
        while i < len(out):
            nl = out.index(b"\n", i)
            head = out[i:nl].decode()
            f = head.split()
            if len(f) < 3:
                i = nl + 1
                continue
            sha, size = f[0], int(f[2])
            data = out[nl + 1 : nl + 1 + size]
            i = nl + 1 + size + 1
            if b"\x00" in data[:8192]:
                continue  # binary
            texts[sha] = data.decode("utf-8", errors="replace")
    return pairs, texts, len(ids), len(blobs)


# ------------------------------------------------------- identifier patterns

# A role is what the document says the token IS. The same digits can appear as a
# commit in one report and a binary sha256 in another, so role is attached to each
# occurrence, never to the token globally.
ROLE_PATTERNS = [
    ("elf_buildid", re.compile(r"BuildId:\s*([0-9a-f]{16,40})", re.I)),
    ("patch_sha256", re.compile(r"patch[^.\n]{0,40}sha256[^0-9a-f\n]{0,20}([0-9a-f]{8,64})", re.I)),
    ("exe_sha256", re.compile(r"(?:exe|binary|engine|build|forge)[^.\n]{0,30}sha256[^0-9a-f\n]{0,20}([0-9a-f]{8,64})", re.I)),
    ("sha256", re.compile(r"sha256[^0-9a-f\n]{0,25}([0-9a-f]{8,64})", re.I)),
    ("sha256_prefix_after", re.compile(r"([0-9a-f]{8,64})[^0-9a-z\n]{0,14}sha256", re.I)),
    ("fnv1a64", re.compile(r"FNV[^0-9a-f\n]{0,30}([0-9a-f]{16})", re.I)),
    # "PC r15" / "PCr15" is a revision label. "PC20" without the r is the settings
    # block (S14 + six options) and is a different kind of thing -- keep them apart,
    # because counting them together is what made an earlier pass read PC20 as a build.
    ("named_build", re.compile(r"\bPC\s?r(\d{1,3})(?![0-9])", re.I)),
    ("commit", re.compile(r"(?:commit|base|HEAD|rev|tree|on)\s*[`'\"\[\]()*]{0,3}([0-9a-f]{7,40})(?![0-9a-f])", re.I)),
]

BARE_SHA = re.compile(r"(?<![0-9a-fA-F])([0-9a-f]{7,40})(?![0-9a-fA-F])", re.I)

# Tokens that are provably NOT identifiers: well-known mixing constants and asm
# immediates. Excluding them is what turns 2,400 noisy matches into a real list.
NOT_IDENTIFIERS = {
    "9e3779b97f4a7c15",  # splitmix64 / golden-ratio increment
    "bf58476d1ce4e5b9",  # splitmix64 mix constant
    "94d049bb133111eb",  # splitmix64 mix constant
    "aa55aa55aa55aa55",  # movabs test pattern seen in a disassembly
    "deadbeef",
}


def classify_occurrences(pairs, texts):
    """(token, role) -> set of (seat, path). Occurrence-level, not token-level."""
    occ = collections.defaultdict(set)
    for blob, path in pairs:
        text = texts.get(blob)
        if not text:
            continue
        seat = seat_of(path)
        for role, rx in ROLE_PATTERNS:
            for m in rx.finditer(text):
                tok = m.group(1).lower()
                if role == "named_build":
                    occ[("PC r" + tok, "named_build")].add((seat, path))
                    continue
                if len(tok) < 7:
                    continue
                if tok in NOT_IDENTIFIERS:
                    continue
                occ[(tok, role)].add((seat, path))
    return occ


# ---------------------------------------------------------------- resolution


def resolve_commit(tok, commits, repo, base):
    """Resolve a token as a commit. Returns (verdict, detail)."""
    hits = [c for c in commits if c.startswith(tok)]
    if not hits:
        # cat-file can see objects that are unreachable from refs; check anyway so a
        # dangling-but-present object is not reported as absent.
        t = git("cat-file", "-t", tok, repo=repo)
        if t.returncode == 0:
            return "UNRESOLVED-format", (
                f"object exists as {t.stdout.strip()} but is not a commit reachable from any ref"
            )
        return "UNRESOLVED", "no commit in `git rev-list --all` starts with this prefix"
    if len(hits) > 1:
        return "AMBIGUOUS", f"{len(hits)} commits share this prefix; a {len(tok)}-char prefix does not pin a build"
    sha = hits[0]
    has_engine = git("cat-file", "-e", f"{sha}:forge-combo29", repo=repo).returncode == 0
    is_base = sha.startswith(base)
    anc = git("merge-base", "--is-ancestor", sha, base, repo=repo).returncode == 0
    desc = git("merge-base", "--is-ancestor", base, sha, repo=repo).returncode == 0
    if is_base:
        rel = "IS the audit base"
    elif anc and desc:
        rel = "same commit as base"
    elif anc:
        rel = "ancestor of base (older tree)"
    elif desc:
        rel = "descendant of base"
    else:
        mb = git("merge-base", sha, base, repo=repo).stdout.strip()
        rel = f"unrelated branch (merge-base {mb[:9]})" if mb else "unrelated (no merge-base)"
    subj = git("log", "-1", "--format=%s", sha, repo=repo).stdout.strip()[:70]
    detail = f"{sha[:12]} | forge-combo29/={'yes' if has_engine else 'NO'} | {rel} | {subj}"
    if not has_engine:
        return "RESOLVED-NO-ENGINE", detail
    return "RESOLVED", detail


def resolve_named_build(tok, named_index):
    """'PC r15' is a label, not a commit. It resolves only if the record pins it."""
    return named_index.get(tok)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/agent/repos/dwqww")
    ap.add_argument("--base", default="6b98f2170a3210e71beed04bbd2553972c253ed7")
    ap.add_argument("--out", default="evidence")
    ap.add_argument(
        "--cache",
        default=None,
        help="scratch dir for extracted blobs; created owner-only if absent "
             "(default: a fresh private temp dir)",
    )
    args = ap.parse_args()

    commits, refs, by_kind = enumerate_commits(args.repo)
    print(f"refs enumerated: {len(refs)}  {dict(by_kind)}", file=sys.stderr)
    print(f"commits reachable from all refs: {len(commits)}", file=sys.stderr)

    cache = args.cache or pathsafe.private_dir("forge-prov-corpus-")
    pairs, texts, n_obj, n_blob = build_corpus(args.repo, cache)
    print(f"swarm objects: {n_obj}  text blobs read: {len(texts)}", file=sys.stderr)

    occ = classify_occurrences(pairs, texts)

    # Named builds: the record pins PC r15 to a binary sha, not to a commit.
    named_index = {
        "PC r15": "label; pinned in FABLE_TO_swarm_5.md to patch sha256 d6bd72c531f785f4 "
                  "and to binary sha256 068f0927...; no commit carries the name",
        "PC20": "settings block (S14 + six options), not a build",
    }

    rows = []
    for (tok, role), places in sorted(occ.items(), key=lambda kv: -len(kv[1])):
        seats = sorted({s for s, _ in places if s})
        if role == "commit" or (role == "sha256" and len(tok) >= 7):
            verdict, detail = resolve_commit(tok, commits, args.repo, args.base)
            if role == "sha256" and verdict == "UNRESOLVED":
                verdict, detail = "NOT-A-COMMIT", "cited as a sha256, not as a commit"
            elif role == "sha256" and verdict == "RESOLVED":
                verdict, detail = "COINCIDES-WITH-COMMIT", detail
        elif role == "named_build":
            d = resolve_named_build(tok, named_index)
            verdict, detail = ("RESOLVED-LABEL", d) if d else ("UNRESOLVED", "unpinned label")
        elif role == "elf_buildid":
            verdict, detail = "NOT-A-COMMIT", "ELF BuildId from a backtrace; identifies a .so or a binary, not a source revision"
        elif role == "fnv1a64":
            verdict, detail = "NOT-A-COMMIT", "FNV-1a 64 hash of a data file, not a build"
        else:
            verdict, detail = "BINARY-OR-ARTEFACT", "sha256 of an artefact; resolvable only by rebuild"
        rows.append(
            {
                "identifier": tok,
                "role": role,
                "seat_reports": len({p for _, p in places}),
                "seats": seats,
                "verdict": verdict,
                "detail": detail,
            }
        )

    out_path = pathsafe.checked_path(args.out, os.getcwd(), create=True)
    pathsafe.dump_json(
        {
            "refs_enumerated": len(refs),
            "refs_by_kind": dict(by_kind),
            "commits_reachable": len(commits),
            "base": args.base,
            "swarm_objects": n_obj,
            "text_blobs": len(texts),
            "rows": rows,
        },
        "identifiers.json",
        out_path,
    )
    print(f"wrote {len(rows)} identifier rows to {args.out}/identifiers.json", file=sys.stderr)


if __name__ == "__main__":
    main()
