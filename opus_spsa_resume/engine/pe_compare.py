"""pe_compare.py - raw and normalized byte comparison of two PE32+ executables (no execution).

usage: python -I -B pe_compare.py <a.exe> <b.exe> [--json out.json]
Raw: sha256 of each file and whether they are equal. Normalized: both images with these fields zeroed, which the
recipe fills from absolute paths and content hashes rather than from code:
  * COFF header TimeDateStamp (lld --no-insert-timestamp writes a hash of the image), optional header CheckSum;
  * every debug directory entry's TimeDateStamp; CODEVIEW (RSDS) GUID, Age and PDB path bytes (same length kept);
    REPRO entry data;
  * the COFF symbol and string table, if the image has one (reported separately: equal / different / length).
Reports the number of differing bytes after normalization and the sections they fall into. Exit 0 always."""
import hashlib
import json
import struct
import sys
from pathlib import Path


def parse(b):
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    if b[pe:pe + 4] != b"PE\0\0":
        raise SystemExit("not a PE image")
    coff = pe + 4
    nsec, ts, psym, nsym, optsize = struct.unpack_from("<HIIIH", b, coff + 2)
    opt = coff + 20
    magic = struct.unpack_from("<H", b, opt)[0]
    if magic != 0x20B:
        raise SystemExit("not PE32+")
    dd = opt + 112
    dbg_rva, dbg_size = struct.unpack_from("<II", b, dd + 6 * 8)
    secs = []
    st = opt + optsize
    for i in range(nsec):
        name, vsize, va, rsize, rptr = struct.unpack_from("<8sIIII", b, st + 40 * i)
        secs.append({"name": name.rstrip(b"\0").decode("ascii", "replace"), "va": va, "vsize": vsize, "ptr": rptr,
                     "size": rsize})

    def rva2off(rva):
        for s in secs:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["size"]):
                return s["ptr"] + rva - s["va"]
        return None

    return {"coff": coff, "ts_off": coff + 4, "checksum_off": opt + 64, "psym": psym, "nsym": nsym,
            "dbg_off": rva2off(dbg_rva) if dbg_rva else None, "dbg_size": dbg_size, "secs": secs}


def normalize(b):
    b = bytearray(b)
    p = parse(b)
    masks = []

    def zero(off, n, why):
        b[off:off + n] = b"\0" * n
        masks.append({"off": off, "len": n, "what": why})

    zero(p["ts_off"], 4, "COFF TimeDateStamp")
    zero(p["checksum_off"], 4, "optional header CheckSum")
    if p["dbg_off"] is not None:
        for i in range(p["dbg_size"] // 28):
            e = p["dbg_off"] + 28 * i
            _, _, _, _, typ, size, _, ptr = struct.unpack_from("<IIHHIIII", b, e)
            zero(e + 4, 4, f"debug entry {i} TimeDateStamp")
            if typ == 2 and b[ptr:ptr + 4] == b"RSDS":
                zero(ptr + 4, 20, "RSDS GUID+Age")
                zero(ptr + 24, size - 24, "RSDS PDB path")
            elif typ == 16 and size:
                zero(ptr, size, "REPRO hash")
    sym = None
    if p["psym"]:
        sym = bytes(b[p["psym"]:])
        zero(p["psym"], len(b) - p["psym"], "COFF symbol+string table")
    return bytes(b), p, masks, sym


def section_of(p, off):
    for s in p["secs"]:
        if s["ptr"] <= off < s["ptr"] + s["size"]:
            return s["name"]
    return "headers/other"


def main(argv):
    a, bpath = Path(argv[1]), Path(argv[2])
    A, B = a.read_bytes(), bpath.read_bytes()
    out = {"a": str(a), "b": str(bpath), "a_sha256": hashlib.sha256(A).hexdigest(),
           "b_sha256": hashlib.sha256(B).hexdigest(), "raw_equal": A == B, "sizes": [len(A), len(B)]}
    na, pa, ma, sa = normalize(A)
    nb, pb, mb, sb = normalize(B)
    out["masked_fields"] = sorted({m["what"] for m in ma + mb})
    out["layout_equal"] = [(s["name"], s["ptr"], s["size"]) for s in pa["secs"]] == \
                          [(s["name"], s["ptr"], s["size"]) for s in pb["secs"]]
    if len(na) != len(nb):
        out["normalized_equal"] = False
        out["note"] = "different file sizes after normalization"
    else:
        diff = [i for i in range(len(na)) if na[i] != nb[i]]
        out["normalized_equal"] = not diff
        out["normalized_diff_bytes"] = len(diff)
        by = {}
        for i in diff:
            k = section_of(pa, i)
            by[k] = by.get(k, 0) + 1
        out["normalized_diff_by_section"] = by
    out["symbol_table"] = None if sa is None and sb is None else {
        "a_len": None if sa is None else len(sa), "b_len": None if sb is None else len(sb), "equal": sa == sb}
    out["sections_sha256"] = {}
    for s in pa["secs"]:
        sb_ = next((x for x in pb["secs"] if x["name"] == s["name"]), None)
        ha = hashlib.sha256(na[s["ptr"]:s["ptr"] + s["size"]]).hexdigest()
        hb = hashlib.sha256(nb[sb_["ptr"]:sb_["ptr"] + sb_["size"]]).hexdigest() if sb_ else None
        out["sections_sha256"][s["name"]] = {"equal": ha == hb, "a": ha[:16], "b": (hb or "")[:16]}
    text = json.dumps(out, indent=1)
    if "--json" in argv:
        Path(argv[argv.index("--json") + 1]).write_text(text + "\n", encoding="ascii")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
