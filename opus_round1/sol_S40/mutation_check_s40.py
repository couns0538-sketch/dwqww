#!/usr/bin/env python3
"""Planted-bug check for the S40 tool: every mutant must make the test suite FAIL.
usage: python -I -B mutation_check_s40.py SCRATCH_DIR   (FORGE_S40_FEN2BIN / _HCE_DUMP / _V3B / _FIXTURE pass through)
Each mutant = the tool with one or two exact text replacements (each pattern must occur exactly once)."""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "forge_sol_S40_merge_datagen_20261027.py"
TEST = HERE / "test_forge_sol_S40_merge_datagen_20261027.py"
MUTANTS = {
    "M01_identity_and_key_ignore_side_to_move": [
        ("return mix64(h ^ (np.asarray(stm).astype(U64) + U64(0x632BE59BD9B4E019)))", "return mix64(h ^ U64(0x632BE59BD9B4E019))"),
        ("np.asarray(stm, np.uint8).reshape(-1, 1)], axis=1)", "np.zeros_like(np.asarray(stm, np.uint8)).reshape(-1, 1)], axis=1)")],
    "M02_group_rule_without_fullmove": [
        ("return (fm[1:] < fm[:-1]) | (pc[1:] > pc[:-1]) | (rc[1:] != rc[:-1])", "return (pc[1:] > pc[:-1]) | (rc[1:] != rc[:-1])")],
    "M03_group_reset_at_file_junctions": [
        ("        gid, ginfo = infer_groups(S[\"fm\"], S[\"pcs\"], S[\"rc\"])\n",
         "        gid, ginfo = infer_groups(S[\"fm\"], S[\"pcs\"], S[\"rc\"])\n        gid = gid + src_of\n")],
    "M04_holdout_game_rule_dropped": [
        ("assign((g_touch | g_hold_id)[gid], R_HOLD_GAME)", "assign(g_hold_id[gid], R_HOLD_GAME)")],
    "M05_no_exact_confirmation": [
        ("ok = (identity33(boards[r_rows], stm[r_rows]) == ident[s_rows]).all(axis=1)", "ok = np.ones(len(r_rows), bool)")],
    "M06_meta_result_shift": [
        ("(S[\"stm\"][sel] | (S[\"rc\"][sel] << 1)).astype(np.uint8)", "(S[\"stm\"][sel] | (S[\"rc\"][sel] << 2)).astype(np.uint8)")],
    "M07_result_codes_swapped": [
        ("rc = 0 if r == 0.0 else 1 if r == 0.5 else 2 if r == 1.0 else -1", "rc = 2 if r == 0.0 else 1 if r == 0.5 else 0 if r == 1.0 else -1")],
    "M08_nibble_order_swapped": [
        ("            if s & 1:\n                b[s >> 1] |= pc << 4", "            if not s & 1:\n                b[s >> 1] |= pc << 4")],
    "M09_out_dir_inside_input_allowed": [("        if is_within(out, d):\n", "        if False and is_within(out, d):\n")],
    "M10_tripwire_disabled": [("    if largest > TRIPWIRE_LIMIT:\n", "    if largest > TRIPWIRE_LIMIT + 1000:\n")],
    "M11_committed_bytes_ignored": [("                limit = int(args.part_committed_bytes)", "                limit = None")],
    "M12_dup_second_marks_first_occurrence": [
        ("later = first_s[inv_s] != np.arange(len(surv))", "later = first_s[inv_s] == np.arange(len(surv))")],
    "M13_main_scan_uses_holdout": [("mt_main = scan_role(refs_main, \"main\"", "mt_main = scan_role(refs_hold, \"main\"")],
    "M14_hce_subset_off_by_one": [
        ("write_fhce(out / f\"{stem}.hce\", hce_all[sel])", "write_fhce(out / f\"{stem}.hce\", hce_all[np.maximum(sel - 1, 0)])")],
    "M15_holdout_rule_off_ignored": [
        ("if in_hold.any() and args.holdout_game_rule == \"drop-group\":", "if in_hold.any():")],
    "M16_label_conflict_ignores_score": [
        ("diff = (scores[r_ok] != S[\"score\"][s_ok]) | (rcs[r_ok] != S[\"rc\"][s_ok])", "diff = (rcs[r_ok] != S[\"rc\"][s_ok])")],
    "M17_manifest_md5_wrong_file": [
        ("\"\".join(f\"{file_md5(out / n)}  {n}\\n\" for n in names)", "\"\".join(f\"{file_md5(out / names[0])}  {n}\\n\" for n in names)")],
    "M18_text_output_wrong_row": [("                if is_kept[g]:\n", "                if is_kept[g - 1]:\n")],
    "M19_live_db_guard_removed": [("            if is_within(args.seen_db, d):\n", "            if False and is_within(args.seen_db, d):\n")],
    "M20_part_read_without_flag": [("            if parts and not args.include_part:\n", "            if False:\n")],
    "M21_first_match_overwritten": [("                            if mt.first_file[s] < 0:\n", "                            if True:\n")],
    "M22_bad_lines_accepted": [("    if rank != 0 or file != 8 or wk != 1 or bk != 1 or cnt > 32:\n        return None\n",
                                "    if rank != 0 or file != 8:\n        return None\n")],
}


def main():
    scratch = Path(sys.argv[1]); scratch.mkdir(parents=True, exist_ok=True)
    src = TOOL.read_text(encoding="utf-8"); results = {}
    # control: the UNMUTATED tool under the same harness conditions must pass, or no mutant result means anything
    cdir = scratch / "M00_control_unmutated"; cdir.mkdir(exist_ok=True)
    ctl = cdir / TOOL.name
    if not ctl.exists():
        ctl.write_text(src, encoding="utf-8", newline="\n")
    p = subprocess.run([sys.executable, "-I", "-B", str(TEST)], env=dict(os.environ, FORGE_S40_TOOL=str(ctl), FORGE_S40_TMP=str(cdir)),
                       capture_output=True, text=True)
    print(f"M00_control_unmutated: {'PASS' if p.returncode == 0 else 'FAIL'}", flush=True)
    if p.returncode != 0:
        print(p.stderr[-3000:]); return 2
    for name, edits in MUTANTS.items():
        text = src
        for old, new in edits:
            n = text.count(old)
            if n != 1:
                sys.exit(f"{name}: pattern occurs {n} times: {old!r}")
            text = text.replace(old, new)
        mdir = scratch / name; mdir.mkdir(exist_ok=True)
        mut = mdir / TOOL.name
        if not mut.exists():
            mut.write_text(text, encoding="utf-8", newline="\n")
        env = dict(os.environ, FORGE_S40_TOOL=str(mut), FORGE_S40_TMP=str(mdir))
        p = subprocess.run([sys.executable, "-I", "-B", str(TEST)], env=env, capture_output=True, text=True)
        failed = [l.split(" (")[0] for l in p.stderr.splitlines() if l.startswith(("FAIL:", "ERROR:"))]
        results[name] = {"returncode": p.returncode, "caught": p.returncode != 0, "failing_tests": failed}
        print(f"{name}: {'CAUGHT' if p.returncode else 'SURVIVED'} {failed}", flush=True)
    caught = sum(r["caught"] for r in results.values())
    print(json.dumps({"mutants": len(results), "caught": caught}, indent=1))
    (scratch / "mutation_results.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    return 0 if caught == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
