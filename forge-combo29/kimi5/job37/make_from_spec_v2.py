#!/usr/bin/env python3
# kimi5 job 37: reads ONLY options_spec.tsv and writes
#   (a) census_r15d.patch.txt   r15d -> all options, one file, diff -u, applies with patch -p1 -F0
#   (b) census_kF.patch.txt     the same options on the kF tree (kF = r15d + carbon2/job17 stack)
#   (c) bounds_check.txt        per-row bounds check; exit code 1 and the row named on any failure
#   (d) runlist.tsv             Step 4's run list (every NEW option +- 1 step, clamped; + ImprovingLookback 4)
#   (e) reading_guide.tsv       option | file | r15d line | old text | new text, one row per changed place
# The replacement SITES live in this script (committed); the spec carries the option table.
# Every site string is verified to occur exactly `want` times in the tree and its line(s) are
# cross-checked against the spec's "lines" column (spec lines must be a subset of the found lines).
# usage: make_from_spec.py SPEC R15D_TREE KF_TREE OUTDIR [--bounds-only]
import os, shutil, subprocess, sys

# ---------------------------------------------------------------- spec parsing
def read_spec(path):
    rows, tuner = [], {}
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                if line.startswith("# TUNER-STEP "):
                    p = line.replace(":", " : ").split()
                    tuner[p[2]] = int(p[3])
                continue
            c = line.split("\t")
            if c[0] == "name":
                continue
            rows.append(dict(name=c[0], lines=[int(x) for x in c[1].split(",")],
                             default=int(c[2]), min=int(c[3]), max=int(c[4]), step=int(c[5]),
                             bound=c[6], cls=c[7], tune=c[8]))
    return rows, tuner

