# verify_evidence.ps1 - an independent recount of the job-3 evidence (PowerShell 5.1, ASCII only).
#
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File verify_evidence.ps1 [-Log FILE]
#
# It shares no code with the Python harness and starts no engine. It hashes the frozen executables and the
# probes again, reads the receipts and ledgers under out\job3, and recomputes what PROOF.md states: the pins
# against the numbers of the job text, divide and warm results against the lock's, the fuzz totals per
# candidate, and that every counted row names the frozen binaries and holds two equal output hashes. Then it
# compares its own totals with the verdict table of PROOF.md.
# Last line: "VERIFY EVIDENCE OK n/n" (exit 0) or "VERIFY EVIDENCE FAILED ..." (exit 3). It writes nothing, except
# with -Log: then the printed lines are also written to that file (the handoff keeps one as VERIFY_EVIDENCE.log).
# A PASS in PROOF.md is accepted only with 20,000,000 positions on the auxiliary tier AND all 200 chunks on the
# release executables for that candidate.
param([string]$Log = '')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'job3_env.ps1')
[void](J3-Pin 0x78)
$R = Join-Path $J3_OUT 'runs'
$CANDS = @('EVL', 'PCM', 'CKL', 'WNP', 'KPC', 'BUN')
$PROBED = @('LOCK', 'LOCKEQ') + $CANDS
$TAGS9 = @('LOCK', 'LOCKCOPY', 'LOCKEQ') + $CANDS
$script:n = 0; $script:bad = 0; $script:lines = New-Object System.Collections.ArrayList
function Say([string]$s) { [void]$script:lines.Add($s); Microsoft.PowerShell.Utility\Write-Output $s }

