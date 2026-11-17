#!/usr/bin/env python3
"""sweep_universals.py <findings.md> [--rows]

Extract every UNIVERSAL claim from a findings table, so each one can be tested as a claim.

WHY. The S-C91 error was one wrong clause inside a correct finding: *"a fresh session gives no diagnostic at
all."* The finding was tested; the caveat was not. The caveat contained a **universal negative**, and a
universal negative is the cheapest kind of claim to test and the most expensive kind to get wrong, because a
reader trusts a caveat without checking it.

So: generate the list mechanically rather than recalling it. Recall finds the claims I already remember being
unsure about; a grep finds the ones I was sure about, which are the dangerous ones.

WHAT COUNTS AS A UNIVERSAL CLAIM. A phrase that asserts over ALL cases:
    never, cannot, can never, no ... at all, always, none, every, must, impossible,
    "only" (as a restriction), "no <noun>" when it means "zero of them"

Each hit is printed with its row id, the matched phrase, and enough context to test it. The output is a CHECKLIST,
not a verdict: some universals are true and provable by inspection (`bestmove 0000` is never a legal move).

CONTROLS, because a sweep that reports nothing looks identical to a clean sweep:
  1. an injected universal MUST be found
  2. a non-universal sentence MUST NOT be found
  3. a universal split across a table cell boundary MUST still be found (the rows are long, and a phrase
     straddling `|` would be missed by a naive line-based grep)
"""
import argparse
import re
import sys

# Ordered so the most specific phrases report first; `only` and `must` are last because they are the noisiest.
PATTERNS = [
    ("never", r"\bnever\b"),
    ("cannot", r"\bcannot\b"),
    ("can never", r"\bcan\s+never\b"),
    ("no ... at all", r"\bno\b[^.|]{0,60}?\bat all\b"),
    ("none", r"\bnone\b"),
    ("always", r"\balways\b"),
    ("every ... (universal)", r"\bevery\b[^.|]{0,40}?\b(is|are|gives|returns|produces)\b"),
    ("impossible", r"\bimpossible\b"),
    ("must (unconditional)", r"\bmust\b(?!\s+not)"),
    ("only (restriction)", r"\bonly\b"),
]

ROW_RE = re.compile(r"^\|\s*(S-[A-Za-z0-9]+)\s*\|(.*)$")


def sentences(text):
    """Split a cell into rough sentences so a hit can be reported with its own context."""
    parts = re.split(r"(?<=[.;!?])\s+", text)
    return [p for p in parts if p.strip()]


def scan(md):
    """Yield (row_id, phrase, sentence) for every universal claim in the findings table."""
    hits = []
    for ln in md.splitlines():
        m = ROW_RE.match(ln)
        if not m:
            continue
        rid, rest = m.group(1), m.group(2)
        # the cells, joined, because a phrase can straddle a `|`
        flat = " ".join(c.strip() for c in rest.split("|") if c.strip())
        for sent in sentences(flat):
            for name, pat in PATTERNS:
                if re.search(pat, sent, re.I):
                    hits.append((rid, name, sent.strip()))
                    break
    return hits


def run_controls():
    ok = True

    def chk(n, c, d=""):
        nonlocal ok
        print("  %-56s %s %s" % (n, "PASS" if c else "FAIL", d))
        if not c:
            ok = False

    print("controls:")
    inject = "| S-TEST1 | **a fresh session gives no diagnostic at all.** | x |"
    plain = "| S-TEST2 | the score was 30 cp and the move was e2e4. | x |"
    straddle = "| S-TEST3 | the engine is | never | going to do that |"
    h1 = scan(inject)
    h2 = scan(plain)
    h3 = scan(straddle)
    chk("1 an injected universal IS found", any(h[0] == "S-TEST1" for h in h1),
        "(%d hits)" % len(h1))
    chk("2 a non-universal sentence is NOT found", len(h2) == 0, "(%d hits)" % len(h2))
    chk("3 a universal straddling a cell boundary IS found",
        any(h[0] == "S-TEST3" for h in h3), "(%d hits)" % len(h3))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("findings")
    ap.add_argument("--rows", action="store_true", help="print row ids only")
    a = ap.parse_args()

    if not run_controls():
        print("\nCONTROLS FAILED - refusing to scan")
        sys.exit(2)

    md = open(a.findings, encoding="utf-8", errors="replace").read()
    hits = scan(md)

    if a.rows:
        seen = []
        for rid, _, _ in hits:
            if rid not in seen:
                seen.append(rid)
        print("\n".join(seen))
        print("\n%d rows contain at least one universal" % len(seen), file=sys.stderr)
        return

    cur = None
    for rid, name, sent in hits:
        if rid != cur:
            print("\n%s" % rid)
            cur = rid
        s = sent if len(sent) <= 200 else sent[:197] + "..."
        print("   [%-22s] %s" % (name, s))

    rows = len({h[0] for h in hits})
    print("\n%d universal claim(s) across %d row(s)" % (len(hits), rows))
    print("\nEach line is a CLAIM TO TEST, not a finding. The test is the one that worked on S-C91:")
    print("  'is there a case where this is not true?' - one command, and it must be able to return YES.")


if __name__ == "__main__":
    main()
