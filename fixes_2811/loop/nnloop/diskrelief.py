"""Free disk space from old self-play data before the disk limit stops the loop (added 2026-11-15).

Owner, 2026-11-15: "when selfplay gets too large for disk space filter the positions that frees space by a bit".

What is touched: ONLY rounds that are no longer in the training window (the loop trains on the newest rounds up
to [train] max_window_positions; older rounds are read by nothing in the loop). For such a round, oldest first:
  1. its training cache (filtered.plain.cache-*.npz, about 1.1 GB) is deleted: it can be rebuilt from the
     positions file at any time;
  2. its positions file (filtered.plain, about 1.5 GB of text) is packed to filtered.plain.gz (about a fifth of
     the size) and the unpacked file removed. NO POSITION IS LOST: unpack with any gzip tool to get the same
     file back (the packed file is read back and compared by size and checksum before the original is removed).
It stops as soon as the free space is back above the wanted figure. Nothing else is ever deleted here.
  3. (since 2026-11-16, owner: the lab's own self-play data may go to his other disks, never below 30 GB free
     there) when C: is still under [limits] overflow_below_gb, the PACKED positions file of such a round is moved
     to a folder of the lab's own on another disk ([limits] overflow_dirs: each a direct child of a drive's root,
     carrying OVERFLOW_MARKER; a folder of that name without the marker is never used): copied create-only,
     compared byte for byte, a pointer file (MOVED_POINTER) written in its place, and only then the original
     removed. restore_plain brings such a round back from there when it re-enters the training window.
If that is not enough, the loop's ordinary disk limit ([limits] min_free_gb) stops the loop and the owner decides.

Config, [limits]: relief_below_gb (0 or unset = off); step 3: overflow_dirs, overflow_below_gb (unset or 0 =
off), overflow_floor_gb (never under 30). Each round packed is written into the loop's notes.
A packed round that comes back into the training window is unpacked again before the training (restore_plain,
called by run.py; 2026-11-16).
"""
from __future__ import annotations

import gzip
import json
import os
import shutil
import time
import zlib
from pathlib import Path


def _crc_file(path: Path, opener=open) -> tuple[int, int]:
    crc, n = 0, 0
    with opener(path, "rb") as fh:
        while True:
            b = fh.read(1 << 22)
            if not b:
                break
            crc = zlib.crc32(b, crc)
            n += len(b)
    return crc, n


LAB_ROOT = Path("C:/nnue-lab")


def _is_link(p: Path) -> bool:
    """A symbolic link or a junction (Windows' mount-point kind of link)."""
    try:
        return p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction())
    except OSError:
        return True                       # cannot tell: treat as a link, i.e. do not touch


def round_in_lab(data_dir: Path) -> str | None:
    """None when data_dir is a plain <runs>/rNNNN/data folder of the lab; otherwise why not (Opus 2026-11-16, the
    live-code part of review finding A1: a round folder or its data folder that is a link or a junction, made by
    hand, would let steps 1/2 delete and write wherever it points, outside the lab)."""
    rnd, runs = data_dir.parent, data_dir.parent.parent
    for p in (runs, rnd, data_dir):
        if _is_link(p):
            return f"{p} is a link or junction"
    try:
        real, lab = data_dir.resolve(strict=True), LAB_ROOT.resolve()
        want = runs.resolve(strict=True) / rnd.name / data_dir.name
    except OSError as e:
        return f"{data_dir} cannot be resolved ({type(e).__name__})"
    if real != want:
        return f"{data_dir} resolves to {real}, not {want}"
    if lab != real and lab not in real.parents:
        return f"{data_dir} resolves to {real}, outside {lab}"
    return None


def pack_round(data_dir: Path) -> dict:
    """Step 1 and 2 for one round's data folder. Returns what was done and the bytes freed."""
    out = {"dir": str(data_dir), "caches_deleted": 0, "packed": False, "freed_bytes": 0}
    why = round_in_lab(data_dir)
    if why is not None:
        raise RuntimeError(f"not a plain round folder of the lab: {why}; nothing touched")
    plain = data_dir / "filtered.plain"
    packed = data_dir / "filtered.plain.gz"
    # caches only when the positions (plain or packed) are there to rebuild them from
    if plain.exists() or packed.exists():
        for c in sorted(data_dir.glob("filtered.plain.cache-*.npz")):
            if _is_link(c):
                continue                  # a link is never followed or removed here
            size = c.stat().st_size
            c.unlink()
            out["caches_deleted"] += 1
            out["freed_bytes"] += size
    if plain.exists() and not packed.exists() and not _is_link(plain):
        tmp = data_dir / "filtered.plain.gz.part"
        # a .part left by an interrupted run is REMOVED first and the new one made with "x" (create, never open an
        # existing file): writing into an existing name would write through a hard link into another file (review
        # finding A9, the live-code part)
        tmp.unlink(missing_ok=True)
        with open(plain, "rb") as src, open(tmp, "xb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=6) as dst:
                shutil.copyfileobj(src, dst, 1 << 22)
            raw.flush()
            os.fsync(raw.fileno())        # on the disk before the original goes (audit finding 2, 2026-11-17)
        if _crc_file(tmp, gzip.open) != _crc_file(plain):
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"packed copy of {plain} does not read back equal; nothing removed")
        size = plain.stat().st_size
        tmp.replace(packed)
        plain.unlink()
        out["packed"] = True
        out["freed_bytes"] += size - packed.stat().st_size
    return out


