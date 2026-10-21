"""Final read-only metadata authentication. Does not import reviewed modules."""
import ast
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat

ROOT = Path("/workspace/dwqww")
E = ROOT / "validation/hosted-nearest-pawn-performance-20261021"
OUT = E / "independent-review"
PKG = ROOT / ".github/hosted-nearest-pawn-performance"
WF = ROOT / ".github/workflows/forge-hosted-nearest-pawn-performance.yml"
checks = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def identity(path):
    assert path.is_file() and not path.is_symlink(), str(path)
    return dict(sha256=sha(path), mode=stat.S_IMODE(path.stat().st_mode))


def check(name, condition):
    checks.append(dict(name=name, passed=bool(condition)))


def safe(root, name):
    part = PurePosixPath(name)
    assert not part.is_absolute() and ".." not in part.parts and part.as_posix() == name
    path = root / name
    assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve())
    return path


started = datetime.datetime.now(datetime.timezone.utc).isoformat()
cfg = read(PKG / "protocol.json")
checkpoint = read(E / "ENABLED-PREPARATION-CHECKPOINT.json")
meta = read(E / "READY-METADATA-CHECK.json")
offline = read(E / "READY-OFFLINE-RESULT.json")
expected = {
    PKG / "protocol.json": "229be7aafc47d8337b9691bb4b323fcf832b6ab31e28c015e2150c1e51709aef",
    WF: "3bc1003fb7e8340993a35d2fb328efdcd1a2971bc9a14621d8fd4848e15d6afd",
    PKG / "PACKAGE-SHA256SUMS": "9ece2241f9a11bdc906bab7036abdae9f15fcbe0de39df431201633404e14742",
    E / "READY-METADATA-CHECK.json": "d117651f8691e438211ccdbf8cb3fcc1712dd49d92dfd4726b07d1d22ba72f46",
    E / "READY-OFFLINE-RESULT.json": "59cd69320ced9158b065a57d06f4166114b6ae2278bde2d06b45e24e5a2fbad8",
    E / "ENABLED-PREPARATION-CHECKPOINT.json": "1e9e221c00480f7e2ed9f8179ebe954f7042de9c929eba964972daf7050c2cef",
    E / "independent-review/REVIEW.json": "09bd77aa239d5173155c25ea77b3b4e02b77555c3d7499d6e15472f48cefe441",
}
check("All exact sealed identities and canonical review unchanged",
      all(sha(path) == digest for path, digest in expected.items()))
seal = E / "EVIDENCE-SHA256SUMS.enabled-pre-review"
check("Exact closed320-entry preparer seal",
      sha(seal) == "b9b2d83affc21c2771a4572f92ad8b4890a09c916365570fd049e5f2adc83e6f")
seal_rows = [line.split("  ", 1) for line in seal.read_text().splitlines()]
check("Every320 sealed preparer original byte identity",
      len(seal_rows) == len({n for _, n in seal_rows}) == 320
      and all(sha(safe(E, name)) == digest for digest, name in seal_rows))

fixed = dict(status="PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH",
             baseline_sha="fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e",
             candidate_sha="2e151d019bc58dff2ab4e76e99ef99516af8d222",
             source_file_counts=dict(baseline=75, candidate=76),
             compiler="g++-14", attempts=1, fault_retries=0, bench_depth=11,
             expected_nodes=321912, benches_per_process=5, aa_blocks=15, ab_blocks=31,
             bootstrap_seed=20261029, bootstrap_draws=10000, sample_timeout_seconds=60,
             build_work_seconds=690, timing_work_seconds=3600, workflow_status="FROZEN")
check("Strict source/count/compiler/attempt/statistical settings",
      all(cfg.get(k) == v and type(cfg.get(k)) is type(v) for k, v in fixed.items()))
check("All five genuine qualification statuses pass",
      all(cfg[k] == "PASSED" for k in ["source_gates_status", "parity_review_status",
                                      "capture_review_status", "root_review_status",
                                      "independent_review_status"]))
check("Exact nonLTO/nonfastmath generic flags",
      cfg["release_flags"] == "-O3 -DNDEBUG -march=x86-64-v3 -mtune=generic -fno-fast-math -ffp-contract=off -fno-lto")
