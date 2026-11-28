# 6-Patch Orthogonal Super-Stack Proof (`superstack_6patch.exe`)

**Summary:** All 6 orthogonal production patches applied cleanly (`6/6 RC=0` sequentially onto a fresh copy of `C:\nnue-lab\forge\r15dsg`), compiled cleanly with `clang++ 23.1.5` (`build_fast.py --jobs 4`, non-PGO), passed `run_master_gates.py --quick` (`hard_pass: true`) across **all 3** target neural networks (`r0067` 768w `FORGENN3`, `G3_FULL25 diag_e24` 1024w `FORGENN3-P`, and `G2` 1024w `FORGENN3-P`), and completed Clang UBSan (`-O1 -g -fsanitize=undefined -fno-sanitize-recover=all`) `bench 10` + `selfgame softnodes 1000` with **`0` undefined-behavior errors** (`RC=0`, `stderr` 0 bytes) across all 3 nets.

- **Compiled Executable:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\builds\superstack_6patch.exe` (`2,399,232` B, `SHA-256: 327F58F47050863F7A5A8CC61FF0EF79EA5692F12633D69909DBD88D20B7E87B`)
- **Machine-Readable Proof:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\superstack_6patch_proof.json`
- **r0067 Startpos Eval:** `info string eval hce 0 nnue 87 total 87`

---

## 1. Sequential `git apply` Verification (`6/6 RC=0`)

Applied sequentially in exact order to a temporary copy of `C:\nnue-lab\forge\r15dsg` (`_work_superstack`, deleted after verification):

| # | Patch Path | Bytes | SHA-256 | Sequential `git apply` |
|---:|---|---:|---|---|
| 1 | `C:\nnue-lab\neon\forge_fixes\patches\V3P_pairwise_psqt_fused_v3.patch` | `43,075` | `57F3455F185463CFA7859727DA9C6A91BCAADB3934DA4492A6E78029DCAAC763` | `RC=0` |
| 2 | `C:\nnue-lab\neon\forge_fixes\patches\SF33_qs_overhaul_SF13_plus_SF32.patch` | `2,236` | `6C6A32A6347692BA39F42FDE1C010CEE04EE0A52D724767F6FA56BA016C9A92E` | `RC=0` |
| 3 | `C:\nnue-lab\neon\forge_fixes\patches\SF8_conthist_6ply.patch` | `3,155` | `62DCF1F3DA0AC212A3807E59EB61E144B3705EA2A8A716B70A391E81AF4C8779` | `RC=0` |
| 4 | `C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamA_search\patches\proto_1_corrhist_minor.patch` | `7,602` | `E1CD152B4D78CD7880F55DD8967EB561FE246FE5773232CE22825DF5B2071B14` | `RC=0` |
| 5 | `C:\nnue-lab\neon\forge_fixes\patches\SF15_rfp_failsoft_blend.patch` | `501` | `826E49E15407EE62E528C86E41297D964C97D55AE88F58F8F2E2948669863B81` | `RC=0` |
| 6 | `C:\nnue-lab\neon\forge_fixes\patches\SF27_goodcap_caphist_see_threshold.patch` | `2,306` | `342E838E44A7326B550B4BE75998104926FA9E794D65C896CCB45C0FA4106826` | `RC=0` |

Build command (`RC=0`, `4.2s`):
```powershell
C:\nnue-lab\venv\Scripts\python.exe -B C:\nnue-lab\neon\forge_fixes\build_fast.py --src _work_superstack --out C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\builds\superstack_6patch.exe --jobs 4
```

---

## 2. Multi-Net `run_master_gates.py --quick` Verification (`3/3 hard_pass: true`)

