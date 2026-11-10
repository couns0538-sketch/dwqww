"""mg_format.py - codec of the mgprobe transcript, version 2 (standard library only).

A transcript is a sequence of frames: u32 magic "MGP1", u32 payload length, payload. Little-endian.
Payload head: u32 playout, u16 ply, u8 kind, u8 flags.
  kind 253  identity, always the first frame: which probe wrote the transcript (version, tag, sha256 of the
            harness source, sha256 of the source-tree manifest, extra defines); flags = 1 when the null-move
            block is written
  kind 0    one visited position (layout below, the same order as mgprobe.cpp writes it)
  kind 1    the probe could not play the path move (str uci): its legal list lacks it
  kind 2    the probe rejected the seed FEN (str error, str fen)
  kind 254  trailer: u64 records, u64 hard self-check failures, u64 incremental/refresh differences

  python -I -B mg_format.py TRANSCRIPT [first [count]]     prints decoded records (the "dump" of the probe)
"""
import struct
import sys

MAGIC = 0x3150474D
ALL_ONES = 0xFFFFFFFFFFFFFFFF
VALUE_NONE = 32002
PROMO = {2: "n", 3: "b", 4: "r", 5: "q"}


class Malformed(Exception):
    pass


def frames_tolerant(data):
    """([(payload offset, payload length)], error text or None): the well-formed frames up to the first bad or
    cut one. A frame needs at least the 8-byte record head."""
    spans = []
    pos, n = 0, len(data)
    while pos < n:
        if n - pos < 8:
            return spans, f"truncated frame header at byte {pos} (record {len(spans)})"
        magic, length = struct.unpack_from("<II", data, pos)
        if magic != MAGIC:
            return spans, f"bad frame magic at byte {pos} (record {len(spans)})"
        if length < 8:
            return spans, f"frame shorter than a record head at byte {pos} (record {len(spans)})"
        if pos + 8 + length > n:
            return spans, f"truncated record at byte {pos} (record {len(spans)}): needs {length} bytes, {n - pos - 8} left"
        spans.append((pos + 8, length))
        pos += 8 + length
    return spans, None


def frames(data):
    """[(payload offset, payload length)] of every frame; Malformed names the byte offset of a bad or cut frame."""
    spans, error = frames_tolerant(data)
    if error:
        raise Malformed(error)
    return spans


def frame(payload):
    return struct.pack("<II", MAGIC, len(payload)) + payload


def kind_of(data, span):
    return data[span[0] + 6]


class _Reader:
    def __init__(self, b):
        self.b, self.p = b, 0

    def take(self, fmt):
        try:
            v = struct.unpack_from(fmt, self.b, self.p)
        except struct.error as e:
            raise Malformed(f"record is shorter than its layout ({e})") from None
        self.p += struct.calcsize(fmt)
        return v

    def moves(self):
        (n,) = self.take("<H")
        return list(self.take(f"<{n}I"))

    def u64s(self, n):
        return list(self.take(f"<{n}Q"))

    def raw(self, n):
        if self.p + n > len(self.b):
            raise Malformed("record is shorter than its layout")
        v = bytearray(self.b[self.p:self.p + n])
        self.p += n
        return v

    def text(self):
        (n,) = self.take("<H")
        return bytes(self.raw(n)).decode("latin-1")


def decode(payload):
    r = _Reader(payload)
    playout, ply, kind, flags = r.take("<IHBB")
    d = {"playout": playout, "ply": ply, "kind": kind, "flags": flags}
    if kind == 254:
        d["records"], d["hard"], d["soft"] = r.take("<QQQ")
    elif kind == 253:
        d["version"] = r.text()
        d["tag"] = r.text()
        d["harness"] = r.text()
        d["tree"] = r.text()
        d["defs"] = r.text()
    elif kind == 1:
        d["uci"] = r.text()
    elif kind == 2:
        d["error"] = r.text()
        d["fen"] = r.text()
    elif kind == 0:
        d["key"], d["pawn_key"] = r.take("<QQ")
        d["side"], d["castling"], ep1, _reserved, d["halfmove"], d["fullmove"] = r.take("<BBBBHH")
        d["ep"] = ep1 - 1
        d["checkers_main"], d["checkers_twin"], d["checkers_fresh"], d["checkers_direct"] = r.take("<QQQQ")
        d["has_before"], d["has_after"] = r.take("<BB")
        d["all"] = r.moves()
        d["caps"] = r.moves()
        d["quiets"] = r.moves()
        n = len(d["all"])
        d["bits"] = r.raw(n)
        d["one_bits"] = r.raw(n)
        d["post_bits"] = r.raw(n)
        d["legal"] = r.moves()
        d["legal_caps"] = r.moves()
        d["child_one"] = r.u64s(n)
        d["child_main"] = r.u64s(n)
        (d["hce"], d["off"], d["on_refresh"], d["on_inc"], d["net"], d["rev1_off"], d["rev8_off"],
         d["rev8_on"]) = r.take("<8i")
        if flags & 1:
            (has,) = r.take("<B")
            nall = r.moves()
            m = len(nall)
            d["null"] = {"has": has, "all": nall, "bits": r.raw(m), "child": r.u64s(m)}
        else:
            d["null"] = None
    else:
        raise Malformed(f"unknown record kind {kind}")
    if r.p != len(payload):
        raise Malformed(f"record of kind {kind} has {len(payload) - r.p} bytes more than its layout")
    return d


