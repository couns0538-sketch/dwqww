"""Opus 2026-11-24, the package admission (the seats' spec package_admission.md, sha256 09a89a6c...; SETUP_PLAN 2.7
D6 and failure rows 1, 2 and 42; known answers tmp/opus_scratch/admit/KNOWN_ANSWERS_admission_by_opus.md, written
before this code). Before a program of the package does anything, it proves that the files about to run are the
PINNED package and that each has a current YES of all three seats on its exact bytes. Standard library only, the
same file on the PC and on Linux. It only reads: it writes no file, makes no cache and follows no link.

    admit.py --root DIR --pin SHA256 --ledger FILE    exit 0 ADMITTED; 3 REFUSED (the first discrepancy first);
                                                       2 a bad call
From a program of the package, FIRST, before any work (every program runs with -I -B -S: D6 says -I -B; the -S is
my proposal for the seats, because without it site's .pth files import foreign modules before the program starts):
    listed = admit.require(root, pin, ledger)            # raises admit.Refused
    import ...                                           # the program's own modules
    admit.roster(root, listed)                           # each imported module: a listed file or the interpreter's own
    path = admit.use(root, listed, "home/policy.json")   # a data file is read only while listed and unchanged

The hash list <root>/MANIFEST.sha256 is the publisher's form, the one the boot guard reads: `<sha256>  <path>` lines,
the last line `digest <sha256 of the lines before it>`, LF only. Its own sha256 is the pin, given from OUTSIDE (D6):
the value the boot guard compares with the run header's `package`. The ledger lies outside the root. A vote line is
`YES <sha256> <seat> scripts_v2/<path>` or `NOT YET <sha256> <seat> scripts_v2/<path>` (seats astra, neon, fable;
the prefix as every vote line on the branch writes it; a line without it carries no decision, Fable's read of 25 Nov); any other line (a
heading, AGREE, a publisher's note, a line with more or fewer fields) carries no decision. A seat's decision on a
file is its LAST line for that path and those exact bytes (the spec: "the latest decision ... on its exact bytes"):
a vote on other bytes neither gives nor takes away.
"""
import argparse
import hashlib
import os
import re
import stat
import sys
import sysconfig

SEATS = ("astra", "neon", "fable")
LIST = "MANIFEST.sha256"
HEX = re.compile(r"[0-9a-f]{64}")
PREFIX = "scripts_v2/"                               # a vote line's path as on the branch: scripts_v2/<hash-list path>
LINE = re.compile(r"([0-9a-f]{64})  ([A-Za-z0-9_./-]+)")   # the boot guard's line (bootguard.py, package())


class Refused(Exception):
    def __init__(self, reasons):
        super().__init__(reasons[0])
        self.reasons = list(reasons)


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def is_link(path) -> bool:
    # off Windows there are no junctions; os.path.isjunction exists from Python 3.12 on
    return os.path.islink(path) or getattr(os.path, "isjunction", lambda _p: False)(path)


def inside(path, root) -> bool:
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r.rstrip(os.sep) + os.sep)


def read_list(root, pin) -> dict:
    """{path: sha256} of the hash list; Refused. The pin comes first: nothing in the root is believed before it."""
    p = os.path.join(root, LIST)
    if is_link(p) or not os.path.isfile(p):
        raise Refused([f"{LIST}: missing, a link or not a plain file"])
    with open(p, "rb") as f:
        data = f.read()
    got = hashlib.sha256(data).hexdigest()
    if got != pin:
        raise Refused([f"{LIST}: not the pinned hash list (its sha256 {got[:12]}, the pin {pin[:12]})"])
    try:
        body = data.decode("ascii").split("\n")
    except UnicodeDecodeError:
        raise Refused([f"{LIST}: a byte that is not ASCII"]) from None
    if body.pop() != "" or len(body) < 2 or body[-1] != "digest " + hashlib.sha256(
            ("\n".join(body[:-1]) + "\n").encode("ascii")).hexdigest():
        raise Refused([f"{LIST}: no last line end, no file, or a last line that is not `digest <sha256 of the "
                       f"lines before it>`"])
    listed, folded = {}, set()
    for ln in body[:-1]:
        m = LINE.fullmatch(ln)
        if not m or any(s in ("", ".", "..") for s in m[2].split("/")) or m[2] == LIST:
            raise Refused([f"{LIST}: a line that is not `<sha256>  <plain relative path>`: {ln[:80]!r}"])
        if m[2].lower() in folded:   # a path twice, also in another case (one file on Windows)
            raise Refused([f"{LIST}: {m[2]} is listed twice"])
        folded.add(m[2].lower())
        listed[m[2]] = m[1]
    return listed


