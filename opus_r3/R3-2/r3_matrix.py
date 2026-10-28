#!/usr/bin/env python3
"""R3-2 interaction matrix: bench nodes and paired ABBA CPU-time NPS of Forge configurations against the all-OFF
engine (adapted from opus_round1/sol_S29/nps_ab.py and opus_round1/sol_SIT/nps_ab_opts.py).

A configuration = one exe (build switches) + UCI options + Threads + the single configurations it combines.
  T1 configurations: the engine's `bench <depth>`. Bench always searches with its own Searcher (1 worker, 16 MB
     table, src/uci.cpp `forge::Searcher bench_searcher(16)`), so Threads never reaches bench.
  T2 configurations: the 8 bench positions searched with `ucinewgame` / `position fen` / `go depth <d>` at
     Threads 2, Hash 16 on the main searcher (the only way to search with 2 workers). Nodes = the last
     `info depth` line of each search; they vary from run to run (lazy SMP).
Every run is a fresh process created at IDLE priority (plus `nice -n 19` around this script). CPU time is taken with
GetProcessTimes (user + kernel, all threads) right before the measured command and right after its last output line,
so start-up and net loading are excluded; QueryProcessCycleTime is recorded as a finer-grained cross-check.

subcommands (common options: --build-dir, --net-dir, --syzygy, --out):
  list                                    print the configurations
  nets   --worktree W                     write the replica nets (forge_nnue_v2.py from-inc, O4 standalone_copy.py)
  nodes  [--only k1,k2] [--reps 2]        bench d11/d13/d16 of every T1 configuration, --reps fresh processes each
  nps    [--only k1,k2] [--runs 8] [--depth 16] [--skip-done]
                                          ABBA (A = OFF exe, no options, same Threads; B = the configuration),
                                          --runs fresh processes per side
  report [--md out.md]                    matrix table + pair analysis from the saved JSON results
"""
import argparse
import json
import math
import os
import re
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path

PINS = {11: 312866, 13: 862329, 16: 3024920}
DEPTHS = (11, 13, 16)
BENCH_FENS = (   # src/uci.cpp, command "bench"
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
)
EXES = ("base", "base_copy", "o2", "nozero", "s13", "speedstack", "ss_s13",
        "base_h3", "o2_h3", "lazy", "o2_lazy", "prof", "int16", "o2_int16", "int16_lazy")
EXE_FLAGS = {"base": "", "base_copy": "(byte copy of base.exe)", "o2": "-DFORGE_NNUE_O2=1",
             "nozero": "-DFORGE_NOZERO_MOVE_BUFFERS=1", "s13": "-DFORGE_S13_TT_CHILD_PREFETCH=1",
             "speedstack": "-DFORGE_SPEEDSTACK=1", "ss_s13": "-DFORGE_SPEEDSTACK=1 -DFORGE_S13_TT_CHILD_PREFETCH=1",
             "base_h3": "", "o2_h3": "-DFORGE_NNUE_O2=1",
             "lazy": "-DFORGE_NNUE_LAZY_ACC=1", "o2_lazy": "-DFORGE_NNUE_O2=1 -DFORGE_NNUE_LAZY_ACC=1",
             "prof": "-DFORGE_PROF=1 (+ src/profile.cpp)", "int16": "-DFORGE_NNUE_INT16=1",
             "o2_int16": "-DFORGE_NNUE_O2=1 -DFORGE_NNUE_INT16=1",
             "int16_lazy": "-DFORGE_NNUE_INT16=1 -DFORGE_NNUE_LAZY_ACC=1"}
# Stack head each exe was built from: 467a59b3 = the exes of build_all.sh (source 2432670b = opus-r3-stack@467a59b3 +
# the CMake test fix); 330237f3 = the final R3-1 head (merged into this branch, build_h3.sh). The final head's default
# build is not byte-identical to the first pass (HardDeadline output fix in the default path), so every configuration
# built from it is timed against base_h3 (same head), and H3DRIFT times base_h3 against the first-pass base.
EXE_HEAD = {k: "467a59b3" for k in EXES}
EXE_HEAD.update({k: "330237f3" for k in ("base_h3", "o2_h3", "lazy", "o2_lazy", "prof", "int16", "o2_int16",
                                          "int16_lazy")})
# replica nets: file -> forge_nnue_v2.py from-inc arguments (None = O4 standalone_copy.py of r1.fnn2)
NETS = {
    "r1.fnn2": ["--replica", "r1"],
    "rm8.fnn2": ["--replica", "rm8"],
    "r1_ob8.fnn2": ["--replica", "r1", "--output-buckets", "8"],
    "r1_t.fnn2": ["--replica", "r1", "--threats-zero"],
    "r1_p.fnn2": ["--replica", "r1", "--pawn-pairs-zero"],
    "r1_t_p.fnn2": ["--replica", "r1", "--threats-zero", "--pawn-pairs-zero"],
    "r1_t_ob8.fnn2": ["--replica", "r1", "--threats-zero", "--output-buckets", "8"],
    "r1_p_ob8.fnn2": ["--replica", "r1", "--pawn-pairs-zero", "--output-buckets", "8"],
    "r1_t_p_ob8.fnn2": ["--replica", "r1", "--threats-zero", "--pawn-pairs-zero", "--output-buckets", "8"],
    "r1_pure.fnn2": None,
}


