# S08 TLS sanitizer regression, v2 profiling-only repair

The original v1 ASan+UBSan engine failed its first bare bench11 before UCI.
That failed engine, its build receipt, stderr, v1 source freeze, Release ON ELF,
and earlier d11 passing evidence remain unchanged. v1 is not qualified by the
Release-only passes.

## Root cause observed in the generated code

The v1 pointer definition `thread_local Bank* current_bank=nullptr` already has
constant initialization under C++20. Its external declaration did not communicate
that guarantee to other translation units. GCC14.2 consequently emits a weak
optional TLS initialization wrapper in each consuming TU. Under the exact O2/g
ASan+UBSan recipe, the linked Worker::search code contains:

- 0x42871a: CMP the weak TLS initializer GOT slot against zero.
- 0x428729: JE skips the absent initializer.
- 0x42873e: MOV FS:0 into RAX; 0x428747: LEA RAX-0x30 computes TLS address.
- 0x42874e: JE enters the UBSan store-null handler at0x4354a9.

MOV and LEA do not set arithmetic flags. That JE therefore reuses ZF from the
initializer-presence check, rather than testing the computed TLS address. The
handler is taken because the weak initialization function is absent. The real
store path writes FS:-0x30. This is evidence of incorrect GCC14 sanitizer/TLS
code generation, not evidence of a null Bank object or expired bank lifetime.
Saved symbol and disassembly files bind this finding to the failed f52b engine.

## Smallest tested source repair

Only the declaration and definition in NEW `S08/Lprime_v2` change:

```cpp
extern thread_local constinit Bank* current_bank;
thread_local constinit Bank* current_bank=nullptr;
```

An explanatory header comment describes cross-TU visibility. `constinit` keeps
the pointer mutable, requires constant initialization, and tells every consuming
TU no dynamic TLS initializer is needed. Scope restoration, atomics, all55
counter sites, search/eval/NNUE arithmetic, order, and network bytes are unchanged.
The v2 fixture's nm output contains defined current_bank but no weak TLS init
symbol. Every consumer must be rebuilt; profile.cpp-only rebuild is insufficient.

## RED, negative controls, GREEN, and retained failures

All C++ fixtures use GCC14.2, C++20, O2/g/DNDEBUG, H256/Profile, x86-64-v3,
znver5 tuning, strict floating point, ASan+UBSan/frame pointers, CPU0/nice19.
Runtime options retain `detect_leaks=1:abort_on_error=1` and
`halt_on_error=1:print_stacktrace=1`.

1. v1 two-TU fixture: compile0, run1, same profile.hpp store-null diagnostic.
2. Definition-only constinit negative: compile0, run1, same diagnostic. The
   external declaration must communicate the guarantee to consumers.
3. v2 initial fixture: compile0; first sandbox run and diagnostic run aborted at
   LeakSanitizer shutdown because its helper could not attach to its own main
   thread (EPERM). These failures and verbose logs are retained. No sanitizer
   was disabled. Approved fixture-only runs outside that command sandbox retain
   leak checking and pass with empty stderr.
4. Expanded v2 two-TU fixture: compile0/run0, empty stderr. Tests disabled-first
   entry, nested independent banks, disabled nested scopes, fresh workers starting
   null while a main-thread scope is active, worker restoration, main context
   isolation, overflow flag, and quiescent reset.
5. Broken-restoration negative: compile0/run1 with actual count assertion failures.
6. The old source contract expected the literal `thread_local Bank*`; applying it
   to valid v2 syntax failed one check. Its provisional GREEN-named log actually
   records that failure and is preserved with an explicitly FAILURE-named copy.
   NEW v2 source-contract test checks the required external constinit property:
   v1 RED1/6, v2 GREEN6/6. The OFF projection, real node/branch placements,
   runtime default, conditional CMake inclusion, and final-summary order pass.

Commands, return codes, unmodified stdout/stderr, and SHA256 are in this capsule.
No main engine was rerun, no full engine compiled, and no Git command was used.

## Patch and validation boundary

The new canonical engine-only patch applies and reverses using GNU patch-p1-F0
on independent tiny L/Lprime/B copies. Reversed original files match byte-exactly;
B accepts its existing three-line offsets with no fuzz. Original patch5c631 and
all original source trees remain unchanged. Documentation append patches from v1
still apply separately because no documentation bytes changed in this repair.

The source-only OFF projection is identical to the original. A new OFF ELF has
not yet been produced; canonical e3df remains an expected pin, not a new result.
Full v2 native qualification is PENDING a separate root grant: fresh Release ON
and ASan+UBSan builds, first bare11 before any UCI for each new ELF, all five
reference node counts11/13/16/20/22 (308972/745494/2460422/11901452/31111774),
full15 Lprime ON registered CTest (16 on qualified B), same four KNOWN/zero new
FAIL, FMA/strict-flags audit, and the already proposed perft4/25-WACx20k/T2 and
TT/correction/runtime sampling. Additional sampling does not replace fullCTest.
NPS is not a performance measurement in this correctness exercise. No v1 native
pass is transferred to the changed v2 ELF. Use a fresh v2 cache; do not mutate the
failed v1 ASAN cache or resume it as v2.