# ---------------------------------------------------------------- sites table
# (option, file, old, new, want).  file s = src/search.cpp, h = include/forge/search.hpp.
T = "tune::"
SITES = [
    # --- job 35's 39 (ImprovingLookbackFallback removed; 2034 keeps its literal 4)
    ("TtNear50Clock", "s", "const bool near50 = board.halfmove_clock() >= 90;",
     "const bool near50 = board.halfmove_clock() >= " + T + "TtNear50Clock;", 2),
    ("TtNear50Clock", "s", "        board.halfmove_clock() < 90 &&",
     "        board.halfmove_clock() < " + T + "TtNear50Clock &&", 1),
    ("ImprovingLookback", "s",
     "        if ((ss - 2)->static_eval != ValueNone) improving = ss->static_eval > (ss - 2)->static_eval;",
     "        if ((ss - " + T + "ImprovingLookback)->static_eval != ValueNone) improving = ss->static_eval > (ss - " + T + "ImprovingLookback)->static_eval;", 1),
    ("RfpWorseningDrop", "s", "ss->static_eval + (ss - 1)->static_eval > 2",
     "ss->static_eval + (ss - 1)->static_eval > " + T + "RfpWorseningDrop", 1),
    ("RfpWorseningDiv", "s", "? tune::RfpMargin / 3 : 0;", "? tune::RfpMargin / " + T + "RfpWorseningDiv : 0;", 1),
    ("NullGateSlope,NullGateOffset", "s", "ss->static_eval >= beta - 24 * depth + 180 &&",
     "ss->static_eval >= beta - " + T + "NullGateSlope * depth + " + T + "NullGateOffset &&", 1),
    ("NullEvalReductionCap", "s", "std::min((eval - beta) / tune::NullMoveEvalDivisor, 3);",
     "std::min((eval - beta) / tune::NullMoveEvalDivisor, " + T + "NullEvalReductionCap);", 1),
    ("NullVerifyDepth", "s", "depth < 14 && tune::NullThreatVerify && cheaper_enemy_attacks_dearer(board);",
     "depth < " + T + "NullVerifyDepth && tune::NullThreatVerify && cheaper_enemy_attacks_dearer(board);", 1),
    ("NullVerifyDepth", "s", "if (depth < 14 && !threat_gate) {", "if (depth < " + T + "NullVerifyDepth && !threat_gate) {", 1),
    ("ProbcutImprovingDiscount", "s", "const int probcut_beta = beta + tune::ProbcutMargin - 50 * improving;",
     "const int probcut_beta = beta + tune::ProbcutMargin - " + T + "ProbcutImprovingDiscount * improving;", 1),
    ("ProbcutTtDepthMargin", "s", "!(tt_hit && tt_depth >= depth - 3 && tt_score != ValueNone && tt_score < probcut_beta)) {",
     "!(tt_hit && tt_depth >= depth - " + T + "ProbcutTtDepthMargin && tt_score != ValueNone && tt_score < probcut_beta)) {", 1),
    ("ProbcutSearchReduction", "s", "value = -search_child(board, ss + 1, depth - 4, -probcut_beta, -probcut_beta + 1, !cut_node);",
     "value = -search_child(board, ss + 1, depth - " + T + "ProbcutSearchReduction, -probcut_beta, -probcut_beta + 1, !cut_node);", 1),
    ("ProbcutTtDepthMargin", "s", ", move, depth - 3, BoundLower, ss->tt_pv, board.halfmove_clock());",
     ", move, depth - " + T + "ProbcutTtDepthMargin, BoundLower, ss->tt_pv, board.halfmove_clock());", 2),
    ("TtPruneIirOffset", "s", "depth >= tune::IirDepth + 2 && cut_node &&",
     "depth >= tune::IirDepth + " + T + "TtPruneIirOffset && cut_node &&", 1),
    ("FutilityImprovingDiv", "s", "? tune::FutilityBase / 2 : 0;", "? tune::FutilityBase / " + T + "FutilityImprovingDiv : 0;", 1),
    ("HistPruneWeakNum", "s", "? -tune::HistoryPruneMultiplier * depth * 3 / 4",
     "? -tune::HistoryPruneMultiplier * depth * " + T + "HistPruneWeakNum / 4", 1),
    ("SingularTtDepthMargin", "s", "!is_mate_score(tt_score) && tt_depth >= depth - 3) {",
     "!is_mate_score(tt_score) && tt_depth >= depth - " + T + "SingularTtDepthMargin) {", 1),
    ("SingularDepthDiv", "s", "const int singular_depth = std::max(1, (depth - 1) / 2);",
     "const int singular_depth = std::max(1, (depth - 1) / " + T + "SingularDepthDiv);", 1),
    ("DoubleExtMargin,DoubleExtLimit", "s", "if (!pv_node && singular_score < singular_beta - 24 && inherited_double_extensions <= 6) {",
     "if (!pv_node && singular_score < singular_beta - " + T + "DoubleExtMargin && inherited_double_extensions <= " + T + "DoubleExtLimit) {", 1),
    ("DoubleExtPlies", "s", "                    extension = 2;", "                    extension = " + T + "DoubleExtPlies;", 1),
    ("DoubleExtPlies", "s", "ss->double_extensions = inherited_double_extensions + (extension == 2);",
     "ss->double_extensions = inherited_double_extensions + (extension == " + T + "DoubleExtPlies);", 1),
    ("LmrMinDepth", "s", "board.halfmove_clock() + new_depth < 100 && depth >= 2 &&",
     "board.halfmove_clock() + new_depth < 100 && depth >= " + T + "LmrMinDepth &&", 1),
    ("LmrNoisyMoveCount", "s", "(quiet || !ss->tt_pv || move_count > 4)) {",
     "(quiet || !ss->tt_pv || move_count > " + T + "LmrNoisyMoveCount)) {", 1),
    ("LmrTtPv", "s", "            if (ss->tt_pv) r -= 1;", "            if (ss->tt_pv) r -= " + T + "LmrTtPv;", 1),
    ("LmrNotImproving", "s", "            if (!improving) r += 1;", "            if (!improving) r += " + T + "LmrNotImproving;", 1),
    ("LmrCutNode", "s", "            if (cut_node) r += 2;", "            if (cut_node) r += " + T + "LmrCutNode;", 1),
    ("LmrTtCapture", "s", "            if (tt_capture && quiet) r += 1;", "            if (tt_capture && quiet) r += " + T + "LmrTtCapture;", 1),
    ("LmrGiveCheck", "s", "            if (gives_check) r -= 1;", "            if (gives_check) r -= " + T + "LmrGiveCheck;", 1),
    ("LmrInCheck", "s", "            if (in_check) r -= 1;", "            if (in_check) r -= " + T + "LmrInCheck;", 1),
    ("LmrCutoffAdd", "s", "(ss + 1)->cutoff_count > tune::LmrCutoffThreshold) r += 1;",
     "(ss + 1)->cutoff_count > tune::LmrCutoffThreshold) r += " + T + "LmrCutoffAdd;", 1),
    ("LmrHistoryClamp", "s", "r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);",
     "r -= std::clamp(history / tune::LmrHistoryDivisor, -" + T + "LmrHistoryClamp, " + T + "LmrHistoryClamp);", 1),
    ("LmrDeeperBase,LmrDeeperDepthMul", "s", "const bool do_deeper = score > best_score + 40 + 2 * new_depth;",
     "const bool do_deeper = score > best_score + " + T + "LmrDeeperBase + " + T + "LmrDeeperDepthMul * new_depth;", 1),
    ("LmrShallowerBase,LmrShallowerDepthMul", "s", "const bool do_shallower = score < best_score + new_depth;",
     "const bool do_shallower = score < best_score + " + T + "LmrShallowerBase + " + T + "LmrShallowerDepthMul * new_depth;", 1),
    ("LmrQuietBoostDiv", "s", "update_continuation(ss, moved, move.to, history_bonus(depth) / 2);",
     "update_continuation(ss, moved, move.to, history_bonus(depth) / " + T + "LmrQuietBoostDiv);", 1),
    ("HistBonusBetaMargin", "s", "depth + (best_score > beta + 100)", "depth + (best_score > beta + " + T + "HistBonusBetaMargin)", 1),
    ("PvQuietBonusDiv", "s", "history_bonus(depth) / 4", "history_bonus(depth) / " + T + "PvQuietBonusDiv", 4),
    ("CuckooRepMinClock", "s", "{ return board.halfmove_clock() >= 3; }", "{ return board.halfmove_clock() >= " + T + "CuckooRepMinClock; }", 1),
    ("AspStartDepth", "s", "const bool narrow = depth >= 4 && !(tune::AspArmLate && reopen_full_window);",
     "const bool narrow = depth >= " + T + "AspStartDepth && !(tune::AspArmLate && reopen_full_window);", 1),
    ("AspDeltaGrowDiv,AspDeltaGrowAdd", "s", "            delta += delta / 2 + 4;",
     "            delta += delta / " + T + "AspDeltaGrowDiv + " + T + "AspDeltaGrowAdd;", 1),
    # --- K5's 20 new options
    ("LmpNotImprovingDiv", "s", "    return improving ? tune::LmpBase + depth * depth : (tune::LmpBase + depth * depth) / 2;",
     "    return improving ? tune::LmpBase + depth * depth : (tune::LmpBase + depth * depth) / " + T + "LmpNotImprovingDiv;", 1),
    ("HistoryBonusOffset", "s", "    return std::min(tune::HistoryBonusMax, tune::HistoryBonusQuadratic * depth * depth + tune::HistoryBonusLinear * depth - 32);",
     "    return std::min(tune::HistoryBonusMax, tune::HistoryBonusQuadratic * depth * depth + tune::HistoryBonusLinear * depth - " + T + "HistoryBonusOffset);", 1),
    ("TtAgePenalty", "s", "                            ? replace->depth - 4 * static_cast<int>((32U + generation - replace->generation()) & 31U)",
     "                            ? replace->depth - " + T + "TtAgePenalty * static_cast<int>((32U + generation - replace->generation()) & 31U)", 1),
    ("TtAgePenalty", "s", "        const int score = entry.depth - 4 * age;",
     "        const int score = entry.depth - " + T + "TtAgePenalty * age;", 1, 2),
    ("TtAgePenalty", "s", "        if (entry.depth - 4 * relative_age(entry) < replace->depth - 4 * relative_age(*replace)) replace = &entry;",
     "        if (entry.depth - " + T + "TtAgePenalty * relative_age(entry) < replace->depth - " + T + "TtAgePenalty * relative_age(*replace)) replace = &entry;", 1),
    ("TtStoreDepthSlack", "s", "depth + 4 > entry->depth ||", "depth + " + T + "TtStoreDepthSlack > entry->depth ||", 2, 4),
    ("QuietCheckBonus", "s", "            if ((check_squares[pt] & square_bb(move.to)) != 0) value += 12000;",
     "            if ((check_squares[pt] & square_bb(move.to)) != 0) value += " + T + "QuietCheckBonus;", 1),
    ("QuietCheckBonus", "s", "            return searcher_.quiet_history(board_, ss_, move) + (direct_check(move) ? 12000 : 0);",
     "            return searcher_.quiet_history(board_, ss_, move) + (direct_check(move) ? " + T + "QuietCheckBonus : 0);", 1),
    ("CaptureValueWeight", "s", "            int score = 10 * value + capture_history[moved][move.to][victim];",
     "            int score = " + T + "CaptureValueWeight * value + capture_history[moved][move.to][victim];", 1),
    ("CaptureValueWeight", "s", "            int score = 10 * capture_value(board_, move) + searcher_.capture_history_value(board_, move);",
     "            int score = " + T + "CaptureValueWeight * capture_value(board_, move) + searcher_.capture_history_value(board_, move);", 1),
    ("PromoQueenScore,PromoUnderScore", "s", "            if (move.is_promotion()) score += move.promotion == Queen ? 20000 : -5000;",
     "            if (move.is_promotion()) score += move.promotion == Queen ? " + T + "PromoQueenScore : " + T + "PromoUnderScore;", 1),
    ("NoisyValueWeight,NoisyMoverDiv", "s",
     "return 1'000'000 + 10 * capture_value(board_, move) -\n                       SeePieceValue[static_cast<std::size_t>(piece_type(board_.moved_piece(move)))] / 10;",
     "return 1'000'000 + " + T + "NoisyValueWeight * capture_value(board_, move) -\n                       SeePieceValue[static_cast<std::size_t>(piece_type(board_.moved_piece(move)))] / " + T + "NoisyMoverDiv;", 1),
    ("CorrectionClampDiv", "s", "    const int diff = std::clamp((best_score - static_eval) * CorrectionGrain, -CorrectionLimit / 4, CorrectionLimit / 4);",
     "    const int diff = std::clamp((best_score - static_eval) * CorrectionGrain, -CorrectionLimit / " + T + "CorrectionClampDiv, CorrectionLimit / " + T + "CorrectionClampDiv);", 1),
    ("CorrectionWeightCap", "s", "    const int weight = std::min(depth + 1, 16);",
     "    const int weight = std::min(depth + 1, " + T + "CorrectionWeightCap);", 1),
    ("ContHistBack4Div", "s", "back == 4 ? bonus / 2 : bonus", "back == 4 ? bonus / " + T + "ContHistBack4Div : bonus", 1),
    ("SingularExtPlies", "s", "\n                extension = 1;", "\n                extension = " + T + "SingularExtPlies;", 1),
    ("SingularTtCutExt", "s", "                extension = -2;", "                extension = " + T + "SingularTtCutExt;", 1),
    ("SingularCutNodeExt", "s", "                extension = -1;", "                extension = " + T + "SingularCutNodeExt;", 1),
    ("CheckExtPlies", "s", "\n            extension = 1;", "\n            extension = " + T + "CheckExtPlies;", 1),
    ("LmrFullDepthMoves,LmrFullDepthMovesRoot", "s", "            move_count > 1 + (root_node ? 1 : 0) && !bare_king_mode &&",
     "            move_count > " + T + "LmrFullDepthMoves + (root_node ? " + T + "LmrFullDepthMovesRoot : 0) && !bare_king_mode &&", 1),
]

