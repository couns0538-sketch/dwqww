"""Opus 2026-11-24: the test of run/admit.py against the known answers K1 to K5
(tmp/opus_scratch/admit/KNOWN_ANSWERS_admission_by_opus.md, written before the code). Standard library only.

    python -I -B -S test_admit.py <admit.py> <a NEW folder> [plantN]

Start it with -I -B -S, as every program of the package: its K2b cases call admit.roster() in this process, and
roster() refuses a process started without them; without them the test stops at once with exit 2 (Opus 25 Nov).

A plant changes one text of the copy under test (PLANTS below; the old text must stand exactly once) and must make
this test fail. Runs on Windows and on Linux; a case this platform cannot make (a file symlink without the right, a
FIFO) prints SKIP with its reason and is counted apart, never as a PASS. Exit 0 = every check passed, 1 = not."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import sysconfig
import types
from pathlib import Path

if not (sys.flags.isolated and sys.flags.dont_write_bytecode and sys.flags.no_site):
    print("STOP: start this test with -I -B -S, as every program of the package (its K2b cases call admit.roster() "
          "in THIS process, and roster() refuses a process started without them)")
    sys.exit(2)
SRC, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
PLANT = sys.argv[3] if len(sys.argv) > 3 else ""
WORK.mkdir()   # must be NEW

PLANTS = {
    "plant1": ("    if got != pin:\n", "    if False:\n"),                                     # pin not compared
    "plant2": ('    if body.pop() != "" or len(body) < 2 or body[-1] != "digest " + hashlib.sha256(',
               '    if body.pop() != "" or len(body) < 2 or body[-1][:7] != "digest " or not hashlib.sha256('),  # digest
    "plant3": ("        if m[2].lower() in folded:", "        if False:"),                        # duplicates
    "plant4": ('any(s in ("", ".", "..") for s in m[2].split("/"))', 'any(s == "" for s in m[2].split("/"))'),  # dots
    "plant5": ("            elif rel != LIST and rel not in listed:\n", "            elif False:\n"),   # unlisted
    "plant6": ('                if e.name == "__pycache__":', '                if False:'),         # cache excepted
    "plant7": ("            if e.is_symlink() or is_link(e.path):", "            if False:"),        # links in walk
    "plant8": ("        if is_link(p) or not stat.S_ISREG(st.st_mode) or not inside(p, root):",
               "        if not os.path.exists(p):"),                                             # listed non-files
    "plant9": ("        if got != sha:\n", "        if False:\n"),                                  # bytes not compared
    "plant10": [("                last[(t[1], t[2], t[0])] = dec", "                last[(t[1], t[2], 'x')] = dec"),
                ("            d = last.get((seat, rel, sha))", "            d = last.get((seat, rel, 'x'))")],  # bytes
    "plant11": [("                last[(t[1], t[2], t[0])] = dec", "                last[(t[1], 'x', t[0])] = dec"),
                ("            d = last.get((seat, rel, sha))", "            d = last.get((seat, 'x', sha))")],  # path
    "plant12": ('            if t[:2] == ["NOT", "YET"]:', '            if False:'),             # NOT YET unread
    "plant13": [("t[1] in SEATS:", "t[1].lower() in SEATS:"),
                ("                last[(t[1], t[2], t[0])] = dec", "                last[(t[1].lower(), t[2], t[0])] = dec")],
    "plant14": ('            elif t[:1] == ["YES"]:', '            elif t[:1] in (["YES"], ["AGREE"]):'),  # AGREE
    "plant15": ("            if len(t) == 3 and", "            if len(t) >= 3 and"),                # a note accepted
    "plant16": ("    if inside(ledger, root):\n", "    if False:\n"),                               # ledger inside
    "plant17": ("        elif any(inside(f, d) for d in site) or not any(inside(f, d) for d in lib):",
                "        elif False:"),                                                          # outside modules
    "plant18": ("    if not (sys.flags.isolated and sys.flags.dont_write_bytecode and sys.flags.no_site):",
                "    if False:"),                                                                # flags
    "plant26": (" and sys.flags.no_site):", "):"),                                               # -S not demanded
    "plant19": ("        elif any(inside(f, d) for d in site) or not", "        elif not"),         # site-packages
    "plant20": ("    if rel not in listed:\n        raise Refused([f\"{rel}: not a listed file",
                "    if False:\n        raise Refused([f\"{rel}: not a listed file"),           # use(): unlisted
    "plant21": (" or file_sha256(p) != listed[rel]:", ":"),                                      # use(): bytes
    "plant22": ("    return listed, walk(root, listed) + files(root, listed) + votes(listed, last)",
                "    return listed, votes(listed, last) + files(root, listed) + walk(root, listed)"),  # order
    "plant23": ("    with open(p, \"rb\") as f:\n        data = f.read()",
                "    with open(p, \"rb\") as f:\n        data = f.read()\n"
                "    open(os.path.join(root, 'admit_seen.txt'), 'a').close()"),                # it writes
    "plant24": ("    if is_link(os.path.normpath(root)) or not os.path.isdir(root):",
                "    if not os.path.isdir(root):"),                                           # root a link
    "plant25": ("            if d != \"YES\":", "            if d is None:"),                     # NOT YET as YES
}

text = SRC.read_text(encoding="utf-8")
if PLANT:
    for old, new in (PLANTS[PLANT] if isinstance(PLANTS[PLANT], list) else [PLANTS[PLANT]]):
        assert text.count(old) == 1, f"{PLANT}: the old text stands {text.count(old)} times"
        text = text.replace(old, new)
MOD = WORK / "mod"
MOD.mkdir()
(MOD / "admit.py").write_bytes(text.encode("utf-8"))
ADMIT_TEXT = text
sys.path.insert(0, str(MOD))
import admit as A  # noqa: E402

PY = sys.executable
SEATS = ("astra", "neon", "fable")
FAILS, SKIPS, NPASS = [], [], [0]


def check(name, ok, detail: object = ""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok or not detail else f"  [{str(detail)[:300]}]"))
    if ok:
        NPASS[0] += 1
    else:
        FAILS.append(name)


def skip(name, why):
    print(f"SKIP {name} ({why})")
    SKIPS.append(name)


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


ENTRY = '''import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import admit
root, pin, ledger, out = sys.argv[1:5]
try:
    listed = admit.require(root, pin, ledger)
    if len(sys.argv) > 6:
        sys.path.insert(0, sys.argv[6])
    import b
    admit.roster(root, listed)
    policy = admit.use(root, listed, sys.argv[5] if len(sys.argv) > 5 else "home/policy.json")
except admit.Refused as e:
    print("REFUSED " + e.reasons[0])
    sys.exit(3)
with open(out, "x") as f:
    f.write("game " + b.WORD + "\\n")
print("PLAYED")
'''


def make_list(root: Path) -> str:
    """The publisher's form (publish_v2.py): sorted, `sha  path`, then `digest <sha of the lines before>`."""
    rows = [f"{sha(f)}  {f.relative_to(root).as_posix()}" for f in sorted(p for p in root.rglob("*")
            if p.is_file() and p.name != "MANIFEST.sha256")]
    data = ("\n".join(rows + ["digest " + hashlib.sha256(("\n".join(rows) + "\n").encode()).hexdigest()]) + "\n")
    (root / "MANIFEST.sha256").write_bytes(data.encode())
    return hashlib.sha256(data.encode()).hexdigest()


