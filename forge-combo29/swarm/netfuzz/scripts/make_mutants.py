#!/usr/bin/env python3
"""Generate every net mutant from the pristine v3 net.

Rule from the brief: a mutant is derived from the real net, so the ONLY difference
from a valid net is the field under test. Two families:

  * header mutants are RE-CHECKSUMMED, so the FNV-1a check cannot be the thing that
    refuses them. Whatever refuses them is the field-level guard under test.
  * byte-flip mutants are NOT re-checksummed, so the checksum layer is under test.
  * the single `rechecksummed` case carries a valid checksum for altered weights; it
    must load (a checksum detects accident, not intent) and is the 12th damage case.

Also emits truncations at named boundaries and the oversized-dimension claims.

Prints a JSON manifest (field, offset, old, new, bytes, sha256) to stdout.
Usage: make_mutants.py <pristine net> <out dir>
"""
import hashlib
import json
import os
import struct
import sys

MASK = (1 << 64) - 1
IV = 14695981039346656037


def fnv1a(data):
    h = IV
    for byte in data:
        h = ((h ^ byte) * 1099511628211) & MASK
    return h


def reseal(raw, mutate):
    """Apply `mutate` to a bytearray copy, then recompute the trailing checksum."""
    data = bytearray(raw)
    mutate(data)
    data[len(data) - 8:] = struct.pack("<Q", fnv1a(bytes(data[:-8])))
    return bytes(data)


def put32(value):
    return lambda d: d.__setitem__(slice(20, 24), struct.pack("<I", value))


def set_u32(offset, value):
    return lambda d: d.__setitem__(slice(offset, offset + 4), struct.pack("<I", value))


def set_i32(offset, value):
    return lambda d: d.__setitem__(slice(offset, offset + 4), struct.pack("<i", value))


def set_byte(offset, value):
    return lambda d: d.__setitem__(offset, value)


def compose(*fns):
    def run(d):
        for fn in fns:
            fn(d)
    return run


def region(name):
    return {"name": name}


