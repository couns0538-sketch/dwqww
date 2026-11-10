"""Name and mechanism search for DUPCHECK.md (read-only on everything it searches).

For every item (a closed item of the brief, a prior speed switch, or a pool candidate) it runs a NAME
regex and a MECHANISM regex over
  1. the branch-tip text corpus (tools/fetch_corpus.py; .md .cpp .hpp .h .patch .diff of every fetched branch),
  2. the commit messages of every fetched branch,
  3. text files (<= 2 MB) and file names in the crew / QA folders on the PC that this job may read.
Never searched: F:\\ospd, C:\\ospd_hunt, D:\\forge_jobs_20261107 (banned for this job).

Output: one TSV row per (item, kind, source) with the hit count and up to 6 example locations, and a
printed summary. The verdicts in DUPCHECK.md are written by hand from this file.

usage: dupcheck_search.py REPO CORPUS_DIR OUT_TSV
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402

PC_ROOTS = [
    r"D:\forge_qa", r"D:\forge-qa", r"D:\sdk_jobs\sdk_longjob_20261106", r"D:\grok_sdk_speed_20261107",
    r"D:\forge_deepres_20261109", r"D:\forge-runs", r"D:\forge_coder_checks",
    r"D:\qa_speed_bundle_20261105", r"D:\qa_speed_bundles_partial_20261105", r"D:\qa_speed_quiet_20261105",
    r"D:\qa_simd_pc_20261105", r"D:\qa_vnni_20261105",
    r"C:\Users\Administrator\grok-pc\incoming", r"C:\Users\Administrator\grok-pc\forge_deepres_stage_20261109",
    r"C:\Users\Administrator\grok-pc\crew_gates_20261107", r"C:\Users\Administrator\grok-pc\coder-fuzz",
    r"C:\Users\Administrator\grok-pc\forge_push\qa_reports", r"C:\Users\Administrator\grok-pc\forge_push\locks",
    r"C:\Users\Administrator\grok-pc\forge_push\sdk_speedonly_20261107",
    r"C:\Users\Administrator\grok-pc\forge_push\overnight_timing_20261108",
]
PC_TOP_ONLY = [r"C:\Users\Administrator\grok-pc\forge_push"]          # top-level file names and small text files only
BANNED = ("f:\\ospd", "c:\\ospd_hunt", "d:\\forge_jobs_20261107")
TEXT_EXT = {".md", ".txt", ".patch", ".diff", ".cpp", ".hpp", ".h", ".ps1", ".py", ".sh", ".json", ".csv", ".ok", ".log"}
SKIP_DIR = {".git", "obj", "m2gen", "m2use", "__pycache__", "node_modules"}
MAX_BYTES = 2_000_000
MAX_DEPTH = 5

# (item, group, name regex, mechanism regex or None)
ITEMS = [
    # --- closed list of the brief ---
    ("H4 SLIDER_PDEP16", "brief-closed", r"SLIDER_PDEP16|slider_pdep16", r"_pdep_u64|pdep\(pext"),
    ("FT-accum / finny refresh", "brief-closed", r"FORGE_NNUE_FINNY|finny|FT.?accum", r"refresh.?cache|RefreshCache|accumulator refresh"),
    ("KING_LINES", "brief-closed", r"FORGE_SPD_KING_LINES|KING_LINES", r"refresh_king_lines|single_blockers"),
    ("CorrHistPrefetch", "brief-closed", r"CorrHistPrefetch|T05D-03", r"prefetch[^\n]{0,60}correction|correction[^\n]{0,60}prefetch"),
    ("int16 accumulators", "brief-closed", r"FORGE_NNUE_INT16|NNUE_W1_INT16|FORGE_SDK_NNUE_INT|T05-01", r"int16[^\n]{0,30}(accumulator|first.layer|w1)"),
    ("MATKEY_FAST", "brief-closed", r"MATKEY_FAST", r"closed form[^\n]{0,60}(material|key)"),
    ("AVX2/AVX-512/VNNI NNUE", "brief-closed", r"FORGE_SPD_NNUE_ZMM|FORGE_SPD_NNUE_AVX512|INT8_VNNI|FORGE_NNUE_AVX2", r"_mm512_|vpdpbusd"),
    ("lockless TT / nodes_ layout", "brief-closed", r"TtLockless|FORGE_SMP_LAYOUT|smp_layout|lockless", r"false sharing|alignas\(64\)[^\n]{0,40}nodes_"),
    ("C2 MATKEY_ONCE", "brief-closed", r"MATKEY_ONCE|matkey_once|52597688", r"material_key\(board\)[^\n]{0,80}once|node_material"),
    ("QUIET_FLAG", "brief-closed", r"QUIET_FLAG|quietflag|8fcd0679|62acae36", r"moves_\[index_ - 1\]\.skip"),
    ("e4gate", "brief-closed", r"e4gate|e5gate|enc4|enc5", None),
    ("SMP NODELIMIT_D1 / EARLYSTOP_D1", "brief-closed", r"NODELIMIT|EARLYSTOP|nodelimit|earlystop", None),
    ("PICKBEST", "brief-closed", r"FORGE_SPD_PICKBEST|PICKBEST|T05D-02", r"score << 32|first.maximum scan"),
    ("raw-eval cache", "brief-closed", r"EvalCacheKB|FORGE_EVAL_MEMO|EvalMemo|T05F-01|nps_abba_evalcache", r"eval(uation)? (cache|memo)"),
    # --- prior speed switches found in the inventory (treated as closed) ---
    ("H1/H7 LARGEPAGES", "prior", r"FORGE_SPD_LARGEPAGES", None),
    ("H2/D4d DIRTY_INPLACE", "prior", r"DIRTY_INPLACE", None),
    ("H3 NNUE_COLUMNS", "prior", r"NNUE_COLUMNS", None),
    ("H5/D4b MOVE_STORE32", "prior", r"MOVE_STORE32", None),
    ("H6 PICK_FIRST", "prior", r"PICK_FIRST", None),
    ("H8 HCE_LOCALS", "prior", r"HCE_LOCALS", None),
    ("H9 PTYPE_ARITH", "prior", r"PTYPE_ARITH", None),
    ("B4a BADCAP_PREFIX", "prior", r"BADCAP_PREFIX", None),
    ("B4b PICKER_SCRATCH", "prior", r"PICKER_SCRATCH", None),
    ("B7a QS_STALEMATE_LATE", "prior", r"QS_STALEMATE_LATE", None),
    ("B7b LEGAL_WITNESS", "prior", r"LEGAL_WITNESS", None),
    ("B10 SEE_HOIST", "prior", r"SEE_HOIST", None),
    ("D4c MOVE_EQ32", "prior", r"MOVE_EQ32", None),
    ("B9e EVASION_GEN", "prior", r"EVASION_GEN|evasion_gen", None),
    ("TT_REPLACE_CACHE", "prior", r"TT_REPLACE_CACHE", None),
    ("PAWN_ENTRY32 / T05B-01", "prior", r"PAWN_ENTRY32|T05B-01|pawn-king entry", None),
    # --- pool candidates of this job ---
    ("cand WITNESS_NOPIN", "candidate", r"WITNESS_NOPIN|HASLEGAL_FAST",
     r"has_legal_move[\s\S]{0,600}?(queen line|line of the own king|cannot be pinned|attacks::line\()"),
    ("cand EVADE_LEGAL", "candidate", r"EVADE_LEGAL|FORGE_CHECK_INFO|checkMask|check.mask",
     r"more_than_one\(checkers_?\)|between\((king|ksq|king_square\([a-z_]+\))[^)]*\)[^\n]{0,80}checkers|to = checker or between|checker or between"),
    ("cand CHECKERS_KL", "candidate", r"CHECKERS_KL|incrcheck|tri-state hint|gives.check hint",
     r"checkers_\s*=\s*(?!attackers_to|0\b|undo|candidate|compute_checkers|other)[^;\n]{3,}"),
    ("cand PAWN_CAPMASK", "candidate", r"PAWN_CAPMASK|CAPMASK",
     r"capturers\s*=\s*pawns\s*&|pawn_attacks_bb\((them|opposite\(us\)),\s*enemy\)"),
    ("cand HCE_REUSE", "candidate", r"HCE_REUSE",
     r"WeakQueen[^\n]{0,160}reus|reus[^\n]{0,160}WeakQueen|queen_bishop|queen_rook|q_bishop|q_rook"),
    ("cand KL_LAZY", "candidate", r"KL_LAZY",
     r"(pins?|checks?)_valid|valid_(pins?|checks?)|lazy[^\n]{0,40}king.?lines|king.?lines[^\n]{0,60}(split|lazily in two|two halves)"),
]


def load_manifest(corpus):
    m = {}
    path = os.path.join(corpus, "MANIFEST.tsv")
    with open(path, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 5 and p[2] != "SKIPPED_TOO_BIG":
                m[os.path.normpath(os.path.join(corpus, p[2]))] = f"{p[3]}:{p[4]}"
    return m


def walk(root, top_only=False):
    low = root.lower()
    if any(low.startswith(b) for b in BANNED):
        return
    base_depth = root.rstrip("\\").count("\\")
    for d, dirs, files in os.walk(root):
        if top_only:
            dirs[:] = []
        else:
            dirs[:] = [x for x in dirs if x not in SKIP_DIR]
            if d.count("\\") - base_depth >= MAX_DEPTH:
                dirs[:] = []
        for name in files:
            yield os.path.join(d, name)


def main():
    repo, corpus, out = sys.argv[1], sys.argv[2], sys.argv[3]
    print(pinguard.ensure(), flush=True)
    compiled = [(item, group, re.compile(nrx), re.compile(mrx) if mrx else None) for item, group, nrx, mrx in ITEMS]
    hits = {}   # (item, kind, source) -> [count, examples]

    def add(item, kind, source, where, n):
        e = hits.setdefault((item, kind, source), [0, []])
        e[0] += n
        if len(e[1]) < 6:
            e[1].append(where)

    def scan_text(text, where, source):
        for item, _group, nrx, mrx in compiled:
            n = len(nrx.findall(text))
            if n:
                add(item, "name", source, where, n)
            if mrx is not None:
                n = sum(1 for _ in mrx.finditer(text))
                if n:
                    add(item, "mechanism", source, where, n)

    # 1. corpus
    manifest = load_manifest(corpus)
    n_corpus = 0
    for path, origin in manifest.items():
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        n_corpus += 1
        scan_text(text, origin, "corpus")
    print(f"corpus files searched: {n_corpus}", flush=True)

    # 2. commit messages
    log = subprocess.run(["git", "-C", repo, "log", "--remotes=origin", "--format=%h%x09%s%x09%b%x1e"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout
    commits = [c.strip() for c in log.split("\x1e") if c.strip()]
    for c in commits:
        scan_text(c, "commit " + c.split("\t", 1)[0], "commits")
    print(f"commit messages searched: {len(commits)}", flush=True)

    # 3. PC folders: names and small text files
    n_files = n_text = 0
    for root, top in [(r, False) for r in PC_ROOTS] + [(r, True) for r in PC_TOP_ONLY]:
        if not os.path.isdir(root):
            print(f"missing PC root: {root}", flush=True)
            continue
        for path in walk(root, top):
            n_files += 1
            for item, _group, nrx, _m in compiled:
                if nrx.search(os.path.basename(path)):
                    add(item, "name", "pc-filename", path, 1)
            ext = os.path.splitext(path)[1].lower()
            if ext not in TEXT_EXT:
                continue
            try:
                if os.path.getsize(path) > MAX_BYTES:
                    continue
                text = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            n_text += 1
            scan_text(text, path, "pc-text")
    print(f"PC files seen: {n_files}, text files searched: {n_text}", flush=True)

    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("item\tgroup\tkind\tsource\thits\texamples\n")
        for item, group, _n, _m in compiled:
            for kind in ("name", "mechanism"):
                for source in ("corpus", "commits", "pc-filename", "pc-text"):
                    e = hits.get((item, kind, source))
                    if e:
                        f.write(f"{item}\t{group}\t{kind}\t{source}\t{e[0]}\t{' | '.join(e[1])}\n")
                    elif not (kind == "mechanism" and source == "pc-filename"):
                        f.write(f"{item}\t{group}\t{kind}\t{source}\t0\t\n")
    for item, group, _n, _m in compiled:
        parts = []
        for kind in ("name", "mechanism"):
            for source in ("corpus", "commits", "pc-filename", "pc-text"):
                e = hits.get((item, kind, source))
                if e:
                    parts.append(f"{kind[0]}:{source}={e[0]}")
        print(f"{group:12} {item:34} {' '.join(parts) or 'NO HITS'}", flush=True)


if __name__ == "__main__":
    main()