DECL_ANCHOR = "int LmrCutoffThreshold = 3;"
TABLE_ANCHOR = '        {"LmrCutoffThreshold", &LmrCutoffThreshold, 0, 20},'
EXTERN_ANCHOR = "extern int LmrCutoffThreshold;    // child cutoff count above which late moves are reduced more (0 = off)"

def find_lines(text, needle):
    skip = 1 if needle.startswith("\n") else 0
    out, start = [], 0
    while True:
        i = text.find(needle, start)
        if i < 0:
            break
        out.append(text.count("\n", 0, i + skip) + 1)
        start = i + len(needle)
    return out

def kind_of(bound):
    return bound.split(":", 1)[0].strip()

# ---------------------------------------------------------------- bounds check (c)
def bounds_check(rows, out):
    bad = []
    for r in rows:
        name, d, lo, hi, st = r["name"], r["default"], r["min"], r["max"], r["step"]
        kind = kind_of(r["bound"])
        one = "one side" in r["bound"]
        msgs = []
        if st < 1:
            msgs.append("step < 1")
        if not r["bound"].strip():
            msgs.append("bound by empty")
        if one:
            if "minus only" in r["bound"] and not (lo <= d - st and d + st > hi):
                msgs.append("one side minus claimed but plus side fits or minus does not")
            if "plus only" in r["bound"] and not (d - st < lo and d + st <= hi):
                msgs.append("one side plus claimed but minus side fits or plus does not")
        else:
            if not (lo <= d - st):
                msgs.append(f"min {lo} > default-step {d-st}")
            if not (d + st <= hi):
                msgs.append(f"default+step {d+st} > max {hi}")
        if kind == "divisor" and lo < 1:
            msgs.append("divisor row with min < 1")
        if kind == "index":
            cap = None
            if "stack_[" in r["bound"]:
                cap = int(r["bound"].split("stack_[", 1)[1].split("]", 1)[0])
            if cap is None:
                msgs.append("index row names no array bound")
            elif hi > cap:
                msgs.append(f"index row max {hi} above its bound stack_[{cap}]")
        status = "OK" if not msgs else "FAIL"
        out.append(f"{status}\t{name}\t{d}\t[{lo},{hi}]\tstep {st}\t{kind}\t{'; '.join(msgs)}")
        if msgs:
            bad.append(name)
    return bad

