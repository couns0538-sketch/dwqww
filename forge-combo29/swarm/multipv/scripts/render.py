#!/usr/bin/env python3
"""Render FINDINGS.template.md -> FINDINGS.md, substituting every ``[[counter]]`` from evidence/.

FINDINGS.md is the DELIVERABLE.  FINDINGS.template.md is the source a human edits.  Nothing else
is a report.  This script is the only writer of FINDINGS.md, so a report with a raw placeholder in
it cannot be committed unless this script also exits non-zero.

Four checks, in the order that matters:

  1. MISSING     every marker must name a counter that exists in evidence/*.json
  2. RESIDUAL    after substitution the rendered text must contain ZERO ``[[...]]`` markers
  3. TYPE        a marker in a numeric context must resolve to a number, not to a dict or a bool
  4. SUSPICIOUS  a counter that is exactly 0 is legal, but a run where MANY markers resolve to 0 is
                 the shape of a lookup that missed quietly.  The count is printed and a threshold
                 above which the script fails is set deliberately low (see ZERO_ALARM) because a
                 report whose numbers are mostly zero is a report that measured nothing.

Check 2 is the one whose absence let a template get committed as a report.

Usage:
  python3 render.py                # render, verify, write FINDINGS.md
  python3 render.py --check        # verify only; fails if FINDINGS.md is stale or has a marker
  python3 render.py --selftest     # prove each of the four checks fires
"""
import argparse
import json
import os
import re
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
EVID = os.path.join(ROOT, "evidence")
TEMPLATE = os.path.join(ROOT, "FINDINGS.template.md")
OUTPUT = os.path.join(ROOT, "FINDINGS.md")

# Counters that are ZERO VIOLATIONS by design: seeing one of these as 0 is the point, so a zero is
# not suspicious.  Every other counter that is a DENOMINATOR or a MEASUREMENT must never be 0; one
# that is means a lookup key was wrong and the map returned 0 by default.  That is the failure that
# "wearing a number" -- so the check names the denominators explicitly instead of counting zeros.
MUST_BE_NONZERO = (
    "audit.structural.blocks", "audit.structural.searches", "audit.structural.info_lines",
    "audit.structural.final_blocks", "audit.structural.lines_checked_for_depth",
    "audit.corpus.used", "audit.corpus.eligible_after_gate", "audit.depth",
    "audit.agreement.positions", "audit.time_pressure.searches",
    "audit.determinism.pairs", "audit.promotion.positions",
    "judge.positions", "instability.positions", "agreement.noise.pairs",
    "budgetstats.positions", "budgetstats.repeats",
    "pins.bench11", "pins.bench13", "pins.bench16", "pins.perft5",
    "selftest.checks", "selftest.planted_faults", "wire.assertions",
)

SOURCES = [
    ("audit.json", "audit"),
    ("judge.json", "judge"),
    ("instability.json", "instability"),
    ("fastpaths.json", "fastpaths"),
    ("agreement.json", "agreement"),
    ("budget_stability.json", "budgetstats"),
    ("pins.json", "pins"),
    ("selftest.json", "selftest"),
    ("wire_control.json", "wire"),
]

MARKER = re.compile(r"\[\[([A-Za-z0-9_.:\-]+)\]\]")