def _moves(lst):
    return struct.pack(f"<H{len(lst)}I", len(lst), *lst)


def _text(s):
    b = s.encode("latin-1")
    return struct.pack("<H", len(b)) + b


def encode(d):
    """Inverse of decode (payload only). Used by the self-test to build corrupted fixtures."""
    kind = d["kind"]
    head = struct.pack("<IHBB", d["playout"], d["ply"], kind, d["flags"])
    if kind == 254:
        return head + struct.pack("<QQQ", d["records"], d["hard"], d["soft"])
    if kind == 253:
        return head + _text(d["version"]) + _text(d["tag"]) + _text(d["harness"]) + _text(d["tree"]) + _text(d["defs"])
    if kind == 1:
        return head + _text(d["uci"])
    if kind == 2:
        return head + _text(d["error"]) + _text(d["fen"])
    n = len(d["all"])
    out = [head, struct.pack("<QQ", d["key"], d["pawn_key"]),
           struct.pack("<BBBBHH", d["side"], d["castling"], d["ep"] + 1, 0, d["halfmove"], d["fullmove"]),
           struct.pack("<QQQQ", d["checkers_main"], d["checkers_twin"], d["checkers_fresh"], d["checkers_direct"]),
           struct.pack("<BB", d["has_before"], d["has_after"]),
           _moves(d["all"]), _moves(d["caps"]), _moves(d["quiets"]), bytes(d["bits"]), bytes(d["one_bits"]), bytes(d["post_bits"]),
           _moves(d["legal"]), _moves(d["legal_caps"]),
           struct.pack(f"<{n}Q", *d["child_one"]), struct.pack(f"<{n}Q", *d["child_main"]),
           struct.pack("<8i", d["hce"], d["off"], d["on_refresh"], d["on_inc"], d["net"], d["rev1_off"],
                       d["rev8_off"], d["rev8_on"])]
    if d["flags"] & 1:
        nl = d["null"]
        m = len(nl["all"])
        out += [struct.pack("<B", nl["has"]), _moves(nl["all"]), bytes(nl["bits"]), struct.pack(f"<{m}Q", *nl["child"])]
    return b"".join(out)


def legal_lists(data):
    """The legal-move list (UCI text) of every position record, without decoding the rest of the record."""
    out = []
    for o, n in frames(data):
        if data[o + 6] != 0:
            continue
        p = o + 8 + 16 + 8 + 32 + 2                     # head, keys, state, four checkers, two has_legal_move bytes
        (n_all,) = struct.unpack_from("<H", data, p)
        p += 2 + 4 * n_all
        (n_caps,) = struct.unpack_from("<H", data, p)
        p += 2 + 4 * n_caps
        (n_quiets,) = struct.unpack_from("<H", data, p)
        p += 2 + 4 * n_quiets + 3 * n_all
        (n_legal,) = struct.unpack_from("<H", data, p)
        out.append([uci(m) for m in struct.unpack_from(f"<{n_legal}I", data, p + 2)])
    return out


# ---------------------------------------------------------------- readable forms
def square(i):
    return "abcdefgh"[i & 7] + str((i >> 3) + 1)


def uci(move):
    """UCI text of a move word (from | to << 8 | promotion << 16 | flags << 24)."""
    return square(move & 0xFF) + square((move >> 8) & 0xFF) + PROMO.get((move >> 16) & 0xFF, "")


