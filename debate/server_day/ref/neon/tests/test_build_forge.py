"""Neon 2026-11-23, self-test for ref/neon/build_forge.py (D10, N16, section 7 row 5).

    python3 -I -B test_build_forge.py <source dir> <net.fnn3> <workloads dir> <known dir> <NEW work folder>

Tests on real frozen source (including a work path WITH SPACES):
 B1  existing --work-dir refused (rc=2)
 B2  PLANT=bad_source_hash fails before compiling (rc=1)
 B3  PLANT=profile_error fails during profile run before pass 2 (rc=1)
 B4  PLANT=missing_profile fails pass 2 under -Werror=missing-profile (rc=1)
 B5  PLANT=other_source fails pass 2 under -Werror=coverage-mismatch (rc=1)
 B6  clean plain_o3_lto + pgo_lto build (path with spaces) matches verify.json, startup.json, n12_batch.json,
     and runs a small interleaved 2-worker D10 self-play comparator proving bit-identical game digests
"""
import json
import subprocess
import sys
from pathlib import Path

if len(sys.argv) != 6:
    print(__doc__)
    sys.exit(2)

SRC, NET, WL, KN, WORK = (Path(a).resolve() for a in sys.argv[1:6])
if WORK.exists():
    print(f"STOP: {WORK} already exists (pass a NEW work folder)")
    sys.exit(2)
WORK.mkdir(parents=True)

SCRIPT = Path(__file__).resolve().parent.parent / "build_forge.py"
results = []


def check(name: str, ok, detail="") -> None:
    results.append((name, bool(ok)))
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f": {str(detail)[:260]}" if not ok and detail != "" else ""), flush=True)


def run_build(out_dir: Path, extra: list) -> tuple:
    cmd = [
        sys.executable, "-I", "-B", str(SCRIPT),
        "--variant", "avx2_pext",
        "--source", str(SRC),
        "--net", str(NET),
        "--workloads", str(WL),
        "--known", str(KN),
        "--work-dir", str(out_dir),
        "--jobs", "4",
        *extra,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=600, check=False)
    rep = None
    rf = out_dir / "build_report.json"
    if rf.is_file():
        rep = json.loads(rf.read_text(encoding="ascii"))
    return p.returncode, p.stdout.strip(), p.stderr.strip(), rep


# B1: existing work dir refused
b1 = WORK / "b1_exists"
b1.mkdir()
rc, out, err, _ = run_build(b1, ["--modes", "plain_o3"])
check("B1 existing --work-dir refused (rc=2)", rc == 2, (rc, out, err))

# B2: bad_source_hash fails before compile
rc, out, err, rep = run_build(WORK / "b2_bad_src", ["--modes", "plain_o3", "--plant", "bad_source_hash"])
check("B2 PLANT=bad_source_hash refused before compiling", rc == 1 and "SOURCE.sha256 mismatch" in err and rep is None, (rc, err))

# B3: profile_error fails during profile run before pass 2
rc, out, err, rep = run_build(WORK / "b3_prof_err", ["--modes", "pgo_nolto", "--plant", "profile_error"])
check("B3 PLANT=profile_error fails during profile run (unknown option refused)",
      rc == 1 and "profile run failed" in err and rep is None, (rc, err))

# B4: missing_profile fails pass 2 under -Werror=missing-profile
rc, out, err, rep = run_build(WORK / "b4_missing_prof", ["--modes", "pgo_nolto", "--plant", "missing_profile"])
check("B4 PLANT=missing_profile fails pass 2 (-Werror=missing-profile)",
      rc == 1 and "pass 2 compile failed" in err and rep is None, (rc, err))

# B5: other_source fails pass 2 under -Werror=coverage-mismatch
rc, out, err, rep = run_build(WORK / "b5_other_src", ["--modes", "pgo_nolto", "--plant", "other_source"])
check("B5 PLANT=other_source fails pass 2 (-Werror=coverage-mismatch)",
      rc == 1 and "pass 2 compile failed" in err and rep is None, (rc, err))

# B6: clean plain_o3_lto + pgo_lto in a path WITH SPACES + 2-worker D10 self-play comparator
b6 = WORK / "b6 clean spaced"
rc, out, err, rep = run_build(b6, [
    "--modes", "plain_o3_lto,pgo_lto",
    "--bench-workers", "2", "--bench-games", "4", "--bench-reps", "2", "--bench-seed", "b6seed",
])
check("B6 clean plain_o3_lto + pgo_lto (spaced path) passes verify/startup/n12_batch + bit-identical D10 bench",
      rc == 0 and rep is not None
      and rep["modes"]["plain_o3_lto"]["checks"]["n12_batch"]["equal"] is True
      and rep["modes"]["pgo_lto"]["checks"]["n12_batch"]["equal"] is True
      and rep["modes"]["pgo_lto"]["gcda_count"] == len(rep["units"])
      and rep["benchmark"] is not None
      and len(rep["benchmark"]["common_sg_digest"]) == 64
      and rep["benchmark"]["d10_n16_verdict"] in ("pgo_faster", "pgo_slower_use_plain", "inconclusive_gain_not_shown"),
      (rc, out, err))

bad = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(bad)} of {len(results)} checks pass")
print("ALL " + str(len(results)) + " CHECKS PASS" if not bad else "FAILED: " + "; ".join(bad))
sys.exit(1 if bad else 0)
