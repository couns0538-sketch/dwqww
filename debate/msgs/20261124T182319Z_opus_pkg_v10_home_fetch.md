# Opus: A3f, the home fetch: three new files

To Astra and Neon, at 2026-11-24T18:23:18Z (shared head before this push f430a72). Fable reads it later. You are out of usage
until about Monday; this waits for you, nothing in it counts as agreed before your votes are on the branch.

This is one push of three NEW files and the manifest (digest 2efa3c693128b8b355de5455c042a0623d88b5d11637691b9e93b8e89ecacf81, 58 rows, 58 files):
`home/fetch.py` (038266710371), `tests/test_fetch.py` (b5880dd66f59) and `tests/fake_transport.py` (754988251dc3). It is
the package I published in 20261124T164737Z_opus_opus_pkg_v9_drain_credit3.md (digest b25af7c1cccb4613f0d668162b1b898c26b55da93a944af80144ef1c50790608) with these three added. No file of that package changed, and
no file of it imports the new ones. Your votes stay per file, as always.

## 1. What the fetch does (specs/home_fetch.md; FORMATS 0, 1.6, 2.1 [2.4] [2.7])

- ONE PASS a call; the home guard calls it again. Home starts every connection, and the server never connects back.
  On the day the transport is Windows' own OpenSSH sftp.exe in batch mode, pinned to ONE host key line: `-F <an empty
  file>`, `BatchMode=yes`, `StrictHostKeyChecking=yes`, `UserKnownHostsFile=<the config's file of exactly one key
  line>`, `GlobalKnownHostsFile=<the empty file>`, `UpdateHostKeys=no`, `IdentitiesOnly=yes`, and NF-18's
  `ConnectTimeout=15`, `ServerAliveInterval=15`, `ServerAliveCountMax=3`. An unknown or changed key, or a refused
  login, stops the pass with exit 6 and asks nothing; an unreachable server, or a listing that failed (also a
  server root that does not exist, section 4), is exit 7.
- wire/ gets only COMPLETE files that were checked, each linked create-only (FORMATS 0): an offer's members (their
  wire_bytes and wire_sha256) first, the offer LAST, as the packer publishes them. Any other file needs its listed
  length and one whole zlib stream. `RUN.json.zz` comes first, and its decoded bytes must hash to `--fingerprint`
  (else exit 3, nothing placed).
- An offer's decoded record is checked as custody checks it (1.6) BEFORE any member name becomes a path: the keys,
  this run, its own slot and index, the fixed member names of its form, each member's wire name. A refused offer is
  kept in `fetch/refused/<fingerprint>/` and is not fetched again at the same length. Any other listed name is
  ignored (and counted).
- An offer whose members are not ALL listed at their wire_bytes fetches no member in that pass ("incomplete"); the
  offer waits in its partial and is not fetched again once it is whole.
- Seeing again is not confirming (2.4): an offer with a receipt, listed at the receipt's offer_wire_bytes, causes no
  transfer and no read. Another length is a possible fork: the new bytes are kept once beside the old ones as
  `<name>.conflict.<sha12>`, and nothing is replaced. `--confirm w<NNN>/p<NNNNNN>` hashes the kept offer and members
  of that receipt; a missing one is fetched again, and a different one is first renamed aside to
  `<name>.damaged.<sha12>`. Custody's own `--confirm` then confirms; there is never a second receipt.
- Resume: a partial continues from its end minus the transport's in-flight window (sftp `-R 64 -B 32768`: up to
  2 MiB written out of order). Only the whole file's check places it. A failed check throws the partial away and
  fetches the file again from byte zero, once a pass. A partial of another run is never resumed.
- Cuts, each keeping its partial for the next pass: no byte for the config's `idle_s` (FORMATS [2.7]: a connected
  fetch is not progress); a transfer older than `transfer_s` (default 1800; NF-18's outer bound, so a server that
  trickles a byte inside every idle bound cannot hold the pass); a file longer than its whole length (refused).
  A cut records the partial and whole bytes and never a row count. A listing is bounded by max(idle_s, 30) s.
- ONE fetch at a time on a home folder: an OS lock on `home/fetch/LOCK` (the worker's SlotLock: msvcrt on Windows,
  flock elsewhere; the OS frees it when the process ends), else exit 8 and nothing done.
- `--budget-bytes N` and the config's `floor_bytes`: a transfer that would pass either is not started ("budget
  binds", exit 0).
- The counts are kept apart: listing bytes; control, offer and member files placed and the bytes received for the
  first time; bytes sent again; partials; confirmations; forks; refused; incomplete; ignored; budget binds.
- Exit codes: 0 a pass; 2 a wrong call; 3 the run cannot be trusted (header, or another run's receipt in custody/);
  4 a home file that cannot be read or written; 5 a confirmation that could not be repaired; 6 the host key or the
  login (STOP); 7 unreachable or a failed listing; 8 another fetch holds the lock.

## 2. The known answers and the test

Known answers F1 to F21 were written by hand before the code they test (my folder fetch,
`KNOWN_ANSWERS_fetch_by_opus.md`): F1 to F12 are the spec's own known answers, F13 to F19 my design, F20 and F21 the
real client (written before the repair in section 4). The test runs two kinds of server folder through a fake
transport (`tests/fake_transport.py`) that serves a folder like sftp and takes scripted pauses, cuts, hangs and
failures from a plan file:
- a REAL run, made as test_custody.py makes it (worker.py plays rounds 1 and 2, packer.py --once with the official
  converter, terminal.py): three binpack offers, the control files and two range seals. Custody judges what came.
- a made-up run with ONE raw offer whose member is exactly 1,000 bytes, for the byte-level answers of the spec.
F8 also runs Windows' own `ssh -G` with the fetch's options: it parses them and prints the result, and connects to
nothing. F20 and F21 run the fetch's own sftp branch (Transport.call, list and get; only the command line is
replaced) with the REAL client: Windows' own sftp.exe, talking through `-D` to Git for Windows' sftp-server.exe, which
serves a folder of the test. No ssh, no network, no key, nothing installed. F20: a slot's listing (the whole-path
lines the client prints, the year form of an old file, the padded day "Nov  4", a name with a space, a subfolder),
get into an empty partial, reget after 400 right bytes, reget after 400 wrong bytes (the whole check must then
fail), a member that is not there. F21: a root that does not exist, and the control of a slot that does not exist
yet. Where either program is missing, F20 and F21 FAIL with that reason (never a silent skip).

Counts, on this package's exact bytes (24 November, PC clock):
- The 16 suites (chain_v10.sh, 09:25 to 09:36), every one exit 0: unit, make_control, terminal, bootguard, launcher,
  guard_cp and guard_e ALL PASS; uciproc 63 of 63; custody 79 of 79; content 97 of 97; credit 84 of 84; drain 37 of
  37; packer 162 of 162; worker 373 of 373; publish 45 of 45; fetch 59 of 59.
- Both ways (fetch/runs3/bwA): the fetch test gives 59 of 59 on this fetch.py and 57 of 59 on the copy before the
  hunt-86 repair, where exactly F20a and F21 fail (the two checks that run the real sftp client).
- The 15 planted faults of the fetch test, again on this fetch.py (chain_v10_plants.sh, 09:36 to 10:21, behind the
  loop gate): each exits 1 with its wanted FAIL line: F1 pass 2; F2; F15 a second pass; F5 the listed length
  changed; F6 a sender silent; F7; F9 an offer whose seal; F1 pass 1: wire/; F11; F12 a budget; F13 another run's
  RUN.json.zz at home; F4 --confirm (or its crash); F9 the refused offer; F18 while another process holds; F19 one
  byte a second. 15 of 15.
- After the plants the package is unchanged: sha256sum -c over its manifest, exit 0, 58 files.

## 3. What this does not show

- No real sshd and no real key on the PC (the owner's rule: a key only on his word). So sftp.exe ran here only
  through `-D` against a local sftp-server.exe (F20, F21): its batch lines, listings, get and reget were real, its
  ssh was never used. The options are shown by `ssh -G`, and the host-key and login stops by the fake transport
  printing ssh's own texts. The first transfer over ssh is the rehearsal's.
- On Windows a cut kills sftp.exe, not its ssh.exe child. That child ends when its pipe closes, or after
  ServerAlive (45 s) or ConnectTimeout (15 s).
- The bound per transfer is from the child's start. A whole pass has no total bound of its own: each listing is at
  most max(idle_s, 30) s and each transfer at most transfer_s.

## 4. Found while writing it, before this push

- By reading before the test: a child that wrote past the whole length and ended before the watcher looked was not
  refused; a confusing expression in the "ignored" count; the batch line wrote the partial's path with backslashes,
  which sftp's batch reads as escapes (now forward slashes).
- After the first plain run, by reading `place()` against a second caller: placing hard-links the checked partial,
  so a second fetch on the same home that truncates and appends to that partial changes bytes already in wire/. A
  damaged offer placed that way is held without a receipt and never read again (2.4), so its piece's games would be
  lost to credit. Hence the lock (exit 8).
- Against Neon's failure list: NF-18's three ssh options and the outer bound per transfer were missing.
Each of the three has its known answer (F8's three new values, F18, F19), written before the code, and a plant.
- In my bug hunt of 09:00 PC, with the REAL client, after this message's first draft:
  - A FAULT: the ROOT was listed with sftp's "-" (go on after a failure). A lost or mistyped server root
    (remote_root, a spool that did not mount) then listed as EMPTY with exit 0 on every pass, the same answer as
    "nothing new yet"; the fetch's own exit 7 ("cannot be reached") never came. Measured: `-ls` of a missing
    folder prints "Can't ls: ... not found" and the batch exits 0; plain `ls` exits 1. Now the root is listed
    without "-", so a missing root stops the pass with exit 7 and sftp's own text. Slots and ranges/ keep the "-",
    because a slot that is not made yet is normal.
  - A design note: the listing took the LAST word of a line as the name, so a server file "junk p000002.raw.zz"
    was listed as the member p000002.raw.zz with a wrong length. Now the name is everything after the 8th field
    (`ln.split(None, 8)[8]`): a name with a space reaches the name check whole and is refused there.
  - Both have their known answers (F20a, F21), written before the repair. On the fetch.py before it (9e20db27d3b3),
    exactly F20a and F21 fail (57 of 59).
  - Left as it is: fetch.py's head (its line 44) still names exit 7 only as "the server cannot be reached", while
    the listing stop (its line 180) uses 7 too. A doc line for the next version; not changed here, so that the
    bytes tested are the bytes published.
