# pin_check.ps1 - Opus R15: check any Forge exe against the lock pins over UCI.
#   bench d11 / d13 / d16 (-Full adds d20 / d22), `go perft 5` on startpos and kiwipete.
# Modes (exit 0 = good, 1 = bad, 2 = bad arguments or the exe cannot run):
#   plain             no -Options, no -Expect: every bench depth and both perfts must equal the lock pins -> PASS / FAIL
#   ON line           -Options 'N=V;N2=V2': every option must be advertised by `uci` and accepted, perft must still equal
#                     the pins and the bench must differ from the lock pins at >= 1 depth -> LIVE; equal everywhere ->
#                     FAIL (dead option: the line would be a lock-vs-lock gate)
#   expected nodes    -Expect 'd11=N,d13=N,...' (with or without -Options): bench must equal these numbers -> PASS / FAIL
# The script sets its own priority class and CPU mask first, so the engine inherits both from its first instruction.
# usage: powershell -NoProfile -ExecutionPolicy Bypass -File pin_check.ps1 -Exe X [-Options 'N=V;...'] [-Full]
#        [-Expect 'd11=..,d13=..'] [-Mask 0x3] [-Priority Idle|BelowNormal] [-Json out.json] [-TimeoutSec 900]
param(
    [Parameter(Mandatory = $true)][string]$Exe,
    [string]$Options = '',
    [string]$Expect = '',
    [switch]$Full,
    [string]$Mask = '0x3',
    [ValidateSet('BelowNormal', 'Idle')][string]$Priority = 'Idle',
    [string]$Json = '',
    [int]$TimeoutSec = 900
)
$ErrorActionPreference = 'Stop'
# String keys only: an [ordered] dictionary indexed with an int is read by POSITION (ArgumentOutOfRange), not by key.
$LockPins = [ordered]@{ 'd11' = 312866; 'd13' = 862329; 'd16' = 3024920; 'd20' = 12389307; 'd22' = 34048354 }
$PerftPins = [ordered]@{ startpos = 4865609; kiwipete = 193690690 }
$Kiwipete = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'

function Fail-Args([string]$msg) { [Console]::Error.WriteLine("pin_check: $msg"); exit 2 }

if (-not (Test-Path -LiteralPath $Exe -PathType Leaf)) { Fail-Args "exe not found: $Exe" }
if ($Json -and (Test-Path -LiteralPath $Json)) { Fail-Args "json target exists (never overwritten): $Json" }
if ($Json) { $jd = Split-Path -Parent $Json; if ($jd -and -not (Test-Path -LiteralPath $jd -PathType Container)) { Fail-Args "json folder missing: $jd" } }
try { $m = [Convert]::ToInt64($Mask, 16) } catch { $m = 0 }
if ($m -le 0) { Fail-Args "-Mask '$Mask' is not a hexadecimal CPU mask" }

# options: 'N=V;N2=V2' (names may contain spaces, values may not)
$opts = [ordered]@{}
foreach ($part in @($Options.Split(';') | Where-Object { $_.Trim() })) {
    $kv = $part.Split('=', 2)
    if ($kv.Count -ne 2 -or -not $kv[0].Trim() -or -not $kv[1].Trim()) { Fail-Args "bad option '$part' (want Name=Value)" }
    $opts[$kv[0].Trim()] = $kv[1].Trim()
}
$depths = @(11, 13, 16); if ($Full) { $depths += 20, 22 }
$expected = [ordered]@{}
if ($Expect) {
    foreach ($part in @($Expect.Split(',') | Where-Object { $_.Trim() })) {
        if ($part.Trim() -notmatch '^d(\d+)=(\d+)$') { Fail-Args "bad -Expect item '$part' (want d11=312866)" }
        $expected['d' + [int]$Matches[1]] = [long]$Matches[2]
    }
    $depths = @($expected.Keys | ForEach-Object { [int]$_.Substring(1) })
}
$mode = if ($Expect) { 'expected' } elseif ($opts.Count) { 'on-line' } else { 'plain' }

