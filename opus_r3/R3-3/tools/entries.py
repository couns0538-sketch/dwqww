"""R3-3 gate entries: one dict per gate, in recommended run order (rank = position).

Expectation and risk texts are EXPECTATIONS, not measurements and not Elo claims. Facts quote the job REPORTs
(paths relative to the stack tree, opus_round1/<JOB>/REPORT.md unless noted).
"""

AL1 = [312866, 862329, 3024920, 12389307, 34048354]
SYZ = r'D:\grok-pc-data\dwqww\.claude\worktrees\syzygy345'

# exe key -> (file name, how it is built from the final opus-r3-stack head)
EXES = {
    'base': ('forge_r3_base.exe', 'default PC recipe build (build_pc.sh, no -D switch); used without options as the opponent of every gate'),
    'stack': ('forge_r3_stack.exe', 'the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates'),
    'nnueo2': ('forge_r3_nnueo2.exe', 'build_pc.sh ... -DFORGE_NNUE_O2=1'),
    'nozero': ('forge_r3_nozero.exe', 'build_pc.sh ... -DFORGE_NOZERO_MOVE_BUFFERS=1'),
    'speedstack': ('forge_r3_speedstack.exe', 'build_pc.sh ... -DFORGE_SPEEDSTACK=1'),
    'ttprefetch': ('forge_r3_ttprefetch.exe', 'build_pc.sh ... -DFORGE_S13_TT_CHILD_PREFETCH=1 (adds UCI TtChildPrefetch, default false)'),
    'lazyacc': ('forge_r3_lazyacc.exe', 'build_pc.sh ... -DFORGE_NNUE_LAZY_ACC=1 (adds UCI NnueLazyAcc, default false); name given by the main session'),
    'int16': ('forge_r3_int16.exe', 'build_pc.sh ... -DFORGE_NNUE_INT16=1 (adds UCI NnueInt16, default false; S-A2 merged as 97b01454); name given by the main session'),
    'h512': ('forge_r3_h512.exe', 'build_pc.sh ... -DFORGE_NNUE_HIDDEN=512 -DFORGE_NNUE_WEIGHTS="<trained H512 .inc>" (S-A4 flags merged as a4fa82bb); no H512 net exists'),
}

E = []


def add(**kw):
    kw.setdefault('options', [])
    kw.setdefault('smp', False)
    kw.setdefault('longer_tc', False)
    kw.setdefault('early_stop', False)
    kw.setdefault('pins_label', None)
    kw.setdefault('pins_on_report', None)
    kw.setdefault('test_plan', None)
    kw.setdefault('notes', [])
    E.append(kw)


# ---------------- Tier A: node-exact speed (same tree as the opponent) ----------------
add(slug='nnueo2', feature='FORGE_NNUE_O2 (O2 NNUE accumulator kernels)', job='opus_round1/O2/REPORT.md',
    tier='A', status='runnable', exe='nnueo2', pins_on_report=None, test_plan='G-B4 (srand 1894620847, not reused)',
    gain='small positive (largest measured node-exact speed-up of the set)', risk='low',
    reason='bit-identical NNUE output (1.3M-position parity, 0 differences), about +3.3% to +3.6% bench NPS on idle CI runners',
    facts=['bit-identical output: parity 1,303,743 positions (CTest) and 1,578,127 with the 5_nnue sample, 0 differences; bench identical at all 5 depths; FMA 0',
           'quiet runner (CI run 40462176391): AL1 -> O2 +3.57% CPU NPS d16 [+3.28, +3.86], +3.66% d20 [+3.10, +4.22]; O2\'s own share (O3 -> O2) +3.26% / +3.25%; loaded PC d20 +3.01% [+1.43, +4.59] (advisory)',
           'the O2 report proposed no gate (speed-only); the stack turned it into a build switch, so it is gated here as the user asked'])