def list_bytes(rows) -> bytes:
    return ("\n".join(rows + ["digest " + hashlib.sha256(("\n".join(rows) + "\n").encode()).hexdigest()]) + "\n").encode()


def put_list(root: Path, data: bytes) -> str:
    (root / "MANIFEST.sha256").write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def write_ledger(path: Path, lines) -> None:
    body = ["# APPROVALS: the three-YES ledger (a heading carries no decision)",
            "AGREE 0000 astra FORMATS.md (a document vote is no file YES)"]
    body += [" ".join(x) if isinstance(x, tuple) else x for x in lines]
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def fresh(name, files=None):
    d = WORK / name
    root = d / "pkg"
    (root / "run").mkdir(parents=True)
    (root / "home").mkdir()
    (root / "run" / "a.py").write_bytes(ENTRY.encode())
    (root / "run" / "b.py").write_bytes(b'WORD = "b"\n')
    (root / "run" / "admit.py").write_bytes(ADMIT_TEXT.encode("utf-8"))
    (root / "home" / "policy.json").write_bytes(b'{"owner":"x"}\n')
    for rel, data in (files or {}).items():
        (root / rel).write_bytes(data)
    pin = make_list(root)
    rels = [ln.split("  ", 1)[1] for ln in (root / "MANIFEST.sha256").read_text().splitlines()[:-1]]
    votes = [("YES", sha(root / r), s, r) for r in rels for s in SEATS]
    ledger = d / "ledger.txt"
    write_ledger(ledger, votes)
    return d, root, pin, ledger, votes


