"""Reviewer-owned read-only JSON/hash reader; no reviewed code execution."""
import ast
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat

ROOT = Path("/workspace/dwqww")
E = ROOT / "validation/hosted-nearest-pawn-performance-20261021"
OUT = E / "capture-support-independent-review"
PKG = ROOT / ".github/hosted-nearest-pawn-performance"
BASE = "fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e"
CAND = "2e151d019bc58dff2ab4e76e99ef99516af8d222"
HELPER = "461a65d2fecdf208994749cb0d44c56bf2f8524610f211a4bf76bd019c25704d"
DRIVER = "6584ec98e24d74be636e208bfc30097a67543b992c929236405ffbddadb972fc"
checks = []
frozen = {}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path):
    assert path.is_file() and not path.is_symlink(), str(path)
    info = path.stat()
    return dict(sha256=sha(path), bytes=info.st_size,
                mode=stat.S_IMODE(info.st_mode))


def check(name, condition):
    checks.append(dict(name=name, passed=bool(condition)))


def read(path):
    return json.loads(path.read_bytes())


def freeze(path):
    frozen[str(path)] = identity(path)


started = datetime.datetime.now(datetime.timezone.utc).isoformat()
seal = E / "capture-support/SHA256SUMS"
check("Exact closed support seal",
      sha(seal) == "b66919d52a5eaf8eb1e03b62bf766bba1d9062e416b9e33bdce460cd10284734")
freeze(seal)
rows = {}
for line in seal.read_text().splitlines():
    digest, name = line.split("  ", 1)
    path = PurePosixPath(name)
    assert name not in rows and not path.is_absolute() and ".." not in path.parts
    assert re.fullmatch("[0-9a-f]{64}", digest)
    rows[name] = digest
    check("Sealed original: " + name, sha(E / name) == digest)
    freeze(E / name)
check("Exactly 24 sealed support originals", len(rows) == 24)
check("Exact reviewed driver", sha(E / "capture_actual_five.py") == DRIVER)
check("Actual frozen helper equals package and trusted executed461a",
      sha(E / "capture-support/owned_process.frozen.py")
      == sha(PKG / "owned_process.py") == HELPER)
for name in ["capture_actual_five.py", "test_capture_preparation.py",
             "capture-support/verify_prototype_scope.py"]:
    ast.parse((E / name).read_bytes(), filename=name)
    check("AST parses without import: " + name, True)

initial = E / "independent-review-initial/REVIEW.json"
check("Initial disabled review unchanged",
      sha(initial) == "535642f3a85294da825582a5599b874190824354c57d30179fb8a906675f039f")
freeze(initial)
initial_review = read(initial)
for name, key in [
    (PKG / "protocol.json", "protocol_sha256"),
    (ROOT / ".github/workflows/forge-hosted-nearest-pawn-performance.yml", "workflow_sha256"),
    (PKG / "PACKAGE-SHA256SUMS", "package_inventory_sha256"),
]:
    check("Initial packet unchanged: " + name.name, sha(name) == initial_review[key])
    freeze(name)
cfg = read(PKG / "protocol.json")
check("DRAFT packet and empty maps remain",
      cfg["status"] == "DRAFT_BLOCKED_PREPARATION_ONLY"
      and cfg["workflow_status"] == "DISABLED"
      and cfg["correctness_evidence_sha256"] == cfg["transport_captures"] == {})
example = read(E / "ROOT-CAPTURE-AUTHORIZATION.example.json")
check("Example cannot authorize",
      example["authorized"] is False and example["status"] == "EXAMPLE_ONLY_NOT_AUTHORIZED"
      and example["input_sha256"] == {} and example["driver_sha256"] == DRIVER)

status = read(E / "CAPTURE-SUPPORT-STATUS.json")
check("Support remains prepared with zero captures",
      status["status"] == "PREPARED_CAPTURE_SUPPORT_ONLY_NOT_AUTHORIZED"
      and status["engines_compilers_benchmarks_git_hosted"] == 0
      and status["root_authorization_exists"] is False
      and status["actual_captures_directory_exists"] is False)