# ------------------------------------------------------------------------------------------------------ re-entry
# Opus 2026-11-16, Fable's job 6: a round packed by step 2 that comes BACK into the training window (the cap went up,
# or a longer window) was left out of the training without a word (run.py took only rounds whose filtered.plain
# exists). run.py now asks restore_plain() for such a round before the training.
CACHE_PER_PLAIN = 0.75    # the trainer's cache filtered.plain.cache-*.npz is about 0.70 of filtered.plain (round 16:
                          # 1.068 against 1.520 GB); the trainer makes it again from the restored text


def _gz_plain_bytes(packed: Path) -> int:
    """About the size of the unpacked text, on the safe side: gzip's own ISIZE (the size mod 2**32; a round's text
    is 0.3 to 1.6 GB, far below 4 GiB) or 6 times the packed size (text of this kind packs about 5:1), the larger."""
    with open(packed, "rb") as fh:
        fh.seek(-4, 2)
        isize = int.from_bytes(fh.read(4), "little")
    return max(isize, 6 * packed.stat().st_size)


def restore_plain(data_dir: Path, free_gb_fn, min_free_gb: float) -> dict:
    """Bring a round's filtered.plain back from its filtered.plain.gz. The text is unpacked to filtered.plain.part
    (a stale one removed first, the new one made create-only), read back and compared with the packed copy (CRC and
    size; gzip checks its own CRC as well) before it takes the name filtered.plain; then the .gz is removed. A .gz
    that cannot be removed (in use) stays beside it ("packed_left"): harmless, step 2 leaves a round with both alone.
    Refused (RuntimeError, nothing changed) when the folder is not a plain round folder of the lab, when there is no
    packed copy to bring it back from (a round dropped by step 2b is named), or when the text plus the training cache
    the trainer will make from it would take the free space under min_free_gb."""
    data_dir = Path(data_dir)
    out = {"dir": str(data_dir), "restored": False, "bytes": 0, "packed_left": False}
    why = round_in_lab(data_dir)
    if why is not None:
        raise RuntimeError(f"not a plain round folder of the lab: {why}; nothing touched")
    plain, packed = data_dir / "filtered.plain", data_dir / "filtered.plain.gz"
    if plain.exists():
        return out
    moved = None
    if not packed.exists() and (data_dir / MOVED_POINTER).exists():
        moved = _read_pointer(data_dir / MOVED_POINTER)[0]   # step 3 moved it: read it there (refused when the copy
        packed = moved                                        # is not where and what the pointer says)
        out["moved_from"] = str(moved)
    if not packed.is_file() or _is_link(packed):
        extra = (" (DROPPED.txt is there: dropped by step 2b; bring it back with "
                 "pipeline/experiments/rebuild_round.py)") if (data_dir / "DROPPED.txt").exists() else ""
        raise RuntimeError(f"{data_dir} holds neither filtered.plain nor filtered.plain.gz (as a plain file){extra}")
    need_gb = _gz_plain_bytes(packed) * (1 + CACHE_PER_PLAIN) / 2**30
    free = free_gb_fn()
    if free - need_gb < min_free_gb:
        raise RuntimeError(f"bringing it back needs about {need_gb:.1f} GB (positions and the training cache made "
                           f"from them); {free:.1f} GB are free and [limits] min_free_gb is {min_free_gb:g}: "
                           f"not restored")
    tmp = data_dir / "filtered.plain.part"
    tmp.unlink(missing_ok=True)           # a link is removed itself, never written through (see pack_round)
    try:
        with gzip.open(packed, "rb") as src, open(tmp, "xb") as dst:
            shutil.copyfileobj(src, dst, 1 << 22)      # a damaged .gz stops here (gzip checks its CRC at the end)
            dst.flush()
            os.fsync(dst.fileno())        # on the disk before the packed copy goes (audit finding 2, 2026-11-17)
        same = _crc_file(tmp) == _crc_file(packed, gzip.open)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    if not same:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"the unpacked copy of {packed} does not read back equal; nothing changed")
    tmp.replace(plain)
    out["restored"] = True
    out["bytes"] = plain.stat().st_size
    try:
        packed.unlink()                   # a moved round: the lab's own copy on the other disk
        if moved is not None:
            (data_dir / MOVED_POINTER).unlink()
    except OSError:
        out["packed_left"] = True
    return out


