"""launcher.py: writes the day's header RUN.json ONCE, before the pilot (A3b, part 2; FORMATS 1.1, 1.2, 0;
SETUP_PLAN D3, D5, D6, D15). Standard library, the worker module and the boot guard only.

    launcher.py --root DIR --exe ENGINE --net NET --manifest MANIFEST.json --package-list MANIFEST.sha256
                --pinned SHA256 --run NAME --lease-start UTC --lease-end UTC --slots N --piece-games G
                --round-games R --pilot-rounds K (--root-seed S | --openings FILE)
                [--sync-wait 900] [--etc /etc] [--dmi /sys/class/dmi/id]

The header (FORMATS 1.1): schema 2; the run name; the lease's start and end as the provider shows them; the hard
cutoff = min(start + 23 h, end - 1 h), the latest D that D5 allows (a schedule can only tighten it); the machine's
boot id (the worker's own reading); `instance` and `instance_provable`, read by the boot guard's own function, so
that the header and every later boot are read the same way; `package` = the pinned sha256 of the package's hash
list (pinned OUTSIDE the package, D6); the sha256 of the engine file, of the net (it must be the manifest's), of the
manifest's option lines (each ended by LF); the manifest's game line; the opening rule, the seed rule with 8 plies
or a list (refused with more than one slot: the slots would play the same openings, FORMATS 1.1 [2.3]); the slots
0 to N-1; piece_games; the pilot ranges of D3: K whole rounds of R games for every slot, round r holding the
counters (r-1)R+1 to rR, schedule 0 (a schedule continues each slot's rows at that length).
Written create-only (FORMATS 0): the same bytes there already = done; other bytes = kept as
RUN.json.conflict.<12hex> and exit 4. Nothing else is written. Before writing, in this order: the arguments; the
clock synchronised (waited for, at most --sync-wait seconds); the lease against UTC now; the package list (its
sha256 is the pinned one, the publisher's form, every file it names has its sha256: the boot guard's own check);
the net; the instance provable (D15: a restart is survived without anybody, and an unprovable instance holds every
reboot for a person).

Exit codes: 0 written (or the same bytes were there); 2 arguments (the manifest's form too); 4 RUN.json there with
other bytes, or a file that cannot be read or written; 5 this machine, its clock or the package do not qualify. A
refusal names its reason in one line and writes nothing.

VERSION 2 (24 Nov; Astra 8290095d and Neon 20261123T222600Z; known answers written before the code):
- --pilot-rounds at most 9999, because the worker refuses a row of round 10000.
- --piece-games at most 99999999, FORMATS 1.2's counter bound.
- The manifest is checked whole before it is used:
  - options a list of printable-ASCII texts, so no LF inside a line (the hash joins the lines with LF);
  - selfgame_line such a text;
  - net_sha256 64 hex.
- The boot id is read inside a handler (exit 5).
- An OSError while a file is read or written is exit 4, never a traceback."""
import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import NoReturn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bootguard as BG  # noqa: E402
import record  # noqa: E402
import worker as W  # noqa: E402
from worker import Stop, canon, create_only, file_sha256, sha256_bytes  # noqa: E402

HOUR = 3600
TEXT = re.compile(r"[\x20-\x7e]+")              # a text of printable ASCII, no line end inside (version 2)