$me = [System.Diagnostics.Process]::GetCurrentProcess()
try { $me.PriorityClass = $Priority; $me.ProcessorAffinity = [IntPtr]$m } catch { Fail-Args "cannot set priority / mask: $($_.Exception.Message)" }

$sha = (Get-FileHash -LiteralPath $Exe -Algorithm SHA256).Hash.ToLower()
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = (Resolve-Path -LiteralPath $Exe).Path
$psi.UseShellExecute = $false; $psi.RedirectStandardInput = $true; $psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true; $psi.CreateNoWindow = $true
$psi.WorkingDirectory = Split-Path -Parent $psi.FileName
try { $p = [System.Diagnostics.Process]::Start($psi) } catch { Fail-Args "cannot start ${Exe}: $($_.Exception.Message)" }
$errTask = $p.StandardError.ReadToEndAsync()
$script:pending = $null
$script:log = New-Object System.Collections.Generic.List[string]
function Send([string]$line) {
    $script:log.Add("> $line")
    try { $p.StandardInput.WriteLine($line); $p.StandardInput.Flush() } catch { $script:log.Add("! write failed (engine gone?): $($_.Exception.Message)") }
}
# Read lines until one matches $pattern; returns the match or $null on timeout / engine exit. Lines are logged.
function Read-Until([string]$pattern, [int]$sec) {
    $deadline = (Get-Date).AddSeconds($sec)
    while ($true) {
        if ($null -eq $script:pending) { $script:pending = $p.StandardOutput.ReadLineAsync() }
        $left = [int](($deadline - (Get-Date)).TotalMilliseconds)
        if ($left -le 0) { return $null }
        if (-not $script:pending.Wait([Math]::Min($left, 1000))) { continue }
        $line = $script:pending.Result; $script:pending = $null
        if ($null -eq $line) { return $null }   # end of stream: the engine exited
        $script:log.Add($line)
        if ($line -match $pattern) { return $Matches }
    }
}

