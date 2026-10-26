"""Read-only, offline gate-manifest audit. Python 3.10+ standard library."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT_FIELDS = frozenset({"comment", "base", "gates", "lock"})
GATE_FIELDS = frozenset({
    "ag_base_lock_sha", "ag_exe_planned", "ag_exe_swap", "ag_front", "ag_nps",
    "ag_position", "base_override", "cand", "cap_games", "concurrency",
    "confirm_first", "confirm_of", "driver_note", "driver_notes", "dropped_note",
    "early_stop", "exe", "gate", "longer_tc_confirm_if_h1", "longer_tc_confirm_reason",
    "notes", "ok", "ok_driver2", "ok_original", "openings_start", "options",
    "prebench", "prebench_depths", "rerun_of", "rework_note", "run_if", "runner",
    "sha256", "sprt", "srand", "stack", "status", "tag", "tc", "watch_time",
})
ENGINE_FIELDS = frozenset({"name", "exe", "sha256", "options"})
LOCK_FIELDS = frozenset({"locked", "decided", "net", "exe", "sha256", "inference",
                         "evidence", "previous_baseline"})
NESTED_FIELDS = {
    "sprt": frozenset({"elo0", "elo1", "nonreg"}),
    "early_stop": frozenset({"games", "elo_max", "llr_max", "rule"}),
    "prebench": frozenset({"cand_off", "cand_on"}),
    "run_if": frozenset({"gate_tag", "min_elo", "if_no_result", "else", "note"}),
    "stack": frozenset({"parts", "min_part_elo"}),
}
TC = re.compile(r"\d+(\.\d+)?\+\d+(\.\d+)?", re.ASCII)
SHA256 = re.compile(r"[0-9a-fA-F]{64}")
TAG = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
DRIVER_PROVENANCE = {
    "source": "files/23_pc_autonomy/driver_r7/forge_queue_r7_conc_candidate_20261025.ps1",
    "sha256": "02069e058b3823d0f73f9ce7b8673a6a005d31dea40c57f5282a1c97c0fbb5a0",
    "evidence": {
        "tc": {"line": 89, "default": "10+0.1"},
        "openings_start": {"line": 92, "default": 1},
        "sprt": {"lines": [94, 95, 97], "default": {"elo0": 0, "elo1": 10, "nonreg": False}},
        "write_tag": {"lines": [85, 86, 354], "meaning": "tag creates a directory and log/PGN names"},
    },
    "scope": "Supplied proposed driver copy only; no PC execution or deployment verified.",
}


def finding(code, pointer, message):
    return {"code": code, "pointer": pointer, "message": message}


class ManifestError(ValueError):
    def __init__(self, code, pointer, message):
        super().__init__(message)
        self.finding = finding(code, pointer, message)


def _load_manifest_and_hash(path, max_bytes=8 * 1024 * 1024):
    """Reject duplicate keys and nonstandard JSON numbers before schema auditing."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ManifestError("JSON_DUPLICATE_KEY", "/", "Duplicate JSON key {!r}; values must never be silently replaced".format(key))
            result[key] = value
        return result

    def constant(value):
        raise ManifestError("JSON_CONSTANT", "/", "Nonstandard JSON number {!r} is forbidden".format(value))

    def integer(value):
        if len(value.lstrip("-")) > 4096:
            raise ManifestError("JSON_NUMBER", "/", "JSON integer exceeds the offline audit limit of 4096 digits")
        return int(value)

    try:
        with Path(path).open("rb") as stream:
            raw = stream.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise ManifestError("INPUT_SIZE", "/", "Manifest exceeds the {}-byte input budget".format(max_bytes))
        text = raw.decode("utf-8-sig")
        depth, in_string, escaped = 0, False, False
        for char in text:
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
            elif char == '"':
                in_string = True
            elif char in "[{":
                depth += 1
                if depth > 64:
                    raise ManifestError("JSON_DEPTH", "/", "JSON nesting exceeds the offline audit limit of 64 containers")
            elif char in "]}":
                depth -= 1
        data = json.loads(text, object_pairs_hook=pairs, parse_constant=constant, parse_int=integer)
        return data, hashlib.sha256(raw).hexdigest()
    except (OSError, UnicodeError) as exc:
        raise ManifestError("INPUT_READ", "/", "Cannot read manifest: {}".format(exc)) from exc
    except json.JSONDecodeError as exc:
        raise ManifestError("JSON_SYNTAX", "/", "Invalid JSON at line {}, column {}: {}".format(exc.lineno, exc.colno, exc.msg)) from exc
    except RecursionError as exc:
        raise ManifestError("JSON_DEPTH", "/", "JSON nesting exceeds the decoder limit") from exc