add(slug='nozero', feature='FORGE_NOZERO_MOVE_BUFFERS (S14 follow-up: no zero-fill of the move buffers)', job='opus_round1/sol_S14/REPORT.md',
    tier='A', status='runnable', exe='nozero',
    gain='small positive', risk='low (node-exact; relies on never reading an unwritten buffer slot, which was audited and tested)',
    reason='node-exact; +1.25% to +2.70% CPU NPS on four quiet-runner samples (5 of 8 CIs exclude 0)',
    facts=['switch on: bench d11-d22, perft5 and kiwipete ALL OK on the PC box recipe and on CI; pick order identical over 6 storage patterns',
           'quiet runners: +1.25% to +2.70% CPU NPS, 5 of 8 CIs exclude 0, every A/A control includes 0; loaded PC advisory +5.64% d16 / +4.62% d20',
           'uninitialised MoveList/MovePicker storage (UninitArray, C++20 implicit object creation): ASan+UBSan and TSan clean, valgrind memcheck 0 errors, clang MSan clean where it applies'])

# ---------------- Tier B: tree-changing search / eval, Threads 1 ----------------
add(slug='corrhistplus4', feature='CorrHistPlus=4 (non-pawn correction history, C2 bit 4)', job='opus_round1/C2/REPORT.md',
    tier='B', status='runnable', exe='stack', options=['option.CorrHistPlus=4'], pins_label='CHP4',
    pins_on_report=[340927, 734347, 2794671, 12132495, 37005405], longer_tc=True,
    gain='uncertain, plausibly small positive', risk='medium (ON cost about 1-3% NPS per bit; tree change)',
    reason='the related NonPawnCorr+PawnHist pack ended with a positive LLR in all 4 of its PC gates (0.63-2.48 at [0,10], all capped); no test-plan row',
    facts=['bench ON vs OFF: d11 +9.0%, d13 -14.8%, d16 -7.6%, d20 -2.1%, d22 +8.7%',
           'ON-path cost about 1-3% per bit (same-tree weight-0 A/B, wide CIs)',
           'related ledger rows (different implementation, NonPawnCorr+PawnHist vs h256_e12): G34 LLR 2.48, G38 1.11, G39 0.63, G43 2.32, all "cap with no decision"'])
add(slug='corrhistplus1', feature='CorrHistPlus=1 (continuation correction history, C2 bit 1)', job='opus_round1/C2/REPORT.md',
    tier='B', status='runnable', exe='stack', options=['option.CorrHistPlus=1'], pins_label='CHP1',
    pins_on_report=[318363, 915778, 2347193, 9687762, 19269711], longer_tc=True, test_plan='G-B1 (srand 885637590, not reused)',
    gain='uncertain, plausibly small positive', risk='medium (large deep-tree change: d22 -43%; ON cost about 1-3%)',
    reason='test-plan idea G-B1; related ContCorrectionWeight=60 gate (G87) capped at LLR 0.68',
    facts=['bench ON vs OFF: d11 +1.8%, d13 +6.2%, d16 -22.4%, d20 -21.8%, d22 -43.4%',
           'EVAL change: the test plan asks for a 40+0.4 confirm after an H1'])
add(slug='corrhistplus2', feature='CorrHistPlus=2 (minor-piece correction history, C2 bit 2)', job='opus_round1/C2/REPORT.md',
    tier='B', status='runnable', exe='stack', options=['option.CorrHistPlus=2'], pins_label='CHP2',
    pins_on_report=[296553, 824640, 2914749, 13945117, 40489211], longer_tc=True, test_plan='G-B2 (srand 2115600525, not reused)',
    gain='uncertain', risk='medium (d20/d22 trees grow +12.6% / +18.9%)',
    reason='test-plan idea G-B2; deep-tree growth is the crew flag for a longer-TC confirm',
    facts=['bench ON vs OFF: d11 -5.2%, d13 -4.4%, d16 -3.6%, d20 +12.6%, d22 +18.9%'])
add(slug='cuckoorep', feature='CuckooRep (upcoming-repetition detection, C6)', job='opus_round1/C6/REPORT.md',
    tier='B', status='runnable', exe='stack', options=['option.CuckooRep=true'], pins_label='CUCKOO',
    pins_on_report=[324211, 790682, 3148570, 10326301, 31204053], longer_tc=True,
    gain='uncertain, plausibly small positive', risk='low-medium (about 1% per-node cost; history-dependent draw bound)',
    reason='standard technique, contained effect (draw bound only); OFF path instruction-identical to the lock',
    facts=['ON bench d11-d22 324211/790682/3148570/10326301/31204053 (d20 -16.7%)', 'per-node cost about 1% on the same tree'])