def relieve(round_dirs: list[tuple[int, Path]], want_free_gb: float, free_gb_fn, say) -> list[dict]:
    """round_dirs: (round number, data folder) of rounds OUTSIDE the training window, oldest first."""
    done = []
    for rr, d in round_dirs:
        if free_gb_fn() >= want_free_gb:
            break
        if not d.is_dir():
            continue
        try:
            res = pack_round(d)
        except Exception as e:  # noqa: BLE001
            say(f"disk relief: round {rr} left as it is ({type(e).__name__}: {str(e)[:160]})")
            continue
        if res["freed_bytes"] > 0:
            res["round"] = rr
            done.append(res)
            say(f"disk relief: round {rr} (no longer in the training window): training cache deleted "
                f"({res['caches_deleted']} file(s)), positions {'packed to filtered.plain.gz' if res['packed'] else 'already packed'}; "
                f"{res['freed_bytes'] / 1e9:.2f} GB freed, {free_gb_fn():.1f} GB free now. No position was lost.")
    return done


# ------------------------------------------------------------------------------------- step 3: another disk
# Owner, 2026-11-15 about 09:25, and 2026-11-16 about 18:05 (Opus's window): "you are allowed to write the self play
# data if disk space gets right to other disks once all disks are at 30gb thats the stop"; about 18:10: build it,
# "if youre calculations are wrong it could waaste days". What moves: ONLY the packed positions file
# (filtered.plain.gz, step 2) of a round OUTSIDE the training window, oldest first, while C: is under the wanted
# figure. The game file (raw_selfplay.binpack) and every small file stay on C:. Nothing outside the lab's own
# overflow folders is ever written, and nothing there is written that is not one of these files, the marker or a
# .part being copied.
OVERFLOW_MARKER = "NNUE_LAB_OVERFLOW_MARKER.txt"
MOVED_POINTER = "filtered.plain.gz.MOVED.json"
OVERFLOW_FLOOR_MIN_GB = 30.0             # the owner's floor for every other disk; a config value under it is raised
_MARKER_TEXT = (
    "This folder belongs to the NNUE lab in C:\\nnue-lab (the owner's chess engine training).\n"
    "It holds ONLY the lab's own self-play data (packed positions files of old rounds), moved here by\n"
    "C:\\nnue-lab\\pipeline\\nnloop\\diskrelief.py (step 3) when C: ran short, with the owner's permission of\n"
    "2026-11-15 and 2026-11-16. This disk is never taken below 30 GB free by it. Every moved file has a pointer\n"
    "file (filtered.plain.gz.MOVED.json) in its round folder under C:\\nnue-lab\\runs. Nothing else on this\n"
    "disk was touched.\n")


def _disk_free_gb(path) -> float:
    p = Path(path)
    return shutil.disk_usage(p.anchor or str(p)).free / 2**30


def _root_shape_problem(root: Path) -> str | None:
    """None when root has the shape of an overflow folder: an absolute path that is a direct child of a drive's
    root, on another drive than the lab's. The shape only; the disk is not looked at."""
    root = Path(root)
    if not root.is_absolute() or not root.drive:
        return f"{root} is not an absolute path with a drive"
    if root.parent != Path(root.anchor) or root.name in ("", ".", ".."):
        return f"{root} is not a direct child of its drive's root"
    if root.drive.upper() == LAB_ROOT.drive.upper():
        return f"{root} is on the lab's own drive"
    return None