def load_manifest(path, *, max_bytes=8 * 1024 * 1024):
    """Read a bounded UTF-8 JSON manifest; never write or alter its bytes."""
    return _load_manifest_and_hash(path, max_bytes)[0]


def _number(value):
    return type(value) is int or (type(value) is float and math.isfinite(value))


def _pointer(parent, key):
    return parent + "/" + str(key).replace("~", "~0").replace("/", "~1")


def _unknown_fields(data, allowed, pointer, findings):
    for key in sorted(set(data) - allowed, key=str):
        findings.append(finding("UNSUPPORTED_FIELD", _pointer(pointer, key),
                                "Field {!r} is outside the audited schema; its write behavior is unverified".format(key)))


def _engine(data, pointer, findings, allowed=ENGINE_FIELDS):
    if not isinstance(data, dict):
        findings.append(finding("ENGINE_SHAPE", pointer, "Engine descriptor must be an object"))
        return
    _unknown_fields(data, allowed, pointer, findings)
    if not isinstance(data.get("exe"), str) or not data["exe"].strip():
        findings.append(finding("EXE_REQUIRED", _pointer(pointer, "exe"), "exe must be present as a nonempty read-only executable path"))
    if not isinstance(data.get("sha256"), str) or not SHA256.fullmatch(data["sha256"]):
        findings.append(finding("SHA256_FULL", _pointer(pointer, "sha256"), "sha256 must be present as exactly 64 hexadecimal characters"))


def _tag_write(tag, pointer, findings):
    # Inspect original components too: traversal may hide a protected component.
    components = [part.rstrip(" .").casefold() for part in tag.replace("\\", "/").split("/")]
    if any(part in {"lock", "locks", "baseline", ".git"} or part.startswith("dist-v") for part in components):
        findings.append(finding("WRITE_PROTECTED", pointer,
                                "tag {!r} derives a write inside a protected dist-v*/lock/baseline directory after Windows normalization".format(tag)))
        return
    reserved = tag.split(".", 1)[0].casefold()
    if (not TAG.fullmatch(tag) or tag.endswith((".", " ")) or
            reserved in {"con", "prn", "aux", "nul"} or
            re.fullmatch(r"(?:com|lpt)[1-9]", reserved)):
        findings.append(finding("WRITE_PATH_UNSAFE", pointer,
                                "tag {!r} must be one portable write-directory component; absolute paths, traversal, separators, device names and Windows aliases are forbidden".format(tag)))


