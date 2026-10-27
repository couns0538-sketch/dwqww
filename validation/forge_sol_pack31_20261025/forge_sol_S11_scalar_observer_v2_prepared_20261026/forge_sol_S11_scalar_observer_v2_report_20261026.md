# S11 scalar observer v2 — source-only successor

The original LP parity attempt remains FAIL at its ISA precheck; its receipt is
7877d436b260d802035d98d497d715a3d8c218c20df4e0180ebb425ba8c67630.
No million-position oracle arm started. No result is rescued or relabeled here.
All completed Release and sanitizer results remain separate evidence.

Independent review35ed06dec1a3b115d574abab252b5157ecfe9613e193dbb3f87ba17ddadb8809
bound the original object bytes and disassembly. The two YMM operations are
VMOVDQA stores of the zeroed register to the64-byte stack-lane initializer. Four
XMM VBLENDVPS instructions perform bit selection around scalar comparisons and
clamps. The old observer treated any YMM reference and any remaining `ps` suffix
as numerical vector arithmetic, rejecting these non-arithmetic operations.

The new observer changes only verify_disassembly. Its other16 function/class
ASTs remain identical. It permits precisely these forms:

- VMOVDQA from a YMM register to `(%rsp)` or `0xHEX(%rsp)`.
- VBLENDVPS with exactly four XMM register operands.

Unknown wide opcodes, other transfer operands, YMM blends and memory blends
remain blocked. NNUE-wide FMA and ZMM rejection remains unchanged. Scalar float32
multiply/add evidence is still required, and packed numerical operations,
float64 and x87 arithmetic are still rejected. Every instruction is examined;
allowing a blend does not bypass later arithmetic checks. The revised claim is
**scalar float32 numerical arithmetic with enumerated bit-preserving transfers
and selections**, not an entirely scalar instruction sequence.

The actual old full capture and110-instruction excerpt give2 permitted stores,
4 selections,9 scalar multiplies and20 scalar additions. These are read-only
classifications of existing bytes, not new engine or parity execution.

The versioned consumer pins the new helper SHA before loading, at native entry,
and after a future run. It also pins the unchanged original FAIL receipt at all
those boundaries. Its eight existing helper/binding/corpus functions remain
AST-identical. Its main AST is identical after removal of exactly four explicit
pin/metadata statements. Engine code, compiler flags, source/build binding,
corpus, capture, byte comparison, retention, and1800/500/180-second limits remain
unchanged. The new result schema explicitly names observer_v2.

| Check | Status |
|---|---|
| Actual full/excerpt old observer | RED preserved,5 assertion failures/0 errors |
| Same16 observer tests with v2 | PASS |
| Original nine arithmetic negatives | Retained and passing as rejection controls |
| New after-blend/wide/transfer/selection negatives | PASS as rejection controls |
| Six dispatch/import/postflight/binding tests | PASS, pure/read-only |
| Actual old/new LP/B binding identity | Equal, no native execution |
| Engine/compiler/corpus/retention/timer changes | None |
| New native parity retry | UNVERIFIED; NOT RUN |
| Speed, Windows, Elo | UNVERIFIED; no claim |

The original sealed proof/consumer and failed attempt remain unchanged. Draft
controls and all original pure-test stdout/stderr are retained. New LP/B output
paths and commands are recorded in the dated preregistration. They require root
publication/review and a separate explicit first-case native grant.