def ucis(lst):
    return [uci(m) for m in lst]


def squares(bb):
    return [square(i) for i in range(64) if (bb >> i) & 1]


def bb_text(bb):
    return f"0x{bb:016x} [{' '.join(squares(bb)) or '-'}]"


def parse_path(path_text):
    """{playout: (seed fen, [moves])} of a path chunk."""
    playouts, current = {}, None
    for line in path_text.splitlines():
        if line.startswith("P "):
            parts = line.split(" ", 4)
            current = int(parts[1])
            playouts[current] = (parts[4].strip(), [])
        elif line.startswith("M") and current is not None:
            playouts[current][1].extend(line[1:].split())
    return playouts


def replay_command(path_text, playout, ply):
    """The UCI position command that reaches the record (seed FEN and the moves played up to its ply)."""
    if not path_text:
        return "(no path file given)"
    entry = parse_path(path_text).get(playout)
    if entry is None:
        return f"(playout {playout} is not in the path file)"
    fen, moves = entry
    return f"position fen {fen}" + (" moves " + " ".join(moves[:ply]) if ply else "")


def describe(d):
    k = d["kind"]
    if k == 254:
        return f"TRAILER records {d['records']} self-check failures {d['hard']} incremental/refresh differences {d['soft']}"
    if k == 253:
        return (f"IDENTITY {d['version']} tag {d['tag']} harness {d['harness']} tree manifest {d['tree']} defines [{d['defs']}] "
                f"null-move block {'on' if d['flags'] & 1 else 'off'}")
    if k == 1:
        return f"playout {d['playout']} ply {d['ply']}: MISSING MOVE {d['uci']}"
    if k == 2:
        return f"playout {d['playout']}: REJECTED FEN [{d['fen']}] error [{d['error']}]"
    lines = [f"playout {d['playout']} ply {d['ply']} key {d['key']:016x} pawnkey {d['pawn_key']:016x} "
             f"side {'wb'[d['side']]} castling {d['castling']} ep {square(d['ep']) if d['ep'] >= 0 else '-'} "
             f"halfmove {d['halfmove']} fullmove {d['fullmove']}",
             f"  checkers main {bb_text(d['checkers_main'])} twin {d['checkers_twin']:016x} fresh {d['checkers_fresh']:016x} direct {d['checkers_direct']:016x}",
             f"  has_legal_move before {d['has_before']} after {d['has_after']}",
             f"  legal {len(d['legal'])}: {' '.join(ucis(d['legal']))}",
             f"  legal captures {len(d['legal_caps'])}: {' '.join(ucis(d['legal_caps']))}",
             f"  generated all {len(d['all'])}: " + " ".join(
                 f"{uci(m)}{'' if b & 1 else '(illegal)'}{'+' if b & 2 else ''}" for m, b in zip(d["all"], d["bits"])),
             "  first-query answers (legal, check): " + " ".join(f"{uci(m)}={b & 1}{(b >> 1) & 1}" for m, b in zip(d["all"], d["one_bits"])),
             "  answers after make and unmake differ from the first ones: " + str(bytes(d["post_bits"]) != bytes(d["bits"])),
             f"  generated captures {len(d['caps'])}: {' '.join(ucis(d['caps']))}",
             f"  generated quiets {len(d['quiets'])}: {' '.join(ucis(d['quiets']))}",
             "  checkers after make: " + " ".join(
                 f"{uci(m)}={c:x}" for m, c, b in zip(d["all"], d["child_main"], d["bits"]) if b & 1 and c),
             f"  eval hand-crafted {d['hce']} net off {d['off']} net on {d['on_refresh']} (incremental {d['on_inc']}) raw net {d['net']} "
             f"back1 off {d['rev1_off']} back8 off {d['rev8_off']} back8 on {d['rev8_on']}"]
    if d["null"] is not None:
        nl = d["null"]
        lines.append(f"  null child: has_legal_move {nl['has']}, generated {len(nl['all'])}, legal {sum(1 for b in nl['bits'] if b & 1)}")
    return "\n".join(lines)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    data = open(argv[1], "rb").read()
    first = int(argv[2]) if len(argv) > 2 else 0
    count = int(argv[3]) if len(argv) > 3 else 5
    spans = frames(data)
    print(f"{len(spans)} frames, {len(data)} bytes")
    for o, n in spans[first:first + count]:
        print(describe(decode(data[o:o + n])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
