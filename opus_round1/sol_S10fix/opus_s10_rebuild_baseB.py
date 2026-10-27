#!/usr/bin/env python3
"""S10-3 helper: rebuild Sol's base B source tree (and the ImprovingRazorGuard patch on it) from git objects.

Sol's base B (`01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src`) is not on the PC as a folder, but every
one of its files is in the repository's object database (AL1 tree 294dbed3 = L except the net, the h256_e12 net at
f4911f27, and Sol's own checkpoints on commit 17aa0cae). This tool:
  1. reads Sol's frozen per-file sha256 list for base B (`original_source_freezes.B` in his S10 patchcheck v3 result),
  2. finds a blob with exactly that sha256 for every path (first at the same path in a few known commits, then any blob
     of the same basename anywhere in the object database),
  3. writes the tree read-only-sourced into --out (must not exist), and reports matched / missing paths,
  4. optionally applies a patch with `git -c core.autocrlf=false apply` (LF kept; no .orig/.rej backups) and checks the patched files against Sol's
     post-apply freeze row (kind=source_freeze, feature, base B).
Nothing is written outside --out; the repository is only read.
usage: opus_s10_rebuild_baseB.py --repo R --out DIR [--patch P --feature improving_razor] [--json result.json]
"""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path

SOL_COMMIT = "17aa0cae"
PATCHCHECK = ("validation/forge_sol_pack31_20261025/forge_sol_after_S09_continuation_20261026/S10/"
              "forge_sol_S10_patchcheck_v3_result_20261026.json")
KNOWN_COMMITS = ("294dbed3", "f4911f27", "1ab50b2d")


def git(repo, *args, binary=False):
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True)
    return out.stdout if binary else out.stdout.decode("utf-8", "replace")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob_index(repo):
    """basename -> list of (blob id, path) over every object reachable from any ref."""
    index = {}
    for line in git(repo, "rev-list", "--all", "--objects").splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2 and parts[1]:
            index.setdefault(parts[1].rsplit("/", 1)[-1], []).append((parts[0], parts[1]))
    return index


def find_blob(repo, path, want, index, cache):
    for commit in KNOWN_COMMITS:
        try:
            data = git(repo, "show", f"{commit}:{path}", binary=True)
        except subprocess.CalledProcessError:
            continue
        if sha(data) == want:
            return data, f"{commit}:{path}"
    for blob, where in index.get(path.rsplit("/", 1)[-1], []):
        if blob not in cache:
            try:
                kind = git(repo, "cat-file", "-t", blob).strip()
            except subprocess.CalledProcessError:
                kind = "?"
            cache[blob] = git(repo, "cat-file", "blob", blob, binary=True) if kind == "blob" else None
        data = cache[blob]
        if data is not None and sha(data) == want:
            return data, f"blob {blob} ({where})"
    return None, None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--base", default="B", choices=("L", "Lprime", "B"))
    ap.add_argument("--patch")
    ap.add_argument("--feature", default="improving_razor")
    ap.add_argument("--json")
    ap.add_argument("--apply-include", action="append", default=[],
                    help="apply only these patch paths (repeatable; e.g. the engine files when docs are absent)")
    a = ap.parse_args(argv)
    repo, out = Path(a.repo), Path(a.out)
    if out.exists():
        raise SystemExit(f"--out {out} exists; refusing to overwrite")
    check = json.loads(git(repo, "show", f"{SOL_COMMIT}:{PATCHCHECK}"))
    freeze = check["original_source_freezes"][a.base]
    index, cache = blob_index(repo), {}
    result = {"base": a.base, "sol_commit": SOL_COMMIT, "patchcheck": PATCHCHECK, "files": len(freeze),
              "matched": {}, "missing": []}
    out.mkdir(parents=True)
    for path, want in sorted(freeze.items()):
        data, where = find_blob(repo, path, want, index, cache)
        if data is None:
            result["missing"].append(path)
            continue
        dst = out / path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        result["matched"][path] = {"sha256": want, "source": where}
    print(f"base {a.base}: {len(result['matched'])}/{len(freeze)} files rebuilt byte-exact; missing: {result['missing']}")
    if a.patch:
        patch = Path(a.patch).resolve()
        include = [f"--include={p}" for p in a.apply_include]
        proc = subprocess.run(["git", "-c", "core.autocrlf=false", "apply", "-p1", "--verbose", *include, str(patch)], cwd=out,
                              capture_output=True, text=True)
        result["apply"] = {"patch": str(patch), "patch_sha256": sha(patch.read_bytes()), "include": a.apply_include, "returncode": proc.returncode,
                           "stdout": proc.stdout, "stderr": proc.stderr}
        print(f"git apply rc={proc.returncode}\n{proc.stderr.strip()}")
        rows = [r for r in check["rows"] if r.get("kind") == "source_freeze" and r.get("feature") == a.feature
                and r.get("base") == a.base]
        if rows:
            after = rows[0]["files"]
            cmp = {}
            for path, want in sorted(after.items()):
                p = out / path
                got = sha(p.read_bytes()) if p.is_file() else None
                cmp[path] = "MATCH" if got == want else ("ABSENT" if got is None else "DIFF")
            result["post_apply_vs_sol"] = cmp
            bad = {k: v for k, v in cmp.items() if v != "MATCH"}
            print(f"post-apply vs Sol's {a.feature}/{a.base} freeze: {len(cmp) - len(bad)}/{len(cmp)} MATCH; other: {bad}")
    if a.json:
        Path(a.json).write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0 if not result["missing"] else 2


if __name__ == "__main__":
    sys.exit(main())
