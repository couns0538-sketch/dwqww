"""Read closed current finite evidence; never execute reviewed code or engines."""
import datetime
import hashlib
import json
from pathlib import Path
import stat

ROOT = Path("/workspace/dwqww")
E = ROOT / "validation/hosted-nearest-pawn-performance-20261021"
OUT = E / "independent-review"
BASE = "fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e"
CAND = "2e151d019bc58dff2ab4e76e99ef99516af8d222"
checks = []
frozen = {}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path):
    assert path.is_file() and not path.is_symlink(), str(path)
    info = path.stat()
    return dict(sha256=sha(path), bytes=info.st_size, mode=stat.S_IMODE(info.st_mode))


def read(path):
    frozen[str(path)] = identity(path)
    return json.loads(path.read_bytes())


def check(name, condition):
    checks.append(dict(name=name, passed=bool(condition)))


started = datetime.datetime.now(datetime.timezone.utc).isoformat()
for rel, expected_sha, count in [
    ("independent-review-initial/REVIEW.json",
     "535642f3a85294da825582a5599b874190824354c57d30179fb8a906675f039f", 252),
    ("capture-support-independent-review/REVIEW.json",
     "79d1254b62014745af7cd35eb2285934af17189af6de521244000c8a392f30a2", 728),
]:
    path = E / rel
    result = read(path)
    check("Prior independent receipt identity: " + rel,
          sha(path) == expected_sha and result["independent_checks"] == count)

for label, commit, native_name, experiment, count in [
    ("baseline", BASE, "pawn-span-fill-native-20261020", "pawn-span-fill-20261020", 12),
    ("candidate", CAND, "nearest-pawn-native-20261020", "nearest-pawn-distance-20261020", 13),
]:
    native = ROOT / "validation" / native_name
    root_path = ROOT / "validation" / experiment / "root-verification/NATIVE.json"
    proof = read(root_path)
    final_path = native / "FINAL-RECEIPT.json"
    final = read(final_path)
    version = 20 if label == "baseline" else 21
    check(label + " current root/native identities and 36/39,8,56 gates",
          proof["status"] == f"PASS_ROOT_FULL_NATIVE{version}_ORIGINALS_AND_GIT_SOURCE_REVIEW"
          and proof["source_commit"] == final["source_commit"] == commit
          and final["status"] == "STABLE"
          and (proof["ctest"], proof["active_uci"], proof["exact_cold_warm_searches"])
          == (count * 3, 8, 56)
          and (final["native_ctests"], final["default_tsan_active_checks"],
               final["exact_cold_warm_searches"]) == (count * 3, 8, 56))
    manifest = native / "EVIDENCE-SHA256SUMS"
    frozen[str(manifest)] = identity(manifest)
    check(label + " exact full evidence/root bindings and first attempts",
          proof["native_final_receipt_sha256"] == sha(final_path)
          and proof["native_manifest_sha256"] == sha(manifest)
          and proof["native_profile_attempts"] == dict(release=1, asan=1, tsan=1)
          and proof["exact_evidence_tree_verified"] is True and proof["engine_gate_retries"] == 0
          and final["all_owned_processes_closed"] is True and final["independent_audit_failed"] == 0)
    source = read(native / "ROOT-FROZEN-SOURCE-GATES.json")
    check(label + " actual frozen source count and identity",
          source["source_commit"] == commit and len(source["inputs"]) == (75 if version == 20 else 76))
    for profile in ["release", "asan", "tsan"]:
        entry = final["native_profiles"][profile]
        receipt_path = native / f"frozen-{profile}-attempt1/summary.json"
        receipt = read(receipt_path)
        check(label + " " + profile + " exact PASS receipt/attempt/count",
              entry["status"] == "PASS" and type(entry["attempts"]) is int and entry["attempts"] == 1
              and entry["ctest_count"] == count and entry["receipt_sha256"] == sha(receipt_path)
              and receipt["status"] == "PASS" and receipt["source_commit"] == commit
              and len(receipt["ctest_names"]) == count)
        if version == 21:
            check("Candidate " + profile + " actual nearest finite checks",
                  (entry["nearest_pawn_checks"], entry["nearest_target_sets"],
                   entry["nearest_constexpr_assertions"]) == (791680, 395840, 6))
    if version == 21:
        check("Candidate root source and nearest counts exact",
              sha(root_path) == "fea7ace3bddaa69bf6b840f8d1901b448905f79ef24744188d704bfd01fb95fb"
              and (proof["nearest_pawn_checks_each_profile"], proof["nearest_target_sets_each_profile"],
                   proof["nearest_constexpr_assertions_each_profile"]) == (791680, 395840, 6)
              and final["driver_source_mutations_after_start"] is False
              and final["all_originals_retained"] is True)

winroot_path = ROOT / "validation/nearest-pawn-distance-20261020/root-verification/WINDOWS.json"
winroot = read(winroot_path)
win = ROOT / "validation/nearest-pawn-windows-20261021"
final = read(win / "FINAL-STATUS.json")
audit = read(win / "independent-audit.json")
runtime = read(win / "runtime-attempt1/result.json")
raw_manifest = read(win / "windows-originals-SHA256.json")
check("Current genuine Windows21 root proof exact identity",
      sha(winroot_path) == "f1ab747d91f7662ccfb1a071f7e76816c459503872732cb626a39192894a60b5"
      and winroot["status"] == "PASS_ROOT_WINDOWS21_ORIGINALS_AND_ARTIFACT_REVIEW"
      and winroot["source_commit"] == CAND)
