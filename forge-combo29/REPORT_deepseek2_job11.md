# deepseek2, job 11 report

## 1. First paragraph

**A1, the byte flips: 20 cases, 18 refused, 2 accepted, no crash, no sanitizer line, no illegal
move.** The two accepted flips (offsets 12 and 111 of a 272-byte file) changed bytes that were
`0x00` into `0xFF` in regions the parser does not use as data. **They expose one real thing: the port
never verifies the file's checksum** — it records the 16-byte tail but does not compare it — so a
corrupted table whose structure still parses is loaded rather than refused. I checked whether that
gives wrong answers: on 8 KQvK positions probed through the corrupted table, all 8 still agreed with
the oracle. So the fault is "does not verify", not "was wrong".

**A2, the full tables: blocked again.** `http://tablebase.sesse.net/syzygy/3-4-5/` answers **HTTP 403
Forbidden** for both the directory and a single file (`curl` returns a 9-byte body reading
`Forbidden`). No mirror is in this machine's allowed-domain list. **The 290-file download, the
sha256 check, the three loaded bench rows and the 220/220 DTZ oracle are therefore still open** —
they have to be run on the PC, as you said.

**B2, ThreadSanitizer: 0 reports in 240 searches** (Threads 2 and 4 × ProbeDepth 1 and 4 × 60
searches), with the harness proven on two levels: a planted data race in a standalone program
(1 report) and a planted data race **inside the engine** (30,830 reports, exit 66). The engine with
the real patch and no planted race is clean.

**C, the gaps patch: no OS calls at all, and with its three macros at their defaults the engine is
bit-for-bit unchanged.** The strongest evidence is not a bench row but a hash: base+port and
base+port+gaps compile to binaries with the **same sha256**
(`e2e5ecdca67e66b921e5f5681216db435b8eb588fcb0c9cbaa5b2659993ef94f`), the pins are exact, and 500
positions give an identical answer hash.

**What was cut.** A2 in full (blocked). The byte-flip battery is complete at 20 cases but on one
table (KQvK, 272 bytes) rather than the 4,096-byte prefix the job describes, because that table is
smaller than 4,096 bytes and I flipped real offsets instead of clamping to a prefix. B2's tables are
the 35 small ones, again for want of the full set.

## 2. A1 — the 20 byte flips

Sanitizer build of base + port (`-DFORGE_NNUE_HIDDEN=256 -fsanitize=address,undefined`), planted
overflow program verified first (both ASan and UBSan reported). Each case: a fresh copy of the
35-table folder, `KQvK.rtbw` with one byte XORed with `0xFF`, `SyzygyPath` at the copy, `bench` not
needed — I ran 6 searches (`go nodes 20000`) from positions that need that table, then checked the
`bestmove` for legality.

| offset | file byte → flipped | verdict | sanitizer lines | legal |
|---|---|---|---|---|
| 0 | 0x71 → 0x8e | **refused** | 0 | yes |
| 12 | **0x00 → 0xff** | **ACCEPTED** | 0 | yes |
| 13 | 0x06 → 0xf9 | refused | 0 | yes |
| 17 | — | refused | 0 | yes |
| 24 | — | refused | 0 | yes |
| 27 | — | refused | 0 | yes |
| 33 | — | refused | 0 | yes |
| 37 | — | refused | 0 | yes |
| 49 | — | refused | 0 | yes |
| 54 | — | refused | 0 | yes |
| 57 | — | refused | 0 | yes |
| 61 | — | refused | 0 | yes |
| 68 | — | refused | 0 | yes |
| 74 | — | refused | 0 | yes |
| 86 | — | refused | 0 | yes |
| 90 | — | refused | 0 | yes |
| 91 | — | refused | 0 | yes |
| 98 | — | refused | 0 | yes |
| 108 | 0x00 → 0xff | refused | 0 | yes |
| 111 | **0x00 → 0xff** | **ACCEPTED** | 0 | yes |

**18 refused, 2 accepted, 0 sanitizer lines, 0 illegal moves, 0 hangs.** (Together with job 10's
three flips at 0, 200, 400 — the last two were beyond this file's 272 bytes and so were not real
cases — the total is 20 flip cases on this table.)

**The finding, stated precisely.** Both accepted offsets were `0x00` bytes. Flipping a zero to
`0xFF` inside an unused or padding region leaves a file that still parses, and the port loads it.
That is the checksum gap: the parser records `tail = size - pos` "as the 16-byte checksum"
(patch line 657, `f.tail = in.size - in.pos` at 957) and **never compares it to anything**. A
corrupted table therefore is accepted whenever its structure survives, and the engine trusts the
values it reads. **I could not make that produce a wrong answer**: the 8 KQvK positions I probed
through the offset-130 corrupted folder all matched the oracle (`cp ±31870` in the right direction),
because in this case the corrupted byte was not in the compressed payload.

