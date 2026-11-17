#!/usr/bin/env python3
"""check_settings_values.py [harness.py ...]

THE CHECK THAT A COUNT CANNOT DO: does each harness send the SAME VALUES as the canonical S14 / PC20 list, not just
the same number of options?

Why it matters: my S14 values are hand-copied into every harness. A count assertion passes if the list has 14
entries; it cannot see that `LmrHistoryDivisor 5643` was typed as `5634` in one file. That transcription error would
silently produce a differently-configured search whose numbers still look plausible — which is exactly the failure
class of S-W7.

The canonical values come from THE SWARM brief (the authority a finding must match):

    LmrQuietBase 93, LmrQuietDivisor 205, LmrNoisyBase 13, LmrNoisyDivisor 333, LmrHistoryDivisor 5643,
    NullMoveBase 5, LmpBase 8, HistoryPruneMultiplier 2220, HistoryBonusQuadratic 24, HistoryBonusLinear 54,
    HistoryBonusMax 2212, SingularDepth 6, IirDepth 2, NonPawnCorrection true

Usage:
    python3 check_settings_values.py                     # check every harness in this folder
    python3 check_settings_values.py path/to/harness.py  # check one

Exit 0 only when EVERY harness matches the canonical values exactly.
"""
import glob
import importlib.util
import os
import sys

# The canonical S14 list, copied from the brief above. If this ever disagrees with the brief, the BRIEF wins
# and this constant is the thing that is wrong.
CANON_S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
CANON_PC20X = {
    "CuckooRep": "true", "HistRework": "2", "TtPruneV2": "true", "CorrHistV2": "true",
    "MateAlphaGuard": "true", "OwnBook": "false",
}
CANON_BASE = {"Hash": "16", "Threads": "1"}


def parse_list(entries):
    """Parse BOTH spellings in use: "Name X" and "Name value X" -> {Name: X}.

    Two formats exist because the harnesses write "Hash 16" and send
    `setoption name <first> value <last>`, while check_settings.py writes "Hash value 16" and
    splits on " value ". A checker that understood only one reported the other as malformed --
    which is what my first version did, flagging six healthy harnesses.
    """
    out = {}
    dupes = []
    for e in entries:
        if " value " in e:
            name, value = e.rsplit(" value ", 1)
        else:
            parts = e.rsplit(" ", 1)
            if len(parts) != 2:
                continue
            name, value = parts
        if name in out:
            dupes.append(name)
        out[name] = value
    return out, dupes


def load(path):
    name = "m_" + os.path.basename(path).replace(".", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def check_one(path):
    """Return (problems, note). problems == [] means the values match canon."""
    try:
        m = load(path)
    except Exception as e:  # a harness that cannot even import is a problem
        return ["cannot import: %s" % str(e)[:80]], ""
    s14 = getattr(m, "S14", None)
    x = getattr(m, "PC20X", None) or getattr(m, "PC20_EXTRA", None)
    if s14 is None:
        return [], "no S14 list (not a PC20 harness)"

    problems = []
    got14, dup14 = parse_list(s14)
    if dup14:
        problems.append("duplicate in S14: %s" % dup14)
    for k, v in CANON_S14.items():
        if k not in got14:
            problems.append("S14 missing %s" % k)
        elif got14[k] != str(v):
            problems.append("S14 %s = %s, canon %s" % (k, got14[k], v))
    for k in got14:
        if k not in CANON_S14:
            problems.append("S14 has extra option %s = %s" % (k, got14[k]))

    if x is not None:
        gotx, dupx = parse_list(x)
        if dupx:
            problems.append("duplicate in PC20X: %s" % dupx)
        for k, v in CANON_PC20X.items():
            if k not in gotx:
                problems.append("PC20X missing %s" % k)
            elif gotx[k] != str(v):
                problems.append("PC20X %s = %s, canon %s" % (k, gotx[k], v)
                                )
        for k in gotx:
            if k not in CANON_PC20X:
                problems.append("PC20X has extra option %s = %s" % (k, gotx[k]))
    return problems, ""


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(here, "*.py")))
    bad = 0
    checked = 0
    for path in paths:
        problems, note = check_one(path)
        base = os.path.basename(path)
        if note:
            print("%-32s SKIP  %s" % (base, note))
            continue
        checked += 1
        if problems:
            bad += 1
            print("%-32s ** %d PROBLEM(S) **" % (base, len(problems)))
            for p in problems:
                print("   %s" % p)
        else:
            print("%-32s values match canon" % base)
    print()
    print("%d harness(es) checked by VALUE; %d with problems" % (checked, bad))
    if bad == 0:
        print("PASS: every PC20 harness sends the canonical S14 and PC20 values, not just the right count")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
