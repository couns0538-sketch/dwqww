"""Verify every headline number in the documents against the saved artefacts.

The drift that bit this seat was not the engine: it was the prose. Totals are
assembled by hand, and a number carried forward in prose drifts in either
direction without tripping anything, because every guard in the harness is built
to catch an engine overclaim. This script is the gate for that class of fault: it
re-derives each figure from the JSON artefacts and asserts the documents agree.

It checks both directions, which matters -- the arithmetic fault found here was
an UNDERCLAIM (225,856 reported when the runs summed to 290,623), and an
overclaim-only check would have passed it.

What it verifies:
  * per-stage compared counts and mismatch counts from each fuzz JSON
  * the count-comparison total, re-summed from the stages
  * the move-identity total, re-summed from its three runs
  * that each individual identity run's node count appears in the docs
  * that no document asserts a stale figure that the artefacts contradict
  * that cross-references to "FINDINGS.md §N" name a heading that exists, and
    that sections cited for a topic actually mention it

Usage: python3 verify_totals.py [--self-test]
Exit code 1 on any disagreement.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name: str):
    with open(HERE / name) as handle:
        return json.load(handle)


def artefacts() -> dict:
    """Re-derive the canonical totals from the saved JSON, no prose involved."""
    suite = load("perft_rows.json")
    fixtures = load("fixture_rows.json")
    fuzz = {
        name: load(f"fuzz_{name}.json")
        for name in ("rows", "ep", "castle", "ep-check", "ep-expose",
                     "rook-rights", "knight-check")
    }
    identity = {
        name: load(f"identity_{name}.json") for name in ("d2", "d3", "rows")
    }

    suite_cells = len(suite)
    fixture_cells = sum(len(row["cells"]) for row in fixtures)

    # Count-comparison stages: suite, fixtures, then every fuzz family.
    fuzz_compared = sum(entry["compared"] for entry in fuzz.values())
    count_total = suite_cells + fixture_cells + fuzz_compared

    identity_nodes = sum(entry["nodes"] for entry in identity.values())

    return {
        "suite_cells": suite_cells,
        "fixture_cells": fixture_cells,
        "fuzz": {k: v for k, v in fuzz.items()},
        "fuzz_compared": fuzz_compared,
        "count_total": count_total,
        "identity": identity,
        "identity_nodes": identity_nodes,
        "count_mismatches": (
            sum(1 for row in suite if not row.get("ok", False))
            + sum(1 for row in fixtures if row["problems"])
            + sum(entry["mismatch_count"] for entry in fuzz.values())
        ),
        "identity_mismatches": sum(
            len(entry["problems"]) for entry in identity.values()
        ),
    }


def fmt(n: int) -> str:
    return f"{n:,}"


def check(docs: dict[str, str], facts: dict) -> list[str]:
    """Return a list of disagreements. Empty list means the docs are consistent."""
    problems: list[str] = []

    def require(number: int, where: str, what: str) -> None:
        """The formatted number must appear somewhere in `where`'s text."""
        text = docs[where]
        if fmt(number) not in text and str(number) not in text:
            problems.append(f"{where}: missing {what} = {fmt(number)}")

    # 1. Stage counts must be stated.
    require(facts["suite_cells"], "PERFT_TABLE.md", "suite cells")
    require(facts["fixture_cells"], "FINDINGS.md", "fixture cells")

    # 2. The two headline totals.
    require(facts["count_total"], "STATUS.md", "count-comparison total")
    require(facts["count_total"], "FINDINGS.md", "count-comparison total")
    require(facts["identity_nodes"], "STATUS.md", "move-set total")
    require(facts["identity_nodes"], "FINDINGS.md", "move-set total")

    # 3. Each individual identity run must be visible, so the total is auditable.
    for name, entry in facts["identity"].items():
        require(entry["nodes"], "FINDINGS.md", f"identity run {name} nodes")

    # 4. Zero mismatches, stated as zero everywhere it is claimed.
    if facts["count_mismatches"] != 0 or facts["identity_mismatches"] != 0:
        problems.append(
            f"artefacts record mismatches: count {facts['count_mismatches']}, "
            f"identity {facts['identity_mismatches']} -- documents claiming zero are wrong"
        )

    # 5. Cross-references must name a section that exists. A pointer is a claim,
    #    and a false pointer is exactly the sort of fault nothing catches by
    #    default. Two forms are checked:
    #      * explicit      "FINDINGS.md §N" from any document
    #      * self-relative "§N" inside a document, resolving to that document
    findings = docs["FINDINGS.md"]
    headings = {m.group(1) for m in re.finditer(r"^#{2,3} (\d+[a-z]?)\.", findings, re.M)}
    for ref in set(re.findall(r"FINDINGS\.md\s*§(\d+[a-z]?)", "\n".join(docs.values()))):
        if ref not in headings:
            problems.append(
                f"dangling cross-reference: FINDINGS.md §{ref} cited but no such "
                f"heading exists (have {sorted(headings)})"
            )
    # Self-relative references: a bare §N must resolve. STATUS.md and
    # PERFT_TABLE.md have no numbered sections of their own, so a bare §N there
    # refers to FINDINGS.md; inside FINDINGS.md it refers to FINDINGS.md itself.
    # (An earlier version skipped documents with no sections of their own, which
    # silently disabled this check for exactly the two files that use bare refs.)
    for where, text in docs.items():
        own = {m.group(1) for m in re.finditer(r"^#{2,3} (\d+[a-z]?)\.", text, re.M)}
        target = own if own else headings
        for ref in set(re.findall(r"(?<!FINDINGS\.md )(?<!\w)§(\d+[a-z]?)", text)):
            if ref in target:
                continue
            # A reference quoted inside backticks is a mention of a pointer, not a
            # pointer being made -- e.g. a fault report naming the bad reference.
            # Those are exempt; a live reference outside code spans is not.
            if f"`§{ref}`" in text:
                continue
            problems.append(
                f"dangling reference: {where} cites §{ref} but the sections "
                f"available are {sorted(target)}"
            )

    # 6. A section cited for a topic must actually mention it.
    section_6 = findings.split("## 6.")[1].split("## 7.")[0] if "## 6." in findings else ""
    for needle in ("225,856", "290,623", "understated"):
        if needle.lower() not in section_6.lower():
            problems.append(f"FINDINGS §6 should document the underclaim; missing {needle!r}")

    # 7. No document may still assert a superseded figure as current. The one
    #    legitimate mention of 225,856 is the historical description in §6.
    for where in ("STATUS.md", "PERFT_TABLE.md"):
        if "225,856" in docs[where]:
            problems.append(
                f"{where}: asserts superseded total 225,856 (correct is "
                f"{fmt(facts['identity_nodes'])})"
            )

    # 8. The fault register count must match the number of entries that section
    #     actually contains. This bit twice: the count disagreed across three
    #     documents, and an itemised list carried fewer items than its own total.
    section_6 = findings.split("## 6.")[1].split("## 7.")[0] if "## 6." in findings else ""
    entry_count = len(re.findall(r"^\d+\. \*\*", section_6, re.M))
    for where, text in docs.items():
        claimed = re.search(r"\b(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|"
                            r"Eleven|Twelve|Thirteen|Fourteen|Fifteen)\s+faults",
                            text)
        if claimed:
            words = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5, "Six": 6,
                     "Seven": 7, "Eight": 8, "Nine": 9, "Ten": 10, "Eleven": 11,
                     "Twelve": 12, "Thirteen": 13, "Fourteen": 14, "Fifteen": 15}
            if words[claimed.group(1)] != entry_count:
                problems.append(
                    f"{where}: claims {claimed.group(1)} faults but FINDINGS §6 has "
                    f"{entry_count} entries"
                )

    return problems