def run_check(root, pin, ledger):
    return A.check(str(root), pin, str(ledger))


def cli(root, pin, ledger):
    r = subprocess.run([PY, "-I", "-B", "-S", str(MOD / "admit.py"), "--root", str(root), "--pin", pin, "--ledger",
                        str(ledger)], capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout


def entry(root, pin, ledger, out, *extra, flags=("-I", "-B", "-S")):
    r = subprocess.run([PY, *flags, str(root / "run" / "a.py"), str(root), pin, str(ledger), str(out), *extra],
                       capture_output=True, text=True, timeout=120)
    return r.returncode, (r.stdout + r.stderr).strip()


def inventory(top: Path):
    out = []
    for dp, dns, fns in os.walk(top):
        dns.sort()
        for n in sorted(dns + fns):
            p = Path(dp) / n
            out.append((p.relative_to(top).as_posix(), p.is_dir(), None if p.is_dir() else sha(p)))
    return out


def first(reasons, *words) -> bool:
    return bool(reasons) and all(w in reasons[0] for w in words)


def k1():
    d, root, pin, ledger, votes = fresh("k1")
    listed, reasons = run_check(root, pin, ledger)
    check("K1 nine YES (here twelve: four files) current, bytes unchanged: ADMITTED", reasons == [] and len(listed) == 4,
          reasons)
    rc, out = cli(root, pin, ledger)
    check("K1 the command line: exit 0 and ADMITTED", rc == 0 and out.startswith("ADMITTED"), (rc, out))
    c = "home/policy.json"
    sc = sha(root / c)
    write_ledger(ledger, votes + [("NOT", "YET", sc, "fable", c)])
    listed, reasons = run_check(root, pin, ledger)
    complete = [r for r in listed if not any(x.startswith(r + ":") for x in reasons)]
    check("K1a fable's later NOT YET on C's bytes: REFUSED, first reason names C and fable",
          first(reasons, c, "fable", "NOT YET"), reasons)
    check("K1a the other three files stay complete (3 of 4)", sorted(complete) == ["run/a.py", "run/admit.py", "run/b.py"],
          (complete, reasons))
    rc, out = cli(root, pin, ledger)
    check("K1a the command line: exit 3 and REFUSED naming C", rc == 3 and out.startswith(f"REFUSED: {c}: fable"), (rc, out))
    without_f = [v for v in votes if not (v[2] == "fable" and v[3] == c)]
    write_ledger(ledger, without_f + [("YES", sc, "astra", c)])
    check("K1b a second YES by astra is not the third seat: REFUSED naming fable",
          first(run_check(root, pin, ledger)[1], c, "fable", "no decision"))
    write_ledger(ledger, without_f + [("YES", sc, "fable", c), ("NOT", "YET", sc, "fable", c), ("YES", sc, "fable", c)])
    check("K1c YES, NOT YET, YES on the same bytes: ADMITTED", run_check(root, pin, ledger)[1] == [])
    write_ledger(ledger, without_f + [("YES", sc, "fable", c), ("NOT", "YET", sc, "fable", c)])
    check("K1c NOT YET last: REFUSED", first(run_check(root, pin, ledger)[1], c, "fable", "NOT YET"))
    old = hashlib.sha256(b'{"owner":"y"}\n').hexdigest()
    write_ledger(ledger, without_f + [("YES", old, "fable", c)])
    check("K1d fable's only YES names OTHER bytes: REFUSED", first(run_check(root, pin, ledger)[1], c, "fable", "no decision"))
    write_ledger(ledger, without_f + [("YES", old, "fable", c), ("NOT", "YET", old, "fable", c), ("YES", sc, "fable", c)])
    check("K1d a NOT YET on other bytes takes nothing away from a YES on these: ADMITTED", run_check(root, pin, ledger)[1] == [])
    for label, line in (("another path", f"YES {sc} fable home/policy2.json"),
                        ("an AGREE line", f"AGREE {sc} fable {c}"),
                        ("three fields", f"YES {sc} fable"),
                        ("a capital seat", f"YES {sc} Fable {c}"),
                        ("an unknown seat", f"YES {sc} opus {c}"),
                        ("a note after the path", f"YES {sc} fable {c} (read)")):
        write_ledger(ledger, without_f + [line])
        check(f"K1e {label}: no decision, REFUSED", first(run_check(root, pin, ledger)[1], c, "fable"))
    write_ledger(ledger, without_f + [f"YES {sc} fable {c}"])
    check("K1e control: the exact line ADMITTED", run_check(root, pin, ledger)[1] == [])


def k2():
    d, root, pin, ledger, votes = fresh("k2")
    listed, reasons = run_check(root, pin, ledger)
    check("K2 admitted first", reasons == [], reasons)
    (root / "run" / "b.py").write_bytes(b'WORD = "c"\n')
    check("K2 one byte of the imported helper changed: REFUSED naming it",
          first(run_check(root, pin, ledger)[1], "run/b.py", "sha256"))
    pin2 = make_list(root)
    rels = [ln.split("  ", 1)[1] for ln in (root / "MANIFEST.sha256").read_text().splitlines()[:-1]]
    ledger2 = d / "ledger2.txt"
    write_ledger(ledger2, [("YES", sha(root / r), s, r) for r in rels for s in SEATS])
    check("K2 a matching hash list made inside the changed tree: REFUSED by the outside pin",
          first(run_check(root, pin, ledger2)[1], "MANIFEST.sha256", "not the pinned"))
    check("K2 control: the same tree with its own pin and fresh votes ADMITTED", run_check(root, pin2, ledger2)[1] == [])
    d, root, pin, ledger, votes = fresh("k2p")
    (root / "home" / "policy.json").write_bytes(b'{"owner":"z"}\n')
    check("K2 one byte of the owner's policy changed: REFUSED naming it",
          first(run_check(root, pin, ledger)[1], "home/policy.json", "sha256"))
    d, root, pin, ledger, votes = fresh("k2a")
    listed = A.require(str(root), pin, str(ledger))
    shutil.copyfile(root / "home" / "policy.json", d / "policy.json")
    try:
        A.use(str(root), listed, "../policy.json")
        check("K2a use() of an identical policy beside the package: refused", False, "returned")
    except A.Refused:
        check("K2a use() of an identical policy beside the package: refused", True)
    check("K2a control: use() of the listed policy returns its path",
          os.path.samefile(A.use(str(root), listed, "home/policy.json"), root / "home" / "policy.json"))
    rc, out = entry(root, pin, ledger, d / "game_beside.txt", "../policy.json")
    check("K2a the real entry told to read the copy beside: exit 3, no game",
          rc == 3 and "REFUSED" in out and not (d / "game_beside.txt").exists(), (rc, out))
    shutil.copyfile(root / "home" / "policy.json", root / "home" / "policy_copy.json")
    check("K2a an identical policy at an unlisted path inside: REFUSED",
          first(run_check(root, pin, ledger)[1], "home/policy_copy.json", "does not name"))
    try:
        A.use(str(root), listed, "home/policy_copy.json")
        check("K2a use() of the unlisted copy: refused", False, "returned")
    except A.Refused:
        check("K2a use() of the unlisted copy: refused", True)
    (root / "home" / "policy_copy.json").unlink()
    (root / "home" / "policy.json").write_bytes(b'{"owner":"w"}\n')
    try:
        A.use(str(root), listed, "home/policy.json")
        check("K2a use() after the policy changed since the admission: refused", False, "returned")
    except A.Refused:
        check("K2a use() after the policy changed since the admission: refused", True)
    d, root, pin, ledger, votes = fresh("k2b")
    (root / "run" / "c.py").write_bytes(b"X = 1\n")
    check("K2b an unlisted helper inside the root: REFUSED", first(run_check(root, pin, ledger)[1], "run/c.py", "does not name"))
    d, root, pin, ledger, votes = fresh("k2b_real")
    rc, out = entry(root, pin, ledger, d / "game_ok.txt")
    check("K2b control: the real entry plays (exit 0, its game file)",
          rc == 0 and out == "PLAYED" and (d / "game_ok.txt").read_text() == "game b\n", (rc, out))
    (d / "outside").mkdir()
    (d / "outside" / "b.py").write_bytes(b'WORD = "b"\n')
    rc, out = entry(root, pin, ledger, d / "game_out.txt", "home/policy.json", str(d / "outside"))
    check("K2b the real entry imports the helper from OUTSIDE the root: exit 3 (roster), no game",
          rc == 3 and "module b" in out and not (d / "game_out.txt").exists(), (rc, out))
    listed = A.require(str(root), pin, str(ledger))
    ns = types.SimpleNamespace
    for label, f, ok in (("a listed file of the root", root / "run" / "b.py", True),
                         ("the interpreter's own json", Path(json.__file__), True),
                         ("an unlisted file inside the root", root / "run" / "zz.py", False),
                         ("a copy outside the root", d / "outside" / "b.py", False),
                         ("a file in site-packages", Path(sysconfig.get_paths()["purelib"]) / "fake_mod.py", False)):
        try:
            A.roster(str(root), listed, {"m": ns(__file__=str(f))})
            got = True
        except A.Refused:
            got = False
        check(f"K2b roster(): {label} {'passes' if ok else 'refused'}", got == ok)


def k3():
    d, root, pin, ledger, votes = fresh("k3")
    good = (root / "MANIFEST.sha256").read_text().splitlines()[:-1]
    cases = (("a path twice", good + [good[0]], "twice"),
             ("a path twice in another case", good + [good[0].split("  ")[0] + "  " + good[0].split("  ")[1].upper()],
              "twice"),
             ("an absolute path", good + [good[0].split("  ")[0] + "  /etc/hosts"], "not `<sha256>"),
             ("a .. path", good + [good[0].split("  ")[0] + "  ../x.py"], "not `<sha256>"),
             ("a . path", good + [good[0].split("  ")[0] + "  ./run/b.py"], "not `<sha256>"),
             ("one space", good + [good[0].replace("  ", " ")], "not `<sha256>"),
             ("the list listing itself", good + [good[0].split("  ")[0] + "  MANIFEST.sha256"], "not `<sha256>"))
    for label, rows, word in cases:
        p = put_list(root, list_bytes(rows))
        check(f"K3 {label}: REFUSED", first(run_check(root, p, ledger)[1], "MANIFEST.sha256", word))
    for label, data in (("CR LF line ends", list_bytes(good).replace(b"\n", b"\r\n")),
                        ("a wrong digest line", list_bytes(good)[:-3] + (b"0\n" if list_bytes(good)[-2:-1] != b"0" else b"1\n")),
                        ("no digest line", ("\n".join(good) + "\n").encode()),
                        ("no last line end", list_bytes(good)[:-1]),
                        ("an empty list", list_bytes([])),
                        ("a byte that is not ASCII", list_bytes(good[:-1] + [good[-1] + "é"]))):
        p = put_list(root, data)
        check(f"K3 {label}: REFUSED", first(run_check(root, p, ledger)[1], "MANIFEST.sha256"))
    pin = put_list(root, list_bytes(good))
    check("K3 control: the good list again ADMITTED", run_check(root, pin, ledger)[1] == [])
    check("K3 a pin of upper-case hex: REFUSED", run_check(root, pin.upper(), ledger)[1] == ["the pin is not 64 lowercase hex digits"])
    rc, out = cli(root, "XYZ", ledger)
    check("K3 a pin that is not hex on the command line: exit 2", rc == 2, (rc, out))
    (root / "run" / "__pycache__").mkdir()
    check("K3 an empty __pycache__ folder: REFUSED", first(run_check(root, pin, ledger)[1], "run/__pycache__", "cache"))
    (root / "run" / "__pycache__" / "b.cpython-312.pyc").write_bytes(b"x")
    check("K3 a __pycache__ with a .pyc: REFUSED", first(run_check(root, pin, ledger)[1], "run/__pycache__"))
    shutil.rmtree(root / "run" / "__pycache__")
    (root / "run" / "b.pyc").write_bytes(b"x")
    check("K3 a stray .pyc: REFUSED", first(run_check(root, pin, ledger)[1], "run/b.pyc"))
    (root / "run" / "b.pyc").unlink()
    d, root, pin, ledger, votes = fresh("k3dir", {"run/x.py": b"X = 1\n"})
    (root / "run" / "x.py").unlink()
    (root / "run" / "x.py").mkdir()
    check("K3 a listed path that is a folder: REFUSED", first(run_check(root, pin, ledger)[1], "run/x.py", "not a plain file"))
    # links: a file link to the right bytes, an extra link, a folder link or junction, the root as a link
    d, root, pin, ledger, votes = fresh("k3link")
    real = d / "real_b.py"
    shutil.copyfile(root / "run" / "b.py", real)
    (root / "run" / "b.py").unlink()
    try:
        os.symlink(real, root / "run" / "b.py")
        made = True
    except OSError as e:
        made = False
        skip("K3 a listed file that is a link to the right bytes", f"no file link here: {e.strerror}")
    if made:
        r = run_check(root, pin, ledger)[1]
        check("K3 a listed file that is a link to the right bytes: REFUSED", first(r, "run/b.py", "link"), r)
    d, root, pin, ledger, votes = fresh("k3dirlink")
    (d / "elsewhere").mkdir()
    made = False
    if os.name == "nt":
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(root / "home" / "jn"), str(d / "elsewhere")],
                           capture_output=True, text=True)
        made = r.returncode == 0
        why = r.stdout + r.stderr
    else:
        try:
            os.symlink(d / "elsewhere", root / "home" / "jn", target_is_directory=True)
            made = True
        except OSError as e:
            why = e.strerror
    if made:
        r = run_check(root, pin, ledger)[1]
        check("K3 a folder link or junction inside the root: REFUSED", first(r, "home/jn", "link"), r)
    else:
        skip("K3 a folder link or junction inside the root", why)
    if hasattr(os, "mkfifo"):
        d, root, pin, ledger, votes = fresh("k3fifo")
        try:
            os.mkfifo(root / "run" / "pipe")
            r = run_check(root, pin, ledger)[1]
            check("K3 a FIFO inside the root: REFUSED", first(r, "run/pipe", "neither"), r)
        except OSError as e:
            skip("K3 a FIFO inside the root", f"cannot make one here: {e.strerror}")
    else:
        skip("K3 a FIFO inside the root", "no FIFOs on this platform")
    d, root, pin, ledger, votes = fresh("k3rootlink")
    made = False
    if os.name == "nt":
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(d / "rootlink"), str(root)], capture_output=True, text=True)
        made, why = r.returncode == 0, r.stdout + r.stderr
    else:
        try:
            os.symlink(root, d / "rootlink", target_is_directory=True)
            made = True
        except OSError as e:
            why = e.strerror
    if made:
        r = run_check(d / "rootlink", pin, ledger)[1]
        check("K3 the root given as a link or junction: REFUSED", first(r, "not a plain folder"), r)
    else:
        skip("K3 the root given as a link or junction", why)