check("188 processes940 canonicalcommands and90/12/65 limits",
      cfg["bounds"]["planned_fresh_processes"] == 4 + 4 * (15 + 31) == 188
      and cfg["bounds"]["planned_bench_commands"] == 188 * 5 == 940
      and [cfg["bounds"][k] for k in ["job_minutes", "build_step_minutes", "timing_step_minutes"]]
      == [90, 12, 65])
common = ast.parse((PKG / "common.py").read_bytes())
required = ast.literal_eval(next(n.value for n in common.body if isinstance(n, ast.Assign)
                                and any(isinstance(t, ast.Name) and t.id == "REQUIRED_PROOFS"
                                        for t in n.targets)))
proofs = cfg["correctness_evidence_sha256"]
check("Exact13 mandatory proof list and genuine67 bound proof bytes",
      cfg["mandatory_finite_proof_paths"] == list(required) and len(required) == 13
      and set(required).issubset(proofs) and len(proofs) == 67
      and all(sha(safe(ROOT, name)) == digest for name, digest in proofs.items()))
check("No final-enabled review/report/helper outputs inside protocol map",
      not any("/independent-review/FINAL-ENABLED" in n
              or n.endswith("/independent-review/final_enabled_metadata_reader.py") for n in proofs))
check("Final metadata linked to exact enabled workflow",
      sha(WF) == cfg["workflow_sha256"] == checkpoint["workflow_sha256"] == meta["workflow_sha256"])
inventory = [line.split("  ", 1) for line in (PKG / "PACKAGE-SHA256SUMS").read_text().splitlines()]
actual_names = sorted([str(f.relative_to(ROOT)) for f in PKG.rglob("*")
                       if f.is_file() and f.name != "PACKAGE-SHA256SUMS"] + [str(WF.relative_to(ROOT))])
check("Exact21 package entries, no omitted or extra files",
      [name for _, name in inventory] == actual_names and len(inventory) == 21
      and all(sha(safe(ROOT, name)) == digest for digest, name in inventory))

transport_records = []
provenance = read(E / "actual-five-captures/PROVENANCE.json")
for label in ["baseline", "candidate"]:
    entry = cfg["transport_captures"][label]
    capture = provenance["captures"][label]
    check(label + " genuine capture metadata source/binary",
          entry["source_commit"] == cfg[label + "_sha"] == capture["source_commit"]
          and entry["engine_sha256"] == capture["binary_sha256_before"]["forge"]
          == capture["binary_sha256_after"]["forge"])
    for key in ["stdin", "stdout", "stderr", "facts", "provenance", "source_manifest"]:
        name = entry[key + "_path"]
        check(label + " bound transport record " + key, name in proofs
              and sha(safe(ROOT, name)) == proofs[name])
        transport_records.append(name)
check("Twelve actual transport consumptions and181 normal frozen inputs",
      len(transport_records) == 12 and len(provenance["frozen_inputs"]) == 181
      and provenance["status"] == "PASS_BOTH_ACTUAL_FIVE_COMMAND_CAPTURES_NOT_SPEED_EVIDENCE"
      and provenance["measured_nps_difference"] is None and provenance["elo_gain"] is None)
observed = meta["final_byte_mode_rehash"]
check("All322 frozen inputs independently rehashed with modes",
      observed["status"] == "passed" and observed["mismatches"] == []
      and len(observed["observed"]) == 322
      and all(identity(Path(name)) == record for name, record in observed["observed"].items()))
scope = read(E / "capture-support/PROTOTYPE-SOURCE-SCOPE.json")
check("Historical160 source correspondence remains NULL/version20",
      len(scope["consumed_inputs"]) == 160 and scope["historical_probe_source_commit"] is None
      and scope["historical_probe_version"] == "6.4.20" and scope["source_files_each"] == 76
      and scope["only_changed_files"] == ["CMakeLists.txt", "src/uci.cpp"])
check("Actual13missing and three negative READY controls retained",
      set(meta["controls"]) == set(required) | {"DRAFT", "empty_actual_captures", "wrong_source_counts"}
      and all(meta["controls"][name] == "Full current/native/Windows/parity proof binding missing"
              for name in required)
      and meta["missing_mandatory_proofs_rejected"] == 13
      and meta["additional_controls_rejected"] == 3)
