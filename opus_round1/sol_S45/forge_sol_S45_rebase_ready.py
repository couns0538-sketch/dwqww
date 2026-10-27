#!/usr/bin/env python3
"""S45 new-lock rebase readiness (lock-agnostic).

  run    --config candidates.json --base-name NAME --base-tree <source tree> [--net NET.inc] [--base-ref d11,...,d22]
         --work <new dir> --out-json r.json --out-md r.md [--depths 11,13,16,20,22] [--precheck-depth 16] [--only a,b]
      Builds the base (the tree, with --net as src/nnue_weights.inc when given), benches it, then for every queued
      candidate in the config: copies the base, checks the patch with BOTH commands (`git apply --check -p1` and GNU
      `patch -p1 -F0 --dry-run`), applies it, builds it with the lock recipe, benches it OFF at all depths against
      the base, and runs the ON precheck:
        tunable                 ON options (and ON build flags if any) at the precheck depth: nodes must DIFFER
                                from OFF (the option still does something on this base);
        node_exact              ON (build flags + options) at all depths: nodes must EQUAL the base;
        fixed_depth_inert       an option that by design does nothing in a fixed-depth search (time management,
                                SMP-only): ON at the precheck depth must EQUAL OFF; its real effect needs a timed or
                                multi-thread test (reported as UNVERIFIED);
        bugfix_node_identical   no option: the OFF bench equal to the base is the check;
        none                    nothing to rebase (reported with its note).
      READY = both apply checks pass, the net file is untouched, build OK with FMA 0, OFF bench == base at every
      depth, and the ON check passes.
  voids  --manifest <copy of forge_gates.json> --results <copy of FORGE_RESULTS.csv> --lock-name NAME [--lock-sha SHA]
         [--code-base NAME] --out-json v.json --out-md v.md
      Classifies every manifest gate for the lock NAME (see classify_gate) and lists the queued gates that are void.

Read-only on every input; writes only the new --work directory and the --out files (never under a PC data dir).
Child processes run at Idle priority on Windows. One compiler or engine process at a time.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

IDLE = 0x00000040 if os.name == "nt" else 0
DEFAULT_BUILD = "/d/grok-pc-data/dwqww/.claude/worktrees/b/tools/build_pc.sh"
TREE_PARTS = ("src", "include", "tests", "bench", "tools")
PROTECTED = ("forge_push", "selfplay_out", "forge_nnue_train", os.path.join("Administrator", "grok-pc"))
KINDS = ("tunable", "node_exact", "fixed_depth_inert", "bugfix_node_identical", "none")


# ------------------------------------------------------------------------------------------------ small helpers

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def refuse_protected(path: Path, what: str) -> None:
    norm = str(Path(path).resolve()).lower()
    for p in PROTECTED:
        if p.lower() in norm:
            raise SystemExit(f"refusing to write {what} under a protected PC data directory: {path}")


def tool(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise SystemExit(f"{name} not found on PATH")
    return found


def copy_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=False)
    for part in TREE_PARTS:
        if (src / part).is_dir():
            shutil.copytree(src / part, dst / part)
    shutil.copyfile(src / "CMakeLists.txt", dst / "CMakeLists.txt")


# ------------------------------------------------------------------------------------------------ patch checks

def check_patch(tree: Path, patch: Path) -> dict:
    """Both commands on an untouched copy; neither changes the tree. git is kept from finding any enclosing repo."""
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(tree.parent.resolve()))
    g = subprocess.run([tool("git"), "apply", "--check", "-p1", "--verbose", str(patch.resolve())], cwd=tree,
                       capture_output=True, text=True, env=env, creationflags=IDLE)
    p = subprocess.run([tool("patch"), "-p1", "-F0", "--dry-run", "--no-backup-if-mismatch", "-i", str(patch.resolve())],
                       cwd=tree, capture_output=True, text=True, creationflags=IDLE)
    out = p.stdout + p.stderr
    return {"git_apply_check": g.returncode == 0, "git_output": (g.stdout + g.stderr).strip()[-2000:],
            "gnu_patch_dry_run": p.returncode == 0, "gnu_output": out.strip()[-2000:],
            "gnu_offset_hunks": len(re.findall(r"with fuzz|offset", out)),
            "gnu_fuzz_hunks": len(re.findall(r"with fuzz", out)),
            "files": sorted(set(re.findall(r"^\+\+\+ b/(\S+)", patch.read_text(encoding="utf-8", errors="replace"), re.M)))}


def apply_patch(tree: Path, patch: Path, use_git: bool) -> None:
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(tree.parent.resolve()))
    cmd = ([tool("git"), "apply", "-p1", str(patch.resolve())] if use_git else
           [tool("patch"), "-p1", "-F0", "--no-backup-if-mismatch", "-i", str(patch.resolve())])
    r = subprocess.run(cmd, cwd=tree, capture_output=True, text=True, env=env, creationflags=IDLE)
    if r.returncode != 0:
        raise RuntimeError(f"apply failed: {r.stdout}{r.stderr}")


# ------------------------------------------------------------------------------------------------ build + bench

def build(tree: Path, exe: Path, flags: list[str], build_script: str, log: Path) -> dict:
    bash = tool("bash")
    r = subprocess.run([bash, build_script, tree.resolve().as_posix(), exe.resolve().as_posix(), *flags],
                       capture_output=True, text=True, creationflags=IDLE)
    log.write_text(r.stdout + r.stderr, encoding="utf-8")
    sha = re.search(r"sha256 ([0-9a-f]{64})", r.stdout)
    fma = re.search(r"count: (\d+)", r.stdout)
    warnings = len(re.findall(r"warning", r.stdout + r.stderr, re.I))
    return {"ok": r.returncode == 0 and exe.exists(), "sha256": sha.group(1) if sha else None,
            "fma": int(fma.group(1)) if fma else None, "warnings": warnings, "flags": flags}


def bench(exe: Path, depths: list[int], options: dict[str, str] | None = None) -> dict:
    """bench at each depth in one engine process; returns {"nodes": {d: n}, "nps": {d: nps}, "option_errors": [...]}."""
    p = subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
                         creationflags=IDLE)

    def send(s: str) -> None:
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(pat: str, seen: list[str] | None = None) -> re.Match:
        rx = re.compile(pat)
        for line in p.stdout:
            if seen is not None:
                seen.append(line.strip())
            m = rx.search(line)
            if m:
                return m
        raise RuntimeError(f"{exe.name} exited before {pat}")

    try:
        send("uci")
        uci: list[str] = []
        wait(r"^uciok", uci)
        for o in ("Threads value 1", "Hash value 16", "OwnBook value false"):
            send("setoption name " + o)
        for k, v in (options or {}).items():
            send(f"setoption name {k} value {v}")
        send("isready")
        seen: list[str] = []
        wait(r"^readyok", seen)
        nodes, nps = {}, {}
        for d in depths:
            send(f"bench {d}")
            m = wait(rf"bench depth {d} nodes (\d+) time (\d+) nps (\d+)")
            nodes[d], nps[d] = int(m.group(1)), int(m.group(3))
        send("quit")
        p.wait(timeout=60)
    finally:
        if p.poll() is None:
            p.stdin.close()
            p.wait(timeout=60)
    advertised = {m.group(1) for l in uci for m in [re.match(r"option name (.+?) type ", l)] if m}
    return {"nodes": nodes, "nps": nps, "option_errors": [l for l in seen if "invalid value" in l],
            "unadvertised_options": sorted(k for k in (options or {}) if k not in advertised)}


# ------------------------------------------------------------------------------------------------ decisions

def on_check(kind: str, off_nodes: dict[int, int], on_nodes: dict[int, int] | None, base_nodes: dict[int, int],
             precheck_depth: int) -> tuple[bool | None, str]:
    """(pass, text). None = not applicable."""
    if kind == "tunable":
        if not on_nodes or precheck_depth not in on_nodes:
            return False, "no ON bench"
        same = on_nodes[precheck_depth] == off_nodes.get(precheck_depth)
        return (not same), (f"d{precheck_depth} ON {on_nodes[precheck_depth]} vs OFF {off_nodes.get(precheck_depth)}: "
                            + ("INERT (ON == OFF)" if same else "ON != OFF"))
    if kind == "fixed_depth_inert":
        if not on_nodes or precheck_depth not in on_nodes:
            return False, "no ON bench"
        same = on_nodes[precheck_depth] == off_nodes.get(precheck_depth)
        return same, (f"d{precheck_depth} ON {on_nodes[precheck_depth]} vs OFF {off_nodes.get(precheck_depth)}: "
                      + ("ON == OFF as designed (effect needs a timed test, UNVERIFIED)" if same
                         else "ON != OFF although the option should be inert at fixed depth"))
    if kind == "node_exact":
        if not on_nodes:
            return False, "no ON bench"
        diff = [d for d in base_nodes if on_nodes.get(d) != base_nodes[d]]
        return (not diff), ("ON == base at all depths" if not diff else f"ON differs at d{','.join(map(str, diff))}")
    if kind == "bugfix_node_identical":
        return None, "no option (fix always on): OFF bench == base is the check"
    return None, "nothing to rebase"


def verdict(row: dict) -> str:
    if row["kind"] == "none":
        return "N/A"
    reasons = []
    if not row.get("git_apply_check"):
        reasons.append("git apply --check fails")
    if not row.get("gnu_patch_dry_run"):
        reasons.append("patch -p1 -F0 fails")
    if row.get("net_touched"):
        reasons.append("patch changes the net")
    if row.get("patch_sha256_mismatch"):
        reasons.append("patch sha256 differs from the config")
    b = row.get("build_off") or {}
    if not b.get("ok"):
        reasons.append("OFF build failed")
    elif b.get("fma") != 0:
        reasons.append(f"FMA {b.get('fma')}")
    if row.get("off_equals_base") is not True:
        reasons.append("OFF bench != base")
    if row.get("on_pass") is False:
        reasons.append("ON check failed: " + row.get("on_text", ""))
    if row.get("option_errors"):
        reasons.append("option errors")
    return "READY" if not reasons else "NOT READY (" + "; ".join(reasons) + ")"


# ------------------------------------------------------------------------------------------------ run

def load_config(path: Path) -> list[dict]:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for c in cfg["candidates"]:
        if c["kind"] not in KINDS:
            raise SystemExit(f"{c['name']}: unknown kind {c['kind']}")
        c = dict(c)
        if c.get("patch"):
            c["patch_path"] = (path.parent / c["patch"]).resolve()
        out.append(c)
    return out


def cmd_run(a: argparse.Namespace, build_fn=build, bench_fn=bench) -> int:
    work = Path(a.work)
    if work.exists():
        raise SystemExit("--work must be a new directory")
    for p in (work, Path(a.out_json), Path(a.out_md)):
        refuse_protected(p, "output")
    for p in (a.out_json, a.out_md):
        if Path(p).exists():
            raise SystemExit(f"{p} exists; outputs must be new files")
    depths = [int(d) for d in a.depths.split(",")]
    pre = a.precheck_depth
    if pre not in depths:
        raise SystemExit("--precheck-depth must be one of --depths")
    cands = load_config(Path(a.config))
    if a.only:
        keep = set(a.only.split(","))
        cands = [c for c in cands if c["name"] in keep]
    work.mkdir(parents=True)
    base_tree = work / "base" / "src_tree"
    copy_tree(Path(a.base_tree), base_tree)
    if a.net:
        shutil.copyfile(a.net, base_tree / "src" / "nnue_weights.inc")
    net_md5 = md5_file(base_tree / "src" / "nnue_weights.inc")
    report = {"tool": "forge_sol_S45_rebase_ready run", "base_name": a.base_name, "base_tree": str(a.base_tree),
              "net": str(a.net) if a.net else "(tree's own)", "net_md5": net_md5, "depths": depths,
              "precheck_depth": pre, "config": str(a.config), "config_sha256": sha256_file(Path(a.config)), "rows": []}
    print(f"# base {a.base_name}: net md5 {net_md5}", flush=True)
    base_build = build_fn(base_tree, work / "base" / "forge_base.exe", [], a.build_script, work / "base" / "build.log")
    report["base_build"] = base_build
    if not base_build["ok"]:
        raise SystemExit("base build failed")
    base_bench = bench_fn(work / "base" / "forge_base.exe", depths)
    report["base_bench"] = base_bench["nodes"]
    if a.base_ref:
        ref = [int(x) for x in a.base_ref.split(",")]
        report["base_ref"] = dict(zip(depths, ref))
        report["base_identity"] = all(base_bench["nodes"][d] == r for d, r in zip(depths, ref))
    print(f"# base bench {[base_bench['nodes'][d] for d in depths]} identity "
          f"{report.get('base_identity', 'n/a (no --base-ref)')} FMA {base_build['fma']}", flush=True)
    for c in cands:
        row = {"name": c["name"], "kind": c["kind"], "gate": c.get("gate", ""), "source": c.get("source", ""),
               "note": c.get("note", ""), "on_options": c.get("on_options", {}), "on_build_flags": c.get("on_build_flags", [])}
        if c["kind"] == "none":
            row["on_pass"], row["on_text"] = on_check("none", {}, None, {}, pre)
            row["verdict"] = verdict(row)
            report["rows"].append(row)
            print(f"{c['name']}: N/A ({c.get('note', '')})", flush=True)
            continue
        patch = c["patch_path"]
        row["patch"] = str(patch)
        row["patch_sha256"] = sha256_file(patch)
        row["patch_sha256_mismatch"] = bool(c.get("patch_sha256")) and c["patch_sha256"] != row["patch_sha256"]
        cdir = work / c["name"]
        tree = cdir / "src_tree"
        copy_tree(base_tree, tree)
        row.update(check_patch(tree, patch))
        if row["git_apply_check"] or row["gnu_patch_dry_run"]:
            apply_patch(tree, patch, use_git=row["git_apply_check"])
            row["applied_with"] = "git apply -p1" if row["git_apply_check"] else "patch -p1 -F0"
            row["net_touched"] = md5_file(tree / "src" / "nnue_weights.inc") != net_md5
            row["build_off"] = build_fn(tree, cdir / "forge_off.exe", [], a.build_script, cdir / "build_off.log")
            if row["build_off"]["ok"]:
                off = bench_fn(cdir / "forge_off.exe", depths)
                row["off_bench"] = off["nodes"]
                row["off_equals_base"] = all(off["nodes"][d] == base_bench["nodes"][d] for d in depths)
                on_nodes = None
                if c["kind"] in ("tunable", "node_exact", "fixed_depth_inert"):
                    exe_on = cdir / "forge_off.exe"
                    if c.get("on_build_flags"):
                        row["build_on"] = build_fn(tree, cdir / "forge_on.exe", c["on_build_flags"], a.build_script,
                                                   cdir / "build_on.log")
                        exe_on = cdir / "forge_on.exe"
                        if not row["build_on"]["ok"] or row["build_on"]["fma"] != 0:
                            row["on_pass"], row["on_text"] = False, "ON build failed or FMA != 0"
                    if row.get("on_pass") is not False:
                        on = bench_fn(exe_on, depths if c["kind"] == "node_exact" else [pre], c.get("on_options", {}))
                        on_nodes = on["nodes"]
                        row["on_bench"] = on_nodes
                        row["option_errors"] = on["option_errors"]
                        row["unadvertised_options"] = on["unadvertised_options"]
                if row.get("on_pass") is not False:
                    row["on_pass"], row["on_text"] = on_check(c["kind"], off["nodes"], on_nodes, base_bench["nodes"], pre)
        row["verdict"] = verdict(row)
        report["rows"].append(row)
        print(f"{c['name']}: git {row['git_apply_check']} gnu {row['gnu_patch_dry_run']} (offset hunks "
              f"{row['gnu_offset_hunks']}) OFF==base {row.get('off_equals_base')} ON {row.get('on_text', '-')} -> {row['verdict']}",
              flush=True)
    Path(a.out_json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    Path(a.out_md).write_text(render_run(report), encoding="utf-8", newline="\n")
    return 0


def render_run(r: dict) -> str:
    d = r["depths"]
    L = [f"### Base `{r['base_name']}` (net md5 `{r['net_md5']}`)", "",
         f"- base bench d{'/'.join(map(str, d))}: {'/'.join(str(r['base_bench'][x]) for x in d)}"
         + (f"; reference {'/'.join(str(r['base_ref'][x]) for x in d)} -> identity "
            f"{'PASS' if r.get('base_identity') else 'FAIL'}" if 'base_ref' in r else "")
         + f"; base build FMA {r['base_build']['fma']}", "",
         "| candidate | kind | gate | git apply --check | patch -p1 -F0 | build OFF (FMA) | OFF bench = base (" + "/".join(f"d{x}" for x in d)
         + ") | ON precheck | verdict |", "|---|---|---|---|---|---|---|---|---|"]
    for row in r["rows"]:
        if row["kind"] == "none":
            L.append(f"| {row['name']} | none | {row['gate'] or '-'} | - | - | - | - | {row['on_text']}: {row['note']} | N/A |")
            continue
        b = row.get("build_off") or {}
        off = row.get("off_bench")
        offs = ("= base" if row.get("off_equals_base") else "/".join(str(off[x]) for x in d)) if off else "-"
        L.append(f"| {row['name']} | {row['kind']} | {row['gate'] or '-'} | {'PASS' if row['git_apply_check'] else 'FAIL'} | "
                 f"{'PASS' if row['gnu_patch_dry_run'] else 'FAIL'}{' (' + str(row['gnu_offset_hunks']) + ' offset)' if row['gnu_offset_hunks'] else ''} | "
                 f"{'OK' if b.get('ok') else 'FAIL'} ({b.get('fma')}) | {offs} | {row.get('on_text', '-')} | {row['verdict']} |")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------------------------------------ void gates

def read_results(path: Path) -> set[str]:
    text = Path(path).read_text(encoding="utf-8-sig")
    return {str(r.get("gate", "")).strip() for r in csv.DictReader(io.StringIO(text)) if r.get("gate")}


def candidate_base(g: dict) -> str:
    """Which lock the candidate exe was built on: manifest fields first, then the exe-name convention."""
    if g.get("ag_rebuilt_on"):
        return str(g["ag_rebuilt_on"])
    exe = str(g.get("exe", ""))
    if exe.endswith("_AL1.exe"):
        return "AL1 tree (exe suffix _AL1)"
    if exe.startswith("forge_h256_"):
        return "h256_e12 code tree + own net (exe name; net-only candidate)"
    if "h256" in exe:
        return "h256_e12 tree (exe name)"
    if exe.endswith(("_epa.exe", "_ep10.exe")) or "ep10" in exe:
        return "ep10 (exe name)"
    return "unknown"


def classify_gate(g: dict, done: set[str], base: dict, lock_name: str, lock_sha: str | None) -> dict:
    """State: DONE (a result row exists), DROPPED, HELD, QUEUED. For a queued/held gate and the lock NAME:
       VALID          opponent is the lock (name or sha) -> stays a promotion gate;
       VOID_OPPONENT  the gate is meant to be measured against the lock (ag_vs_lock or no stated policy) but its
                      opponent is another engine -> its verdict cannot promote over NAME; re-gate vs NAME, new srand;
       OLD_OPPONENT_COMBINE  explicitly kept against an older lock ("keeps old opponent; an H1 goes to COMBINE_LIST")
                      -> informative only for NAME: rebuild on NAME + new gate vs NAME before adoption."""
    gid = str(g.get("gate"))
    status = str(g.get("status", ""))
    ok = str(g.get("ok", ""))
    if gid in done:
        state = "DONE"
    elif status.startswith("DROPPED") or "DROPPED" in ok:
        state = "DROPPED"
    elif status.startswith("HELD"):
        state = "HELD"
    else:
        state = "QUEUED"
    opp = g.get("base_override") or base
    opp_name, opp_sha = str(opp.get("name", "")), str(opp.get("sha256", "")).upper()
    vs_lock = str(g.get("ag_vs_lock", ""))
    # Only the current note counts: a gate rebuilt later quotes its superseded policy after "Old note:".
    notes = (str(g.get("notes", "")).split("Old note:")[0] + " " + str(g.get("driver_note", "")).split("Old note:")[0])
    combine = "COMBINE_LIST" in notes and "keeps old opponent" in notes
    is_lock = opp_name.endswith(lock_name) or opp_name == lock_name or (lock_sha and opp_sha == lock_sha.upper())
    if state in ("DONE", "DROPPED"):
        cls = state
    elif is_lock:
        cls = "VALID"
    elif combine:
        cls = "OLD_OPPONENT_COMBINE"
    else:
        cls = "VOID_OPPONENT"
    return {"gate": gid, "tag": g.get("tag", ""), "exe": g.get("exe", ""), "options": g.get("options", []),
            "state": state, "opponent": opp_name, "opponent_sha8": opp_sha[:8], "ag_vs_lock": vs_lock,
            "candidate_base": candidate_base(g), "class": cls}


def cmd_voids(a: argparse.Namespace) -> int:
    for p in (a.out_json, a.out_md):
        if Path(p).exists():
            raise SystemExit(f"{p} exists; outputs must be new files")
        refuse_protected(Path(p), "output")
    m = json.loads(Path(a.manifest).read_text(encoding="utf-8-sig"))
    done = read_results(Path(a.results))
    rows = [classify_gate(g, done, m["base"], a.lock_name, a.lock_sha) for g in m["gates"]]
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    out = {"tool": "forge_sol_S45_rebase_ready voids", "manifest": str(a.manifest), "manifest_sha256": sha256_file(Path(a.manifest)),
           "results": str(a.results), "results_sha256": sha256_file(Path(a.results)), "lock_name": a.lock_name,
           "lock_sha": a.lock_sha, "label": a.label, "counts": counts, "rows": rows}
    Path(a.out_json).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n")
    Path(a.out_md).write_text(render_voids(out), encoding="utf-8", newline="\n")
    print(json.dumps(counts))
    return 0


def render_voids(v: dict) -> str:
    L = [f"### Queued gates if the lock is `{v['lock_name']}`" + (f" ({v['label']})" if v.get("label") else ""), "",
         "counts: " + ", ".join(f"{k} {n}" for k, n in sorted(v["counts"].items())), "",
         "| gate | tag | state | opponent | candidate built on | class |", "|---|---|---|---|---|---|"]
    for r in v["rows"]:
        if r["class"] in ("DONE", "DROPPED"):
            continue
        L.append(f"| {r['gate']} | {r['tag']} | {r['state']} | {r['opponent']} ({r['opponent_sha8']}) | {r['candidate_base']} | {r['class']} |")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------------------------------------ main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--config", required=True)
    r.add_argument("--base-name", required=True)
    r.add_argument("--base-tree", required=True)
    r.add_argument("--net")
    r.add_argument("--base-ref")
    r.add_argument("--work", required=True)
    r.add_argument("--out-json", required=True)
    r.add_argument("--out-md", required=True)
    r.add_argument("--depths", default="11,13,16,20,22")
    r.add_argument("--precheck-depth", type=int, default=16)
    r.add_argument("--only")
    r.add_argument("--build-script", default=DEFAULT_BUILD)
    v = sub.add_parser("voids")
    v.add_argument("--manifest", required=True)
    v.add_argument("--results", required=True)
    v.add_argument("--lock-name", required=True)
    v.add_argument("--lock-sha")
    v.add_argument("--label", default="")
    v.add_argument("--out-json", required=True)
    v.add_argument("--out-md", required=True)
    a = ap.parse_args(argv)
    return cmd_run(a) if a.cmd == "run" else cmd_voids(a)


if __name__ == "__main__":
    sys.exit(main())