def validate_manifest(manifest, *, driver_defaults=False):
    """Return all findings without mutating input. Strict schema is authoritative.

    Explicit driver_defaults=True is a secondary effective-value audit. It fills
    only fully absent tc/sprt/openings_start fields, never malformed overrides.
    """
    findings = []
    if isinstance(manifest, dict):
        _unknown_fields(manifest, ROOT_FIELDS, "", findings)
        gates = manifest.get("gates")
        for key, allowed in (("base", ENGINE_FIELDS), ("lock", LOCK_FIELDS)):
            if key in manifest:
                _engine(manifest[key], "/" + key, findings, allowed)
        prefix = "/gates"
    elif isinstance(manifest, list):
        gates = manifest
        prefix = ""
    else:
        return [finding("MANIFEST_SHAPE", "/", "manifest must be an object with a gates list, or a list of gate objects")]
    if not isinstance(gates, list):
        findings.append(finding("GATES_SHAPE", "/gates", "gates must be a JSON list of objects"))
        return findings

    tags, write_tags, seeds, starts = {}, {}, {}, {}
    for index, gate in enumerate(gates):
        pointer = _pointer(prefix, index)
        if not isinstance(gate, dict):
            findings.append(finding("GATE_SHAPE", pointer, "Each gate must be a JSON object"))
            continue
        tag = gate.get("tag")
        if not isinstance(tag, str) or not tag:
            findings.append(finding("TAG_REQUIRED", _pointer(pointer, "tag"), "tag must be a nonempty string naming the derived output directory"))
        else:
            _tag_write(tag, _pointer(pointer, "tag"), findings)
            if tag in tags:
                findings.append(finding("TAG_DUPLICATE", _pointer(pointer, "tag"), "tag {!r} duplicates {} and would reuse its output directory".format(tag, tags[tag])))
            elif tag.casefold() in write_tags:
                findings.append(finding("TAG_WRITE_COLLISION", _pointer(pointer, "tag"), "tag {!r} collides with {} on a case-insensitive Windows write path".format(tag, write_tags[tag.casefold()])))
            tags.setdefault(tag, pointer)
            write_tags.setdefault(tag.casefold(), pointer)
        _engine(gate, pointer, findings, GATE_FIELDS)
        if "base_override" in gate:
            _engine(gate["base_override"], _pointer(pointer, "base_override"), findings)

        concurrency = gate.get("concurrency")
        if type(concurrency) is not int:
            findings.append(finding("CONCURRENCY_TYPE", _pointer(pointer, "concurrency"), "concurrency must be an integer, excluding booleans"))
        elif not 1 <= concurrency <= 8:
            findings.append(finding("CONCURRENCY_RANGE", _pointer(pointer, "concurrency"), "concurrency must be in 1..8; found {!r}".format(concurrency)))

        if "tc" not in gate and not driver_defaults:
            findings.append(finding("TC_REQUIRED", _pointer(pointer, "tc"), "tc is missing; strict audit requires an explicit time control"))
        else:
            tc = gate.get("tc", "10+0.1")
            if not isinstance(tc, str) or not TC.fullmatch(tc):
                findings.append(finding("TC_FORMAT", _pointer(pointer, "tc"), "tc must match digits[.digits]+digits[.digits] exactly; found {!r}".format(tc)))

        if "sprt" not in gate and not driver_defaults:
            findings.append(finding("SPRT_REQUIRED", _pointer(pointer, "sprt"), "sprt is missing; strict audit requires explicit elo0, elo1 and nonreg"))
        else:
            sprt = gate.get("sprt", {"elo0": 0, "elo1": 10, "nonreg": False})
            sp = _pointer(pointer, "sprt")
            if not isinstance(sprt, dict):
                findings.append(finding("SPRT_SHAPE", sp, "sprt must be an object with elo0, elo1 and nonreg"))
            else:
                _unknown_fields(sprt, NESTED_FIELDS["sprt"], sp, findings)
                elo0, elo1 = sprt.get("elo0"), sprt.get("elo1")
                if not _number(elo0) or not _number(elo1) or not elo0 < elo1:
                    findings.append(finding("SPRT_BOUNDS", sp, "sprt elo0 and elo1 must be finite numbers excluding booleans, with elo0 < elo1"))
                if type(sprt.get("nonreg")) is not bool:
                    findings.append(finding("SPRT_NONREG", _pointer(sp, "nonreg"), "sprt nonreg must be present as a JSON boolean"))

        if "early_stop" in gate:
            early = gate["early_stop"]
            ep = _pointer(pointer, "early_stop")
            if not isinstance(early, dict):
                findings.append(finding("EARLY_STOP_SHAPE", ep, "early_stop must be an object when present"))
            else:
                _unknown_fields(early, NESTED_FIELDS["early_stop"], ep, findings)
                missing = sorted({"games", "elo_max", "llr_max"} - set(early))
                if missing:
                    findings.append(finding("EARLY_STOP_COMPLETE", ep, "early_stop is incomplete; missing fields: {}".format(", ".join(missing))))
                elif (type(early["games"]) is not int or early["games"] <= 0 or
                      not _number(early["elo_max"]) or not _number(early["llr_max"])):
                    findings.append(finding("EARLY_STOP_TYPES", ep, "early_stop games must be a positive integer and elo_max/llr_max finite numbers; booleans are forbidden"))

        for field, seen, type_code, duplicate_code in (
                ("srand", seeds, "SRAND_TYPE", "SRAND_DUPLICATE"),
                ("openings_start", starts, "OPENINGS_START_TYPE", "OPENINGS_START_DUPLICATE")):
            fp = _pointer(pointer, field)
            if field not in gate and field == "openings_start" and not driver_defaults:
                findings.append(finding("OPENINGS_START_REQUIRED", fp, "openings_start is missing; strict audit requires an explicit unique start"))
                continue
            value = gate.get(field, 1 if field == "openings_start" and driver_defaults else None)
            if type(value) is not int or (field == "openings_start" and value < 1):
                findings.append(finding(type_code, fp, "{} must be {}integer, excluding booleans".format(field, "a positive " if field == "openings_start" else "an ")))
            elif value in seen:
                detail = " (effective driver default for absent field)" if field not in gate else ""
                findings.append(finding(duplicate_code, fp, "{} {!r}{} duplicates {}; uniqueness applies to every gate, including held/dropped entries".format(field, value, detail, seen[value])))
            else:
                seen[value] = fp

        for field in ("prebench", "run_if", "stack"):
            if field in gate:
                value = gate[field]
                fp = _pointer(pointer, field)
                if not isinstance(value, dict):
                    findings.append(finding("METADATA_SHAPE", fp, "{} must be an object in the audited driver schema".format(field)))
                else:
                    _unknown_fields(value, NESTED_FIELDS[field], fp, findings)

    for index, gate in enumerate(gates):
        if isinstance(gate, dict) and "confirm_of" in gate:
            target = gate["confirm_of"]
            if not isinstance(target, str) or target not in tags:
                findings.append(finding("CONFIRM_TARGET", _pointer(_pointer(prefix, index), "confirm_of"),
                                        "confirm_of {!r} must exactly match an existing tag, including case and whitespace".format(target)))
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="Read-only UTF-8 JSON input; UTF-8 BOM is accepted")
    parser.add_argument("--driver-defaults", action="store_true", help="Secondary effective-value audit using evidenced supplied-driver defaults; strict remains authoritative")
    args = parser.parse_args(argv)
    report = {"audit_profile": "driver-defaults-secondary" if args.driver_defaults else "strict-authoritative",
              "input": args.manifest, "read_only": True}
    if args.driver_defaults:
        report["driver_defaults_provenance"] = DRIVER_PROVENANCE
    try:
        data, report["input_sha256"] = _load_manifest_and_hash(args.manifest)
        report["findings"] = validate_manifest(data, driver_defaults=args.driver_defaults)
        report["valid"] = not report["findings"]
        status = 0 if report["valid"] else 1
    except ManifestError as exc:
        report.update(valid=False, findings=[exc.finding])
        status = 2
    except OSError as exc:
        report.update(valid=False, findings=[finding("INPUT_READ", "/", "Cannot hash manifest: {}".format(exc))])
        status = 2
    print(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False))
    return status


if __name__ == "__main__":
    sys.exit(main())