def overflow_root(root, create: bool) -> tuple[Path | None, str | None]:
    """(root, None) when root is the lab's own overflow folder and may be used; (None, why) otherwise. With create, a
    missing root is made (one mkdir, never its parents) and the marker written create-only. A root that exists
    without the marker, or is a link, a junction or not a folder, is never used and never written into."""
    root = Path(root)
    why = _root_shape_problem(root)
    if why:
        return None, why
    if _is_link(root):
        return None, f"{root} is a link or junction"
    if not root.exists():
        if not create:
            return None, f"{root} does not exist"
        try:
            root.mkdir()                  # no parents; an existing name (made meanwhile) is refused, not reused
            with open(root / OVERFLOW_MARKER, "x", encoding="utf-8") as fh:
                fh.write(_MARKER_TEXT + "Made: " + time.strftime("%Y-%m-%d %H:%M:%S") + " (PC clock)\n")
        except OSError as e:
            return None, f"{root} could not be made ({type(e).__name__}: {e})"
    if _is_link(root) or not root.is_dir():
        return None, f"{root} is a link, a junction or not a folder"
    m = root / OVERFLOW_MARKER
    if _is_link(m) or not m.is_file():
        return None, f"{root} exists but does not carry the lab's marker {OVERFLOW_MARKER}: not ours, not touched"
    return root, None


def _read_pointer(pointer: Path) -> tuple[Path, dict]:
    """(the moved copy, the pointer's data). Raises when the pointer is not a plain file, names a folder that is not
    the lab's own overflow folder, or the copy is not there, not inside that folder, or not of the recorded size."""
    if _is_link(pointer) or not pointer.is_file():
        raise RuntimeError(f"{pointer} is not a plain file")
    info = json.loads(pointer.read_text(encoding="utf-8"))
    root, why = overflow_root(Path(info["root"]), create=False)
    if why:
        raise RuntimeError(f"the pointer {pointer} names a folder that is not usable: {why}")
    dest = Path(info["moved_to"])
    try:
        real = dest.resolve(strict=True)
    except OSError as e:
        raise RuntimeError(f"the moved copy {dest} named by {pointer} is not there ({type(e).__name__})")
    if root.resolve() not in real.parents:
        raise RuntimeError(f"{dest} resolves to {real}, not inside {root}")
    if _is_link(dest) or not dest.is_file() or dest.stat().st_size != int(info["bytes"]):
        raise RuntimeError(f"{dest} is not the plain file of {info['bytes']} bytes that {pointer} names")
    return dest, info


def move_round(data_dir, roots, floor_gb: float, disk_free_gb=_disk_free_gb) -> dict:
    """Step 3 for one round's data folder (outside the training window, packed by step 2). Returns what was done;
    "skip" says why nothing was, "all_full" that no other disk has room above its floor."""
    data_dir = Path(data_dir)
    floor_gb = max(OVERFLOW_FLOOR_MIN_GB, float(floor_gb))
    out = {"dir": str(data_dir), "moved": False, "freed_bytes": 0, "to": None}
    why = round_in_lab(data_dir)
    if why is not None:
        raise RuntimeError(f"not a plain round folder of the lab: {why}; nothing touched")
    plain, packed, pointer = data_dir / "filtered.plain", data_dir / "filtered.plain.gz", data_dir / MOVED_POINTER
    if plain.exists():
        out["skip"] = "its positions are not packed (step 2 first)"
        return out
    if not packed.exists():
        out["skip"] = "moved already" if pointer.exists() else "no packed positions file"
        return out
    if _is_link(packed) or not packed.is_file():
        raise RuntimeError(f"{packed} is not a plain file; nothing touched")
    src = _crc_file(packed)
    if pointer.exists():                  # an earlier run copied it and wrote the pointer, then stopped
        dest, _info = _read_pointer(pointer)
        if _crc_file(dest) != src:
            raise RuntimeError(f"{pointer} names {dest}, which differs from {packed}; nothing touched")
        packed.unlink()
        out.update(moved=True, freed_bytes=src[1], to=str(dest), finished_earlier=True)
        return out
    need_gb, chosen, notes = src[1] / 2**30, None, []
    free_of = {}
    for r0 in roots:
        try:
            free_of[str(r0)] = float(disk_free_gb(Path(r0)))
        except OSError as e:
            notes.append(f"{r0}: free space unreadable ({type(e).__name__})")
    for r0 in sorted((Path(x) for x in free_of), key=lambda p: -free_of[str(p)]):
        free = free_of[str(r0)]
        if free - need_gb < floor_gb:
            notes.append(f"{r0}: {free:.1f} GB free, the floor is {floor_gb:g} GB")
            continue
        root, why = overflow_root(r0, create=False)   # the owner made both folders (20 Nov): a missing one is not ours to make
        if why:
            notes.append(why)
            continue
        chosen = root
        break
    if chosen is None:
        out.update(skip="; ".join(notes) or "no overflow folder named", all_full=True)
        return out
    rel = data_dir.resolve(strict=True).relative_to(LAB_ROOT.resolve())
    dest_dir = chosen / rel
    p = chosen
    for part in rel.parts:                # no link on the way down, BEFORE anything is made (mkdir would go through)
        p = p / part
        if _is_link(p):
            raise RuntimeError(f"{p} is a link or junction; nothing moved")
    dest_dir.mkdir(parents=True, exist_ok=True)
    if dest_dir.resolve(strict=True) != chosen.resolve(strict=True) / rel:
        raise RuntimeError(f"{dest_dir} resolves elsewhere (a link or junction on the way); nothing moved")
    dest = dest_dir / "filtered.plain.gz"
    if dest.exists():                     # an earlier run copied it and stopped before the pointer
        if _is_link(dest) or not dest.is_file() or _crc_file(dest) != src:
            raise RuntimeError(f"{dest} exists and is not the same file as {packed}; nothing moved")
    else:
        tmp = dest_dir / "filtered.plain.gz.part"
        tmp.unlink(missing_ok=True)       # a link is removed itself, never written through
        try:
            with open(packed, "rb") as fs, open(tmp, "xb") as fd:
                shutil.copyfileobj(fs, fd, 1 << 22)
                fd.flush()
                os.fsync(fd.fileno())
            same = _crc_file(tmp) == src
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
        if not same:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"the copy of {packed} on {chosen} does not read back equal; nothing moved")
        tmp.replace(dest)
    if _crc_file(dest) != src:
        raise RuntimeError(f"{dest} does not read back equal after its rename; the original stays")
    info = {"moved_to": str(dest), "root": str(chosen), "bytes": src[1], "crc32": src[0], "round_dir": str(data_dir),
            "by": "pipeline/nnloop/diskrelief.py step 3", "when": time.strftime("%Y-%m-%d %H:%M:%S")}
    ptmp = data_dir / (MOVED_POINTER + ".part")
    ptmp.unlink(missing_ok=True)
    with open(ptmp, "x", encoding="utf-8") as fh:
        json.dump(info, fh, indent=1)
        fh.flush()
        os.fsync(fh.fileno())
    ptmp.replace(pointer)
    _read_pointer(pointer)                # the pointer must lead to the copy before the original goes
    packed.unlink()
    out.update(moved=True, freed_bytes=src[1], to=str(dest))
    return out