add(slug='syzygy345', feature='SyzygyPath (own Syzygy WDL/DTZ probing, 3-4-5-man tables; SyzygyProbeDepth=1 and Syzygy50MoveRule=true stay at their defaults)', job='opus_round1/C1/REPORT.md',
    tier='B', status='runnable', exe='stack', options=['option.SyzygyPath=' + SYZ], pins_label='SYZ', longer_tc=False,
    test_plan='G-B6 (srand 739447198, not reused)',
    gain='uncertain, plausibly small positive (acts only in positions with at most 5 pieces)', risk='low-medium (probe cost in small endgames; table folder must stay readable)',
    reason='only the candidate probes (opponent has no tables), tablebase adjudication stays off as C1 asks',
    facts=['36,513 known-answer checks, 0 failures; 17/17 planted bugs caught; TB scores keep their TT distance (review fix)',
           'bench with the 3-4-5 set loaded: d11 313631, d13 866959, d16 2460490 (C1), d20/d22 measured here',
           'tables: 290 files, 939 MiB, read-only at ' + SYZ],
    notes=['the candidate processes need read access to the table folder; 8 concurrent candidate engines share the memory-mapped files',
           'tablebase adjudication stays off in fastchess (config tb_adjudication disabled), so endgames are played out'])
add(slug='histrework2', feature='HistRework=2 (correction/history rework, A1)', job='opus_round1/sol_A1/REPORT.md',
    tier='B', status='runnable', exe='stack', options=['option.HistRework=2'], pins_label='HR2',
    pins_on_report=[320427, 881902, 3041041, 12218938, 28571078], longer_tc=True,
    gain='uncertain', risk='medium (tree change; d22 -16.1%)',
    reason='A1 plan: first gate of the three levels (smallest node change, passes the crew +10% screen at d13/d16)',
    facts=['bench ON vs OFF: d11 +2.4%, d13 +2.3%, d16 +0.5%, d20 -1.4%, d22 -16.1%',
           'the A1 code costs about 1% NPS even OFF (quiet runner): it is in both the candidate and the opponent here, so this gate does not see it'])
add(slug='corrmargins', feature='CorrMargins=1 (correction-size pruning margins, O5)', job='opus_round1/O5/REPORT.md',
    tier='B', status='runnable', exe='stack', options=['option.CorrMargins=1'], pins_label='CM1',
    pins_on_report=[343365, 858019, 2522546, 12894582, 22287047], longer_tc=True, test_plan='G-B3 (srand 1162618901, not reused)',
    gain='uncertain', risk='medium (four pruning margins move at once; d22 -34.5%)',
    reason='test-plan idea G-B3; O5 notes correction terms tend to gain more at longer TC',
    facts=['bench ON vs OFF: d11 +9.75%, d13 -0.5%, d16 -16.6%, d20 +4.1%, d22 -34.5%',
           'sub-gates without a rebuild are possible later (one of CorrRfpPct/CorrFutilityPct/CorrNullMovePct/CorrLmrPct at a time)'])
add(slug='speedstack', feature='FORGE_SPEEDSTACK (S29: S11 material-key table + S13 child TT prefetch, compile time)', job='opus_round1/sol_S29/REPORT.md',
    tier='A', status='runnable', exe='speedstack',
    gain='about zero (speed-up under 1%)', risk='low',
    reason='node-exact; quiet runner +0.18% d16 / +0.50% d20; makes R3-16 and R3-17 redundant',
    facts=['switch ON: bench equals the AL1 pins at all 5 depths; UCI option list unchanged',
           'quiet runner ABBA: d16 +0.18% [-0.53, +0.89], d20 +0.50% [+0.04, +0.97]; loaded PC within noise',
           'Sol\'s design: one non-regression SPRT [-3,1] for the stack (gated here at [0,5] as the user asked)'])
add(slug='netscale99', feature='NetScale=99 (eval-scale mapping, S41)', job='opus_round1/sol_S41/REPORT.md',
    tier='B', status='runnable', exe='stack', options=['option.NetScale=99'], pins_label='NS99', longer_tc=False,
    gain='about zero', risk='low (1% eval rescale; single bench depths move up to 14.6%, total tree size unchanged)',
    reason='S41 found the AL1 net +1.2% above h256_e12 scale; 99 maps it back',
    facts=['S41: AL1 @99 every bench depth within +-14.6%; 100-position totals at depth 12 within 0.6%', 'OFF path costs nothing measurable (quiet runner)'])
