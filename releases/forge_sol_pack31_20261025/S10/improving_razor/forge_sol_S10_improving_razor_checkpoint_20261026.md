# S10 ImprovingRazorGuard checkpoint — 2026-10-26

Decision: **REJECTED search screen; B qualification incomplete.** The unchanged original Lprime run failed the registered absolute20% node guard at d20 and solved270/300 in its only WAC ON screen, below283. The WAC run had0 illegal moves. No repeat, source tuning, speed claim or Elo claim.

Patch SHA256 `398a1bdac9606dea0b0b1b938dcd8e6ec7e6b8674435aee3584c3af6c8eda286`; frozen producer SHA256 `d6b8b9909373903e2ac3d2aca10e731acffeaff8352db8619d0577945f55b08b`. The hypothesis disabled razoring only while improving. Both build and UCI switches remain OFF by default.

|Depth|Lprime OFF|Lprime ON|B OFF|B ON|
|---|---:|---:|---|---|
|11|308972|301162|308972|301162|
|13|745494|785078|745494|UNVERIFIED; not run|
|16|2460422|2851256|2460422|UNVERIFIED; not run|
|20|11901452|9011938|11901452|UNVERIFIED; not run|
|22|31111774|25347487|UNVERIFIED; observer timeout|UNVERIFIED; not run|

Lprime Release and ASan/UBSan full configured CTest each passed14/14 with the four source-pinned known findings and zero new failures. Both Release perft5 counts matched4865609/193690690. Both profiles had scoped NNUE ELF/object FMA0. The compile-OFF8-production-TU proof passed. Actual ASan OFF/ON d11 matched308972/301162. The reviewed ON/T2 supplement passed three legal searches, one active marker before the first bestmove, artifact/source integrity, and observed unlimited RLIMIT_AS before/after without setting a limit.

B passed FIRST bare d11 before UCI and matched OFF d11/13/16/20. Its OFF d22 produced no completed benchmark summary before the frozen180-second observer deadline. The controller then terminated its owned process: receipt elapsed181.674795928s, returncode-15, empty stderr, complete capture, no remaining group members. That result is **FAIL for the bounded attempt**. B full Std, perft, FMA, ASan and T2 remain UNVERIFIED/not run. No source or timer was changed and no retry occurred. This observation establishes neither a spontaneous engine crash nor an Elo loss.

Original result SHAs: Lprime `8ee523a3a8316d5bfddb49ac15f57bd86d87bbdc494f99ab47c889b2822a6bfe`; B `c25a7580918ef7b82ab4c02450787d8269c7ca977b0ad27e2e596258d401fdc9`; Lprime T2 `afcdd5599d64c135df054fb18d6cc642ec4fb9a0daaec1d3e28ef400bd660762`.

The separate read-only resource observations preserve prior actual timings and a fresh quota/visible-workload snapshot. Quiet B OFF22 completed in107.121s; improving B OFF20 completed in63.510s. The timed-out d22 has no measured final node count/NPS/CPU time. Current cgroup quota4 CPUs does not reconstruct past scheduling. An initial sandbox process scan had access denials; zero visible owned processes was not evidence of idle state. The fresh escaped snapshot saw the live singular controller and its forge child, with0 read denials. No root cause or extrapolated d22 NPS is claimed. These standalone JSON records retain their exact original bytes:

- Resource observation SHA256 `46605fa73c22619e50bcf4fa45d77449efe15d76da490c4c4090a4fe28af8d36`.
- Visibility addendum SHA256 `c28eb6f38266aa0bdbf65da3b4afcaec906d50d8fdf66ddd9c079c985f5de363`.

The sealed data archive predates those sidecar observations and is unchanged: `forge_sol_S10_improving_razor_evidence_20261026.tar.gz`, 8430332 bytes, SHA256 `4b5322ac6ed3341604e771e6872c2ec0e5838b6bff99462b9b4679d1d8c4284e`. It preserves260 original data files/65,298,668 bytes. Python and GNU decoders verified all261 members including the original-to-member map; originals, binaries and caches remain intact locally. Mapping SHA256 `24bbcc0663fb25157f1645fdb71fa3944ef15e89d7a088f18265bf28eb487ffa`. No private source tree or build binary is packed.

Windows/owner-PC eligibility and playing strength remain UNVERIFIED. The next original frozen candidate is SingularSiblingLmr; its running case retains180 seconds per component. Any future runtime policy requires separate preregistration for an unstarted case and cannot rescue these past observations.
