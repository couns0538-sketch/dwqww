# Windows 6.4.17 promotion-recapture SEE candidate

Frozen source/tests: `47f0560221d986e41a309853e1295c557fcf5bf6`. Parent16 source: `553caef144ae2e1b696ba35d7a0eb1a50a03fde9`.
Exact69-file non-bytecode export. Only board.cpp, tests/tests.cpp and version labels differ.
All8headers, NNUE/eval/weights and other4testfiles match parent16.
Strict static LLVM-MinGW23.1.3 Zen5 build: one job, C++20 Release, no FMA/LTO/fast-math.
Build and all8Winechecks passed first attempt, including28mirroredSEEcases (56), zero-threshold
checks, full core/perft, TT8groups, rule50,18,947 legal-witness comparisons,UCI,ponder,5OwnBook.

ActualWindows17 bench11signature: 382424 nodes. Expectation was unknown before
execution; no native/prior count was imposed. Signature/source/PE/rawlog were frozen at
2026-10-20T20:07:06.087367+00:00, before package start 2026-10-20T20:07:06.276884+00:00; freeze is embedded in provenance/raw archive.

Independent audit attempt1 failed only a case-sensitive README wording assertion.
Original checker, failed trace/logs/command remain unchanged. Root authorized one exact
phrase casefold correction in a new copied checker; attempt2 passed all1,211checks.
Exactdiff/schema/provenance/checkerSHA are saved under independent-audit-scope-casefix*.
No engines reran and no source/package/PE/rawZIP/freeze bytes changed for that correction.
Final read-only ZIP/tree/SHA256SUMS/raw/source/parent/freeze verification passed.

Artifact `releases/forge-6.4.17-candidate-windows-zen5.zip` (10591760 bytes).
ZIP SHA256: `9c532d5394b58f8654e316de99b4a5771149e75327c31586ae179814212e85f9`.
ExactPE SHA256: `abfec902a99737df1855f2eb54e0267b4744d1f98b81a040b5b06220ab34ab7d`.
Core SHA256: `64967f5b6ce7daec378d9ce25275cc95eb817b7236b42e3430642208a4d9a86f`.
Raw archive SHA256: `7f3a177d074b65953b2f0693ead05eafae078c62ddaba28f2a5928adb533ad40`,165 originals retained.
All435preservedparent16files remain identical. Full source/all6PEs/core/builds/logs retained.
Outside source/build/package-capture paths are `/workspace/.cloud-setup/forge-promotion-windows-` plus
`source`, `build` and `package-capture`. No live Windows build/test/audit job remains.

Native17gates are independently reported by root; this Windows stage alone does not accept
candidate/release or establish NPS/Elo/native Windows/Ryzen gains. Original16TSan8/9 failure
and separate16five-case finite OwnBook diagnostic remain qualified. All own files now stable
for complete17archive; further source/docs/Git/ignore work belongs to root.