| Net | Format | Gate JSON (`SHA-256`) | Overall Status | `hard_pass` | `perft 5` | `v3_parity` (120 FENs) | `Default b11/b13` | `B4 b11/b13` | `eval_net_full` | `loader_safety` |
|---|---|---|---|---|---:|---|---|---|---|---|
| `r0067` (`C:\nnue-lab\runs\forge\r0067\train\cand.fnn3`) | `FORGENN3` 768w | `superstack_6patch_r0067_gate.json` (`1D3046821FA0AE75EA09FEEA6630A547AAF4DAD275F29494D517BB5864C7B893`) | `PASS_WITH_ADVISORY_FLAGS` | `true` | `4,865,609` (`6/6`) | `0 cp` max diff (`8/8` OB) | `292,124 / 878,165` (`+21.10%` vs `base_r15dsg`) | `247,028 / 692,234` (`+9.50%` vs `base_r15dsg`) | `mse=0.01302`, `corr=0.7754` | `15/15` (`v3p=True`) |
| `G3_FULL25 diag_e24` (`C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e24\cand.fnn3`) | `FORGENN3-P` 1024w | `superstack_6patch_g3e24_gate.json` (`EDAE978444D0F7FF6BA4134B0F9CE1949E290130BAAA7BD741C8E198456ED9A3`) | `PASS` (0 advisory flags!) | `true` | `4,865,609` (`6/6`) | `0 cp` max diff (`8/8` OB) | `266,024 / 616,519` | `209,630 / 589,318` | `mse=0.01175`, `corr=0.7984` | `15/15` (`v3p=True`) |
| `G2` (`C:\nnue-lab\neon\forge_fixes\gpu_runs\G2_v3p_1024_pairwise_psqt\cand.fnn3`) | `FORGENN3-P` 1024w | `superstack_6patch_g2_gate.json` (`569A772C2F3AECD55134B5A3CB405DD29A1D38D8420ACDAF383F97FA4A96C80B`) | `PASS_WITH_ADVISORY_FLAGS` | `true` | `4,865,609` (`6/6`) | `0 cp` max diff (`8/8` OB) | `314,673 / 846,139` | `251,918 / 608,824` | `mse=0.01234`, `corr=0.7864` | `15/15` (`v3p=True`) |

*Note:* `r0067` used `--baseline-exe C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe`. The two `FORGENN3-P` 1024w nets (`G3_e24` and `G2`) omitted `--baseline-exe` (matching `v3p_fused_gate_G2.json` and `STACK_V3Pv3_SF13_SF8_W2P1_gate_full.json`) because `base_r15dsg.exe` lacks `V3P` support and intentionally rejects `FORGENN3-P` flag bits (`unknown flag bits`).

---

## 3. Clang UBSan Verification (`0` Errors Across `768w` & `1024w`)

Compiled inside temporary `_work_superstack` (removed after testing) with `clang++ 23.1.5`:
```text
clang++.exe -std=c++20 -O1 -g -fsanitize=undefined -fno-sanitize-recover=all
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1
  -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1
  -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1
  -march=znver5 -pthread --sysroot=C:\nnue-lab\tools\mingw64
  -stdlib=libstdc++ -rtlib=libgcc -unwindlib=libgcc -I_work_superstack\include _work_superstack\src\*.cpp
  -fuse-ld=lld -o _work_superstack\ubsan_superstack.exe
```

Executed with `Threads=1, Hash=16, OwnBook=false, HistRework=2, CorrHistV2=true, TtPruneV2=true, CuckooRep=true, LmrDeeperShallower=true`:

| Net | `RC` | UBSan `stderr` | `bench 10` | `selfgame softnodes 1000` |
|---|---:|---:|---|---|
| `r0067` (`768w`) | `0` | `0` bytes (`0` errors) | `info string bench depth 10 nodes 161639 time 104 nps 1554221` | `sgend result 0 reason plylimit plies 100 run 0 searches 100 nodes 195710` |
| `G3_FULL25 diag_e24` (`1024w`) | `0` | `0` bytes (`0` errors) | `info string bench depth 10 nodes 143649 time 111 nps 1294135` | `sgend result 0 reason drawadj plies 65 run 6 searches 66 nodes 121806` |
| `G2` (`1024w`) | `0` | `0` bytes (`0` errors) | `info string bench depth 10 nodes 128242 time 98 nps 1308591` | `sgend result 0 reason drawadj plies 75 run 6 searches 76 nodes 149820` |
