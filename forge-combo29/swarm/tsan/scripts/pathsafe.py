#!/usr/bin/env python3
"""Validate every path these audit scripts take from the command line.

SonarCloud flagged this folder on Security Rating for New Code: argv values
went straight into open(), shutil.rmtree() and subprocess.Popen(). The audit
is a local tool, but "local" is not a reason to let a typo in --out delete a
directory, and the fix is cheap.

Every path that will be WRITTEN, created or destroyed must go through
resolve_out(), which refuses a target outside the audit root. Paths that are
only READ go through resolve_in(), which requires the file to exist. An
executable goes through resolve_exe(), which requires a regular file that is
executable.

The audit root defaults to the folder containing this script's parent (the
swarm/tsan folder) and can be widened with FORGE_AUDIT_ROOT when the evidence
legitimately belongs elsewhere.
"""
import os
import stat
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent.parent


class UnsafePath(SystemExit):
    pass


def audit_roots():
    """Allowed roots: the audit folder, plus anything in FORGE_AUDIT_ROOT.

    A single path or an os.pathsep-separated list is accepted, because the
    build script works in a temporary directory outside the audit folder and
    still must not be handed an arbitrary path.
    """
    raw = os.environ.get("FORGE_AUDIT_ROOT")
    if not raw:
        return [DEFAULT_ROOT]
    roots = [Path(p).expanduser().resolve() for p in raw.split(os.pathsep) if p]
    return roots or [DEFAULT_ROOT]


def audit_root() -> Path:
    """The primary root, for messages."""
    return audit_roots()[0]


def _inside(target: Path, root: Path) -> bool:
    try:
        target.relative_to(root)
        return True
    except ValueError:
        return False


def _under_some_root(target: Path) -> bool:
    return any(_inside(target, r) for r in audit_roots())


def resolve_out(raw, what="output path") -> Path:
    """A path we will CREATE. Must stay inside an allowed root."""
    if not raw:
        raise UnsafePath("%s: empty" % what)
    target = Path(raw).expanduser().resolve()
    if not _under_some_root(target):
        raise UnsafePath("%s %r is outside the allowed roots %s "
                         "(set FORGE_AUDIT_ROOT to allow it)"
                         % (what, str(target), [str(r) for r in audit_roots()]))
    return target


def resolve_in(raw, what="input path") -> Path:
    """A path we will READ. Must exist and be a regular file."""
    if not raw:
        raise UnsafePath("%s: empty" % what)
    target = Path(raw).expanduser().resolve()
    if not target.is_file():
        raise UnsafePath("%s %r is not a regular file" % (what, str(target)))
    return target


def resolve_exe(raw, what="executable") -> Path:
    """An executable we will launch. Must be a regular, executable file."""
    if not raw:
        raise UnsafePath("%s: empty" % what)
    target = Path(raw).expanduser().resolve()
    if not target.is_file():
        raise UnsafePath("%s %r is not a regular file" % (what, str(target)))
    mode = target.stat().st_mode
    if not (mode & stat.S_IXUSR):
        raise UnsafePath("%s %r is not executable" % (what, str(target)))
    return target


def resolve_dir_in(raw, what="input directory") -> Path:
    """A directory we will READ/copy from. Must exist and be a directory."""
    if not raw:
        raise UnsafePath("%s: empty" % what)
    target = Path(raw).expanduser().resolve()
    if not target.is_dir():
        raise UnsafePath("%s %r is not a directory" % (what, str(target)))
    return target


def resolve_dir_out(raw, what="output directory") -> Path:
    """A directory we will create, empty, or copy into."""
    target = resolve_out(raw, what)
    if target.exists() and not target.is_dir():
        raise UnsafePath("%s %r exists and is not a directory" % (what, str(target)))
    # rmtree on "/" or a top-level dir would be catastrophic even if a caller
    # widened the root by accident.
    if target == target.anchor or len(target.parts) < 3:
        raise UnsafePath("%s %r is too shallow to delete" % (what, str(target)))
    return target


if __name__ == "__main__":
    # Self-test: every refusal and every acceptance is exercised, so a
    # checker that silently stopped checking would be visible.
    root = audit_root()
    ok = True

    def expect_refusal(fn, *a, **k):
        global ok
        try:
            fn(*a, **k)
        except UnsafePath:
            print("  refused as expected: %s%r" % (fn.__name__, a))
            return
        print("  *** DID NOT REFUSE: %s%r" % (fn.__name__, a))
        ok = False

    def expect_ok(fn, *a, **k):
        global ok
        try:
            r = fn(*a, **k)
            print("  allowed as expected: %s -> %s" % (fn.__name__, r))
        except UnsafePath as e:
            print("  *** WRONGLY REFUSED: %s (%s)" % (fn.__name__, e))
            ok = False

    expect_refusal(resolve_out, "/etc/evil.json")
    expect_refusal(resolve_out, "../../../evil.json")
    expect_refusal(resolve_out, "")
    expect_refusal(resolve_dir_out, "/")
    expect_refusal(resolve_dir_out, "/tmp")
    expect_refusal(resolve_exe, "/etc/hostname")
    expect_refusal(resolve_in, "/nonexistent/file")

    expect_ok(resolve_out, str(root / "evidence" / "x.json"))
    expect_ok(resolve_dir_out, str(root / "evidence" / "sub"))
    expect_ok(resolve_exe, sys.executable)
    expect_ok(resolve_in, __file__)

    print("PATHSAFE_SELFTEST_PASS" if ok else "PATHSAFE_SELFTEST_FAIL")
    sys.exit(0 if ok else 1)
