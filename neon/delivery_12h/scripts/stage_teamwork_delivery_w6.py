"""Stage verified Wave 6 curated text-only deliverables into C:\\nnue-lab\\teamwork\\.

SAFETY CONTRACT:
  - Defaults unconditionally to `--dry-run` (read-only; NEVER touches C:\\nnue-lab\\teamwork\\).
  - Mutually exclusive `--dry-run` / `--live` / `--verify-debate-index` modes.
  - NO `--allow-unfrozen` escape hatch.
  - Refuses `--live` (`RC=2`) unless BOTH:
      (a) `--confirm-quest-complete YES_COPY_TO_TEAMWORK`, AND
      (b) `HANDOFF_12H_DATA_QUALITY.md` has zero `[PENDING` / `[TRAINING` / `[TESTING` markers,
      AND missing == 0, pending_sibling == 0, immutable_mismatch == 0, forbidden_ext == 0,
      forbidden_path == 0, and (total_files_bytes + manifest_json_bytes) <= 1_887_436 (1.8 MiB).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True

LAB = Path(r"C:\nnue-lab")
DEFAULT_DEST = LAB / "teamwork" / "neon_12h_quest_delivery"
MAX_BUNDLE_BYTES = 1_887_436  # 1.8 MiB
HERE = Path(__file__).resolve().parent

LIVING_INDEX_PATHS = {
    (LAB / "neon" / "filter_quest" / "HANDOFF_12H_DATA_QUALITY.md").resolve(),
    (LAB / "neon" / "filter_quest" / "PHASE_B_METHODS_AND_DESIGN.md").resolve(),
    (LAB / "neon" / "forge_fixes" / "ALL_MATCHES_SCOREBOARD.md").resolve(),
    (LAB / "neon" / "forge_fixes" / "ALL_MATCHES_SCOREBOARD.json").resolve(),
    (LAB / "neon" / "filter_quest" / "STAGE2_FILTER_QUEST_SUMMARY.md").resolve(),
    (LAB / "neon" / "filter_quest" / "STAGE2_FILTER_QUEST_SUMMARY.json").resolve(),
}

FORBIDDEN_SUFFIXES = {
    ".exe",
    ".pt",
    ".fnn3",
    ".fqs",
    ".z",
    ".plain",
    ".pgn",
    ".npz",
    ".binpack",
    ".dll",
    ".lib",
    ".o",
    ".obj",
    ".pyc",
    ".part",
}

FORBIDDEN_DIR_NAMES = {"__pycache__", ".pytest_cache"}

MANIFEST: list[dict] = [
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\HANDOFF_12H_DATA_QUALITY.md",
        "dest_rel": "docs\\HANDOFF_12H_DATA_QUALITY.md",
        "sha256": "bae42cb53544dd3560fcc456decd5811d7a8afef4a084cb7ddafd7a293129e6a",
        "freeze_mutable": True
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\PHASE_A_BASELINE.md",
        "dest_rel": "docs\\PHASE_A_BASELINE.md",
        "sha256": "1e4acba0cbe744a0896991be898f92ec70f3913088591aa90af5ec0868be629f",
        "freeze_mutable": False
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\PHASE_B_METHODS_AND_DESIGN.md",
        "dest_rel": "docs\\PHASE_B_METHODS_AND_DESIGN.md",
        "sha256": "d8c81bc215a59ace988c2d9fd66240600d463193cb5419b44836fd34c0263f6b",
        "freeze_mutable": True
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\QUEST_DECLARATION.md",
        "dest_rel": "docs\\QUEST_DECLARATION.md",
        "sha256": "6e0f481cc3fd5fab01cdeaecbc47827099c79a315c456e46132a0fe68bb3baca",
        "freeze_mutable": False
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\EXPERIMENTS_DECLARED.md",
        "dest_rel": "docs\\EXPERIMENTS_DECLARED.md",
        "sha256": "204940b6de3b211cc4b68021a66c29008c729d3196aee0390ba4284b9a52f404",
        "freeze_mutable": False
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave2\\streamA_search\\COMBO_DIAGNOSIS.md",
        "dest_rel": "docs\\COMBO_DIAGNOSIS.md",
        "sha256": "8a7846faf723d686c89b857e8c6873d8d973864561ebd86d9f622d287a188ed7",
        "freeze_mutable": False
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave2\\streamB_nnue\\AUDIT_AND_TESTS.md",
        "dest_rel": "docs\\AUDIT_AND_TESTS.md",
        "sha256": "98feab0d083c240de3026e0368a77ea9ee334d2e4f4c65371d9505dabc1eb85c",
        "freeze_mutable": False
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave2\\streamB_nnue\\NNUE_G3_G4_DESIGN.md",
        "dest_rel": "docs\\NNUE_G3_G4_DESIGN.md",
        "sha256": "44b3b658190f99dae1dbf0354d2f6a87365fdca3491c533e6804b5b0fc3bf9b1",
        "freeze_mutable": False
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave2\\streamC_gates\\GATE_MATRIX.md",
        "dest_rel": "docs\\GATE_MATRIX.md",
        "sha256": "7c77d6efa8bc8c186aeecf4bf275b66da6346715a32f26eb720c5ecd2cfd0673",
        "freeze_mutable": False
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave3\\streamA_search_packets\\ROUND5_6_SUMMARY.md",
        "dest_rel": "docs\\ROUND5_6_SUMMARY.md",
        "sha256": "1f124ca4cd3906dcba038c87e7aae455677afd6da8375eb23961e041a4b3107a",
        "freeze_mutable": False
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamA_search_packets\\ROUND6_8_SUMMARY.md",
        "dest_rel": "docs\\ROUND6_8_SUMMARY.md",
        "sha256": "24470baa178af4ca627f13b3c5cb4e418efcf965b086d8f22062513b504c4094",
        "freeze_mutable": False
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamC_handoff_reaudit\\HANDOFF_REAUDIT_W4.md",
        "dest_rel": "docs\\HANDOFF_REAUDIT_W4.md",
        "sha256": "f023c7a9d4b43d9728f105fe3a41d81912cf5ce4d4a5a5a87a5036cb7c5bc54c",
        "freeze_mutable": False
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamC_handoff_reaudit\\PATCH_AUDIT_MATRIX_W4.md",
        "dest_rel": "docs\\PATCH_AUDIT_MATRIX_W4.md",
        "sha256": "0c9ef48d60f7e4dc068ff7ac044fdc71c21edacba9e6ed7613b541b3c66d4064",
        "freeze_mutable": False
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\ALL_MATCHES_SCOREBOARD.md",
        "dest_rel": "docs\\ALL_MATCHES_SCOREBOARD.md",
        "sha256": "da3b6568e7a1148af8285a196b777ae7507e6e9a63a5a200cf794f689187146c",
        "freeze_mutable": True
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\SERVER_DAY_ARCH_SCALING_BRIEF.md",
        "dest_rel": "docs\\SERVER_DAY_ARCH_SCALING_BRIEF.md",
        "sha256": "18bf483ce49e093c1ee2578776ed8b55013c36d5c42c7954275d3cae3b0027b0",
        "freeze_mutable": False
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\POST_G3_SPSA_RECIPE.md",
        "dest_rel": "docs\\POST_G3_SPSA_RECIPE.md",
        "sha256": "e168163d0d1c78ce1139ae22ab972135a4049b138cf78a4c0b42467a6417d543",
        "freeze_mutable": False
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamA_search_packets\\SUPERSTACK_6PATCH_PROOF.md",
        "dest_rel": "docs\\SUPERSTACK_6PATCH_PROOF.md",
        "sha256": "fdbd6779a156aa74edf71c95511f0c93a269fdbfb1f339e8afebf41ab963109c",
        "freeze_mutable": True
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamB_serverday_v2\\SERVER_DAY_V2_RUNBOOK.md",
        "dest_rel": "docs\\SERVER_DAY_V2_RUNBOOK.md",
        "sha256": "d191a144d383191392d6b67bd1ebc74cfd8df917bfaee928e02ed8d1bc7fe1d2",
        "freeze_mutable": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave3\\streamA_search_packets\\packets\\packet_SF17_SF18_tm.md",
        "dest_rel": "packets\\packet_SF17_SF18_tm.md",
        "sha256": "ea12ec3fee36134a446c9631305553bc96b4d4d41241c422d8fce4fc635410b9",
        "freeze_mutable": False
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave3\\streamA_search_packets\\packets\\packet_SF20_killer_lmr_relief.md",
        "dest_rel": "packets\\packet_SF20_killer_lmr_relief.md",
        "sha256": "e3486adf8e3f6971c3a155e15425da61e9d0ea6cc1b80f6cf5328a15c6d0d436",
        "freeze_mutable": False
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamA_search_packets\\packets\\packet_SF21_corrhist_gravity_clean.md",
        "dest_rel": "packets\\packet_SF21_corrhist_gravity_clean.md",
        "sha256": "27c70bb5aa89d5feda74ef7d2e589e326c3a545ac9750b1f1cb131c891aaa97c",
        "freeze_mutable": False
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamA_search_packets\\packets\\packet_SF22_low_ply_history.md",
        "dest_rel": "packets\\packet_SF22_low_ply_history.md",
        "sha256": "07ddbec815dfc00bca40cd1110a99f7ab48d50eb6b65d74ef28f220b66e58fd9",
        "freeze_mutable": False
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamA_search_packets\\packets\\packet_SF23_capture_hist_badcap_lmr.md",
        "dest_rel": "packets\\packet_SF23_capture_hist_badcap_lmr.md",
        "sha256": "b7ecdd1261fab6e184a47a2f3842b93bf745804e9908ba2d01c6db2d1f82e95f",
        "freeze_mutable": False
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamA_search_packets\\packets\\packet_SF24_qs_evasion_pruning.md",
        "dest_rel": "packets\\packet_SF24_qs_evasion_pruning.md",
        "sha256": "9f21dc57d81156e74c7902f97af033dd729a07bd1358e38df9f1837fc64e3226",
        "freeze_mutable": False
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamA_search_packets\\packets\\packet_SF25_faillow_prior_move_hist.md",
        "dest_rel": "packets\\packet_SF25_faillow_prior_move_hist.md",
        "sha256": "1b77cd24d44dc193157384e6d0f5e02021f1c0ef1ca597bd0aa6cf28dd9862a2",
        "freeze_mutable": False
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamA_search_packets\\packets\\packet_SF26_cutoff_surprise_hist_depth.md",
        "dest_rel": "packets\\packet_SF26_cutoff_surprise_hist_depth.md",
        "sha256": "b4d544b9ddeec687fb57ef667315fcc268dc6cdb9d3e097313acb6cb2c80b92a",
        "freeze_mutable": False
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamA_search_packets\\packets\\packet_proto_7_ttpv_lmr_and_iir.md",
        "dest_rel": "packets\\packet_proto_7_ttpv_lmr_and_iir.md",
        "sha256": "ccad82c120554a13eb2e9bde261bac6c2991f717c20ba802fd2058ef316cb385",
        "freeze_mutable": False
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamA_search_packets\\packets\\packet_proto_8_eval_lmp_and_capfut.md",
        "dest_rel": "packets\\packet_proto_8_eval_lmp_and_capfut.md",
        "sha256": "2c2dec7f5469dc0029587735cdb9d2187a95e59452861b822471c7ae3eed82fc",
        "freeze_mutable": False
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\PACKET_SF13_QS_EVASION_PRUNING.md",
        "dest_rel": "packets\\PACKET_SF13_QS_EVASION_PRUNING.md",
        "sha256": "545d4c76114cee8144818d4e8c51a391a8d8ed6e5d567e1e4b2200cceaf601ea",
        "freeze_mutable": False
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\PACKET_SF15_RFP_FAILSOFT_BLEND.md",
        "dest_rel": "packets\\PACKET_SF15_RFP_FAILSOFT_BLEND.md",
        "sha256": "39dec1f3e61e7ef72a6c6a21f40d1c9473f6bda66f007c362dbbbe41f088dcf0",
        "freeze_mutable": False
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\PACKET_SF27_GOODCAP_CAPHIST_SEE.md",
        "dest_rel": "packets\\PACKET_SF27_GOODCAP_CAPHIST_SEE.md",
        "sha256": "2e4710dcfff9617ce2d7c4e5f5896f5a7191a83f4ea57300b7e9a4810d076bb7",
        "freeze_mutable": False
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\PACKET_SF32_QS_SEE1_FUTILITY.md",
        "dest_rel": "packets\\PACKET_SF32_QS_SEE1_FUTILITY.md",
        "sha256": "f4c02da77841a86872a67a29eac0ac9bd2b5d48998d8dde4e7b49e7b39a2bb07",
        "freeze_mutable": False
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamA_search_packets\\packets\\packet_SF28_qs_evasion_tight_and_standpat_ttpv.md",
        "dest_rel": "packets\\packet_SF28_qs_evasion_tight_and_standpat_ttpv.md",
        "sha256": "4f5df08bb05b03d4ef4128afcd8fabbd7e7b817e03b0d571f202f10ec3a9f552",
        "freeze_mutable": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamA_search_packets\\packets\\packet_SF29_lmr_pv_ext_and_eval_diff.md",
        "dest_rel": "packets\\packet_SF29_lmr_pv_ext_and_eval_diff.md",
        "sha256": "2ffac7a8f582b82c7af5957ccfb79b8add4d086ea4391b235531cfb9d6780552",
        "freeze_mutable": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamA_search_packets\\packets\\packet_SF30_probcut_tt_and_corrhist_promo_fix.md",
        "dest_rel": "packets\\packet_SF30_probcut_tt_and_corrhist_promo_fix.md",
        "sha256": "1ade4eaa9ca2642c82bb424fedfab55ed90be6478b246fbc2ebc264fe72c30ef",
        "freeze_mutable": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamA_search_packets\\packets\\packet_SF31_singular_triple_ext_and_neg_ext.md",
        "dest_rel": "packets\\packet_SF31_singular_triple_ext_and_neg_ext.md",
        "sha256": "6609580c42f2abeee5463c31c96586284e95251a43fca623fd4543e70e7ae483",
        "freeze_mutable": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamA_search_packets\\packets\\packet_SF33_qs_overhaul_SF13_plus_SF32.md",
        "dest_rel": "packets\\packet_SF33_qs_overhaul_SF13_plus_SF32.md",
        "sha256": "45bd82c20776cb4c1e9c75aab2f2997e4dbe78d8a7d49370173a8bfb42955ae9",
        "freeze_mutable": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamA_search_packets\\packets\\packet_proto_9_corr_complexity_rfp_lmr.md",
        "dest_rel": "packets\\packet_proto_9_corr_complexity_rfp_lmr.md",
        "sha256": "a1bc61ace06c5f8b66f6ef63679843163b5e86c57018b14bb4ba6bc1dab5b8a1",
        "freeze_mutable": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamA_search_packets\\packets\\packet_proto_10_cutnode_history_and_cap_lmr.md",
        "dest_rel": "packets\\packet_proto_10_cutnode_history_and_cap_lmr.md",
        "sha256": "fec97e031dd107aaec1402a90414a2cf16a9b7b4ef9421fbb4e44b55b0c76aa6",
        "freeze_mutable": True
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\V3P_pairwise_psqt_fused_v3.patch",
        "dest_rel": "patches\\V3P_pairwise_psqt_fused_v3.patch",
        "sha256": "57f3455f185463cfa7859727da9c6a91bcaadb3934da4492a6e78029dcaac763",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\STACK_V3Pv3_SF13_SF8_W2P1.patch",
        "dest_rel": "patches\\STACK_V3Pv3_SF13_SF8_W2P1.patch",
        "sha256": "f441957d44396bd022bbdb0dc723416af23d0921c5230d3aa3926431bccff0d8",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\datagen_uci_cc0_parity.patch",
        "dest_rel": "patches\\datagen_uci_cc0_parity.patch",
        "sha256": "5b8bba1c416bad446437c2415573428b04c8ea5952be1af403cfef3a6ba1726d",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\datagen_uci_startpos_only.patch",
        "dest_rel": "patches\\datagen_uci_startpos_only.patch",
        "sha256": "c0c92cb75a56b8a5e0d9670befd6509e21a912ac6facf2124e62e1734494eba8",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\datagen_uci_parity_7_8_minimal.patch",
        "dest_rel": "patches\\datagen_uci_parity_7_8_minimal.patch",
        "sha256": "184c6d2b8f880a7a22d23667e5b9ab38df53037c9736e14a115c84b9efa556c7",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave2\\streamB_nnue\\train_v3p_g3_flags.patch",
        "dest_rel": "patches\\train_v3p_g3_flags.patch",
        "sha256": "4c479d27d742029a737aa7225a8bc1017d990aadb29d1a062fa1f20c169cb51d",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\patches\\cache_key_t149.patch",
        "dest_rel": "patches\\cache_key_t149.patch",
        "sha256": "21180473548d5a15e640882de745239968689fc9f0e17274cec3939c55699088",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\patches\\filterqc_integrity_telemetry.patch",
        "dest_rel": "patches\\filterqc_integrity_telemetry.patch",
        "sha256": "0ade663d66a1f95fb5b34cf7a6c0fca5d4a94ddae37ae1530ccac591cf00546d",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\patches\\selfgame_skipcheck_optin.patch",
        "dest_rel": "patches\\selfgame_skipcheck_optin.patch",
        "sha256": "424190468df17483519dd388afdd26d538cb4446923858b900300bd7808dc1c7",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF8_conthist_6ply.patch",
        "dest_rel": "patches\\SF8_conthist_6ply.patch",
        "sha256": "62dcf1f3da0ac212a3807e59eb61e144b3705ea2a8a716b70a391e81af4c8779",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF13_qs_evasion_pruning.patch",
        "dest_rel": "patches\\SF13_qs_evasion_pruning.patch",
        "sha256": "63eb3288af4712a7d641035177e561448e6fc94041d8ee916776ab3fced6b6e4",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF15_rfp_failsoft_blend.patch",
        "dest_rel": "patches\\SF15_rfp_failsoft_blend.patch",
        "sha256": "826e49e15407ee62e528c86e41297d964c97d55ae88f58f8f2e2948669863b81",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF32_qs_see1_futility_pruning.patch",
        "dest_rel": "patches\\SF32_qs_see1_futility_pruning.patch",
        "sha256": "57ed10e7cf383d2345fdab6c41214ddda938f53d32bfdd374483d78e16a31b7b",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF33_qs_overhaul_SF13_plus_SF32.patch",
        "dest_rel": "patches\\SF33_qs_overhaul_SF13_plus_SF32.patch",
        "sha256": "6c6a32a6347692ba39f42fde1c010cee04ee0a52d724767f6fa56ba016c9a92e",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave2\\streamA_search\\patches\\proto_1_corrhist_minor.patch",
        "dest_rel": "patches\\proto_1_corrhist_minor.patch",
        "sha256": "e1cd152b4d78cd7880f55dd8967eb561fe246fe5773232ce22825df5b2071b14",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave2\\streamA_search\\patches\\SF6b_quiet_only.patch",
        "dest_rel": "patches\\SF6b_quiet_only.patch",
        "sha256": "56feb2fd7a7815c19b8bbadd809211a8061cfc73957c1eec41c5101d6b8f182d",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF6_lmr_fractional_caphist.patch",
        "dest_rel": "patches\\SF6_lmr_fractional_caphist.patch",
        "sha256": "41f598471de6bf600fee0e837bd907ba32e5db5370207ff489f48b1aa4d74337",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF9_minor_corrhist_conservative.patch",
        "dest_rel": "patches\\SF9_minor_corrhist_conservative.patch",
        "sha256": "2e79f0c92e188e3b178c78b1219c62086e660977422003f1199aaace7413caca",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF14_lmr_ttpv_cutnode_ext.patch",
        "dest_rel": "patches\\SF14_lmr_ttpv_cutnode_ext.patch",
        "sha256": "8b2208d07d14090dfe5759126c0870a87fb4faa6036ce84c8fce7a61da29830d",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF17_tm_bestmove_avg_eval.patch",
        "dest_rel": "patches\\SF17_tm_bestmove_avg_eval.patch",
        "sha256": "d7aaf51cde99336b021a87f38bab7b119a702f5cb96cd036d8bedd8ccfb7b88c",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF18_tm_ply_curve.patch",
        "dest_rel": "patches\\SF18_tm_ply_curve.patch",
        "sha256": "4b87a33856f12c14336323e102fbb62ea42ef2497873065c1f4b86cfe4f2f041",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\COMBO_v2_SF8_SF13.patch",
        "dest_rel": "patches\\COMBO_v2_SF8_SF13.patch",
        "sha256": "98840d3606ef5f77a3555e69fd6f19fecee9682cb07aa470f58f17968cc6ae5d",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF19_capture_history_see_prune.patch",
        "dest_rel": "patches\\SF19_capture_history_see_prune.patch",
        "sha256": "e4ee3e9039d0b5c1110e1788938ee11e732828bfb2d820a49f135cb91e3deb3f",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF20_killer_lmr_relief.patch",
        "dest_rel": "patches\\SF20_killer_lmr_relief.patch",
        "sha256": "44b74785d72c119a5f22d09b33a63226379d08c36d5fec0542f71d088246c825",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF21_corrhist_gravity_clean.patch",
        "dest_rel": "patches\\SF21_corrhist_gravity_clean.patch",
        "sha256": "157a5407d4b029ffc967c470c3c4b8c0e3bd00986a4c27def1c3c7b796712a72",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF22_low_ply_history.patch",
        "dest_rel": "patches\\SF22_low_ply_history.patch",
        "sha256": "83d26808e1251d2d19aaa7fbf2c31f62b3643efc9b3cf7b0d7347ee2da9e6229",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF23_capture_hist_badcap_lmr.patch",
        "dest_rel": "patches\\SF23_capture_hist_badcap_lmr.patch",
        "sha256": "a9f015d28ba40fb0bd262f68ebc2fc77cb744338e173872654860d6b7da66698",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF24_qs_evasion_pruning.patch",
        "dest_rel": "patches\\SF24_qs_evasion_pruning.patch",
        "sha256": "0d7fedfd0a7c8324fd6db421db3c2026070e1c13d08025a2916bb0659b3d5a8c",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF25_faillow_prior_move_hist.patch",
        "dest_rel": "patches\\SF25_faillow_prior_move_hist.patch",
        "sha256": "4617216e6cddb66052ba5b01174a19600e714b0195f75b345efa1a7c1cdb1996",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF26_cutoff_surprise_hist_depth.patch",
        "dest_rel": "patches\\SF26_cutoff_surprise_hist_depth.patch",
        "sha256": "20875f4e37743df312274458ef07e20fb1c3018ef24f9fec7bf1a687c106fdf9",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF27_goodcap_caphist_see_threshold.patch",
        "dest_rel": "patches\\SF27_goodcap_caphist_see_threshold.patch",
        "sha256": "342e838e44a7326b550b4be75998104926fa9e794d65c896ccb45c0fa4106826",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF28_qs_evasion_tight_and_standpat_ttpv.patch",
        "dest_rel": "patches\\SF28_qs_evasion_tight_and_standpat_ttpv.patch",
        "sha256": "45252132c8615e269c667b97fc10b1d77c01648fb505723afea3af4e7dee7b77",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF29_lmr_pv_ext_and_eval_diff.patch",
        "dest_rel": "patches\\SF29_lmr_pv_ext_and_eval_diff.patch",
        "sha256": "d89dcd817b9930abafd43b56256bfb446b76660377c1f45bdaf2c5e66b59679e",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF30_probcut_tt_and_corrhist_promo_fix.patch",
        "dest_rel": "patches\\SF30_probcut_tt_and_corrhist_promo_fix.patch",
        "sha256": "092f8f2145eb5cabf916baeb495afdd995fbcb0d737c310ba8c55eca1cc3960f",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF31_singular_triple_ext_and_neg_ext.patch",
        "dest_rel": "patches\\SF31_singular_triple_ext_and_neg_ext.patch",
        "sha256": "51dd9dcc0736019018246cadb7d196dbf034e90f85a91dee4a2c1a5fd5358e03",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF34_tactical_cutoff_quiet_malus_and_prior_refute.patch",
        "dest_rel": "patches\\SF34_tactical_cutoff_quiet_malus_and_prior_refute.patch",
        "sha256": "056b3bae0db5193ebff6d7f4cd0a0d72e6646c8a56fc2fe40c08b3d53946b325",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF35_razoring_d3_quadratic_and_nmp_minply.patch",
        "dest_rel": "patches\\SF35_razoring_d3_quadratic_and_nmp_minply.patch",
        "sha256": "4cd9f3953d840e249c1a2c397debb5b6fb0cd684f4c45f702e296b40af8aec5a",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF36_threat_quiet_move_ordering.patch",
        "dest_rel": "patches\\SF36_threat_quiet_move_ordering.patch",
        "sha256": "7a07741e601136ee2fc0c5066e05a677516d4b901df5de93c02e883e748963d6",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF38_corrhist_major.patch",
        "dest_rel": "patches\\SF38_corrhist_major.patch",
        "sha256": "02cc557e461d40ec2f1cf368230446ab4f522e31cf360012a3b6a02e1b417490",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF39_corrhist_minor_plus_major.patch",
        "dest_rel": "patches\\SF39_corrhist_minor_plus_major.patch",
        "sha256": "4160fef92c8c4f42b5e4c75f676d66532b6be696d63c60d2c7f9325e62563ee5",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\SF40_tt_recency_pv_admit_and_pv_conthist.patch",
        "dest_rel": "patches\\SF40_tt_recency_pv_admit_and_pv_conthist.patch",
        "sha256": "16dd427a387abb59a828a7eeb545032e1de6166ec691e93fff99b92532115c62",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave3\\streamA_search_packets\\patches\\proto_5_hist_malus_lmp.patch",
        "dest_rel": "patches\\proto_5_hist_malus_lmp.patch",
        "sha256": "c4d9336f1e347894056269cf7418520e65304ca874ffcec62c5d303044cf8be8",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave3\\streamA_search_packets\\patches\\proto_6_nmp_probcut_refine.patch",
        "dest_rel": "patches\\proto_6_nmp_probcut_refine.patch",
        "sha256": "9a7a0bf51b9548f07ba4ee670b6353fd02e053f2686ed2129f248a5478a4b824",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamA_search_packets\\patches\\proto_7_ttpv_lmr_and_iir.patch",
        "dest_rel": "patches\\proto_7_ttpv_lmr_and_iir.patch",
        "sha256": "6f08b20178def1d47c4c5c40cd1fd983426331d7d64a8b02cc86835dd9cb7bcb",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamA_search_packets\\patches\\proto_8_eval_lmp_and_capfut.patch",
        "dest_rel": "patches\\proto_8_eval_lmp_and_capfut.patch",
        "sha256": "1862cea0b89387be43bef0a74be9cda2bbf2a41ab6e3921406f93b385e62af63",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamA_search_packets\\patches\\proto_9_corr_complexity_rfp_lmr.patch",
        "dest_rel": "patches\\proto_9_corr_complexity_rfp_lmr.patch",
        "sha256": "776b26a2b2717eb5c8520adfec1cc348c03110f5f2ef8914f26887a0185915f1",
        "freeze_mutable": True
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamA_search_packets\\patches\\proto_10_cutnode_history_and_cap_lmr.patch",
        "dest_rel": "patches\\proto_10_cutnode_history_and_cap_lmr.patch",
        "sha256": "528028eb7566422d677004cfdf7d049326122ccacad74f39e675911ffd31bc46",
        "freeze_mutable": True
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\v3p_surface4a_v3_parity.patch",
        "dest_rel": "patches\\v3p_surface4a_v3_parity.patch",
        "sha256": "29d2af4dd4601312889215cbef8f08977d71d9a55d65f0023880b7013b41c777",
        "freeze_mutable": False
    },
    {
        "category": "patches",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\patches\\v3p_surface4b_v3_model_check.patch",
        "dest_rel": "patches\\v3p_surface4b_v3_model_check.patch",
        "sha256": "68572e4546a453def301c8e163ab3470b49ae1dc7af8e40b723f651aa708589c",
        "freeze_mutable": False
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\partition_fqs_buckets.py",
        "dest_rel": "scripts\\partition_fqs_buckets.py",
        "sha256": "5ed379ec05d403a29880dec22c0bf572ed4e921ce95b16539e3104ba7a16457e",
        "freeze_mutable": False
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\verify_syzygy_heldout_integrity.py",
        "dest_rel": "scripts\\verify_syzygy_heldout_integrity.py",
        "sha256": "f30f8c7d9a44275261615ebae4eb4796b7e27beb0d3260ac7a32c9b049b61d21",
        "freeze_mutable": False
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\train_v3p_stream.py",
        "dest_rel": "scripts\\train_v3p_stream.py",
        "sha256": "441bb3cb0dbc79ff24c0d7db16c98ecfc061bc90b46dde2675202a04e2dab6be",
        "freeze_mutable": False
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\run_post_g3_pipeline.py",
        "dest_rel": "scripts\\run_post_g3_pipeline.py",
        "sha256": "2a2eb47c1340d33d544be13d61d2e88ad1ed58cdd1843b364cc44239d2ae9f84",
        "freeze_mutable": False
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamB_linux_serverday\\linux_guards.py",
        "dest_rel": "scripts\\linux_guards.py",
        "sha256": "0c160fe3f0818f973f53087421e887b2e0fa42f8756b5742b8f07e5b37935758",
        "freeze_mutable": False
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamB_linux_serverday\\run_datagen_epyc.sh",
        "dest_rel": "scripts\\run_datagen_epyc.sh",
        "sha256": "792dbfc43c165f7d5dc5753e023191a16509f7afaa0b91bba2694fef4691503b",
        "freeze_mutable": False
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamB_linux_serverday\\run_dedup_buckets.sh",
        "dest_rel": "scripts\\run_dedup_buckets.sh",
        "sha256": "7c9aa6e15545952e62ca19094f670799dfd4a3f574bbe9831e75a842e39639a8",
        "freeze_mutable": False
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamB_linux_serverday\\run_train_stream_gpu.sh",
        "dest_rel": "scripts\\run_train_stream_gpu.sh",
        "sha256": "c0bdc534ba6003f6329202eea38bdc367f53e45156b0506ed78b273902e0a545",
        "freeze_mutable": False
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gen_cc0_selfgame_fqs.py",
        "dest_rel": "scripts\\gen_cc0_selfgame_fqs.py",
        "sha256": "d4b5411166d6445fbf00d6a1a1c373e055d73ef25eeb521afec2f6a93a7f2f8a",
        "freeze_mutable": False
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\rescore_fqs_selective.py",
        "dest_rel": "scripts\\rescore_fqs_selective.py",
        "sha256": "726f24b4c3a0cccd0dee81f8eb22363f5c71ee4adcf905e1114dbd6ae164b61d",
        "freeze_mutable": False
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\forge_v3p.py",
        "dest_rel": "scripts\\forge_v3p.py",
        "sha256": "9c649326b775372a753354e19429f72e4262bfb5dc04e265812c5adcaddb81f0",
        "freeze_mutable": False
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\train_v3p.py",
        "dest_rel": "scripts\\train_v3p.py",
        "sha256": "d93bae73a621eff48d86c585992f97794efec19f2d748bb6f57877691192953d",
        "freeze_mutable": False
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\server_day_streaming_filter.py",
        "dest_rel": "scripts\\server_day_streaming_filter.py",
        "sha256": "6d322dd82eebf4eb7859a602d4fd12c6590b12ff78ec14a3df3f97208cb17f98",
        "freeze_mutable": False
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\filter_fqs_to_fqs.py",
        "dest_rel": "scripts\\filter_fqs_to_fqs.py",
        "sha256": "41269e9be0f28984ea8a5fe599ef22c86a039f5a61131e1bf15a5d5cf72e814e",
        "freeze_mutable": False
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamB_serverday_v2\\run_datagen_epyc_v2.sh",
        "dest_rel": "scripts\\run_datagen_epyc_v2.sh",
        "sha256": "31faaedc3b1d41cdd7fd76b76498d70ecd9070757719f761e832b7daf64fbc06",
        "freeze_mutable": True
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamB_serverday_v2\\run_train_stream_gpu_v2.sh",
        "dest_rel": "scripts\\run_train_stream_gpu_v2.sh",
        "sha256": "86605fd05914ce6f1e6f444835410b337c107ed1c5d75b1a9d72eac3d740b42e",
        "freeze_mutable": True
    },
    {
        "category": "tests",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamB_linux_serverday\\tests\\test_bucketed_dedup_and_stream_fixes.py",
        "dest_rel": "tests\\test_bucketed_dedup_and_stream_fixes.py",
        "sha256": "291ddffb851eb69a05dbf36312fbc2301cf6b9a2e5407c01de23a4ea225d9a61",
        "freeze_mutable": False
    },
    {
        "category": "tests",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamA_search_packets\\tests\\test_round9_11_and_wave5_search.py",
        "dest_rel": "tests\\test_round9_11_and_wave5_search.py",
        "sha256": "c216bb9dee911d59d3205072c3c01c632cb667dff58e5603358840bf2dde5140",
        "freeze_mutable": True
    },
    {
        "category": "tests",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamB_serverday_v2\\tests\\test_serverday_v2_pipeline.py",
        "dest_rel": "tests\\test_serverday_v2_pipeline.py",
        "sha256": "328b2cb8a342cc0dc3faeccb4d77b666491ee721aed17ac58d9aa930b4749b84",
        "freeze_mutable": True
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\ALL_MATCHES_SCOREBOARD.json",
        "dest_rel": "audits\\ALL_MATCHES_SCOREBOARD.json",
        "sha256": "f57ea1995eba481d726b14b9628bf4c633f0177bae250eaabbfa78fb93a7fd0f",
        "freeze_mutable": True
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\LIVE_LOOP_PARITY_BIAS_AUDIT.json",
        "dest_rel": "audits\\LIVE_LOOP_PARITY_BIAS_AUDIT.json",
        "sha256": "cc0a0aeed348afa5336bd3b343b1a59cc1cb52297cd0173fe1690b8ca437aa93",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\COLOR_AND_OUTCOME_SYMMETRY.json",
        "dest_rel": "audits\\COLOR_AND_OUTCOME_SYMMETRY.json",
        "sha256": "a3b4d88c3a09a23bab5a64746eb93ae488a2bcb6cd8cf210b3980ac9e80cc790",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\PARITY_FIX_PILOT_4K.json",
        "dest_rel": "audits\\PARITY_FIX_PILOT_4K.json",
        "sha256": "b4dcbaf6be8b0af4e3e019bfaa45fd5984f4dcc711f7100b030358a368371a7d",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\WDL_CALIBRATION_AUDIT.json",
        "dest_rel": "audits\\WDL_CALIBRATION_AUDIT.json",
        "sha256": "fc603ac498a51b213a2c1733abc9cabbe4785d0974e54b15047da9185160f5ba",
        "freeze_mutable": True
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\OPENING_AND_KB16_DIVERSITY.json",
        "dest_rel": "audits\\OPENING_AND_KB16_DIVERSITY.json",
        "sha256": "0b24f075f2490a2b4faeaad5352c3010776cad7965bf4914d6653b09cf989c87",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\CROSS_SPLIT_LEAKAGE_AUDIT.json",
        "dest_rel": "audits\\CROSS_SPLIT_LEAKAGE_AUDIT.json",
        "sha256": "7c879c6e0376db5b5b105df56f7588b2d3ed6cc2a7362b8f5caa83dabc9a75ea",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\SERVER_DAY_COST_MODEL.json",
        "dest_rel": "audits\\SERVER_DAY_COST_MODEL.json",
        "sha256": "152cd19e9975d03b2692bb4c5c32a682e9e6287f17e2d66c1ce0a8d843527353",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\SF19_ERROR_TAXONOMY.json",
        "dest_rel": "audits\\SF19_ERROR_TAXONOMY.json",
        "sha256": "c5005018523204225a2dab4cbeae06710f0ebb5b7baae14b29fea077bc7dee44",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\G3_SCALING_TRAJECTORY.json",
        "dest_rel": "audits\\G3_SCALING_TRAJECTORY.json",
        "sha256": "b6da207e315114db7677f753feb70f8586520180b04fd5d1e8393f2aa39abc8a",
        "freeze_mutable": True
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\G3_RESIDUAL_BLUNDER_DIAGNOSIS.json",
        "dest_rel": "audits\\G3_RESIDUAL_BLUNDER_DIAGNOSIS.json",
        "sha256": "8f6ab3f92df1eee85b557e53ce37e00f55fc1247a7d0526edd2d3f42928cb4c7",
        "freeze_mutable": True
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\G3_QUIET_BLUNDER_DEPTH_PROBE.json",
        "dest_rel": "audits\\G3_QUIET_BLUNDER_DEPTH_PROBE.json",
        "sha256": "9e14d65f14cd9980e8645bb2c13322b833d486a395098dcb40d07035c1aeeb1a",
        "freeze_mutable": True
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\V3P_FUSED_V3_VERIFY_PROOF.json",
        "dest_rel": "audits\\V3P_FUSED_V3_VERIFY_PROOF.json",
        "sha256": "8bdfbb7300a84076b566dd53af5773b1c26013fc216e2266631987ff6c522ade",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\UBSAN_STACK_PROOF.json",
        "dest_rel": "audits\\UBSAN_STACK_PROOF.json",
        "sha256": "edaf038fbe39d68022350939db27e965eca66dd3cd53abec46d1b67f041b53f2",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\MULTITHREAD_STRESS_PROOF.json",
        "dest_rel": "audits\\MULTITHREAD_STRESS_PROOF.json",
        "sha256": "d10a41ccefce83405d1558434c318b29424a63fc2ef6814201ac9271a3b0fa7a",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\V3P_FUSED_BITEXACT_PROOF.json",
        "dest_rel": "audits\\V3P_FUSED_BITEXACT_PROOF.json",
        "sha256": "de2eeea0e7978f26d68ee9b11980e6ed1f66b4021870820876fd4ad632dc3855",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\V3P_FUSED_V3_REPORT.json",
        "dest_rel": "audits\\V3P_FUSED_V3_REPORT.json",
        "sha256": "230faae8b814b0b32ee9765b391fcc776ef839e5e3ae55409e10aff1619ad0eb",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\V3P_WIDTH_SCALING.json",
        "dest_rel": "audits\\V3P_WIDTH_SCALING.json",
        "sha256": "2077c3adaebd6ac7efd5f015142defc6631dc69e3c0634222ab7756ab9fac740",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\V3P_KB16_FEASIBILITY.json",
        "dest_rel": "audits\\V3P_KB16_FEASIBILITY.json",
        "sha256": "9c91cf72b3394fa9b2a3857c51f07bfce2bbb197fb56dae4e0c79bed45da5f04",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\baseline_r0067_scorecard.json",
        "dest_rel": "audits\\baseline_r0067_scorecard.json",
        "sha256": "13950486c75e3edc80ec32f4ac960b45d24a6a89b7f5c388fbfd76362e1675c2",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\stm_bias_root_cause.json",
        "dest_rel": "audits\\stm_bias_root_cause.json",
        "sha256": "aec3965fc204436d5f7032aa9aab7aab1d4d46dfaed03cb7f4b6f43a1bd4f81b",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\cc0_book_audit.json",
        "dest_rel": "audits\\cc0_book_audit.json",
        "sha256": "1da807bea16ce832088e1fc0d4dc419ace521d223cbf283f775913228d03f9e0",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\book_cc0_clean_meta.json",
        "dest_rel": "audits\\book_cc0_clean_meta.json",
        "sha256": "afe3d8b53c633034c9c05c027004f0628cb4739869d92787fbffabd847615fc4",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\pilot_datagen_parity_7_8.json",
        "dest_rel": "audits\\pilot_datagen_parity_7_8.json",
        "sha256": "74ce8489278b5aa4970114f86c878551934aca3da5dfebabd85459283eccf61b",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\rescore_depth_curve.json",
        "dest_rel": "audits\\rescore_depth_curve.json",
        "sha256": "112162c61fedb4fcc22a5b199689ea2f4623dbde447a42dbba7a2c55aceefca1",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\sf19_slice_r0067.json",
        "dest_rel": "audits\\sf19_slice_r0067.json",
        "sha256": "4a2d0a954b2050b7b2af84285b97e597346320f2b08f78f0e72e72d8ed7fded8",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\sf19_slice_G1.json",
        "dest_rel": "audits\\sf19_slice_G1.json",
        "sha256": "c9e0df8a36a5425e4cbf32398b43fc132ec368ad84db16b0a59d72d7ff5218a6",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\anchors\\heldout_eval_r0067.json",
        "dest_rel": "audits\\heldout_eval_r0067.json",
        "sha256": "639aad8609d7bcbe06dc39dd1099794a1786c2c475915a174ab7ff0241c70124",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\anchors\\heldout_eval_G2.json",
        "dest_rel": "audits\\heldout_eval_G2.json",
        "sha256": "7c5007d2a53ad0bd4019ae06fb87c7160b19b972a43e7dbb9f990a03ab081a95",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\anchors\\heldout_integrity_verification.json",
        "dest_rel": "audits\\heldout_integrity_verification.json",
        "sha256": "7dfe88d9b537fed19f45ad169cfada6e904aadbc902c1e0b94b5df85e1114adf",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\anchors\\s5_s7_overlap_audit.json",
        "dest_rel": "audits\\s5_s7_overlap_audit.json",
        "sha256": "7f6bcd378bb64e6e1c8893df68fd9ada63eb566d1702dafe4e22b2f2a45d2fc3",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\ROUND10_SEARCH_BUILD_REPORT.json",
        "dest_rel": "audits\\ROUND10_SEARCH_BUILD_REPORT.json",
        "sha256": "83762d41a76f8fbfd37b33be1e80cd3185e4f3c004789e614219844358ab7965",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\ROUND11_SEARCH_BUILD_REPORT.json",
        "dest_rel": "audits\\ROUND11_SEARCH_BUILD_REPORT.json",
        "sha256": "10bc8c2d964647860e16a43f8e88099781a9c7ff413fe0ed5be3b2d40856487b",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\ROUND12_BUILD_REPORT.json",
        "dest_rel": "audits\\ROUND12_BUILD_REPORT.json",
        "sha256": "12e1739a33235f858559373a602f77562c5549cdca03939973ad263143cb2b81",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\ROUND13_BUILD_REPORT.json",
        "dest_rel": "audits\\ROUND13_BUILD_REPORT.json",
        "sha256": "510ac18ff3bc0c2abe26564aadf0b2de9e18fb213a52587d1d853d59d0a60da4",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamA_search_packets\\builds\\proto_7_gate.json",
        "dest_rel": "audits\\proto_7_gate.json",
        "sha256": "98a2c0f1f37804cf8e24ade78ef428948aa6cfc95c1f6fc37112d7164f9b25ce",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave4\\streamA_search_packets\\builds\\proto_8_gate.json",
        "dest_rel": "audits\\proto_8_gate.json",
        "sha256": "4bd548cd7c63380763553cad1f362fecdddcd63f584218b361063d4c769789d7",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamA_search_packets\\superstack_6patch_proof.json",
        "dest_rel": "audits\\superstack_6patch_proof.json",
        "sha256": "f20a0a4f0b0c9629d3f96e601266637320f0c59583be86a058c278515ca86227",
        "freeze_mutable": True
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamA_search_packets\\builds\\proto_9_corr_complexity_rfp_lmr_gate.json",
        "dest_rel": "audits\\proto_9_corr_complexity_rfp_lmr_gate.json",
        "sha256": "215cb73d8cf24894ad5c7824caa514482a36ec78d6a8f7b272198df0c0003f76",
        "freeze_mutable": True
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave5\\streamA_search_packets\\builds\\proto_10_cutnode_history_and_cap_lmr_gate.json",
        "dest_rel": "audits\\proto_10_cutnode_history_and_cap_lmr_gate.json",
        "sha256": "2e33a0b015c62b11e3085b7147d03c6827fb98ec1b905db6ea27c73d887cac82",
        "freeze_mutable": True
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\results\\audit_cc0_v2_dedup_phase.json",
        "dest_rel": "audits\\filter_quest_results_audit_cc0_v2_dedup_phase.json",
        "sha256": "09d71c18e89f04b75693e4106b79ee3732ac6bf068d1d3e5cd4f79ffdd10e1fb",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\results\\audit_neardups_and_correlation.json",
        "dest_rel": "audits\\filter_quest_results_audit_neardups_and_correlation.json",
        "sha256": "7f09aae7f09121005635e61cfc379d8fa0733bd185bc7cebce4734b142c4a7a1",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\results\\audit_r0202.json",
        "dest_rel": "audits\\filter_quest_results_audit_r0202.json",
        "sha256": "09bbb44f8fcfea324052ec01b31ab6e2e01fbc18753c972721ab17aef13837b7",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\results\\audit_val_and_r0203_raw.json",
        "dest_rel": "audits\\filter_quest_results_audit_val_and_r0203_raw.json",
        "sha256": "f3accfea6db70bb3b4e387910f77362e6a30f573dfa65eb4e1394fcba6f1a6a6",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\results\\cross_round_dedup_r0178_r0202_m64.json",
        "dest_rel": "audits\\filter_quest_results_cross_round_dedup_r0178_r0202_m64.json",
        "sha256": "898e07e0bd81a5194e52c46dd9886917d1ee22390a390e938bcc41d680f95b62",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\results\\m4_vs_train_shift.json",
        "dest_rel": "audits\\filter_quest_results_m4_vs_train_shift.json",
        "sha256": "9d820da3b64c4278a296c20485a4cd8779b818cef4dd5f68a235882649b2019b",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\results\\offline_eval_table.json",
        "dest_rel": "audits\\filter_quest_results_offline_eval_table.json",
        "sha256": "e2eef0eecdf6187bd1b9699fbecc2253582a3f48447e4fadb2da01c80fbafa5f",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\results\\parallel_filter_benchmark.json",
        "dest_rel": "audits\\filter_quest_results_parallel_filter_benchmark.json",
        "sha256": "e81633ca15da3aa9ec1c68ad69cdc345e3e59f38c34d082ece532e96493c38c3",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\results\\partition_fqs_buckets_bench.json",
        "dest_rel": "audits\\filter_quest_results_partition_fqs_buckets_bench.json",
        "sha256": "cbf81bfa3b2d1e72842c516a1303c65a74932a75b09bfb33a18b41fec18acbe5",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\results\\SERVER_DAY_OB_MIX_AUDIT.json",
        "dest_rel": "audits\\filter_quest_results_SERVER_DAY_OB_MIX_AUDIT.json",
        "sha256": "a18497efac3888069e245fb7a3fa6b585023745ea5637afa3f9235b8b736e993",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\results\\WITHIN_GAME_CORRELATION_AUDIT.json",
        "dest_rel": "audits\\filter_quest_results_WITHIN_GAME_CORRELATION_AUDIT.json",
        "sha256": "a045c1d720dcac9273c7df9b2735b6fbfbfcbada0812f8ff6785aa367a8a009e",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\diag_e6\\diag_summary.json",
        "dest_rel": "audits\\G3_FULL25_diag_e6_diag_summary.json",
        "sha256": "e4a2403f12104258cc8d1303cc361d0a981511693c3d43f59d4b329408dbc21f",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\diag_e6\\eval_full.json",
        "dest_rel": "audits\\G3_FULL25_diag_e6_eval_full.json",
        "sha256": "3d51685bf36921a4e9dd43c3eb6ccee07dcf7504ff06d558a2bef33a9cf1f839",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\diag_e6\\heldout_syzygy_4k.json",
        "dest_rel": "audits\\G3_FULL25_diag_e6_heldout_syzygy_4k.json",
        "sha256": "1c0b702a80821cfe9eb4e44bb7f14758669f6ffcad3989116d149a41369c03d8",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\diag_e6\\net_sanity_v2.txt",
        "dest_rel": "audits\\G3_FULL25_diag_e6_net_sanity_v2.txt",
        "sha256": "fb693b310fffec898c4412f71fd98494d1144cd93a91e53e5a697444d047beaa",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\diag_e6\\sf19_slice.json",
        "dest_rel": "audits\\G3_FULL25_diag_e6_sf19_slice.json",
        "sha256": "6463deab6c604379bc795b5fb36cdcbd6a1fd6b3d4aed6a061a02e2ee24ff371",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\diag_e12\\eval_full.json",
        "dest_rel": "audits\\G3_FULL25_diag_e12_eval_full.json",
        "sha256": "3c74504749478488a929636555d412a2ba3f311e1b5a70fb1a31b816e3920d3e",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\diag_e12\\heldout_syzygy_4k.json",
        "dest_rel": "audits\\G3_FULL25_diag_e12_heldout_syzygy_4k.json",
        "sha256": "4d6810219946596efddcf8184df200a00cadf632c81d3995c0de86863b78aa68",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\diag_e12\\sf19_slice.json",
        "dest_rel": "audits\\G3_FULL25_diag_e12_sf19_slice.json",
        "sha256": "fa2705202bec8240540d63a373064e0431ca91e7e2398a6d607b7d963046abe4",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\diag_e12\\swa_meta.json",
        "dest_rel": "audits\\G3_FULL25_diag_e12_swa_meta.json",
        "sha256": "e60d7c77edcd25600483a79a145cf46c7acad0ca87b6f0c56f76dbceb9748a61",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\diag_e24\\diag_summary.json",
        "dest_rel": "audits\\G3_FULL25_diag_e24_diag_summary.json",
        "sha256": "eea294f1ed92bb0a8ae77fccf6ef80c9fc74bbcb7c4abc06d4b69f64774b8ab7",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\diag_e24\\eval_full.json",
        "dest_rel": "audits\\G3_FULL25_diag_e24_eval_full.json",
        "sha256": "ede50e0e3af50840616a8a30e261242478aedf32735c8c02ac36272b11c3d64f",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\diag_e24\\heldout_syzygy_4k.json",
        "dest_rel": "audits\\G3_FULL25_diag_e24_heldout_syzygy_4k.json",
        "sha256": "0a661f06444e022545c8d3a376c86dc8cc1ea829deeb6c57664d404d62990b78",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\diag_e24\\net_sanity_v2.txt",
        "dest_rel": "audits\\G3_FULL25_diag_e24_net_sanity_v2.txt",
        "sha256": "73b9e77c043a3d996ee09686e0642b78c27fd5b3b0897e39ae560c7481f9f8b9",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\diag_e24\\sf19_slice.json",
        "dest_rel": "audits\\G3_FULL25_diag_e24_sf19_slice.json",
        "sha256": "f148fb871da27898df8e64720b23d2ce65df6099ec84abe15933561097c889ea",
        "freeze_mutable": False
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\PLAN_V3P_LOOP_PLACEMENT_INVENTORY.md",
        "dest_rel": "docs\\PLAN_V3P_LOOP_PLACEMENT_INVENTORY.md",
        "sha256": "7ae59122a5c0628b77eda9681668907011a3d2f0f18ae5bf531bb46a72bcde21",
        "freeze_mutable": False
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\STAGE2_FILTER_QUEST_SUMMARY.md",
        "dest_rel": "docs\\STAGE2_FILTER_QUEST_SUMMARY.md",
        "sha256": "c17033d8b8a4102b0709fb5b6d62af7cf9a42ef7aa850ce91dffdf01f6eda56d",
        "freeze_mutable": True
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\forge_train_v3p_loop_adapter.py",
        "dest_rel": "scripts\\forge_train_v3p_loop_adapter.py",
        "sha256": "55bc6078392b19df16860d8a93420c9af3b52bfeefe0026ef04888da841b7631",
        "freeze_mutable": False
    },
    {
        "category": "tests",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\test_v3p_surface2_format.py",
        "dest_rel": "tests\\test_v3p_surface2_format.py",
        "sha256": "c3157540e4cf92804183607bbd338262afd3e271240e8c0dd5cd1a6b60031574",
        "freeze_mutable": False
    },
    {
        "category": "tests",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\test_v3p_surface4_parity_and_modelcheck.py",
        "dest_rel": "tests\\test_v3p_surface4_parity_and_modelcheck.py",
        "sha256": "18f7d8de513c3386c69682b13911bed385b5407645956eb6325db95dd9181528",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\post_g3_summary.json",
        "dest_rel": "audits\\G3_FULL25_post_g3_summary.json",
        "sha256": "c17ed87657eeee881e4839a4bd37e62590674a449d89544be5985a2cbabcfcc5",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\eval_full_cand.json",
        "dest_rel": "audits\\G3_FULL25_eval_full_cand.json",
        "sha256": "b6d596b4b9acabddf5c018f8872c66a685a7a77786a7ff03c26ab347fdf5beeb",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\heldout_syzygy_4k_cand.json",
        "dest_rel": "audits\\G3_FULL25_heldout_syzygy_4k_cand.json",
        "sha256": "adec936dd6ce3ccc5be75453be51eac77838824e965ef84607ad5e084c602233",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\sf19_slice_cand.json",
        "dest_rel": "audits\\G3_FULL25_sf19_slice_cand.json",
        "sha256": "9c7745409c45fc145ab6d52239760c1cda5ccafbd59f3576b9ffe2f57cfc7881",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\master_gate_full_cand.json",
        "dest_rel": "audits\\G3_FULL25_master_gate_full_cand.json",
        "sha256": "356f63d9c87c93a25427f5eab8d33b17f4592616089875da2a2b22c7c30f4442",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\net_sanity_v2_cand.txt",
        "dest_rel": "audits\\G3_FULL25_net_sanity_v2_cand.txt",
        "sha256": "eab287868ffd33c8b50e2d8b322964e8837cb73958ed586a03b99b980b4f09a6",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\gpu_runs\\G3_FULL25_v3p_1024_cc0_anchored\\metrics.json",
        "dest_rel": "audits\\G3_FULL25_metrics.json",
        "sha256": "5c227a17c17a0173ab7c51548b098f912600baef46b942e6b332e2593bbe37de",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\matches\\G3_FULL25_vs_r0067_1000g_50k\\summary.json",
        "dest_rel": "audits\\G3_FULL25_vs_r0067_1000g_50k_summary.json",
        "sha256": "2acbaa65272ba182bf3d63759b053423654b5169d3ddf909ecd65d27fb5a01b5",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\matches\\G3_FULL25_vs_r0067_1000g_50k\\declaration_20261127_222833.json",
        "dest_rel": "audits\\G3_FULL25_vs_r0067_1000g_50k_declaration_20261127_222833.json",
        "sha256": "f7371869469791a87916c1ce1e303776f3604c49d08418cc2a788672c987d474",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\matches\\G3_FULL25_vs_r0202_1000g_50k\\summary.json",
        "dest_rel": "audits\\G3_FULL25_vs_r0202_1000g_50k_summary.json",
        "sha256": "bf0b092f06a89cffd444e4ce81ebadcb6f89fdb3b9eeac164213674bb58667e1",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\matches\\G3_FULL25_vs_r0202_1000g_50k\\declaration_20261127_223800.json",
        "dest_rel": "audits\\G3_FULL25_vs_r0202_1000g_50k_declaration_20261127_223800.json",
        "sha256": "6166b0ced7d8dacde4ed7b36eef31a945817e503ac396a14a293acd2c4819436",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\matches\\G3_FULL25_vs_r0067_600g_250k\\summary.json",
        "dest_rel": "audits\\G3_FULL25_vs_r0067_600g_250k_summary.json",
        "sha256": "7030b0793828ec0c9b4c33ff64f71c24187d4692828575f282a1c67515d1333c",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\matches\\G3_FULL25_vs_r0067_600g_250k\\declaration_20261127_224737.json",
        "dest_rel": "audits\\G3_FULL25_vs_r0067_600g_250k_declaration_20261127_224737.json",
        "sha256": "63fa62ee1c5d20ec247fe9615d8fbbe2a9ed6d1cf3da9c608cb6001872fee57d",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\matches\\G3_FULL25_vs_r0202_600g_250k\\summary.json",
        "dest_rel": "audits\\G3_FULL25_vs_r0202_600g_250k_summary.json",
        "sha256": "d4a82130a301daaee903b261232dc7c71f5b4e993d0de0d0b0ec58d3b48abfe0",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\matches\\G3_FULL25_vs_r0202_600g_250k\\declaration_20261127_230522.json",
        "dest_rel": "audits\\G3_FULL25_vs_r0202_600g_250k_declaration_20261127_230522.json",
        "sha256": "936a86818d39ab2f62e43618c5a9bb267d2a684644ad22dcbb4bb0ecfd4a15a9",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\G3_VS_R0067_PGN_DIAGNOSIS.json",
        "dest_rel": "audits\\G3_VS_R0067_PGN_DIAGNOSIS.json",
        "sha256": "6516eb180dd7a619ea8a0c065229dd66a52c241cfe01bcb5cd05a98caab805f8",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\G3_STM_TEMPO_BY_SOURCE_AUDIT.json",
        "dest_rel": "audits\\G3_STM_TEMPO_BY_SOURCE_AUDIT.json",
        "sha256": "04eba7445196499a56cc64e88933dd430a640c35477ecd9912dac80ad97b6482",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\G3_INDIST_TEMPO_AUDIT.json",
        "dest_rel": "audits\\G3_INDIST_TEMPO_AUDIT.json",
        "sha256": "98a3778aeb4183ef1d527e067c1f8da02e3fccdfad01ed58ccdd7370156491e4",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\pilot_datagen_parity_7_8_G3_R4.json",
        "dest_rel": "audits\\pilot_datagen_parity_7_8_G3_R4.json",
        "sha256": "99a8c85ce551cb310d48a3f1ec36b739f0baa68fd6491e54a9ad76364274b46d",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\V3P_PLACEMENT_PACKAGE_VERIFICATION.json",
        "dest_rel": "audits\\V3P_PLACEMENT_PACKAGE_VERIFICATION.json",
        "sha256": "bed11cb8c91772de96e3b3fb4833799bc370f69c379a79b68c6208870c2d72ae",
        "freeze_mutable": False
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\filter_quest\\STAGE2_FILTER_QUEST_SUMMARY.json",
        "dest_rel": "audits\\STAGE2_FILTER_QUEST_SUMMARY.json",
        "sha256": "5b3df20128271863c8404978243ea55701519a4979f61bea9a1fe39dec9c1d12",
        "freeze_mutable": True
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\SERVERDAY_ARCH_SUITE_SUMMARY.json",
        "dest_rel": "audits\\SERVERDAY_ARCH_SUITE_SUMMARY.json",
        "sha256": "6e31f3da625c36d1bc6899136b7ceef6073f9c49fb664005ecad50c10ed5efe4",
        "freeze_mutable": False
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamA_v3p_placement_packets\\PACKET_SURFACE1_V3P_KERNEL_LINEBYLINE.md",
        "dest_rel": "packets\\PACKET_SURFACE1_V3P_KERNEL_LINEBYLINE.md",
        "sha256": "a01420de4e9288ad2f63617e997f85fb8cad5ec50a8a696b508b10f9d5ae397d",
        "freeze_mutable": True,
        "wave6_sibling": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamA_v3p_placement_packets\\PACKET_SURFACES2_5_LOOP_INTEGRATION.md",
        "dest_rel": "packets\\PACKET_SURFACES2_5_LOOP_INTEGRATION.md",
        "sha256": "521dc0043b58b6e52b5d5bcbf129b4857c76c22643847cfd1ff6b0e95b2f029c",
        "freeze_mutable": True,
        "wave6_sibling": True
    },
    {
        "category": "tests",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamA_v3p_placement_packets\\tests\\test_v3p_placement_and_parity_w6.py",
        "dest_rel": "tests\\test_v3p_placement_and_parity_w6.py",
        "sha256": "ec41754ef74762a9f3413ee2497cc3cd5be5681584669d152907246ef0665a81",
        "freeze_mutable": True,
        "wave6_sibling": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamB_round12_14_packets\\PACKET_SF34.md",
        "dest_rel": "packets\\PACKET_SF34.md",
        "sha256": "dd1d77a37e9e44d09850b944705556b05c3744e52a9697a0bd1d447ea08fb37a",
        "freeze_mutable": True,
        "wave6_sibling": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamB_round12_14_packets\\PACKET_SF35.md",
        "dest_rel": "packets\\PACKET_SF35.md",
        "sha256": "6ecc49faba5c388b54f5830413b9917be45bc5572ffa4eef9b195e6d8b8d3768",
        "freeze_mutable": True,
        "wave6_sibling": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamB_round12_14_packets\\PACKET_SF36.md",
        "dest_rel": "packets\\PACKET_SF36.md",
        "sha256": "8ff78fc6e87a137dda8dea2bf920d9307a39e2f1e93c7b179f69fd518af34d74",
        "freeze_mutable": True,
        "wave6_sibling": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamB_round12_14_packets\\PACKET_SF37.md",
        "dest_rel": "packets\\PACKET_SF37.md",
        "sha256": "148c96699b40abd2af98975720a19dd8eae7907ee60e44c7380437f5526952ea",
        "freeze_mutable": True,
        "wave6_sibling": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamB_round12_14_packets\\PACKET_SF38.md",
        "dest_rel": "packets\\PACKET_SF38.md",
        "sha256": "cc01dc97ad3ddc806653b158d8838419c2242683a5c3842a52f61e9a6ce246ce",
        "freeze_mutable": True,
        "wave6_sibling": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamB_round12_14_packets\\PACKET_SF39.md",
        "dest_rel": "packets\\PACKET_SF39.md",
        "sha256": "5d72e0eef27fb1b195049bf30ade87175643160c1ff79c6a574e31508d1ec4fb",
        "freeze_mutable": True,
        "wave6_sibling": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamB_round12_14_packets\\PACKET_SF40.md",
        "dest_rel": "packets\\PACKET_SF40.md",
        "sha256": "5ef1d11509289ffc7c0aca205530a6695b0c01581ae7197b42b9ca989d0009ee",
        "freeze_mutable": True,
        "wave6_sibling": True
    },
    {
        "category": "packets",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamB_round12_14_packets\\PACKET_LMR_DEEPER_UCI.md",
        "dest_rel": "packets\\PACKET_LMR_DEEPER_UCI.md",
        "sha256": "4384994283605df5fedf43344f06eeed5743865f69577a1bf8c74f2132c863ad",
        "freeze_mutable": True,
        "wave6_sibling": True
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamB_round12_14_packets\\verify_round12_14_orthogonality.py",
        "dest_rel": "scripts\\verify_round12_14_orthogonality.py",
        "sha256": "991b4317a55e3106342a14d18cc4fc723b4d41281278fe5dec5fce4f9242052f",
        "freeze_mutable": True,
        "wave6_sibling": True
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamB_round12_14_packets\\round12_14_orthogonality.json",
        "dest_rel": "audits\\round12_14_orthogonality.json",
        "sha256": "98a9d33191c95e67b1ab344340639891c83a8ed61e3cea7e5860d8b01a18656c",
        "freeze_mutable": True,
        "wave6_sibling": True
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamC_final_delivery_w6\\DEBATE_EVIDENCE_INDEX_W6.md",
        "dest_rel": "docs\\DEBATE_EVIDENCE_INDEX_W6.md",
        "sha256": "f89388f25bf4472014e04b9c69ba6572644d2847e7932785f49fb1514f4c7062",
        "freeze_mutable": True
    },
    {
        "category": "docs",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamC_final_delivery_w6\\DELIVERY_MANIFEST_W6.md",
        "dest_rel": "docs\\DELIVERY_MANIFEST_W6.md",
        "sha256": None,
        "freeze_mutable": True
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamC_final_delivery_w6\\verify_all_patches_w6.py",
        "dest_rel": "scripts\\verify_all_patches_w6.py",
        "sha256": "f3794ff2e5f6045bdc273850ad7baad8c9889bb4ab80e2daf556d9ac4cab4318",
        "freeze_mutable": True
    },
    {
        "category": "scripts",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamC_final_delivery_w6\\stage_teamwork_delivery_w6.py",
        "dest_rel": "scripts\\stage_teamwork_delivery_w6.py",
        "sha256": None,
        "freeze_mutable": True
    },
    {
        "category": "audits",
        "source": "C:\\nnue-lab\\neon\\forge_fixes\\teamwork_wave6\\streamC_final_delivery_w6\\verify_all_patches_w6_report.json",
        "dest_rel": "audits\\verify_all_patches_w6_report.json",
        "sha256": "1d430f287625ee784acccaefd19051537cb7795206de5d024b5bf9643bd07fee",
        "freeze_mutable": True
    }
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_handoff_frozen(handoff_path: Path) -> list[str]:
    if not handoff_path.exists():
        return ["MISSING HANDOFF_12H_DATA_QUALITY.md"]
    text = handoff_path.read_text(encoding="utf-8", errors="replace")
    markers = re.findall(r"\[(?:PENDING|TRAINING|TESTING)[^\]]*(?:\]|$)", text)
    return sorted(set(markers))


def has_forbidden_path(path_obj: Path) -> bool:
    return any(part in FORBIDDEN_DIR_NAMES or part.startswith("_work_") for part in path_obj.parts)


def parse_scoreboard_md(sb_path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for ln in sb_path.read_text(encoding="utf-8").splitlines():
        if not ln.startswith("| "):
            continue
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cols) < 9 or cols[0] in ("Group", "---"):
            continue
        grp, mname_raw, games, wdl, elo_ci, z_val, los_val, ptnml, clean = cols[:9]
        mname = mname_raw.strip("`")
        rows[mname] = {
            "grp": grp.strip("`"),
            "games": games,
            "wdl": wdl.strip("`"),
            "elo_ci": elo_ci,
            "z": z_val,
            "los": los_val,
            "ptnml": ptnml.strip("`"),
            "clean": clean,
        }
    return rows


def verify_debate_index(index_path: Path, strict_living: bool = False) -> int:
    if not index_path.exists():
        print(f"FAIL: missing debate index {index_path}", file=sys.stderr)
        return 1
    text = index_path.read_text(encoding="utf-8")

    # 1. Forbidden terminology check across all files in streamC_final_delivery_w6
    banned_stem = "".join(["c", "u", "r", "e"])
    banned_re = re.compile(banned_stem + r"[a-z]*", flags=re.IGNORECASE)
    bad_hits: list[str] = []
    for p in sorted(HERE.iterdir()):
        if p.is_file():
            content = p.read_text(encoding="utf-8", errors="replace")
            matches = banned_re.findall(content)
            if matches:
                bad_hits.append(f"{p.name}: {matches}")
    if bad_hits:
        print(f"FAIL: forbidden terminology detected: {bad_hits}", file=sys.stderr)
        return 1

    # 2. Verify every SHA-256 registry row against live disk bytes & hash
    row_re = re.compile(
        r"^\|\s*`([^`]+)`\s*\|\s*`(C:\\nnue-lab\\[^`]+)`\s*\|\s*([\d,]+)\s*\|\s*`([0-9a-f]{64})`\s*\|"
    )
    checked = 0
    static_mismatches = 0
    living_drift = 0
    for ln in text.splitlines():
        m = row_re.match(ln)
        if not m:
            continue
        label, raw_path, raw_bytes, raw_sha = m.groups()
        checked += 1
        p = Path(raw_path)
        exp_bytes = int(raw_bytes.replace(",", ""))
        is_living = "(living)" in label.lower() or p.resolve() in LIVING_INDEX_PATHS
        if not p.exists():
            static_mismatches += 1
            print(f"[MISSING_INDEX_TARGET] {label}: {p}", file=sys.stderr)
            continue
        act_bytes = p.stat().st_size
        act_sha = sha256_file(p)
        if act_bytes != exp_bytes or act_sha != raw_sha:
            if is_living:
                living_drift += 1
                print(
                    f"[LIVING_DRIFT] {label}: idx=({exp_bytes}, {raw_sha[:16]}) vs disk=({act_bytes}, {act_sha[:16]})",
                    file=sys.stderr if strict_living else sys.stdout,
                )
            else:
                static_mismatches += 1
                print(
                    f"[HASH_DRIFT] {label}: idx=({exp_bytes}, {raw_sha[:16]}) vs disk=({act_bytes}, {act_sha[:16]})",
                    file=sys.stderr,
                )

    # 3. Verify unpooled scoreboard rows recorded in index match ALL_MATCHES_SCOREBOARD.md with 0 numeric diffs
    sb_md = LAB / "neon" / "forge_fixes" / "ALL_MATCHES_SCOREBOARD.md"
    sb_map = parse_scoreboard_md(sb_md)
    sec4 = text.split("## 4. Unpooled Fastchess Scoreboard")[1].split("## 5. Open Debate Questions")[0]
    idx_map: dict[str, dict[str, str]] = {}
    dup_rows = 0
    for ln in sec4.splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", ln):
            continue
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cols) < 9:
            continue
        _, grp, mname_raw, wdl, elo_ci, z_val, los_val, ptnml, clean = cols[:9]
        mname = mname_raw.strip("`")
        if mname in idx_map:
            dup_rows += 1
            print(f"[SCOREBOARD_DUPLICATE] {mname}", file=sys.stderr)
        idx_map[mname] = {
            "grp": grp.strip("`"),
            "wdl": wdl.strip("`"),
            "elo_ci": elo_ci,
            "z": z_val,
            "los": los_val,
            "ptnml": ptnml.strip("`"),
            "clean": clean,
        }

    scoreboard_missing = 0
    scoreboard_diffs = 0
    for mname, idx_rec in idx_map.items():
        if mname not in sb_map:
            scoreboard_missing += 1
            print(f"[SCOREBOARD_MISSING_FROM_LIVE] {mname}", file=sys.stderr)
            continue
        sb_rec = sb_map[mname]
        for k in ("grp", "wdl", "elo_ci", "z", "los", "ptnml", "clean"):
            if idx_rec[k] != sb_rec[k]:
                scoreboard_diffs += 1
                print(
                    f"[SCOREBOARD_ROW_DIFF] {mname} field={k}: idx={idx_rec[k]!r} vs live={sb_rec[k]!r}",
                    file=sys.stderr,
                )

    extra_sb = sorted(set(sb_map) - set(idx_map))
    if extra_sb:
        print(
            f"[LIVING_DRIFT] ALL_MATCHES_SCOREBOARD.md has {len(extra_sb)} newer match row(s) not in index: {extra_sb}",
            file=sys.stderr if strict_living else sys.stdout,
        )

    print(
        f"VERIFY_DEBATE_INDEX: rows_checked={checked} | static_mismatches={static_mismatches} | "
        f"living_drift={living_drift} | scoreboard_rows={len(idx_map)}/{len(sb_map)} | "
        f"scoreboard_diffs={scoreboard_diffs} | scoreboard_missing={scoreboard_missing} | "
        f"forbidden_words=0 | strict_living={strict_living}"
    )
    if (
        checked == 0
        or static_mismatches > 0
        or scoreboard_diffs > 0
        or scoreboard_missing > 0
        or dup_rows > 0
        or (strict_living and (living_drift > 0 or len(idx_map) != len(sb_map)))
    ):
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Stage verified Wave 6 curated text-only deliverables into C:\\nnue-lab\\teamwork\\ (defaults to --dry-run)."
    )
    mode_grp = ap.add_mutually_exclusive_group()
    mode_grp.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview staging without touching C:\\nnue-lab\\teamwork\\ (default).",
    )
    mode_grp.add_argument(
        "--live",
        action="store_true",
        help="Enable live copy ONLY when BOTH --confirm-quest-complete YES_COPY_TO_TEAMWORK AND 0 freeze markers hold.",
    )
    mode_grp.add_argument(
        "--verify-debate-index",
        action="store_true",
        help="Verify every live SHA-256 row, unpooled scoreboard rows, and forbidden-word check in DEBATE_EVIDENCE_INDEX_W6.md.",
    )
    ap.add_argument(
        "--strict-living",
        action="store_true",
        help="With --verify-debate-index, fail RC=1 on any (living) file or scoreboard row count drift.",
    )
    ap.add_argument(
        "--confirm-quest-complete",
        type=str,
        default="",
        help="Required exact confirmation token: YES_COPY_TO_TEAMWORK",
    )
    ap.add_argument(
        "--require-siblings",
        action="store_true",
        help="Fail --dry-run if any Wave 6 parallel sibling output is missing.",
    )
    ap.add_argument(
        "--dest",
        type=str,
        default=str(DEFAULT_DEST),
        help="Destination staging directory inside C:\\nnue-lab\\teamwork\\.",
    )
    args = ap.parse_args()

    if args.verify_debate_index:
        return verify_debate_index(HERE / "DEBATE_EVIDENCE_INDEX_W6.md", strict_living=bool(args.strict_living))

    is_live = bool(args.live)
    handoff_path = Path(MANIFEST[0]["source"])
    pending_markers = check_handoff_frozen(handoff_path)

    # Dual-gate live enforcement (NO --allow-unfrozen escape hatch)
    if is_live and args.confirm_quest_complete != "YES_COPY_TO_TEAMWORK":
        print(
            "REFUSED: --live requires exact --confirm-quest-complete YES_COPY_TO_TEAMWORK. Zero files touched.",
            file=sys.stderr,
        )
        return 2

    if is_live and pending_markers:
        print(
            f"REFUSED: HANDOFF_12H_DATA_QUALITY.md is not frozen yet (found markers: {pending_markers}). "
            "All [PENDING]/[TRAINING]/[TESTING] markers must be cleared first. Zero files touched.",
            file=sys.stderr,
        )
        return 2

    dest_root = Path(args.dest)
    mode_label = "LIVE_COPY" if is_live else "DRY_RUN (read-only, C:\\nnue-lab\\teamwork\\ untouched)"
    print(f"STAGE_MODE: {mode_label}")
    print(f"DEST_ROOT : {dest_root}")
    print(f"FREEZE_CHECK: {'FROZEN (0 pending markers)' if not pending_markers else f'UNFROZEN markers={pending_markers}'}")

    missing = 0
    pending_sibling = 0
    changed = 0
    immutable_mismatch = 0
    forbidden_ext = 0
    forbidden_path = 0
    matched = 0
    total_bytes = 0
    copy_sources: list[tuple[Path, str]] = []
    compact_files: list[dict] = []

    for item in MANIFEST:
        src = Path(item["source"])
        dest_rel_path = Path(item["dest_rel"])
        dst = dest_root / dest_rel_path
        if any(suf.lower() in FORBIDDEN_SUFFIXES for suf in src.suffixes) or any(
            suf.lower() in FORBIDDEN_SUFFIXES for suf in dest_rel_path.suffixes
        ):
            forbidden_ext += 1
            print(f"[FORBIDDEN_EXT] {src} -> {dest_rel_path}")
        if has_forbidden_path(src) or has_forbidden_path(dest_rel_path):
            forbidden_path += 1
            print(f"[FORBIDDEN_PATH] {src} -> {dest_rel_path}")
        if not src.exists():
            if item.get("wave6_sibling"):
                pending_sibling += 1
                print(f"[PENDING_W6_SIBLING] {src} -> {dst}")
            else:
                missing += 1
                print(f"[MISSING] {src} -> {dst}")
            continue

        size = src.stat().st_size
        total_bytes += size
        actual_sha = sha256_file(src)
        expected_sha = item.get("sha256")
        if expected_sha is not None and actual_sha == expected_sha:
            state = "MATCH"
            matched += 1
        elif item.get("freeze_mutable"):
            state = "CHANGED_MUTABLE" if expected_sha is not None else "MUTABLE_SELF"
            changed += 1
        else:
            state = "SHA_MISMATCH"
            changed += 1
            immutable_mismatch += 1
        print(f"[{state}] {item['dest_rel']} | {size} B | sha256={actual_sha[:16]} | src={src}")
        copy_sources.append((src, item["dest_rel"]))
        compact_files.append(
            {
                "dest_rel": item["dest_rel"],
                "bytes": size,
                "sha256": actual_sha,
                "category": item["category"],
                "freeze_mutable": bool(item.get("freeze_mutable")),
            }
        )

    manifest_payload = {
        "dest_root": str(dest_root),
        "total_files": len(compact_files),
        "total_files_bytes": total_bytes,
        "max_bundle_bytes": MAX_BUNDLE_BYTES,
        "files": compact_files,
    }
    manifest_json_bytes_data = json.dumps(manifest_payload, separators=(",", ":")).encode("utf-8")
    manifest_json_bytes = len(manifest_json_bytes_data)
    total_staged_bytes = total_bytes + manifest_json_bytes
    over_budget = total_staged_bytes > MAX_BUNDLE_BYTES

    if is_live and (
        missing > 0
        or pending_sibling > 0
        or immutable_mismatch > 0
        or forbidden_ext > 0
        or forbidden_path > 0
        or over_budget
    ):
        print(
            f"REFUSED: missing={missing}, pending_sibling={pending_sibling}, "
            f"immutable_mismatch={immutable_mismatch}, forbidden_ext={forbidden_ext}, "
            f"forbidden_path={forbidden_path}, total_bytes={total_bytes}+{manifest_json_bytes}={total_staged_bytes} "
            f"(cap={MAX_BUNDLE_BYTES}); aborting live copy.",
            file=sys.stderr,
        )
        return 2

    if is_live:
        dest_root.mkdir(parents=True, exist_ok=True)
        for src_p, dest_rel in copy_sources:
            dst = dest_root / dest_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_p, dst)
        (dest_root / "MANIFEST_SHA256.json").write_bytes(manifest_json_bytes_data)
        print(
            f"LIVE_COPY_COMPLETE: copied {len(copy_sources)} files + MANIFEST_SHA256.json "
            f"({total_bytes}+{manifest_json_bytes}={total_staged_bytes} B) into {dest_root}"
        )
        return 0

    print(
        f"\nDRY_RUN_SUMMARY: total={len(MANIFEST)} | matched={matched} | changed={changed} | "
        f"immutable_mismatch={immutable_mismatch} | missing={missing} | pending_sibling={pending_sibling} | "
        f"forbidden_ext={forbidden_ext} | forbidden_path={forbidden_path} | "
        f"total_bytes={total_bytes}+{manifest_json_bytes}={total_staged_bytes}/{MAX_BUNDLE_BYTES}"
    )
    ok = (
        missing == 0
        and immutable_mismatch == 0
        and forbidden_ext == 0
        and forbidden_path == 0
        and not over_budget
        and (not args.require_siblings or pending_sibling == 0)
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