def k3a():
    d, root, pin, ledger, votes = fresh("k3a")
    inv0 = inventory(root)
    rc, out = entry(root, pin, ledger, d / "game1.txt")
    check("K3a the entry with -I -B plays", rc == 0 and out == "PLAYED", (rc, out))
    check("K3a ... and no file appeared in the package", inventory(root) == inv0)
    check("K3a ... and the check again ADMITTED", run_check(root, pin, ledger)[1] == [])
    pyc = d / "pyc_prefix"
    rc, out = entry(root, pin, ledger, d / "game2.txt", flags=("-I", "-S", "-X", f"pycache_prefix={pyc}"))
    check("K3a bytecode writes enabled (cache sent outside): exit 3 by the flags, no game",
          rc == 3 and "-I -B -S" in out and not (d / "game2.txt").exists(), (rc, out))
    check("K3a ... the package itself unchanged", inventory(root) == inv0)
    rc, out = entry(root, pin, ledger, d / "game2s.txt", flags=("-I", "-B"))
    check("K3a without -S (site's .pth files may import foreign modules): exit 3, no game, package unchanged",
          rc == 3 and "-I -B -S" in out and not (d / "game2s.txt").exists() and inventory(root) == inv0, (rc, out))
    rc, out = entry(root, pin, ledger, d / "game3.txt", flags=("-I", "-S"))
    caches = [p for p in root.rglob("__pycache__")]
    check("K3a the entry WITHOUT -B: a __pycache__ appears in the package and the entry refuses (exit 3, no game)",
          rc == 3 and bool(caches) and not (d / "game3.txt").exists(), (rc, out, caches))
    r = run_check(root, pin, ledger)[1]
    check("K3a ... and every later check REFUSES it", first(r, "__pycache__"), r)


