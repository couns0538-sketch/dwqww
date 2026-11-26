"""Opus 2026-11-25 (Fable's finding A of FABLE-2511-READ-PKG10-FETCH: no program of the package put anything on the
server; specs/home_control_delivery.md; FORMATS 1.2 [2.8] [2.9]): the home DELIVERY of the owner's decisions. Known
answers written before this code: tmp/opus_scratch/deliver/KNOWN_ANSWERS_deliver_by_opus.md on the PC, read by Fable
(FABLE-2511-DELIVER-KA: DV1, DV3 to DV5 YES; the sequence and observe changed by her H1, the dot-name's compare by
H3, the probe by H4). Standard library only; nothing is installed. Home starts every connection; the server never
connects back.

    deliver.py probe   --home DIR --fingerprint HEX64 --config FILE
    deliver.py send    --home DIR --fingerprint HEX64 --config FILE --made NEWDIR
    deliver.py observe --home DIR --fingerprint HEX64

THE CONNECTION is home/fetch.py's Transport (the pinned sftp.exe options, R1 and R2, judge(): an unknown or changed
host key or a refused login is exit 6, an unreachable server 7), imported, not copied; FILE is fetch.py's config
(transport sftp); <remote_root>/inbox/ is the guard's (G3). DIR is fetch.py's home folder: wire/RUN.json.zz must
decode to bytes whose sha256 is HEX64 (else exit 4, and nothing is made there: Fable's D2 of 25 Nov).
DIR/deliver/: LOCK (one delivery or observe at a time, else exit 8), journal.jsonl (one canonical line a step), sent/
(THE SENT CHAIN: create-only copies of every decision sent, EVIDENCE.<e>.json, CONTROL.<k>.json and both .zz, written
BEFORE its first byte travels; it is what tools/make_control.py gets as --accepted), back/ (bytes read back, removed
after each compare). DIR/control/ is THE SEEN CHAIN: observe alone writes it.
PROBE (H4), once after the admission: two names are put into the inbox, `rename -l` of one onto the other must fail,
and (v16, P3a: the positive control) `rename -l` of it onto a FREE third name must succeed, the listing showing
the second and the third name and not the first; all three are removed and the inbox is listed without them; a
journal line with refused, kept, moved and gone. Exit 0: the rename is create-only and it works; 3: it replaced
the other name, did not move onto a free one, or a name stayed (the text names the step). Send holds while the
journal has no passed probe of this run.
SEND takes ONE decision that make_control.py wrote into NEWDIR and refuses (exit 4, nothing written) anything else:
not exactly EVIDENCE.<e>.json, CONTROL.<k>.json and their .zz; a .zz that is not one whole zlib stream (at most 16
MiB) of its .json; an evidence whose name is not its sha256 (make_control writes without a flush: a short file) or
that holds local_only; a control that is not canonical with the guard's keys, schema 2, this run, k as its name,
evidence = e, a kind of the four, owner_policy = the evidence's inputs.plan_sha256 (G3 c).
It HOLDS (exit 3, nothing sent, the reason named): k not one more than the sent chain, or prev not its last
control's sha256; another control under the same k in sent/; the newest sent control's effect VISIBLE (a schedule or
the fence) and not seen yet, for any kind but fence (an effect none, kind matches or outcome UNQUALIFIED, is never
visible at home: the next one is built on it and the guard's chain rule decides; H1); a bound later than the one in
force (the newest SCHEDULE.<n>.json.zz in DIR/wire/, else the header's hard cutoff) or a dispatch end after its
cutoff; the SERVER's clock at or past the cutoff in force, or no usable clock line, for any kind but fence (a stop
is never held at home); no passed probe. The same bytes again are a retry: they pass (bounds are not checked
again). v16 (K3): the server's clock is home/clock.py's server_now, measured from the guard's CLOCK.json (the PC's
clock runs about 7 hours ahead and held every control from 7 hours before the cutoff). It runs late by up to about
75 s, never early: a control may leave up to about 75 s after the real cutoff, which is harmless, since the
server's guard takes no control after the cutoff by its own clocks (guard.py, one_pass).
THE TRANSFER: the inbox is listed FIRST (no "-": a missing inbox is exit 7; a host key or login failure ends here with
6, before any put). Then every sent control above the seen chain up to k, in order, its evidence first and the
control LAST: a final name in the inbox already is read back and compared (equal: nothing put; other bytes: exit 3
CONFLICT, nothing replaced); else ONE batch puts it under .<name>.part (a name the guard never reads) and gets that
back, the bytes are compared (other bytes: exit 7, no rename; H3), and only then `rename -l` makes the final name
(the legacy rename: OpenSSH's sftp-server links then unlinks, so it never replaces a name; the probe proves it on the
day's server). A last listing must show every final name at its length. Send never claims acceptance.
OBSERVE: a schedule in DIR/wire/ whose evidence is sent control j's sha256, or this run's fence whose why names it,
shows that j and every sent control below it were accepted (the guard reads k only after k - 1): DIR/control/ gets
each one's EVIDENCE.<e>.json and then CONTROL.<i>.json, create-only, in order. Neither: "not seen yet", exit 0.
Exit: 0 done; 2 a wrong call; 3 HELD or CONFLICT; 4 refused input, or a home file that is not what it must be; 6 the
host key or the login (STOP); 7 the server cannot be reached, a failed transfer, or a dot-name read back with other
bytes; 8 another delivery holds DIR/deliver/LOCK. The last line names what was done.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
sys.path.insert(0, str(HERE))
import fetch as F  # noqa: E402   the connection; it puts run/ on the path for worker
import clock as CK  # noqa: E402   v16 K3: the server's time, measured (home/clock.py)
import make_control as MC  # noqa: E402   the chain check, the names and the keys, as the control maker reads them
from worker import SlotLock, Stop, canon, create_only, parse_canon, sha256_bytes  # noqa: E402

HEX64 = re.compile(r"[0-9a-f]{64}")
EV_NAME = re.compile(r"EVIDENCE\.([0-9a-f]{64})\.json")
SCHED_WIRE = re.compile(r"SCHEDULE\.([1-9][0-9]{0,2})\.json\.zz")
MAX_DECODED = 16 << 20


def unzz(data: bytes, what: str) -> bytes:
    """One whole zlib stream of at most 16 MiB decoded (the guard's bound), else Stop 4."""
    d = zlib.decompressobj()
    try:
        out = d.decompress(data, MAX_DECODED + 1)
    except zlib.error as e:
        raise Stop(4, f"{what}: not a zlib stream ({e})") from None
    if len(out) > MAX_DECODED or d.unconsumed_tail or not d.eof or d.unused_data:
        raise Stop(4, f"{what}: not one whole zlib stream of at most 16 MiB")
    return out


def record(data: bytes, what: str) -> dict:
    try:
        obj = parse_canon(data, what)
    except ValueError as e:
        raise Stop(4, str(e)) from None
    if not isinstance(obj, dict):
        raise Stop(4, f"{what}: not a record")
    return obj


def when(text, what: str) -> int:
    try:
        return MC.utc(text, what)
    except (MC.Refused, ValueError) as e:
        raise Stop(4, f"{what}: not a UTC time ({e})") from None


def visible(c: dict) -> bool:
    """An acceptance home can see: the effect is a schedule or the fence (make_control.effect gives none for kind
    matches and for the outcome UNQUALIFIED, whatever the policy)."""
    return not (c["kind"] == "matches" or c["decision"] == "UNQUALIFIED")


def tail(text: str) -> str:
    return " | ".join(ln.strip() for ln in text.strip().splitlines()[-3:])[-240:]


class Wire(F.Transport):
    """fetch.py's pinned child, rooted at the inbox: list("") is `ls -ln "<remote_root>/inbox"` (no "-"), get(name, ..)
    reads inbox/<name>; run(lines) is one batch of the delivery's own lines."""

    def __init__(self, cfg: dict, ddir: Path):
        if cfg.get("transport") != "sftp":
            raise Stop(2, "deliver.py needs the config's sftp transport")
        super().__init__(cfg, ddir)
        root = self.root.rstrip("/")
        if not root or any(ch in root for ch in '"\\\r\n'):
            raise Stop(2, "remote_root must be a path without quotes, backslashes or line ends")
        self.root = self.inbox = f"{root}/inbox"

    def run(self, lines: list):
        self.batch.write_text("".join(ln + "\n" for ln in lines), encoding="ascii")
        try:
            p = subprocess.run(self.cmd, capture_output=True, timeout=self.cap)
        except subprocess.TimeoutExpired:
            raise Stop(7, f"no end within {self.cap} s: {lines[0][:80]}") from None
        return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


class Home:
    def __init__(self, home: Path, fp: str):
        if not HEX64.fullmatch(fp):
            raise Stop(2, "--fingerprint must be 64 lowercase hex digits")
        if not home.is_dir():
            raise Stop(2, f"{home}: no such home folder")
        self.home, self.fp = home, fp
        self.ddir, self.seen, self.wire = home / "deliver", home / "control", home / "wire"
        self.sent, self.back, self.journal = self.ddir / "sent", self.ddir / "back", self.ddir / "journal.jsonl"
        # the run header FIRST: nothing is made in a folder that is not this run's home (Fable's D2 of 25 Nov: a
        # mistyped --home got deliver/ and control/ before the refusal). Read before the lock, and safely so: fetch.py
        # places wire/RUN.json.zz first and never replaces it during a run.
        p = self.wire / "RUN.json.zz"
        data = unzz(p.read_bytes(), "wire/RUN.json.zz") if p.is_file() else b""
        if sha256_bytes(data) != fp:
            raise Stop(4, "DIR/wire/RUN.json.zz is not this run's header (the fingerprint; fetch.py places it first)")
        self.h = record(data, "RUN.json")
        self.ddir.mkdir(exist_ok=True)
        try:
            self.lock = SlotLock(self.ddir)             # held until the process ends; the OS frees it
        except Stop:
            raise Stop(8, f"another delivery holds {self.ddir / 'LOCK'}: nothing done") from None
        for d in (self.sent, self.back, self.seen):
            d.mkdir(exist_ok=True)

    def note(self, **rec) -> None:
        rec["at_utc"] = F.utc()
        with open(self.journal, "ab") as f:
            f.write(canon(rec))
            f.flush()
            os.fsync(f.fileno())

    def probed(self) -> bool:
        if not self.journal.exists():
            return False
        for ln in self.journal.read_bytes().splitlines():
            try:
                r = json.loads(ln)
            except ValueError:
                continue                                # a line torn by a crash
            if isinstance(r, dict) and r.get("t") == "probe" and r.get("run_fingerprint") == self.fp \
                    and r.get("passed") is True:
                return True
        return False

    def chain(self, folder: Path, what: str) -> list:
        """[(control bytes, control, evidence bytes)] of 1..m, read as make_control.py reads an accepted folder."""
        try:
            pairs = MC.chain(folder, self.fp)[3]
        except (MC.Refused, ValueError) as e:
            raise Stop(4, f"{what} is not a chain of controls: {e}") from None
        return [((folder / f"CONTROL.{c['k']}.json").read_bytes(), c,
                 (folder / f"EVIDENCE.{c['evidence']}.json").read_bytes()) for c, _ in pairs]

    def chains(self):
        sent, seen = self.chain(self.sent, "DIR/deliver/sent/"), self.chain(self.seen, "DIR/control/")
        if len(seen) > len(sent) or any(a[0] != b[0] for a, b in zip(seen, sent)):
            raise Stop(4, "DIR/control/ (the seen chain) is not the beginning of DIR/deliver/sent/ (the sent chain)")
        return sent, seen

    # ---- DV1 the input ---------------------------------------------------------------------------------------------
    def made(self, newdir: Path) -> dict:
        names = sorted(p.name for p in newdir.iterdir()) if newdir.is_dir() else []
        ev = [n for n in names if EV_NAME.fullmatch(n)]
        ct = [n for n in names if MC.CTL_NAME.fullmatch(n)]
        if len(ev) != 1 or len(ct) != 1 or names != sorted([ev[0], ev[0] + ".zz", ct[0], ct[0] + ".zz"]) \
                or not all((newdir / n).is_file() for n in names):
            raise Stop(4, f"{newdir.name}: not exactly the four files of ONE decision (EVIDENCE.<sha256>.json, "
                          f"CONTROL.<k>.json and their .zz): {names[:6]}")
        e, k = EV_NAME.fullmatch(ev[0]).group(1), int(MC.CTL_NAME.fullmatch(ct[0]).group(1))
        evb, evz, cb, cz = ((newdir / n).read_bytes() for n in (ev[0], ev[0] + ".zz", ct[0], ct[0] + ".zz"))
        if unzz(evz, ev[0] + ".zz") != evb or unzz(cz, ct[0] + ".zz") != cb:
            raise Stop(4, f"{newdir.name}: a .zz does not decode to its .json")
        if sha256_bytes(evb) != e:
            raise Stop(4, f"{ev[0]}: its name is not its sha256 (a short or a changed file)")
        c, er = record(cb, ct[0]), record(evb, ev[0])
        if sorted(c) != MC.CONTROL_KEYS or c["schema"] != 2 or c["k"] != k or c["kind"] not in MC.KINDS \
                or c["run_fingerprint"] != self.fp or c["evidence"] != e:
            raise Stop(4, f"{ct[0]}: not a control of FORMATS 1.2 of this run with k {k} and evidence {e[:12]}...")
        if "local_only" in er:
            raise Stop(4, f"{ev[0]}: holds local_only (the full report never travels; the guard holds a control "
                          f"resting on it)")
        if not isinstance(er.get("inputs"), dict) or c["owner_policy"] != er["inputs"].get("plan_sha256"):
            raise Stop(4, f"{ct[0]}: owner_policy is not the evidence's inputs.plan_sha256 (G3 c)")
        return {"k": k, "c": c, "sha": sha256_bytes(cb), "plain": cb,
                "files": [(ev[0], evb), (ev[0] + ".zz", evz), (ct[0], cb), (ct[0] + ".zz", cz)]}

    # ---- DV2 the sequence, DV3 the bounds ------------------------------------------------------------------------
    def sequence(self, d: dict, sent: list, seen: list) -> str:
        k, c = d["k"], d["c"]
        if k <= len(sent):
            if sent[k - 1][0] != d["plain"]:
                raise Stop(3, f"HELD: a different control under the same sequence k {k} was sent before "
                              f"(DIR/deliver/sent/CONTROL.{k}.json): a decision is kept across retries")
            return "retry"
        prev = sha256_bytes(sent[-1][0]) if sent else "first"
        if k != len(sent) + 1 or c["prev"] != prev:
            raise Stop(3, f"HELD: CONTROL.{k}.json is not the next of the sent chain (k {len(sent) + 1}, prev "
                          f"{prev[:12]}): make it with --accepted DIR/deliver/sent")
        if sent and c["kind"] != "fence" and visible(sent[-1][1]) and len(seen) < len(sent):
            m = sent[-1][1]
            raise Stop(3, f"HELD: sent control {m['k']} ({m['kind']} {str(m['decision'])[:40]}) is not seen accepted "
                          f"yet: fetch.py and deliver.py observe first (a fence is never held by this)")
        return "new"

    def bounds(self, c: dict) -> None:
        cut = disp = when(self.h.get("hard_cutoff_utc"), "the header's hard_cutoff_utc")
        sched = {int(m.group(1)): p for p in self.wire.glob("SCHEDULE.*.json.zz") if (m := SCHED_WIRE.fullmatch(p.name))}
        if sched:
            n = max(sched)
            s = record(unzz(sched[n].read_bytes(), sched[n].name), f"SCHEDULE.{n}.json")
            if s.get("run_fingerprint") != self.fp or s.get("n") != n:
                raise Stop(4, f"wire/SCHEDULE.{n}.json.zz is not schedule {n} of this run")
            cut, disp = when(s.get("cutoff_utc"), f"SCHEDULE.{n}'s cutoff_utc"), \
                when(s.get("dispatch_end_utc"), f"SCHEDULE.{n}'s dispatch_end_utc")
        c_cut, c_disp = when(c["cutoff_utc"], "cutoff_utc"), when(c["dispatch_end_utc"], "dispatch_end_utc")
        if c_cut > cut or c_disp > disp or c_disp > c_cut:
            raise Stop(3, f"HELD: a bound later than the one in force (cutoff {c['cutoff_utc']} against {MC.T(cut)}, "
                          f"dispatch end {c['dispatch_end_utc']} against {MC.T(disp)}) or a dispatch end after the cutoff")
        if c["kind"] != "fence":                        # v16 K3: the SERVER's time (late, never early)
            try:
                now = CK.server_now(self.home, self.fp)
            except CK.ClockRefused as e:
                raise Stop(3, f"HELD: the server's time is not known ({e}): a control other than a fence waits "
                              f"for a clock line (clock.py measure); a fence still goes") from None
            if now >= cut:
                raise Stop(3, f"HELD: D has come ({MC.T(cut)}, the cutoff in force) by home's reading of the "
                              f"server's clock, which is late by up to about 75 s; the guard takes no control "
                              f"after the cutoff by its own clocks (guard.py, one_pass): no new playing time; a "
                              f"fence still goes")

    # ---- DV4 and DV5 the transfer ----------------------------------------------------------------------------------
    def listing(self, w: Wire) -> dict:
        return w.list("")[0]                            # judge() inside: 6 or 7; a failed listing 7

    def compare_final(self, w: Wire, name: str, data: bytes) -> None:
        back = self.back / name
        back.unlink(missing_ok=True)
        res, text, _ = w.get(name, back, len(data))
        got = back.read_bytes() if back.exists() else b""
        back.unlink(missing_ok=True)
        if res == "long" or (res == 0 and got != data):
            raise Stop(3, f"CONFLICT: the inbox's {name} holds other bytes than the ones sent; nothing replaced")
        if res != 0:
            F.judge(text)
            raise Stop(7, f"the read back of {name} failed ({res}): {tail(text)}")

    def transfer(self, w: Wire, todo: list):
        listed = self.listing(w)                        # DV5: the FIRST child of a send
        put = there = 0
        for name, data in todo:
            if name in listed:
                self.compare_final(w, name, data)
                there += 1
                self.note(t="file", name=name, how="there already")
                continue
            dot, back = f"{w.inbox}/.{name}.part", self.back / name
            back.unlink(missing_ok=True)
            rc, text = w.run([f'put "{(self.sent / name).as_posix()}" "{dot}"', f'get "{dot}" "{back.as_posix()}"'])
            if rc:
                F.judge(text)
                raise Stop(7, f"the put of {name} failed (exit {rc}): {tail(text)}")
            got = back.read_bytes() if back.exists() else b""
            back.unlink(missing_ok=True)
            if got != data:
                raise Stop(7, f".{name}.part read back with other bytes ({len(got)} of {len(data)}): no rename")
            rc, text = w.run([f'rename -l "{dot}" "{w.inbox}/{name}"'])
            if rc:
                F.judge(text)
                if name not in self.listing(w):
                    raise Stop(7, f"the rename to {name} failed (exit {rc}): {tail(text)}")
                self.compare_final(w, name, data)       # made meanwhile by another sender: equal, or CONFLICT
                there += 1
                self.note(t="file", name=name, how="made meanwhile")
                continue
            put += 1
            self.note(t="file", name=name, how="put")
        final = self.listing(w)
        short = [n for n, data in todo if final.get(n) != len(data)]
        if short:
            raise Stop(7, f"the last listing does not show {short[0]} at its length")
        return put, there


def probe(home: Home, w: Wire) -> str:
    home.listing(w)                                     # the host key and the login first
    a, b, c = f"probe.{os.getpid()}.a", f"probe.{os.getpid()}.b", f"probe.{os.getpid()}.c"
    local = home.back / "probe.bytes"
    local.write_bytes(b"probe\n")
    rc, text = w.run([f'put "{local.as_posix()}" "{w.inbox}/{a}"', f'put "{local.as_posix()}" "{w.inbox}/{b}"'])
    if rc:
        F.judge(text)
        raise Stop(7, f"the probe's put failed (exit {rc}): {tail(text)}")
    rc, text = w.run([f'rename -l "{w.inbox}/{a}" "{w.inbox}/{b}"'])
    refused = rc != 0
    both = home.listing(w)
    kept = a in both and b in both
    rc, text = w.run([f'rename -l "{w.inbox}/{a}" "{w.inbox}/{c}"'])     # P3a: the positive step, a FREE name
    after = home.listing(w)
    moved = rc == 0 and b in after and c in after and a not in after
    w.run([f'-rm "{w.inbox}/{a}"', f'-rm "{w.inbox}/{b}"', f'-rm "{w.inbox}/{c}"'])
    gone = not ({a, b, c} & set(home.listing(w)))
    local.unlink(missing_ok=True)
    passed = refused and kept and moved and gone
    home.note(t="probe", run_fingerprint=home.fp, passed=passed, refused=refused, kept=kept, moved=moved,
              gone=gone)
    if not passed:
        steps = [s for s, ok in (("the rename onto an existing name was NOT refused (it REPLACED the name)", refused),
                                 ("a probe name was missing before the move", kept),
                                 ("the move onto a free name failed", moved),
                                 ("a probe name stayed after the removal", gone)) if not ok]
        raise Stop(3, f"the probe FAILED: {'; '.join(steps)}: no send goes out")
    return ("deliver: probe passed (`rename -l` refuses an existing name and moves to a free one; the probe names "
            "removed)")


def send(home: Home, w: Wire, newdir: Path) -> str:
    d = home.made(newdir)                               # DV1
    sent, seen = home.chains()
    how = home.sequence(d, sent, seen)                  # DV2
    if how == "new":
        home.bounds(d["c"])                             # DV3
    if not home.probed():
        raise Stop(3, "HELD: no passed probe of this run in DIR/deliver/journal.jsonl (deliver.py probe, once after "
                      "the admission)")
    for name, data in d["files"]:                       # the sent chain, BEFORE the first byte travels
        create_only(home.sent / name, data)
    home.note(t="sent_copy", k=d["k"], control=d["sha"], how=how)
    sent, seen = home.chains()
    todo = []
    for cb, c, _ in sent[len(seen):d["k"]]:             # every sent control above the seen chain up to k, in order
        for name in (f"EVIDENCE.{c['evidence']}.json.zz", f"CONTROL.{c['k']}.json.zz"):
            todo.append((name, (home.sent / name).read_bytes()))
    put, there = home.transfer(w, todo) if todo else (0, 0)
    home.note(t="sent", k=d["k"], control=d["sha"], put=put, there=there)
    c = d["c"]
    return (f"deliver: CONTROL.{d['k']}.json {d['sha'][:12]} ({c['kind']} {str(c['decision'])[:40]}) {how}: "
            f"{len(todo) // 2} control(s) in the inbox, {put} file(s) put, {there} there already; its acceptance is "
            f"seen only by deliver.py observe after a fetch")


def observe(home: Home) -> str:
    sent, seen = home.chains()
    named = set()
    for p in home.wire.glob("SCHEDULE.*.json.zz"):
        if SCHED_WIRE.fullmatch(p.name):
            s = record(unzz(p.read_bytes(), p.name), p.name[:-3])
            if s.get("run_fingerprint") == home.fp and HEX64.fullmatch(str(s.get("evidence"))):
                named.add(s["evidence"])
    why = ""
    fz = home.wire / "FENCE.json.zz"
    if fz.is_file():
        f = record(unzz(fz.read_bytes(), "wire/FENCE.json.zz"), "FENCE.json")
        why = str(f.get("why")) if f.get("run_fingerprint") == home.fp else ""
    top = max([i for i, (cb, _, _) in enumerate(sent, 1)
               if sha256_bytes(cb) in named or (why and sha256_bytes(cb) in why)], default=0)
    if top <= len(seen):
        return (f"deliver: observe: not seen yet: {len(sent) - len(seen)} sent control(s) above the seen chain of "
                f"{len(seen)}" if len(sent) > len(seen) else f"deliver: observe: all {len(seen)} sent control(s) seen")
    for cb, c, evb in sent[len(seen):top]:
        create_only(home.seen / f"EVIDENCE.{c['evidence']}.json", evb)
        create_only(home.seen / f"CONTROL.{c['k']}.json", cb)
        home.note(t="seen", k=c["k"], control=sha256_bytes(cb))
    return f"deliver: observe: controls {len(seen) + 1} to {top} accepted (seen through a schedule or the fence)"


def main() -> int:
    ap = argparse.ArgumentParser(description="The home delivery of the owner's decisions.", allow_abbrev=False)
    ap.add_argument("what", choices=("probe", "send", "observe"))
    ap.add_argument("--home", required=True)
    ap.add_argument("--fingerprint", required=True)
    ap.add_argument("--config")
    ap.add_argument("--made")
    a = ap.parse_args()
    home = None
    try:
        if (a.what != "observe") != (a.config is not None) or (a.what == "send") != (a.made is not None):
            raise Stop(2, "probe and send need --config, send needs --made, observe takes neither")
        home = Home(Path(a.home).resolve(), a.fingerprint)
        if a.what == "observe":
            print(observe(home))
            return 0
        try:
            cfg = json.loads(Path(a.config).read_text(encoding="ascii"))
        except (OSError, ValueError) as e:
            raise Stop(2, f"the config cannot be read: {e}") from None
        if not isinstance(cfg, dict):
            raise Stop(2, "the config is not one JSON object")
        w = Wire(cfg, home.ddir)
        print(probe(home, w) if a.what == "probe" else send(home, w, Path(a.made).resolve()))
        return 0
    except Stop as e:
        print(f"deliver: STOP {e.code}: {e}")
        if home is not None:
            try:
                home.note(t="stop", code=e.code, why=str(e)[:300])
            except OSError:
                pass
        return e.code
    except OSError as e:
        print(f"deliver: STOP 4: a home file cannot be read or written: {e}")
        return 4


if __name__ == "__main__":
    sys.exit(main())
