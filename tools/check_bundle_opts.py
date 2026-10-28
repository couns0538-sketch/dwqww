#!/usr/bin/env python3
"""Verify a binary's UCI option names and exact supplied ranges.

Usage: python tools/check_bundle_opts.py EXE --spec options.json
       python tools/check_bundle_opts.py EXE --require Hash --require 'Clear Hash'

The JSON schema is {"options": ["Name", {"name": "Hash", "type": "spin",
"min": 1, "max": 2048, "default": 16}]}. Only name is required per entry;
other fields compare exactly when supplied. Check defaults use JSON booleans.
Extra advertised options are allowed; all advertisements must be well formed.
The timeout bounds the complete uci/quit process, including clean exit.

IDEA_SOURCE: User's A3 bundle-validation request and the public UCI option /
uciok command contract; independently implemented with the Python standard library.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys


TYPES = {"spin", "check", "string", "button", "combo"}
FIELDS = {"name", "type", "min", "max", "default"}
OPTION = re.compile(r"option\s+name\s+(.+?)\s+type\s+(\w+)(?:\s+(.*))?")
INTEGER = re.compile(r"[+-]?\d+", re.ASCII)


def valid_name(name):
    return isinstance(name, str) and bool(name.strip()) and name == name.strip() and not any(
        char in name for char in "\r\n\x00")


def validate_spec(data):
    """Validate the complete schema before starting an executable."""
    if not isinstance(data, dict) or set(data) != {"options"} or not isinstance(data["options"], list):
        raise ValueError("spec must be an object containing only an options array")
    options = []
    names = set()
    for entry in data["options"]:
        option = {"name": entry} if isinstance(entry, str) else entry
        if not isinstance(option, dict) or not valid_name(option.get("name")) or set(option) - FIELDS:
            raise ValueError(f"malformed spec option or unknown field: {entry!r}")
        name = option["name"]
        if name.casefold() in names:
            raise ValueError(f"duplicate spec option: {name}")
        names.add(name.casefold())
        kind = option.get("type")
        if kind is not None and (not isinstance(kind, str) or kind not in TYPES):
            raise ValueError(f"invalid type for {name}: {kind!r}")
        if "type" in option and kind is None:
            raise ValueError(f"invalid type for {name}: null")
        for field in ("min", "max"):
            if field in option and (type(option[field]) is not int or kind not in (None, "spin")):
                raise ValueError(f"{name}: {field} requires an integer and a spin option")
        if "min" in option and "max" in option and option["min"] > option["max"]:
            raise ValueError(f"{name}: min exceeds max")
        if "default" in option:
            default = option["default"]
            expected_type = {"spin": int, "check": bool, "string": str, "combo": str}.get(kind)
            if "min" in option or "max" in option:
                expected_type = int
            if kind == "button" or type(default) not in (int, bool, str) or (
                    expected_type is not None and type(default) is not expected_type):
                raise ValueError(f"{name}: invalid default for option type")
            if "min" in option and default < option["min"] or "max" in option and default > option["max"]:
                raise ValueError(f"{name}: default is outside the supplied bounds")
        options.append(dict(option))
    return options


def parse_options(lines):
    """Parse only the advertisement terminated by an actual uciok line."""
    options = {}
    names = set()
    for raw in lines:
        line = raw.strip()
        if line == "uciok":
            return options
        if not line or line.split(maxsplit=1)[0] != "option":
            continue
        match = OPTION.fullmatch(line)
        if not match:
            raise ValueError(f"malformed option line: {line!r}")
        name, kind, tail = match.groups()
        if not valid_name(name) or kind not in TYPES:
            raise ValueError(f"malformed option line: {line!r}")
        if name.casefold() in names:
            raise ValueError(f"duplicate advertised option: {name}")
        names.add(name.casefold())
        option = {"name": name, "type": kind}
        tail = tail or ""
        if kind == "spin":
            tokens = tail.split()
            if len(tokens) != 6:
                raise ValueError(f"{name}: spin requires default, min and max")
            for field, value in zip(tokens[::2], tokens[1::2]):
                if field not in {"default", "min", "max"} or field in option or not INTEGER.fullmatch(value):
                    raise ValueError(f"{name}: malformed spin field {field} {value}")
                option[field] = int(value)
            if not option["min"] <= option["default"] <= option["max"]:
                raise ValueError(f"{name}: spin default is outside min/max bounds")
        elif kind == "check":
            fields = tail.split()
            if fields not in (["default", "true"], ["default", "false"]):
                raise ValueError(f"{name}: check default must be true or false")
            option["default"] = fields[1] == "true"
        elif kind == "button":
            if tail:
                raise ValueError(f"{name}: button has unexpected fields")
        elif kind == "string":
            default = re.fullmatch(r"default(?:\s+(.*))?", tail)
            if not default:
                raise ValueError(f"{name}: string requires a default")
            option["default"] = default[1] or ""
        elif kind == "combo":
            default = re.fullmatch(r"default\s+(.+)", tail)
            if not default:
                raise ValueError(f"{name}: combo requires a default")
            values = re.split(r"\s+var\s+", default[1])
            if len(values) < 2 or not all(values) or values[0] not in values[1:]:
                raise ValueError(f"{name}: combo default must be one of its var values")
            option["default"] = values[0]
        options[name] = option
    raise ValueError("engine did not return uciok")


def check_options(actual, expected):
    for option in expected:
        name = option["name"]
        if name not in actual:
            raise ValueError(f"missing required option: {name}")
        for field, want in option.items():
            got = actual[name].get(field)
            if type(got) is not type(want) or got != want:
                raise ValueError(f"{name}: {field} expected {want!r}, advertised {got!r}")


def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def positive_timeout(value):
    try:
        timeout = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("timeout must be a positive finite number") from error
    if not math.isfinite(timeout) or timeout <= 0:
        raise argparse.ArgumentTypeError("timeout must be a positive finite number")
    return timeout


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("exe", type=Path, help="path to the UCI executable")
    parser.add_argument("--spec", type=Path, help="JSON option specification")
    parser.add_argument("--require", action="append", default=[], metavar="NAME", help="required option; repeatable")
    parser.add_argument("--timeout", type=positive_timeout, default=10.0, help="total process timeout in seconds (10)")
    args = parser.parse_args(argv)
    try:
        expected = []
        if args.spec:
            expected = validate_spec(json.loads(args.spec.read_text(encoding="utf-8"), object_pairs_hook=unique_json_object))
        for name in args.require:
            entry = validate_spec({"options": [name]})[0]
            if not any(option["name"] == name for option in expected):
                expected.append(entry)
        if not expected:
            raise ValueError("provide at least one option via --spec or --require")
        # UCI consumes these commands in order; quit also makes process success observable.
        completed = subprocess.run([str(args.exe.resolve())], input="uci\nquit\n", capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", timeout=args.timeout,
                                   shell=False)
        if completed.returncode != 0:
            raise ValueError(f"engine exited with status {completed.returncode}: {completed.stderr.strip()[:500]}")
        actual = parse_options(completed.stdout.splitlines())
        check_options(actual, expected)
    except subprocess.TimeoutExpired:
        print(f"FAIL: engine timed out after {args.timeout:g} seconds", file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {len(expected)} required options verified; {len(actual)} advertised; uciok and clean exit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