check("Original offline progression retained",
      [(r["tests"], r["exit_code"]) for r in status["offline_attempts"]]
      == [(9, 1), (9, 0), (10, 0)])
for attempt, count, passed in [(1, 9, 8), (2, 9, 9), (3, 10, 10)]:
    text = (E / f"capture-preparation-attempt{attempt}.stderr").read_text()
    check(f"Original support attempt{attempt} output",
          f"Ran {count} tests" in text
          and sum(line.endswith(" ... ok") for line in text.splitlines()) == passed
          and (text.rstrip().endswith("OK") if attempt > 1 else "FAILED (errors=1)" in text))
test_tree = ast.parse((E / "test_capture_preparation.py").read_bytes())
names = [n.name for c in test_tree.body if isinstance(c, ast.ClassDef)
         for n in c.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
last_log = (E / "capture-preparation-attempt3.stderr").read_text()
check("Ten test declarations match saved ten passing test names",
      len(names) == 10 and all(re.search("^" + re.escape(n) + r" \(.*\) \.\.\. ok$",
                                       last_log, re.M) for n in names))
test_text = (E / "test_capture_preparation.py").read_text()
check("Derived mocks explicitly excluded from actual qualification",
      "DERIVED root21/Windows21 proof mocks" in test_text
      and "These dictionaries are never written as actual qualification evidence" in test_text
      and "Controlled missing Windows21" in test_text)

plans = {
    "baseline": dict(commit=BASE, source=Path("/workspace/.cloud-setup/pawn-span-fill-native-source"),
                     build=Path("/workspace/.cloud-setup/pawn-span-fill-native-release"),
                     native=ROOT / "validation/pawn-span-fill-native-20261020",
                     proof=ROOT / "validation/pawn-span-fill-20261020/root-verification/NATIVE.json",
                     files=75, ctests=12, version=20),
    "candidate": dict(commit=CAND, source=Path("/workspace/.cloud-setup/nearest-pawn-native-source"),
                      build=Path("/workspace/.cloud-setup/nearest-pawn-native-release"),
                      native=ROOT / "validation/nearest-pawn-native-20261020",
                      proof=ROOT / "validation/nearest-pawn-distance-20261020/root-verification/NATIVE.json",
                      files=76, ctests=13, version=21),
}
inspection = read(E / "CAPTURE-PREPARATION.json")
windows_observed = {}
for label, plan in plans.items():
    native, proof_path = plan["native"], plan["proof"]
    final_path, manifest = native / "FINAL-RECEIPT.json", native / "ROOT-FROZEN-SOURCE-GATES.json"
    final, proof = read(final_path), read(proof_path)
    expected = read(manifest)["inputs"]
    for path in [final_path, proof_path, manifest, native / "EVIDENCE-SHA256SUMS"]:
        freeze(path)
    check(label + " actual complete native gates",
          final["status"] == "STABLE" and final["source_commit"] == plan["commit"]
          and proof["source_commit"] == plan["commit"]
          and proof["status"] == f"PASS_ROOT_FULL_NATIVE{plan['version']}_ORIGINALS_AND_GIT_SOURCE_REVIEW"
          and (final["native_ctests"], final["default_tsan_active_checks"],
               final["exact_cold_warm_searches"]) == (plan["ctests"] * 3, 8, 56)
          and (proof["ctest"], proof["active_uci"], proof["exact_cold_warm_searches"])
          == (plan["ctests"] * 3, 8, 56))
    check(label + " genuine root hashes and process closure",
          proof["native_final_receipt_sha256"] == sha(final_path)
          and proof["native_manifest_sha256"] == sha(native / "EVIDENCE-SHA256SUMS")
          and proof["exact_evidence_tree_verified"] is True
          and proof["engine_gate_retries"] == 0
          and proof["native_profile_attempts"] == dict(release=1, asan=1, tsan=1)
          and final["all_owned_processes_closed"] is True
          and final["independent_audit_failed"] == 0)
    check(label + " actual revision-specific receipt fields",
          final.get("engine_tests_builds_failed") == 0 if plan["version"] == 20
          else final["driver_source_mutations_after_start"] is False
          and final["all_originals_retained"] is True)
    check(label + " complete source inventory",
          len(expected) == plan["files"]
          and {f.relative_to(plan["source"]).as_posix() for f in plan["source"].rglob("*")
               if f.is_file()} == set(expected))
    for name, digest in expected.items():
        path = plan["source"] / name
        check(label + " frozen source bytes: " + name, sha(path) == digest)
        freeze(path)
    profiles = final["native_profiles"]
    check(label + " exact native profiles", set(profiles) == {"release", "asan", "tsan"})
    for profile in ["release", "asan", "tsan"]:
        path = native / f"frozen-{profile}-attempt1/summary.json"
        entry, receipt = profiles[profile], read(path)
        freeze(path)
        check(label + " " + profile + " actual first attempt and receipt",
              type(entry["attempts"]) is int and entry["attempts"] == 1
              and entry["ctest_count"] == plan["ctests"] and entry["status"] == "PASS"
              and entry["receipt_sha256"] == sha(path) and receipt["status"] == "PASS"
              and receipt["source_commit"] == plan["commit"]
              and len(receipt["ctest_names"]) == plan["ctests"])
        if plan["version"] == 21:
            check("Candidate " + profile + " nearest finite checks",
                  (entry["nearest_pawn_checks"], entry["nearest_target_sets"],
                   entry["nearest_constexpr_assertions"]) == (791680, 395840, 6))
        if profile == "release":
            check(label + " live inspected Release source correspondence",
                  receipt["source_export"] == str(plan["source"])
                  and receipt["source_sha256_before_tests"]
                  == receipt["source_sha256_after_tests"] == expected
                  and receipt["actual_ctest_commands"] == receipt["expected_ctest_commands"]
                  and inspection["sources"][label]["source_manifest_sha256"] == sha(manifest)
                  and inspection["sources"][label]["build_receipt_sha256"] == sha(path))
            for name in ["forge", "libforge_core.a"]:
                artifact = plan["build"] / name
                check(label + " original artifact " + name,
                      sha(artifact) == receipt["binary_sha256_after"][name]
                      == inspection["sources"][label]["binary_sha256_before"][name])
                freeze(artifact)
    active_path = native / "active-uci-wrapper-attempt1/COMMAND.json"
    active = read(active_path)
    freeze(active_path)
    check(label + " active UCI gate",
          active["status"] == "PASS" and active["source_commit"] == plan["commit"]
          and active["exit_code"] == 0)
    if plan["version"] == 21:
        check("Root candidate nearest finite checks",
              (proof["nearest_pawn_checks_each_profile"], proof["nearest_target_sets_each_profile"],
               proof["nearest_constexpr_assertions_each_profile"]) == (791680, 395840, 6))
    windows_path = proof_path.with_name("WINDOWS.json")
    if windows_path.is_file():
        windows = read(windows_path)
        freeze(windows_path)
        check(label + " genuine Windows root schema",
              windows["status"] == f"PASS_ROOT_WINDOWS{plan['version']}_ORIGINALS_AND_ARTIFACT_REVIEW"
              and windows["source_commit"] == plan["commit"]
              and windows["source_files_rehashed"] == (72 if plan["version"] == 20 else 73)
              and windows["wine_checks_passed"] == (11 if plan["version"] == 20 else 12))
        windows_observed[label] = dict(path=str(windows_path), sha256=sha(windows_path),
                                      status=windows["status"])
    else:
        windows_observed[label] = dict(path=str(windows_path), status="MISSING_CAPTURE_GATE_BLOCKED")

scope_path = E / "capture-support/PROTOTYPE-SOURCE-SCOPE.json"
scope = read(scope_path)
check("Exact source-only correspondence identity and scope",
      sha(scope_path) == "bc662ec7346ede2248edc7bc756c29a53194bb354ae35b19c464005fa2d7aa58"
      and len(scope["consumed_inputs"]) == 160 and scope["source_files_each"] == 76
      and scope["protected_engine_inputs_identical"] == 19
      and scope["historical_probe_source_commit"] is None
      and scope["historical_probe_version"] == "6.4.20" and scope["candidate_source_commit"] == CAND
      and (scope["historical_rows"], scope["historical_integer_fields"]) == (95, 61465))
for name, expected in scope["consumed_inputs"].items():
    path = Path(name)
    check("Source correspondence original: " + name, identity(path) == expected)
    freeze(path)
old_map = read(ROOT / "validation/nearest-pawn-distance-20261020/EXPECTED-SOURCE-76.json")
new_map = read(plans["candidate"]["native"] / "ROOT-FROZEN-SOURCE-GATES.json")["inputs"]
changed = [name for name in old_map if old_map[name] != new_map[name]]
check("Exactly 74 unchanged and two version-label source files",
      set(old_map) == set(new_map) and len(old_map) == 76
      and changed == ["CMakeLists.txt", "src/uci.cpp"])
for name in changed:
    old = (Path("/workspace/.cloud-setup/nearest-pawn-prototype-source") / name).read_text()
    new = (plans["candidate"]["source"] / name).read_text()
    check("Only one version label changes: " + name,
          old.count("6.4.20") == 1 and old.replace("6.4.20", "6.4.21") == new)
protected = [name for name in old_map if name.startswith(("include/", "src/"))
             and name != "src/uci.cpp"]
check("Nineteen protected production files identical",
      len(protected) == 19 and all(old_map[name] == new_map[name] for name in protected))
for name in ["public-diff/PROBE-RECEIPT.json", "public-diff/public-diff-attempt1/RESULT.json"]:
    historical = read(ROOT / "validation/nearest-pawn-distance-20261020" / name)
    check("Historical probe identity unchanged: " + name,
          historical["source_commit"] is None and historical["prototype_version"] == "6.4.20"
          and historical["rows"] == 95 and historical["compared_integer_fields"] == 61465)
check("No capture authorization or actual captures created",
      not (E / "ROOT-CAPTURE-AUTHORIZATION.json").exists() and not (E / "actual-five-captures").exists())
for name, expected in frozen.items():
    check("Final reviewed input unchanged: " + name, identity(Path(name)) == expected)
failed = [row for row in checks if not row["passed"]]
result = dict(
    status="PASS_CAPTURE_SUPPORT_EVIDENCE_REVIEW_NOT_EXECUTION_AUTHORIZATION" if not failed
    else "FAILED_CAPTURE_SUPPORT_EVIDENCE_REVIEW",
    reviewer="/root/archive_clock_complete",
    started_utc=started, completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    checker_sha256=sha(Path(__file__)), check_count=len(checks), failed_check_count=len(failed),
    findings=failed, checks=checks, selected_frozen_inputs=frozen,
    actual_windows_observation=windows_observed, driver_sha256=DRIVER,
    support_manifest_sha256=sha(seal), baseline_sha=BASE, candidate_sha=CAND,
    source_correspondence=dict(inputs=160, files_each=76, unchanged=74, version_labels=2,
                               protected=19, historical_trace_not_replayed_or_relabelled=True),
    reviewed_code_or_tests_imported_or_executed=False,
    captures_engines_compilers_timing_git_network_executed=False,
    launch_authorization=False,
    qualifications=[
        "Read-only AST/JSON/hash reader only; no reviewed driver/helper/tests executed.",
        "Original 8/9 failed, 9/9 and 10/10 passed offline outputs authenticated without rerun.",
        "A genuine missing Windows21 proof remains a capture blocker; derived mocks are not proof.",
        "Historical source correspondence preserves null source commit/version20; no probe replay.",
        "Later actual captures and READY/enabled metadata need separate source-bound review.",
    ])
with (OUT / "EVIDENCE-REVIEW.json").open("x") as output:
    json.dump(result, output, indent=2)
    output.write("\n")
print(json.dumps(dict(status=result["status"], checks=len(checks), failed=len(failed),
                      findings=failed, reviewed_inputs=len(frozen),
                      windows=windows_observed), indent=2))
raise SystemExit(1 if failed else 0)
