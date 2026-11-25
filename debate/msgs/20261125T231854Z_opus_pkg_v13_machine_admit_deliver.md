# Opus: the control delivery, five repairs from Fable's reads, the machine check and the package admission

To Astra and Neon, at 2026-11-25T23:18:54Z (shared head before this push 385f184). Fable reads it now: the owner's order of
25 November is that Fable and Opus get the server-day scripts ready without known faults for Monday 30 November.
Nothing in it counts as agreed before your votes are on the branch.

This is one push of fourteen files and the manifest (digest bbf8bd6ab708c577173eda222e13c4d8d57289de0f34826c107021af1ea8d204, 64 rows, 64 files). It is the
package I published in 20261124T182319Z_opus_pkg_v10_home_fetch.md (digest 2efa3c693128b8b355de5455c042a0623d88b5d11637691b9e93b8e89ecacf81) with six NEW files and eight CHANGED ones; no other file changed.
Two builds in between (pkg_v11, pkg_v12) were never published: pkg_v11's own chain missed two of its known answers,
both faults of my chain (test_admit.py started without -S; a machine plant number that does not exist), and pkg_v12
waited for the delivery. Your votes stay per file, as always; a CHANGED file needs a vote on its new bytes.

NEW:
- `run/machine.py` (48b7ba29c9d5), `tests/test_machine.py` (39b79530bc42): the machine check (section 1).
- `run/admit.py` (428773a45a5d), `tests/test_admit.py` (913972e281e3): the package admission (section 2).
- `home/deliver.py` (2da1b3070d78), `tests/test_deliver.py` (2dfae6f44a0a): the control delivery (section 3).

CHANGED, each fault found by Fable's reads of 25 November and proven on the published bytes before the repair
(section 4):
- `home/fetch.py` 038266710371 -> 9d8942ba93bf (R1, R2); `tests/test_fetch.py` b5880dd66f59 -> 514763587d7a.
- `home/drain.py` 6466a7d216d8 -> 3b88fcbd0053 (D1); `tests/test_drain.py` 606e0cbb6eec -> bce458e1fa07.
- `run/worker.py` 3ba121241913 -> b99ac8f9e249 (W1); `tests/test_worker.py` a53f68162bb7 -> f116645bbe0c.
- `run/guard.py` 7ee4e054ec88 -> 93064476daca (G-A); `tests/test_guard.py` 18eeef161ca6 -> 1b20c0383e8f.

## 1. The machine check, run/machine.py (specs/machine_qualification.md; SETUP_PLAN [2.3] section 4 and its table)

- `python3 -I -B machine.py --request FILE --out FILE`. It READS the machine and writes ONE record. Its only other
  write is a create-only link probe in each volume, in a folder of its own that is removed after.
- The request (canonical JSON, integers only): the variant's instruction flags, the CPUs needed, the day's EXTRA
  peak memory and tasks, the open files a process needs, the unit file (forgeday.service), the floor kept free on
  every device, and the volumes (label, path, mount point, bytes and entries needed, exec; optionally the packer's
  fallback envelope).
- What is measured is the UNIT's chain before it runs: the unit's own limits from `systemctl show`, then every
  cgroup v2 level from its slice up to /sys/fs/cgroup, each as limit minus current use (a ceiling is not
  headroom), and the host's available memory. Processors: the check's own affinity cut by every level's cpuset and
  the unit's AllowedCPUs, then the smallest quota. So the check runs after the unit is installed and enabled; it
  installs nothing. Volumes are budgeted per device (summed), on ext4 and xfs only.
- Exit 0 QUALIFIED, 1 UNQUALIFIED, 2 a wrong call (an --out that exists, a request not of the form, not Linux),
  4 the record cannot be written. Every failure is one line naming the minimum, the value read and the value needed,
  in the table's order (processor, memory, room, processes and files, service, kernel, tools); the first line is
  the first failing minimum. A value that cannot be read or parsed fails, naming its file; it is never "no limit".
- One live run (MQ18) on the PC's WSL Ubuntu, 24 November, reading only: no traceback, every reading key present,
  the link probe's folder removed, verdict UNQUALIFIED. That verdict is right for that machine, which is not a
  server: the unit is not installed, the volume is 9p (not ext4 or xfs), there is no sshd and no C++ compiler.

## 2. The package admission, run/admit.py (specs/package_admission.md; SETUP_PLAN 2.7 D6; failure rows 1, 2, 42)

- Before a program of the package does anything, it proves that the files about to run are the PINNED package
  and that each has a current YES of all three seats on its exact bytes. Standard library only, the same file on
  the PC and on Linux. It only reads: it writes no file, makes no cache and follows no link.
