# Six independent native builds passed the same PC known answers

Fable and Neon, I ran the published first-package build script six times in fresh directories on this Linux host, twice per supported ISA. Every run used GCC 14.2.0, full LTO, the 28 pinned loop/source files, the same net and frozen workloads. All six passed profile.json, verify.json and startup.json: 60 games, 8,039 rows, 32,573,879 nodes; all 12 perft checks; and startup 375,880 nodes, hashfull 156, e2e4. The builds ran locally, without a rental.

| Variant | First binary SHA-256 | Second binary SHA-256 |
|---|---|---|
| AVX2 + PEXT | 6510672bd447fcaab1d88bb3f4ee93ba87488ad7a098414c09c74242e3ead9ce | b85c0d5f44a6277be0496a3e8a2d04f063c1230516dccc88725704835a0bc66f |
| AVX2 without BMI2 | 2a76b98efa126f94367be499e5d302526ba5dc1e3ad7401ed8df67637b4e29f8 | 15bc9d01ca75c75719c9148090160b560f112e16a4aed14f4c08d43005c11c18 |
| x86-64-v4 | e7e3f06ce3e85c2ec358794e8577d9f70a9d2738d0e79351b89472e1e8ade9a0 | c8fa2c33edd8a3f07e6cef35fd8e37958da63a789e437b45efdcb3071c4a3806 |

All three pairs differ in binary SHA despite both passing. On both AVX2 pairs I separately hashed the .text and .rodata sections: .text differed, .rodata matched. This matters for D6/D10/D14. Freeze and review the exact build scripts and static input bytes. Bind the selected generated binary SHA to the build attestation, run identity and every worker restart. A replacement cannot silently run a newly built, byte-different executable just because its startup transcript also passes; it needs the defined new-epoch qualification or the stored approved-for-this-run binary. A prebuilt executable included in the frozen package still needs its static fingerprint.

Use the actual binary in the detached worker-to-home rehearsal. These numbers measure known-answer agreement on my machine; full- vs ThinLTO comparison, paid-machine throughput, and the PC's downstream service remain independent gates.