# ----------------------------------------------------------------------------------------------- configurations
def configs(net_dir, syzygy):
    """Every configuration of the matrix. expect: exact = node-exact by design (bench == lock pins);
    tree = changes the search tree. ref = the branch's own ON pins (d11, d13, d16) where a report gives them."""
    n = lambda f: str(Path(net_dir) / f)
    v2 = lambda f, *o: list(o) + [("NNUEFile", n(f))]   # request options first, NNUEFile last
    C = []

    def add(key, label, group, exe="base", opts=(), threads=1, parts=(), expect="exact", ref=None, v2part=False,
            nodes=True, nps=True, note="", cmd="bench", a_exe=None):
        a_exe = a_exe or ("base_h3" if EXE_HEAD[exe] == "330237f3" else "base")   # A side: OFF of the same head
        C.append(dict(key=key, label=label, group=group, exe=exe, opts=[list(o) for o in opts], threads=threads,
                      parts=list(parts), expect=expect, ref=ref, v2=v2part, nodes=nodes and threads == 1,
                      nps=nps, note=note, cmd=cmd, head=EXE_HEAD[exe], a_exe=a_exe))

    # controls
    add("OFF", "OFF (base.exe, no options)", "control", nps=False)
    add("AA_T1", "A/A control T1 (base_copy.exe)", "control", exe="base_copy")
    add("AA_T2", "A/A control T2 (base_copy.exe, Threads 2)", "control", exe="base_copy", threads=2)
    # runtime options alone (T1 bench)
    add("CHP1", "CorrHistPlus=1", "single", opts=[("CorrHistPlus", "1")], expect="tree", ref=(318363, 915778, 2347193))
    add("CHP2", "CorrHistPlus=2", "single", opts=[("CorrHistPlus", "2")], expect="tree", ref=(296553, 824640, 2914749))
    add("CHP4", "CorrHistPlus=4", "single", opts=[("CorrHistPlus", "4")], expect="tree", ref=(340927, 734347, 2794671))
    add("CHP7", "CorrHistPlus=7", "single", opts=[("CorrHistPlus", "7")], expect="tree", ref=(317529, 866764, 2715911))
    add("CM", "CorrMargins=1", "single", opts=[("CorrMargins", "1")], expect="tree", ref=(343365, 858019, 2522546))
    add("CE", "CorrExt=1", "single", opts=[("CorrExt", "1")], expect="tree", ref=(312961, 838790, 2891507))
    add("CR", "CuckooRep=true", "single", opts=[("CuckooRep", "true")], expect="tree", ref=(324211, 790682, 3148570))
    add("MKT", "MaterialKeyTable=true", "single", opts=[("MaterialKeyTable", "true")])
    add("NS99", "NetScale=99", "single", opts=[("NetScale", "99")], expect="tree")
    add("HR1", "HistRework=1", "single", opts=[("HistRework", "1")], expect="tree", ref=(373261, 1043893, 3399770))
    add("HR2", "HistRework=2", "single", opts=[("HistRework", "2")], expect="tree", ref=(320427, 881902, 3041041))
    add("IT", "IntendedThreefold=true", "single", opts=[("IntendedThreefold", "true")],
        note="bench positions carry no game history, so no claim can fire")
    add("HD10", "HardDeadline=10", "single", opts=[("HardDeadline", "10")], note="bench is unclocked")
    add("SYZ", "SyzygyPath=syzygy345", "single", opts=[("SyzygyPath", syzygy)], expect="tree",
        ref=(313631, 866959, 2460490))
    add("LTT_T1", "LocklessTT=true (T1)", "single", opts=[("LocklessTT", "true")])
    add("SEN_T1", "SmpExactNodes=true (T1)", "single", opts=[("SmpExactNodes", "true")], nps=False)
    add("SBT_T1", "SmpBestThread=true (T1)", "single", opts=[("SmpBestThread", "true")], nps=False)
    add("LTT_T2", "LocklessTT=true (T2)", "single", opts=[("LocklessTT", "true")], threads=2)
    add("SEN_T2", "SmpExactNodes=true (T2)", "single", opts=[("SmpExactNodes", "true")], threads=2)
    add("SBT_T2", "SmpBestThread=true (T2)", "single", opts=[("SmpBestThread", "true")], threads=2)
    # v2 options alone, function-preserving replica nets (PureNnue: the r1 weights flagged stand-alone, no HCE)
    add("V2R1", "v2 path: r1 replica, NNUEKingBuckets=1", "single-v2", opts=v2("r1.fnn2", ("NNUEKingBuckets", "1")),
        v2part=True)
    add("KB8", "NNUEKingBuckets=8 (rm8 replica)", "single-v2", opts=v2("rm8.fnn2", ("NNUEKingBuckets", "8")), v2part=True)
    add("OB8", "NNUEOutputBuckets=8 (r1 + 8 heads)", "single-v2", opts=v2("r1_ob8.fnn2", ("NNUEOutputBuckets", "8")),
        v2part=True)
    add("THR", "NNUEThreats=1 (r1 + zero threats)", "single-v2", opts=v2("r1_t.fnn2", ("NNUEThreats", "1")), v2part=True)
    add("PP", "NNUEPawnPairs=1 (r1 + zero pawn pairs)", "single-v2", opts=v2("r1_p.fnn2", ("NNUEPawnPairs", "1")),
        v2part=True)
    add("PURE", "PureNnue=1 (r1 weights stand-alone)", "single-v2", opts=v2("r1_pure.fnn2", ("PureNnue", "1")),
        expect="tree", v2part=True, note="no function-preserving pure net exists: the HCE term is dropped")
    # compile switches alone
    add("O2", "FORGE_NNUE_O2", "switch", exe="o2")
    add("NOZERO", "FORGE_NOZERO_MOVE_BUFFERS", "switch", exe="nozero")
    add("S13SW", "FORGE_S13_TT_CHILD_PREFETCH, option off", "switch", exe="s13")
    add("TCP", "FORGE_S13_TT_CHILD_PREFETCH + TtChildPrefetch=true", "switch", exe="s13",
        opts=[("TtChildPrefetch", "true")])
    add("SS", "FORGE_SPEEDSTACK", "switch", exe="speedstack")
    # TT group
    add("LTT_TCP_T1", "LocklessTT + TtChildPrefetch (T1)", "TT", exe="s13",
        opts=[("LocklessTT", "true"), ("TtChildPrefetch", "true")], parts=["LTT_T1", "TCP"])
    add("TCP_T2", "TtChildPrefetch=true (T2)", "TT", exe="s13", opts=[("TtChildPrefetch", "true")], threads=2)
    add("LTT_TCP_T2", "LocklessTT + TtChildPrefetch (T2)", "TT", exe="s13",
        opts=[("LocklessTT", "true"), ("TtChildPrefetch", "true")], threads=2, parts=["LTT_T2", "TCP_T2"])
    add("SS_TCP", "FORGE_SPEEDSTACK + S13 switch + TtChildPrefetch (T1)", "TT-extra", exe="ss_s13",
        opts=[("TtChildPrefetch", "true")], parts=["SS", "TCP"])
    add("SS_MKT", "FORGE_SPEEDSTACK + MaterialKeyTable", "extra", exe="speedstack",
        opts=[("MaterialKeyTable", "true")], parts=["SS", "MKT"])
    # correction group (CorrHistPlus at 7 = all three keys)
    add("CHP7_CM", "CorrHistPlus=7 + CorrMargins", "corr", opts=[("CorrHistPlus", "7"), ("CorrMargins", "1")],
        parts=["CHP7", "CM"], expect="tree")
    add("CHP7_CE", "CorrHistPlus=7 + CorrExt", "corr", opts=[("CorrHistPlus", "7"), ("CorrExt", "1")],
        parts=["CHP7", "CE"], expect="tree")
    add("CM_CE", "CorrMargins + CorrExt", "corr", opts=[("CorrMargins", "1"), ("CorrExt", "1")],
        parts=["CM", "CE"], expect="tree")
    add("CHP7_CM_CE", "CorrHistPlus=7 + CorrMargins + CorrExt", "corr",
        opts=[("CorrHistPlus", "7"), ("CorrMargins", "1"), ("CorrExt", "1")], parts=["CHP7", "CM", "CE"], expect="tree")
    # search-instance matrix extras (CuckooRep is the third instance option) and shared-code extras
    add("CM_CR", "CorrMargins + CuckooRep", "instances", opts=[("CorrMargins", "1"), ("CuckooRep", "true")],
        parts=["CM", "CR"], expect="tree")
    add("CE_CR", "CorrExt + CuckooRep", "instances", opts=[("CorrExt", "1"), ("CuckooRep", "true")],
        parts=["CE", "CR"], expect="tree")
    add("CM_CE_CR", "CorrMargins + CorrExt + CuckooRep", "instances",
        opts=[("CorrMargins", "1"), ("CorrExt", "1"), ("CuckooRep", "true")], parts=["CM", "CE", "CR"], expect="tree")
    add("HR2_CHP7", "HistRework=2 + CorrHistPlus=7", "extra", opts=[("HistRework", "2"), ("CorrHistPlus", "7")],
        parts=["HR2", "CHP7"], expect="tree")
    add("IT_CR", "IntendedThreefold + CuckooRep", "extra", opts=[("IntendedThreefold", "true"), ("CuckooRep", "true")],
        parts=["IT", "CR"], expect="tree")
    add("NS99_V2R1", "NetScale=99 + v2 r1 replica", "extra", opts=[("NetScale", "99")] + v2("r1.fnn2",
        ("NNUEKingBuckets", "1")), parts=["NS99", "V2R1"], expect="tree")
    # NNUE group (O2 with a v2 option = the v2 path: O2 only changes the compiled-in net's code)
    add("O2_THR", "O2 + NNUEThreats", "nnue", exe="o2", opts=v2("r1_t.fnn2", ("NNUEThreats", "1")), parts=["O2", "THR"])
    add("O2_PP", "O2 + NNUEPawnPairs", "nnue", exe="o2", opts=v2("r1_p.fnn2", ("NNUEPawnPairs", "1")), parts=["O2", "PP"])
    add("O2_OB8", "O2 + NNUEOutputBuckets=8", "nnue", exe="o2", opts=v2("r1_ob8.fnn2", ("NNUEOutputBuckets", "8")),
        parts=["O2", "OB8"])
    add("THR_PP", "NNUEThreats + NNUEPawnPairs", "nnue",
        opts=v2("r1_t_p.fnn2", ("NNUEThreats", "1"), ("NNUEPawnPairs", "1")), parts=["THR", "PP"])
    add("THR_OB8", "NNUEThreats + NNUEOutputBuckets=8", "nnue",
        opts=v2("r1_t_ob8.fnn2", ("NNUEThreats", "1"), ("NNUEOutputBuckets", "8")), parts=["THR", "OB8"])
    add("PP_OB8", "NNUEPawnPairs + NNUEOutputBuckets=8", "nnue",
        opts=v2("r1_p_ob8.fnn2", ("NNUEPawnPairs", "1"), ("NNUEOutputBuckets", "8")), parts=["PP", "OB8"])
    add("THR_PP_OB8", "NNUEThreats + NNUEPawnPairs + NNUEOutputBuckets=8", "nnue",
        opts=v2("r1_t_p_ob8.fnn2", ("NNUEThreats", "1"), ("NNUEPawnPairs", "1"), ("NNUEOutputBuckets", "8")),
        parts=["THR", "PP", "OB8"])
    add("O2_THR_PP_OB8", "O2 + NNUEThreats + NNUEPawnPairs + NNUEOutputBuckets=8", "nnue", exe="o2",
        opts=v2("r1_t_p_ob8.fnn2", ("NNUEThreats", "1"), ("NNUEPawnPairs", "1"), ("NNUEOutputBuckets", "8")),
        parts=["O2", "THR", "PP", "OB8"])
    # final stack head 330237f3 (coordinator, R3-1): S12 null-edge accumulator alias (NnueLazyAcc), S08fix profile
    # counters (FORGE_PROF), S-A2 NnueInt16; every one timed against base_h3 (the OFF exe of the same head)
    add("H3DRIFT", "final-head OFF exe (330237f3) vs first-pass OFF exe (467a59b3)", "head3", exe="base_h3",
        a_exe="base", note="A = first-pass base.exe, B = base_h3.exe: does the first-pass matrix still describe "
                           "the final head?")
    add("O2H3", "FORGE_NNUE_O2 at the final head", "head3", exe="o2_h3")
    add("LAZYSW", "FORGE_NNUE_LAZY_ACC, option off", "head3", exe="lazy")
    add("LAZY", "FORGE_NNUE_LAZY_ACC + NnueLazyAcc=true", "head3", exe="lazy", opts=[("NnueLazyAcc", "true")])
    add("O2_LAZY", "O2 + NnueLazyAcc (both change the compiled-in accumulator path)", "head3", exe="o2_lazy",
        opts=[("NnueLazyAcc", "true")], parts=["O2H3", "LAZY"])
    add("LAZY_THR", "NnueLazyAcc + NNUEThreats (alias is compiled-in-net code; v2 path runs)", "head3", exe="lazy",
        opts=[("NnueLazyAcc", "true")] + v2("r1_t.fnn2", ("NNUEThreats", "1")), parts=["LAZY", "THR"])
    add("PROFSW", "FORGE_PROF build, bench (counting off)", "head3", exe="prof",
        note="diagnostic build; the UCI Profile option never reaches bench (bench_searcher.set_profiling(bench_prof))")
    add("PROF", "FORGE_PROF build, bench_prof (counting on)", "head3", exe="prof", cmd="bench_prof")
    add("PROF_CM_CE", "FORGE_PROF bench_prof + CorrMargins + CorrExt (counters inside the combined instance)",
        "head3", exe="prof", cmd="bench_prof", opts=[("CorrMargins", "1"), ("CorrExt", "1")], parts=["PROF", "CM_CE"])
    add("INT16SW", "FORGE_NNUE_INT16, option off", "head3", exe="int16")
    add("INT16", "FORGE_NNUE_INT16 + NnueInt16=true", "head3", exe="int16", opts=[("NnueInt16", "true")],
        expect="tree", ref=(330610, 858175, 2760596))
    add("O2_INT16", "O2 + NnueInt16 (the int16 hooks run before O2's float kernels)", "head3", exe="o2_int16",
        opts=[("NnueInt16", "true")], parts=["O2H3", "INT16"])
    add("INT16_LAZY", "NnueInt16 + NnueLazyAcc (the alias drives the int16 accumulators)", "head3",
        exe="int16_lazy", opts=[("NnueInt16", "true"), ("NnueLazyAcc", "true")], parts=["INT16", "LAZY"])
    add("INT16_THR", "NnueInt16 + NNUEThreats (int16 applies to the compiled-in net only)", "head3", exe="int16",
        opts=[("NnueInt16", "true")] + v2("r1_t.fnn2", ("NNUEThreats", "1")), parts=["INT16", "THR"])
    return C


