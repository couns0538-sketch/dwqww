"""Fable 2026-11-23, server-day plan (SETUP_PLAN.md rows 6 and 11; the first read's findings on uciproc.py,
drive.py and check_run.py): ONE table of what the frozen engine may say. Standard library only; the same file
runs on the PC and on Linux, and the player, the driver and the transcript checker all use this one table.

The rule is an ALLOW list, not a list of known bad lines: a line that is not one of the kinds a clean run
prints stops whatever was being done. The engine has one message with free text (`info string <error>` from its
old net loader) and may get new messages with a new source; a list of bad words cannot know those.

Every allowed kind is matched as a WHOLE line in the exact shape the source prints it (second version, after
Astra's read of the first: a bare prefix such as `info string eval hce ` with nothing behind it was accepted).
A cut-off line is therefore refused like an unknown one. Third version, after Astra's read of the second: the
search line and the option line had kept a free tail (`info depth 18 seldepth` and `option name Hash type
spinach` passed); both now have the source's exact forms. What the shapes do NOT judge: whether a score, a node
count or a checksum is the right one; that is the known answers' and the net check's work.

INFO_ALLOWED / INFO_REFUSING / INFO_NOT_ON_THE_DAY classify every `info string` literal of the engine's source
by its first words; tests/test_uciproc.py reads the source and fails on a literal that is in none of the three
(a new source needs a new look at this file).
"""
import re

# `info string ...` forms a clean run of the day prints (their first words; the whole shapes are below)
INFO_ALLOWED = ("NNUE v3 loaded: ", "NNUE v3 active: ", "eval hce ", "bench depth ")
# forms that say the engine did NOT take something, or found a fault
INFO_REFUSING = ("ERROR NNUE v3: ", "NNUE v3: NNUEArch is on and no network is loaded yet", "NNUE v3: no network loaded",
                 "V3 VERIFY FAILED at ply ", "cannot load book ", "illegal move ", "invalid FEN: ",
                 "invalid value for option ", "perft depth must be an integer from 0 to 10",
                 "searchmoves restriction has no legal root moves", "unknown option ")
# forms that are normal for the engine and must not appear on the day (a book, the clock's traces, the old loader)
INFO_NOT_ON_THE_DAY = ("book move ", "loaded book ", "loaded nnue ", "softnodes nodes ", "TmNodeShare ",
                       "TmFinishIteration hold depth ")

_PLAIN = re.compile(r"[ -~]*")                 # printable ASCII only: no NUL, no CR, no escape, no DEL
_MOVE = r"[a-h][1-8][a-h][1-8][qrbn]?"
_FEN = r"[1-8pnbrqkPNBRQK/]+ [wb] (-|[KQkq]{1,4}) (-|[a-h][36]) \d+ \d+"
# the net's own description (nnue_v3.cpp, describe): the path may hold spaces, so it is everything up to " hidden "
_NET = (r"v3 .+ hidden \d+ king_buckets \d+( mirrored)? output_buckets \d+ (residual|standalone) eval_scale \d+"
        r" checksum [0-9a-f]+ max\|w1\| \d+ max\|b1\| \d+ max\|w2\| \d+ kernel (avx512|avx2|scalar)")
_INFO_OK = re.compile(
    r"NNUE v3 (loaded|active): " + _NET
    + r"|eval hce -?\d+ nnue -?\d+ total -?\d+( incheck 1)?"
    + r"|bench depth \d+ nodes \d+ time \d+ nps \d+")
# a search line (search.cpp, the one `info depth` print): two token orders, the second when the engine shows
# more than one line a position; the move list may be empty and may hold `0000`, as the source prints them
_SCORE = r"(cp|mate) -?\d+"
_SEARCH = (r"info depth \d+ (seldepth \d+ score " + _SCORE + r"|multipv \d+ score " + _SCORE + r" seldepth \d+)"
           r" nodes \d+ nps \d+ hashfull \d+ time \d+ pv( (0000|" + _MOVE + r"))*")
# an option line (uci.cpp): the four forms the source prints, each type a whole word with its own tail
_OPTION = (r"option name \S.*? type (check default (true|false)|spin default -?\d+ min -?\d+ max -?\d+"
           r"|string default <empty>|button)")
_OTHER = re.compile(
    r"sg \d+ -?\d+ " + _MOVE + r" " + _FEN                                        # a row: ply score move fen
    + r"|sgend result (-1|0|1) reason (mate|stalemate|rule|plylimit|matescore|evallimit|drawadj)"
      r" plies \d+ run \d+ searches \d+ nodes \d+ fen " + _FEN + r" moves( " + _MOVE + r")*"
    + r"|" + _SEARCH
    + r"|bestmove " + _MOVE + r"( ponder " + _MOVE + r")?"
    + r"|readyok|uciok"
    + r"|id (name|author) .+"
    + r"|" + _OPTION
    + r"|" + _MOVE + r": \d+"                                                    # a perft line
    + r"|nodes \d+")                                                             # perft's total
# NOT in the table, on purpose: an empty line (no clean run prints one: 16 transcripts of the PC, 24 runs of
# Astra's) and `bestmove 0000` (the engine's answer to a search on a position without a legal move, which the
# day never asks for: it would mean that another position than the intended one was searched).


def why_not(line: str) -> str:
    """'' for a line the day expects; otherwise the reason it stops what was being done."""
    if not _PLAIN.fullmatch(line):
        return "a character outside printable ASCII (0x20 to 0x7e): " + ascii(line[:200])
    if line.startswith("info string "):
        rest = line[12:]
        if rest.startswith(INFO_ALLOWED):
            if _INFO_OK.fullmatch(rest):
                return ""
            return "an engine message that is cut off or not in its shape: " + line[:200]
        if rest.startswith(INFO_REFUSING):
            return "the engine refused: " + line[:200]
        return "an engine message the day does not expect: " + line[:200]
    if line.startswith("sgerror"):
        return "the engine gave the game up: " + line[:200]
    if _OTHER.fullmatch(line):
        return ""
    return "a line of no known kind: " + line[:200]