add(slug='intendedthreefold', feature='IntendedThreefold (FIDE 9.2.1 claim in search, S-IT)', job='opus_round1/sol_SIT/REPORT.md',
    tier='B', status='runnable', exe='stack', options=['option.IntendedThreefold=true'], pins_label='IT', longer_tc=False,
    gain='about zero (fires only with repeated keys in the game history)', risk='low-medium (1.10-1.17x CPU per node inside shuffling subtrees)',
    reason='bench positions have no game history, so ON bench = OFF; effect only in games with repetitions',
    facts=['option off: trees identical everywhere; on: no cost measured on bench (quiet runner CIs include 0)',
           'in shuffling positions with duplicated keys the option costs 1.10-1.17x CPU per node'],
    notes=['ON bench equals the OFF pins; the runner accepts this (its "option did not apply" test compares with the old h256_e12 numbers, not AL1)'])
add(slug='harddeadline10', feature='HardDeadline=10 (watchdog bestmove deadline, C3)', job='opus_round1/C3/REPORT.md',
    tier='A', status='runnable', exe='stack', options=['option.HardDeadline=10'], pins_label='HD10', longer_tc=False,
    gain='about zero (no search decision changes while the engine answers on time)', risk='low',
    reason='C3 expects a gate to measure only noise; its value is time safety on a starved machine',
    facts=['0 forced answers in 3,600 normal-load searches with HardDeadline 10 (C3)',
           'Windows starvation demo: lateness 3,750-4,651 ms without, max +28.8 ms with the option',
           'R3-1 fix 5792074a: after a watchdog bestmove the stopped search could still print a late "info depth" line '
           '(33 such lines in about 140 all-ON self-play games); exactly one bestmove per go always held. The fix closes '
           'search output under uci_output_mutex once the watchdog answers; with HardDeadline 0 nothing changes (uci_check --full ALL OK)'],
    notes=['**the candidate exe must be built from a head that contains 5792074a** (check `git merge-base --is-ancestor 5792074a <final head>` before install); the 2047348a probe used for the pins predates the fix, which does not touch fixed-depth bench',
           'fixed-depth bench is unaffected, so cand_on = cand_off (accepted by the runner, see R3-12)',
           'watch_time stays on: a late move would pause this gate, which is exactly what the option should prevent'])
add(slug='corrext', feature='CorrExt=1 (correction-history extensions, O8)', job='opus_round1/O8/REPORT.md',
    tier='B', status='runnable', exe='stack', options=['option.CorrExt=1'], pins_label='CE1',
    pins_on_report=[312961, 838790, 2891507, 12313394, 33298237], longer_tc=True, test_plan='G-C5 (srand 113016036, not reused)',
    gain='uncertain, weak at 10+0.1', risk='medium (extensions compound with depth; the idea "lost at STC" in the source report)',
    reason='the test plan and O8 make 40+0.4 the primary gate; at the PC\'s usual 10+0.1 it is informational',
    facts=['bench ON vs OFF: d11 +0.03%, d13 -2.73%, d16 -4.41%, d20 -0.61%, d22 -2.20%'],
    notes=['owner choice: run this entry with "tc": "40+0.4" instead (the r7 runner supports a per-gate tc field) if the LTC-primary rule of the test plan should apply'])
add(slug='histrework3', feature='HistRework=3 (A1, level 3)', job='opus_round1/sol_A1/REPORT.md',
    tier='B', status='conditional', exe='stack', options=['option.HistRework=3'], pins_label='HR3',
    pins_on_report=[336192, 869621, 3052885, 15664938, 35705218], longer_tc=True,
    gain='uncertain', risk='medium (d20 tree +26.4%: crew flag)',
    reason='A1 plan: run only if R3-08 (HistRework=2) ends H1 or capped with Elo > 0',
    facts=['bench ON vs OFF: d11 +7.5%, d13 +0.8%, d16 +0.9%, d20 +26.4%, d22 +4.9%'],
    notes=['queue it with "run_if": {"gate_tag": "<R3-08 tag>", "min_elo": 0}: the r7 runner then skips it when R3-08 ends below 0 Elo'])