# ----------------------------------------------------------------------------------------------- engine driver
if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    class FILETIME(ctypes.Structure):
        _fields_ = [("lo", wintypes.DWORD), ("hi", wintypes.DWORD)]

    _k32 = ctypes.windll.kernel32

    def proc_cpu(p):
        """(user + kernel seconds of every thread, cycle count) of a live or exited child process."""
        t = [FILETIME() for _ in range(4)]
        if not _k32.GetProcessTimes(wintypes.HANDLE(int(p._handle)), *[ctypes.byref(x) for x in t]):
            raise RuntimeError("GetProcessTimes failed")
        sec = lambda f: ((f.hi << 32) | f.lo) / 1e7
        cycles = ctypes.c_ulonglong(0)
        if not _k32.QueryProcessCycleTime(wintypes.HANDLE(int(p._handle)), ctypes.byref(cycles)):
            cycles.value = 0
        return sec(t[2]) + sec(t[3]), int(cycles.value)

    CREATE_FLAGS = subprocess.IDLE_PRIORITY_CLASS
else:
    def proc_cpu(p):
        with open(f"/proc/{p.pid}/stat") as f:
            fields = f.read().rsplit(")", 1)[1].split()
        tick = os.sysconf("SC_CLK_TCK")
        return (int(fields[11]) + int(fields[12])) / tick, 0
    CREATE_FLAGS = 0


