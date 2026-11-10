"""Byte-range compare of two PE exes, with every differing range classified against the PE layout.

Why: the combo29 lock recipe (-g -gcodeview, lld --pdb) embeds in the exe the absolute PDB path and an
8-byte hash of the PDB contents (CodeView RSDS record, GUID = hash + "LLD PDB."). The PDB covers source
checksums and line numbers, so ANY source edit - even behind a switch at 0 - changes those bytes. A
switch-0 build can therefore never have the lock's sha256; what can and must hold is that every other
byte is equal. This tool proves exactly that (same method as QA's orch_c2.ps1 byte compare, plus the
classification).

Allowed regions (class DEBUG): the IMAGE_DEBUG_DIRECTORY entries, the CodeView record, and the
VirtualSize field of the section that holds them (it follows the path length).
Everything else is class OTHER.

usage: bytecmp.py A.exe B.exe [--json OUT.json]
exit 0 = sha-identical or DEBUG-only differences; 3 = OTHER differences or different length; 1 = error
"""
import hashlib
import json
import struct
import sys


def pe_layout(b: bytes) -> dict:
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    if b[pe:pe + 4] != b"PE\0\0":
        raise ValueError("not a PE file")
    nsec = struct.unpack_from("<H", b, pe + 6)[0]
    opt_size = struct.unpack_from("<H", b, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from("<H", b, opt)[0]
    if magic != 0x20B:
        raise ValueError(f"not PE32+ (magic {magic:#x})")
    dd = opt + 112
    dbg_rva, dbg_size = struct.unpack_from("<II", b, dd + 6 * 8)
    sec_tab = opt + opt_size
    secs = []
    for i in range(nsec):
        o = sec_tab + 40 * i
        name = b[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, va, rsize, rptr = struct.unpack_from("<IIII", b, o + 8)
        secs.append({"name": name, "hdr": o, "vsize": vsize, "va": va, "rsize": rsize, "rptr": rptr})

    def off(rva):
        for s in secs:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rsize"]):
                return rva - s["va"] + s["rptr"], s
        return None, None

    regions = []
    cv = None
    if dbg_rva and dbg_size:
        dbg_off, dbg_sec = off(dbg_rva)
        if dbg_off is not None:
            regions.append((dbg_off, dbg_off + dbg_size, "debug_directory"))
            regions.append((dbg_sec["hdr"] + 8, dbg_sec["hdr"] + 12, f"section_vsize({dbg_sec['name']})"))
            for k in range(dbg_size // 28):
                e = dbg_off + 28 * k
                typ, size, _rva, ptr = struct.unpack_from("<IIII", b, e + 12)
                if typ == 2 and b[ptr:ptr + 4] == b"RSDS":
                    path_end = b.index(b"\0", ptr + 24)
                    cv = {"offset": ptr, "size": size, "guid": b[ptr + 4:ptr + 20].hex(),
                          "age": struct.unpack_from("<I", b, ptr + 20)[0],
                          "path": b[ptr + 24:path_end].decode("ascii", "replace")}
                    regions.append((ptr, ptr + 4, "codeview_sig"))
                    regions.append((ptr + 4, ptr + 20, "codeview_guid"))
                    regions.append((ptr + 20, ptr + 24, "codeview_age"))
                    regions.append((ptr + 24, ptr + max(size, 24), "codeview_path"))
    return {"pe": pe, "timestamp": struct.unpack_from("<I", b, pe + 8)[0],
            "checksum": struct.unpack_from("<I", b, opt + 64)[0], "sections": secs, "regions": regions, "codeview": cv}


def classify(pos: int, regions) -> str:
    for lo, hi, name in regions:
        if lo <= pos < hi:
            return name
    return "OTHER"


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    if out_json in args:
        args.remove(out_json)
    if len(args) != 2:
        print(__doc__)
        return 1
    a = open(args[0], "rb").read()
    b = open(args[1], "rb").read()
    res = {"a": args[0], "b": args[1], "a_bytes": len(a), "b_bytes": len(b),
           "a_sha256": hashlib.sha256(a).hexdigest(), "b_sha256": hashlib.sha256(b).hexdigest(),
           "a_md5": hashlib.md5(a).hexdigest(), "b_md5": hashlib.md5(b).hexdigest()}
    la, lb = pe_layout(a), pe_layout(b)
    res["a_codeview"], res["b_codeview"] = la["codeview"], lb["codeview"]
    res["a_timestamp"], res["b_timestamp"] = la["timestamp"], lb["timestamp"]
    res["a_checksum"], res["b_checksum"] = la["checksum"], lb["checksum"]
    if len(a) != len(b):
        res["verdict"] = "LENGTH_DIFFERS"
        print(f"length differs: {len(a)} vs {len(b)}")
        print("VERDICT LENGTH_DIFFERS")
        if out_json:
            json.dump(res, open(out_json, "w", encoding="utf-8", newline="\n"), indent=1)
        return 3
    regions = la["regions"] + lb["regions"]
    ranges = []
    start = prev = None
    cls = None
    for i in range(len(a)):
        if a[i] != b[i]:
            c = classify(i, regions)
            if start is not None and i == prev + 1 and c == cls:
                prev = i
            else:
                if start is not None:
                    ranges.append((start, prev, cls))
                start = prev = i
                cls = c
    if start is not None:
        ranges.append((start, prev, cls))
    res["ranges"] = [{"from": f"0x{lo:X}", "to": f"0x{hi:X}", "bytes": hi - lo + 1, "class": c} for lo, hi, c in ranges]
    other = sum(hi - lo + 1 for lo, hi, c in ranges if c == "OTHER")
    debug = sum(hi - lo + 1 for lo, hi, c in ranges if c != "OTHER")
    res["differing_bytes_debug"], res["differing_bytes_other"] = debug, other
    if not ranges:
        verdict = "SHA_IDENTICAL"
    elif other == 0:
        verdict = "CODE_DATA_IDENTICAL_DEBUG_RECORD_DIFFERS"
    else:
        verdict = "OTHER_BYTES_DIFFER"
    res["verdict"] = verdict
    print(f"A {res['a_sha256']} {args[0]}")
    print(f"B {res['b_sha256']} {args[1]}")
    print(f"A codeview: {la['codeview']}")
    print(f"B codeview: {lb['codeview']}")
    shown = ranges if len(ranges) <= 40 else ranges[:40]
    print("ranges: " + (",".join(f"0x{lo:X}-0x{hi:X}[{c}]" for lo, hi, c in shown) or "none")
          + (f" ... (+{len(ranges) - 40} more)" if len(ranges) > 40 else ""))
    print(f"differing bytes: debug-record {debug}, other {other}")
    print(f"VERDICT {verdict}")
    if out_json:
        json.dump(res, open(out_json, "w", encoding="utf-8", newline="\n"), indent=1)
    return 0 if other == 0 else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, struct.error) as exc:
        print("ERROR:", exc)
        raise SystemExit(1)