add(slug='materialkeytable', feature='MaterialKeyTable (S11 node-exact material key, runtime option)', job='opus_round1/sol_S11/REPORT.md',
    tier='A', status='runnable', exe='stack', options=['option.MaterialKeyTable=true'], pins_label='MKT',
    gain='about zero', risk='low (key equality proven on all count vectors)',
    reason='no measurable speed effect on PC or runner; already contained in FORGE_SPEEDSTACK (R3-10): skip if R3-10 runs',
    facts=['ON nodes == OFF at all refs (PC AVX2 + scalar, Linux)', 'NPS ON/OFF: no effect measurable (CIs include 0)'])
add(slug='ttprefetch', feature='FORGE_S13_TT_CHILD_PREFETCH + TtChildPrefetch=true (S13)', job='opus_round1/sol_S13/REPORT.md',
    tier='A', status='runnable', exe='ttprefetch', options=['option.TtChildPrefetch=true'],
    pins_on_report=AL1,
    gain='about zero', risk='low',
    reason='node-exact; quiet runner d16 +0.00%, d20 -0.11%; also contained in FORGE_SPEEDSTACK (R3-10): skip if R3-10 runs',
    facts=['switch-on exe, option ON: bench 312866/862329/3024920/12389307/34048354, perft and kiwipete exact',
           'ON prints "info string TtChildPrefetch active" once per Searcher (visible in engine_io.log)'])
add(slug='lazyacc', feature='FORGE_NNUE_LAZY_ACC + NnueLazyAcc=true (S12 null-edge accumulator alias)', job='opus_round1/sol_S12/REPORT.md (branch opus-sol-S12)',
    tier='A', status='runnable', exe='lazyacc', options=['option.NnueLazyAcc=true'],
    pins_on_report=AL1,
    gain='about zero (counted saving about 0.07% of bench time)', risk='low (node-exact; the switch build also counts evaluations for its stats line)',
    reason='S12 itself proposes no gate: no measurable effect within +-0.4% on a quiet runner',
    facts=['node-exact: uci_check --full ALL OK with the option off and on (PC and Linux)',
           'copies avoided per bench: d20 183,232 = 1.4-2.7% of evaluations; quiet runner on/off -0.16% / -0.12% CPU NPS, CIs include 0',
           'ON prints "info string NnueLazyAcc active" and one stats line per search'])
add(slug='histrework1', feature='HistRework=1 (A1, level 1)', job='opus_round1/sol_A1/REPORT.md',
    tier='B', status='conditional', exe='stack', options=['option.HistRework=1'], pins_label='HR1',
    pins_on_report=[373261, 1043893, 3399770, 13180132, 35699757], longer_tc=True,
    gain='uncertain', risk='medium-high (fails the crew node screen: d13 +21.1%, d16 +12.4%)',
    reason='A1 plan: last or skipped',
    facts=['bench ON vs OFF: d11 +19.3%, d13 +21.1%, d16 +12.4%, d20 +6.4%, d22 +4.9%'],
    notes=['A1 plan: run it last or skip it (owner decision); it has no run_if, so it runs when the queue reaches it'])
add(slug='nnueint16', feature='FORGE_NNUE_INT16 + NnueInt16=true (S-A2 int16 inference, int32 accumulators)', job='opus_round1/sol_SA2/REPORT.md (branch opus-sol-SA2)',
    tier='B', status='held-crew', exe='int16', options=['option.NnueInt16=true'],
    pins_on_report=[330610, 858175, 2760596, 9564588, 21638970], longer_tc=True, test_plan='G-A2 (srand 869014820, not reused)',
    gain='negative expected at 10+0.1 (same eval within 1 cp, but slower)', risk='high (-10.5% / -13.0% CPU NPS ON on the PC, CR measured -7%)',
    reason='CR policy "H256 nets are float-only": turning it ON for a gate needs a crew vote; listed for completeness',
    facts=['parity 10000/10000 vs an exact integer reference; max 1 cp difference to the float path',
           'ON changes the tree: d11 +5.7%, d13 -0.5%, d16 -8.7%, d20 -22.8%, d22 -36.4%',
           'merged into the stack behind the build switch FORGE_NNUE_INT16 (97b01454); the main session reports the ON pins d11-d20 330610/858175/2760596/9564588 on the stack'],
    notes=['remove the HELD status after a crew vote; the switch build with the option off must give the AL1 pins (S-A2: option OFF = lock identity)'])