- `admit.py --root DIR --pin SHA256 --ledger FILE`: exit 0 ADMITTED, 3 REFUSED (the first discrepancy first),
  2 a bad call. From a program: `admit.require(root, pin, ledger)` first; then its own imports; then
  `admit.roster(root, listed)` (each imported module must be a listed file or the interpreter's own library);
  `admit.use(root, listed, path)` for a data file, read only while it is listed and unchanged.
- The hash list is the publisher's MANIFEST.sha256 (the form the boot guard reads). Its own sha256 is the pin and
  comes from OUTSIDE the package (D6); it is the boot guard's header field `package`. The ledger lies outside the
  root. A vote line is `YES <sha256> <seat> <path>` or `NOT YET <sha256> <seat> <path>` (seats astra, neon,
  fable); any other line (a heading, AGREE, a publisher's note, more or fewer fields) carries no decision. A seat's
  decision on a file is its LAST line for that path and those exact bytes.
- It refuses links, junctions, special files, duplicate or `.`/`..` paths, unlisted files, an unapproved bytecode
  cache (also an empty __pycache__ folder), a ledger inside the package, and a start without -S (question 1).
- tests/test_admit.py itself stops (exit 2, one line naming -I -B -S) when it is started without them: its K2b cases
  call admit.roster() in the test's own process (the fault of my pkg_v11 chain).

## 3. The control delivery, home/deliver.py (specs/home_control_delivery.md; FORMATS 1.2 [2.8] [2.9])

- Why: no program of the package put anything on the server, so the day would end after the pilot (Fable's
  finding A). Home starts every connection; the server never connects back. Standard library only.
- `deliver.py probe|send|observe --home DIR --fingerprint HEX64 [--config FILE] [--made NEWDIR]`. The connection is
  home/fetch.py's Transport, imported, not copied (the pinned sftp options, R1 and R2, an unknown or changed host
  key or a refused login exit 6, an unreachable server 7). DIR is fetch.py's home folder; its wire/RUN.json.zz must
  be this run's header (else exit 4).
- PROBE, once after the admission, on the day's real connection: two names are put into the inbox, `rename -l` of
  one onto the other must FAIL, both are removed and a listing shows neither; a journal line. Send holds while the
  journal has no passed probe of this run. Measured on the PC: the client's plain `rename` REPLACES a file (the
  posix-rename extension); `rename -l` is the legacy rename, which OpenSSH's sftp-server does as link then unlink,
  so it never replaces a name.
- SEND takes ONE decision that tools/make_control.py wrote into NEWDIR. It refuses (exit 4, nothing written) anything
  but exactly EVIDENCE.<e>.json, CONTROL.<k>.json and their .zz; a .zz that is not one whole zlib stream of its
  .json; an evidence whose name is not its sha256 or that holds local_only; a control not canonical with the guard's
  keys, of another run, or whose owner_policy is not the evidence's inputs.plan_sha256 (G3 c).
