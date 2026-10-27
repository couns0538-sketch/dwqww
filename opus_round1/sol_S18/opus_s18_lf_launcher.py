"""Run one of Sol's unchanged S18 tools on Windows with LF text output.

usage: python -B opus_s18_lf_launcher.py <tool.py> [tool args...]

Sol's filter writes its summary and manifest with Path.write_text(), and his describe tool writes its
histogram JSON with Path.open('x'); on Windows both translate "\n" to "\r\n". His pinned outputs were
written on Linux, so without this shim those files would differ by line endings only. The shim makes
Path.write_text() and text-mode writes through Path.open() default to newline="\n" (an explicit newline
argument is kept; reads and binary modes are unchanged) and then runs the tool as __main__.
The tool file itself is not modified.
"""
from __future__ import annotations

import pathlib
import runpy
import sys

_original_write_text = pathlib.Path.write_text
_original_open = pathlib.Path.open


def _write_text_lf(self, data, encoding=None, errors=None, newline=None):
    return _original_write_text(self, data, encoding=encoding, errors=errors, newline="\n" if newline is None else newline)


def _open_lf(self, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
    if newline is None and "b" not in mode and any(flag in mode for flag in "wxa+"):
        newline = "\n"
    return _original_open(self, mode, buffering, encoding, errors, newline)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    pathlib.Path.write_text = _write_text_lf
    pathlib.Path.open = _open_lf
    tool = sys.argv[1]
    sys.argv = sys.argv[1:]
    runpy.run_path(tool, run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