class EngineDied(Exception):
    pass


class Engine:
    """One fresh engine process: uci, Threads/Hash/OwnBook, the configuration's options, isready."""

    def __init__(self, exe, threads, opts, timeout=900):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, bufsize=1, creationflags=CREATE_FLAGS)
        self.lines = []
        self.timer = threading.Timer(timeout, self._timeout)
        self.timer.daemon = True
        self.timer.start()
        self.timed_out = False
        self.setup_errors = []     # ERROR lines before readyok (half-set v2 requests are expected here)
        self.late_errors = []      # ERROR lines after readyok: a real failure
        self.info_strings = []     # info string lines before readyok (v2 active line, TtChildPrefetch, Syzygy)
        self.ready = False
        self.send("uci")
        self.wait(r"^uciok")
        for o in (f"Threads value {threads}", "Hash value 16", "OwnBook value false"):
            self.send("setoption name " + o)
        for name, value in opts:
            self.send(f"setoption name {name} value {value}")
        self.send("isready")
        self.wait(r"^readyok")
        self.ready = True

    def _timeout(self):
        self.timed_out = True
        self.p.kill()   # our own child process only

    def send(self, s):
        try:
            self.p.stdin.write(s + "\n")
            self.p.stdin.flush()
        except OSError as e:
            raise EngineDied(f"write failed ({e}); last lines {self.lines[-4:]}")

    def wait(self, pat):
        rx = re.compile(pat)
        for line in self.p.stdout:
            line = line.rstrip("\n")
            self.lines.append(line)
            if "ERROR" in line:
                (self.late_errors if self.ready else self.setup_errors).append(line)
            elif line.startswith("info string") and not self.ready:
                self.info_strings.append(line)
            m = rx.search(line)
            if m:
                return m
        self.p.wait(timeout=30)
        raise EngineDied(f"exit status {self.p.returncode} before {pat!r}{' (timeout)' if self.timed_out else ''}; "
                         f"last lines {self.lines[-4:]}")

    def bench(self, depth, cmd="bench"):
        c0, y0 = proc_cpu(self.p)
        w0 = time.perf_counter()
        self.send(f"{cmd} {depth}")
        m = self.wait(rf"bench depth {depth} nodes (\d+) time (\d+) nps (\d+)")
        w1 = time.perf_counter()
        c1, y1 = proc_cpu(self.p)
        return dict(nodes=int(m.group(1)), engine_ms=int(m.group(2)), engine_nps=int(m.group(3)),
                    cpu_s=c1 - c0, cycles=y1 - y0, wall_s=w1 - w0)

    def go_positions(self, depth):
        """T2 workload: the bench positions, each from a cleared searcher (ucinewgame), go depth <depth>."""
        nodes = 0
        c0, y0 = proc_cpu(self.p)
        w0 = time.perf_counter()
        per = []
        for fen in BENCH_FENS:
            self.send("ucinewgame")
            self.send("position fen " + fen)
            self.send(f"go depth {depth}")
            last = None
            while True:
                m = self.wait(r"^(bestmove|info depth \d+ .* nodes (\d+))")
                if m.group(1).startswith("bestmove"):
                    break
                last = int(m.group(2))
            if last is None:
                raise EngineDied("no info depth line before bestmove")
            per.append(last)
            nodes += last
        w1 = time.perf_counter()
        c1, y1 = proc_cpu(self.p)
        return dict(nodes=nodes, per_position=per, cpu_s=c1 - c0, cycles=y1 - y0, wall_s=w1 - w0,
                    engine_ms=round((w1 - w0) * 1000))

    def close(self):
        try:
            self.send("quit")
        except EngineDied:
            pass
        try:
            self.p.wait(timeout=60)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.wait(timeout=30)
        self.timer.cancel()
        proc_s, proc_cycles = proc_cpu(self.p)
        return dict(rc=self.p.returncode, proc_cpu_s=proc_s, proc_cycles=proc_cycles)


def run_once(exe, threads, opts, depths, workload, cmd="bench"):
    """Fresh process; returns a record (also for a failed run: died / status / errors)."""
    rec = dict(ok=False, died=None, setup_errors=[], late_errors=[], info=[], results={})
    eng = None
    try:
        eng = Engine(exe, threads, opts)
        for d in depths:
            rec["results"][str(d)] = eng.bench(d, cmd) if workload == "bench" else eng.go_positions(d)
        rec.update(eng.close())
        rec["ok"] = rec["rc"] == 0 and not eng.late_errors
    except EngineDied as e:
        rec["died"] = str(e)
        if eng is not None:
            try:
                rec.update(eng.close())
            except Exception as e2:   # noqa: BLE001
                rec["close_error"] = str(e2)
    if eng is not None:
        rec["setup_errors"], rec["late_errors"] = eng.setup_errors, eng.late_errors
        rec["info"] = [s for s in eng.info_strings if "ERROR" not in s][-4:]
    return rec


# ----------------------------------------------------------------------------------------------- statistics
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
        22: 2.074, 24: 2.064, 26: 2.056, 28: 2.048, 30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980, 10 ** 9: 1.960}


def t975(df):
    """two-sided 95% Student t quantile; linear interpolation in 1/df between table entries."""
    if df <= 1:
        return T975[1]
    keys = sorted(T975)
    for lo, hi in zip(keys, keys[1:]):
        if lo <= df <= hi:
            if df == lo:
                return T975[lo]
            w = (1 / df - 1 / hi) / (1 / lo - 1 / hi)
            return T975[hi] + w * (T975[lo] - T975[hi])
    return 1.96


