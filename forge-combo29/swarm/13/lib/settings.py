"""Shared settings definitions with built-in assertions.

WHY THIS EXISTS: twice in this run I built a "PC20" list that was missing the 14 S14 settings, so a
whole grid measured PC6 while labelling itself PC20. Both times the result was a plausible wrong number
(the second doubled the allocation figure: 457 ms where the truth was 145 ms). Copying the list into each
script is what allowed that, so the list now lives here once and every script imports it.

The assertions are the point: a settings list is not evidence of what was sent, only its length and
membership are. Import this module and you cannot quietly have a short list.

Usage:
    from settings import PC20, S14, PC6, NO_OPTIONS, describe
    OPTS = PC20                      # 22 entries, asserted at import
    print(describe(OPTS))            # one-line summary for the report

If a script needs a different regime it must build it from these pieces, so it inherits the checks:
    OPTS = BASE + S14                # 16
    OPTS = BASE + S14 + PC6          # 22  == PC20
"""

# The four honesty-pin settings regimes, as the swarm defined them.
BASE = [("Threads", "1"), ("Hash", "16")]
NO_OPTIONS = []                      # a fresh engine, no setoption at all (the pins' regime)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]

PC6 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
       ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

PC20 = BASE + S14 + PC6

# ---- the assertions -------------------------------------------------------
# Every list above is checked at import time, so importing this module is itself the guard.
assert len(S14) == 14, "S14 must hold exactly the 14 settings of FABLE file 1, found %d" % len(S14)
assert len(PC6) == 6, "PC6 must hold exactly the six PC settings, found %d" % len(PC6)
assert len(BASE) == 2, "BASE must be Threads + Hash, found %d" % len(BASE)
assert len(PC20) == 22, ("PC20 must be Threads+Hash+14 S14+6 PC settings = 22, found %d - if you edited "
                         "this list, check you did not drop a section" % len(PC20))
assert len({n for n, _v in PC20}) == 22, "PC20 has a duplicate option name"

# The names that a 'PC20' list MUST contain. A length check alone would pass a list that swapped one
# S14 entry for something else, so membership is checked too.
_REQUIRED_S14_NAMES = {"LmrQuietBase", "LmrQuietDivisor", "LmrNoisyBase", "LmrNoisyDivisor",
                       "LmrHistoryDivisor", "NullMoveBase", "LmpBase", "HistoryPruneMultiplier",
                       "HistoryBonusQuadratic", "HistoryBonusLinear", "HistoryBonusMax",
                       "SingularDepth", "IirDepth", "NonPawnCorrection"}
_REQUIRED_PC6_NAMES = {"CuckooRep", "HistRework", "TtPruneV2", "CorrHistV2", "MateAlphaGuard", "OwnBook"}
_names = {n for n, _v in PC20}
_missing = (_REQUIRED_S14_NAMES | _REQUIRED_PC6_NAMES | {"Threads", "Hash"}) - _names
assert not _missing, "PC20 is missing required options: %s" % sorted(_missing)


def describe(opts):
    """One-line, report-ready description of what a run actually sent."""
    names = [n for n, _v in opts]
    if not names:
        return "no setoption at all (fresh engine)"
    if opts == PC20:
        return "PC20 (Threads 1, Hash 16, 14 S14 settings, 6 PC settings) = %d options" % len(opts)
    if opts == S14:
        return "S14 (14 settings)"
    if opts == BASE:
        return "Threads 1, Hash 16"
    return "%d options: %s" % (len(opts), ", ".join(names))


def check(opts, expect_len=None, must_include=()):
    """Explicit check for a script that builds its own list. Raises with a clear message."""
    if expect_len is not None and len(opts) != expect_len:
        raise SystemExit("FAIL: settings list has %d entries, expected %d: %s"
                         % (len(opts), expect_len, [n for n, _v in opts]))
    have = {n for n, _v in opts}
    missing = set(must_include) - have
    if missing:
        raise SystemExit("FAIL: settings list is missing %s" % sorted(missing))
    return True