def walk(root, listed) -> list:
    """A link or junction, a bytecode cache, an object that is neither a plain folder nor a plain file, or a file
    the list does not name: each is a reason. Nothing is followed; the order is fixed (sorted names)."""
    reasons, todo = [], [""]
    while todo:
        rel_dir = todo.pop(0)
        try:
            with os.scandir(os.path.join(root, *rel_dir.split("/")) if rel_dir else root) as it:
                entries = sorted(it, key=lambda e: e.name)
        except OSError as e:
            reasons.append(f"{rel_dir or '.'}: cannot be listed ({e.strerror})")
            continue
        for e in entries:
            rel = f"{rel_dir}/{e.name}" if rel_dir else e.name
            if e.is_symlink() or is_link(e.path):
                reasons.append(f"{rel}: a link or junction (never followed)")
            elif e.is_dir(follow_symlinks=False):
                if e.name == "__pycache__":
                    reasons.append(f"{rel}: a bytecode cache (every program of the package runs with -I -B)")
                else:
                    todo.append(rel)
            elif not e.is_file(follow_symlinks=False):
                reasons.append(f"{rel}: neither a plain file nor a plain folder")
            elif rel != LIST and rel not in listed:
                reasons.append(f"{rel}: a file the hash list does not name")
    return reasons


def files(root, listed) -> list:
    reasons = []
    for rel, sha in sorted(listed.items()):
        p = os.path.join(root, *rel.split("/"))
        try:
            st = os.lstat(p)
        except OSError:
            reasons.append(f"{rel}: missing")
            continue
        if is_link(p) or not stat.S_ISREG(st.st_mode) or not inside(p, root):
            reasons.append(f"{rel}: not a plain file of the package (a link, a folder or another object)")
            continue
        got = file_sha256(p)
        if got != sha:
            reasons.append(f"{rel}: sha256 {got[:12]}, not the listed {sha[:12]}")
    return reasons


def decisions(ledger) -> dict:
    """{(seat, path, sha256): the seat's LAST decision on those bytes at that path} from the vote lines."""
    last = {}
    with open(ledger, encoding="utf-8") as f:
        for line in f:
            t = line.split()
            if t[:2] == ["NOT", "YET"]:
                dec, t = "NOT YET", t[2:]
            elif t[:1] == ["YES"]:
                dec, t = "YES", t[1:]
            else:
                continue
            if len(t) < 3 or not t[2].startswith(PREFIX):    # no scripts_v2/: no decision (Fable 25 Nov)
                continue
            t[2] = t[2][len(PREFIX):]                         # three fields exactly: the next line alone decides
            if len(t) == 3 and HEX.fullmatch(t[0]) and t[1] in SEATS:
                last[(t[1], t[2], t[0])] = dec
    return last


def votes(listed, last) -> list:
    reasons = []
    for rel, sha in sorted(listed.items()):
        for seat in SEATS:
            d = last.get((seat, rel, sha))
            if d != "YES":
                reasons.append(f"{rel}: {seat} has {'no decision' if d is None else d} on these bytes ({sha[:12]})")
    return reasons