def paired(a, b):
    """ABBA pairs (a[i], b[i]) -> mean log ratio, its standard error, df."""
    d = [math.log(y / x) for x, y in zip(a, b)]
    n = len(d)
    m = statistics.mean(d)
    se = statistics.stdev(d) / math.sqrt(n) if n > 1 else float("inf")
    return m, se, n - 1


def welch(a, b):
    """Welch difference of means relative to mean(a) (as nps_ab.py), with a Satterthwaite t interval."""
    ma, mb = statistics.mean(a), statistics.mean(b)
    va, vb = statistics.variance(a) / len(a), statistics.variance(b) / len(b)
    se = math.sqrt(va + vb)
    df = (va + vb) ** 2 / ((va ** 2) / (len(a) - 1) + (vb ** 2) / (len(b) - 1)) if va + vb > 0 else 10 ** 9
    t = t975(df)
    return (mb / ma - 1), (mb - ma - t * se) / ma, (mb - ma + t * se) / ma


def pct(x):
    return (math.exp(x) - 1) * 100


def combine(terms):
    """sum of (coef, (mean, se, df)) log-ratio estimates -> (mean, se, Satterthwaite df)."""
    m = sum(c * e[0] for c, e in terms)
    v = sum((c * e[1]) ** 2 for c, e in terms)
    den = sum(((c * e[1]) ** 2) ** 2 / max(e[2], 1) for c, e in terms)
    df = v ** 2 / den if den > 0 else 10 ** 9
    return m, math.sqrt(v), df


def ci(est):
    m, se, df = est
    t = t975(df)
    return m - t * se, m + t * se


# ----------------------------------------------------------------------------------------------- commands
def paths(a):
    exes = {k: str(Path(a.build_dir) / f"{k}.exe") for k in EXES}
    return exes, configs(a.net_dir, a.syzygy)


def select(C, only):
    if not only:
        return C
    keys = set(only.split(","))
    unknown = keys - {c["key"] for c in C}
    if unknown:
        raise SystemExit(f"unknown configuration(s): {sorted(unknown)}")
    return [c for c in C if c["key"] in keys]


def cmd_list(a):
    exes, C = paths(a)
    for c in C:
        print(f"{c['key']:15s} T{c['threads']} {c['exe']:10s} {c['expect']:5s} parts={','.join(c['parts']) or '-':22s} "
              f"{c['label']}  opts={c['opts']}")
    print(f"{len(C)} configurations; exes: " + ", ".join(f"{k}={exes[k]}" for k in EXES))