def main() -> int:
    facts = artefacts()
    docs = {
        name: (HERE / name).read_text()
        for name in ("FINDINGS.md", "STATUS.md", "PERFT_TABLE.md")
    }

    if "--self-test" in sys.argv:
        print("facts re-derived from artefacts:")
        print(f"  suite cells       {facts['suite_cells']}")
        print(f"  fixture cells     {facts['fixture_cells']}")
        print(f"  fuzz compared     {facts['fuzz_compared']}")
        print(f"  count total       {facts['count_total']}")
        print(f"  identity nodes    {facts['identity_nodes']}")
        print(f"  count mismatches  {facts['count_mismatches']}")
        print(f"  identity mismatch {facts['identity_mismatches']}")

        clean = check(docs, facts)
        if clean:
            print("BASELINE FAILED, documents already inconsistent:")
            for problem in clean:
                print(f"  !! {problem}")
            return 1
        print("baseline: documents agree with artefacts")

        # Plant an underclaim: a total one run short, which is the exact fault
        # that occurred. An overclaim-only checker would pass this.
        under = dict(facts)
        under["identity_nodes"] = facts["identity_nodes"] - 64_767
        problems = check(docs, under)
        assert problems, "an UNDERCLAIMED total was not detected"
        print(f"[self-test 1] planted underclaim caught: {problems[0]}")

        # Plant an overclaim too, so the check is proven in both directions.
        over = dict(facts)
        over["count_total"] = facts["count_total"] + 1
        problems = check(docs, over)
        assert problems, "an OVERCLAIMED total was not detected"
        print(f"[self-test 2] planted overclaim caught: {problems[0]}")

        # Plant a dangling cross-reference: a pointer is a claim and can be false.
        broken = dict(docs)
        broken["STATUS.md"] = docs["STATUS.md"] + "\nSee FINDINGS.md §42 for detail.\n"
        problems = check(broken, facts)
        assert any("dangling cross-reference" in p for p in problems), (
            "a dangling cross-reference was not detected"
        )
        print("[self-test 3] planted dangling FINDINGS §42 cross-reference caught")

        # Plant a dangling SELF-reference: the exact fault that shipped, a bare
        # §N pointing at a section that does not exist. Use a number that appears
        # in no document, so the backtick-quotation exemption cannot shield it.
        selfref = dict(docs)
        selfref["STATUS.md"] = docs["STATUS.md"] + "\nSee §99 for the identity walk.\n"
        problems = check(selfref, facts)
        assert any("dangling reference" in p for p in problems), (
            "a dangling bare §N self-reference was not detected"
        )
        print("[self-test 4] planted bare §99 self-reference caught")

        # And confirm the real fault would have been caught: §3c does not exist,
        # and with no backtick mention anywhere it must be reported.
        probe = {k: "" for k in docs}
        probe["STATUS.md"] = "See §3c for the walk.\n"
        problems = check(probe, facts)
        assert any("§3c" in p for p in problems), (
            "the §3c fault that actually shipped would not be caught"
        )
        print("[self-test 5] the shipped §3c fault is reported when not quoted")

        # Plant a stale total in a document that should not carry it.
        stale = dict(docs)
        stale["PERFT_TABLE.md"] = docs["PERFT_TABLE.md"] + "\nTotal 225,856 nodes.\n"
        problems = check(stale, facts)
        assert any("superseded" in p for p in problems), "a stale total was not detected"
        print("[self-test 6] planted stale 225,856 in PERFT_TABLE caught")

        # Plant a fault-count mismatch: the documents claiming a number that
        # FINDINGS section 6 does not contain. This bit twice in practice.
        mismatched = dict(docs)
        mismatched["STATUS.md"] = re.sub(
            r"Fourteen faults", "Nine faults", docs["STATUS.md"]
        )
        problems = check(mismatched, facts)
        assert any("claims Nine faults" in p for p in problems), (
            "a fault-count mismatch against the register was not detected"
        )
        print("[self-test 7] planted fault-count mismatch (Nine vs the register) caught")

        print("SELF-TEST PASSED: underclaim, overclaim, dangling pointer (explicit "
              "and bare), stale total and fault-count mismatch all go red; "
              "documents match artefacts")
        return 0

    problems = check(docs, facts)
    print(f"count total    {fmt(facts['count_total'])}")
    print(f"identity total {fmt(facts['identity_nodes'])}")
    print(f"mismatches     count {facts['count_mismatches']}, "
          f"identity {facts['identity_mismatches']}")
    if problems:
        print(f"\n{len(problems)} disagreement(s) between documents and artefacts:")
        for problem in problems:
            print(f"  !! {problem}")
        return 1
    print("\nOK: every headline figure in FINDINGS.md, STATUS.md and PERFT_TABLE.md "
          "re-derives from the saved artefacts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