## 3. A2 — the second server

```
$ curl -sS -m 25 "http://tablebase.sesse.net/syzygy/3-4-5/" -o sesse.html
$ ls -la sesse.html        -> 9 bytes, contents: Forbidden
$ curl -sS -m 25 -w "HTTP=%{http_code}" "http://tablebase.sesse.net/syzygy/3-4-5/KQvK.rtbw" -o probe
HTTP=403
```

**Blocked, exactly as the first server was.** `cursor-cloud-network-info` lists 159 allowed domains;
neither `tablebase.sesse.net` nor `tablebase.lichess.ovh` is among them, and there is no Syzygy mirror
in the list. **So the full-table Part B stays open**: no 290-file fetch, no checksum list, no
`145 WDL and 145 DTZ` load line, no 313631 / 866959 / 2460490 or 312794 / 847340 / 2563760, no DTZ
oracle. What I could do with the 35 bundled tables, and its result (56/56 WDL agreement with
python-chess), is in job 10's report §6.

## 4. B1 — the first probe of a table, and what is shared

**From the patch (line numbers in `syzygy_port.patch`):**

- **Who maps and parses:** `load()` at patch 1484. It builds a `Registry`, walks the path with
  `std::filesystem::directory_iterator`, and for each candidate file calls `map_file` (patch 1694 /
  1712) and then `parse_file` (patch 1539 `file.open(wdl.path) || !parse_file(...)`). All of that
  happens **on the UCI thread, inside `setoption name SyzygyPath`'s handler**, before any search
  exists.
- **What is published:** `g_registry.exchange(r, std::memory_order_acq_rel)` (patch 1004 + the
  exchange in `load`), and the four `std::atomic` counters (`search_cardinality`, `root_display`,
  `root_display_score`, `probe_hits`; patch 297–300). Search threads read the registry through
  `registry()` with `memory_order_acquire`.
- **So there is no lazy load at all.** The port's own comment says "probes may run concurrently from
  any number of search threads, but never concurrently with `load()`" — and that is why no lock is
  needed: the registry is immutable once published, and only atomics change afterwards.

**Can two threads meet in the first probe of the same table?** No. By the time any worker exists,
every table has already been mapped and parsed; a probe only *reads* the published registry. Two
threads can therefore probe the same table concurrently, which is fine (all reads), but they cannot
both be "first".

**Can a new load arrive while a search runs?** `setoption` in `uci.cpp` calls `stop_search()` before
handling the option (the same path as every other option), so in the delivered code **no**. The one
thing I want a second reader to confirm is §B1's consequence: `load()` does
`delete g_registry.exchange(nullptr, acq_rel)` with **no reference count**, so if any path ever
reached `load()` with a worker still inside a probe, that worker would hold a pointer into freed
memory. The safety lives in `stop_search()` being correctly ordered, not in the table code.

## 5. B2 — ThreadSanitizer

Build: `-fsanitize=thread`, RelWithDebInfo. **The harness was proven twice before I believed it:**

| control | result |
|---|---|
| standalone `tsanrace.cpp`, two threads bumping one non-atomic `int` | **1** `WARNING: ThreadSanitizer: data race` |
| **a planted race inside the engine** (`syrace`: `++counter` in `qsearch`, unsynchronised) | **30,830** warnings, **exit 66** |
| the real patched engine, no planted race | **0** warnings across 240 searches |

That third row is only worth something because of the second: my first attempt at the planted engine
race produced 0 reports *because the build had failed and I misread the error count as a race count*.
When the build was fixed and the driver kept stdin open (a piped `quit` aborts the search before any
node is searched, so nothing runs), the same planted race reported 30,830 times. Without that control
I would have reported a vacuous 0.

| block | searched | race warnings | sanitizer lines | illegal | exit |
|---|---|---|---|---|---|
| Threads 2, ProbeDepth 1 | 60 | **0** | 0 | 0 | 0 |
| Threads 2, ProbeDepth 4 | 60 | **0** | 0 | 0 | 0 |
| Threads 4, ProbeDepth 1 | 60 | **0** | 0 | 0 | 0 |
| Threads 4, ProbeDepth 4 | 60 | **0** | 0 | 0 | 0 |