# ---------------------------------------------------------------- patch builder (a)(b)(e)
def build_tree(src_tree, dst, rows, guide, tag):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src_tree, dst, ignore=shutil.ignore_patterns("build"))
    search_p = os.path.join(dst, "src/search.cpp")
    hpp_p = os.path.join(dst, "include/forge/search.hpp")
    search = open(search_p).read()
    hpp = open(hpp_p).read()
    orig = {"src/search.cpp": search, "include/forge/search.hpp": hpp}

    decls = DECL_ANCHOR + "\n// job 37 census options (kimi5): defaults are today's hand-set numbers.\n" + \
            "\n".join(f"int {r['name']} = {r['default']};" for r in rows)
    table = TABLE_ANCHOR + "\n" + "\n".join(
        f'        {{"{r["name"]}", &{r["name"]}, {r["min"]}, {r["max"]}}},' for r in rows)
    externs = EXTERN_ANCHOR + "\n" + "\n".join(f"extern int {r['name']};" for r in rows)

    for anchor, block, fname in ((DECL_ANCHOR, decls, "src/search.cpp"),
                                 (TABLE_ANCHOR, table, "src/search.cpp"),
                                 (EXTERN_ANCHOR, externs, "include/forge/search.hpp")):
        text = search if fname.endswith(".cpp") else hpp
        if text.count(anchor) != 1:
            print(f"FAIL anchor count for {anchor[:50]} in {tag}")
            sys.exit(1)
        if fname.endswith(".cpp"):
            search = search.replace(anchor, block)
        else:
            hpp = hpp.replace(anchor, block)
        guide.append(("(registration)", fname, find_lines(orig[fname], anchor)[0],
                      anchor.strip(), f"+ {len(rows)} option {'decls' if fname.endswith('hpp') else 'rows'}"))

    spec_lines = {}
    for r in rows:
        for ln in r["lines"]:
            spec_lines.setdefault(r["name"], set()).add(ln)
    found_by_opt = {}

    for site in SITES:
        opt, fcode, old, new, want = site[0], site[1], site[2], site[3], site[4]
        if tag == "kF" and len(site) > 5:
            want = site[5]
        text = search if fcode == "s" else hpp
        fname = "src/search.cpp" if fcode == "s" else "include/forge/search.hpp"
        found = find_lines(orig[fname], old)
        if len(found) == want and text.count(old) != want:
            print(f"FAIL {tag} count drifted for {opt}: {old[:70]!r}")
            sys.exit(1)
        if len(found) != want:
            print(f"FAIL {tag} count {len(found)} != {want} for {opt}: {old[:70]!r}")
            sys.exit(1)
        for rname in opt.split(","):
            if not any(x["name"] == rname for x in rows):
                print(f"FAIL {rname} in sites but not in spec")
                sys.exit(1)
            found_by_opt.setdefault(rname, set()).update(found)
        guide.append((opt, fname, ",".join(str(x) for x in found), old.strip(), new.strip()))
        if fcode == "s":
            search = search.replace(old, new)
        else:
            hpp = hpp.replace(old, new)

    if tag == "r15d":  # the spec's "lines" column holds r15d lines only
        for rname, speclines in spec_lines.items():
            missing = speclines - found_by_opt.get(rname, set())
            if missing:
                print(f"FAIL {tag} spec lines {sorted(missing)} of {rname} not among found {sorted(found_by_opt.get(rname, set()))}")
                sys.exit(1)

    open(search_p, "w").write(search)
    open(hpp_p, "w").write(hpp)