check("Actual first53offline pass and source/checkpoint hashes bind it",
      offline["attempt"] == 1 and offline["tests"] == 53 and offline["observed_tool_exit_code"] == 0
      and offline["metadata_check_exit_code"] == 0
      and checkpoint["offline_tests"] == 53 and checkpoint["offline_exit_code"] == 0
      and checkpoint["offline_receipt_sha256"] == sha(E / "READY-OFFLINE-RESULT.json")
      and offline["metadata_check_sha256"] == sha(E / "READY-METADATA-CHECK.json"))
for stream in ["stdout", "stderr"]:
    check("Original closed READY53 " + stream + " identity",
          sha(E / ("ready-offline-attempt1." + stream)) == offline[stream + "_sha256"])

snapshot_root = E / "pre-enable-disabled"
snapshot = read(snapshot_root / "SNAPSHOT.json")
changed = set(read(E / "ENABLED-METADATA-MUTATION.json")["changed_paths"])
check("Only four intended metadata paths changed",
      changed == {".github/hosted-nearest-pawn-performance/protocol.json",
                  ".github/hosted-nearest-pawn-performance/README.md",
                  ".github/hosted-nearest-pawn-performance/PACKAGE-SHA256SUMS",
                  ".github/workflows/forge-hosted-nearest-pawn-performance.yml"})
for name, row in snapshot["records"].items():
    saved = safe(snapshot_root, row["snapshot_path"])
    assert saved.stat().st_size == row["bytes"] and identity(saved) == {
        "sha256": row["sha256"], "mode": row["mode"]}
    if name not in changed:
        assert identity(safe(ROOT, name)) == {"sha256": row["sha256"], "mode": row["mode"]}
check("All166 original DRAFT files retained and all unmodified live identities intact",
      len(snapshot["records"]) == 166)
auth = read(E / "ROOT-ONE-ATTEMPT-AUTHORIZATION.json")
check("Root oneattempt authorization sourcebound and final-review prerequisite",
      auth["status"] == "ROOT_AUTHORIZES_ONE_FRESH_HOST_CALIBRATION_THEN_ELIGIBLE_AB_ONLY"
      and auth["baseline_source"] == cfg["baseline_sha"]
      and auth["candidate_source"] == cfg["candidate_sha"]
      and auth["launches_so_far"] == 0
      and auth["final_enabled_metadata_review"] == "REQUIRED_BEFORE_TRIGGER")
check("Root permitted only unchanged execution code and prior anomalies retained",
      auth["reviewed_execution_code_sha256"] == checkpoint["execution_code_sha256"]
      and cfg["prior_anomalies"] == read(snapshot_root / "package/protocol.json")["prior_anomalies"])
check("Final live protocol/canonical bytes still unchanged",
      all(sha(path) == digest for path, digest in expected.items()))
failed = [row for row in checks if not row["passed"]]
result = dict(status="PASS_FINAL_ENABLED_METADATA_INDEPENDENT_READ_REVIEW" if not failed
              else "FAILED_FINAL_ENABLED_METADATA_INDEPENDENT_READ_REVIEW",
              reviewer="/root/archive_clock_complete", started_utc=started,
              completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              check_count=len(checks), failed_check_count=len(failed), findings=failed, checks=checks,
              exact_metadata_identities={str(p.relative_to(ROOT)): h for p, h in expected.items()},
              sealed_preparer_originals=320, proof_bindings=67, transport_consumptions=12,
              capture_frozen_inputs=181, final_frozen_inputs_rehashed_bytes_and_modes=322,
              retained_DRAFT_snapshot_files=166, reviewed_code_or_tests_executed=False,
              engines_compilers_timing_git_network_or_mutations=False)
with (OUT / "FINAL-ENABLED-METADATA.json").open("x") as output:
    json.dump(result, output, indent=2)
    output.write("\n")
print(json.dumps(dict(status=result["status"], checks=len(checks), failed=len(failed),
                      findings=failed), indent=2))
raise SystemExit(1 if failed else 0)