def main():
    pristine = sys.argv[1]
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    raw = open(pristine, "rb").read()

    version, header_bytes, inputs, hidden, kb, ob, flags, qa, qb, scale = struct.unpack_from(
        "<IIIIIIIiii", raw, 8)
    w1_bytes = 2 * kb * 768 * hidden
    w1_end = header_bytes + w1_bytes
    b1_end = w1_end + 2 * hidden
    w2_end = b1_end + 2 * ob * 2 * hidden
    b2_end = w2_end + 4 * ob
    assert b2_end + 8 == len(raw), (b2_end + 8, len(raw))

    cases = []          # (name, cls, field, offset, bytes, expect, note)

    def add(name, cls, field, offset, data, expect, note=""):
        path = os.path.join(outdir, name + ".fnn3")
        with open(path, "wb") as handle:
            handle.write(data)
        stored = struct.unpack_from("<Q", data, len(data) - 8)[0] if len(data) >= 8 else None
        computed = fnv1a(data[:-8]) if len(data) >= 8 else None
        cases.append({
            "name": name,
            "class": cls,
            "field": field,
            "offset": offset,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "checksum_stored": None if stored is None else "%016x" % stored,
            "checksum_computed": None if computed is None else "%016x" % computed,
            "checksum_valid": stored is not None and stored == computed,
            "expect": expect,
            "note": note,
        })

    # ---------- controls: must LOAD ----------
    add("ctrl_pristine", "control", "none (pristine file)", None, raw, "accept",
        "the net every mutant is derived from")
    add("ctrl_kingmap_permuted", "control", "king_bucket_map (in-range permutation)", 48,
        reseal(raw, lambda d: d.__setitem__(slice(48, 112), bytes(reversed(d[48:112])))),
        "accept", "valid-checksum header change that stays in range: proves refusals are not blanket")
    add("ctrl_outputmap_rotated", "control", "output_bucket_map (in-range rotation)", 112,
        reseal(raw, lambda d: d.__setitem__(slice(112, 145), bytes(list(d[112:145])[1:] + [0]))),
        "accept", "second valid-checksum in-range header change")
    add("ctrl_flags_residual_cleared", "control", "flags 2 -> 0 (mirror off)", 32,
        reseal(raw, set_u32(32, 0)), "accept", "flag removal stays legal")
    add("ctrl_weight_inrange", "control", "w1[0] 1 -> 2 (checksum resealed)", header_bytes,
        reseal(raw, lambda d: d.__setitem__(slice(header_bytes, header_bytes + 2),
                                             struct.pack("<h", 2))),
        "accept", "weight change with a valid checksum must load")

    # ---------- header mutants, all re-checksummed ----------
    add("hdr_magic", "header", "magic[0] 'F' -> 'X'", 0, reseal(raw, set_byte(0, ord("X"))),
        "refuse", "same length, same checksum validity")
    add("hdr_version_4", "header", "version 3 -> 4", 8, reseal(raw, set_u32(8, 4)), "refuse", "")
    add("hdr_version_0", "header", "version 3 -> 0", 8, reseal(raw, set_u32(8, 0)), "refuse", "")
    add("hdr_header_bytes_191", "header", "header_bytes 192 -> 191", 12,
        reseal(raw, set_u32(12, 191)), "refuse", "")
    add("hdr_header_bytes_256", "header", "header_bytes 192 -> 256", 12,
        reseal(raw, set_u32(12, 256)), "refuse", "a longer header would shift every block")
    add("hdr_inputs_767", "header", "inputs 768 -> 767", 16, reseal(raw, set_u32(16, 767)), "refuse", "")
    add("hdr_inputs_1536", "header", "inputs 768 -> 1536", 16, reseal(raw, set_u32(16, 1536)), "refuse", "")
    add("hdr_hidden_544", "header", "hidden 512 -> 544 (in range, x32, body not resized)", 20,
        reseal(raw, set_u32(20, 544)), "refuse", "in-range claim, size mismatch")
    add("hdr_hidden_480", "header", "hidden 512 -> 480 (in range, x32, body not resized)", 20,
        reseal(raw, set_u32(20, 480)), "refuse", "")
    add("hdr_hidden_1056", "header", "hidden 512 -> 1056 (> MaxHidden)", 20,
        reseal(raw, set_u32(20, 1056)), "refuse", "")
    add("hdr_hidden_0", "header", "hidden 512 -> 0 (< MinHidden)", 20,
        reseal(raw, set_u32(20, 0)), "refuse", "")
    add("hdr_hidden_500", "header", "hidden 512 -> 500 (not a multiple of 32)", 20,
        reseal(raw, set_u32(20, 500)), "refuse", "the AVX-512 kernel reads in 32-lane steps")
    add("hdr_king_9", "header", "king_buckets 8 -> 9 (in range, body not resized)", 24,
        reseal(raw, set_u32(24, 9)), "refuse", "")
    add("hdr_king_1", "header", "king_buckets 8 -> 1 (in range, body not resized)", 24,
        reseal(raw, set_u32(24, 1)), "refuse", "")
    add("hdr_king_33", "header", "king_buckets 8 -> 33 (> MaxKingBuckets)", 24,
        reseal(raw, set_u32(24, 33)), "refuse", "")
    add("hdr_king_0", "header", "king_buckets 8 -> 0", 24, reseal(raw, set_u32(24, 0)), "refuse", "")
    add("hdr_out_9", "header", "output_buckets 8 -> 9 (in range, body not resized)", 28,
        reseal(raw, set_u32(28, 9)), "refuse", "")
    add("hdr_out_17", "header", "output_buckets 8 -> 17 (> MaxOutputBuckets)", 28,
        reseal(raw, set_u32(28, 17)), "refuse", "")
    add("hdr_out_0", "header", "output_buckets 8 -> 0", 28, reseal(raw, set_u32(28, 0)), "refuse", "")
    add("hdr_flags_residual", "header", "flags 2 -> 3 (residual|mirror)", 32,
        reseal(raw, set_u32(32, 3)), "refuse", "loader accepts, UCI unloads: residual unsupported")
    add("hdr_flags_unknown", "header", "flags 2 -> 4 (unknown bit 2)", 32,
        reseal(raw, set_u32(32, 4)), "refuse", "")
    add("hdr_qa_254", "header", "qa 255 -> 254", 36, reseal(raw, set_i32(36, 254)), "refuse", "")
    add("hdr_qb_32", "header", "qb 64 -> 32", 40, reseal(raw, set_i32(40, 32)), "refuse", "")
    add("hdr_scale_0", "header", "eval_scale 400 -> 0", 44, reseal(raw, set_i32(44, 0)), "refuse", "")
    add("hdr_scale_10001", "header", "eval_scale 400 -> 10001 (> MaxEvalScale)", 44,
        reseal(raw, set_i32(44, 10001)), "refuse", "")
    add("hdr_reserved_1", "header", "reserved[15] 0 -> 1", 160, reseal(raw, set_byte(160, 1)),
        "refuse", "reserved bytes must be zero")
    add("hdr_kingmap_oob", "header", "king_bucket_map[0] 0 -> 8 (== king_buckets)", 48,
        reseal(raw, set_byte(48, 8)), "refuse", "index would read past w1's bucket range")
    add("hdr_kingmap_255", "header", "king_bucket_map[0] 0 -> 255", 48,
        reseal(raw, set_byte(48, 255)), "refuse", "")
    add("hdr_outmap_oob", "header", "output_bucket_map[0] 0 -> 8 (== output_buckets)", 112,
        reseal(raw, set_byte(112, 8)), "refuse", "index would read past w2")
    add("hdr_outmap_255", "header", "output_bucket_map[32] 7 -> 255", 144,
        reseal(raw, set_byte(144, 255)), "refuse", "")

    # ---------- oversized dimension claims (decompression-bomb shape) ----------
    add("bomb_max_dims", "bomb", "hidden 1024 / king 32 / out 16, body unchanged", 20,
        reseal(raw, compose(set_u32(20, 1024), set_u32(24, 32), set_u32(28, 16))),
        "refuse", "legal-range maxima: expected size ~50 MB, file is 6.3 MB")
    add("bomb_hidden_max_only", "bomb", "hidden 512 -> 1024, king/out unchanged", 20,
        reseal(raw, set_u32(20, 1024)), "refuse", "")
    add("bomb_king_max_only", "bomb", "king_buckets 8 -> 32, hidden/out unchanged", 24,
        reseal(raw, set_u32(24, 32)), "refuse", "")
    add("bomb_out_max_only", "bomb", "output_buckets 8 -> 16, hidden/king unchanged", 28,
        reseal(raw, set_u32(28, 16)), "refuse", "")

    # ---------- checksum-layer mutants, NOT re-checksummed ----------
    add("ck_flip_w1", "checksum", "w1 byte XOR 1 at file/3", len(raw) // 3,
        bytes(bytearray(raw[:len(raw) // 3]) + bytes([raw[len(raw) // 3] ^ 1]) + raw[len(raw) // 3 + 1:]),
        "refuse", "accidental weight damage")
    add("ck_flip_b1", "checksum", "b1 byte XOR 1", w1_end + 4,
        bytes(bytearray(raw[:w1_end + 4]) + bytes([raw[w1_end + 4] ^ 1]) + raw[w1_end + 5:]),
        "refuse", "")
    add("ck_flip_w2", "checksum", "w2 byte XOR 1", b1_end + 4,
        bytes(bytearray(raw[:b1_end + 4]) + bytes([raw[b1_end + 4] ^ 1]) + raw[b1_end + 5:]),
        "refuse", "")
    add("ck_flip_b2", "checksum", "b2 byte XOR 1", w2_end,
        bytes(bytearray(raw[:w2_end]) + bytes([raw[w2_end] ^ 1]) + raw[w2_end + 1:]),
        "refuse", "")
    add("ck_flip_scale", "checksum", "eval_scale low byte XOR 1 (in range: 400 -> 401)", 44,
        bytes(bytearray(raw[:44]) + bytes([raw[44] ^ 1]) + raw[45:]), "refuse",
        "the altered value is itself legal; only the checksum sees it")
    add("ck_flip_stored", "checksum", "stored checksum byte XOR 1", len(raw) - 1,
        bytes(bytearray(raw[:-1]) + bytes([raw[-1] ^ 1])), "refuse", "")

    # ---------- the 12th net: corruption plus a recomputed checksum ----------
    flip_off = len(raw) // 3
    recalc = bytearray(raw)
    recalc[flip_off] ^= 0xFF
    recalc[len(raw) - 8:] = struct.pack("<Q", fnv1a(bytes(recalc[:-8])))
    add("rechecksummed", "adversarial", "w1 byte XOR 0xFF at file/3, checksum recomputed", flip_off,
        bytes(recalc), "accept",
        "must load: FNV-1a detects accident, not intent")

    # ---------- truncation at every boundary ----------
    add("tr_zero", "truncation", "cut to 0 bytes", None, b"", "refuse", "")
    add("tr_8", "truncation", "cut to 8 bytes (magic only)", None, raw[:8], "refuse", "")
    add("tr_191", "truncation", "cut to 191 bytes (one short of the header)", None, raw[:191],
        "refuse", "")
    add("tr_header_192", "truncation", "cut at exactly the header length", None, raw[:192],
        "refuse", "header alone cannot carry a checksum")
    add("tr_200", "truncation", "cut at header + 8 bytes", None, raw[:200], "refuse",
        "first size that clears the minimum-length gate")
    add("tr_w1_start", "truncation", "cut at exactly the first weight block (header+w1)", None,
        raw[:w1_end], "refuse", "")
    add("tr_w1_mid", "truncation", "cut mid-w1 (header + w1/2)", None, raw[:header_bytes + w1_bytes // 2],
        "refuse", "")
    add("tr_w1_mid_block", "truncation", "cut mid-block: b1 cut in half", None, raw[:w1_end + hidden],
        "refuse", "")
    add("tr_w2_mid", "truncation", "cut mid-w2", None, raw[:b1_end + 2 * ob * hidden], "refuse", "")
    add("tr_b2_mid", "truncation", "cut mid-b2", None, raw[:w2_end + 8], "refuse", "")
    add("tr_drop_checksum", "truncation", "cut the last 8 bytes (all weights intact)", None, raw[:-8],
        "refuse", "stored 'checksum' would be the last 8 bytes of b2")
    add("tr_1_short", "truncation", "one byte short of complete", None, raw[:-1], "refuse", "")
    add("tr_extend_1", "truncation", "one byte past complete (appended 0x00)", None, raw + b"\x00",
        "refuse", "")
    add("tr_extra_block", "truncation", "an extra b1 block appended, checksum resealed", None,
        reseal(raw, lambda d: d.__setitem__(slice(len(d), len(d)), raw[w1_end:w1_end + 2 * hidden])),
        "refuse", "a duplicated layer: size check, not a header field")

    print(json.dumps({
        "pristine": {"path": pristine, "bytes": len(raw),
                     "sha256": hashlib.sha256(raw).hexdigest(),
                     "header": {"version": version, "header_bytes": header_bytes, "inputs": inputs,
                                "hidden": hidden, "king_buckets": kb, "output_buckets": ob,
                                "flags": flags, "qa": qa, "qb": qb, "eval_scale": scale},
                     "layout": {"w1": [header_bytes, w1_end], "b1": [w1_end, b1_end],
                                "w2": [b1_end, w2_end], "b2": [w2_end, b2_end],
                                "checksum": [b2_end, b2_end + 8]}},
        "outdir": outdir,
        "cases": cases,
    }, indent=1))


if __name__ == "__main__":
    main()