def make_patch(orig, patched, out_path):
    chunks = []
    for rel in ("src/search.cpp", "include/forge/search.hpp"):
        p = subprocess.run(["diff", "-u", "--label", f"a/{rel}", "--label", f"b/{rel}",
                            os.path.join(orig, rel), os.path.join(patched, rel)],
                           capture_output=True, text=True)
        if p.returncode == 1:
            chunks.append(p.stdout)
        elif p.returncode != 0:
            print("FAIL diff: " + p.stderr)
            sys.exit(1)
    with open(out_path, "w") as f:
        f.write("".join(chunks))
    return sum(c.count("@@") // 2 for c in chunks)

# ---------------------------------------------------------------- run list (d)
def run_list(rows, extra_out):
    out = ["option\tside\tvalue"]
    for r in rows:
        if "new (K5)" not in r["tune"]:
            continue
        d, st, lo, hi = r["default"], r["step"], r["min"], r["max"]
        if d - st >= lo:
            out.append(f"{r['name']}\tm\t{d - st}")
        if d + st <= hi:
            out.append(f"{r['name']}\tp\t{d + st}")
    il = next(r for r in rows if r["name"] == "ImprovingLookback")
    out.append(f"ImprovingLookback\tp\t{il['default'] + il['step']}")
    extra_out.write("\n".join(out) + "\n")
    return len(out) - 1

# ---------------------------------------------------------------- main
def main():
    spec_path, r15d_tree, kf_tree, outdir = sys.argv[1:5]
    bounds_only = len(sys.argv) > 5 and sys.argv[5] == "--bounds-only"
    os.makedirs(outdir, exist_ok=True)
    rows, tuner = read_spec(spec_path)

    lines = [f"bounds check on {spec_path}: {len(rows)} rows"]
    bad = bounds_check(rows, lines)
    lines.append(f"RESULT: {'FAIL rows: ' + ', '.join(bad) if bad else 'all rows OK'}")
    with open(os.path.join(outdir, "bounds_check.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    if bad:
        print("BOUNDS FAIL: " + ", ".join(bad))
        sys.exit(1)
    print(f"bounds OK ({len(rows)} rows)")
    if bounds_only:
        return

    guide = []
    build_tree(r15d_tree, "/tmp/j37/patched_r15d", rows, guide, "r15d")
    hunks_a = make_patch(r15d_tree, "/tmp/j37/patched_r15d", os.path.join(outdir, "census_r15d.patch.txt"))

    kf_guide_len = len(guide)
    build_tree(kf_tree, "/tmp/j37/patched_kF", rows, guide, "kF")
    hunks_b = make_patch(kf_tree, "/tmp/j37/patched_kF", os.path.join(outdir, "census_kF.patch.txt"))

    with open(os.path.join(outdir, "reading_guide.tsv"), "w") as f:
        f.write("option\tfile\tr15d line\told text\tnew text\n")
        for opt, fname, ln, old, new in guide[:kf_guide_len]:
            f.write(f"{opt}\t{fname}\t{ln}\t{old.replace(chr(10), chr(92)+chr(110))}\t{new.replace(chr(10), chr(92)+chr(110))}\n")

    with open(os.path.join(outdir, "runlist.tsv"), "w") as f:
        n_runs = run_list(rows, f)
    print(f"patches: r15d {hunks_a} hunks, kF {hunks_b} hunks; guide rows {kf_guide_len}; runs {n_runs}")

main()