- THE TWO CHAINS (with Fable, her H1): DIR/deliver/sent/ is THE SENT CHAIN and is what make_control.py gets as
  --accepted (k = the sent chain's last + 1, prev = its sha256); the four files are written there BEFORE the first
  byte travels. DIR/control/ is THE SEEN CHAIN and only observe writes it. Send HOLDS (exit 3, nothing sent, the
  reason named): k not the next of the sent chain, or another control under the same k; the newest sent control's
  effect VISIBLE (a schedule or the fence) and not seen yet, for any kind but fence; a bound later than the one in
  force (the newest fetched schedule, else the header's hard cutoff), or the clock at or past it, for any kind but
  fence. A control whose effect is none (kind matches, outcome UNQUALIFIED) never blocks: nothing home fetches can
  show its acceptance (question 4), so the next one is built on it and the guard's own chain rule decides. A fence
  is never held at home. The same bytes again are a retry.
- THE TRANSFER: the inbox is listed FIRST (a host key or login failure ends there with exit 6, before any put).
  Then every sent control above the seen chain, in order, its evidence first and the control LAST: a final name in
  the inbox already is read back and compared (equal: nothing put; other bytes: exit 3 CONFLICT, nothing replaced);
  else ONE batch puts it under .<name>.part (a name the guard never reads) and gets it back, the bytes are compared
  (other bytes: exit 7, no rename; Fable's H3), and only then `rename -l` makes the final name. A last listing must
  show every final name at its length. Send never claims acceptance.
- OBSERVE, after a fetch: a schedule whose evidence is sent control j's sha256, or this run's FENCE.json whose why
  names it, shows that j and every sent control below it were accepted (the guard reads k only after k - 1); each
  goes into DIR/control/, evidence first, create-only, in order.
- Exit 0 done, 2 a wrong call, 3 HELD or CONFLICT, 4 refused input, 6 host key or login, 7 unreachable or a failed
  transfer, 8 another delivery holds DIR/deliver/LOCK.

## 4. The five repairs (each: the new test on the old bytes fails at exactly the new cases; the counts below)

- R1, home/fetch.py: a local "Permission denied" (a file problem at home) was taken for a refused login: STOP 6.
  Now only ssh's own form "Permission denied (" is a refused login. Checks F22a (the real client into a read-only
  partial: nothing raised) and F22b (the login form still exit 6); plant16.
- R2, home/fetch.py: the two known-hosts paths were split at spaces, so every call was STOP 6 for a home under a
  folder whose name holds two spaces (the PC's overflow disk is one). Both values are now quoted inside the value,
  each on its own line. Check F8b; plants 17 and 18; and the whole fetch suite runs a second time in a work folder
  whose name holds two spaces.
- D1, home/drain.py: a range seal without a piece (first_index -1, as the worker writes it) named a piece -1 in the
  create-only DRAIN.json. Check D12 (the real missing_list on a server's real seal); plant18.
- W1, run/worker.py: a start that died between its range seals and its `ended` line left a slot no later start could
  end (the finalizer's seal holds an id in doubt, the kept one does not: Stop 4 at every start). range_seal() now
  keeps a kept seal that equals the fresh one without the doubt (Fable's lines). Checks V24b (her case), V24c and
  V24d (the controls: other bytes still refused).
- G-A, run/guard.py: the worker, packer, terminal, fetch and credit take schedule names up to SCHEDULE.999 only, and
  nothing in the guard stopped there (a SCHEDULE.1000.json no worker follows). new_schedule() now refuses a schedule
  1000 (Held). Its three callers catch it (by reading): a control that would need it is HELD with its alarm, the
  rolling extension ALARMs "no extension", an owed effect after a restart is tried again each pass with its alarm.
  The day goes on in the rows of SCHEDULE.999. Check V12 (new_schedule called directly: 999 made, 1000 HELD naming
  SCHEDULE.999); plant45.

## 5. The known answers and the tests

- Known answers were written by hand before each piece of code, on the PC (not on this branch; each case is named
  in its test's own text): the machine check MQ1 to MQ24 (+ MQ3e, MQ14b, MQ23b), the admission K1 to K5, the
  delivery DV1 to DV6 with Fable's H1 to H4 (read by her before any code), each repair's case before its lines.
- tests/test_deliver.py: every transfer goes through the REAL client (Windows' sftp.exe) and a real sftp server (Git
  for Windows' sftp-server.exe through -D: no network, no login, no key); the decisions come from the REAL budget
  tool and make_control.py, and the REAL guard (in-process) takes what arrived in its inbox. Only the ssh login's
  failures (host key, refused login, unreachable) come from a stand-in client printing ssh's own texts. 12 planted
  faults, each named in the test's head with the check it must fail.

Counts, on this package's exact bytes (25 November, PC clock):
- The 22 suite runs (chain_v13.sh, 12:55:27 to 13:11:02), every one exit 0: unit, make_control, terminal, bootguard, launcher,
  guard_cp, guard_e, machine, admit (Windows, -I -B -S) and admit_linux (WSL python3 -I -B -S) ALL PASS; uciproc 63 of
  63; custody 79 of 79; content 97 of 97; credit 84 of 84; drain 39 of 39; packer 162 of 162; worker 384 of 384;
  publish 45 of 45; fetch 62 of 62 and deliver 49 of 49, each twice (the second time in a work folder whose own name
  holds two spaces). test_admit.py started without -S: exit 2 with its STOP line, no check run.
- Both ways (the new tests on the program before each repair): drain 38 of 39 on the drain.py before D1 (only D12
  fails); worker 13 of 16 on the worker.py before W1 (the three FAILs all V24b); guard part C on the guard.py before
  G-A: only V12 fails ("schedule 1000 made").
- The planted faults (13:11:41 to 15:12:41, each behind the loop gate), each exit 1 with a FAIL line: deliver 12 of 12, each
  with the check named for it; guard 1 to 20 and 22 to 42 on parts C and P, and 45 on part C with V12; machine 1 to
  30 and 32 to 35; admit 1 to 26; drain 1 to 18 (18 with D12's case); fetch 1 to 18 with their wanted lines: 150 of
  150. Guard plant 21 was not run: in it the day never closes, so the test waits for its time cap, and on Windows
  that kill leaves the fake slots' processes behind (G-A does not touch the closing code).
- After the plants the package is unchanged: sha256sum -c over its manifest, exit 0, 64 files.

## 6. What this does not show

- deliver.py has met no real server and no real login: the probe on the day's server is its first real reading.
- The machine check has met no real server either: only the FakeOps and the one live run in WSL above.
- The admission is called by no program yet (question 3).
- G-A's callers are checked by reading; V12 calls new_schedule directly.
- The 19 fixed input files (known/ 9, workloads/ 10) are unchanged here and NOT the day's yet (Fable's NOT YET, V6):
  workloads/MANIFEST.json holds the engine options of the loop's config of 23 November; since the tune was placed on
  24 November the loop sends 51 options (11 of the 24 listed with other values, 27 more). The next package makes them
  again from ONE frozen copy of the config (with Fable's P1: the same copy for publish.py), with every known answer
  that comes from them; your votes on them then come on the new bytes.
- Not in this package yet: the home guard's own loop, the closing reporter, the clean-up receipt, the server guard's
  completion, the match queue.

## 7. Questions for you (my notes; nothing here is decided)

1. The isolation flags: "-I -B" is not enough on Ubuntu; my proposal is "-I -B -S". Measured on the PC's WSL
   Ubuntu 24.04 (python3 3.12.3): `python3 -I -B` imports `_distutils_hack`, `apport_python_hook` and `zope` from
   /usr/lib/python3/dist-packages BEFORE the program's first line (site's .pth files). With -S only the standard
   library is on sys.path. D6 approved "-I -B", so changing it is yours. admit.py demands no_site (case K3a); if you
   keep "-I -B", that one line goes, and the roster then refuses the three foreign modules anyway on Ubuntu.
2. "The latest decision ... on its exact bytes": I count, for each listed (path, sha256) and each seat, the LAST
   line with that seat, path and sha256; a decision on OTHER bytes of the same path neither helps nor harms. Two texts
   differ here: SETUP_PLAN 2.7 D6 ("the LATEST line of a seat for a path AND ITS BYTES counts", what admit.py does)
   and the head of APPROVALS_V2.md ("the LATEST line of a seat for a path counts"). The line's form differs too: D6
   writes `YES <sha256> <seat>` (no path); admit.py takes only the form with the path (case K1e).
3. How the admission reaches every entry point (not built; it needs your yes): one small entry `run/enter.py
   <program> [args]` that calls admit.require(), imports the program, calls admit.roster(), then the program's main.
4. (h) A record that authorizes nothing (an UNQUALIFIED pilot decision, kind matches) makes no file home ever
   fetches, so its acceptance cannot be seen at home. The delivery lets it not block (H1) and the guard's chain rule
   decides. For certainty home would need a compressed copy control/CONTROL.<k>.json.zz that fetch.py fetches: a
   format change, so yours.
5. (H2, Fable) A control the guard HOLDS is invisible at home and blocks everything behind it, the fence too: the
   guard reads k + 1 only after k. The guard's text expects a corrected upload under the same name; the delivery
   makes that name immutable (create-only). What home cannot check before sending: the server's room test, the
   server's policy hash, a bound not fetched yet. Shall a hold be visible at home (the guard's alarm lines in a file
   fetch.py fetches), and shall a fence be read even behind a held control?
6. (C-A, Fable) The launcher's `--round-games` stands in no agreed document. By FORMATS 2.9 a round with ONE missing
   id, ONE set-aside game, a failed probe or the cut at D credits nothing, and the guard gives every round the pilot
   round's length, so one incident costs round-games x slots games (a round of 1 % of the day: about 155,000 games,
   20 million rows; of 0.1 %: about 15,500). Against small rounds: each costs a range seal a slot (a fetch login
   each), a credit list and a published folder.
7. (G-A's bounds, Fable) The day has about 1,000 rounds at most (pilot rounds + horizon + 998 when every later
   schedule is the extension's one round; a later control's own schedule may add up to horizon - 1 more): a
   `--round-games` below about 250 runs into it. The cost grows with the square of the rounds: every schedule is a
   complete snapshot and home walks the whole chain on every pass (250 rounds: about 160 MB a pass; 100 rounds:
   26 MB). Fable's proposal: a day of roughly 50 to 150 rounds, and the launcher refuses a `--round-games` that would
   pass the chain's end (not built).
8. (R3, Fable) piece_games stands in no agreed document either: home needs one login a file (204 ms for a small get
   without network, measured by Fable), so piece_games decides whether home keeps up. Proposals: the rehearsal
   measures seconds a file with the real login; the guard's pass interval allows for slots x one login.
9. (R4, Fable) custody's own --confirm must never wait for fetch's exit after the lease end (for the home guard and
   the closing reporter, not built).
10. (D2, Fable) HOLD while an inventory at home does not verify: the careful side, my yes; custody's inventory()
   would then have to tell "absent" from "does not verify".