function Chk([string]$text, $fails) {      # one check: a text and the list of what contradicts it (not "Group": that is an alias)
    $script:n++
    $list = @($fails | Where-Object { $null -ne $_ })      # an empty list may arrive as $null
    if ($list.Count -gt 0) {
        $script:bad++
        Say "BAD  $text"
        foreach ($x in ($list | Select-Object -First 8)) { Say "       $x" }
        if ($list.Count -gt 8) { Say ("       ... and {0} more" -f ($list.Count - 8)) }
    } else { Say "OK   $text" }
}
function J([string]$path) {
    if (Test-Path -LiteralPath $path) { return (Get-Content -LiteralPath $path -Raw | ConvertFrom-Json) }
    return $null
}
function Tsv([string]$path) {
    # rows of a tab-separated file as hashtables; the file may still be appended to by a running fuzz
    $rows = New-Object System.Collections.ArrayList
    if (-not (Test-Path -LiteralPath $path)) { return ,$rows }
    $fs = New-Object System.IO.FileStream($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    $sr = New-Object System.IO.StreamReader($fs, [System.Text.Encoding]::ASCII)
    try {
        $head = $sr.ReadLine().Split("`t")
        while (-not $sr.EndOfStream) {
            $ln = $sr.ReadLine()
            if ($ln.Trim() -eq '') { continue }
            $p = $ln.Split("`t")
            if ($p.Length -ne $head.Length) { continue }      # a row that is being written
            $h = @{}
            for ($k = 0; $k -lt $head.Length; $k++) { $h[$head[$k]] = $p[$k] }
            [void]$rows.Add($h)
        }
    } finally { $sr.Dispose(); $fs.Dispose() }
    return ,$rows
}
function Compact($x) { return ($x | ConvertTo-Json -Compress -Depth 6) }
function Cnt($x) { if ($null -eq $x) { return 0 }; return @($x).Count }      # a missing or empty list counts 0
function N($x) { return ([int64]$x).ToString('N0', [System.Globalization.CultureInfo]::InvariantCulture) }

# ---------------------------------------------------------------- A. the binaries, hashed now
$JOBMD5 = @{ LOCK = 'c0051c99695f48bf93272d96fe7548c3'; EVL = '35781e5cac204370584ff4cb1f5ee93e'; PCM = '2cd6d44845e343f8b206b60f876c2165'
             CKL = '8a159aed19f0d1ff0a9ee468e279794f'; WNP = '1bf0291be0b2936c394c9a908f7432fe'; KPC = '55e1fe1230b5d19bd5382636a86f9c90' }
$inputs = @{}
foreach ($e in (J (Join-Path $R 'freeze\INPUTS.json'))) { $inputs[$e.tag] = $e }
$exe = @{}; $probe = @{}; $f = @()
foreach ($t in $TAGS9) { $exe[$t] = J3-Hash (Join-Path $J3_OUT "bin\$t\engine.exe") 'SHA256' }
foreach ($t in $JOBMD5.Keys) { if ((J3-Hash (Join-Path $J3_OUT "bin\$t\engine.exe") 'MD5') -ne $JOBMD5[$t]) { $f += "${t}: MD5 is not the one of the job text" } }
foreach ($t in $PROBED) { if ($exe[$t] -ne $inputs[$t].exe_sha256 -or $inputs[$t].status -ne 'OK') { $f += "${t}: sha256 is not the one of INPUTS.json, or its status is not OK" } }
if ($exe['LOCKCOPY'] -ne $exe['LOCK']) { $f += 'LOCKCOPY is not byte-identical to LOCK' }
if (@($CANDS | ForEach-Object { $exe[$_] } | Where-Object { $_ -eq $exe['LOCK'] }).Count -gt 0) { $f += 'a candidate executable is the lock executable' }
Chk 'executables: the 6 MD5s of the job text (lock and five QA builds), 8 sha256 of INPUTS.json, LOCKCOPY = LOCK, no candidate = LOCK' $f
$f = @()
foreach ($t in $PROBED) {
    $probe[$t] = J3-Hash (Join-Path $J3_OUT "aux2\$t\mgprobe.exe") 'SHA256'
    $rc = J (Join-Path $J3_OUT "aux2\$t\AUX_RECEIPT.json")
    if ($null -eq $rc -or $probe[$t] -ne $rc.exe_sha256) { $f += "${t}: probe sha256 is not the one of its build receipt" }
}
if (@($probe.Values | Sort-Object -Unique).Count -ne 8) { $f += 'two probes are the same file' }
Chk 'probes: 8 files, each with the sha256 of its build receipt, all different' $f

# ---------------------------------------------------------------- B. pins against the numbers of the job text
$DEPTHS = @(11, 13, 16, 20, 22)
$PIN_ON = @(312866, 862329, 3024920, 12389307, 34048354)
$PIN_OFF = @(375354, 907205, 2448617, 13573040, 24506465)
$f = @()
foreach ($t in $TAGS9) {
    $p = J (Join-Path $R "pins\$t.json")
    if ($null -eq $p) { $f += "${t}: no receipt"; continue }
    if ($p.exe_sha256 -ne $exe[$t]) { $f += "${t}: the receipt names another executable" }
    for ($i = 0; $i -lt 5; $i++) {
        $on = $p.bench.("net_on_d" + $DEPTHS[$i]).nodes; $off = $p.bench.("net_off_d" + $DEPTHS[$i]).nodes
        if ([int64]$on -ne $PIN_ON[$i]) { $f += "${t}: bench net on depth $($DEPTHS[$i]) is $on" }
        if ([int64]$off -ne $PIN_OFF[$i]) { $f += "${t}: bench net off depth $($DEPTHS[$i]) is $off" }
    }
    if ([int64]$p.perft.startpos_perft5.nodes -ne 4865609) { $f += "${t}: startpos perft 5 is $($p.perft.startpos_perft5.nodes)" }
    if ([int64]$p.perft.kiwipete_perft4.nodes -ne 4085603) { $f += "${t}: kiwipete perft 4 is $($p.perft.kiwipete_perft4.nodes)" }
    if ([int64]$p.perft.kiwipete_perft5.nodes -ne 193690690) { $f += "${t}: kiwipete perft 5 is $($p.perft.kiwipete_perft5.nodes)" }
}
Chk 'pins: the 13 numbers of the job text in the receipts of 9 executables, each receipt naming the frozen file' $f

# ---------------------------------------------------------------- C. perft divide against the lock's
$ld = J (Join-Path $R 'divide\LOCK.json'); $f = @(); $roots = 0
if ($null -eq $ld -or $ld.status -ne 'DONE' -or $ld.exe_sha256 -ne $exe['LOCK'] -or @($ld.positions).Count -ne 10) { $f += 'LOCK: no usable receipt with ten runs' }
else {
    foreach ($q in $ld.positions) { $roots += @($q.divide).Count; if ($null -ne $q.published -and [int64]$q.total -ne [int64]$q.published) { $f += "LOCK $($q.name): total $($q.total) is not the published $($q.published)" } }
    foreach ($t in ($TAGS9 | Where-Object { $_ -ne 'LOCK' })) {
        $d = J (Join-Path $R "divide\$t.json")
        if ($null -eq $d -or $d.status -ne 'DONE' -or $d.exe_sha256 -ne $exe[$t]) { $f += "${t}: no receipt of the frozen executable"; continue }
        for ($i = 0; $i -lt 10; $i++) {
            $a = $ld.positions[$i]; $b = $d.positions[$i]
            if ($a.fen -ne $b.fen -or $a.depth -ne $b.depth -or $a.total -ne $b.total -or (Compact $a.divide) -ne (Compact $b.divide) -or (Cnt $b.other_lines) -ne 0) { $f += "${t}: $($a.name) depth $($a.depth) differs from the lock" }
        }
    }
}
Chk "perft divide: 10 runs, $roots root moves, every count equal to the lock's for 8 executables; lock totals equal the published ones" $f

# ---------------------------------------------------------------- D. warm transcript, E. soak
$f = @(); $lw = J (Join-Path $R 'warm\LOCK.json')
foreach ($t in $TAGS9) {
    $w = J (Join-Path $R "warm\$t.json")
    if ($null -eq $w -or $w.status -ne 'DONE' -or $w.exe_sha256 -ne $exe[$t]) { $f += "${t}: no receipt of the frozen executable"; continue }
    $now = J3-Hash (Join-Path $R "warm\$t.transcript.txt") 'SHA256'
    if ($now -ne $w.transcript_sha256) { $f += "${t}: the transcript file is not the one of the receipt" }
    if ($now -ne $lw.transcript_sha256) { $f += "${t}: the transcript differs from the lock's" }
    if ([int64]$w.bench13 -ne 862329 -or $w.searches -ne 101 -or $w.exit -ne 0 -or (Cnt $w.illegal_or_invalid_lines) -ne 0) { $f += "${t}: bench13 $($w.bench13), searches $($w.searches), exit $($w.exit)" }
}
Chk 'warm transcript: the transcript files of 9 executables hashed now, all equal to the lock''s; 101 searches; bench 13 still 862329' $f
$f = @()
foreach ($t in $TAGS9) {
    $s = J (Join-Path $R "soak\$t.json")
    if ($null -eq $s -or $s.exe_sha256 -ne $exe[$t]) { $f += "${t}: no receipt of the frozen executable"; continue }
    $illegal = @($s.searches | Where-Object { -not $_.legal }).Count
    $threads = @($s.searches | ForEach-Object { $_.threads } | Sort-Object -Unique) -join ','
    if ($s.status -ne 'STABLE' -or $s.exit -ne 0 -or @($s.searches).Count -ne 78 -or $illegal -ne 0 -or [int64]$s.bench13_after -ne 862329 -or $threads -ne '2,3,4') { $f += "${t}: status $($s.status), exit $($s.exit), searches $(@($s.searches).Count), illegal bestmoves $illegal, threads $threads" }
}
Chk 'Threads soak: 9 executables, 78 searches each at Threads 2, 3 and 4, every bestmove legal, exit 0, bench 13 afterwards 862329 (stability only)' $f

# ---------------------------------------------------------------- F. edge suite
$suiteFile = Join-Path $J3_PACK 'suite\edge_suite.tsv'
$suite = Tsv $suiteFile; $suiteSha = J3-Hash $suiteFile 'SHA256'
$legal = @($suite | Where-Object { $_['class'] -eq 'LEGAL' })
$distinct = @($legal | ForEach-Object { $_['fen'] } | Sort-Object -Unique -CaseSensitive).Count
$f = @()
if ($distinct -lt 300 -or $distinct -ne $legal.Count) { $f += "legal entries $($legal.Count), distinct FENs $distinct" }
if (@($suite | Where-Object { $_['category'] -eq '' -or $_['provenance'] -eq '' -or $_['class'] -notin @('LEGAL', 'REJECTED', 'UNREACHABLE') }).Count -ne 0) { $f += 'an entry without category, provenance or class' }
Chk ("edge suite file: {0} legal entries with {1} distinct FENs (at least 300 required), {2} rejected, {3} unreachable, kept apart by class; category and provenance on every entry" -f $legal.Count, $distinct, @($suite | Where-Object { $_['class'] -eq 'REJECTED' }).Count, @($suite | Where-Object { $_['class'] -eq 'UNREACHABLE' }).Count) $f
$f = @(); $recs = ''; $blocks = ''
foreach ($t in ($TAGS9 | Where-Object { $_ -ne 'LOCK' })) {
    $e = J (Join-Path $R "edge\$t.json")
    if ($null -eq $e) { $f += "${t}: no receipt"; continue }
    $wantProbe = $(if ($t -eq 'LOCKCOPY') { $probe['LOCK'] } else { $probe[$t] })
    if ($e.exe_sha256 -ne $exe[$t] -or $e.lock_exe_sha256 -ne $exe['LOCK'] -or $e.probe_sha256 -ne $wantProbe -or $e.suite_sha256 -ne $suiteSha) { $f += "${t}: the receipt names another executable, probe or suite file" }
    if ($e.status -ne 'MATCH' -or $e.tier_a_legal.status -ne 'EQUAL' -or $e.tier_r_legal.status -ne 'EQUAL' -or $e.legal_entries -ne $legal.Count) { $f += "${t}: status $($e.status), tier A $($e.tier_a_legal.status), tier R $($e.tier_r_legal.status)" }
    if ((Cnt $e.legal_position_differences) + (Cnt $e.robustness_differences) + (Cnt $e.harness_errors) + (Cnt $e.lock_vs_oracle.probe_differences) + (Cnt $e.lock_vs_oracle.exe_differences) + (Cnt $e.lock_rejected_handling_problems) -ne 0 -or $e.lock_vs_oracle.entries -ne $legal.Count) { $f += "${t}: a difference, an error or an oracle disagreement is listed" }
    if (-not $e.tier_r_rejected.identical_to_lock -or -not $e.tier_a_rejected.identical_to_lock -or -not $e.search_signature.net_on.identical_to_lock -or -not $e.search_signature.net_off.identical_to_lock) { $f += "${t}: rejected entries or search signature not identical to the lock" }
    $recs = $e.tier_a_legal.records; $blocks = $e.tier_r_legal.perft_blocks
}
Chk "edge suite run: 8 tags MATCH ($recs probe records and $blocks perft blocks each), no legal-position or robustness difference, lock equal to the oracle, receipts naming the frozen files" $f

# ---------------------------------------------------------------- G. fuzz, auxiliary tier
$seedSha = @{ v1 = (J3-Hash (Join-Path $J3_OUT 'corpus\seeds_v1.txt') 'SHA256').Substring(0, 16); v2 = (J3-Hash (Join-Path $J3_OUT 'corpus\seeds_v2.txt') 'SHA256').Substring(0, 16) }
$aux = Tsv (Join-Path $R 'fuzz_aux\ledger.tsv'); $f = @(); $countA = @{}; $harness = @{}; $pathA = @{}
foreach ($c in $CANDS) {
    $rows = @($aux | Where-Object { $_['cand'] -eq $c })
    $ok = @{}; $pos = 0
    foreach ($w in $rows) {
        $k = [int]$w['chunk']; $harness[$w['harness_sha256']] = 1
        if ($w['status'] -ne 'OK') { $f += "${c} chunk ${k}: status $($w['status'])"; continue }
        if ($w['ref_sha256'] -ne $w['cand_sha256']) { $f += "${c} chunk ${k}: OK row with two different transcript hashes" }
        if ($w['lock_probe_sha256'] -ne $probe['LOCK'] -or $w['cand_probe_sha256'] -ne $probe[$c]) { $f += "${c} chunk ${k}: the row names another probe" }
        $wantSeeds = $(if ($k -lt 100) { 'v1:' + $seedSha['v1'] } else { 'v2:' + $seedSha['v2'] })
        if ($w['seeds'] -ne $wantSeeds) { $f += "${c} chunk ${k}: seeds $($w['seeds'])" }
        if ($pathA.ContainsKey($k) -and $pathA[$k] -ne $w['path_sha256']) { $f += "chunk ${k}: two different inputs for the same chunk" }
        $pathA[$k] = $w['path_sha256']
        if (-not $ok.ContainsKey($k)) { $ok[$k] = 1; $pos += [int64]$w['positions'] }
    }
    $missing = @(0..199 | Where-Object { -not $ok.ContainsKey($_) })
    if ($missing.Count -ne 0) { $f += "${c}: chunks without an OK row: $($missing.Count)" }
    $countA[$c] = $pos
}
if ($harness.Keys.Count -ne 1) { $f += "harness hashes in the rows: $($harness.Keys.Count)" }
Chk ("fuzz tier A: {0} rows; per candidate chunks 0-199 each once, {1} positions; every row OK with two equal transcript hashes, the frozen probes, the right seeds file and one harness hash" -f $aux.Count, (($CANDS | ForEach-Object { N $countA[$_] } | Sort-Object -Unique) -join ' / ')) $f

# ---------------------------------------------------------------- H. fuzz, release executables
$uci = Tsv (Join-Path $R 'fuzz_uci\ledger.tsv'); $f = @(); $countR = @{}; $shared = 0
foreach ($c in $CANDS) {
    $ok = @{}; $pos = 0
    foreach ($w in @($uci | Where-Object { $_['cand'] -eq $c })) {
        $k = [int]$w['chunk']
        if ($w['status'] -ne 'OK') { $f += "${c} chunk ${k}: status $($w['status'])"; continue }
        if ($w['ref_out_sha256'] -ne $w['cand_out_sha256']) { $f += "${c} chunk ${k}: OK row with two different output hashes" }
        if ($w['lock_exe_sha256'] -ne $exe['LOCK'] -or $w['cand_exe_sha256'] -ne $exe[$c]) { $f += "${c} chunk ${k}: the row names another executable" }
        if ($w['tie'] -ne 'lock exe = lock probe on 100000' -or $w['perft_depth'] -ne '2') { $f += "${c} chunk ${k}: tie '$($w['tie'])', depth $($w['perft_depth'])" }
        if ($pathA.ContainsKey($k)) { if ($pathA[$k] -ne $w['path_sha256']) { $f += "chunk ${k}: tier R ran another input than tier A" } elseif ($c -eq 'EVL') { $shared++ } }
        if (-not $ok.ContainsKey($k)) { $ok[$k] = 1; $pos += [int64]$w['positions'] }
    }
    $countR[$c] = $pos
}
Chk ("fuzz tier R: {0} rows; per candidate {1} positions; every row OK with two equal output hashes, the frozen executables and the tie to the lock probe; the input of {2} chunks is the input tier A ran" -f $uci.Count, (($CANDS | ForEach-Object { N $countR[$_] } | Sort-Object -Unique) -join ' / '), $shared) $f

# ---------------------------------------------------------------- I. cache-state variants, J. cross-tier, K. search, L. targets, M. replays
$warm = Tsv (Join-Path $R 'fuzz_warm\ledger.tsv'); $f = @()
foreach ($c in $CANDS) {
    foreach ($v in 'never_cleared', 'cleared_before_every_playout') {
        $rows = @($warm | Where-Object { $_['cand'] -eq $c -and $_['variant'] -eq $v })
        $good = @($rows | Where-Object { $_['status'] -eq 'OK' -and $_['ref_sha256'] -eq $_['cand_sha256'] -and $_['positions'] -eq '100000' -and $_['lock_probe_sha256'] -eq $probe['LOCK'] -and $_['cand_probe_sha256'] -eq $probe[$c] })
        if ($rows.Count -eq 0 -or $good.Count -ne $rows.Count) { $f += "${c} ${v}: $($good.Count) good rows of $($rows.Count)" }
    }
}
Chk ("cache-state variants: {0} rows, both variants for every candidate, every row OK with two equal transcript hashes and the frozen probes" -f $warm.Count) $f
$f = @()
foreach ($t in $PROBED) {
    $x = J (Join-Path $R "crosstier\$t.json")
    if ($null -eq $x -or $x.status -ne 'MATCH' -or $x.positions -ne 2000 -or $x.identical_lists -ne 2000 -or $x.probe_sha256 -ne $probe[$t] -or $x.exe_sha256 -ne $exe[$t]) { $f += "${t}: not MATCH 2000 of 2000 with the frozen files" }
}
Chk 'probe against its own release executable: 8 tags, 2,000 positions each, identical move lists, receipts naming the frozen files' $f
$f = @(); $sigN = ''
foreach ($c in $CANDS) {
    foreach ($net in 'on', 'off') {
        $x = J (Join-Path $R "search_sig\${c}_net$net.json")
        if ($null -eq $x) { $f += "${c} net ${net}: no receipt"; continue }
        if (-not $x.identical_to_lock -or $x.rows_sha256 -ne $x.lock_rows_sha256 -or $x.exit -ne 0 -or $x.exe_sha256 -ne $exe[$c] -or $x.lock_exe_sha256 -ne $exe['LOCK']) { $f += "${c} net ${net}: not identical, or another executable, or exit $($x.exit)" }
        $sigN = "$($x.positions) positions, depth $($x.depth)"
    }
}
Chk "search signatures (supplementary): 6 candidates, net on and off, $sigN, equal row hashes, exit 0, the frozen executables" $f
$f = @(); $tn = ''
foreach ($t in (@('LOCKEQ') + $CANDS)) {
    $x = J (Join-Path $R "wnp_targets\$t.json")
    if ($null -eq $x -or $x.status -ne 'MATCH' -or $x.targets -ne $x.positions_identical -or $x.probe_sha256 -ne $probe[$t] -or $x.lock_probe_sha256 -ne $probe['LOCK']) { $f += "${t}: not MATCH with the frozen probes" } else { $tn = $x.targets }
}
Chk "WITNESS_NOPIN targets (supplementary): 7 tags, $tn targets each, identical records, the frozen probes" $f
$f = @(); $reps = @(Get-ChildItem -LiteralPath (Join-Path $R 'replay') -Filter '*.json' -ErrorAction SilentlyContinue)
foreach ($p in $reps) { $x = J $p.FullName; if ($x.status -ne 'REPRODUCED') { $f += "$($p.Name): $($x.status)" } }
if ($reps.Count -eq 0) { $f += 'no replay receipt' }
Chk ("replays: {0} counted ledger rows run again, every one reproduced with every hash equal to the row" -f $reps.Count) $f

# ---------------------------------------------------------------- N. self-test, failure folder
$logs = @(Get-ChildItem -LiteralPath (Join-Path $R 'selftest') -Filter '*.log' | Sort-Object LastWriteTime)
$last = (Get-Content -LiteralPath $logs[-1].FullName | Select-Object -Last 1).Trim(); $f = @()
if ($last -notmatch '^SELFTEST PASS (\d+)/(\d+)$' -or $Matches[1] -ne $Matches[2]) { $f += "the newest log $($logs[-1].Name) ends with: $last" }
$notPass = @(Get-Content -LiteralPath $logs[-1].FullName | Where-Object { $_ -match '^(FAIL|ERROR)' }).Count
if ($notPass -ne 0) { $f += "$notPass FAIL lines in the newest log" }
Chk "self-test: the newest log $($logs[-1].Name) ends with '$last' and holds no FAIL line" $f
$ff = @(Get-ChildItem -LiteralPath (Join-Path $J3_OUT 'fail') -Recurse -File -ErrorAction SilentlyContinue)
$f = @(); if ($ff.Count -ne 0) { $f += "$($ff.Count) files" }
Chk 'failure folder out\job3\fail: empty' $f

# ---------------------------------------------------------------- O. the ledger copies in evidence\ are the ledgers of out\job3
$evA = @{}; $evR = @{}; $chunksA = @{}; $chunksR = @{}; $f = @(); $behind = 0
foreach ($pair in @(@('fuzz_aux', $aux, $evA, $chunksA), @('fuzz_uci', $uci, $evR, $chunksR))) {
    $copy = Tsv (Join-Path $J3_PACK "evidence\$($pair[0])\ledger.tsv"); $live = $pair[1]
    if ($copy.Count -eq 0 -or $copy.Count -gt $live.Count) { $f += "$($pair[0]): the copy has $($copy.Count) rows, the ledger $($live.Count)" }
    else {
        for ($i = 0; $i -lt $copy.Count; $i++) { if ($copy[$i]['when'] -ne $live[$i]['when'] -or $copy[$i]['cand'] -ne $live[$i]['cand'] -or $copy[$i]['chunk'] -ne $live[$i]['chunk'] -or $copy[$i]['status'] -ne $live[$i]['status']) { $f += "$($pair[0]): row $($i + 1) of the copy is not row $($i + 1) of the ledger"; break } }
        $behind += $live.Count - $copy.Count
    }
    foreach ($c in $CANDS) {
        $ok = @{}; $pos = 0
        foreach ($w in @($copy | Where-Object { $_['cand'] -eq $c -and $_['status'] -eq 'OK' })) { $k = [int]$w['chunk']; if (-not $ok.ContainsKey($k)) { $ok[$k] = 1; $pos += [int64]$w['positions'] } }
        $pair[2][$c] = $pos
        $pair[3][$c] = @($ok.Keys | Where-Object { [int]$_ -ge 0 -and [int]$_ -le 199 }).Count
    }
}
Chk ("ledger copies in evidence\: row for row the ledgers of out\job3 (the ledgers have {0} rows more: {1})" -f $behind, $(if ($behind -eq 0) { 'the copies are complete' } else { 'a fuzz was still running when the report was made, or has run since' })) $f

# ---------------------------------------------------------------- P. the verdict table of PROOF.md against a recount of the copies
$countA = $evA; $countR = $evR
$proof = Get-Content -LiteralPath (Join-Path $J3_PACK 'PROOF.md'); $f = @(); $verdicts = @()
foreach ($c in $CANDS) {
    $row = @($proof | Where-Object { $_ -like "| ${c}: *" }) | Select-Object -First 1
    if (-not $row) { $f += "${c}: no row in the verdict table"; continue }
    $cell = $row.Split('|')
    $v = $(if ($cell[2] -match '\*\*([A-Z ]+)\*\*') { $Matches[1] } else { '?' })
    $a = [int64]($cell[3].Trim() -replace ',', ''); $r = [int64]($cell[4].Trim() -replace ',', '')
    $verdicts += "$c $v"
    if ($a -ne $countA[$c]) { $f += "${c}: PROOF.md says tier A $a, this recount $($countA[$c])" }
    if ($r -ne $countR[$c]) { $f += "${c}: PROOF.md says tier R $r, this recount $($countR[$c])" }
    if ($v -eq 'PASS' -and ($countA[$c] -lt 20000000 -or $chunksA[$c] -ne 200 -or $countR[$c] -lt 20000000 -or $chunksR[$c] -ne 200 -or $script:bad -ne 0)) { $f += "${c}: PROOF.md says PASS, but this recount has a failed check, or fewer than 200 chunks and 20,000,000 positions on one of the two tiers (tier A $($chunksA[$c]) chunks, tier R $($chunksR[$c]) chunks)" }
    $verdicts[$verdicts.Count - 1] += " (A $($chunksA[$c])/200, R $($chunksR[$c])/200 chunks)"
}
Chk ("PROOF.md verdict table against this recount: " + ($verdicts -join ', ')) $f

if ($script:bad -eq 0) { Say ("VERIFY EVIDENCE OK {0}/{0}  ({1})" -f $script:n, (J3-Now)) } else { Say ("VERIFY EVIDENCE FAILED: {0} of {1} checks  ({2})" -f $script:bad, $script:n, (J3-Now)) }
if ($Log -ne '') { [System.IO.File]::WriteAllLines($Log, [string[]]$script:lines, [System.Text.Encoding]::ASCII) }
if ($script:bad -eq 0) { exit 0 } else { exit 3 }