# ---------------- Tier C: SMP-only (Threads > 1 on both sides) ----------------
add(slug='smpbestthread', feature='SmpBestThread=true (O1: report the best worker, mate-aware ranking)', job='opus_round1/O1/REPORT.md',
    tier='C', status='needs-runner', exe='stack', options=['option.SmpBestThread=true'], pins_label='SMPB', smp=True, longer_tc=True,
    gain='uncertain, plausibly small positive at Threads 4', risk='low-medium (review fix: a found mate is never replaced by a deeper non-mate)',
    reason='the only SMP option that can change the played move; O1 asks for a 40+0.4 confirm after an H1',
    facts=['inert at Threads 1 (bench identical)', '500 self-play games at Threads 4 with SmpExactNodes+SmpBestThread on: 0 illegal, 0 crashes, 0 stalls'])
add(slug='locklesstt', feature='LocklessTT=true (O1-LTT lockless shared TT)', job='opus_round1/O1-LTT/REPORT.md',
    tier='C', status='needs-runner', exe='stack', options=['option.LocklessTT=true'], pins_label='LTT', smp=True,
    test_plan='G-B5 (srand 1325124880, not reused)',
    gain='uncertain, about zero on 4 vCPUs; unknown with 12 free cores', risk='low-medium (torn writes become misses by design; 24/24 stress runs 0 corrupted, TSan 0)',
    reason='acts only with Threads > 1 (at Threads 1 it costs about 2% NPS), so it is gated, and would be used, only with Threads > 1',
    facts=['Threads 1: bench identical, same-binary NPS -2.25% d16 / -2.06% d20', 'CI 4 vCPUs: on/off NPS 0.990 / 1.014 / 1.013 at T2/T4/T8, time-to-depth differences inside one sd',
           'setoption true prints "info string LocklessTT active" (visible in engine_io.log)'])
add(slug='smpexactnodes', feature='SmpExactNodes=true (O1 bug 1 fix: exact helper node counts)', job='opus_round1/O1/REPORT.md',
    tier='C', status='needs-runner', exe='stack', options=['option.SmpExactNodes=true'], pins_label='SMPX', smp=True,
    gain='about zero in timed games (it fixes go nodes and early info counts)', risk='low',
    reason='a correctness fix for node-limited play; O1 expects only a small effect at time controls',
    facts=['AL1 lock: 4/5 rounds of go nodes 20000 at Threads 3 played an unsearched move; with the option 0/5'])

# ---------------- Tier D: needs a trained net (blocked) ----------------
NET_NOTE = 'BLOCKED: no trained net exists. Every .fnn2 on the PC is a lock replica, an identity net or a CPU smoke net (find over F:\\ and D:\\grok-pc-data, nothing under F:\\forge_nnue_train).'
add(slug='kingbuckets', feature='NNUEKingBuckets=N + NNUEFile=<trained king-bucket net> (C4)', job='opus_round1/C4/REPORT.md',
    tier='D', status='blocked-net', exe='stack', options=['option.NNUEFile=<KB_NET.fnn2>', 'option.NNUEKingBuckets=<N of that net>'],
    early_stop=True, longer_tc=True, test_plan='G-C1 (srand 1352390606, not reused; "gate only on A1 data")',
    gain='uncertain; potentially the largest NNUE item once trained on enough data', risk='medium (training cost; NPS with a real net unmeasured)',
    reason='prerequisite: GPU training of a king-bucket net on the A1 data (C4 recipe), then v2_parity PASS and NPS d16/d20',
    facts=['lock replicas r1/r4/rm2/rm8/rm16 reproduce the AL1 pins (function-preserving, cannot show a gain)', NET_NOTE])
add(slug='outputbuckets', feature='NNUEOutputBuckets=8 + NNUEFile=<trained 8-head net> (C5)', job='opus_round1/C5/REPORT.md',
    tier='D', status='blocked-net', exe='stack', options=['option.NNUEFile=<OB8_NET.fnn2>', 'option.NNUEOutputBuckets=8'],
    early_stop=True, longer_tc=True, test_plan='G-C6 (srand 817455375, not reused)',
    gain='uncertain', risk='medium (v2 path costs about 1-2% CPU on the lock tree)',
    reason='prerequisite: GPU training of an 8-head net (lock recipe + --output-buckets 8)',
    facts=['C5 smoke nets (CPU, synthetic/sample data) are not playing nets', NET_NOTE])
