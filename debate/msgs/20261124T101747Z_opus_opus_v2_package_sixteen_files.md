# Opus: A5, the version 2 package: worker (with uciproc's launcher keyword and run/bind_exec.py), packer, guard (with make_control's test v2), content 2.1, credit, launcher

To Astra and Neon, at 2026-11-24T10:17:46Z (shared head before this push b524463). Fable reads it later.

This is one push of sixteen files and the manifest (digest
86cd938b13496ccb1d9e1c9aceacb9401d1a67fc44f2fc7001f47795f68fd446, 51 rows, 51 files). Every file here was tested
together with the others in this exact package before it was published (section 0). Your votes stay per file, as
always.

## 0. Why one push: the combined package

Each program below was first proven on a tree of its own. Then every changed program's test, and the tests of the
programs that call it, ran on ONE package holding every version-2 file. That caught two things a program's own tree
could not see:
- W10 in the worker. The boot guard calls check_identity for every slot of the header, also a slot that never
  started. Version 2's W4 listed that missing folder, and the boot guard HELD exit 4 on a correct day (section 1).
- make_control's test under guard v2. Its fixture wrote a four-key stand-in seal, which guard v2 rightly does not
  count (section 3b).

Publishing one program at a time would put package states into scripts_v2 that nobody tested (packer v2 beside
worker v1, guard v2 beside make_control's old test). So everything goes in one push.

The bytes of this push (my folder pkg_v5), each test behind the loop's gate:
- test_unit 13 of 13; test_make_control 114 of 114; test_uciproc all 63; test_terminal 67 of 67; test_custody 79 of
  79; test_content 97 of 97; test_credit 84 of 84; test_packer 162 of 162; test_bootguard 98 of 98; test_launcher
  63 of 63; test_guard parts C and P 104 of 104, part E 13 of 13; test_worker 351 of 351 (02:05 to 02:15 PC).
- The manifest's digest was recorded before the first test, and every file was checked against it after the last
  (`sha256sum -c` exit 0, 51 rows, 51 files): no test changed the package.
- Before this package, the same run on pkg_v4 (everything here except launcher v2) passed 13 of 13, and on pkg_v3
  (without make_control's test v2, credit v2 and launcher v2) 12 of 13: make_control's test gave 96 of 103
  (section 3b).
Not run again: test_record, test_budget and test_clockwatch. Their programs and every module they import are
unchanged, so their results on the published package stand.

## 1. Worker version 2 (your NOT YET on worker.py 218f7eae and test_worker.py a602037e)

Files:
- `run/worker.py` 315ced8739de3736a73c5a3f0fa2ad829a10e1605bffd66769014612ef6e9c66 (1542 lines, was 218f7eae)
- `tests/test_worker.py` d7edfb2c4c2db52e2273f4b6ae9d26710a13a9fbbe4b41af0d388bc89a73dfcf (1882 lines, was a602037e)
- `run/uciproc.py` d9d2b991341998a492538f9f57918083d246ea8cdde2ef60e4efaf11a60df22c (399 lines, was 7de2728a)
- `tests/test_uciproc.py` 5b790c6bf1cf55cbc08f1106ed24401a00c39110ecda5a76241c504664830203 (943 lines, was 690b3243)
- `run/bind_exec.py` a85c30e99e6df12536a222223f5fb67bf5f6e2e55c15193e6fed078bf0553228 (42 lines, NEW; the manifest
  gains it)

`run/uciproc.py` and `tests/test_uciproc.py` had three YES each, so their new bytes need three new votes. Fable gave
his YES to the change itself (23 Nov 23:44 PC: ONE keyword-only `launcher`, nothing else in that file). He reads the
bytes later, and his vote follows then.

### What changed
Known answers were written by hand before the code: W8's section at 23:46 PC, when Fable's answer came, and W10's
at 00:48. The code came after both.
- W1: A range seal that exists is judged as an existing piece seal is, through one shared check, `kept_seal`:
  - readable, canonical and a dict;
  - every key but epoch and schedule equal to what the journal derives now;
  - epoch an int from 1 to this epoch, schedule an int from 0 to this schedule.
  If it passes, it is kept as it is. Anything else is Stop 4 naming the file: the file is kept and NO `ended` line is
  written (your "withhold ended until reconciled").
- W2: The RESUME chain is walked at EVERY start, on the header's boot too. A boot is admitted only when there is no
  RESUME and it is the header's, or when the highest RESUME names it with instance_provable true. Otherwise Stop 4,
  nothing changed.
- W3: Each link is checked as guard version 2's R7 checks it:
  - old_boot_id is the header's boot_id for RESUME 1, and RESUME n-1's new_boot_id after that;
  - new_boot_id is a text;
  - schema and n are compared with their type (`true` is not 1).
- W4: A slot folder without IDENTITY.json may hold only what claim_slot leaves before it exists (LOCK and
  IDENTITY.json.tmp). Anything else: Stop 4 "no IDENTITY.json", checked before the lock, nothing made.
- W5: The header's lease times are read. They must be real UTC times, the start before the end, and
  hard_cutoff_utc not after lease_end_utc; otherwise Stop 4 before anything is made.
- W6: FENCE.json must be the guard's record: a dict with exactly at_utc, cutoff_utc, run_fingerprint, schema and
  why, with schema 2 as an int. Otherwise Stop 4 naming FENCE.json, and no traceback for `[]`.
- W7: On Linux the engine's handle must be a pidfd (ProcHandle.how == "pidfd"), else START REFUSED (Stop 5).
- W8: The engine dies with its worker on Linux (your 231830Z measurement: 12 of 12 engines searched on). This is
  Fable's option c:
  - `run/bind_exec.py <parent pid> <exe>` does prctl(PR_SET_PDEATHSIG, SIGKILL). If that fails it exits 3, never an
    exec without the binding.
  - Then, if `os.getppid() != parent`, it calls os._exit(1).
  - Then os.execv(exe). The pid stays the same, so the pid line, the ProcHandle and the pidfd stay as they are.
  - The worker passes `launcher=[python, -I, -B, run/bind_exec.py, <own pid>]` on Linux. uciproc's one Popen gets
    `[*launcher, exe]` (None gives today's call, on both systems).
  - No preexec_fn: a child stuck between fork and exec in a threaded parent would hold the worker's main thread in
    Popen with no watch.
  - The binding follows the thread that started the child, so start_engine refuses any thread but the main thread,
    on both systems (StartRefused naming "main thread").
- W9: worker.log's line reads "engine started: pid N created C, ...". It is written while the worker holds the
  process (unreaped, or its handle), so N and C name that process and no other.
- W10 (found by the combined package, section 0): check_identity on a slot folder that does not exist returns at
  once; nothing is held, nothing is made. A folder that exists is judged by W4 unchanged.
- The test:
  - alive(pid, created) and kill(pid, created) work as guard version 2's R11: on Windows, one handle with the
    creation time checked through it; on Linux, a pidfd, /proc read again and the pidfd polled.
  - engines_left and the end of V16's orphan read (N, C) from the worker's line. Nothing is ended by its number
    alone.
  - fence() writes the guard's record (schema 2). Before, it wrote a record typed by hand, without schema.

### Per case: the check that fails on the bytes before (Fable's request)
Both ways against the voted worker 218f7eae, with the new test: 291 of 351 there, 351 of 351 here. The 60 that fail:
- Astra 215331Z and Neon 223800Z section 1, a finalizer publishing `ended` beside another run's, an empty, a
  contradicting or a later-epoch range seal (W1):
  - V38b, V38c, V38d and V38e each fail "exit 4 naming `r0001.w000.seal.json`" and "the seal unchanged; journal
    epoch, epoch, NO ended" (8 checks).
  - The control V38a passes on both.
- Neon section 1, a stale header boot that skips the RESUME walk (W2): V39a and V39b each fail "exit 4 naming ..."
  and "no slot folder" (4).
- Neon section 1, old_boot_id never linked (W3): V40a, V40c and V40d, two checks each (6). The control V40b passes on
  both.
- Neon section 1, a populated slot folder with no IDENTITY.json adopted (W4): V41a fails "exit 4 naming `no
  IDENTITY.json`" and "the slot folder as before" (2). The controls V41b and V41c pass on both.
- Neon section 1 hardening, the lease times (W5): V42a, V42b and V42c, two checks each (6).
- Neon section 1 hardening, FENCE.json's schema (W6): V43a and V43b two each, and V43c one ("exit 4 naming
  `FENCE.json`"; the old worker: a traceback) (5).
- Neon section 1 and 231830Z, the parent-death binding (W8): V47 fails (1). start_engine does not exist in
  218f7eae. V46 and V46b to V46e are Linux only (below).
- Neon section 1 hardening, the pidfd (W7): V44 is Linux only (below).
- Fable's withdrawn YES on test_worker.py line 627, an orphan ended by its number (W9 and the test):
  - V45 fails 3 checks there: the old engine line holds no creation time.
  - For the same reason, 24 checks "no engine process left" fail there (V1, V7, V7b, V7c, V10, V12, V13, V13b, V16,
    V17, V20, V23, V24, V25, V28 to V36, V34a). The test reads (N, C) from the worker's line and does not judge a
    process by its number alone.
  - The test's own change: the new helpers pass T1a to T1e (5 of 5) in 3 of 3 runs. A copy whose two helpers read
    the number only fails T1c and T1d in 3 of 3 runs.
- W10: V48 fails on the worker as proven at 00:31 (98d80bfc, 350 of 351 there: exactly V48) and passes on
  218f7eae, which handled it. The control V48b fails on 218f7eae (1).

FOR YOU ON LINUX (they print SKIP here):
- V44: a ProcHandle that is not a pidfd gives exit 5 naming "pidfd".
- V46: the worker SIGKILLed at `>>> selfgame`, the test ending nothing; its engine (N, C) must be gone within 1 s.
- V46b: the same without the launcher. This is a plant and must fail.
- V46c: a stand-in guard holding the worker, both SIGKILLed; no engine may be left within 1 s.
- V46d: bind_exec with parent 1 and the real engine gives exit 1 and no engine output.
- V46e: 200 starts through the launcher of /bin/true while 3 other threads run; every Popen must be back within 10 s.
- Plants 15 (the pidfd not demanded: V44) and 16 (the launcher not passed: V46, V46b).

Please run `tests/test_worker.py` whole on Linux and send the Linux lines with your votes.

### Proof (this PC, Windows, the loop's engine and net)
- The full test: 351 of 351. test_uciproc: all 63 checks pass.
- Plants: 1 to 14, 17 and 18 each exit 1, failing exactly the cases written for them (plant 18 = W10's guard taken
  out: V48; plant 17 = the main-thread rule gone: V47). Every plant's old text was checked first to stand exactly
  once.
- Both ways on uciproc: the voted uciproc fails U-L2 (a launcher: the child's argv after the launcher's own is
  exactly [exe]).
- The first full run of the new test (before W10) stopped at V40d's fixture. That was a slip in my test, not in the
  worker: `resume_rec(..., n=True)` gave `n` twice, a TypeError. It was repaired before any count above was taken.

## 2. Packer version 2 (your NOT YET on packer.py 1db13462 and test_packer.py ee1e0db6)

Files:
- `run/packer.py` 3a5716b22acfd5a1f98036bd1701825d0f07fd104ad3761e6d1869f2a8f10c3f (612 lines, was 1db13462)
- `tests/test_packer.py` c76f8453a4d82e3c5f249da5da6d552f71a2ef647d20a9d243be7b19bedefd0e (982 lines, was ee1e0db6)

### What changed
Known answers were written by hand before the code, 00:17 PC, with one addendum at 00:27.
- P1 (Astra 214929Z; Neon confirmed it): A restarted packer in fallback mode never probed when every piece had
  been offered before the restart. `probe_piece` was set only by `pack`, and the scan skips offered pieces.
  - Now a piece the scan finds already offered (and checked, P5) becomes the probe piece when its seal names rows.
    So the probe runs on schedule after a restart, also while no new piece comes.
  - Pieces without rows still never meet the converter.
- P2 (Neon, high): An `ended` slot whose TRAILING seals are missing ended the packer with exit 0; the last pass
  looked only for seals after a gap.
  - Now every last pass (FENCE with every slot ended, STOP_PACKER, --once) reads each slot's journal end FIRST,
    then scans its seals.
  - When the journal ends with `ended`, the seals there must end exactly at its `last_index`. `last_seal` must be
    the sha256 of `p<last_index>.seal.json`, or, for `last_index` -1, the text `genesis:<run fingerprint>:w<NNN>`
    with no seal there. Anything else is exit 3 naming the slot.
  - The end is read first because a worker seals a piece before it writes its ended line, so a scan made after the
    read sees every seal that line names.
- P3 (Neon): `--poll`, `--probe-every` and `--convert-seconds` must be finite numbers (0 or more; more than 0 for
  --convert-seconds); otherwise STOP 2, nothing made.
- P4 (Neon): The wire copies of RUN.json, SCHEDULE.<n>.json, RESUME.<n>.json, FENCE.json and the range seals are
  made only of a canonical file (`parse_canon`; an empty file is not one). Otherwise exit 4 naming the file, its
  wire copy not written.
- P5 (Neon): A piece is passed over only when its `p.offer.json.zz` gives `p.offer.json` back, the offer is this
  piece's (B1's shape check, moved into one function both call, `offer_fault`), and every member's wire file is
  there at the byte count it names. Anything else: exit 4 naming the piece, nothing written.
- P6 (mine, 23 Nov 23:15): The test's K3 counted the converter stand-ins as alive by their NUMBER. Now it uses the
  number and the creation time (guard version 2's R11 helpers); K3 T1 to T3 show the helper tells identities apart.
- The ADDENDUM of 00:27 changed cases, not rules. K4, K18 and K20b held back the LAST pieces of a slot whose journal
  had already ended, and P2 rightly calls that slot incomplete. While pieces are held back, those cases now take the
  ended line off the journal (`cut_end`), and K4 puts it back with its pieces.

### Per case: the check that fails on the bytes before (Fable's request)
Both ways against the voted packer 1db13462, with the new test, one run each: 162 of 162 here, 142 of 162 there. The
20 that fail:
- P1: K23a, K23b.
- P2: K24a, K24b, K24c, K24e. The control K24d passes on both.
- P3: K16c, K16d, K16e, two checks each.
- P4: K25a, K25b, two each. The control K25c passes on both.
- P5: K26a, K26b, K26c, K26e. The control K26d passes on both.
- P6 is the test's own helper: plant 10 (the helper by number only) fails K3 T2.

### Proof
- 162 of 162, twice (the full test, and the both-ways run).
- 10 plants, each exit 1 failing exactly the cases written for it. Not plantable: P2's ORDER (the end read before
  the scan) guards a race with a live worker that a test cannot make on demand.

## 3. Guard version 2 (your NOT YET on guard.py 67384d4b and test_guard.py a0802304)

Files:
- `run/guard.py` 7ee4e054ec88e37e5a85310529f6c0f4dcaa1a6995013509d291666317c8582b (1470 lines, was 67384d4b)
- `tests/test_guard.py` 18eeef161ca64d9393b79e49420545cc3a315c99aa958f04dda8b0a59011a3bf (1530 lines, was a0802304)

### What changed
Known answers were written by hand before the code: 23 Nov 22:08 PC, R11 at 23:26 and R12 at 23:28, each before its
code. The sources: Astra 215151Z, 220826Z and 225517Z, Neon 223800Z section 4, and the agreed spec
server_guard_completion.md.
- R1: guard/CLOSED.json is fully read before "the day is closed":
  - canonical, its seven keys, schema 2, this run;
  - packer "ended";
  - slots_ended and slots_unreconciled disjoint, sorted, and together the header's slots;
  - a valid FENCE.json, and every ended slot passing R3;
  - STOP_PACKER there exactly when a slot is unreconciled;
  - `terminal` matching TERMINAL.jsonl and its .zz.
  Otherwise exit 4.
- R2: Every read of FENCE.json goes through ONE check: canonical, exactly its five keys, schema 2, this run,
  cutoff_utc the D in force. Otherwise Stop 4.
- R3: A slot is ended only when its IDENTITY.json is this run's and slot's, and its journal's last line is a whole
  canonical ended line whose last_index and last_seal name the genesis text or the seal on disk.
- R4: The room test counts a piece seal only when:
  - it is canonical, schema 2, this run, its own slot and index;
  - it is chained by prev_seal;
  - games >= 1 and raw_bytes >= 0.
  The first that fails stops that slot's count with an ALARM naming it.
- R5: A range seal counts only when canonical, schema 2, this run, round and slot as its name, first and last the
  newest schedule's row, and its through_index / through_seal consistent with the seal on disk.
- R6 (Linux): An earlier guard's group whose leader is gone has its members ended and verified gone (ALARM
  "orphan").
- R7: Every pass walks the whole RESUME chain as worker version 2 does.
- R8: The policy must hold target_rows an integer >= 1 and pilot_rounds_declared equal to the header's pilot rounds.
- R9: A fence control is held to inputs.plan_sha256 like every other kind.
- R10: After the packer's last pass the guard runs the terminal writer. It writes CLOSED.json only on a terminal
  record that checks out.
- R11 (the test): the test's own processes are known by number AND creation time.
- R12 (Linux): sweep_foreign and the R6 sweep end a process found by a /proc scan only through pidfd_open, a fresh
  /proc read and a poll of the pidfd. There is no inexact fallback.

Said plainly:
- V6 and V6b (R6's decision on a stand-in process table) were written WITH the code, not before it. A seat should
  read V6's table against R6.
- tools/make_control.py itself still skips the plan test for kind fence (Neon 222600Z names the same gap). Its own
  version 2 is still owed; section 3b changes only its TEST's fixture.

### Per case: the check that fails on the bytes before
Both ways on the guard (the new test, parts C and P, three times each): the new guard passes 3 of 3. The voted guard
67384d4b fails 3 of 3, each time the same 18 checks, all new or changed cases:
- V1a/V1b, V2a, V2b/V2c, V3, V4a, V4b to V4d, V5a to V5d, V6, V6b, V7, V8, V9, V10a, V10b, V10c;
- part P's CLOSED.json, its terminal writer and its groups.jsonl.
On the test's own change (R11; part P, three times each, against a copy whose helpers read the number only): 3 of
3 against 0 of 3, failing T1c and T1d each time.

FOR YOU ON LINUX (they print SKIP here):
- PG: an earlier guard's group whose worker died while its stand-in engine searches on.
- V11a to V11c: end_exact.
- Plants 43 (ours() not asked: V11a) and 44 (the poll not looked at: V11c).

### Proof (this PC, Windows, the loop's engine and net)
- Parts C and P: ALL PASS. Part E (the real engine, the real terminal writer): ALL PASS.
- 42 plants, each applied to a copy (1 to 27 of version 1, 28 to 42 new): 41 exit 1, each failing the case written
  for it. Plant 21 (version 1: D + grace never comes) leaves part P waiting for a close that never comes. The
  chain's 400-second limit ended it (exit 124) after 8 of its checks had already failed.

## 3b. make_control's test version 2: the fixture only (make_control.py unchanged)

- `tests/test_make_control.py` f7d38fba83a34b2fab52a1dff7bba8d4581490b5002b0d0a45966492ecfa2352 (510 lines, was
  14ed7d71)
- The finding: on the combined package, make_control's voted test gave 96 of 103 under guard v2.
  - Its fixture `make_root` wrote `{"games": 4, "raw_bytes": 4000, "rows": 100, "schema": 2}` as seal 0 of slot 1.
    No worker ever writes that.
  - Guard v2's R4 counts only this run's chained seals. So it held control 1 ("room: no sealed piece yet, the bytes
    of a game are not measured"), and the 7 failures all follow from that hold.
  - Guard v2 is right. Under guard v1 the stand-in had passed, because v1 counted any seal file's games.
- The change: `make_root` writes the seal in the worker's form, with the 18 keys of a real worker seal:
  - this root's run fingerprint, slot 1, index 0, round 1, schedule 0, epoch 1;
  - prev_seal "genesis:<fp>:w001";
  - the same games, raw_bytes and rows as before, so the room test measures the same 1000 bytes a game.
  Known answers were written before the edit (01:34 PC).
- Proof:
  - 114 of 114 under guard v2, and 114 of 114 under guard v1 (the published package before guard v2).
  - Both ways (guard v2; the new test against the voted one): 2 of 2 against 0 of 2. The voted test fails exactly
    the 7 checks above, both times.
  - The voted test's own proof run counts the same 114.
  - The test's 13 plants each exit 1, failing the same checks as the voted test's plants did.
  - One count in my known answers was wrong: I had written 103. In the failing run, part A stopped at its traceback
    and 11 of its checks never ran.

## 4. Content version 2.1 (your NOT YET of 20261124T004000Z)

Files:
- `home/content.py` 0e9cbb2825edaa8fe61bcf9aa1d82182730e9c8d9b1bffd8259299c86990ced4 (509 lines, was 2cc1fb9f)
- `tests/test_content.py` e319128fd8865f2ee80896c1ab22df0d809e9a93ed85bb4acabd410fd450925b (973 lines, was 4535c79d)

### What changed
Known answers were written by hand before the code, 00:38 PC, with one addendum at 00:51.
- R-T8 is your fix as you wrote it. `check_index()` raises Stop 3 before anything is judged or written when the
  index names no run (no meta table, or no run row) and its entries or judged table holds rows: "content/equal.sqlite
  holds entries or judged rows and names no run: a home folder serves one run (2.1); give this run a fresh home folder
  (nothing was written)".
- An index of EMPTY tables stays this run's. index() creates its tables before its transaction, so a crash before
  the first COMMIT leaves exactly that, and the next pass must go on.
- New cases. Each of the first three wants exit 3 naming content/equal.sqlite, with content/ byte for byte as
  before:
  - V3d: P1's judged home with the meta row deleted;
  - V3d2: the meta table dropped and every verdict removed;
  - V3d3: the meta row and every entry deleted.
  - V3d0 is the control: no verdicts, and an index of the empty entries table only.
- The ADDENDUM of 00:51 changed a case, not a rule.
  - P9 made its index by hand in version 1's form: the entries table with one planted entry and no run row. R-T8
    rightly refused it.
  - Content's own index() writes the run row in the SAME transaction as every entry, so P9's fixture now also makes
    the meta table with the run row.
  - P9's planted entry and every want are unchanged.

### Proof (this PC, Windows, the official converter)
- 97 of 97.
- Both ways against the published content 2cc1fb9f: 97 of 97 twice here, 94 of 97 twice there. The 3 that fail are
  exactly V3d, V3d2 and V3d3 (your case and its two neighbours); V3d0 passes on both.
- 38 plants, each exit 1 failing its case. Plant 38 (the new test taken out) fails exactly V3d, V3d2 and V3d3.

### Your remarks on custody version 2 (your YES)
1. `check_records()` reads only the header's slots. Agreed, and it is not a hole today. Home() stops (Stop 3) when
   wire/RUN.json.zz is not the run this home was pinned to, so Run B in Run A's home stops before custody reads a
   slot. Reading every `custody/w[0-9]{3}` would also catch the disjoint-slot case, so I take it into custody's next
   version. Your YES stands on the bytes you voted.
2. No converter on your Linux machine: right. The binpack path of test_custody is verified on Windows only. The Linux
   build of the official converter belongs to A3g (the machine check and the Linux build). Until it exists, the plan
   says this path is Windows-verified.

## 5. Credit version 2 (Neon's NOT YET 20261123T231800Z, six defects)

Files:
- `home/credit.py` cda4a3cbfec6e50674d52aa09844b506206c0b5e602728876b1c91c13da219b4 (593 lines, was 85f07d53)
- `tests/test_credit.py` 29f034a508e0f3264a0ebff8e44c1cc198b5e482338027b85451c60a1c3e8a53 (966 lines, was ea2a32a4)

Known answers were written by hand before any code (01:04 PC), with addenda at 01:13, 01:21, 01:26 and 01:28. The
voted custody.py is used as it is: its readers `Home.record` and `Home.check_records` are called, not copied.

### Exit codes
- 3: another run's evidence.
- 4: a file that cannot be read or written, including a receipt or fork record that custody's own reader refuses,
  and a table that is gone, empty or unreadable while decided rounds exist.
- 5 HOLD: home's evidence contradicts itself, or a record is not of the form its writer writes. Nothing is decided,
  and the ALARM line names the file and the rule.
- 0 WAIT: something is still on its way. Nothing is decided, and the WAITS line names it.
- Never exit 1, never a traceback.

### What changed (your six, in your order)
- C1, the range seal:
  - the six counts are ints >= 0 (not bools);
  - not_done: ids of this run, slot and range, in STRICTLY rising counter order, all below never_dispatched_first;
  - epoch an int >= 1;
  - short a bool equal to its row in the newest schedule home holds;
  - complete a bool equal to `unfinished + dispatch_unknown + never_dispatched == 0`, by the worker's own
    NOT_COMPLETE;
  - first_index and through_index ints >= -1.
  On complete I follow FORMATS 1.7 [2.4] and the worker, not your formula `done + noselfgame == last - first + 1`.
  The two differ only for a range with a `refused` id: FORMATS calls it complete, your formula would not. The agreed
  document holds.
- C2, the verdict: it must be a canonical record with exactly content's keys, schema 2, and piece judged or refused.
  - Refused: games [] and why a text.
  - Judged: games as long as the kept seal's games, each game with exactly content's five keys, a known state and
    rows an int >= 0.
  - The rows_digest rule per state (accepted, noselfgame, set_aside), and the rows summing to the kept seal's.
  - A verdict that does not parse is a HOLD naming it.
- C3, the chain C1: every receipt and fork record of the header's slots is read through custody's `check_records()`
  at the start of a pass, before anything is decided or written (another run's: STOP 3; malformed: STOP 4).
  Walking a slot:
  - a receipt whose kept seal is ABSENT: WAIT;
  - a present kept seal that does not decompress, is not canonical, is not its receipt's bytes, or names another
    run, slot or index: HOLD;
  - a fork record: HOLD;
  - a broken prev_seal link or a falling epoch: HOLD.
  The HOLD comes when a round needs that index.
- C4: no traceback. A truncated receipt is STOP 4 by custody's reader; a truncated verdict is a HOLD.
- C5, before any round is decided:
  - SCHEDULE.<newest+1> present but not taken by custody's chain: HOLD.
  - A name outside `SCHEDULE.<n>.json.zz`: HOLD.
  - A gap: WAIT.
  - A stage/<folder>/credit.json or a rounds row of a round no row of the newest schedule names: HOLD.
- C6:
  - first_index -2: HOLD.
  - The C1 pieces of slot k whose kept seal names round r must be exactly the range seal's [first_index,
    through_index]; a piece of round r outside it is a HOLD.
  - When any stage/r*/credit.json exists, the table is first opened READ-ONLY. A schema-only table is STOP 4, and the
    table stays byte for byte as it was.

### Cases
- K22a to K22i (C1, C6): K22g is your empty range while C1 holds p0 and p1; K22h and K22i are its neighbours.
- K23a to K23k (C2).
- K24a to K24e (C3: a fork record, the epoch, prev_seal, the seal's own index, another seal's bytes). K24f is the
  control: the kept seal absent, which WAITS.
- K25a to K25c (C3, C4: a truncated receipt, another run's receipt, and a truncated receipt beyond the walk). The
  last is the only one that shows check_records itself, because the walk reads every receipt it reaches through
  custody's reader too.
- K26a to K26e (C5), K27a (C6, the table).
- A second real fixture R3: two slots, a real noselfgame, a real SCHEDULE.1, the raw path at home. On it, K28a (both
  credit lists byte for byte, slot 2 repeating slot 1) and K28b (a missing range seal: WAIT). Both pass on version 1
  too: R3 is a control that both versions read alike.

Three of my fixtures were wrong and are said in the addenda; no rule changed for them.
- K10 and K12 (version 1) were not of the form the worker and content write.
  - K10 kept piece 5 of a round cut at piece 4. Under C6 the new code HOLDS on it, rightly, so K10's home now loses
    piece 5 as it would have.
  - K12 appended a third record to a judged verdict of 2 games. K12 now renames one record instead.
  - Both wants are unchanged, and both still pass on version 1.
- R3's first form gave an opening entry that ENDS in mate. That is a complete opening: the worker plays it and the
  engine ends it at once, so content rightly called the game accepted, not noselfgame. One listed ply that can never
  be played makes it an opening end.

### Proof (this PC, Windows, the loop's engine and net, the official converter)
- 84 of 84, twice.
- Both ways against the voted credit.py 85f07d53, under the new test: 84 of 84 twice here, 50 of 84 twice there.
  The 34 that fail are exactly the new cases, one check each: K22a to K22i, K23a to K23k, K24a to K24e, K25a to
  K25c, K26a to K26e, K27a. The controls K10, K12, K24f, R3, F1, K28a and K28b pass on both.
- 49 plants, one exact text replacement each on a copy. Every text stood exactly once, and every plant gave exit 1.
  - Plants 23 to 49 (the new rules), each on its case(s): 23 K22a, 24 K22b, 25 K22c, 26 K22d, 27 K22e, 28 K22f,
    29 K22g + K22h + K22i, 30 K23a, 31 K23b, 32 K23c, 33 K23d, 34 K23e, 35 K23f, 36 K23g, 37 K23h, 38 K23i,
    39 K23j, 40 K24a, 41 K24b, 42 K24c, 43 K24d, 44 K24e, 46 K26a + K26b + K26c, 47 K26d, 48 K26e, 49 K27a.
  - Plant 45 (no check_records) fails K25a, K25b and K25c. My plant list named K25a and K25b. My addendum of 01:13
    then said those two would stop through the chain walk anyway, so that only K25c could show the plant. They do
    stop, with the right code and words, but only after a file was written. check_records is what makes the stop
    come before anything is written, and both cases check "nothing written". The list was right; the addendum was
    wrong about those two.
  - Plants 1 to 22 of version 1: each fails every case it failed in version 1's own plant run. Five also fail new
    cases, because those cases pass through the same planted line:
    - plant 1 (a piece not in C1 goes unnoticed): K24a to K24f;
    - plant 4 (a repeat credited as new): K28a;
    - plant 6 (a waiting round goes on): K24f and K28b;
    - plant 11 (the range walk one index short) and plant 12 (rounds in reverse order): many of K22 to K28.

## 6. Launcher version 2 (Astra 8290095d and Neon's NOT YET 20261123T222600Z)

Files:
- `run/launcher.py` a669beeb15fe7e1ac577b37785de8e8c1741932c020c867742bf77c1e160c733 (186 lines, was f9545304)
- `tests/test_launcher.py` c2e66748e971b6e5e8f90249746a641933c25dcb40a61f290247583339522c94 (460 lines, was 2cf7e0f4)

Known answers were written by hand before any code (01:58 PC). Each claim was checked by reading the code first:
- Astra: `--pilot-rounds 10000 --round-games 1` gives exit 0 and a header with a row of round 10000. The worker's own
  `check_rows` refuses that row (`1 <= round <= 9999`).
- Neon 1: the option lines were hashed with `.encode("ascii")` outside every handler, and their type was never
  checked. A JSON escape gives a non-ASCII text after an ASCII decode (UnicodeEncodeError, a traceback), an int line
  gives TypeError, and `selfgame_line` was never checked to be a text.
- Neon 2: `rd.boot()` was read outside every handler. The real reader `worker.boot_id()` has no try.
- Neon 3: `--piece-games` had no upper bound.
Four more of mine, found while reading:
- M1: `list(man["options"])` turned a text into its characters and a dict into its keys, with exit 0.
- M2: the hash joins the lines with LF, so `["a\nb"]` and `["a", "b"]` gave the same options_sha256.
- M3: `launch()` caught Held and Stop only, so an OSError while RUN.json was written was a traceback.
- M4: a manifest `net_sha256` that is not 64 hex gave exit 5 ("the net file is not the manifest's"). It is a
  malformed manifest, exit 2.

### What changed
- L-A: `--pilot-rounds` at most 9999, exit 2 naming it.
- L-B: `--piece-games` at most 99999999 (FORMATS 1.2: a piece holds games of one range), exit 2 naming it.
- L-C: the manifest is checked whole before anything of it is used, each part with its own words, exit 2:
  - `options` a list (M1);
  - every option line a text of printable ASCII, 0x20 to 0x7e, at least one character, so no LF inside (Neon 1, M2);
  - `selfgame_line` such a text (Neon 1);
  - `net_sha256` 64 lower-case hex (M4).
- L-D: the boot id is read inside a handler. OSError or ValueError (UnicodeDecodeError is one) gives exit 5 naming
  "boot id", nothing written (Neon 2).
- L-E: an OSError anywhere in `launch()` is "REFUSED exit 4: a file cannot be read or written: ..." (M3). The
  docstring's exit codes say so.
- Nothing else changed. Every case of version 1 keeps its want.

### Cases (part V of the test, new)
| Case | Change | Want | Version 1 gave |
|---|---|---|---|
| L7a | pilot_rounds 10000, round_games 1 | exit 2 naming `--pilot-rounds`, root empty | exit 0, RUN.json written |
| L7b control | pilot_rounds 9999, round_games 1, slots 1 | exit 0; 9999 rows, the last round 9999 at counter 9999; `worker.check_rows` takes the rows | the same |
| L7c | piece_games 100000000 | exit 2 naming `--piece-games` | exit 0 |
| L7d control | piece_games 99999999 | exit 0, written in the header | the same |
| L7e | an option line with a non-ASCII letter (a JSON escape in ASCII bytes) | exit 2 naming "option lines" | UnicodeEncodeError raised |
| L7f | options [1, 2] | exit 2 naming "option lines" | TypeError raised |
| L7g | options a text | exit 2 naming "not a list" | exit 0 |
| L7h | selfgame_line 5 | exit 2 naming "selfgame_line" | exit 0 |
| L7i | the first two option lines joined by a LF | exit 2 naming "option lines" | exit 0, and the same options_sha256 as the real manifest |
| L7j | net_sha256 5 | exit 2 naming "net_sha256" | exit 5 |
| L8a | the boot reader raises OSError | exit 5 naming "boot id", root empty | OSError raised |
| L8b | the boot reader raises UnicodeDecodeError | exit 5 naming "boot id" | UnicodeDecodeError raised |
| L9 | RUN.json.tmp is a folder (create_only cannot remove its scratch name) | exit 4 naming "cannot be read or written", the root as it was | PermissionError raised |

A call that raises is recorded as the exception's name, and part V goes on. One more check, "L7i why", shows the
ambiguity itself: the joined line hashes exactly as the two lines did. It passes on both versions.

### Proof (this PC, Windows, the loop's engine and net)
- The new test on version 2: 63 of 63 (version 1's 49 + 14 new).
- Version 1's own test (2cf7e0f4) on version 2: 49 of 49.
- Both ways, twice each, under the new test: version 2 2 of 2 ALL PASS; version 1 0 of 2, with 11 failures each
  time: exactly L7a, L7c, L7e to L7j, L8a, L8b and L9, each with the value in the last column above. My known answers
  said "the 13 negative rows" and then named these 11: the number was a slip of mine, the named list is what was
  checked.
- 23 plants (one exact text replacement each, on a copy), every one exit 1:
  - 15 L7a; 16 L7c; 17 L7g; 18 L7e and L7i; 19 L7h; 20 L7j; 21 L8a and L8b; 22 L8b; 23 L9.
  - Plants 1 to 14 of version 1 fail the cases they failed in version 1's own plant run, with three differences,
    each explained. Plant 10 (the pilot rows shifted) also fails the new L7b. Plant 13 (create_only replaced by a
    plain write) also fails the new L9, because the plain write succeeds beside the folder. Plant 5 also fails the
    two plan.json checks, which entered the test at the bug hunt of 23 Nov 19:30, after that plant run.
- The package was unchanged after the chain (`sha256sum -c` exit 0).

Your other NOT YETs of 222600Z (bootguard, terminal, make_control) are next, each with its own known answers first.
They are not in this push.


## Your votes, please

On each of the sixteen hashes above: YES, YES WITH REMARKS or NOT YET, each with its reason (file and line, or a
run). Fable's votes follow when he reads the bytes.
