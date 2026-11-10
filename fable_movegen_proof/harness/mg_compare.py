"""mg_compare.py - compare two mgprobe transcripts (reference = lock probe, candidate = candidate probe).

Equality is byte equality of the whole transcript. When the bytes differ, the first differing record is
decoded on both sides and the differing field is named with the expected (reference) and actual (candidate)
value and the UCI position command that reaches it.

Status values:
  EQUAL          every record byte-identical; `positions` position records were compared
  MISMATCH       a well-formed candidate record differs from the reference record: a candidate difference
  MALFORMED      the candidate output is missing, cut or not a transcript: a run to repeat, not a verdict
  HARNESS_ERROR  the reference is unusable or the two outputs were made from different inputs

  python -I -B mg_compare.py REF CAND [--path CHUNK]
Exit 0 EQUAL, 3 MISMATCH, 2 MALFORMED, 1 HARNESS_ERROR or usage.
"""
import collections
import sys

import mg_format
from mg_format import bb_text, uci, ucis

Result = collections.namedtuple("Result", "status positions detail")

EVAL_FIELDS = (
    ("hce", "static eval, hand-crafted without cache"),
    ("off", "static eval net off (pawn-cache path)"),
    ("on_refresh", "static eval net on (refresh path)"),
    ("on_inc", "static eval net on (incremental path)"),
    ("net", "raw net output (eval term)"),
    ("rev1_off", "static eval net off of the position 1 plies back (stale-cache probe)"),
    ("rev8_off", "static eval net off of the position 8 plies back (stale-cache probe)"),
    ("rev8_on", "static eval net on of the position 8 plies back (stale-cache probe)"),
)


def _list_diff(name, ref, cand):
    """Text for two move lists that differ: set difference first, then order."""
    rs, cs = set(ref), set(cand)
    if rs != cs or len(ref) != len(cand):
        missing = [uci(m) for m in ref if m not in cs]
        extra = [uci(m) for m in cand if m not in rs]
        return (f"{name} set differs: missing {missing or '[]'}, extra {extra or '[]'} "
                f"(expected {len(ref)} moves, got {len(cand)}); expected {' '.join(ucis(ref))}; got {' '.join(ucis(cand))}")
    k = next(i for i in range(len(ref)) if ref[i] != cand[i])
    return (f"{name} order differs at index {k}: expected {uci(ref[k])}, got {uci(cand[k])} (same set of {len(ref)} moves); "
            f"expected {' '.join(ucis(ref))}; got {' '.join(ucis(cand))}")


def _diff_position(r, c):
    """The first differing field of two position records, in order of importance."""
    for f in ("playout", "ply", "key"):
        if r[f] != c[f]:
            return (f"position differs ({f}): reference playout {r['playout']} ply {r['ply']} key {r['key']:016x}, "
                    f"candidate playout {c['playout']} ply {c['ply']} key {c['key']:016x}: wrong position or desynchronised input")
    for f in ("pawn_key", "side", "castling", "ep", "halfmove", "fullmove"):
        if r[f] != c[f]:
            return f"position state differs ({f}): expected {r[f]}, got {c[f]}"
    if r["legal"] != c["legal"]:
        return _list_diff("legal move", r["legal"], c["legal"])
    for f, label in (("all", "generated list All"), ("caps", "generated list Captures"), ("quiets", "generated list Quiets")):
        if r[f] != c[f]:
            return _list_diff(label, r[f], c[f])
    if r["bits"] != c["bits"]:
        k = next(i for i in range(len(r["bits"])) if r["bits"][i] != c["bits"][i])
        what = "is_legal" if (r["bits"][k] ^ c["bits"][k]) & 1 else "gives_check"
        bit = 1 if what == "is_legal" else 2
        return (f"{what} differs for generated move {uci(r['all'][k])}: expected {int(bool(r['bits'][k] & bit))}, "
                f"got {int(bool(c['bits'][k] & bit))}")
    if r["legal_caps"] != c["legal_caps"]:
        return _list_diff("legal move (captures only)", r["legal_caps"], c["legal_caps"])
    for f, route in (("checkers_main", "board reached by make_move with king lines"), ("checkers_twin", "board that never built king lines"),
                     ("checkers_fresh", "board set from the FEN"), ("checkers_direct", "direct attack test")):
        if r[f] != c[f]:
            return f"checkers bitboard differs ({route}): expected {bb_text(r[f])}, got {bb_text(c[f])}"
    for f, route in (("child_main", "board with king lines"), ("child_one", "copy after one query")):
        if r[f] != c[f]:
            k = next(i for i in range(len(r[f])) if r[f][i] != c[f][i])
            return (f"checkers after the make of {uci(r['all'][k])} differ ({route}): expected {bb_text(r[f][k])}, "
                    f"got {bb_text(c[f][k])}")
    for f, when in (("has_before", "before king lines exist"), ("has_after", "after king lines exist")):
        if r[f] != c[f]:
            return f"has_legal_move differs ({when}): expected {r[f]}, got {c[f]}"
    for f, label in EVAL_FIELDS:
        if r[f] != c[f]:
            return f"{label} differs: expected {r[f]}, got {c[f]}"
    rn, cn = r["null"], c["null"]
    if (rn is None) != (cn is None):
        return f"null-move child presence differs: expected {rn is not None}, got {cn is not None}"
    if rn is not None:
        if rn["has"] != cn["has"]:
            return f"null-move child: has_legal_move differs: expected {rn['has']}, got {cn['has']}"
        if rn["all"] != cn["all"]:
            return "null-move child: " + _list_diff("generated list All", rn["all"], cn["all"])
        if rn["bits"] != cn["bits"]:
            k = next(i for i in range(len(rn["bits"])) if rn["bits"][i] != cn["bits"][i])
            return f"null-move child: is_legal differs for {uci(rn['all'][k])}: expected {rn['bits'][k] & 1}, got {cn['bits'][k] & 1}"
        if rn["child"] != cn["child"]:
            k = next(i for i in range(len(rn["child"])) if rn["child"][i] != cn["child"][i])
            return (f"null-move child: checkers after the make of {uci(rn['all'][k])} differ: expected {bb_text(rn['child'][k])}, "
                    f"got {bb_text(cn['child'][k])}")
    return "records differ in bytes but no decoded field differs (codec defect)"