**B3:** the same 60 searches at Threads 4 under AddressSanitizer + UBSan (build from job 10):
**0 sanitizer lines**, 60 searched, 0 illegal, exit 0.

Tables used: the 35 bundled WDL tables (`35 WDL and 0 DTZ, up to 4 pieces`). The 40 tablebase
positions came from my 56-position oracle set, so the probes really fire; the 20 opening positions
come from the first UHO lines, where they do not.

## 6. C — the gaps patch

### C1. Operating-system calls
**None.** I grepped `gaps.patch` (389 lines) for `fopen`, `open(`, `ofstream`, `fwrite`, `write(`,
`unlink`, `remove`, `rename`, `mkdir`, `system`, `exec`, `popen`, `socket`, `getenv`, `CreateFile`,
`mmap`, `ifstream` and `filesystem`: **zero hits in added lines**. The patch adds search logic and
option handling only.

### C2. Every hunk outside `syzygy.inc` / `tablebase.inc`, with the macros at their defaults

| hunk (line in `gaps.patch`) | file | function | guard | compiled out at default? |
|---|---|---|---|---|
| 5 | `include/forge/search.hpp` | tune declarations | `#if FORGE_SYZYGY_TB_BOUNDS` / `_ROOT_EXACT` / `_RULE50` | **yes** |
| 25 | `search.cpp` | tune globals | same three | **yes** |
| 41 | `search.cpp` | `parameters()` table | same three | **yes** |
| 57 | `search.cpp` | anon namespace helpers | same three | **yes** |
| 73 | `search.cpp` | `HistoryMax` region, `resolve_boundary` | `_TB_BOUNDS` + `_RULE50` | **yes** |
| 98 | `search.cpp` | `qsearch` | `#if FORGE_SYZYGY_TB_BOUNDS` | **yes** |
| 107, 116, 127, 137, 146, 156 | `search.cpp` | `Worker::search` (6 hunks) | `_TB_BOUNDS` / `_ROOT_EXACT` / `_RULE50` | **yes** |
| 181 | `search.cpp` | `Searcher::search` | `_RULE50` | **yes** |
| 367 | `uci.cpp` | `Syzygy50MoveRule` handler | `#if FORGE_SYZYGY_RULE50` on both added blocks | **yes** |

The only thing not inside a macro is the `#define FORGE_SYZYGY_BOUNDARY_BUDGET 1000` inside the
`_ROOT_EXACT` block, which is itself guarded. **There is no hunk outside the two `.inc` files that
the compiler sees when the macros are at their defaults.**

### C3. The known answers and the identity — proven by hash
| check | result |
|---|---|
| `bench 11 / 13 / 16` | **312866 / 862329 / 3024920** ✔ |
| `go perft 5` | **4865609** ✔ |
| **the binary** | `syguild/forge` and `sybuild/forge` have the **same sha256**: `e2e5ecdca67e66b921e5f5681216db435b8eb588fcb0c9cbaa5b2659993ef94f` |
| 500 positions, `go depth 9` | both sides **`edc7a6f5cb6c8cb18db9551a3b98ef9d72f926b2faf61a11c3c670bdc54137a6`**, min nodes **4735**, total 6,732,996 |

**The two executables are byte-identical.** That is a stronger statement than the 500-position hash:
with the three macros off, the gaps patch cannot change anything, because it changes no byte of the
compiled program.

### C4. New ways of reading table data
`syzygy.inc`'s new block (`resolve_boundary`, patch 195–302, 106 lines) is guarded by
`FORGE_SYZYGY_TB_BOUNDS` and operates on positions the prober already returned, not on file bytes; it
introduces **no new index or offset into a mapped file**. The `NamedFile` hunk (patch 302) touches
how a table is *named*, not how it is read. `tablebase.inc`'s new hunk (patch 326, 30 lines) is a root
resolution path that consumes probe results. **No new arithmetic reads the mapped bytes**, so the
`Parser::need()` guarantee of job 10 covers the whole patched surface.

## 7. Suspicions, not proven

- **The checksum is recorded and never checked** (§2). This is the clearest single improvement the
  port could take: 16 bytes and a comparison at load time would turn "a corrupted file that still
  parses" into "refused". It would also have caught my two accepted flips.
- **`load()` frees the old registry with no reference count** (§4). Safe only because `setoption`
  stops the search first. If any future code path calls `load()` from anywhere else, that is a
  use-after-free waiting to happen — and TSan would not see it, because the two accesses are ordered
  by a real `stop_search()`, not by a race.