def header(a, rd) -> dict:
    """The header, or BG.Held(code, reason) before anything is written."""
    def no(code, text) -> NoReturn:
        raise BG.Held(code, text)
    if not re.fullmatch(r"[a-z0-9]{1,32}", a.run or ""):
        no(2, "--run: 1 to 32 letters a-z or digits")
    if not re.fullmatch(r"[0-9a-f]{64}", a.pinned or ""):
        no(2, "--pinned: the sha256 of the package's hash list, 64 lower-case hex digits")
    try:
        start, end = W.utc(a.lease_start, "--lease-start"), W.utc(a.lease_end, "--lease-end")
    except Stop as e:
        no(2, str(e))
    if end <= start:
        no(2, "the lease ends before it starts")
    for name in ("slots", "piece_games", "round_games", "pilot_rounds"):
        if type(getattr(a, name)) is not int or getattr(a, name) < 1:
            no(2, f"--{name.replace('_', '-')} is an integer >= 1")
    if a.slots > 1000 or a.round_games * a.pilot_rounds > 99999999:
        no(2, "at most 1000 slots, and the pilot's counters at most 99999999 (FORMATS 1.2)")
    if a.pilot_rounds > 9999:                   # Astra 8290095d: the worker's check_rows refuses round 10000
        no(2, "--pilot-rounds is at most 9999: a round is r0001 to r9999, and the worker refuses round 10000")
    if a.piece_games > 99999999:                # Neon 222600Z: a piece's games are counters of one range (FORMATS 1.2)
        no(2, "--piece-games is at most 99999999: a piece holds games of one range, whose counters stop there")
    if (a.root_seed is None) == (a.openings is None):
        no(2, "exactly one of --root-seed (the seed rule) and --openings (the list rule)")
    if a.root_seed is not None:
        if not re.fullmatch(r"[A-Za-z0-9_]{1,64}", a.root_seed):
            no(2, "--root-seed: 1 to 64 letters, digits or _")
        rule = {"kind": "seed", "plies": 8, "root_seed": a.root_seed}
    else:
        if a.slots > 1:
            no(2, "the list rule with more than one slot: the slots would play the same openings (FORMATS 1.1 [2.3])")
        try:
            data = Path(a.openings).read_bytes()
            lines = data.decode("ascii").split("\n")[:-1]
        except (OSError, UnicodeDecodeError):
            no(2, "--openings cannot be read as ASCII")
        if not data.endswith(b"\n") or not all(all(record.MOVE.fullmatch(m) for m in ln.split(" ")) if ln else True
                                                for ln in lines):
            no(2, "--openings: lines of moves, each ended by LF")
        rule = {"kind": "list", "sha256": sha256_bytes(data), "count": len(lines)}
    if not Path(a.root).is_dir():
        no(2, "--root is not a folder")
    t0 = time.monotonic()
    while not rd.synced():
        left = a.sync_wait - (time.monotonic() - t0)
        if left <= 0:
            no(5, f"the clock is not synchronised after {a.sync_wait:g} s (D5)")
        rd.sleep(min(5.0, left))
    now, cut = rd.utc(), min(start + 23 * HOUR, end - HOUR)
    if now < start:
        no(2, f"UTC now ({BG.T(now)}) is before the lease start ({a.lease_start})")
    if cut <= now:
        no(2, f"the hard cutoff min(start + 23 h, end - 1 h) = {BG.T(cut)} is not after UTC now ({BG.T(now)})")
    BG.BootGuard(a, rd).package({"package": a.pinned})
    try:
        man = json.loads(Path(a.manifest).read_bytes().decode("ascii"))
        opts, line, want = man["options"], man["selfgame_line"], man["net_sha256"]
        net, exe = file_sha256(Path(a.net)), file_sha256(Path(a.exe))
    except (OSError, ValueError, KeyError, TypeError) as e:
        no(2, f"the manifest, the net or the engine cannot be read: {e!r}")
    if not isinstance(opts, list):              # list() made a text into its characters and a dict into its keys
        no(2, "the manifest's options are not a list")
    if not all(isinstance(ln, str) and TEXT.fullmatch(ln) for ln in opts):     # Neon 222600Z; "a\nb" hashed as 2
        no(2, "the manifest's option lines are not all texts of printable ASCII (0x20 to 0x7e, no line end inside: "
              "the hash joins them with LF)")
    if not (isinstance(line, str) and TEXT.fullmatch(line)):                    # Neon 222600Z
        no(2, "the manifest's selfgame_line is not a text of printable ASCII")
    if not (isinstance(want, str) and W.HEX64.fullmatch(want)):                 # a malformed manifest, not another net
        no(2, "the manifest's net_sha256 is not 64 lower-case hex digits")
    if net != want:
        no(5, "the net file is not the manifest's net_sha256")
    inst = BG.read_instance(Path(a.etc), Path(a.dmi))
    if not BG.provable(inst):
        no(5, "the instance is not provable (a machine id and at least one hardware value): every reboot would be "
              "held for a person (D15)")
    try:
        boot = rd.boot()
    except (OSError, ValueError) as e:          # Neon 222600Z: worker.boot_id() reads /proc with no handler
        no(5, f"the boot id cannot be read: {e!r}")
    return {"schema": 2, "run": a.run, "lease_start_utc": a.lease_start, "lease_end_utc": a.lease_end,
            "hard_cutoff_utc": BG.T(cut), "boot_id": boot, "instance": inst, "instance_provable": True,
            "package": a.pinned, "engine_sha256": exe, "net_sha256": net,
            "options_sha256": sha256_bytes("".join(ln + "\n" for ln in opts).encode("ascii")),
            "game_line": line, "opening_rule": rule, "slots": list(range(a.slots)),
            "piece_games": a.piece_games,
            "pilot_ranges": [{"first": (r - 1) * a.round_games + 1, "last": r * a.round_games, "round": r,
                              "schedule": 0, "short": False, "slot": k}
                             for r in range(1, a.pilot_rounds + 1) for k in range(a.slots)]}


def launch(a, rd=None) -> int:
    rd = rd or BG.readers()
    try:
        h = header(a, rd)
        data = canon(h)
        create_only(Path(a.root) / "RUN.json", data)
    except BG.Held as e:
        print(f"REFUSED exit {e.code}: {e.text}", flush=True)
        return e.code
    except Stop as e:
        print(f"REFUSED exit {e.code}: {e}", flush=True)
        return e.code
    except OSError as e:                        # version 2: a file that cannot be read or written, never a traceback
        print(f"REFUSED exit 4: a file cannot be read or written: {e!r}", flush=True)
        return 4
    print(f"launcher: RUN.json of run {h['run']}: fingerprint {sha256_bytes(data)}; slots {a.slots}; pilot rounds "
          f"{a.pilot_rounds}, {a.round_games} games a slot each; hard cutoff {h['hard_cutoff_utc']}", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ("root", "exe", "net", "manifest", "package-list", "pinned", "run", "lease-start", "lease-end"):
        ap.add_argument("--" + name, required=True)
    for name in ("slots", "piece-games", "round-games", "pilot-rounds"):
        ap.add_argument("--" + name, type=int, required=True)
    ap.add_argument("--root-seed")
    ap.add_argument("--openings")
    ap.add_argument("--sync-wait", type=float, default=900.0)
    ap.add_argument("--etc", default="/etc")
    ap.add_argument("--dmi", default="/sys/class/dmi/id")
    a = ap.parse_args()
    if not 0 <= a.sync_wait <= 86400:
        print("REFUSED exit 2: --sync-wait is 0 to 86400 seconds")
        return 2
    return launch(a)


if __name__ == "__main__":
    sys.exit(main())
