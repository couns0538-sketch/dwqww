#!/usr/bin/env python3
"""pc20.py — shared setup for running any check under PC20 on the PC r15 build.

PC20 (file 5) = the 14 S14 settings, then CuckooRep true, HistRework 2, TtPruneV2 true,
CorrHistV2 true, MateAlphaGuard true, OwnBook false; Threads 1, Hash 16 (the thread rule).

Every check imports this so the settings are stated once and provably identical.
"""
PC20 = [
    "LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
    "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
    "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
    "SingularDepth 6", "IirDepth 2", "NonPawnCorrection true",
    # the six PC20 extras
    "CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true",
    "MateAlphaGuard true", "OwnBook false",
    # the thread rule
    "Threads 1", "Hash 16",
]

# the same list as UCI lines, for the waiting driver
PC20_LINES = [f"setoption name {o.partition(' ')[0]} value {o.partition(' ')[2]}" for o in PC20]


def describe():
    return "PC20 (S14 + CuckooRep/HistRework 2/TtPruneV2/CorrHistV2/MateAlphaGuard/OwnBook false, Threads 1, Hash 16)"