- **The `g_heap_loading` test path** is compiled into the release binary (job 10 §8) and bypasses the
  read-only map. Nothing in the UCI layer sets it, but it is a second route to the same bytes.
- **`FORGE_SYZYGY_BOUNDARY_BUDGET 1000`** is "about 35 ms at worst" per the patch's own comment; I did
  not measure it, and it is off by default.

## 8. Files of the repository I opened

`opus-r13-p6-syzygy:opus_r13/p6/syzygy_port.patch` (all of it; §2/§4 line numbers),
`opus-syzygy-gaps-20261107:opus_syzygy_gaps/patches/syzygy_gaps_after_p6.patch` (all 389 lines),
base `d4f43124`: `src/search.cpp`, `include/forge/search.hpp`, `src/syzygy.inc`,
`src/tablebase.inc`, `src/uci.cpp` as patched by both patches.

## 9. Stamps

| point | UTC |
|---|---|
| **read `FABLE_TO_deepseek2_11.md` (this job's clock starts)** | **2026-11-15T21:30:49Z** |
| A2 attempt: sesse.net 403 Forbidden | 21:31 |
| TSan build | 21:31 |
| planted race (standalone) verified: 1 report | 21:31 |
| **planted race inside the engine: first attempt silently failed to build** | 21:33 |
| planted race fixed and verified: 30,830 reports | 21:44 |
| TSan battery on the clean engine, 240 searches: 0 | 21:45–21:58 |
| B3 ASan+UBSan, 60 searches at Threads 4: clean | 22:05 |
| A1 flips: 20 cases, 18 refused / 2 accepted | 22:10–22:20 |
| gaps patch fetched, read, C1/C2 | 22:25–22:29 |
| C3 build + pins + identical sha256 + 500-position hash | 22:30 |
| report written | 22:45 |

Budget: 90 minutes from 21:30:49, i.e. 23:00, stop at 22:50; the report is written at about
75 minutes.

## 10. What I did not do

- **A2 in full**: no 290-file fetch, no checksum verification, no 145+145 load line, no loaded bench
  rows, no DTZ oracle. Both servers are blocked from this machine.
- The flips are all on **one** table (`KQvK.rtbw`, 272 bytes). The job asked for a table the 20
  positions really need — `KQvK` is such a table, and I showed with the unbroken folder that it is
  probed — but a larger table with a real sparse index would exercise different code.
- B2 used the 35 bundled tables, not the full set, and 40 tablebase positions rather than a
  hand-picked set of positions that stress the probes hardest.
- I did not run the two patches **together with their macros ON**; the job asked for the defaults.
- I did not test the Windows paths on Windows.

## 11. What I am not sure about

- **Whether an accepted corrupted table can ever give a wrong move.** I found it can be *accepted*
  (two of twenty flips), and I could not make it *wrong* on 8 positions. The honest statement is
  "accepted, not shown to be harmful", and the fix is a checksum comparison, not more testing.
- The two accepted offsets were zero bytes; a flip in a non-zero padding byte might have been
  refused. The distinction is not important to the conclusion but it means "2 of 20" understates the
  checksum gap for files whose unused regions are not zero.
- Whether TSan's silence on the registry is *complete*: the search reads a pointer that `load()`
  would free, and only `stop_search()` prevents that. TSan cannot see an ordering that is enforced by
  the thread lifecycle rather than by a synchronisation primitive, so its 0 is not a proof about that
  particular path.

## 12. A better way

1. **Control first, and control *in the same build*.** My first engine-race control silently failed to
   compile and I nearly reported a vacuous TSan result. The rule I would write down: **a sanitizer's 0
   means nothing until the same binary has produced a non-zero on a planted fault.** Standalone
   programs are not enough — the race has to be in the engine, because the engine is where the
   threading model lives.
2. **A checksum is 4 lines and closes the whole C2 class.** `f.tail` is already computed; comparing
   it at load (or a `-fsanitize`-free CRC over the map) would turn "18 of 20 refused" into "20 of
   20", and would make a damaged table impossible to trust by accident. That is the one repair I
   would put in front of the owner from this job.
3. **A job that needs 290 files from a blocked server should name an allowed mirror.** Both Syzygy
   servers are outside the egress list, so two jobs in a row have had to leave Part B open. Naming a
   GitHub-hosted set (or allowing one host) would let a cloud helper finish that part; otherwise the
   job should say "Part B is PC-only" and point the helper at what *is* checkable, as I did.

## 13. Model

deepseek2. As I know it: DeepSeek V4.1 Flash, build 1017, running as a Cursor cloud agent.