add(slug='pawnpairs', feature='NNUEPawnPairs=1 + NNUEFile=<trained pawn-pair net> (O7)', job='opus_round1/O7/REPORT.md',
    tier='D', status='blocked-net', exe='stack', options=['option.NNUEFile=<PP_NET.fnn2>', 'option.NNUEPawnPairs=1'],
    early_stop=True, longer_tc=True, test_plan='G-C3 (srand 1319449387, not reused)',
    gain='uncertain', risk='high (-17% to -20% NPS on the same tree)',
    reason='prerequisite: GPU training with pawn-pair inputs; the speed cost must be won back by eval quality',
    facts=['zero-pawn-pair replica: CI -17.6% wall / -17.3% CPU d16', NET_NOTE])
add(slug='threats', feature='NNUEThreats=1 + NNUEFile=<trained threat net> (O6)', job='opus_round1/O6/REPORT.md',
    tier='D', status='blocked-net', exe='stack', options=['option.NNUEFile=<THREAT_NET.fnn2>', 'option.NNUEThreats=1'],
    early_stop=True, longer_tc=True, test_plan='G-C2 (srand 2139766817, not reused; 40+0.4 primary)',
    gain='negative expected at 10+0.1 unless the net is much stronger', risk='high (about -40% NPS)',
    reason='prerequisite: GPU training with threat inputs; O6 makes 40+0.4 the primary gate',
    facts=['zero-threat replica: CI -41.0% wall / -40.6% CPU d16', NET_NOTE],
    notes=['owner choice: "tc": "40+0.4" for this entry (O6 and the test plan: 10+0.1 is informational only)'])
add(slug='purennue', feature='PureNnue=1 + NNUEFile=<GPU-trained pure net> (O4)', job='opus_round1/O4/REPORT.md',
    tier='D', status='blocked-net', exe='stack', options=['option.NNUEFile=<PURE_NET.fnn2>', 'option.PureNnue=1'],
    early_stop=True, longer_tc=True, test_plan='G-A5 (srand 1065932896, not reused)',
    gain='uncertain to negative at H256 (drops the HCE endgame scaling)', risk='high',
    reason='prerequisite: the O4 GPU recipe (pure, same data/width as the lock); the queue Build-Args cannot run it as-is',
    facts=['material-trained smoke net: bench d16 5,669,969 (+87% nodes); trees depend on the net', NET_NOTE])
add(slug='h512', feature='H512 build (S-A4: FORGE_NNUE_HIDDEN=512 + FORGE_NNUE_WEIGHTS=<trained H512 net>)', job='opus_round1/sol_SA4/REPORT.md (branch opus-sol-SA4)',
    tier='D', status='blocked-net', exe='h512', options=[], early_stop=True, longer_tc=True, test_plan='G-A4 (srand 507544535, not reused)',
    gain='negative unless the trained net is clearly better (H512 costs -10% to -14% CPU NPS)', risk='high',
    reason='prerequisite: GPU training of an H512 net (GPU_RECIPE_H512.md; the S-A4 build flags are already on the stack); the widened lock net is exact and cannot show a gain',
    facts=['widened H512 vs H256 on the same tree: NnueInt16 ON -12.1% / -13.7%, float -10.1% / -11.5% CPU NPS (loaded PC)', NET_NOTE])

NO_GATE = [
    ('S32 self-play datagen v2 (FORGE_DATAGEN, `forge datagen` mode)', 'data generation only; no search change (main session: no gate)'),
    ('S37 NNUE inference microbench (forge_nnue_microbench target)', 'tool target; the engine is unchanged'),
    ('S04fix FORGE_ATTACKS_INIT_ONCE (synchronised first attack-table init) + cold-start probe ctest', 'init synchronisation, no search change (main session: no gate)'),
    ('S08fix FORGE_PROF profiling counters (stack 9588a109)', 'diagnostic build switch; the main session marked it "no gate"'),
    ('O3 search.cpp module split', 'no behaviour change (bench/codegen identical)'),
    ('C2 CorrHistPlus=7 (all three keys)', 'three changes in one gate; C2 does not propose it (one option per gate)'),
    ('NetScale 90 / 110', 'cross-check values only; S41 proposes 99 for the lock'),
]