def check(root, pin, ledger):
    """(listed, reasons); no reason = ADMITTED. The first reason is the first discrepancy in a fixed order: the root,
    the pin and the hash list, the ledger's place, the tree, the listed files, the votes."""
    if is_link(os.path.normpath(root)) or not os.path.isdir(root):
        return {}, [f"{root}: not a plain folder"]
    if not HEX.fullmatch(pin or ""):
        return {}, ["the pin is not 64 lowercase hex digits"]
    try:
        listed = read_list(root, pin)
    except Refused as e:
        return {}, e.reasons
    except OSError as e:
        return {}, [f"{LIST}: cannot be read ({e.strerror})"]
    if inside(ledger, root):
        return listed, ["the ledger lies inside the package: it must come from outside (D6)"]
    try:
        last = decisions(ledger)
    except (OSError, UnicodeDecodeError) as e:
        return listed, [f"the ledger cannot be read ({e})"]
    return listed, walk(root, listed) + files(root, listed) + votes(listed, last)


def require(root, pin, ledger) -> dict:
    listed, reasons = check(root, pin, ledger)
    if reasons:
        raise Refused(reasons)
    return listed


def roster(root, listed, modules=None) -> None:
    """The program runs with -I -B, and every imported module that has a file is a listed file of the root or a file
    of the interpreter's own library (not site-packages, not a copy anywhere else); Refused names each other one."""
    reasons = []
    if not (sys.flags.isolated and sys.flags.dont_write_bytecode and sys.flags.no_site):
        reasons.append("the program was not started with -I -B -S (D6: a cache written into the package changes it; "
                       "without -S the interpreter's .pth files run foreign code first: Ubuntu 24.04's python3 loads "
                       "_distutils_hack, apport_python_hook and zope that way)")
    paths = sysconfig.get_paths()
    lib = [d for d in {paths.get("stdlib"), paths.get("platstdlib"), os.path.join(sys.base_prefix, "DLLs")} if d]
    site = [d for d in {paths.get("purelib"), paths.get("platlib")} if d]
    for name, m in sorted((sys.modules if modules is None else modules).items()):
        f = getattr(m, "__file__", None)
        if not f:
            continue
        if inside(f, root):
            rel = os.path.relpath(os.path.realpath(f), os.path.realpath(root)).replace(os.sep, "/")
            if rel not in listed:
                reasons.append(f"module {name}: {rel} is not a listed file of the package")
        elif any(inside(f, d) for d in site) or not any(inside(f, d) for d in lib):
            reasons.append(f"module {name}: {f} is neither a file of the package nor of the interpreter's own library")
    if reasons:
        raise Refused(reasons)


def use(root, listed, rel) -> str:
    """The path of a listed data file, after its bytes were compared again; Refused for anything else (an unlisted
    path, a copy beside the package, a link, changed bytes)."""
    if rel not in listed:
        raise Refused([f"{rel}: not a listed file of the package (only admitted files are read)"])
    p = os.path.join(root, *rel.split("/"))
    if is_link(p) or not os.path.isfile(p) or not inside(p, root) or file_sha256(p) != listed[rel]:
        raise Refused([f"{rel}: not the admitted bytes"])
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="admit the frozen package (exit 0 ADMITTED, 3 REFUSED, 2 bad call)")
    ap.add_argument("--root", required=True)
    ap.add_argument("--pin", required=True)
    ap.add_argument("--ledger", required=True)
    a = ap.parse_args(argv)   # a bad call: argparse's own exit 2
    if not HEX.fullmatch(a.pin):
        print("bad call: --pin must be 64 lowercase hex digits (the sha256 of the hash list, from outside)")
        return 2
    listed, reasons = check(a.root, a.pin, a.ledger)
    if reasons:
        print("REFUSED: " + reasons[0])
        for r in reasons[1:]:
            print("  also: " + r)
        return 3
    print(f"ADMITTED: {len(listed)} files, hash list {a.pin[:12]}, three YES on the exact bytes of every file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
