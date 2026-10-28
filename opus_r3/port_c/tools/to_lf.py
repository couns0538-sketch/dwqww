"""Convert CRLF line ends to LF in the given files (bytes level; prints what changed). usage: to_lf.py <file>..."""
import pathlib
import sys

CRLF = b"\r\n"
CR = b"\r"
for name in sys.argv[1:]:
    p = pathlib.Path(name)
    data = p.read_bytes()
    new = data.replace(CRLF, b"\n")
    if new != data:
        p.write_bytes(new)
        crlf = data.count(CRLF)
        lone = new.count(CR)
        print(f"LF: {name} ({crlf} CRLF), lone CR left: {lone}")