def k3b():
    d, root, pin, ledger, votes = fresh("k3b")
    (d / "runroot").mkdir()
    (d / "runroot" / "receipt.json").write_bytes(b'{"r":1}\n')
    check("K3b a receipt in the run root beside the package: still ADMITTED", run_check(root, pin, ledger)[1] == [])
    (root / "receipt.json").write_bytes(b'{"r":1}\n')
    check("K3b a receipt written into the package root: REFUSED", first(run_check(root, pin, ledger)[1], "receipt.json"))
    (root / "receipt.json").unlink()
    inner = root / "home" / "ledger.txt"
    shutil.copyfile(ledger, inner)
    check("K3b the ledger inside the package: REFUSED first for that",
          first(run_check(root, pin, inner)[1], "the ledger lies inside"))


def k4_k5():
    d, root, pin, ledger, votes = fresh("k4")
    inv0 = inventory(d)
    listed, reasons = run_check(root, pin, ledger)
    rc, out = cli(root, pin, ledger)
    check("K5 the check and the command line wrote nothing (the case folder's inventory unchanged)",
          reasons == [] and rc == 0 and inventory(d) == inv0, (reasons, rc, out))
    r1, o1 = entry(root, pin, ledger, d / "g1.txt")
    r2, o2 = entry(root, pin, ledger, d / "g2.txt")
    check("K4 a restart with the same tree and ledger plays again", (r1, o1, r2, o2) == (0, "PLAYED", 0, "PLAYED"),
          (r1, o1, r2, o2))
    (root / "home" / "policy.json").write_bytes(b'{"owner":"v"}\n')
    r3, o3 = entry(root, pin, ledger, d / "g3.txt")
    check("K4 a restart with one dependency changed: exit 3 before any action (no game file)",
          r3 == 3 and "home/policy.json" in o3 and not (d / "g3.txt").exists(), (r3, o3))
    d, root, pin, ledger, votes = fresh("order")
    (root / "run" / "c.py").write_bytes(b"X = 1\n")
    write_ledger(ledger, votes[:-1])
    r = run_check(root, pin, ledger)[1]
    check("order: an unlisted file is named before a missing vote", first(r, "run/c.py") and len(r) == 2, r)
    (root / "run" / "c.py").unlink()
    (root / "run" / "b.py").write_bytes(b'WORD = "q"\n')
    r = run_check(root, pin, ledger)[1]
    check("order: changed bytes are named before a missing vote", first(r, "run/b.py", "sha256"), r)


for part in (k1, k2, k3, k3a, k3b, k4_k5):
    try:
        part()
    except Exception as e:   # a part that crashes is a failure of that part, the others still run
        check(f"{part.__name__} ran to its end", False, f"{type(e).__name__}: {e}")
print(f"{NPASS[0]} passed, {len(FAILS)} failed, {len(SKIPS)} skipped (platform: {sys.platform}, Python "
      f"{sys.version.split()[0]})" + (f"; plant {PLANT}" if PLANT else ""))
print("ALL PASS" if not FAILS else f"{len(FAILS)} failed: " + "; ".join(FAILS[:6]))
sys.exit(0 if not FAILS else 1)