def _diff(r, c):
    if r["kind"] == 0 and c["kind"] == 0:
        return _diff_position(r, c)
    if r["kind"] == 0 and c["kind"] == 1:
        return (f"legal move set differs: the candidate could not play the path move {c['uci']} "
                f"(missing from its legal list); the reference continued with playout {r['playout']} ply {r['ply']}")
    if r["kind"] == 254 and c["kind"] == 254:
        return (f"self-check counters differ: reference failures {r['hard']} / incremental differences {r['soft']}, "
                f"candidate failures {c['hard']} / incremental differences {c['soft']}; record counts {r['records']} / {c['records']}")
    if r["kind"] == 2 and c["kind"] == 2:
        return f"rejection of the FEN differs: expected [{r['error']}], got [{c['error']}] for {r['fen']}"
    if r["kind"] == 2 or c["kind"] == 2:
        rej, acc = (r, c) if r["kind"] == 2 else (c, r)
        who = "reference rejects, candidate accepts" if r["kind"] == 2 else "reference accepts, candidate rejects"
        return f"handling of the FEN differs ({who}): {rej.get('fen', '?')} error [{rej.get('error', '')}]"
    return f"record kinds differ: reference kind {r['kind']}, candidate kind {c['kind']} (position desynchronised)"


def _usable(data, who):
    """Frame list and trailer of a transcript, or Malformed."""
    if len(data) == 0:
        raise mg_format.Malformed(f"{who} output is empty (missing output)")
    spans = mg_format.frames(data)
    o, n = spans[-1]
    if mg_format.kind_of(data, spans[-1]) != 254:
        raise mg_format.Malformed(f"{who} transcript has no trailer: the output is cut (missing output after record {len(spans) - 1})")
    trailer = mg_format.decode(data[o:o + n])
    if trailer["records"] != len(spans) - 1:
        raise mg_format.Malformed(f"{who} trailer announces {trailer['records']} records but {len(spans) - 1} are present (missing output)")
    return spans, trailer


def compare(ref, cand, path_text=None):
    try:
        rspans, rtrailer = _usable(ref, "reference")
    except mg_format.Malformed as e:
        return Result("HARNESS_ERROR", 0, f"the reference transcript is not usable: {e}")
    if rtrailer["hard"] != 0:
        return Result("HARNESS_ERROR", 0, f"the reference probe reported {rtrailer['hard']} self-check failures")
    n_positions = sum(1 for s in rspans if mg_format.kind_of(ref, s) == 0)
    if ref == cand:
        return Result("EQUAL", n_positions, f"{n_positions} position records byte-identical ({len(rspans) - 1} records, "
                      f"{len(ref)} bytes, incremental/refresh differences {rtrailer['soft']})")
    try:
        cspans, _ = _usable(cand, "candidate")
    except mg_format.Malformed as e:
        return Result("MALFORMED", 0, f"the candidate transcript is not usable: {e}")
    equal = 0
    for i in range(min(len(rspans), len(cspans))):
        (ro, rn), (co, cn) = rspans[i], cspans[i]
        rp, cp = ref[ro:ro + rn], cand[co:co + cn]
        if rp == cp:
            if rp[6] == 0:
                equal += 1
            continue
        try:
            r, c = mg_format.decode(rp), mg_format.decode(cp)
        except mg_format.Malformed as e:
            return Result("MALFORMED", equal, f"record {i} cannot be decoded: {e}")
        where = f"record {i} (playout {r['playout']} ply {r['ply']})"
        replay = mg_format.replay_command(path_text, r["playout"], r["ply"]) if r["kind"] in (0, 1) else ""
        return Result("MISMATCH", equal, f"first difference at {where}: {_diff(r, c)}" + (f" | replay: {replay}" if replay else ""))
    return Result("MISMATCH", equal, f"record counts differ: reference {len(rspans) - 1}, candidate {len(cspans) - 1} (missing or extra records)")


def compare_bound(ref, ref_input_sha, cand, cand_input_sha, path_text=None):
    """compare(), refused when the two outputs were not made from the same input."""
    if ref_input_sha != cand_input_sha:
        return Result("HARNESS_ERROR", 0, f"inputs differ: reference input sha256 {ref_input_sha}, candidate input sha256 "
                      f"{cand_input_sha}; the outputs are not comparable")
    return compare(ref, cand, path_text)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    ref = open(argv[1], "rb").read()
    cand = open(argv[2], "rb").read()
    path_text = open(argv[argv.index("--path") + 1], "r", encoding="ascii").read() if "--path" in argv else None
    res = compare(ref, cand, path_text)
    print(f"{res.status}: positions equal {res.positions}; {res.detail}")
    return {"EQUAL": 0, "MISMATCH": 3, "MALFORMED": 2}.get(res.status, 1)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