def cmd_nets(a):
    py = sys.executable
    tool = Path(a.worktree) / "tools" / "nnue" / "forge_nnue_v2.py"
    inc = Path(a.worktree) / "src" / "nnue_weights.inc"
    out = Path(a.net_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, args in NETS.items():
        if args is None:
            continue
        r = subprocess.run([py, "-I", "-B", str(tool), "from-inc", str(inc), str(out / name)] + args,
                           capture_output=True, text=True, creationflags=CREATE_FLAGS)
        print(r.stdout.strip() or r.stderr.strip())
        if r.returncode:
            raise SystemExit(f"net {name} failed")
    copy = Path(a.worktree) / "opus_round1" / "O4" / "standalone_copy.py"
    r = subprocess.run([py, "-I", "-B", str(copy), str(out / "r1.fnn2"), str(out / "r1_pure.fnn2")],
                       capture_output=True, text=True, creationflags=CREATE_FLAGS)
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode:
        raise SystemExit("r1_pure failed")


def cmd_nodes(a):
    exes, C = paths(a)
    out = Path(a.out) / "nodes"
    out.mkdir(parents=True, exist_ok=True)
    for c in select(C, a.only):
        if not c["nodes"]:
            continue
        if not Path(exes[c["exe"]]).exists():
            print(f"{c['key']}: {exes[c['exe']]} missing, skipped", flush=True)
            continue
        reps = []
        for r in range(a.reps):
            rec = run_once(exes[c["exe"]], c["threads"], c["opts"], DEPTHS, "bench", c.get("cmd", "bench"))
            reps.append(rec)
            got = {d: rec["results"].get(str(d), {}).get("nodes") for d in DEPTHS}
            print(f"{c['key']:15s} rep {r} ok={rec['ok']} rc={rec.get('rc')} nodes " +
                  " ".join(f"d{d}={got[d]}" for d in DEPTHS) +
                  f" setup_errors={len(rec['setup_errors'])} late_errors={len(rec['late_errors'])}"
                  + (f" DIED {rec['died']}" if rec["died"] else ""), flush=True)
        with open(out / f"{c['key']}.json", "w", newline="\n") as f:
            json.dump(dict(config=c, exe=exes[c["exe"]], reps=reps), f, indent=1)


def cmd_nps(a):
    exes, C = paths(a)
    out = Path(a.out) / "nps"
    out.mkdir(parents=True, exist_ok=True)
    for c in select(C, a.only):
        if not c["nps"]:
            continue
        dest = out / f"{c['key']}.json"
        if a.skip_done and dest.exists():
            print(f"{c['key']}: done already, skipped", flush=True)
            continue
        if not Path(exes[c["exe"]]).exists():
            print(f"{c['key']}: {exes[c['exe']]} missing, skipped", flush=True)
            continue
        workload = "bench" if c["threads"] == 1 else "go"
        depth = a.depth if workload == "bench" else a.depth_t2
        a_key = c.get("a_exe", "base")
        if not Path(exes[a_key]).exists():
            print(f"{c['key']}: A side {exes[a_key]} missing, skipped", flush=True)
            continue
        side = {"A": (exes[a_key], c["threads"], [], "bench"),
                "B": (exes[c["exe"]], c["threads"], c["opts"], c.get("cmd", "bench"))}
        runs, first = [], 0
        if a.append and dest.exists():   # more ABBA pairs for a configuration measured before
            with open(dest) as fh:
                runs = json.load(fh)["runs"]
            first = max(r["pair"] for r in runs) + 1
            print(f"{c['key']}: appending pairs {first}..{first + a.runs - 1} to {len(runs)} runs", flush=True)
        order = []
        for i in range(first, first + a.runs):
            order += [("A", i), ("B", i)] if i % 2 == 0 else [("B", i), ("A", i)]
        t_start = time.time()
        for tag, i in order:
            exe, th, opts, bcmd = side[tag]
            rec = run_once(exe, th, opts, [depth], workload, bcmd)
            res = rec["results"].get(str(depth), {})
            runs.append(dict(side=tag, pair=i, ok=rec["ok"], died=rec["died"], rc=rec.get("rc"),
                             setup_errors=len(rec["setup_errors"]), late_errors=rec["late_errors"],
                             info=rec["info"], proc_cpu_s=rec.get("proc_cpu_s"), **res))
            if res:
                print(f"{c['key']:15s} {tag}{i} nodes {res['nodes']} cpu_nps {res['nodes'] / res['cpu_s']:.0f} "
                      f"wall_nps {res['nodes'] / res['wall_s']:.0f} ok={rec['ok']}", flush=True)
            else:
                print(f"{c['key']:15s} {tag}{i} FAILED {rec['died']}", flush=True)
        summary = summarize(runs)
        summary["elapsed_s"] = round(time.time() - t_start, 1)
        with open(dest, "w", newline="\n") as f:
            json.dump(dict(config=c, workload=workload, depth=depth, exe_a=exes[a_key], exe_b=exes[c["exe"]],
                           runs=runs, summary=summary), f, indent=1)
        s = summary
        if s.get("cpu"):
            lo, hi = s["cpu"]["ci_pct"]
            print(f"== {c['key']}: cpu NPS {s['cpu']['pct']:+.2f}% [{lo:+.2f}, {hi:+.2f}] "
                  f"cycles {s['cycles']['pct']:+.2f}% wall {s['wall']['pct']:+.2f}% nodes_equal={s['nodes_equal']} "
                  f"({s['elapsed_s']} s)", flush=True)
        else:
            print(f"== {c['key']}: no complete A/B pairs ({s})", flush=True)


def summarize(runs):
    A = {r["pair"]: r for r in runs if r["side"] == "A" and r.get("nodes")}
    B = {r["pair"]: r for r in runs if r["side"] == "B" and r.get("nodes")}
    pairs = sorted(set(A) & set(B))
    s = dict(pairs=len(pairs), failed=sum(1 for r in runs if not r["ok"]),
             nodes_a=sorted({A[i]["nodes"] for i in pairs}), nodes_b=sorted({B[i]["nodes"] for i in pairs}))
    s["nodes_equal"] = len(s["nodes_a"]) == 1 and s["nodes_a"] == s["nodes_b"]
    if len(pairs) < 2:
        return s
    for metric, fn in (("cpu", lambda r: r["nodes"] / r["cpu_s"]), ("wall", lambda r: r["nodes"] / r["wall_s"]),
                       ("cycles", lambda r: r["nodes"] / r["cycles"] if r["cycles"] else float("nan"))):
        a = [fn(A[i]) for i in pairs]
        b = [fn(B[i]) for i in pairs]
        if any(math.isnan(x) for x in a + b):
            continue
        m, se, df = paired(a, b)
        lo, hi = ci((m, se, df))
        wr, wlo, whi = welch(a, b)
        s[metric] = dict(mean_a=statistics.mean(a), mean_b=statistics.mean(b), log=m, se=se, df=df, pct=pct(m),
                         ci_pct=[pct(lo), pct(hi)], welch_pct=wr * 100, welch_ci_pct=[wlo * 100, whi * 100],
                         sd_a_pct=statistics.stdev(a) / statistics.mean(a) * 100,
                         sd_b_pct=statistics.stdev(b) / statistics.mean(b) * 100)
    s["mean_nodes_b"] = statistics.mean(B[i]["nodes"] for i in pairs)
    s["mean_nodes_a"] = statistics.mean(A[i]["nodes"] for i in pairs)
    return s


# ----------------------------------------------------------------------------------------------- report
def load(out, kind):
    d = {}
    for f in sorted((Path(out) / kind).glob("*.json")):
        with open(f) as fh:
            j = json.load(fh)
        d[j["config"]["key"]] = j
    return d


def node_triple(nodes_rec):
    """nodes at d11/13/16 if every rep agrees, plus status."""
    reps = nodes_rec["reps"]
    vals = []
    for r in reps:
        vals.append(tuple(r["results"].get(str(d), {}).get("nodes") for d in DEPTHS))
    ok = all(r["ok"] for r in reps)
    same = len(set(vals)) == 1
    return vals[0] if vals else None, ok, same, reps


def cmd_report(a):
    exes, C = paths(a)
    byk = {c["key"]: c for c in C}
    N, P = load(a.out, "nodes"), load(a.out, "nps")
    lines = []
    w = lines.append
    M = a.metric
    est = {k: (v["summary"][M]["log"], v["summary"][M]["se"], v["summary"][M]["df"])
           for k, v in P.items() if v["summary"].get(M)}
    drift = est.get("H3DRIFT")   # log(base_h3 / base): the final head's OFF exe against the first-pass OFF exe

    def rel(key, ref):
        """estimate of configuration `key` relative to the OFF exe `ref` (its own A side, or converted with the
        measured H3DRIFT; the drift enters once per converted term)."""
        if key not in est:
            return None
        a_key = byk[key].get("a_exe", "base")
        if a_key == ref:
            return est[key]
        if drift is None:
            return None
        if a_key == "base" and ref == "base_h3":
            return combine([(1.0, est[key]), (-1.0, drift)])
        if a_key == "base_h3" and ref == "base":
            return combine([(1.0, est[key]), (1.0, drift)])
        return None
    nodes = {}
    for k, rec in N.items():
        tri, ok, same, reps = node_triple(rec)
        nodes[k] = dict(tri=tri, ok=ok, same=same, reps=reps)

    def tree_of(key):
        return nodes.get(key, {}).get("tri")

    def is_sig(e):
        lo, hi = ci(e)
        return lo > 0 or hi < 0

    flags = {}

    def flag(key, text):
        flags.setdefault(key, []).append(text)

    # ---- node checks
    node_note = {}
    for c in C:
        k = c["key"]
        if c["threads"] != 1:
            continue
        nd = nodes.get(k)
        if nd is None:
            continue
        if not nd["ok"]:
            bad = [r for r in nd["reps"] if not r["ok"]]
            flag(k, "CONFLICT: run failed (" + "; ".join((r["died"] or f"rc={r.get('rc')} late ERROR {r['late_errors'][:1]}")
                                                for r in bad)[:200] + ")")
            continue
        if not nd["same"]:
            flag(k, "CONFLICT: T1 nodes differ between fresh processes")
        tri = nd["tri"]
        pins = tuple(PINS[d] for d in DEPTHS)
        if not c["parts"]:
            if c["expect"] == "exact" and tri != pins:
                flag(k, "CONFLICT: node-exact option changed nodes")
            if c["expect"] == "tree" and tri == pins:
                flag(k, "no effect: tree option left nodes = OFF")
            if c["ref"] and tri != tuple(c["ref"]):
                flag(k, f"NOTE: nodes differ from the branch pins {c['ref']}")
            node_note[k] = "= lock pins" if tri == pins else ("new tree" + (" (= branch pins)" if c["ref"] and tri ==
                                                                              tuple(c["ref"]) else ""))
            continue
        parts = [byk[p] for p in c["parts"]]
        trees = [p for p in parts if p["expect"] == "tree"]
        if not trees:
            node_note[k] = "node-exact parts: = lock pins" if tri == pins else "node-exact parts but nodes differ"
            if tri != pins:
                flag(k, "CONFLICT: node-exact parts, nodes differ from the pins")
        elif len(trees) == 1:
            want = tree_of(trees[0]["key"])
            if tri == want:
                node_note[k] = f"= {trees[0]['key']} (the one tree-changing part), as expected"
            elif tri == pins:
                node_note[k] = f"= OFF, but {trees[0]['key']} alone changes the tree"
                flag(k, f"CANCELS OUT: nodes = OFF although {trees[0]['key']} alone changes them")
            else:
                node_note[k] = f"differs from {trees[0]['key']} although the other parts are node-exact"
                flag(k, f"CONFLICT: nodes differ from {trees[0]['key']} (other parts are node-exact)")
        else:
            same_as = [p["key"] for p in trees if tree_of(p["key"]) == tri]
            if tri == pins:
                node_note[k] = "= OFF"
                flag(k, "CANCELS OUT: tree-changing parts together give the OFF nodes")
            elif same_as:
                node_note[k] = f"= {same_as[0]} alone"
                flag(k, f"CANCELS OUT: nodes = {same_as[0]} alone (the other part is inert in the combination)")
            else:
                node_note[k] = "new tree (differs from OFF and from every part)"

    # ---- NPS checks: A/A, leave-one-out contributions, additivity
    shared_v2 = "V2R1"

    def predicted(c):
        ref = c.get("a_exe", "base")
        terms = [(1.0, rel(p, ref)) for p in c["parts"]]
        if any(t[1] is None for t in terms):
            return None
        nv2 = sum(1 for p in c["parts"] if byk[p]["v2"])
        if nv2 > 1 and rel(shared_v2, ref) is not None:
            terms.append((-(nv2 - 1), rel(shared_v2, ref)))
        return combine(terms)

    def rest_key(c, drop):
        want = sorted(p for p in c["parts"] if p != drop)
        if len(want) == 1:
            return want[0]
        for o in C:
            if sorted(o["parts"]) == want and o["threads"] == c["threads"]:
                return o["key"]
        return None

    pair_rows = []
    for c in C:
        k = c["key"]
        if not c["parts"] or k not in est:
            continue
        pred = predicted(c)
        inter = combine([(1.0, est[k]), (-1.0, pred)]) if pred else None
        contrib = []
        ref = c.get("a_exe", "base")
        for p in c["parts"]:
            r = rest_key(c, p)
            if r is None or rel(r, ref) is None or rel(p, ref) is None:
                continue
            solo_terms = [(1.0, rel(p, ref))]
            if byk[p]["v2"] and any(byk[q]["v2"] for q in c["parts"] if q != p) and rel(shared_v2, ref) is not None:
                solo_terms.append((-1.0, rel(shared_v2, ref)))
            solo = combine(solo_terms)
            con = combine([(1.0, est[k]), (-1.0, rel(r, ref))])
            diff = combine([(1.0, con), (-1.0, solo)])
            contrib.append((p, r, solo, con, diff))
        # NPS "cancels out" in the job's wording: the combined effect is clearly below either part. Applied when
        # every part has a clear effect (95% interval excludes 0) of the same sign; flagged when the combination's
        # effect is clearly smaller in size than each part's (interval of the signed difference below 0 for every
        # part). Parts with opposite signs offset arithmetically: the interaction column covers them.
        parts_e = [(p, rel(p, ref)) for p in c["parts"]]
        if all(e is not None for _, e in parts_e) and all(is_sig(e) for _, e in parts_e):
            signs = {1.0 if e[0] > 0 else -1.0 for _, e in parts_e}
            if len(signs) == 1:
                s = signs.pop()
                gaps = [(p, combine([(s, est[k]), (-s, e)])) for p, e in parts_e]
                if all(ci(g)[1] < 0 for _, g in gaps):
                    text = (f"combined {pct(est[k][0]):+.2f}% is smaller than every part (" +
                            ", ".join(f"{p} {pct(rel(p, ref)[0]):+.2f}%" for p, _ in parts_e) + ")")
                    n_tree = sum(1 for q in c["parts"] if byk[q]["expect"] == "tree")
                    if n_tree >= 2:   # a new tree: NPS differences mix tree shape with code cost
                        flag(k, "NPS note (new tree, not a code conflict): " + text)
                    else:
                        flag(k, "CANCELS OUT (NPS): " + text)
        pair_rows.append((c, pred, inter, contrib))

    for c in C:
        k = c["key"]
        nd = P.get(k)
        if nd and (nd["summary"]["failed"] or any(r["late_errors"] for r in nd["runs"])):
            flag(k, f"CONFLICT: {nd['summary']['failed']} NPS run(s) failed")
        if nd and c["threads"] == 1 and not nd["summary"].get("nodes_equal") and c["expect"] == "exact" \
                and not c["parts"] and k not in ("OFF",):
            flag(k, "CONFLICT: NPS runs saw nodes != OFF")

    # ---- tables
    def nps_cell(k):
        s = P.get(k, {}).get("summary", {}).get(M)
        if not s:
            return "—"
        lo, hi = s["ci_pct"]
        return f"{s['pct']:+.2f} [{lo:+.2f}, {hi:+.2f}]"

    def dnodes(k):
        tri = tree_of(k)
        if tri is None or None in tri:
            return "—"
        return " / ".join(f"{(n / PINS[d] - 1) * 100:+.1f}%" if n != PINS[d] else "0" for n, d in zip(tri, DEPTHS))

    def nodes_cell(c):
        k = c["key"]
        if c["threads"] != 1:
            s = P.get(k, {}).get("summary", {})
            m = s.get("mean_nodes_b")
            return f"T2 go: mean {m:,.0f} (varies)" if m else "T2: varies"
        tri = tree_of(k)
        if tri is None:
            return "—"
        return " / ".join(str(x) for x in tri)

    mname = {"cycles": "CPU NPS Δ% [95% CI] (cycle-timed CPU)", "cpu": "CPU NPS Δ% [95% CI] (GetProcessTimes)",
             "wall": "wall NPS Δ% [95% CI]"}[M]
    w(f"| config | build / options | nodes d11 / d13 / d16 | Δnodes vs OFF | {mname} | flag |")
    w("|---|---|---|---|---|---|")
    for c in C:
        k = c["key"]
        opts = ", ".join(f"{n}={Path(v).name if n == 'NNUEFile' or n == 'SyzygyPath' else v}" for n, v in c["opts"])
        build = (EXE_FLAGS[c["exe"]] or ("base_h3" if c["exe"] == "base_h3" else "base")) + \
            ("" if c.get("head", "467a59b3") == "467a59b3" else f" [head {c['head']}]") + \
            (f" (`{c['cmd']}`)" if c.get("cmd", "bench") != "bench" else "") + \
            (f" (A side: {c['a_exe']}.exe)" if c.get("a_exe", "base") != "base" else "")
        fl = "; ".join(flags.get(k, [])) or ("ok" if (k in nodes or k in P) else "not run")
        w(f"| {k} ({c['label']}) | {build}{' + ' + opts if opts else ''}{' T2' if c['threads'] == 2 else ''} | "
          f"{nodes_cell(c)} | {dnodes(k) if c['threads'] == 1 else 'n/a'} | {nps_cell(k)} | {fl} |")
    w("")
    w("### Pair analysis (CPU NPS; log-additive prediction = sum of the parts' log ratios; for several v2 parts the "
      "v2-path cost (V2R1) is counted once)")
    w("")
    w("| combination | nodes | measured Δ% [CI] | additive prediction Δ% | interaction (measured − predicted) [CI] | "
      "leave-one-out: part → alone vs added on top of the rest |")
    w("|---|---|---|---|---|---|")
    for c, pred, inter, contrib in pair_rows:
        k = c["key"]
        it = f"{pct(inter[0]):+.2f} [{pct(ci(inter)[0]):+.2f}, {pct(ci(inter)[1]):+.2f}]" if inter else "—"
        pr = f"{pct(pred[0]):+.2f}" if pred else "—"
        loo = "; ".join(f"{p}: {pct(solo[0]):+.1f}% alone, {pct(con[0]):+.1f}% [{pct(ci(con)[0]):+.1f}, "
                        f"{pct(ci(con)[1]):+.1f}] on {r}" for p, r, solo, con, diff in contrib) or "—"
        w(f"| {k} | {node_note.get(k, 'T2: n/a') if c['threads'] == 1 else 'T2: n/a'} | {nps_cell(k)} | {pr} | {it} | {loo} |")
    w("")
    w("### Option effect inside its own switch build (same exe, option on vs off: free of build-to-build layout effects)")
    w("")
    w("| option | switch build, option off vs OFF exe | option on vs OFF exe | option on vs off (same exe) |")
    w("|---|---|---|---|")
    for on, sw in (("TCP", "S13SW"), ("LAZY", "LAZYSW"), ("PROF", "PROFSW"), ("INT16", "INT16SW")):
        if on in est and sw in est:
            d = combine([(1.0, est[on]), (-1.0, est[sw])])
            w(f"| {on} ({byk[on]['label']}) | {nps_cell(sw)} | {nps_cell(on)} | {pct(d[0]):+.2f} "
              f"[{pct(ci(d)[0]):+.2f}, {pct(ci(d)[1]):+.2f}] |")
    w("")
    w("### Flagged")
    any_flag = False
    for c in C:
        for t in flags.get(c["key"], []):
            if t.startswith(("CONFLICT", "CANCELS")):
                w(f"- {c['key']}: {t}")
                any_flag = True
    if not any_flag:
        w("- none")
    w("")
    w("### Notes per configuration (setup info lines, transient half-set ERROR lines, other notes)")
    for c in C:
        k = c["key"]
        bits = []
        nd = nodes.get(k)
        if nd:
            se = sum(len(r["setup_errors"]) for r in nd["reps"])
            if se:
                bits.append(f"{se} transient setup ERROR line(s) over {len(nd['reps'])} processes (half-set v2 "
                            f"request while the options arrive one by one; resolved before readyok)")
            info = nd["reps"][0]["info"] if nd["reps"] else []
            if info:
                bits.append("setup: " + " | ".join(info)[:300])
        for t in flags.get(k, []):
            if not t.startswith(("CONFLICT", "CANCELS")):
                bits.append(t)
        if c["note"]:
            bits.append(c["note"])
        s = P.get(k, {}).get("summary", {})
        if s.get("cpu"):
            bits.append(f"NPS: {s['pairs']} ABBA pairs, Welch {s['cpu']['welch_pct']:+.2f}% "
                        f"[{s['cpu']['welch_ci_pct'][0]:+.2f}, {s['cpu']['welch_ci_pct'][1]:+.2f}], cycles "
                        f"{s['cycles']['pct']:+.2f}% [{s['cycles']['ci_pct'][0]:+.2f}, {s['cycles']['ci_pct'][1]:+.2f}]"
                        if s.get("cycles") else "")
            if c["threads"] == 2 and s.get("wall"):
                bits.append(f"wall NPS {s['wall']['pct']:+.2f}% [{s['wall']['ci_pct'][0]:+.2f}, "
                            f"{s['wall']['ci_pct'][1]:+.2f}]")
        if bits:
            w(f"- {k}: " + "; ".join(b for b in bits if b))
    text = "\n".join(lines) + "\n"
    if a.md:
        with open(a.md, "w", newline="\n", encoding="utf-8") as f:
            f.write(text)
    print(text)
    with open(Path(a.out) / "analysis.json", "w", newline="\n") as f:
        json.dump(dict(flags=flags, node_note=node_note, nodes={k: v["tri"] for k, v in nodes.items()},
                       nps={k: P[k]["summary"] for k in P},
                       pairs=[dict(key=c["key"], pred=pred, inter=inter,
                                   contrib=[dict(part=p, rest=r, solo=s, added=con, diff=d) for p, r, s, con, d in cb])
                              for c, pred, inter, cb in pair_rows]), f, indent=1)


def main():
    sys.stdout.reconfigure(newline="\n", encoding="utf-8")   # LF, UTF-8 logs on Windows too
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["list", "nets", "nodes", "nps", "report"])
    ap.add_argument("--build-dir", default="F:/opus_scratch/build/r3_R3-2")
    ap.add_argument("--net-dir", default="F:/opus_scratch/r3/R3-2/nets")
    ap.add_argument("--syzygy", default="D:\\grok-pc-data\\dwqww\\.claude\\worktrees\\syzygy345")
    ap.add_argument("--out", default="F:/opus_scratch/r3/R3-2/results")
    ap.add_argument("--worktree", default="F:/opus_scratch/worktrees/opus_r3_matrix")
    ap.add_argument("--only", default="")
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--runs", type=int, default=8)
    ap.add_argument("--depth", type=int, default=16)
    ap.add_argument("--depth-t2", type=int, default=16)
    ap.add_argument("--skip-done", action="store_true")
    ap.add_argument("--append", action="store_true", help="nps: add --runs ABBA pairs to an existing result")
    ap.add_argument("--md", default="")
    ap.add_argument("--metric", default="cycles", choices=["cpu", "cycles", "wall"],
                    help="report: NPS metric of the tables (cycles = CPU time from QueryProcessCycleTime, TSC-exact; "
                         "cpu = CPU time from GetProcessTimes, tick-sampled: about 5x noisier on the loaded PC)")
    a = ap.parse_args()
    {"list": cmd_list, "nets": cmd_nets, "nodes": cmd_nodes, "nps": cmd_nps, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
