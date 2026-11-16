#!/usr/bin/env python3
"""instrument_nodes.py : instrument the `go nodes` abort path to find where the wrong mate is published.

Hypothesis (S-F27): with `go nodes N` the search stops mid-iteration and a partial iteration's score is published
as final. The source has a guard for this (`FORGE_FIX_ABORT_PUBLISH`); the observed wrong mate score at
`go nodes 20000` is what the guard exists to prevent.

Instrumentation, stderr only, behind FORGE_NODES_DEBUG:
  A  at the root loop's finished-iteration store:  depth, score, pv_len, nodes, and whether aborted_
  B  in the `aborted_` branch: print whether a partial publish is happening, the score, pv_len, and why
  C  at the final result publication (where result.score is assigned after the loop)
Prints are tagged so the sequence for one `go nodes 20000` search shows exactly which value became final.
"""
import pathlib
import shutil
import subprocess

SRC = pathlib.Path("/agent/repos/pcsrc/forge-combo29")
WORK = pathlib.Path("/agent/repos/dbgnodes")
OUTDIR = pathlib.Path("/agent/repos/dwqww/forge-combo29/swarm/25/debug")

if WORK.exists():
    shutil.rmtree(WORK)
shutil.copytree(SRC, WORK, ignore=shutil.ignore_patterns("tests_*", "docs", "*.zip"))

f = WORK / "src" / "search.cpp"
text = f.read_text()


def sub(old, new, what):
    global text
    if text.count(old) != 1:
        raise SystemExit(f"pattern count {text.count(old)} for {what}")
    text = text.replace(old, new)
    print("instrumented:", what)


# A: the finished-iteration store inside the root loop
sub("""        score = iteration_score;
        result.score = score;
        result.depth = depth;""",
"""        score = iteration_score;
#ifdef FORGE_NODES_DEBUG
        std::cerr << "[NDB finished-iter] depth=" << depth << " score=" << score
                  << " pv_len=" << ss->pv_length << " nodes=" << total_nodes()
                  << " aborted=" << aborted_ << std::endl;
#endif
        result.score = score;
        result.depth = depth;""",
    "A finished-iteration store")

# B: the aborted_ branch that may publish a partial iteration
sub("""        if (aborted_) {
            // A clock or external stop may keep a root move that already raised""",
"""        if (aborted_) {
#ifdef FORGE_NODES_DEBUG
            std::cerr << "[NDB ABORTED] depth=" << depth << " stopped_by_nodes=" << stopped_by_nodes_
                      << " pv_len=" << ss->pv_length << " iteration_score=" << iteration_score
                      << " result.score(before)=" << result.score
                      << " nodes=" << total_nodes() << std::endl;
#endif
            // A clock or external stop may keep a root move that already raised""",
    "B aborted_ branch")

f.write_text(text)
diff = subprocess.run(
    ["diff", "-u", "--label", "a/src/search.cpp", "--label", "b/src/search.cpp",
     str(SRC / "src" / "search.cpp"), str(f)],
    capture_output=True, text=True)
OUTDIR.mkdir(parents=True, exist_ok=True)
patch = OUTDIR / "FORGE_EXPERIMENT_nodes_abort_debug.patch.txt"
patch.write_text(diff.stdout)
print(f"wrote {patch}")
