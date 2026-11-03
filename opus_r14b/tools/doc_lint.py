#!/usr/bin/env python3
"""doc_lint.py - Opus R14-B: catch the text-file mistakes this job made or nearly shipped (own code, stdlib only).

usage: python -I -B doc_lint.py PATH... [--include-logs] [--quiet]
Walks the paths (files or folders; .git, __pycache__ and, unless --include-logs, logs/ folders are skipped) and checks
every text file (.md .py .sh .ps1 .txt .json .yml .cpp .h .hpp .tsv .sha256 .patch):
  control   control bytes other than TAB / LF, or a CR that is not part of CRLF (a bash heredoc with inline Python
            turns \\r \\b \\f in Windows paths into such bytes)
  crlf      CRLF line endings in a file type that .gitattributes keeps LF (.sh .py .ps1 .cpp .md .yml .tsv .sha256)
  utf8      not UTF-8, a U+FFFD replacement character (mojibake), or a BOM in front of a .sh / .py (breaks #!)
  drive     a drive letter glued to a name, e.g. C:o14bpgo2 (the backslashes were eaten on the way) (doc_lint: ignore)
  conflict  a leftover merge marker (<<<<<<< / >>>>>>> at the start of a line)
  table     a GitHub table row with more cells than its header (GitHub drops the extra cells; a | inside `code`
            still splits a cell unless written \\|) - fewer cells is reported too (GitHub pads them)
  link      a relative Markdown link [x](path) whose target does not exist
A line that contains "doc_lint: ignore" is skipped by the drive, utf8 (U+FFFD) and link checks.
Prints file:line: [check] message; exit 0 clean, 1 findings, 2 bad arguments. Hashes are checked by hash_sweep.py.
"""
import os
import re
import sys

TEXT = {".md", ".py", ".sh", ".ps1", ".txt", ".json", ".yml", ".yaml", ".cpp", ".h", ".hpp", ".tsv", ".sha256",
        ".patch"}
LF_ONLY = {".sh", ".py", ".ps1", ".cpp", ".md", ".yml", ".tsv", ".sha256"}
CRLF = b"\r\n"
DRIVE = re.compile(r"(?<![A-Za-z0-9_$%:])[A-Z]:(?=[A-Za-z0-9_]{3,})(?=[A-Z_]*[a-z0-9])(?!\w+://)")
DELIM = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")


def cells(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return len(re.split(r"(?<!\\)\|", s))


def line_of(raw, pos):
    return raw.count(b"\n", 0, max(pos, 0)) + 1


def lint_file(path, out):
    ext = os.path.splitext(path)[1].lower()
    shown = path.replace(os.sep, "/")
    with open(path, "rb") as fh:
        raw = fh.read()
    n0 = len(out)
    bad_ctrl = sorted({c for c in raw if c < 32 and c not in (9, 10, 13)})
    n_cr, n_crlf = raw.count(b"\r"), raw.count(b"\r\n")
    if bad_ctrl or n_cr != n_crlf:
        first = next((i for i, c in enumerate(raw) if c in bad_ctrl), raw.find(b"\r"))
        lone = " + lone CR" if n_cr != n_crlf else ""
        out.append(f"{shown}:{line_of(raw, first)}: [control] bytes {[hex(c) for c in bad_ctrl]}{lone}")
    if ext in LF_ONLY and n_crlf:
        out.append(f"{shown}:{line_of(raw, raw.find(CRLF))}: [crlf] {n_crlf} CRLF line endings in a file kept LF")
    if raw.startswith(b"\xef\xbb\xbf") and ext in (".sh", ".py"):
        out.append(f"{shown}:1: [utf8] BOM in front of a {ext} file")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        out.append(f"{shown}:{line_of(raw, e.start)}: [utf8] not UTF-8 ({e.reason})")
        return len(out) - n0
    lines = text.split("\n")
    in_fence = False
    for i, ln in enumerate(lines, 1):
        if ln.startswith(("<<<<<<< ", ">>>>>>> ")):
            out.append(f"{shown}:{i}: [conflict] merge marker")
        if ext == ".md" and ln.lstrip().startswith("```"):
            in_fence = not in_fence
        if "doc_lint: ignore" in ln:
            continue
        if chr(0xFFFD) in ln:
            out.append(f"{shown}:{i}: [utf8] replacement character U+FFFD")
        if ext in (".md", ".py", ".sh", ".ps1", ".txt"):
            for m in DRIVE.finditer(ln):
                out.append(f"{shown}:{i}: [drive] '{ln[m.start():m.start() + 24]}' - path separator missing?")
        if ext == ".md" and not in_fence:
            for m in LINK.finditer(ln):
                target = m.group(1).split("#")[0]
                if target and not re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) and not target.startswith("/"):
                    if not os.path.exists(os.path.join(os.path.dirname(path), target)):
                        out.append(f"{shown}:{i}: [link] {m.group(1)} does not exist")
    if ext == ".md":
        in_fence = False
        for i in range(len(lines) - 1):
            if lines[i].lstrip().startswith("```"):
                in_fence = not in_fence
            if in_fence or "|" not in lines[i] or not DELIM.match(lines[i + 1]) or "|" not in lines[i + 1]:
                continue
            want = cells(lines[i])
            if cells(lines[i + 1]) != want:
                out.append(f"{shown}:{i + 2}: [table] delimiter row has {cells(lines[i + 1])} cells, header {want}")
            j = i + 2
            while j < len(lines) and lines[j].strip() and "|" in lines[j]:
                got = cells(lines[j])
                if got != want:
                    what = "dropped by GitHub" if got > want else "padded by GitHub"
                    hint = "; escape | as \\|" if got > want else ""
                    out.append(f"{shown}:{j + 1}: [table] {got} cells, header {want} ({what}{hint})")
                j += 1
    return len(out) - n0


def main(argv):
    include_logs = "--include-logs" in argv
    quiet = "--quiet" in argv
    paths = [a for a in argv if not a.startswith("--")]
    unknown = [a for a in argv if a.startswith("--") and a not in ("--include-logs", "--quiet")]
    if not paths or unknown:
        print(__doc__, file=sys.stderr)
        return 2
    out, files = [], 0
    for root in paths:
        if not os.path.exists(root):
            print(f"doc_lint: {root} does not exist", file=sys.stderr)
            return 2
        walk = [(os.path.dirname(root), [], [os.path.basename(root)])] if os.path.isfile(root) else os.walk(root)
        for d, subdirs, names in walk:
            subdirs[:] = [s for s in subdirs if s not in (".git", "__pycache__") and (include_logs or s != "logs")]
            for name in sorted(names):
                if os.path.splitext(name)[1].lower() in TEXT:
                    files += 1
                    lint_file(os.path.join(d, name), out)
    for line in out:
        print(line)
    if not quiet or out:
        print(f"doc_lint: {files} files, {len(out)} findings")
    return 1 if out else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
