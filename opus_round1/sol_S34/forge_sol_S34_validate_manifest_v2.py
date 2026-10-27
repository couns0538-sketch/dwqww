"""Read-only, offline gate-manifest audit, v2. Python 3.10+ standard library only.

v2 of Sol's prepared validator (forge_sol_S34_validate_manifest_20261026.py, sha256 edd2247a...; his file is
unchanged). It keeps his parser hardening and rules and changes what the real PC manifest needs:

1. The default profile is the DEPLOYED gate driver C:/Users/Administrator/grok-pc/forge_push/autorestart/
   forge_queue.ps1 (sha256 636b6cca...). A field the driver defaults may be absent: tc -> 10+0.1 (line 89),
   concurrency -> 5 (line 90), openings_start -> 1 (line 92), sprt -> elo0 0, elo1 10, nonreg false
   (lines 94-97). A present field is never filled: it must be valid as written. --strict keeps Sol's strict
   profile (every field explicit); --driver-defaults is an alias of the default.
2. Annotation fields written and read by autonomy/autopromote.ps1 (sha256 896663b0...) are part of the
   schema: ag_vs_lock (line 439), ag_rebuilt_on and ag_prev (452-453), ag_rebase_of and ag_rebase_exempt24
   (408), ag_void_rerun_of and ag_void_cause (266), pooled (187). The driver never reads them and none of
   them forms a write path. They are type-checked; ag_prev must be an object with only exe, sha256,
   prebench, base_override, srand and ag_vs_lock, and its srand is not part of the srand uniqueness rule.
3. Gate options: a list of strings, each matching the driver's own pattern ^option\\.([^=]+)=(.*)$ (line 216)
   in full, with no control characters, no option name twice (case-insensitive, as UCI names), and none
   of Threads, Hash, OwnBook (the driver sets those itself, line 350).
4. Options in base or base_override (also inside ag_prev) are reported: the driver never passes them to
   fastchess (line 351 adds only Threads/Hash/OwnBook for the base engine).
5. Object keys that differ only in case are rejected at load time: the driver reads the manifest with
   PowerShell ConvertFrom-Json (line 37), whose property names are case-insensitive.

Exit status: 0 no findings, 1 findings, 2 the input could not be read as a manifest (JSON_* / INPUT_*).
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT_FIELDS = frozenset({"comment", "base", "gates", "lock"})
ANNOTATION_STRING_FIELDS = frozenset({"ag_vs_lock", "ag_rebuilt_on", "ag_rebase_of", "ag_void_rerun_of", "ag_void_cause"})
ANNOTATION_BOOL_FIELDS = frozenset({"ag_rebase_exempt24", "pooled"})
GATE_FIELDS = frozenset({
    "ag_base_lock_sha", "ag_exe_planned", "ag_exe_swap", "ag_front", "ag_nps",
    "ag_position", "base_override", "cand", "cap_games", "concurrency",
    "confirm_first", "confirm_of", "driver_note", "driver_notes", "dropped_note",
    "early_stop", "exe", "gate", "longer_tc_confirm_if_h1", "longer_tc_confirm_reason",
    "notes", "ok", "ok_driver2", "ok_original", "openings_start", "options",
    "prebench", "prebench_depths", "rerun_of", "rework_note", "run_if", "runner",
    "sha256", "sprt", "srand", "stack", "status", "tag", "tc", "watch_time",
    "ag_prev",
}) | ANNOTATION_STRING_FIELDS | ANNOTATION_BOOL_FIELDS
ENGINE_FIELDS = frozenset({"name", "exe", "sha256", "options"})
LOCK_FIELDS = frozenset({"locked", "decided", "net", "exe", "sha256", "inference",
                         "evidence", "previous_baseline"})
AG_PREV_FIELDS = frozenset({"exe", "sha256", "prebench", "base_override", "srand", "ag_vs_lock"})
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
OPTION = re.compile(r"option\.([^=]+)=(.*)", re.DOTALL)
CONTROL = re.compile(r"[\x00-\x1f\x7f]")
DRIVER_SET_OPTIONS = frozenset({"threads", "hash", "ownbook"})
DRIVER_DEFAULTS = {"tc": "10+0.1", "concurrency": 5, "openings_start": 1,
                   "sprt": {"elo0": 0, "elo1": 10, "nonreg": False}}
DRIVER_PROVENANCE = {
    "source": "C:/Users/Administrator/grok-pc/forge_push/autorestart/forge_queue.ps1 (deployed, read-only)",
    "sha256": "636b6cca691d0707449147fce1cafc42c3235c22a4419b05e0b2307e1fc2c168",
    "evidence": {
        "read": {"line": 37, "meaning": "Get-Content -Raw | ConvertFrom-Json (case-insensitive property names)"},
        "tc": {"line": 89, "default": "10+0.1"},
        "concurrency": {"line": 90, "default": 5},
        "openings_start": {"line": 92, "default": 1},
        "sprt": {"lines": [94, 95, 97], "default": {"elo0": 0, "elo1": 10, "nonreg": False}},
        "options_pattern": {"line": 216, "pattern": "^option\\.([^=]+)=(.*)$"},
        "engine_args": {"lines": [350, 351], "meaning": "candidate gets Threads/Hash/OwnBook + gate options; base gets Threads/Hash/OwnBook only"},
    },
    "annotations": {
        "source": "C:/Users/Administrator/grok-pc/forge_push/autonomy/autopromote.ps1 (read-only)",
        "sha256": "896663b0307402a7285ba8446c8b486db168075761c2dfbd7832f0a0fcdd7b12",
        "lines": {"ag_vs_lock": 439, "ag_rebuilt_on": 452, "ag_prev": 453, "ag_rebase_of": 408, "ag_rebase_exempt24": 408,
                  "ag_void_rerun_of": 266, "ag_void_cause": 266, "pooled": 187},
    },
}


def finding(code, pointer, message):
    return {"code": code, "pointer": pointer, "message": message}


class ManifestError(ValueError):
    def __init__(self, code, pointer, message):
        super().__init__(message)
        self.finding = finding(code, pointer, message)


def _load_manifest_and_hash(path, max_bytes=8 * 1024 * 1024):
    """Reject duplicate keys (also case-only duplicates) and nonstandard JSON numbers before auditing."""
    def pairs(items):
        result, folded = {}, {}
        for key, value in items:
            if key in result:
                raise ManifestError("JSON_DUPLICATE_KEY", "/", "Duplicate JSON key {!r}; values must never be silently replaced".format(key))
            if key.casefold() in folded:
                raise ManifestError("JSON_CASE_DUPLICATE_KEY", "/",
                                    "JSON keys {!r} and {!r} differ only in case; the driver's ConvertFrom-Json reads property names case-insensitively".format(folded[key.casefold()], key))
            result[key] = value
            folded[key.casefold()] = key
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
    """Read a bounded UTF-8 JSON manifest (a UTF-8 BOM is accepted); never write or alter its bytes."""
    return _load_manifest_and_hash(path, max_bytes)[0]


def _number(value):
    return type(value) is int or (type(value) is float and math.isfinite(value))


def _pointer(parent, key):
    return parent + "/" + str(key).replace("~", "~0").replace("/", "~1")


def _unknown_fields(data, allowed, pointer, findings):
    for key in sorted(set(data) - allowed, key=str):
        findings.append(finding("UNSUPPORTED_FIELD", _pointer(pointer, key),
                                "Field {!r} is outside the audited schema; its write behavior is unverified".format(key)))


def _base_options(data, pointer, findings):
    """The driver passes no manifest options to the base engine (forge_queue.ps1 line 351)."""
    if "options" not in data:
        return
    options = data["options"]
    if not isinstance(options, list):
        findings.append(finding("OPTIONS_SHAPE", _pointer(pointer, "options"), "options must be a JSON list of option.Name=value strings"))
    elif options:
        findings.append(finding("BASE_OPTIONS_IGNORED", _pointer(pointer, "options"),
                                "base engine options {!r} are never passed by the driver (only Threads/Hash/OwnBook); the base would run without them".format(options)))


def _engine(data, pointer, findings, allowed=ENGINE_FIELDS, base=False):
    if not isinstance(data, dict):
        findings.append(finding("ENGINE_SHAPE", pointer, "Engine descriptor must be an object"))
        return
    _unknown_fields(data, allowed, pointer, findings)
    if not isinstance(data.get("exe"), str) or not data["exe"].strip():
        findings.append(finding("EXE_REQUIRED", _pointer(pointer, "exe"), "exe must be present as a nonempty read-only executable path"))
    if not isinstance(data.get("sha256"), str) or not SHA256.fullmatch(data["sha256"]):
        findings.append(finding("SHA256_FULL", _pointer(pointer, "sha256"), "sha256 must be present as exactly 64 hexadecimal characters"))
    if base:
        _base_options(data, pointer, findings)


def _gate_options(gate, pointer, findings):
    if "options" not in gate:
        return
    options, op = gate["options"], _pointer(pointer, "options")
    if not isinstance(options, list):
        findings.append(finding("OPTIONS_SHAPE", op, "options must be a JSON list of option.Name=value strings"))
        return
    seen = {}
    for index, entry in enumerate(options):
        ep = _pointer(op, index)
        if not isinstance(entry, str):
            findings.append(finding("OPTION_FORMAT", ep, "option entry must be a string option.Name=value; found {!r}".format(entry)))
            continue
        if CONTROL.search(entry):
            findings.append(finding("OPTION_CONTROL_CHAR", ep, "option entry {!r} contains a control character; fastchess would pass it to the engine".format(entry)))
            continue
        match = OPTION.fullmatch(entry)
        if match is None:
            findings.append(finding("OPTION_FORMAT", ep, "option entry {!r} must match the driver pattern ^option\\.([^=]+)=(.*)$ in full".format(entry)))
            continue
        name = match.group(1).strip()
        if name.casefold() in DRIVER_SET_OPTIONS:
            findings.append(finding("OPTION_RESERVED", ep, "option {!r} is set by the driver itself for both engines (Threads=1, Hash=16, OwnBook=false)".format(name)))
        elif name.casefold() in seen:
            findings.append(finding("OPTION_DUPLICATE", ep, "option {!r} repeats {} (UCI option names are case-insensitive)".format(name, seen[name.casefold()])))
        else:
            seen[name.casefold()] = ep


def _annotations(gate, pointer, findings):
    for field in sorted(ANNOTATION_STRING_FIELDS & set(gate)):
        if not isinstance(gate[field], str) or not gate[field].strip():
            findings.append(finding("ANNOTATION_TYPE", _pointer(pointer, field), "{} must be a nonempty string (autopromote annotation)".format(field)))
    for field in sorted(ANNOTATION_BOOL_FIELDS & set(gate)):
        if type(gate[field]) is not bool:
            findings.append(finding("ANNOTATION_TYPE", _pointer(pointer, field), "{} must be a JSON boolean (autopromote annotation)".format(field)))
    if "ag_prev" in gate:
        prev, pp = gate["ag_prev"], _pointer(pointer, "ag_prev")
        if not isinstance(prev, dict):
            findings.append(finding("AG_PREV_SHAPE", pp, "ag_prev must be an object (the gate's previous exe/sha256/prebench/base_override/srand)"))
            return
        _unknown_fields(prev, AG_PREV_FIELDS, pp, findings)
        if not isinstance(prev.get("exe"), str) or not prev["exe"].strip():
            findings.append(finding("EXE_REQUIRED", _pointer(pp, "exe"), "ag_prev exe must be present as a nonempty executable path"))
        if not isinstance(prev.get("sha256"), str) or not SHA256.fullmatch(prev["sha256"]):
            findings.append(finding("SHA256_FULL", _pointer(pp, "sha256"), "ag_prev sha256 must be present as exactly 64 hexadecimal characters"))
        if "srand" in prev and type(prev["srand"]) is not int:
            findings.append(finding("SRAND_TYPE", _pointer(pp, "srand"), "ag_prev srand must be an integer, excluding booleans"))
        if "prebench" in prev:
            if not isinstance(prev["prebench"], dict):
                findings.append(finding("METADATA_SHAPE", _pointer(pp, "prebench"), "ag_prev prebench must be an object"))
            else:
                _unknown_fields(prev["prebench"], NESTED_FIELDS["prebench"], _pointer(pp, "prebench"), findings)
        if "base_override" in prev:
            _engine(prev["base_override"], _pointer(pp, "base_override"), findings, base=True)
        if "ag_vs_lock" in prev and (not isinstance(prev["ag_vs_lock"], str) or not prev["ag_vs_lock"].strip()):
            findings.append(finding("ANNOTATION_TYPE", _pointer(pp, "ag_vs_lock"), "ag_prev ag_vs_lock must be a nonempty string"))


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


def validate_manifest(manifest, *, strict=False, driver_defaults=None):
    """Return all findings without mutating input.

    Default profile: the deployed driver's defaults fill fully absent tc/concurrency/sprt/openings_start
    fields (never malformed ones). strict=True: Sol's strict profile, every field explicit.
    driver_defaults is accepted for compatibility with v1 callers: True selects the default profile,
    False selects strict, None (the default) leaves `strict` in charge.
    """
    if driver_defaults is not None:
        strict = not driver_defaults
    defaults = not strict
    findings = []
    if isinstance(manifest, dict):
        _unknown_fields(manifest, ROOT_FIELDS, "", findings)
        gates = manifest.get("gates")
        if "base" in manifest:
            _engine(manifest["base"], "/base", findings, ENGINE_FIELDS, base=True)
        if "lock" in manifest:
            _engine(manifest["lock"], "/lock", findings, LOCK_FIELDS)
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
            _engine(gate["base_override"], _pointer(pointer, "base_override"), findings, base=True)
        _gate_options(gate, pointer, findings)
        _annotations(gate, pointer, findings)

        if "concurrency" not in gate and defaults:
            concurrency = DRIVER_DEFAULTS["concurrency"]
        else:
            concurrency = gate.get("concurrency")
        if type(concurrency) is not int:
            findings.append(finding("CONCURRENCY_TYPE", _pointer(pointer, "concurrency"), "concurrency must be an integer, excluding booleans"))
        elif not 1 <= concurrency <= 8:
            findings.append(finding("CONCURRENCY_RANGE", _pointer(pointer, "concurrency"), "concurrency must be in 1..8; found {!r}".format(concurrency)))

        if "tc" not in gate and not defaults:
            findings.append(finding("TC_REQUIRED", _pointer(pointer, "tc"), "tc is missing; strict audit requires an explicit time control"))
        else:
            tc = gate.get("tc", DRIVER_DEFAULTS["tc"])
            if not isinstance(tc, str) or not TC.fullmatch(tc):
                findings.append(finding("TC_FORMAT", _pointer(pointer, "tc"), "tc must match digits[.digits]+digits[.digits] exactly; found {!r}".format(tc)))

        if "sprt" not in gate and not defaults:
            findings.append(finding("SPRT_REQUIRED", _pointer(pointer, "sprt"), "sprt is missing; strict audit requires explicit elo0, elo1 and nonreg"))
        else:
            sprt = gate.get("sprt", DRIVER_DEFAULTS["sprt"])
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
            if field not in gate and field == "openings_start" and not defaults:
                findings.append(finding("OPENINGS_START_REQUIRED", fp, "openings_start is missing; strict audit requires an explicit unique start"))
                continue
            value = gate.get(field, DRIVER_DEFAULTS["openings_start"] if field == "openings_start" and defaults else None)
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
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("manifest", help="Read-only UTF-8 JSON input; a UTF-8 BOM is accepted")
    profile = parser.add_mutually_exclusive_group()
    profile.add_argument("--strict", action="store_true", help="Sol's strict profile: every field explicit, no driver defaults")
    profile.add_argument("--driver-defaults", action="store_true", help="the default profile (deployed driver defaults); kept as an alias")
    args = parser.parse_args(argv)
    report = {"tool": "forge_sol_S34_validate_manifest_v2",
              "audit_profile": "strict" if args.strict else "deployed-driver-defaults",
              "input": args.manifest, "read_only": True, "driver_provenance": DRIVER_PROVENANCE}
    try:
        data, report["input_sha256"] = _load_manifest_and_hash(args.manifest)
        report["findings"] = validate_manifest(data, strict=args.strict)
        report["valid"] = not report["findings"]
        counts = {}
        for item in report["findings"]:
            counts[item["code"]] = counts.get(item["code"], 0) + 1
        report["finding_counts"] = dict(sorted(counts.items()))
        status = 0 if report["valid"] else 1
    except ManifestError as exc:
        report.update(valid=False, findings=[exc.finding], finding_counts={exc.finding["code"]: 1})
        status = 2
    except OSError as exc:
        report.update(valid=False, findings=[finding("INPUT_READ", "/", "Cannot hash manifest: {}".format(exc))])
        status = 2
    print(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False))
    return status


if __name__ == "__main__":
    sys.exit(main())
