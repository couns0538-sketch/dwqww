"""Shared path resolution for the aspiration audit scripts.

Every script used to hardcode `/tmp/asp/...`, which was where this audit ran and
nowhere else: a reader cloning the branch could not run any of it. Paths are now
derived from the script's own location, with environment overrides, so the
deliverable works from a clean checkout.

Two environment variables:

    ASP_BUILD_ROOT   directory holding the four `forge` binaries (default:
                     <this folder>/../builds). Nothing in `builds/` is committed:
                     they are build outputs, and the brief forbids binaries.
    ASP_EVIDENCE     where JSON evidence is written and read (default:
                     <this folder>/../evidence, which IS committed).

The four builds and the flags that produce them are documented in FINDINGS.md.
`ASP_BUILD_ROOT` deliberately has no `/tmp` default: a hardcoded world-writable
path is both non-portable and an insecure default for a file a script writes to.
"""
import os
import pathlib

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
AUDIT_ROOT = SCRIPTS_DIR.parent


def _dir_from_env(var, default):
    value = os.environ.get(var)
    return pathlib.Path(value) if value else default


BUILD_ROOT = _dir_from_env("ASP_BUILD_ROOT", AUDIT_ROOT / "builds")
EVIDENCE = _dir_from_env("ASP_EVIDENCE", AUDIT_ROOT / "evidence")

# build name -> the macro set that produces it. Kept beside the paths so a
# reader can see what each binary is without reading FINDINGS.md.
BUILD_FLAGS = {
    "stock": "-DFORGE_ASP_TRACE=0 -DFORGE_ASP_FAULT=0 -DFORGE_ASP_OFF=0",
    "trace": "-DFORGE_ASP_TRACE=1 -DFORGE_ASP_FAULT=0 -DFORGE_ASP_OFF=0",
    "fault": "-DFORGE_ASP_TRACE=1 -DFORGE_ASP_FAULT=1 -DFORGE_ASP_OFF=0",
    "noasp": "-DFORGE_ASP_TRACE=0 -DFORGE_ASP_FAULT=0 -DFORGE_ASP_OFF=1",
}


def binary(name):
    """Absolute path of one of the four audit builds, with a clear error."""
    if name not in BUILD_FLAGS:
        raise KeyError(f"unknown build {name!r}; known: {sorted(BUILD_FLAGS)}")
    path = BUILD_ROOT / name / "forge"
    if not path.is_file():
        raise SystemExit(
            f"build {name!r} not found at {path}.\n"
            f"Build it with:\n"
            f"  cmake -S <repo>/forge-combo29 -B {BUILD_ROOT / name} \\\n"
            f"    -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_BUILD_TYPE=Release \\\n"
            f"    -DFORGE_MARCH=x86-64-v4 -DCMAKE_CXX_FLAGS=\"{BUILD_FLAGS[name]}\"\n"
            f"  make -C {BUILD_ROOT / name} -j\n"
            f"or set ASP_BUILD_ROOT to where they already are.")
    return path


def evidence_file(name):
    """Path inside the evidence directory; the directory is created on write."""
    return EVIDENCE / name


def read_evidence(name):
    path = evidence_file(name)
    if not path.is_file():
        raise SystemExit(f"missing evidence {path}; run the producing script first")
    return path.read_text()


def write_evidence(name, text):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    evidence_file(name).write_text(text)
    return evidence_file(name)
