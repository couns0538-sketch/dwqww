"""Write the S34 v2 fixtures: one valid manifest and bad manifests with exactly one planted defect each.

usage: python -I -B make_bad_manifests_v2.py [out_dir]   (default: ./bad_manifests_v2 next to this file)

Sol's 29 v1 fixtures were never pushed (only three names survive in his logs), so they are rebuilt here
from a synthetic manifest in the live file's shape (dict root with comment/base/lock/gates, option.K=V
lists, autopromote annotations). Every fixture is deterministic; index.json lists file, expected code,
a message substring that explains the defect, and the audit profile ("default" or "strict").
The out_dir must not exist yet (no overwrite).
"""
import copy
import json
from pathlib import Path
import sys

A64, B64, C64, D64 = "a" * 64, "b" * 64, "c" * 64, "d" * 64


def valid_manifest():
    base = {"name": "lock_s198", "exe": "forge_lock_s198.exe", "sha256": A64, "options": []}
    return {
        "comment": "S34 v2 synthetic valid manifest (live-file shape; not a real gate list)",
        "base": base,
        "lock": {"locked": "2026-10-26", "decided": "synthetic", "net": "h256_e12", "exe": "forge_lock_s198.exe",
                 "sha256": A64, "inference": "float", "evidence": "synthetic", "previous_baseline": "synthetic"},
        "gates": [
            {"gate": "1", "tag": "gate001_alpha", "cand": "alpha", "exe": "forge_alpha.exe", "sha256": B64,
             "options": ["option.UseFoo=true", "option.FooScale=120"], "srand": 11, "openings_start": 1001,
             "concurrency": 5, "cap_games": 3000, "prebench": {"cand_off": 312866, "cand_on": 312866},
             "base_override": copy.deepcopy(base), "ag_vs_lock": "lock_s198", "ag_rebuilt_on": "AUTOLOCK_1_synthetic",
             "ag_base_lock_sha": A64.upper(),
             "ag_prev": {"exe": "forge_alpha_old.exe", "sha256": C64, "prebench": {"cand_off": 312866},
                         "base_override": copy.deepcopy(base), "srand": 11, "ag_vs_lock": "lock_s197"},
             "early_stop": {"games": 750, "elo_max": -8, "llr_max": -1.5, "rule": "net-only"}},
            {"gate": "2", "tag": "gate002_alpha_confirm", "cand": "alpha", "exe": "forge_alpha.exe", "sha256": B64,
             "options": ["option.UseFoo=true"], "srand": 12, "openings_start": 4001, "concurrency": 7, "tc": "10+0.1",
             "sprt": {"elo0": 0, "elo1": 10, "nonreg": False}, "confirm_of": "gate001_alpha", "pooled": False,
             "ag_rebase_of": "gate001_alpha", "ag_rebase_exempt24": False, "ag_void_rerun_of": "gate001_alpha",
             "ag_void_cause": "time loss", "status": "HELD_synthetic"},
        ],
    }


def dumps(value):
    return json.dumps(value, indent=2, sort_keys=False) + "\n"


def edit(fn):
    data = valid_manifest()
    fn(data)
    return dumps(data)


def g0(data):
    return data["gates"][0]


def g1(data):
    return data["gates"][1]


def second_gate_like_first(data, **changes):
    other = copy.deepcopy(g0(data))
    other.update(srand=21, openings_start=7001, **changes)
    data["gates"].append(other)


def without(gate, *keys):
    for key in keys:
        gate.pop(key, None)


VALID_TEXT = dumps(valid_manifest())

