"""Check that every stated recommendation agrees with the fitted ceiling.

The recommendation is the only part of a findings section that is derivation
rather than measurement, so it is the part that drifts. This script re-derives it
from the grid and fails if any document states something else.

Checks:
  1. the recommendation printed by analysis.py matches the text in FINDINGS.md
  2. every "Hash <= N at M lines" clause in FINDINGS.md <= the fitted Hmax(M)
  3. the shipped report's rule (if a path is given) agrees with the same ceiling
  4. a deliberately wrong clause is rejected -- so the checker can fail

Usage:
    python3 check_advice.py --base grid-base.json
    python3 check_advice.py --base grid-base.json --shipped /path/forge-findings.md
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

import analysis

HERE = "FINDINGS.md"
ANALYSIS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analysis.py")

# The grid's smallest Hash column. No recommendation would name a ceiling below
# it (Hash < 8 MB changes node counts), so a smaller number paired with a line
# count is a measurement, not a ceiling.
HASH_FLOOR = 8
# The engine's MultiPV maximum (uci.cpp: 'option name MultiPV ... max 8').
MPV_MAX = 8


def fitted_ceiling(data: dict, conservative: bool) -> dict[int, int]:
    cells = analysis.table(data)
    cls = analysis.classify(cells, 1.5)
    hmax = {}
    for m in data["mpvs"]:
        safe = [h for h in data["hashes"] if cls.get((h, m), (False, 0))[0]]
        hmax[m] = max(safe) if safe else 0
    if conservative:
        hmax = {m: (hmax[m] if m == 1 else (48 if m == 2 else 24)) for m in hmax}
    return hmax


def normalise(text: str) -> str:
    """Strip markdown decoration so clause parsing sees plain prose.

    Line structure is PRESERVED: table rows and anchors (`^`/`$`) are meaningful,
    and an earlier version that collapsed all whitespace made `^\\| 6 \\| 256 \\|$`
    unmatchable, silently dropping every table-row ceiling.
    """
    text = re.sub(r"^\s*>+\s?", "", text, flags=re.M)   # blockquote markers
    text = text.replace("`", "")                        # inline code
    text = re.sub(r"[*_]", "", text)                    # emphasis
    text = re.sub(r"[ \t]+", " ", text)                 # horizontal only
    return text


def quotation_line_numbers(lines: list[str]) -> set[int]:
    """Lines that belong to a passage about the check rather than an assertion.

    A findings section routinely wraps a quotation across lines, so the cue word
    ("checker", "missed", "defect") can sit on the line ABOVE the one carrying the
    clause. Measured: the shipped report's

        serious miss was a comparison-first clause (`at 6 lines, Hash <= 256`),
        **exactly how a person would hand-edit a boundary**

    had no cue on its own line and was scored as a live recommendation. A window
    covering the clause line and the two lines before it is used instead.
    """
    cues = (
        "checker", "selftest", "self-test", "defect", "quotation", "quotes",
        "quoted", "missed", "planted", "regression", "fails", "failure",
        "bad clause", "wrong", "permissive", "lesson", "trap", "blind",
    )
    marked: set[int] = set()
    for i, line in enumerate(lines):
        low = line.lower()
        if any(c in low for c in cues):
            # A cue marks its own line and the two that follow, which is how far
            # a wrapped sentence usually carries.
            for j in (i, i + 1, i + 2):
                if j < len(lines):
                    marked.add(j)
    return marked


def recommendation_lines(text: str) -> str:
    """Restrict a document to passages that assert a ceiling.

    A checker cannot tell a claim from a quotation of it by grammar. Three
    concrete failures measured while building this:

      1. Scanning the whole document flagged a findings section's QUOTATION of
         the bad clause, failing a correct document.
      2. Narrowing to lines with a marker word ("recommend", ...) made a correct
         recommendation plus a permissive table row pass **entirely silently**.
      3. Dropping lines instead of blanking them breaks table parsing: a row's
         column header lives on an earlier line, so a per-line view cannot tell a
         `MultiPV | Hash` table from a measurement table. Measured: "| 6 | 256 |"
         parsed to nothing under per-line scoping.

    So lines are BLANKED rather than removed, preserving position and the
    surrounding table context for the parser.
    """
    lines = text.splitlines()
    marked = quotation_line_numbers(lines)
    kept = []
    for i, line in enumerate(lines):
        kept.append("" if i in marked else line)
    return "\n".join(kept)


def parse_clauses(text: str) -> list[tuple[int, int, int]]:
    """Find every ceiling bound to a line count. Returns [(ceiling, lo, hi)].

    Two surface forms both occur in practice and both must be caught, because a
    permissive clause written in the form the parser does not know is a silent
    pass:
        "48 MB at 2 lines"        -- number first (the generated sentence)
        "at 6 lines, Hash <= 256"  -- comparison first (a hand edit)
    """
    flat = normalise(text)
    out: list[tuple[int, int, int]] = []

    def lines(lo: str, hi: str | None) -> tuple[int, int]:
        return int(lo), int(hi) if hi else int(lo)

    # Form A: "48 MB at 2 lines" / "24MB for 3-6 lines" / bare "24 at 3-6 lines"
    # Also "256 MB works fine at 6 lines": the ceiling and the line count may be
    # separated by a few words, so allow a short gap that contains no digits.
    for m in re.finditer(
        r"(\d+)(?:\s*MB)?[^0-9\n]{0,20}?(?:at|for|with|up to|when using)\s*(\d+)"
        r"(?:\s*[-\u2013]\s*(\d+))?\s*lines?",
        flat, re.I,
    ):
        lo, hi = lines(m.group(2), m.group(3))
        # The line count is bounded by the engine's MultiPV max: "114 MB at 133
        # lines" is a quotation of a misread, not a ceiling.
        if not (1 <= lo <= MPV_MAX and 1 <= hi <= MPV_MAX):
            continue
        out.append((int(m.group(1)), lo, hi))

    # Form B: "at 6 lines, Hash <= 256" / "Hash <= 256 at 6 lines"
    for m in re.finditer(
        r"(?:at|for)\s*(\d+)(?:\s*[-\u2013]\s*(\d+))?\s*lines?[^.;]*?Hash\s*<=?\s*(\d+)", flat
    ):
        lo, hi = lines(m.group(1), m.group(2))
        out.append((int(m.group(3)), lo, hi))
    for m in re.finditer(
        r"Hash\s*<=?\s*(\d+)[^.;]*?(?:at|for)\s*(\d+)(?:\s*[-\u2013]\s*(\d+))?\s*lines?", flat
    ):
        lo, hi = lines(m.group(2), m.group(3))
        out.append((int(m.group(1)), lo, hi))

    # Form C: table rows / settings lines explicitly pairing a LINE COUNT with a
    # Hash VALUE IN MB. The pairing must be stated, never inferred from adjacency:
    # a bare integer table row is ambiguous with every measurement table in the
    # document. Measured failure: "| 3 | 124.7 | 259.7 | 135.0 |" (an allocation
    # table) was read as the clause "Hash <= 1 at 3 lines".
    for m in re.finditer(r"MultiPV\s*(?:=|:)?\s*(\d+)([^0-9\n|]*?)(\d{1,4})\s*MB", flat, re.I):
        gap = m.group(2).lower()
        # "MultiPV 1 at ANY Hash; otherwise 48 MB ..." is not a ceiling of 48 MB for
        # MPV 1 -- "any Hash" is unbounded. Reading it as 48 produced the bogus
        # clause (48,1,1) and made the generated sentence disagree with the doc.
        if "any" in gap:
            continue
        out.append((int(m.group(3)), int(m.group(1)), int(m.group(1))))
    # Form C: settings lines explicitly pairing a LINE COUNT with a Hash VALUE.
    # Bounded to a plausible Hash range: "133 lines: 114" is a count of lines in a
    # mate table, not a 114 MB ceiling, so 114 is below the Hash floor we accept.
    # The Hash floor is 8 MB (the grid's smallest column); below that the engine
    # changes node counts, so no recommendation would name it.
    # A line count is 1..8 (the engine's MultiPV max), so a pair like
    # "133 lines: 114" is a mate-table line count, not a ceiling. Both slots are
    # bounded: the line count by the engine's limit, the Hash by the floor.
    for m in re.finditer(r"(\d+)\s*lines?\s*[:=]\s*(\d{1,4})\s*(?:MB)?", flat, re.I):
        hash_mb, lc = int(m.group(2)), int(m.group(1))
        if HASH_FLOOR <= hash_mb <= 2048 and 1 <= lc <= MPV_MAX:
            out.append((hash_mb, lc, lc))
    # A markdown row is only a ceiling when its table's HEADER names Hash AND a
    # line count. The header may be several lines up (separator row, blanks).
    # The row must also be a two-column pairing: a wide measurement table like
    # "| `Hash*MPV <= K` | 144 | 4/48 | 3 | 1 |" is not a ceiling, and
    # mis-reading its last two cells produced the bogus clause "Hash <= 1 at 3".
    for m in re.finditer(r"^\s*\|\s*(\d+)\s*\|\s*(\d{1,4})\s*(?:MB)?\s*\|\s*$",
                         flat, re.I | re.M):
        mpv, hash_mb = int(m.group(1)), int(m.group(2))
        if not (1 <= mpv <= 8 and 1 <= hash_mb <= 2048):
            continue
        header = ""
        for chunk in reversed(flat[: m.start()].splitlines()):
            s = chunk.strip()
            if not s or set(s) <= set("|-: "):
                continue
            header = s.lower()
            break
        if "hash" in header and ("line" in header or "multipv" in header or "mpv" in header):
            out.append((hash_mb, mpv, mpv))
    return out


def effective_ceiling(text: str) -> dict[int, int] | None:
    """Expand clauses into {mpv: ceiling}. None when no clause is found."""
    clauses = parse_clauses(text)
    if not clauses:
        return None
    out: dict[int, int] = {}
    for c, lo, hi in clauses:
        for m in range(lo, hi + 1):
            out[m] = c
    return out


def permissive_outside_recommendations(text: str, ceiling: dict[int, int]) -> list[str]:
    """Clauses that look permissive but sit outside a recommendation line.

    These are NOT counted as failures, because they are typically quotations of
    a defect. They are reported instead, because the alternative -- silently
    skipping them -- is the same blind spot this checker exists to close: a hole
    that is printed is a constraint, one that is not is a claim of coverage.
    """
    keep = recommendation_lines(text)
    outside = text
    for line in keep.splitlines():
        outside = outside.replace(line, "", 1)
    found = []
    for c, lo, hi in parse_clauses(outside):
        bad = [m for m in range(lo, hi + 1) if m in ceiling and c > ceiling[m]]
        if bad:
            found.append(f"{c} MB at {lo}-{hi} lines (permissive for MPV {bad})")
    return found


def check(text: str, ceiling: dict[int, int], label: str) -> list[str]:
    failures = []
    scoped = recommendation_lines(text)
    clauses = parse_clauses(scoped)
    if not clauses:
        failures.append(f"{label}: no recommendation clause found at all")
        return failures
    for c, lo, hi in clauses:
        for m in range(lo, hi + 1):
            if m not in ceiling:
                failures.append(f"{label}: clause names MultiPV {m}, not a grid column")
                continue
            # A recommended ceiling may be more conservative than the fit, never
            # more permissive -- a permissive recommendation is a false-safe risk.
            if c > ceiling[m]:
                failures.append(
                    f"{label}: clause 'Hash <= {c} at {m} lines' is MORE permissive "
                    f"than the fitted ceiling {ceiling[m]}"
                )
    for note in permissive_outside_recommendations(text, ceiling):
        print(f"  noted (not a failure): {label} mentions a permissive clause "
              f"outside a recommendation line -- {note}")
    return list(dict.fromkeys(failures))


def read_or_fail(path: str, label: str, quiet: bool = False) -> str | None:
    """Read a required document. A missing input is a FAILURE, never a skip.

    A checker that silently passes when it cannot see its input is the same
    defect class as one that only parses its generator's surface form: it
    reports success for work it did not do.
    """
    try:
        with open(path) as fh:
            return fh.read()
    except FileNotFoundError:
        if not quiet:
            print(f"FAIL: {label} not found at {path!r} -- cannot verify it, so this is not a pass")
        return None
    except OSError as exc:
        if not quiet:
            print(f"FAIL: {label} unreadable at {path!r}: {exc}")
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--shipped", default=None)
    args = ap.parse_args()

    if not os.path.exists(args.base):
        print(f"FAIL: grid JSON not found at {args.base!r}")
        return 1

    data = analysis.load(args.base)
    cons = fitted_ceiling(data, conservative=True)
    fit = fitted_ceiling(data, conservative=False)
    print(f"fitted ceiling      : {fit}")
    print(f"conservative ceiling: {cons}")
    print(f"denominator: {len(data['cells'])} cells")

    # What the script itself prints. Running it is a check: if it errors, the
    # generated sentence cannot be trusted and neither can anything below.
    proc = subprocess.run([sys.executable, ANALYSIS, "--base", args.base],
                          capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(ANALYSIS)) or ".")
    if proc.returncode != 0:
        print(f"FAIL: {ANALYSIS} exited {proc.returncode}; cannot derive the sentence")
        print(proc.stderr.strip()[-600:])
        return 1
    m = re.search(r"^  (MultiPV 1 at any Hash.*)$", proc.stdout, re.M)
    if not m:
        print("FAIL: analysis.py printed no recommendation line")
        return 1
    generated = m.group(1).strip()
    print(f"generated           : {generated}")

    failures = []
    # Check 1: the generated sentence is itself consistent with the ceiling.
    failures += check(generated, cons, "analysis.py output")

    # Check 2: FINDINGS.md states the SAME effective ceiling as analysis.py.
    # Comparing expanded ceilings (not the sentence) keeps the check about the
    # rule rather than about wording, which is what actually has to agree.
    gen_ceiling = effective_ceiling(generated)
    findings = read_or_fail(HERE, HERE)
    if findings is None:
        failures.append(f"{HERE}: cannot read, so its recommendation is UNVERIFIED")
        findings_ceiling = None
    else:
        findings_ceiling = effective_ceiling(findings)
        if findings_ceiling is None:
            failures.append(f"{HERE}: no recommendation clause found at all")
        elif gen_ceiling is not None and findings_ceiling != gen_ceiling:
            diff = {m: (findings_ceiling.get(m), gen_ceiling.get(m))
                    for m in set(findings_ceiling) | set(gen_ceiling)
                    if findings_ceiling.get(m) != gen_ceiling.get(m)}
            failures.append(
                f"{HERE}: stated ceiling {findings_ceiling} != generated {gen_ceiling}; "
                f"per-MPV (stated, generated) differences: {diff}"
            )
        failures += check(findings, cons, HERE)

    # Check 3: the shipped section, if given.
    if args.shipped:
        shipped = read_or_fail(args.shipped, "shipped section")
        if shipped is None:
            failures.append("shipped section: cannot read, so its recommendation is UNVERIFIED")
        else:
            # The shipped doc may recommend the conservative form; it must not be
            # more permissive than the fit.
            failures += check(shipped, fit, "shipped section")

    # Check 4: the checker must reject known-bad clauses in EACH surface form it
    # claims to parse. A permissive clause written in an unparsed form is a silent
    # pass, so each alternative phrasing is tested rather than just one.
    permissive_wrong = [
        "Recommended: 256 MB for 6 lines.",
        "Recommended: cap Hash at 256 MB when using 6 lines.",
        "Recommended: MultiPV 6 is fine up to Hash 256.",
        "Recommended: Hash <= 48 at 2 lines; at 6 lines, Hash <= 256.",
        "Recommended: 48 MB at 2 lines and 24 MB at 3-6, except 256 MB at 6 lines.",
        "Recommended: 48 MB at 2 lines, 24 MB at 3-6 lines, and 256 MB for 6 lines.",
    ]
    for bad in permissive_wrong:
        if not check(bad, cons, "selftest"):
            failures.append(f"selftest: permissive clause ACCEPTED -> {bad}")
    # And a correct clause in each form must be accepted, or the check is useless.
    correct = [
        "Recommended: Hash <= 48 at 2 lines, 24 at 3-6 lines.",
        "MultiPV 1 at any Hash; otherwise 48 MB at 2 lines, 24 MB at 3-6 lines.",
    ]
    for good in correct:
        if check(good, cons, "selftest"):
            failures.append(f"selftest: correct clause REJECTED -> {good}")

    # Check 5: a permissive clause must not escape by surface form, and a
    # measurement table must not be MISREAD as one. Both directions matter: an
    # escape hides a defect, a misread fails a correct document. Every case below
    # was a real misbehaviour measured while building this checker.
    REC = "Recommended: 48 MB at 2 lines, 24 MB at 3-6 lines.\n"
    escapes = [
        ("table row", REC + "\n| MultiPV | Hash |\n|---|---|\n| 6 | 256 |\n"),
        ("settings line", REC + "MultiPV = 6, Hash 256 MB."),
        ("labelled row", REC + "6 lines: 256 MB"),
        ("bare assertion", REC + "256 MB works fine at 6 lines."),
        ("comparison-first", REC + "at 6 lines, Hash <= 256."),
    ]
    for name, text in escapes:
        fails = check(text, cons, f"selftest/{name}")
        # The failure must be the permissive-ceiling one, not merely any failure:
        # a case that "fails" because no clause parsed is not a detection.
        if not any("MORE permissive" in f for f in fails):
            failures.append(
                f"selftest: permissive clause via {name} was not DETECTED as permissive "
                f"(got {fails or 'a clean pass'})"
            )

    not_clauses = [
        ("allocation table", REC + "\n| MPV | alloc | total | nodes | ns |\n"
                                      "|---|---|---|---|---|\n| 3 | 124.7 | 259.7 | 104331 | 1294 |\n"),
        ("fitted-forms table", REC + "\n| predicate | K | wrong | false-safe | false-alarm |\n"
                                        "|---|---|---|---|---|\n| `Hash*MPV <= K` | 144 | 4/48 | 3 | 1 |\n"),
        ("quotation", REC + "One checker missed the clause (`at 6 lines, Hash <= 256`)."),
    ]
    for name, text in not_clauses:
        if check(text, cons, f"selftest/{name}"):
            failures.append(f"selftest: a measurement table/quotation was MISREAD as a clause ({name})")

    # Check 6: a quotation must be surfaced, not dropped silently.
    quote = (REC + "One checker missed the comparison-first clause "
             "(`at 6 lines, Hash <= 256`), exactly how a person edits.")
    if not permissive_outside_recommendations(quote, cons):
        failures.append("selftest: the quotation was dropped silently instead of being noted")

    # Check 7: the Hash floor must be SAFE, not merely convenient. A clause below
    # the floor is skipped, so it must be provably more conservative than every
    # ceiling -- otherwise the floor silently hides a permissive clause.
    lowest_ceiling = min(v for m, v in cons.items() if m > 1)
    if HASH_FLOOR > lowest_ceiling:
        failures.append(
            f"selftest: HASH_FLOOR={HASH_FLOOR} can skip a clause that is NOT "
            f"conservative (lowest ceiling is {lowest_ceiling} MB)"
        )
    # And the floor must actually be the controlling bound, not shadowed by a
    # digit quantifier: measured once, \\d{2,4} made an "8 MB floor" a 10 MB floor.
    if not parse_clauses(f"6 lines: {HASH_FLOOR} MB"):
        failures.append(
            f"selftest: '6 lines: {HASH_FLOOR} MB' does not parse, so HASH_FLOOR "
            f"is not the controlling bound"
        )
    if parse_clauses(f"6 lines: {HASH_FLOOR - 1} MB"):
        failures.append(
            f"selftest: '6 lines: {HASH_FLOOR - 1} MB' parsed despite being below the floor"
        )
    print(f"selftest            : Hash floor {HASH_FLOOR} MB is the controlling bound "
          f"and skips only clauses <= {HASH_FLOOR - 1} MB < lowest ceiling {lowest_ceiling} MB")

    # A line count above the engine's MultiPV max cannot be a recommendation, so
    # bounding it cannot hide one. Assert that, rather than relying on it.
    if MPV_MAX < max(data["mpvs"]):
        failures.append(
            f"selftest: MPV_MAX={MPV_MAX} is below the grid's largest MPV "
            f"{max(data['mpvs'])}, so the bound could skip a real column"
        )
    for high_lc in (9, 133):
        if parse_clauses(f"6 lines: 256 MB" if high_lc == 9 else f"{high_lc} lines: 114"):
            # Above-max line counts may or may not parse, but if they do they must
            # not produce a clause in a grid column.
            for c, lo, hi in parse_clauses(f"{high_lc} lines: 114"):
                if lo <= max(data["mpvs"]):
                    failures.append(
                        f"selftest: '{high_lc} lines' produced a clause inside a real column"
                    )
    print(f"selftest            : line counts bounded at MPV_MAX={MPV_MAX} "
          f"(grid max {max(data['mpvs'])}, so the bound skips no real column)")

    print(f"selftest            : {len(permissive_wrong)} permissive forms rejected, "
          f"{len(correct)} correct forms accepted")
    print(f"selftest            : {len(escapes)} escape-by-surface-form cases rejected, "
          f"{len(not_clauses)} non-clause tables/quotations not misread")
    # Check 5: a MISSING input must fail, never silently pass. This is the same
    # defect class as parsing only the generator's form: reporting success for
    # work not done.
    if read_or_fail("/nonexistent/report.md", "selftest", quiet=True) is not None:
        failures.append("selftest: read_or_fail returned content for a missing file")
    print("selftest            : missing input fails rather than passing (silent by design)")
    print("selftest limit      : a spelled-out line count ('six lines') is NOT parsed; "
          "the check only sees numeric clauses")

    if failures:
        print("\nFAIL")
        for f in failures:
            print("  -", f)
        return 1
    print("\nPASS: every stated recommendation is at least as conservative as the fitted ceiling")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