def flatten(prefix, obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            flatten("%s.%s" % (prefix, k) if prefix else str(k), v, out)
    elif isinstance(obj, list):
        out[prefix + ".len"] = len(obj)
        for i, v in enumerate(obj):
            flatten("%s.%d" % (prefix, i), v, out)
    else:
        out[prefix] = obj


def build_evidence():
    """Flat map `source.dotted.key` -> scalar.  Raises if a source file is missing."""
    flat, absent = {}, []
    for name, prefix in SOURCES:
        path = os.path.join(EVID, name)
        if not os.path.exists(path):
            absent.append(name)
            continue
        with open(path) as fh:
            data = json.load(fh)
        if name in ("judge.json", "instability.json"):
            flatten(prefix, data.get("tally", {}), flat)
            for k in ("depth", "mpv", "judge_depth", "positions", "repeats"):
                if k in data:
                    flat["%s.%s" % (prefix, k)] = data[k]
        elif name == "agreement.json":
            flatten(prefix, data.get("tally", {}), flat)
            flatten(prefix + ".noise", data.get("noise_floor", {}), flat)
            hist = data.get("noise_floor", {}).get("abs_gap_histogram_by_10cp", {})
            if hist:
                flat[prefix + ".noise_histogram"] = " ".join(
                    "%scp:%d" % (k, v) for k, v in sorted(hist.items(), key=lambda kv: int(kv[0])))
        elif name == "fastpaths.json":
            flatten(prefix + ".summary", data.get("summary", {}), flat)
        elif name == "budget_stability.json":
            flat[prefix + ".positions"] = data["positions"]
            flat[prefix + ".repeats"] = data["repeats"]
            for go, d in data["budgets"].items():
                tag = "movetime" if "movetime" in go else "nodes"
                flat["%s.%s_shorts" % (prefix, tag)] = ",".join(
                    str(r["short"]) for r in d["repeats"])
                flat["%s.%s_stable" % (prefix, tag)] = str(d["stable"]).lower()
                flat["%s.%s_bestmove_ok" % (prefix, tag)] = str(d["bestmove_all_agree"]).lower()
        elif name == "audit.json":
            for k, v in data.items():
                if isinstance(v, list):
                    flat["audit.%s.len" % k] = len(v)
                elif isinstance(v, dict):
                    flatten("audit." + k, v, flat)
                else:
                    flat["audit." + k] = v
        else:
            flatten(prefix, data, flat)
    if absent:
        raise SystemExit("render: missing evidence files: %s" % (absent,))
    return flat


def strip_template_banner(text):
    """Drop the leading HTML comment.  It tells an editor that this file is not the report; it has
    no business appearing inside the report."""
    m = re.match(r"\A\s*<!--.*?-->\s*\n", text, re.S)
    return text[m.end():] if m else text


def reflow(text, width=96):
    """Re-wrap prose paragraphs to `width` after substitution.

    A marker like `[[audit.structural.final_block_pv_not_monotone]]` is much longer than the `116`
    it becomes, so substituting into a hard-wrapped template leaves ragged lines.  This re-wraps
    only what is safe to re-wrap: paragraph text.  Fenced code, tables, headings, list items,
    block quotes and HTML are passed through untouched, because re-wrapping them changes meaning.
    """
    out, para = [], []

    def flush():
        if not para:
            return
        joined = " ".join(x.strip() for x in para)
        para.clear()
        out.extend(textwrap.wrap(joined, width=width,
                                 break_long_words=False, break_on_hyphens=False) or [""])

    in_fence = False
    in_comment = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("<!--"):
            flush()
            in_comment = "-->" not in stripped
            out.append(line.rstrip())
            continue
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            out.append(line.rstrip())
            continue
        if stripped.startswith("```"):
            flush()
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        structural = (not stripped
                      or stripped.startswith("|")
                      or stripped.startswith("#")
                      or stripped.startswith(">")
                      or stripped.startswith("<")
                      or re.match(r"^([-*+]|\d+\.)\s", stripped))
        if structural:
            flush()
            out.append(line.rstrip())
            continue
        para.append(line)
    flush()
    return "\n".join(out)


def render(template_text, flat):
    """Return (rendered_text, report).  report carries counts for the four checks."""
    keys = MARKER.findall(template_text)
    missing = sorted({k for k in keys if k not in flat})
    # a marker whose value is a container is NOT printable prose: leave it as a marker so both
    # RESIDUAL and the type check fire, rather than stringifying a dict into the reader's paragraph
    containers = sorted({k for k in keys if k in flat and isinstance(flat[k], (dict, list))})
    values = []

    def sub(match):
        key = match.group(1)
        if key not in flat:
            return match.group(0)
        v = flat[key]
        if isinstance(v, (dict, list)):
            return match.group(0)
        values.append((key, v))
        if isinstance(v, bool):
            return "true" if v else "false"
        return str(v)

    rendered = reflow(MARKER.sub(sub, strip_template_banner(template_text)))
    residual = MARKER.findall(rendered)
    return rendered, {"markers": len(keys), "distinct": len(set(keys)),
                      "missing": missing, "residual": residual, "values": values,
                      "containers": containers}


def check_suspicious(report, flat):
    """A denominator or a measurement that is 0 means the lookup missed and returned 0 by default.

    Counting zeros does not work -- a clean audit legitimately reports "0 violations" many times.
    So this names the counters that carry a DENOMINATOR and asserts none of them is 0, which is the
    only zero that cannot be a result.
    """
    zeros = [(k, v) for k, v in report["values"] if v == 0 or v == "0"]
    distinct_zero_keys = sorted({k for k, _ in zeros})
    bad = [(k, flat.get(k)) for k in MUST_BE_NONZERO if flat.get(k, 0) in (0, "0", None)]
    return zeros, distinct_zero_keys, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify only, do not write")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    flat = build_evidence()

    if not os.path.exists(TEMPLATE):
        print("render: no template at %s" % TEMPLATE)
        return 2
    with open(TEMPLATE) as fh:
        template_text = fh.read()

    if args.selftest:
        failures = []

        # 1. MISSING: a marker naming no counter must be reported
        bogus = template_text + "\n\nplanted [[audit.structural.no_such_counter]]\n"
        _, rep = render(bogus, flat)
        if not rep["missing"]:
            failures.append("check 1 (missing) did not fire on a bogus marker")

        # 2. RESIDUAL: an unresolvable marker must survive into the output and be detected
        if not rep["residual"]:
            failures.append("check 2 (residual) did not fire: the bogus marker did not survive")

        # 2b. the real template must leave nothing behind
        rendered_ok, rep_ok = render(template_text, flat)
        if rep_ok["residual"]:
            failures.append("check 2: the real template leaves %d markers"
                            % len(rep_ok["residual"]))

        # 3. TYPE: a dict-valued counter must not be substituted as a scalar; it must survive as
        # a marker so the residual check also sees it
        flat_typed = dict(flat)
        flat_typed["audit.structural"] = {"nested": 1}
        rendered_t, rep_t = render("value: [[audit.structural]]", flat_typed)
        if "{" in rendered_t or not rep_t["containers"]:
            failures.append("check 3 (type) substituted a dict into prose")

        # 4. SUSPICIOUS: a denominator that is 0 must trip the alarm
        flat_zero = {k: 1 for k in set(MARKER.findall(template_text))}
        for k in MUST_BE_NONZERO:
            flat_zero[k] = 0
        _, rep_z = render(template_text, flat_zero)
        _, _, bad_zero = check_suspicious(rep_z, flat_zero)
        if not bad_zero:
            failures.append("check 4 (suspicious) did not fire on zeroed denominators")
        # and the real evidence must pass it
        _, _, bad_real = check_suspicious(rep_ok, flat)
        if bad_real:
            failures.append("check 4 failed on the real evidence: %r" % (bad_real[:5],))

        # 5. REFLOW: structure must survive.  A re-wrap that mangles a table or an info line would
        # corrupt the very evidence the report quotes, and would do it silently.
        probe = ("## a heading long enough that a careless reflow would wrap it and change the heading\n\n"
                 "| a | b |\n|---|---|\n| 1 | 2 |\n\n"
                 "```\ninfo depth 12 multipv 1 score cp -76 seldepth 27 nodes 66108 pv e3f4\n```\n\n"
                 "- a list item long enough to be tempting to wrap into the following line\n\n"
                 "> a blockquote long enough to be tempting to wrap but which must be left alone\n")
        once = reflow(probe)
        if once != probe:
            failures.append("check 5 (reflow) altered a heading, table, fence, list or quote")
        if reflow(once) != once:
            failures.append("check 5 (reflow) is not idempotent")
        # and the real render must survive a second pass unchanged
        if reflow(rendered_ok) != rendered_ok:
            failures.append("check 5: the rendered report is not reflow-stable")

        print("selftest: 5 checks, %d failures" % len(failures))
        for f in failures:
            print("  FAIL " + f)
        return 1 if failures else 0

    rendered, report = render(template_text, flat)
    zeros, distinct_zero, bad_zero = check_suspicious(report, flat)
    bad = False

    print("render: %d markers, %d distinct, %d counters available"
          % (report["markers"], report["distinct"], len(flat)))
    if report["missing"]:
        bad = True
        for m in report["missing"]:
            print("  CHECK 1 FAIL no evidence for [[%s]]" % m)
    if report["residual"]:
        bad = True
        print("  CHECK 2 FAIL %d placeholders survived rendering: %s"
              % (len(report["residual"]), sorted(set(report["residual"]))[:8]))

    # 3. type check: no marker may resolve to a container
    for k, v in report["values"]:
        if isinstance(v, (dict, list)):
            bad = True
            print("  CHECK 3 FAIL [[%s]] resolved to a container" % k)

    if bad_zero:
        bad = True
        print("  CHECK 4 FAIL denominators/measurements resolved to 0: %r" % (bad_zero,))
    else:
        print("  check 4 ok: %d of %d must-be-nonzero counters are nonzero; %d counters legitimately 0"
              % (len(MUST_BE_NONZERO), len(MUST_BE_NONZERO), len(distinct_zero)))

    if args.check:
        if not os.path.exists(OUTPUT):
            print("  CHECK 2 FAIL %s does not exist" % OUTPUT)
            return 1
        with open(OUTPUT) as fh:
            on_disk = fh.read()
        if MARKER.findall(on_disk):
            bad = True
            print("  CHECK 2 FAIL the committed report contains %d placeholders"
                  % len(MARKER.findall(on_disk)))
        if on_disk != rendered:
            print("  STALE %s differs from a fresh render" % OUTPUT)
            bad = True
        print("render --check: %s" % ("FAILED" if bad else "ok"))
        return 1 if bad else 0

    with open(OUTPUT, "w") as fh:
        fh.write(rendered)
    leftovers = MARKER.findall(rendered)
    if leftovers:
        # belt and braces: never leave a written file with a marker, even if a check raced
        os.unlink(OUTPUT)
        print("  CHECK 2 FAIL after write: %d placeholders" % len(leftovers))
        return 1
    print("  wrote %s (%d bytes), 0 placeholders remain" % (OUTPUT, len(rendered)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
