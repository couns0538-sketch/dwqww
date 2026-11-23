"""Fable 2026-11-23, server-day plan (SETUP_PLAN.md rows 6 and 11; the first read's findings on uciproc.py,
drive.py and check_run.py): ONE table of what the frozen engine may say. Standard library only; the same file
runs on the PC and on Linux, and the player, the driver and the transcript checker all use this one table.

The rule is an ALLOW list, not a list of known bad lines: a line that is not one of the kinds a clean run
prints stops whatever was being done. The engine has one message with free text (`info string <error>` from its
old net loader) and may get new messages with a new source; a list of bad words cannot know those.

EXPECTED is every kind of line seen in the PC's clean runs of the frozen workloads (profile, verify, start-up,
the six fixed games: 9,366 rows, 78 game ends, 36 depth lines). INFO_ALLOWED / INFO_REFUSING / INFO_NOT_ON_THE_DAY
classify every `info string` literal of the engine's source; tests/test_engine_lines.py reads the source and
fails on a literal that is in none of the three (a new source needs a new look at this file).
"""
import re

# `info string ...` forms a clean run of the day prints
INFO_ALLOWED = ("NNUE v3 loaded: ", "NNUE v3 active: ", "eval hce ", "bench depth ")
# forms that say the engine did NOT take something, or found a fault
INFO_REFUSING = ("ERROR NNUE v3: ", "NNUE v3: NNUEArch is on and no network is loaded yet", "NNUE v3: no network loaded",
                 "V3 VERIFY FAILED at ply ", "cannot load book ", "illegal move ", "invalid FEN: ",
                 "invalid value for option ", "perft depth must be an integer from 0 to 10",
                 "searchmoves restriction has no legal root moves", "unknown option ")
# forms that are normal for the engine and must not appear on the day (a book, the clock's traces, the old loader)
INFO_NOT_ON_THE_DAY = ("book move ", "loaded book ", "loaded nnue ", "softnodes nodes ", "TmNodeShare ",
                       "TmFinishIteration hold depth ")

_OTHER = re.compile(
    r"sg \d+ -?\d+ [a-h][1-8][a-h][1-8][qrbn]? \S+ [wb] \S+ \S+ \d+ \d+"      # a row: ply score move fen
    r"|sgend result -?[01] reason \S+ plies \d+ .*"
    r"|info depth \d+ .*"
    r"|bestmove [a-h][1-8][a-h][1-8][qrbn]?( ponder [a-h][1-8][a-h][1-8][qrbn]?)?"
    r"|readyok|uciok"
    r"|id (name|author) .*"
    r"|option name .+ type (check|spin|string|button|combo).*"
    r"|[a-h][1-8][a-h][1-8][qrbn]?: \d+"                                         # a perft line
    r"|nodes \d+"                                                               # perft's total
    r"|")                                                                       # an empty line


def why_not(line: str) -> str:
    """'' for a line the day expects; otherwise the reason it stops what was being done."""
    if line.startswith("info string "):
        rest = line[12:]
        if rest.startswith(INFO_ALLOWED):
            return ""
        if rest.startswith(INFO_REFUSING):
            return "the engine refused: " + line[:200]
        return "an engine message the day does not expect: " + line[:200]
    if line.startswith("sgerror"):
        return "the engine gave the game up: " + line[:200]
    if _OTHER.fullmatch(line):
        return ""
    return "a line of no known kind: " + line[:200]
