# Item1 — writable descriptors for chunk fsync

QA-reported Windows CRT Errno9 reproduced on Linux by enforcing the same access
rule on real regular-file descriptors. Before: one regression error. After:
one PASS with complete conversion, unchanged source and sealed-output verification.
The only production edit changes rb to r+b before fsync; no bytes are rewritten.
Windows runtime not available here; no PC command ran. IDEA_SOURCE: crew QA.