def overflow(round_dirs, roots, want_free_gb: float, floor_gb: float, free_gb_fn, say,
             disk_free_gb=_disk_free_gb) -> list[dict]:
    """Step 3 over round_dirs ((round, data folder) of rounds OUTSIDE the training window, oldest first) until C:
    has want_free_gb free. One note per round moved or left; one WARNING when no other disk has room."""
    done = []
    for rr, d in round_dirs:
        if free_gb_fn() >= want_free_gb:
            break
        if not Path(d).is_dir():
            continue
        try:
            res = move_round(d, roots, floor_gb, disk_free_gb)
        except Exception as e:  # noqa: BLE001
            say(f"disk relief step 3: round {rr} left as it is ({type(e).__name__}: {str(e)[:200]})")
            continue
        if res.get("all_full"):
            say(f"disk relief step 3: WARNING: no other disk has room for round {rr}'s packed positions "
                f"({res['skip'][:300]}); nothing moved, C: has {free_gb_fn():.1f} GB free")
            break
        if res["moved"]:
            res["round"] = rr
            done.append(res)
            say(f"disk relief step 3: round {rr} (no longer in the training window): its packed positions file "
                f"({res['freed_bytes'] / 1e9:.2f} GB) is now {res['to']} (copied, compared byte for byte, a pointer "
                f"left in its place); {free_gb_fn():.1f} GB free on C: now. No position was lost.")
    return done


def overflow_step(cfg: dict, runs, dropped, say, free_gb_fn=None, disk_free_gb=_disk_free_gb) -> list[dict]:
    """What run.py calls after steps 1 and 2: step 3 when [limits] overflow_dirs and overflow_below_gb are set and
    C: has less than overflow_below_gb free; it moves until overflow_below_gb + 5."""
    lim = cfg.get("limits") or {}
    roots = [Path(p) for p in (lim.get("overflow_dirs") or [])]
    below = float(lim.get("overflow_below_gb", 0) or 0)
    if not roots or not below or not dropped:
        return []
    if free_gb_fn is None:
        free_gb_fn = lambda: shutil.disk_usage(str(runs)).free / 2**30   # noqa: E731
    if free_gb_fn() >= below:
        return []
    floor = max(OVERFLOW_FLOOR_MIN_GB, float(lim.get("overflow_floor_gb", OVERFLOW_FLOOR_MIN_GB) or 0))
    return overflow([(rr, Path(runs) / f"r{rr:04d}" / "data") for rr in dropped], roots, below + 5.0, floor,
                    free_gb_fn, say, disk_free_gb)