$problems = New-Object System.Collections.Generic.List[string]
$bench = [ordered]@{}; $perft = [ordered]@{}; $advertised = [ordered]@{}
$t0 = Get-Date
Send 'uci'
if ($null -eq (Read-Until '^uciok' 60)) { $problems.Add('no uciok within 60 s') }
$uciLines = @($script:log | Where-Object { $_ -match '^option name ' })
foreach ($name in $opts.Keys) {
    $line = $uciLines | Where-Object { $_ -match ('^option name ' + [regex]::Escape($name) + ' type ') } | Select-Object -First 1
    if ($line) {
        $advertised[$name] = $line.Substring(12)
        if ($line -match ' min (-?\d+) max (-?\d+)') {
            $lo = [long]$Matches[1]; $hi = [long]$Matches[2]; $v = 0L
            if (-not [long]::TryParse($opts[$name], [ref]$v)) { $problems.Add("option $name value '$($opts[$name])' is not an integer") }
            elseif ($v -lt $lo -or $v -gt $hi) { $problems.Add("option $name value $v outside min $lo max $hi (the engine would clamp it)") }
        }
    } else { $advertised[$name] = $null; $problems.Add("option $name is not advertised by uci (the gate runner refuses it)") }
    Send "setoption name $name value $($opts[$name])"
}
Send 'isready'
if ($null -eq (Read-Until '^readyok' 60)) { $problems.Add('no readyok after setoption') }
$bad = @($script:log | Where-Object { $_ -match '^info string (invalid|unknown|error)' })
foreach ($b in $bad) { $problems.Add("engine said: $b") }
foreach ($d in $depths) {
    Send "bench $d"
    $r = Read-Until ('^info string bench depth ' + $d + ' nodes (\d+)') $TimeoutSec
    if ($null -eq $r) { $problems.Add("bench ${d}: no result within $TimeoutSec s"); break }
    $bench["d$d"] = [long]$r[1]
}
foreach ($pos in @('startpos', 'kiwipete')) {
    if ($pos -eq 'startpos') { Send 'position startpos' } else { Send "position fen $Kiwipete" }
    Send 'go perft 5'
    $r = Read-Until '^nodes (\d+)$' $TimeoutSec
    if ($null -eq $r) { $problems.Add("perft 5 $pos`: no result within $TimeoutSec s"); break }
    $perft[$pos] = [long]$r[1]
}
Send 'quit'
if (-not $p.WaitForExit(30000)) { $problems.Add('engine did not exit 30 s after quit') }
$stderr = ''; try { if ($errTask.Wait(5000)) { $stderr = $errTask.Result } } catch { }
if ($stderr.Trim()) { $problems.Add("stderr: $($stderr.Trim().Split("`n")[0])") }
$t1 = Get-Date

# verdict
$rows = New-Object System.Collections.Generic.List[string]
$benchDiff = 0
foreach ($d in $depths) {
    $k = "d$d"
    $got = if ($bench.Contains($k)) { $bench[$k] } else { $null }
    $want = if ($mode -eq 'expected') { $expected[$k] } elseif ($LockPins.Contains($k)) { $LockPins[$k] } else { $null }
    $lock = if ($LockPins.Contains($k)) { $LockPins[$k] } else { $null }
    if ($null -ne $got -and $null -ne $lock -and $got -ne $lock) { $benchDiff++ }
    $state = if ($null -eq $got) { 'MISSING' } elseif ($mode -eq 'on-line') { if ($got -eq $lock) { 'same as lock' } else { 'differs (live)' } } elseif ($got -eq $want) { 'ok' } else { 'DIFF' }
    $rows.Add(('bench d{0,-3} {1,12}  want {2,12}  {3}' -f $d, $got, $(if ($mode -eq 'on-line') { "lock $lock" } else { $want }), $state))
    if ($mode -ne 'on-line' -and ($null -eq $got -or $got -ne $want)) { $problems.Add("bench d$d = $got, want $want") }
    if ($mode -eq 'on-line' -and $null -eq $got) { $problems.Add("bench d$d missing") }
}
foreach ($pos in $PerftPins.Keys) {
    $got = if ($perft.Contains($pos)) { $perft[$pos] } else { $null }
    $state = if ($got -eq $PerftPins[$pos]) { 'ok' } else { 'DIFF' }
    $rows.Add(('perft5 {0,-9} {1,12}  want {2,12}  {3}' -f $pos, $got, $PerftPins[$pos], $state))
    if ($got -ne $PerftPins[$pos]) { $problems.Add("perft 5 $pos = $got, want $($PerftPins[$pos])") }
}
if ($mode -eq 'on-line' -and $benchDiff -eq 0 -and $bench.Count -eq $depths.Count) { $problems.Add('ON line gives the lock bench at every depth: dead option') }
$verdict = if ($problems.Count) { 'FAIL' } elseif ($mode -eq 'on-line') { 'LIVE' } else { 'PASS' }

"pin_check $verdict  mode $mode  exe $Exe"
"sha256 $sha  options [$Options]  priority $Priority mask $Mask  $([int]($t1 - $t0).TotalSeconds) s"
foreach ($n in $advertised.Keys) { "advertised $n -> $($advertised[$n])" }
$rows
foreach ($x in $problems) { "problem: $x" }
if ($Json) {
    $o = [ordered]@{ tool = 'pin_check.ps1'; verdict = $verdict; mode = $mode; exe = (Resolve-Path -LiteralPath $Exe).Path
        sha256 = $sha; options = $opts; advertised = $advertised; bench = $bench; perft = $perft; problems = @($problems)
        started = $t0.ToString('yyyy-MM-dd HH:mm:ss'); ended = $t1.ToString('yyyy-MM-dd HH:mm:ss'); priority = $Priority; mask = $Mask
        transcript = @($script:log | Where-Object { $_ -notmatch '^[a-h][1-8][a-h][1-8][qrbn]?: \d+$' }) }
    $text = $o | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($Json, $text.Replace("`r`n", "`n") + "`n")
}
if ($verdict -eq 'FAIL') { exit 1 }
exit 0