# (file stem, expected code, explains-substring, profile, text)
CASES = [
    ("duplicate_json_key", "JSON_DUPLICATE_KEY", "Duplicate JSON key", "default",
     VALID_TEXT.replace('"gate": "1",', '"gate": "1", "gate": "1b",', 1)),
    ("case_duplicate_key", "JSON_CASE_DUPLICATE_KEY", "differ only in case", "default",
     VALID_TEXT.replace('"gate": "1",', '"gate": "1", "Gate": "1",', 1)),
    ("syntax", "JSON_SYNTAX", "Invalid JSON", "default", VALID_TEXT.rstrip("\n")[:-1]),
    ("deep_json", "JSON_DEPTH", "nesting exceeds the offline audit limit", "default",
     '{"gates": [], "comment": ' + "[" * 70 + "]" * 70 + "}\n"),
    ("oversized_integer", "JSON_NUMBER", "4096 digits", "default",
     VALID_TEXT.replace('"srand": 11,', '"srand": ' + "9" * 5000 + ",", 1)),
    ("nan_constant", "JSON_CONSTANT", "Nonstandard JSON number", "default",
     VALID_TEXT.replace('"elo_max": -8', '"elo_max": NaN', 1)),
    ("root_unknown_field", "UNSUPPORTED_FIELD", "'outputs_root'", "default",
     edit(lambda d: d.update(outputs_root="F:/somewhere"))),
    ("gates_not_list", "GATES_SHAPE", "gates must be a JSON list", "default",
     edit(lambda d: d.update(gates={"gate001_alpha": {}}))),
    ("gate_not_object", "GATE_SHAPE", "Each gate must be a JSON object", "default",
     edit(lambda d: d["gates"].append("gate003"))),
    ("tag_missing", "TAG_REQUIRED", "tag must be a nonempty string", "default",
     edit(lambda d: without(g1(d), "tag"))),
    ("tag_protected", "WRITE_PROTECTED", "protected dist-v*/lock/baseline", "default",
     edit(lambda d: second_gate_like_first(d, tag="LOCK"))),
    ("tag_traversal", "WRITE_PATH_UNSAFE", "one portable write-directory component", "default",
     edit(lambda d: second_gate_like_first(d, tag="..\\gate_out"))),
    ("tag_duplicate", "TAG_DUPLICATE", "would reuse its output directory", "default",
     edit(lambda d: second_gate_like_first(d))),
    ("tag_case_collision", "TAG_WRITE_COLLISION", "case-insensitive Windows write path", "default",
     edit(lambda d: second_gate_like_first(d, tag="GATE001_ALPHA"))),
    ("exe_missing", "EXE_REQUIRED", "exe must be present as a nonempty read-only executable path", "default",
     edit(lambda d: g0(d).update(exe=""))),
    ("sha_short", "SHA256_FULL", "sha256 must be present as exactly 64 hexadecimal characters", "default",
     edit(lambda d: g0(d).update(sha256="abc123"))),
    ("base_override_not_object", "ENGINE_SHAPE", "Engine descriptor must be an object", "default",
     edit(lambda d: g0(d).update(base_override="lock_s198"))),
    ("concurrency_bool", "CONCURRENCY_TYPE", "concurrency must be an integer", "default",
     edit(lambda d: g0(d).update(concurrency=True))),
    ("concurrency_range", "CONCURRENCY_RANGE", "concurrency must be in 1..8", "default",
     edit(lambda d: g0(d).update(concurrency=9))),
    ("tc_format", "TC_FORMAT", "tc must match digits", "default",
     edit(lambda d: g1(d).update(tc="10+0.1s"))),
    ("sprt_not_object", "SPRT_SHAPE", "sprt must be an object", "default",
     edit(lambda d: g1(d).update(sprt=[0, 10]))),
    ("sprt_bounds", "SPRT_BOUNDS", "elo0 < elo1", "default",
     edit(lambda d: g1(d)["sprt"].update(elo0=10, elo1=0))),
    ("sprt_nonreg", "SPRT_NONREG", "nonreg must be present as a JSON boolean", "default",
     edit(lambda d: g1(d)["sprt"].update(nonreg="false"))),
    ("early_stop_not_object", "EARLY_STOP_SHAPE", "early_stop must be an object", "default",
     edit(lambda d: g0(d).update(early_stop=750))),
    ("early_stop_incomplete", "EARLY_STOP_COMPLETE", "missing fields: llr_max", "default",
     edit(lambda d: g0(d)["early_stop"].pop("llr_max"))),
    ("early_stop_types", "EARLY_STOP_TYPES", "games must be a positive integer", "default",
     edit(lambda d: g0(d)["early_stop"].update(games=0))),
    ("srand_type", "SRAND_TYPE", "srand must be an integer", "default",
     edit(lambda d: g1(d).update(srand="12"))),
    ("srand_duplicate", "SRAND_DUPLICATE", "srand 11 duplicates", "default",
     edit(lambda d: g1(d).update(srand=11))),
    ("openings_start_type", "OPENINGS_START_TYPE", "openings_start must be a positive integer", "default",
     edit(lambda d: g1(d).update(openings_start=0))),
    ("openings_start_duplicate", "OPENINGS_START_DUPLICATE", "openings_start 1001 duplicates", "default",
     edit(lambda d: g1(d).update(openings_start=1001))),
    ("openings_start_default_duplicate", "OPENINGS_START_DUPLICATE", "effective driver default for absent field", "default",
     edit(lambda d: (without(g0(d), "openings_start"), without(g1(d), "openings_start")))),
    ("prebench_not_object", "METADATA_SHAPE", "prebench must be an object in the audited driver schema", "default",
     edit(lambda d: g0(d).update(prebench=312866))),
    ("confirm_target", "CONFIRM_TARGET", "must exactly match an existing tag", "default",
     edit(lambda d: g1(d).update(confirm_of="gate001_ALPHA"))),
    ("unknown_gate_field", "UNSUPPORTED_FIELD", "'output_dir'", "default",
     edit(lambda d: g0(d).update(output_dir="safe_out"))),
    ("options_not_list", "OPTIONS_SHAPE", "options must be a JSON list", "default",
     edit(lambda d: g0(d).update(options="option.UseFoo=true"))),
    ("option_no_prefix", "OPTION_FORMAT", "must match the driver pattern", "default",
     edit(lambda d: g0(d)["options"].append("UseBar=true"))),
    ("option_not_string", "OPTION_FORMAT", "option entry must be a string", "default",
     edit(lambda d: g0(d)["options"].append({"UseBar": True}))),
    ("option_control_char", "OPTION_CONTROL_CHAR", "contains a control character", "default",
     edit(lambda d: g0(d)["options"].append("option.UseBar=true\nisready"))),
    ("option_duplicate", "OPTION_DUPLICATE", "UCI option names are case-insensitive", "default",
     edit(lambda d: g0(d)["options"].append("option.usefoo=false"))),
    ("option_reserved", "OPTION_RESERVED", "set by the driver itself", "default",
     edit(lambda d: g0(d)["options"].append("option.Hash=64"))),
    ("base_options_ignored", "BASE_OPTIONS_IGNORED", "['option.UseNNUE=false']", "default",
     edit(lambda d: d["base"].update(options=["option.UseNNUE=false"]))),
    ("base_override_options_ignored", "BASE_OPTIONS_IGNORED", "['option.Contempt=10']", "default",
     edit(lambda d: g0(d)["base_override"].update(options=["option.Contempt=10"]))),
    ("annotation_string_type", "ANNOTATION_TYPE", "ag_vs_lock must be a nonempty string", "default",
     edit(lambda d: g0(d).update(ag_vs_lock=198))),
    ("annotation_bool_type", "ANNOTATION_TYPE", "pooled must be a JSON boolean", "default",
     edit(lambda d: g1(d).update(pooled="no"))),
    ("ag_prev_not_object", "AG_PREV_SHAPE", "ag_prev must be an object", "default",
     edit(lambda d: g0(d).update(ag_prev="forge_alpha_old.exe"))),
    ("ag_prev_unknown_field", "UNSUPPORTED_FIELD", "'tc'", "default",
     edit(lambda d: g0(d)["ag_prev"].update(tc="10+0.1"))),
    ("ag_prev_srand_type", "SRAND_TYPE", "ag_prev srand must be an integer", "default",
     edit(lambda d: g0(d)["ag_prev"].update(srand=None))),
    ("strict_tc_required", "TC_REQUIRED", "strict audit requires an explicit time control", "strict",
     edit(lambda d: (d["gates"].pop(0), g0(d).pop("confirm_of"), g0(d).pop("ag_rebase_of"), g0(d).pop("ag_void_rerun_of"), g0(d).pop("tc")))),
    ("strict_sprt_required", "SPRT_REQUIRED", "strict audit requires explicit elo0, elo1 and nonreg", "strict",
     edit(lambda d: (d["gates"].pop(0), g0(d).pop("confirm_of"), g0(d).pop("ag_rebase_of"), g0(d).pop("ag_void_rerun_of"), g0(d).pop("sprt")))),
    ("strict_openings_start_required", "OPENINGS_START_REQUIRED", "strict audit requires an explicit unique start", "strict",
     edit(lambda d: (d["gates"].pop(0), g0(d).pop("confirm_of"), g0(d).pop("ag_rebase_of"), g0(d).pop("ag_void_rerun_of"), g0(d).pop("openings_start")))),
]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    out = Path(argv[0]) if argv else Path(__file__).resolve().with_name("bad_manifests_v2")
    out.mkdir()  # must be new: no overwrite
    (out / "valid_manifest_v2.json").write_text(VALID_TEXT, encoding="utf-8", newline="\n")
    (out / "valid_manifest_v2_bom.json").write_bytes(b"\xef\xbb\xbf" + VALID_TEXT.encode("utf-8"))
    index = []
    for stem, code, explains, profile, text in CASES:
        name = "bad_" + stem + ".json"
        (out / name).write_text(text, encoding="utf-8", newline="\n")
        index.append({"file": name, "code": code, "explains": explains, "profile": profile})
    # A file that is not UTF-8 at all (Latin-1 byte in a string).
    (out / "bad_not_utf8.json").write_bytes(VALID_TEXT.replace("synthetic valid", "synth\u00e9tic valid").encode("latin-1"))
    index.append({"file": "bad_not_utf8.json", "code": "INPUT_READ", "explains": "Cannot read manifest", "profile": "default"})
    (out / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("wrote %d bad fixtures + 2 valid fixtures to %s" % (len(index), out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
