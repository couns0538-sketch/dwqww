"""Rebuild the ordered L27 byte stream from both original opening files."""
from hashlib import sha256
from pathlib import Path
import sys
o,book,L=(Path(k).read_bytes() for k in sys.argv[1:4])
def key(line):
    return b' '.join(line.split()[:4])
rows=[key(x) for x in o.splitlines()];seen=set(rows);dropped=[]
for n,row in enumerate(book.splitlines(),1):
    k=key(row)
    if k in seen:
        dropped.append(n)
    else:
        rows.append(k);seen.add(k)
reconstructed=b''.join(x+b' 0 1\n' for x in rows)
assert reconstructed==L
print('O',len(o.splitlines()),sha256(o).hexdigest())
print('Job 24 book',len(book.splitlines()),sha256(book).hexdigest())
print('Excluded book source lines',dropped)
print('L27',len(rows),len(L),sha256(L).hexdigest(),'byte-identical after independently constructing O then book')
