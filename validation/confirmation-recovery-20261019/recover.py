#!/usr/bin/env python3
"""Recover one original artifact and job log as data; never execute their content."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile


RUN_ID = 39332822379
JOB_ID = 118334929163
HEAD_SHA = "f1b44cc71554e8ea1ec61b3ca6adc90da65646b6"
ARTIFACT_ID = 12226439147
ARTIFACT_NAME = "forge-hosted-confirmation-39332822379-1"
ARTIFACT_SHA256 = "1dc3d43767bc95251acdf2ec363e4e79b8a00e15d16b1fbd3202ec644b9a5600"
ORIGINAL_WORKFLOW = ".github/workflows/forge-hosted-confirmation.yml"
RECOVERY_WORKFLOW = ".github/workflows/forge-recover-confirmation.yml"
PACKAGE = Path("validation/confirmation-recovery-20261019")
ARCHIVER = Path(".github/hosted-nnue-strength/archive_results.py")
MATCH_STEP = "Calibrate then run one independent finite-pair SPRT"
UPLOAD_STEP = "Upload all raw evidence even on failure"
PUBLICATION_STEP = "Preserve evidence on a fresh results branch"
SPLIT_SIZE = 64 * 1024 * 1024


def now():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def assert_metadata(artifact, run, job, repository):
    """Fail closed before either download if any frozen identity disagrees."""
    require(artifact.get("id") == ARTIFACT_ID, "Original artifact ID mismatch")
    require(artifact.get("name") == ARTIFACT_NAME, "Original artifact name mismatch")
    require(artifact.get("digest") == "sha256:" + ARTIFACT_SHA256, "Original artifact digest mismatch")
    require(artifact.get("expired") is False, "Original artifact is expired or expiry is unknown")
    artifact_run = artifact.get("workflow_run", {})
    require(artifact_run.get("id") == RUN_ID, "Artifact source run mismatch")
    require(artifact_run.get("head_sha") == HEAD_SHA, "Artifact source head mismatch")
    require(run.get("id") == RUN_ID and run.get("head_sha") == HEAD_SHA, "Original run identity mismatch")
    require(run.get("run_attempt") == 1 and run.get("status") == "completed", "Original run attempt/status mismatch")
    require(run.get("conclusion") == "failure", "Original completed run conclusion mismatch")
    require(run.get("path") == ORIGINAL_WORKFLOW, "Original workflow path mismatch")
    require(run.get("repository", {}).get("full_name") == repository, "Original repository mismatch")
    require(artifact_run.get("repository_id") == run.get("repository", {}).get("id")
            and isinstance(artifact_run.get("repository_id"), int), "Artifact repository identity mismatch")
    require(job.get("id") == JOB_ID and job.get("run_id") == RUN_ID, "Original job/run mismatch")
    require(job.get("head_sha") == HEAD_SHA and job.get("run_attempt") == 1, "Original job head/attempt mismatch")
    require(job.get("status") == "completed" and job.get("conclusion") == "failure", "Original job outcome mismatch")
    for name, conclusion, completed in ((MATCH_STEP, "success", "2026-10-19T22:44:49Z"),
                                       (UPLOAD_STEP, "success", "2026-10-19T22:44:53Z"),
                                       (PUBLICATION_STEP, "failure", None)):
        rows = [row for row in job.get("steps", []) if row.get("name") == name]
        require(len(rows) == 1 and rows[0].get("conclusion") == conclusion, "Original step outcome mismatch: " + name)
        if completed is not None:
            require(rows[0].get("completed_at") == completed, "Original step timestamp mismatch: " + name)


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        # Official REST download endpoints redirect to signed HTTPS storage URLs.
        # Never forward the GitHub bearer token or persist the signed URL.
        require(urllib.parse.urlsplit(newurl).scheme == "https", "Refusing non-HTTPS redirect")
        redirected = super().redirect_request(request, response, code, message, headers, newurl)
        if redirected is not None:
            redirected.remove_header("Authorization")
        return redirected


class Client:
    def __init__(self, out, repository, token):
        require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository), "Invalid repository name")
        require(bool(token), "Standard GitHub Actions token is required")
        self.out = out
        self.api = "https://api.github.com/repos/" + repository
        self.token = token
        self.opener = urllib.request.build_opener(SafeRedirect())
        self.records = []
        provenance = self.out / "retrieval-provenance.json"
        if provenance.exists():
            self.records = json.loads(provenance.read_text(encoding="utf-8"))["requests"]

    def get(self, endpoint, relative):
        record = {"endpoint": self.api + endpoint, "destination": relative, "started_at_utc": now()}
        self.records.append(record)
        path = self.out / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(self.api + endpoint, headers={
            "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": "Bearer " + self.token, "User-Agent": "Forge-original-confirmation-recovery"})
        try:
            with self.opener.open(request, timeout=60) as response, path.open("xb") as destination:
                record["status"] = response.status
                record["headers"] = {key: response.headers[key] for key in
                                     ("Content-Type", "Content-Length", "Date", "ETag", "Last-Modified", "X-GitHub-Request-Id")
                                     if response.headers.get(key) is not None}
                shutil.copyfileobj(response, destination, length=1024 * 1024)
            record.update(size=path.stat().st_size, sha256=digest(path), completed_at_utc=now())
        except Exception as error:
            # Do not stringify network errors: their URL can contain signed query secrets.
            record.update(error_type=type(error).__name__, completed_at_utc=now())
            if isinstance(error, urllib.error.HTTPError):
                record["status"] = error.code
            raise RuntimeError("Official retrieval failed for " + endpoint + "; see redacted provenance") from None
        finally:
            write_json(self.out / "retrieval-provenance.json", {"schema_version": 1, "requests": self.records})
        return path


def read_metadata(out, repository):
    rows = [json.loads((out / "official-metadata" / (name + ".json")).read_text(encoding="utf-8"))
            for name in ("artifact", "run", "job")]
    assert_metadata(*rows, repository)
    return rows


def initialize(out):
    out.mkdir(parents=True, exist_ok=True)
    protocol = json.loads((PACKAGE / "protocol.json").read_text(encoding="utf-8"))
    require(protocol.get("status") == "REVIEWED_READY_FOR_SINGLE_PUSH", "Recovery protocol awaits root review")
    for key, value in (("original_run_id", RUN_ID), ("original_run_attempt", 1),
                       ("original_head_sha", HEAD_SHA), ("original_job_id", JOB_ID),
                       ("original_artifact_id", ARTIFACT_ID), ("original_artifact_name", ARTIFACT_NAME),
                       ("original_artifact_sha256", ARTIFACT_SHA256), ("archive_split_bytes", SPLIT_SIZE),
                       ("match_rerun", False), ("downloaded_code_execution", False)):
        require(protocol.get(key) == value, "Recovery protocol identity mismatch: " + key)
    require(digest(ARCHIVER) == protocol.get("trusted_archive_helper_sha256"), "Frozen archive helper digest mismatch")
    trusted = out / "trusted-recovery-source"
    trusted.mkdir()
    files = [Path(RECOVERY_WORKFLOW), PACKAGE / "recover.py", PACKAGE / "protocol.json", ARCHIVER]
    for path in files:
        target = trusted / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    write_json(out / "recovery-platform.json", {
        "schema_version": 1, "created_at_utc": now(), "python": sys.version, "platform": platform.platform(),
        "github": {name: os.environ.get(name) for name in ("GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_REF",
                   "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_WORKFLOW", "RUNNER_OS", "RUNNER_ARCH")},
        "trusted_source_sha256": {str(path): digest(path) for path in files},
        "original_run_id": RUN_ID, "original_head_sha": HEAD_SHA, "original_job_id": JOB_ID,
        "original_artifact_id": ARTIFACT_ID, "downloaded_code_executed": False})


def metadata(out):
    initialize(out)
    repository = os.environ["GITHUB_REPOSITORY"]
    client = Client(out, repository, os.environ["GITHUB_TOKEN"])
    for endpoint, name in ((f"/actions/artifacts/{ARTIFACT_ID}", "artifact"),
                           (f"/actions/runs/{RUN_ID}", "run"), (f"/actions/jobs/{JOB_ID}", "job")):
        client.get(endpoint, "official-metadata/" + name + ".json")
    read_metadata(out, repository)
    write_json(out / "source-identity-verified.json", {"verified_at_utc": now(), "original_run_id": RUN_ID,
               "original_head_sha": HEAD_SHA, "original_artifact_id": ARTIFACT_ID, "sha256": ARTIFACT_SHA256})


def original_bytes(out):
    repository = os.environ["GITHUB_REPOSITORY"]
    read_metadata(out, repository)
    client = Client(out, repository, os.environ["GITHUB_TOKEN"])
    failures = []
    try:
        client.get(f"/actions/jobs/{JOB_ID}/logs", f"original-downloads/job-{JOB_ID}.log")
    except (RuntimeError, OSError) as error:
        failures.append(type(error).__name__ + ": original job-log retrieval")
    try:
        archive = client.get(f"/actions/artifacts/{ARTIFACT_ID}/zip", f"original-downloads/artifact-{ARTIFACT_ID}.zip")
        require(digest(archive) == ARTIFACT_SHA256, "Original artifact ZIP digest does not match official frozen metadata")
    except (RuntimeError, OSError, ValueError) as error:
        failures.append(type(error).__name__ + ": original artifact ZIP retrieval/integrity")
    require(not failures, "; ".join(failures))


def check_raw_tree(out):
    require(out.is_dir() and not out.is_symlink(), "Raw evidence root must be a real directory")
    for path in out.rglob("*"):
        mode = path.lstat().st_mode
        require(stat.S_ISDIR(mode) or stat.S_ISREG(mode), "Nonregular raw evidence node: " + str(path.relative_to(out)))


def verify_extracted(out):
    check_raw_tree(out)
    original = out / "original-downloads" / f"artifact-{ARTIFACT_ID}.zip"
    require(digest(original) == ARTIFACT_SHA256, "Original artifact ZIP digest changed before extracted-file verification")
    extracted = out / "original-artifact-files"
    require(extracted.is_dir(), "Official action did not create the extracted evidence directory")
    expected = {}
    with zipfile.ZipFile(original) as archive:
        for entry in archive.infolist():
            name = PurePosixPath(entry.filename)
            require(not name.is_absolute() and ".." not in name.parts and "\\" not in entry.filename,
                    "Unsafe original ZIP member")
            require(not stat.S_ISLNK(entry.external_attr >> 16), "Symlink member in original ZIP")
            if entry.is_dir():
                continue
            require(entry.filename not in expected, "Duplicate original ZIP member")
            value = hashlib.sha256()
            with archive.open(entry) as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    value.update(block)
            expected[entry.filename] = {"size": entry.file_size, "sha256": value.hexdigest()}
    actual = {path.relative_to(extracted).as_posix(): {"size": path.stat().st_size, "sha256": digest(path)}
              for path in extracted.rglob("*") if path.is_file()}
    require(bool(expected) and actual == expected, "Official extracted files do not match every original ZIP payload byte")
    write_json(out / "extracted-files-verified.json", {"schema_version": 1, "verified_at_utc": now(),
               "original_zip_sha256": ARTIFACT_SHA256, "files": dict(sorted(expected.items()))})


def diagnose(out):
    """Retain exact derived excerpts, separately from the untouched original log."""
    out.mkdir(parents=True, exist_ok=True)
    path = out / "original-downloads" / f"job-{JOB_ID}.log"
    report = {"schema_version": 1, "cause": "unknown; inspect original publication-step log", "excerpts": []}
    if path.is_file():
        raw = path.read_bytes()
        report.update(original_log_file=str(path.relative_to(out)), original_log_sha256=digest(path),
                      original_log_size=len(raw))
        if zipfile.is_zipfile(path):
            report["cause"] = "unknown; original log endpoint returned a ZIP retained without extraction"
        else:
            lines = raw.decode("utf-8", errors="replace").splitlines()
            needles = (PUBLICATION_STEP, "git push origin", "remote:", "fatal:", "error:", "##[error]", "exceeds GitHub")
            indexes = set()
            for index, line in enumerate(lines):
                if any(needle in line for needle in needles):
                    indexes.update(range(max(0, index - 2), min(len(lines), index + 4)))
            report["excerpts"] = [{"line": index + 1, "text": lines[index]} for index in sorted(indexes)]
            # Excerpts are the diagnosis evidence. Do not infer an upload-size cause,
            # or any other root cause, from public artifact size or failed status.
    else:
        report["cause"] = "unknown; original job-log bytes were not retrieved"
    write_json(out / "publication-failure-diagnosis.json", report)


def verify_publication(out, manifest_path, pathspec):
    check_raw_tree(out)
    require(manifest_path.is_file() and not manifest_path.is_symlink()
            and 0 < manifest_path.stat().st_size <= SPLIT_SIZE, "Oversized or nonregular external manifest")
    spec = importlib.util.spec_from_file_location("trusted_archive_results", ARCHIVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = module.verify_archive(manifest_path)
    require(manifest.get("schema_version") == 1 and manifest.get("format") == "raw-split-zip", "Archive schema mismatch")
    require(manifest.get("split_size") == SPLIT_SIZE, "Archive split size mismatch")
    inventory = [{"path": path.relative_to(out).as_posix(), "size": path.stat().st_size, "sha256": digest(path)}
                 for path in sorted(out.rglob("*")) if path.is_file()]
    require(inventory == manifest["files"], "Archive does not preserve every current raw file")
    files = [manifest_path]
    for part in manifest["parts"]:
        require(0 < part["size"] <= SPLIT_SIZE, "Oversized or empty archive part")
        files.append(manifest_path.parent / part["file"])
    require(set(files) == set(manifest_path.parent.iterdir()), "Unexpected files in publication directory")
    pathspec.write_bytes(b"".join(str(path).encode("utf-8") + b"\0" for path in files))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("metadata", "original-bytes", "verify-extracted", "check-raw-tree", "diagnose", "verify-publication"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--pathspec", type=Path)
    args = parser.parse_args()
    if args.command == "verify-publication":
        require(args.manifest is not None and args.pathspec is not None, "Publication manifest/pathspec are required")
        verify_publication(args.out, args.manifest, args.pathspec)
    else:
        {"metadata": metadata, "original-bytes": original_bytes, "verify-extracted": verify_extracted,
         "check-raw-tree": check_raw_tree, "diagnose": diagnose}[args.command](args.out)


if __name__ == "__main__":
    main()