check("Root actual Windows73source/229raw/521parent/10PE/12runtime/1615audit",
      (winroot["source_files_rehashed"], winroot["raw_originals_byte_verified"],
       winroot["protected_parent_files_rehashed"], winroot["original_built_pe_files_rehashed"],
       winroot["wine_checks_passed"], winroot["audit_checks_verified"]) == (73, 229, 521, 10, 12, 1615))
check("Actual closed Windows final and first-chain provenance",
      final["status"] == "WINDOWS21_FIRST_CHAIN_QUALIFIED_NOT_ELO_ACCEPTED"
      and final["source_commit"] == CAND and final["source_files"] == 73
      and final["fresh_build_attempts"] == final["wine_runtime_attempts"] == 1
      and final["wine_checks_passed"] == 12 and final["all_archived_originals_and_release_immutable"])
check("Actual Windows audit and all1615 finite audit outcomes",
      audit["status"] == "passed" and audit["source_and_tests_commit"] == CAND
      and audit["check_count"] == len(audit["checks"]) == 1615
      and all(c["passed"] is True for c in audit["checks"])
      and audit["engine_execution_during_audit"] is False and audit["new_build_during_audit"] is False)
check("Actual Windows runtime12 and original nearest field names",
      runtime["status"] == "passed" and len(runtime["checks"]) == 12
      and runtime["nearest_pawn_failures"] == 0
      and (runtime["nearest_pawn_checks"], runtime["nearest_pawn_sets"],
           runtime["nearest_constexpr_assertions"]) == (791680, 395840, 6)
      and final["nearest_pawn_sets"] == winroot["nearest_target_sets"] == 395840)
check("Same-platform Windows signature and no hardware/strength claim",
      runtime["bench11_nodes"] == final["bench11_nodes"] == winroot["bench11_nodes"] == 352313
      and winroot["native_windows_or_physical_ryzen_tested"] is False
      and winroot["nps_difference"] is None and winroot["elo_gain"] is None)
raw_archive = win / "windows-originals.zip"
artifact = ROOT / winroot["artifact"]
for path in [raw_archive, artifact, win / "FINAL-REPORT.md"]:
    frozen[str(path)] = identity(path)
check("Current original raw and release archive byte identities",
      len(raw_manifest) == 229
      and sha(raw_archive) == winroot["raw_archive_sha256"] == final["raw_archive_sha256"]
      and sha(artifact) == winroot["artifact_sha256"] == final["artifact_sha256"]
      and artifact.stat().st_size == winroot["artifact_bytes"] == final["artifact_bytes"] == 15445676)

scope_path = E / "capture-support/PROTOTYPE-SOURCE-SCOPE.json"
scope = read(scope_path)
check("Source-only correspondence exact160-input identity",
      sha(scope_path) == "bc662ec7346ede2248edc7bc756c29a53194bb354ae35b19c464005fa2d7aa58"
      and len(scope["consumed_inputs"]) == 160 and scope["source_files_each"] == 76
      and scope["protected_engine_inputs_identical"] == 19
      and scope["historical_probe_source_commit"] is None
      and scope["historical_probe_version"] == "6.4.20"
      and scope["candidate_source_commit"] == CAND)
for name, expected in scope["consumed_inputs"].items():
    path = Path(name)
    check("Current source correspondence original: " + name, identity(path) == expected)
    frozen[str(path)] = identity(path)
check("Historical trace remains genuine95rows61465fields and null-source/version20",
      (scope["historical_rows"], scope["historical_integer_fields"]) == (95, 61465)
      and scope["only_changed_files"] == ["CMakeLists.txt", "src/uci.cpp"]
      and scope["final_inputs_byte_mode_equal"] is True)

for name, expected in frozen.items():
    check("Final current evidence unchanged: " + name, identity(Path(name)) == expected)
failed = [row for row in checks if not row["passed"]]
result = dict(
    status="PASS_CURRENT_FINITE_AND_SOURCE_EVIDENCE_READY_FOR_CAPTURE_RECONCILIATION"
    if not failed else "FAILED_CURRENT_FINITE_AND_SOURCE_EVIDENCE",
    reviewer="/root/archive_clock_complete", started_utc=started,
    completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    checker_sha256=sha(Path(__file__)), check_count=len(checks), failed_check_count=len(failed),
    findings=failed, checks=checks, selected_originals=frozen,
    baseline_sha=BASE, candidate_sha=CAND, source_counts=dict(baseline=75, candidate=76),
    windows_source_count=73, windows_runtime_checks=12, artifact_audit_checks=1615,
    source_correspondence_inputs=160, historical_trace_not_replayed_or_relabelled=True,
    no_reviewed_code_tests_engines_compilers_timing_git_network_execution=True,
    scope="Current source-bound finite evidence only; no speed, Elo, native Windows/Ryzen or launch claim.")
with (OUT / "CURRENT-FINITE-REVIEW.json").open("x") as output:
    json.dump(result, output, indent=2)
    output.write("\n")
print(json.dumps(dict(status=result["status"], checks=len(checks), failed=len(failed),
                      findings=failed, selected_originals=len(frozen)), indent=2))
raise SystemExit(1 if failed else 0)
