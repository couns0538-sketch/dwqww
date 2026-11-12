"""Where do the files of interest sit at the branch tips? Read-only: only `git for-each-ref` and `git ls-tree`.
usage: python -I tip_targets.py <bare repo> <hits.tsv> <out.json>
Writes {path: {blob_oid: [branch, ...]}} for
  - the fixed list of paths below (matched by full path or by basename),
  - every path whose blob has an `unsafe_deserialize` hit in hits.tsv.
"""
import collections
import json
import os
import subprocess
import sys

repo, hits, out_path = sys.argv[1:4]
env = dict(os.environ, GIT_NO_LAZY_FETCH="1")

BASENAMES = {
    "instrument_refresh_stats.py", "ci_fetch_tables.sh", "download_tb.sh",
    "mutation_check.py", "mutation_check.sh", "mutants.ps1", "cand_step.ps1", "check_consistency.ps1",
    "make_bundle.ps1", "make_packs.ps1", "collect_evidence.py", "report.py", "synth_qualify.py",
    "forge_sol_S25_outcontract_v2_20261027.py", "recovered_build_h256_e12.ps1", "assemble-bundle.py",
    "label_teacher_games.py", "default_lock_identity_objects.sh", "material_cache_contract.sh",
    "material_cache_lock_identity.sh", "harness_util.py",
}

unsafe_oids = set()
for line in open(hits, encoding="utf-8"):
    f = line.split("\t")
    if f[0] == "unsafe_deserialize":
        unsafe_oids.add(f[2])

refs = subprocess.run(["git", "--git-dir", repo, "for-each-ref", "--format=%(refname)", "refs/heads"],
                      capture_output=True, text=True, env=env, check=True).stdout.split()
found = collections.defaultdict(lambda: collections.defaultdict(list))
unsafe = collections.defaultdict(lambda: collections.defaultdict(list))
for n, ref in enumerate(refs):
    branch = ref[len("refs/heads/"):]
    raw = subprocess.run(["git", "--git-dir", repo, "ls-tree", "-r", "-z", ref], capture_output=True, env=env, check=True).stdout
    for rec in raw.split(b"\0"):
        if not rec:
            continue
        meta, path = rec.split(b"\t", 1)
        mode, kind, oid = meta.decode().split()
        path = path.decode("utf-8", "replace")
        if os.path.basename(path) in BASENAMES:
            found[path][mode + " " + oid].append(branch)
        if oid in unsafe_oids:
            unsafe[path][oid].append(branch)
json.dump({"branches": len(refs), "targets": found, "unsafe_deserialize": unsafe}, open(out_path, "w", encoding="utf-8"), indent=0)
print("branches", len(refs), "target paths", len(found), "unsafe paths", len(unsafe))
for path in sorted(found):
    variants = found[path]
    print(f"{sum(len(v) for v in variants.values()):>4} branches  {len(variants)} variant(s)  {path}")
