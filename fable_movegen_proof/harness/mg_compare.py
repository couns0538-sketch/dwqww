"""mg_compare.py - compare two mgprobe transcripts (reference = lock probe, candidate = candidate probe).

Equality is byte equality of everything after the identity frame. When the bytes differ, the first differing
record is decoded on both sides and every differing field is named, the first one with its expected (reference)
and actual (candidate) value and the UCI position command that reaches it.

The identity frames are checked before anything is compared: the reference must come from the LOCK probe, the
candidate from the probe the caller expects, both from the same harness source and both with the null-move
block. So a wiring slip (lock against lock, or a probe built from another harness) cannot end as EQUAL.

The records are compared from the start, and a difference found BEFORE a cut or a malformed part of the
candidate output is reported as a difference: a candidate that diverges and then dies is not "a run to repeat".

Status values:
  EQUAL          every record byte-identical; `positions` position records were compared
  MISMATCH       a well-formed candidate record differs from the reference record: a candidate difference
  MALFORMED      the candidate output is missing, cut or not a transcript, and nothing differed before that.
                 If it repeats while the lock's run on the same input is clean, it is treated as a candidate
                 failure to analyse, not as a run to repeat for ever.
  HARNESS_ERROR  the reference is unusable, the identities are wrong, or the two outputs were made from
                 different inputs: no statement about the candidate

  python -I -B mg_compare.py REF CAND [--path CHUNK] [--tag TAG]
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


def _bit_diff(r, c, field, what_legal, what_check):
    k = next(i for i in range(min(len(r[field]), len(c[field]))) if r[field][i] != c[field][i]) if len(r[field]) == len(c[field]) else 0
    if len(r[field]) != len(c[field]):
        return f"{what_legal}: the per-move answers have different lengths ({len(r[field])} / {len(c[field])})"
    legal_bit = (r[field][k] ^ c[field][k]) & 1
    bit = 1 if legal_bit else 2
    name = what_legal if legal_bit else what_check
    mv = uci(r["all"][k]) if k < len(r["all"]) else "?"
    return f"{name} differs for generated move {mv}: expected {int(bool(r[field][k] & bit))}, got {int(bool(c[field][k] & bit))}"


def _diff_position(r, c):
    """Every differing field of two position records, the most telling ones first."""
    out = []
    ident = [f for f in ("playout", "ply") if r[f] != c[f]]
    if ident:
        return [f"position differs ({', '.join(ident)}): reference playout {r['playout']} ply {r['ply']} key {r['key']:016x}, "
                f"candidate playout {c['playout']} ply {c['ply']} key {c['key']:016x}: wrong position or desynchronised input"]
    if r["key"] != c["key"]:
        out.append(f"position key differs at the same playout and ply: reference {r['key']:016x}, candidate {c['key']:016x}: the candidate's "
                   f"make_move produced another position, or the two inputs are different (wrong position)")
    for f in ("pawn_key", "side", "castling", "ep", "halfmove", "fullmove"):
        if r[f] != c[f]:
            out.append(f"position state differs ({f}): expected {r[f]}, got {c[f]}")
    if r["legal"] != c["legal"]:
        out.append(_list_diff("legal move", r["legal"], c["legal"]))
    for f, label in (("all", "generated list All"), ("caps", "generated list Captures"), ("quiets", "generated list Quiets")):
        if r[f] != c[f]:
            out.append(_list_diff(label, r[f], c[f]))
    if r["bits"] != c["bits"]:
        out.append(_bit_diff(r, c, "bits", "is_legal", "gives_check"))
    if r["one_bits"] != c["one_bits"]:
        out.append(_bit_diff(r, c, "one_bits", "is_legal as the first query on a board without king lines", "gives_check as the first query on a board without king lines"))
    if r["post_bits"] != c["post_bits"]:
        out.append(_bit_diff(r, c, "post_bits", "is_legal after make and unmake", "gives_check after make and unmake"))
    if r["legal_caps"] != c["legal_caps"]:
        out.append(_list_diff("legal move (captures only)", r["legal_caps"], c["legal_caps"]))
    for f, route in (("checkers_main", "board reached by make_move with king lines"), ("checkers_twin", "board that never built king lines"),
                     ("checkers_fresh", "board set from the FEN"), ("checkers_direct", "direct attack test")):
        if r[f] != c[f]:
            out.append(f"checkers bitboard differs ({route}): expected {bb_text(r[f])}, got {bb_text(c[f])}")
    for f, route in (("child_main", "board with king lines"), ("child_one", "copy after one query")):
        if r[f] != c[f]:
            if len(r[f]) != len(c[f]):
                out.append(f"checkers after the makes differ in number ({route})")
                continue
            k = next(i for i in range(len(r[f])) if r[f][i] != c[f][i])
            legal = k < len(r["bits"]) and r["bits"][k] & 1
            out.append(f"checkers after the make of {uci(r['all'][k]) if k < len(r['all']) else '?'} differ ({route}): expected {bb_text(r[f][k])}, "
                       f"got {bb_text(c[f][k])}" + ("" if legal else " (this move is not legal: the search never makes it)"))
    for f, when in (("has_before", "before king lines exist"), ("has_after", "after king lines exist")):
        if r[f] != c[f]:
            out.append(f"has_legal_move differs ({when}): expected {r[f]}, got {c[f]}")
    for f, label in EVAL_FIELDS:
        if r[f] != c[f]:
            out.append(f"{label} differs: expected {r[f]}, got {c[f]}")
    rn, cn = r["null"], c["null"]
    if (rn is None) != (cn is None):
        out.append(f"null-move child presence differs: expected {rn is not None}, got {cn is not None}")
    elif rn is not None:
        if rn["has"] != cn["has"]:
            out.append(f"null-move child: has_legal_move differs: expected {rn['has']}, got {cn['has']}")
        if rn["all"] != cn["all"]:
            out.append("null-move child: " + _list_diff("generated list All", rn["all"], cn["all"]))
        if rn["bits"] != cn["bits"]:
            out.append("null-move child: " + _bit_diff({"all": rn["all"], "b": rn["bits"]}, {"all": cn["all"], "b": cn["bits"]}, "b", "is_legal", "gives_check"))
        if rn["child"] != cn["child"]:
            k = next((i for i in range(min(len(rn["child"]), len(cn["child"]))) if rn["child"][i] != cn["child"][i]), 0)
            out.append(f"null-move child: checkers after the make of {uci(rn['all'][k]) if k < len(rn['all']) else '?'} differ: "
                       f"expected {bb_text(rn['child'][k]) if k < len(rn['child']) else '?'}, got {bb_text(cn['child'][k]) if k < len(cn['child']) else '?'}")
    return out or ["records differ in bytes but no decoded field differs (codec defect)"]


def _diff(r, c):
    if r["kind"] == 0 and c["kind"] == 0:
        return _diff_position(r, c)
    if r["kind"] == 0 and c["kind"] == 1:
        return [f"legal move set differs: the candidate could not play the path move {c['uci']} "
                f"(missing from its legal list); the reference continued with playout {r['playout']} ply {r['ply']}"]
    if r["kind"] == 1 and c["kind"] == 1:
        return [f"unplayable path move differs: reference could not play {r['uci']}, candidate could not play {c['uci']}"]
    if r["kind"] == 254 and c["kind"] == 254:
        return [f"self-check counters differ: reference failures {r['hard']} / incremental differences {r['soft']}, "
                f"candidate failures {c['hard']} / incremental differences {c['soft']}; record counts {r['records']} / {c['records']}"]
    if r["kind"] == 2 and c["kind"] == 2:
        return [f"rejection of the FEN differs: expected [{r['error']}], got [{c['error']}] for {r['fen']} / {c['fen']}"]
    if r["kind"] == 2 or c["kind"] == 2:
        rej = r if r["kind"] == 2 else c
        who = "reference rejects, candidate accepts" if r["kind"] == 2 else "reference accepts, candidate rejects"
        return [f"handling of the FEN differs ({who}): {rej.get('fen', '?')} error [{rej.get('error', '')}]"]
    return [f"record kinds differ: reference kind {r['kind']}, candidate kind {c['kind']} (position desynchronised)"]


def _reference(ref, allow_error_records, expect_positions, require_null):
    """(frames, identity, trailer, number of position records) of a usable reference, or Malformed."""
    if len(ref) == 0:
        raise mg_format.Malformed("the output is empty")
    spans = mg_format.frames(ref)
    if len(spans) < 2 or mg_format.kind_of(ref, spans[0]) != 253:
        raise mg_format.Malformed("no identity frame at the start")
    ident = mg_format.decode(ref[spans[0][0]:spans[0][0] + spans[0][1]])
    if ident["tag"] != "LOCK":
        raise mg_format.Malformed(f"it was not written by the LOCK probe but by '{ident['tag']}'")
    if require_null and not ident["flags"] & 1:
        raise mg_format.Malformed("it was written without the null-move block")
    if mg_format.kind_of(ref, spans[-1]) != 254:
        raise mg_format.Malformed(f"no trailer: the output is cut after record {len(spans) - 1}")
    trailer = mg_format.decode(ref[spans[-1][0]:spans[-1][0] + spans[-1][1]])
    if trailer["records"] != len(spans) - 2:
        raise mg_format.Malformed(f"the trailer announces {trailer['records']} records but {len(spans) - 2} are present")
    if trailer["hard"] != 0:
        raise mg_format.Malformed(f"the lock probe reported {trailer['hard']} self-check failures")
    kinds = [mg_format.kind_of(ref, s) for s in spans[1:-1]]
    if not allow_error_records and any(k != 0 for k in kinds):
        raise mg_format.Malformed(f"it holds {sum(1 for k in kinds if k != 0)} records for rejected FENs or unplayable path moves: the path "
                                  f"file is not a path of the lock")
    n_positions = sum(1 for k in kinds if k == 0)
    if expect_positions is not None and n_positions != expect_positions:
        raise mg_format.Malformed(f"it holds {n_positions} positions, the input defines {expect_positions}")
    return spans, ident, trailer, n_positions


def compare(ref, cand, path_text=None, expect_tag=None, allow_error_records=False, expect_positions=None, require_null=True):
    try:
        rspans, rid, rtrailer, n_positions = _reference(ref, allow_error_records, expect_positions, require_null)
    except mg_format.Malformed as e:
        return Result("HARNESS_ERROR", 0, f"the reference transcript is not usable: {e}")
    if len(cand) == 0:
        return Result("MALFORMED", 0, "the candidate transcript is not usable: the output is empty (missing output)")
    cspans, cerror = mg_format.frames_tolerant(cand)
    if not cspans or mg_format.kind_of(cand, cspans[0]) != 253:
        return Result("MALFORMED", 0, f"the candidate transcript is not usable: no identity frame at the start ({cerror or 'first record is not an identity'})")
    try:
        cid = mg_format.decode(cand[cspans[0][0]:cspans[0][0] + cspans[0][1]])
    except mg_format.Malformed as e:
        return Result("MALFORMED", 0, f"the candidate identity frame cannot be decoded: {e}")
    if expect_tag is not None and cid["tag"] != expect_tag:
        return Result("HARNESS_ERROR", 0, f"identity: the candidate transcript was written by probe '{cid['tag']}', expected '{expect_tag}'")
    if cid["harness"] != rid["harness"] or cid["version"] != rid["version"]:
        return Result("HARNESS_ERROR", 0, f"identity: the two probes were built from different harness sources (reference {rid['version']} "
                      f"{rid['harness'][:16]}, candidate {cid['version']} {cid['harness'][:16]})")
    if (cid["flags"] & 1) != (rid["flags"] & 1):
        return Result("HARNESS_ERROR", 0, "identity: one transcript has the null-move block and the other has not")
    ro, co = rspans[1][0] - 8, (cspans[1][0] - 8 if len(cspans) > 1 else len(cand))
    if cerror is None and ref[ro:] == cand[co:]:
        return Result("EQUAL", n_positions, f"{n_positions} position records byte-identical ({len(rspans) - 2} records, {len(ref) - ro} bytes, "
                      f"candidate probe {cid['tag']}, incremental/refresh differences {rtrailer['soft']})")
    equal = 0
    for i in range(1, min(len(rspans), len(cspans))):
        (ao, an), (bo, bn) = rspans[i], cspans[i]
        rp, cp = ref[ao:ao + an], cand[bo:bo + bn]
        if rp == cp:
            if rp[6] == 0:
                equal += 1
            continue
        try:
            r, c = mg_format.decode(rp), mg_format.decode(cp)
        except mg_format.Malformed as e:
            return Result("MALFORMED", equal, f"record {i - 1} cannot be decoded: {e}")
        if c["kind"] == 254 and r["kind"] != 254:
            # the candidate's transcript ends here while the reference goes on
            present = i - 1
            if c["records"] != present or cerror:
                return Result("MALFORMED", equal, f"the candidate trailer announces {c['records']} records but {present} are present "
                              f"(missing output); the {equal} positions before it are identical")
            return Result("MISMATCH", equal, f"the candidate transcript ends after {present} records, the reference has {len(rspans) - 2}: "
                          f"the candidate probe stopped early at record {i - 1} (playout {r['playout']} ply {r['ply']})")
        fields = _diff(r, c)
        where = f"record {i - 1} (playout {r['playout']} ply {r['ply']})"
        replay = mg_format.replay_command(path_text, r["playout"], r["ply"]) if r["kind"] in (0, 1) else ""
        more = f" | {len(fields) - 1} more differing fields in this record: " + "; ".join(f[:90] for f in fields[1:6]) if len(fields) > 1 else ""
        cut = f" | the candidate output is also damaged later: {cerror}" if cerror else ""
        return Result("MISMATCH", equal, f"first difference at {where}: {fields[0]}{more}{cut}" + (f" | replay: {replay}" if replay else ""))
    if cerror:
        return Result("MALFORMED", equal, f"the candidate transcript is not usable: {cerror}; the {equal} positions before it are identical "
                      f"(missing output after them)")
    if mg_format.kind_of(cand, cspans[-1]) != 254:
        return Result("MALFORMED", equal, f"the candidate transcript has no trailer: the output is cut (missing output after record {len(cspans) - 2})")
    ctrailer = mg_format.decode(cand[cspans[-1][0]:cspans[-1][0] + cspans[-1][1]])
    if ctrailer["records"] != len(cspans) - 2:
        return Result("MALFORMED", equal, f"the candidate trailer announces {ctrailer['records']} records but {len(cspans) - 2} are present (missing output)")
    return Result("MISMATCH", equal, f"record counts differ: reference {len(rspans) - 2}, candidate {len(cspans) - 2} (missing or extra records)")


def compare_bound(ref, ref_input_sha, cand, cand_input_sha, path_text=None, **kw):
    """compare(), refused when the two outputs were not made from the same input."""
    if ref_input_sha != cand_input_sha:
        return Result("HARNESS_ERROR", 0, f"inputs differ: reference input sha256 {ref_input_sha}, candidate input sha256 "
                      f"{cand_input_sha}; the outputs are not comparable")
    return compare(ref, cand, path_text, **kw)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    ref = open(argv[1], "rb").read()
    cand = open(argv[2], "rb").read()
    path_text = open(argv[argv.index("--path") + 1], "r", encoding="ascii").read() if "--path" in argv else None
    tag = argv[argv.index("--tag") + 1] if "--tag" in argv else None
    res = compare(ref, cand, path_text, expect_tag=tag)
    print(f"{res.status}: positions equal {res.positions}; {res.detail}")
    return {"EQUAL": 0, "MISMATCH": 3, "MALFORMED": 2}.get(res.status, 1)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
