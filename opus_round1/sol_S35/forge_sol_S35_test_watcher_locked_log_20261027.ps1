#requires -Version 7.0
<#
.SYNOPSIS
  S35 locked-log watcher test harness (Forge PC autonomy; spec Sol S35; written by opus 2026-10-27).

.DESCRIPTION
  Holds a synthetic fastchess-style gate log (<tag>.log, the fastchess stdout file the PC driver redirects) open under a
  writer lock and appends a synthetic "loses on time" line, then checks that a COPY of a watcher sees it.
  Scenarios (each in a fresh scratch sandbox):
    S1  locked log: writer holds <tag>.log (mode 'exclusive' = FileAccess.Write + FileShare.Read, the spec's exclusive
        writer lock; mode 'driver' = ReadWrite + FileShare.Read|Write, what Start-Process -RedirectStandardOutput uses);
        a TL line is appended under the lock. The watcher must ALERT TL 1 with no 'loop error'.
    S2  rotation/truncation: tick 1 TL 1 -> ALERT; the log is moved to partial_<ts>\ (as the driver's Archive-Partial
        does) and a fresh log with one new TL is written -> tick 2 must ALERT again; the writer then truncates in place
        and writes one more new TL -> tick 3 must ALERT again. No 'loop error'.
    S3  missing file: RUN_INFO present, no <tag>.log -> tick 1 no ALERT, no error (HB games 0 TL 0 if printed); the log
        then appears (locked) with one TL -> tick 2 ALERT TL 1.
    S4  UTF-8 BOM: the locked log starts with EF BB BF and its first line is a finished TL game -> ALERT TL 1 and (if the
        watcher prints it) HB games == the true number of 'Finished game' lines (a BOM that is not stripped breaks ^).
  Target kinds:
    e2e       a conc-watcher copy (conc7_watch family) run as a child pwsh for N ticks against the sandbox.
    function  Read-Shared + Log-TLCrash extracted verbatim (PowerShell AST, -ExtractFrom mode) from an autopromote copy,
              called in-process at each tick point; must return the TL/crash counts of the current file.
  SAFETY (copies only): every live path literal of an e2e copy is rewritten to the sandbox (each must occur exactly
  once), the Global\ mutex becomes a Local\ one, and the patched text is refused if any live root, a Global\ name or an
  unstubbed side-effect command remains. The child runner (s35_child_runner.ps1) stubs taskkill/Stop-Process/
  Start-Process/Get-CimInstance/Get-Counter/Start-Sleep. Nothing is written outside -WorkDir; -WorkDir itself is
  refused if it names a live root. No alert or notification leaves the sandbox.

.EXAMPLE
  pwsh -NoProfile -File forge_sol_S35_test_watcher_locked_log_20261027.ps1 -Targets fixtures\targets.json -WorkDir F:\opus_scratch\sol_s35\work -OutJson F:\opus_scratch\sol_s35\suite.json
.EXAMPLE
  pwsh -NoProfile -File forge_sol_S35_test_watcher_locked_log_20261027.ps1 -Watcher <copy of conc7_watch.ps1> -Conc 8 -WorkDir <scratch>
#>
[CmdletBinding(DefaultParameterSetName = 'suite')]
param(
  [Parameter(ParameterSetName = 'suite', Mandatory = $true)][string]$Targets,
  [Parameter(ParameterSetName = 'one', Mandatory = $true)][string]$Watcher,
  [Parameter(ParameterSetName = 'one')][ValidateSet('e2e', 'function')][string]$Kind = 'e2e',
  [Parameter(ParameterSetName = 'one')][ValidateSet(7, 8)][int]$Conc = 8,
  [Parameter(ParameterSetName = 'one')][string]$Label = 'single',
  [Parameter(ParameterSetName = 'extract', Mandatory = $true)][string]$ExtractFrom,
  [Parameter(ParameterSetName = 'extract', Mandatory = $true)][string[]]$Names,
  [Parameter(ParameterSetName = 'extract', Mandatory = $true)][string]$OutFile,
  [string[]]$Scenarios = @('S1', 'S2', 'S3', 'S4'),
  [string]$WorkDir = (Join-Path ([IO.Path]::GetTempPath()) 'forge_s35_work'),
  [string]$OutJson = '',
  [ValidateRange(10, 600)][int]$TickTimeoutSec = 90
)
Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
# pwsh -File passes "a,b" as one string: accept comma lists for the array parameters
$Scenarios = @($Scenarios | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
if ($PSBoundParameters.ContainsKey('Names')) { $Names = @($Names | ForEach-Object { $_ -split ',' } | Where-Object { $_ }) }

$HARNESS = 'forge_sol_S35_test_watcher_locked_log_20261027.ps1 v1'
$LIVE_RX = '(?i)(grok-pc\\forge_push|\\Users\\Administrator\\grok-pc|D:\\grok-pc-data|F:\\forge_nnue_train|F:\\forge_out|Global\\)'
$TAG = 'gate_s35_test'; $NEXT = 'gate_s35_next'; $CAND = 'cand_s35'; $BASE = 'base_s35'
$RUNNER = Join-Path $PSScriptRoot 's35_child_runner.ps1'
$PWSH = Join-Path $PSHOME $(if ($IsWindows) { 'pwsh.exe' } else { 'pwsh' })
# live path literals of the conc7_watch family (lines 14-15 of v0/v1/v2) -> sandbox sub paths
$SUBS = [ordered]@{
  "'C:\Users\Administrator\grok-pc\forge_push\qa_conc7'"                 = 'qa'
  "'C:\Users\Administrator\grok-pc\forge_push\autorestart'"              = 'autorestart'
  "'D:\grok-pc-data\forge_push'"                                         = 'gates'
  "'C:\Users\Administrator\grok-pc\nnue\tools\hwinfo\gpu_sensors.csv'" = 'hw\gpu_sensors.csv'
}
$MUTEX_LIT = "'Global\forge_conc7_watch'"
$DENY = @('Remove-Item', 'Invoke-WebRequest', 'Invoke-RestMethod', 'Send-MailMessage', 'schtasks', 'Register-ScheduledTask',
  'Start-ScheduledTask', 'shutdown', 'Restart-Service', 'Stop-Service', 'Set-Service', 'New-Service')
$ALERT_RX = "ALERT conc-\d+ gate ${TAG}: TL (\d+) crash (\d+)"

function Get-Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() }
function Get-Inner($e) { while ($e.InnerException) { $e = $e.InnerException }; $e }
function Read-HarnessText([string]$p) {
  $fs = [IO.File]::Open($p, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]'ReadWrite,Delete')
  try { $sr = [IO.StreamReader]::new($fs); $sr.ReadToEnd() } finally { $fs.Dispose() }
}
function New-Check([string]$Name, $Ok, [string]$Detail) { [ordered]@{ check = $Name; ok = $Ok; detail = $Detail } }
function Join-Arg([string[]]$a) { ($a | ForEach-Object { if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ } }) -join ' ' }

# ---------------------------------------------------------------- extract mode (function targets)
if ($PSCmdlet.ParameterSetName -eq 'extract') {
  $src = (Resolve-Path -LiteralPath $ExtractFrom).Path; $tok = $null; $errs = $null
  $ast = [Management.Automation.Language.Parser]::ParseFile($src, [ref]$tok, [ref]$errs)
  if ($errs.Count) { throw "parse errors in ${src}: $($errs[0])" }
  $sbld = [Text.StringBuilder]::new()
  [void]$sbld.Append("# S35 function extract: verbatim FunctionDefinitionAst text from $(Split-Path -Leaf $src) sha256 $(Get-Sha $src)`n")
  foreach ($nm in $Names) {
    $hit = @($ast.FindAll({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $nm }, $true))
    if ($hit.Count -ne 1) { throw "function $nm found $($hit.Count) times in $src (need exactly 1)" }
    [void]$sbld.Append("# ${nm}: source lines $($hit[0].Extent.StartLineNumber)-$($hit[0].Extent.EndLineNumber)`n")
    [void]$sbld.Append(($hit[0].Extent.Text -replace "`r`n", "`n") + "`n")
  }
  [IO.File]::WriteAllText($OutFile, $sbld.ToString(), [Text.UTF8Encoding]::new($false))
  "extracted $($Names -join ', ') from $src -> $OutFile sha256 $(Get-Sha $OutFile)"
  exit 0
}

# ---------------------------------------------------------------- fixture builders
function Open-GateLog([string]$Path, [string]$Mode) {
  if ($Mode -eq 'exclusive') { return [IO.FileStream]::new($Path, [IO.FileMode]::Create, [IO.FileAccess]::Write, [IO.FileShare]::Read) }
  if ($Mode -eq 'driver') { return [IO.FileStream]::new($Path, [IO.FileMode]::Create, [IO.FileAccess]::ReadWrite, [IO.FileShare]'Read,Write') }
  throw "unknown writer mode $Mode"
}
function Add-GateLines($Fs, [string[]]$Lines, [switch]$Bom) {
  if ($Bom) { $Fs.Write([byte[]](0xEF, 0xBB, 0xBF), 0, 3) }
  $b = [Text.Encoding]::UTF8.GetBytes((-join ($Lines | ForEach-Object { "$_`r`n" })))
  $Fs.Write($b, 0, $b.Length); $Fs.Flush($true)
}
# fastchess 1.8.x stdout style: 'Started game N of 1500 (W vs B)' / 'Finished game N (W vs B): RESULT {reason}'
function Get-GameLines([int]$From, [int]$To, [int[]]$TL = @(), [switch]$Header, [switch]$FinishedFirst) {
  $o = [Collections.Generic.List[string]]::new()
  if ($Header) { $o.Add('Indexing opening suite...') }
  for ($g = $From; $g -le $To; $g++) {
    if ($g % 2) { $w = $CAND; $k = $BASE } else { $w = $BASE; $k = $CAND }
    if (-not ($FinishedFirst -and $g -eq $From)) { $o.Add("Started game $g of 1500 ($w vs $k)") }
    $r = if ($TL -contains $g) { if ($g % 2) { '0-1 {White loses on time}' } else { '1-0 {Black loses on time}' } } else { '1/2-1/2 {Draw by 3-fold repetition}' }
    $o.Add("Finished game $g ($w vs $k): $r")
  }
  $o.ToArray()   # emitted line by line: callers use @(...) or pass it to a [string[]] parameter
}
function Get-LockState([string]$p) {
  $ra = 'readable'; try { [void][IO.File]::ReadAllText($p) } catch { $ra = 'THROWS ' + (Get-Inner $_.Exception).GetType().Name }
  $sh = 'readable'; try { [void](Read-HarnessText $p) } catch { $sh = 'THROWS ' + (Get-Inner $_.Exception).GetType().Name }
  [ordered]@{ readalltext = $ra; shared_readwrite = $sh; enforced = ($ra -eq 'THROWS IOException' -and $sh -eq 'readable') }
}
function New-Sandbox([string]$Root, [int]$C) {
  if ($Root -match $LIVE_RX) { throw "refusing sandbox $Root" }
  foreach ($d in 'qa', 'autorestart', 'gates', "gates\$TAG", 'hw', 'ctl') { New-Item -ItemType Directory -Force -Path (Join-Path $Root $d) | Out-Null }
  $bom = [Text.UTF8Encoding]::new($true)   # the PC writes these JSON files with a BOM (PowerShell 5.1 Set-Content utf8)
  [IO.File]::WriteAllText((Join-Path $Root 'autorestart\forge_queue_state.json'), ([ordered]@{ current = [ordered]@{ tag = $TAG; pid = 999998 } } | ConvertTo-Json -Depth 4), $bom)
  [IO.File]::WriteAllText((Join-Path $Root "gates\$TAG\RUN_INFO.json"), ([ordered]@{ tag = $TAG; concurrency = $C } | ConvertTo-Json), $bom)
  $man = [ordered]@{ gates = @([ordered]@{ gate = 'S35a'; tag = $TAG; concurrency = $C }, [ordered]@{ gate = 'S35b'; tag = $NEXT; concurrency = $C }) }
  [IO.File]::WriteAllText((Join-Path $Root 'autorestart\forge_gates.json'), ($man | ConvertTo-Json -Depth 6), $bom)
  $csv = Join-Path $Root 'hw\gpu_sensors.csv'
  Set-Content -LiteralPath $csv -Value 'Date,Time,GPU Hot Spot Temperature,GPU Memory Junction Temperature,CPU (Tctl/Tdie)' -Encoding ascii
  (Get-Item -LiteralPath $csv).LastWriteTime = [datetime]'2000-01-01'   # stale -> the watcher's Temps() returns $null
}
function Get-PatchedText([string]$Text, [string]$Sb, [string]$Mutex) {
  foreach ($k in $SUBS.Keys) {
    $n = [regex]::Matches($Text, [regex]::Escape($k)).Count
    if ($n -ne 1) { throw "patch refused: live literal $k occurs $n times (need exactly 1); watcher layout differs" }
    $Text = $Text.Replace($k, "'" + (Join-Path $Sb $SUBS[$k]) + "'")
  }
  $n = [regex]::Matches($Text, [regex]::Escape($MUTEX_LIT)).Count
  if ($n -ne 1) { throw "patch refused: mutex literal occurs $n times (need exactly 1)" }
  $Text = $Text.Replace($MUTEX_LIT, "'Local\$Mutex'")
  if ($Text -match $LIVE_RX) { throw "patch refused: '$($Matches[0])' still present after patching" }
  foreach ($t in $DENY) { if ($Text -match ('(?i)\b' + [regex]::Escape($t) + '\b')) { throw "patch refused: unstubbed side-effect command '$t' in the copy" } }
  $Text
}

# ---------------------------------------------------------------- observers (e2e child watcher or in-process function probe)
function New-Observer($T, [string]$Sb, [int]$Ticks) {
  $o = @{ T = $T; sb = $Sb; ticks = $Ticks; n = 0; proc = $null; logSeen = 0; ctl = (Join-Path $Sb 'ctl'); patched = $null; module = $null }
  if ($T.kind -eq 'e2e') {
    $txt = Get-PatchedText -Text ([IO.File]::ReadAllText($T.fullpath)) -Sb $Sb -Mutex ('forge_s35_' + [guid]::NewGuid().ToString('N'))
    $o.patched = Join-Path $Sb 'watcher_patched.ps1'; [IO.File]::WriteAllText($o.patched, $txt, [Text.UTF8Encoding]::new($true))
  } else {
    $o.module = New-Module -Name ('s35probe_' + [guid]::NewGuid().ToString('N')) -ArgumentList (Join-Path $Sb 'gates'), ([IO.File]::ReadAllText($T.fullpath)) -ScriptBlock {
      param($GatesRoot, $FunctionText)
      $D = $GatesRoot
      . ([scriptblock]::Create($FunctionText))
      function Invoke-S35Probe([string]$Tag) { , @(Log-TLCrash $Tag) }
      Export-ModuleMember -Function Invoke-S35Probe
    }
  }
  $o
}
function Invoke-ObsTick($o) {
  $o.n++
  if ($o.T.kind -eq 'function') {
    $r = & $o.module { param($t) Invoke-S35Probe $t } $TAG
    return [ordered]@{ tick = $o.n; tl = [int]$r[0]; cr = [int]$r[1] }
  }
  if ($o.n -eq 1) {
    $al = @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', $RUNNER, '-Ctl', $o.ctl, '-Patched', $o.patched, '-Ticks', "$($o.ticks)", '-Timeout', "$TickTimeoutSec")
    $o.proc = Start-Process -FilePath $PWSH -ArgumentList (Join-Arg $al) -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $o.sb 'child.out') -RedirectStandardError (Join-Path $o.sb 'child.err')
    $null = $o.proc.Handle
    try { $o.proc.PriorityClass = 'BelowNormal' } catch {}
  } else { Set-Content -LiteralPath (Join-Path $o.ctl ('tick{0}.go' -f $o.n)) -Value 'go' -Encoding ascii }
  $done = Join-Path $o.ctl ('tick{0}.done' -f $o.n); $sw = [Diagnostics.Stopwatch]::StartNew(); $why = $null
  while (-not (Test-Path -LiteralPath $done)) {
    if ($o.proc.HasExited) { $why = "child exited (code $($o.proc.ExitCode)) before tick $($o.n) finished"; break }
    if ($sw.Elapsed.TotalSeconds -gt $TickTimeoutSec) { $why = "timeout after $TickTimeoutSec s waiting for tick $($o.n)"; break }
    Start-Sleep -Milliseconds 100
  }
  $lines = @(); $log = Join-Path $o.sb 'qa\conc7_watch.log'
  if (Test-Path -LiteralPath $log) {
    $all = @((Read-HarnessText $log) -split "`r?`n" | Where-Object { $_ -ne '' })
    $lines = @($all | Select-Object -Skip $o.logSeen); $o.logSeen = $all.Count
  }
  [ordered]@{ tick = $o.n; lines = $lines; problem = $why }
}
function Stop-Observer($o) {
  $r = [ordered]@{ exit = $null; stderr = ''; stub_calls = @(); refused = $false; sandbox_manifest_next_conc = $null }
  if ($o.T.kind -ne 'e2e' -or -not $o.proc) { return $r }
  if (-not $o.proc.WaitForExit($TickTimeoutSec * 1000)) { try { $o.proc.Kill($true) } catch {}; $r.exit = 'killed after timeout (own child only)' } else { $r.exit = $o.proc.ExitCode }
  $err = Join-Path $o.sb 'child.err'; if (Test-Path -LiteralPath $err) { $r.stderr = "$(Get-Content -LiteralPath $err -Raw)".Trim() }
  $sc = Join-Path $o.ctl 'stub_calls.log'; if (Test-Path -LiteralPath $sc) { $r.stub_calls = @(Get-Content -LiteralPath $sc | Select-Object -Unique) }
  $r.refused = Test-Path -LiteralPath (Join-Path $o.ctl 'REFUSED.txt')
  try { $m = [IO.File]::ReadAllText((Join-Path $o.sb 'autorestart\forge_gates.json')) | ConvertFrom-Json; $r.sandbox_manifest_next_conc = @($m.gates | Where-Object { $_.tag -eq $NEXT })[0].concurrency } catch {}
  $r
}

# ---------------------------------------------------------------- checks
function Get-Alerts($lines) { , @($lines | ForEach-Object { $m = [regex]::Match($_, $ALERT_RX); if ($m.Success) { [int]$m.Groups[1].Value } }) }
function Get-HB($lines) {
  foreach ($l in $lines) { $m = [regex]::Match($l, 'HB .*? games (\d+) TL (\d+) crash (\d+)'); if ($m.Success) { return @{ games = [int]$m.Groups[1].Value; tl = [int]$m.Groups[2].Value; cr = [int]$m.Groups[3].Value } } }
  $null
}
function Get-TickChecks($T, $Obs, [string]$Pfx, [int]$ExpectTL, [int]$ExpectGames = -1, [switch]$ExpectNoAlert) {
  $c = @()
  if ($T.kind -eq 'function') {
    $c += New-Check "$Pfx Log-TLCrash returns TL $ExpectTL crash 0" ($Obs.tl -eq $ExpectTL -and $Obs.cr -eq 0) "got TL $($Obs.tl) crash $($Obs.cr)"
    return , $c
  }
  $c += New-Check "$Pfx tick $($Obs.tick) completed" ($null -eq $Obs.problem) "$($Obs.problem)"
  $le = @($Obs.lines | Where-Object { $_ -match 'loop error' })
  $c += New-Check "$Pfx no 'loop error'" ($le.Count -eq 0) ($le -join ' || ')
  $al = Get-Alerts $Obs.lines
  if ($ExpectNoAlert) { $c += New-Check "$Pfx no ALERT" ($al.Count -eq 0) "alerts this tick: $(if ($al.Count) { $al -join ',' } else { 'none' })" }
  else { $c += New-Check "$Pfx ALERT TL $ExpectTL" ($al -contains $ExpectTL) "alerts this tick: $(if ($al.Count) { 'TL ' + ($al -join ',') } else { 'none' })" }
  if ($ExpectGames -ge 0) {
    $hb = Get-HB $Obs.lines
    if ($null -eq $hb) { $c += New-Check "$Pfx HB games $ExpectGames" 'n/a' 'no HB line with a games field (this watcher version prints none)' }
    else { $c += New-Check "$Pfx HB games $ExpectGames TL $ExpectTL" ($hb.games -eq $ExpectGames -and $hb.tl -eq $ExpectTL) "HB games $($hb.games) TL $($hb.tl) crash $($hb.cr)" }
  }
  , $c
}

function Get-ExitCheck($T, $End, [string]$Pfx) {
  if ($T.kind -ne 'e2e') { return , @() }
  , @(New-Check "$Pfx child ran every tick and exited 0, nothing refused, no stderr" ($End.exit -eq 0 -and -not $End.refused -and -not $End.stderr) "exit $($End.exit); refused $($End.refused); stderr '$($End.stderr)'")
}

# ---------------------------------------------------------------- scenarios
function Invoke-S1($T, [string]$Root) {
  $checks = @(); $ev = [ordered]@{}
  foreach ($mode in 'exclusive', 'driver') {
    $sb = Join-Path $Root "S1_$mode"; New-Sandbox $sb $T.conc
    $log = Join-Path $sb "gates\$TAG\$TAG.log"; $fs = Open-GateLog $log $mode
    try {
      Add-GateLines $fs (@(Get-GameLines 1 6 -Header) + "Started game 7 of 1500 ($CAND vs $BASE)")
      Add-GateLines $fs @("Finished game 7 ($CAND vs $BASE): 0-1 {White loses on time}")   # the synthetic TL, appended under the lock
      $lk = Get-LockState $log
      $o = New-Observer $T $sb 1; $t1 = Invoke-ObsTick $o; $end = Stop-Observer $o
    } finally { $fs.Dispose() }
    $checks += New-Check "S1[$mode] writer lock enforced (ReadAllText throws, FileShare.ReadWrite reads)" $lk.enforced "ReadAllText: $($lk.readalltext); FileShare.ReadWrite: $($lk.shared_readwrite)"
    $checks += Get-TickChecks $T $t1 "S1[$mode]" -ExpectTL 1 -ExpectGames 7
    $checks += Get-ExitCheck $T $end "S1[$mode]"
    $ev["S1_$mode"] = [ordered]@{ lock = $lk; tick1 = $t1; child = $end }
  }
  @{ checks = $checks; evidence = $ev }
}
function Invoke-S2($T, [string]$Root) {
  $sb = Join-Path $Root 'S2'; New-Sandbox $sb $T.conc
  $dir = Join-Path $sb "gates\$TAG"; $log = Join-Path $dir "$TAG.log"; $fs = Open-GateLog $log 'exclusive'
  try {
    Add-GateLines $fs (Get-GameLines 1 5 -TL 5 -Header)
    $o = New-Observer $T $sb 3; $t1 = Invoke-ObsTick $o
    # rotation as forge_queue.ps1 Archive-Partial does it: fastchess has exited, the log is moved to partial_<ts>\, a new run creates a fresh log
    $fs.Dispose(); $pd = Join-Path $dir 'partial_20261027_000000'; New-Item -ItemType Directory -Force -Path $pd | Out-Null
    Move-Item -LiteralPath $log -Destination (Join-Path $pd "$TAG.log")
    $fs = Open-GateLog $log 'exclusive'; Add-GateLines $fs (Get-GameLines 1 3 -TL 3 -Header)
    $t2 = Invoke-ObsTick $o
    # truncation in place while the writer keeps the handle (a CREATE_ALWAYS restart without a move)
    $fs.SetLength(0); $fs.Position = 0; Add-GateLines $fs (Get-GameLines 1 2 -TL 2 -Header)
    $t3 = Invoke-ObsTick $o
    $end = Stop-Observer $o
  } finally { $fs.Dispose() }
  $checks = @()
  $checks += Get-TickChecks $T $t1 'S2 tick1 (before rotation)' -ExpectTL 1 -ExpectGames 5
  $checks += Get-TickChecks $T $t2 'S2 tick2 (after move-away rotation, 1 new TL)' -ExpectTL 1
  $checks += Get-TickChecks $T $t3 'S2 tick3 (after in-place truncation, 1 new TL)' -ExpectTL 1
  $checks += Get-ExitCheck $T $end 'S2'
  @{ checks = $checks; evidence = [ordered]@{ tick1 = $t1; tick2 = $t2; tick3 = $t3; child = $end } }
}
function Invoke-S3($T, [string]$Root) {
  $sb = Join-Path $Root 'S3'; New-Sandbox $sb $T.conc
  $log = Join-Path $sb "gates\$TAG\$TAG.log"; $fs = $null
  try {
    $o = New-Observer $T $sb 2; $t1 = Invoke-ObsTick $o          # gate started (RUN_INFO present) but no log file yet
    $fs = Open-GateLog $log 'exclusive'; Add-GateLines $fs (Get-GameLines 1 3 -TL 3 -Header)
    $t2 = Invoke-ObsTick $o
    $end = Stop-Observer $o
  } finally { if ($fs) { $fs.Dispose() } }
  $checks = @()
  $checks += Get-TickChecks $T $t1 'S3 tick1 (log missing)' -ExpectTL 0 -ExpectGames 0 -ExpectNoAlert
  $checks += Get-TickChecks $T $t2 'S3 tick2 (log appears, locked, 1 TL)' -ExpectTL 1
  $checks += Get-ExitCheck $T $end 'S3'
  @{ checks = $checks; evidence = [ordered]@{ tick1 = $t1; tick2 = $t2; child = $end } }
}
function Invoke-S4($T, [string]$Root) {
  $sb = Join-Path $Root 'S4'; New-Sandbox $sb $T.conc
  $log = Join-Path $sb "gates\$TAG\$TAG.log"; $fs = Open-GateLog $log 'exclusive'
  try {
    Add-GateLines $fs (Get-GameLines 1 4 -TL 1 -FinishedFirst) -Bom
    $rd = [IO.File]::Open($log, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
    try { $hd = [byte[]]::new(20); $null = $rd.Read($hd, 0, 20) } finally { $rd.Dispose() }
    $fixOk = ($hd[0] -eq 0xEF -and $hd[1] -eq 0xBB -and $hd[2] -eq 0xBF -and [Text.Encoding]::ASCII.GetString($hd, 3, 15) -eq 'Finished game 1')
    $o = New-Observer $T $sb 1; $t1 = Invoke-ObsTick $o; $end = Stop-Observer $o
  } finally { $fs.Dispose() }
  $checks = @(New-Check 'S4 fixture: EF BB BF then "Finished game 1" (TL) as the first line' $fixOk ([BitConverter]::ToString($hd, 0, 6)))
  $checks += Get-TickChecks $T $t1 'S4 (BOM)' -ExpectTL 1 -ExpectGames 4
  $checks += Get-ExitCheck $T $end 'S4'
  @{ checks = $checks; evidence = [ordered]@{ tick1 = $t1; child = $end } }
}

# ---------------------------------------------------------------- target + suite runners
function Invoke-Target($T, [string]$RunRoot) {
  $root = Join-Path $RunRoot $T.label; New-Item -ItemType Directory -Force -Path $root | Out-Null
  $res = [ordered]@{ label = $T.label; kind = $T.kind; role = $T.role; path = $T.path; sha256 = $T.sha256; conc = $T.conc; scenarios = [ordered]@{} }
  foreach ($s in $Scenarios) {
    try { $r = & "Invoke-$s" $T $root } catch { $r = @{ checks = @(New-Check "$s harness error" $false "$_ @ $($_.InvocationInfo.ScriptLineNumber)"); evidence = @{} } }
    $nf = @($r.checks | Where-Object { $_.ok -is [bool] -and -not $_.ok }).Count
    $res.scenarios[$s] = [ordered]@{ result = $(if ($nf) { 'FAIL' } else { 'PASS' }); checks = $r.checks; evidence = $r.evidence }
  }
  $res.score = '{0}/{1}' -f @($res.scenarios.Values | Where-Object { $_.result -eq 'PASS' }).Count, $res.scenarios.Count
  $res
}

$WorkDir = [IO.Path]::GetFullPath($WorkDir)
if ($WorkDir -match $LIVE_RX -or $WorkDir.Contains("'")) { throw "refusing WorkDir '$WorkDir' (live root or quote character)" }
if (-not (Test-Path -LiteralPath $RUNNER)) { throw "child runner missing: $RUNNER" }
$runId = 'run_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + $PID
$runRoot = Join-Path $WorkDir $runId; New-Item -ItemType Directory -Force -Path $runRoot | Out-Null

$tlist = @()
if ($PSCmdlet.ParameterSetName -eq 'suite') {
  $tp = (Resolve-Path -LiteralPath $Targets).Path; $base = Split-Path -Parent $tp
  $spec = Get-Content -LiteralPath $tp -Raw | ConvertFrom-Json
  foreach ($t in $spec.targets) {
    $full = Join-Path $base $t.path; $sha = Get-Sha $full
    if ($sha -ne $t.sha256) { throw "target $($t.label): file sha256 $sha != targets.json $($t.sha256) (refusing to test an unknown copy)" }
    $exp = [ordered]@{}; foreach ($p in $t.expect.PSObject.Properties) { $exp[$p.Name] = $p.Value }
    $tlist += @{ label = $t.label; kind = $t.kind; role = $t.role; path = $t.path; fullpath = $full; sha256 = $sha; conc = $(if ($t.PSObject.Properties['conc']) { [int]$t.conc } else { 8 }); expect = $exp }
  }
} else {
  $full = (Resolve-Path -LiteralPath $Watcher).Path
  $tlist += @{ label = $Label; kind = $Kind; role = 'single'; path = $full; fullpath = $full; sha256 = (Get-Sha $full); conc = $Conc; expect = $null }
}

$envInfo = [ordered]@{ harness = $HARNESS; harness_sha256 = (Get-Sha $PSCommandPath); runner_sha256 = (Get-Sha $RUNNER); pwsh = $PSVersionTable.PSVersion.ToString()
  os = [Environment]::OSVersion.VersionString; is_windows = $IsWindows; workdir = $runRoot; started = (Get-Date -Format 's') }
Write-Host "S35 harness: pwsh $($envInfo.pwsh) on $($envInfo.os); sandbox root $runRoot"
$results = @(); $allMatch = $true
foreach ($T in $tlist) {
  $r = Invoke-Target $T $runRoot
  if ($T.expect) {
    $mm = @(); foreach ($s in $Scenarios) { if ($T.expect.Contains($s) -and $T.expect[$s] -ne $r.scenarios[$s].result) { $mm += "$s expected $($T.expect[$s]) got $($r.scenarios[$s].result)" } }
    $r.expected = $T.expect; $r.matches_expected = ($mm.Count -eq 0); $r.mismatches = $mm; if ($mm.Count) { $allMatch = $false }
  }
  $results += $r
  $row = ($Scenarios | ForEach-Object { "$_ $($r.scenarios[$_].result)" }) -join '  '
  Write-Host ('{0,-46} {1,-8} {2,-9} {3}  score {4}{5}' -f $r.label, $r.kind, $r.role, $row, $r.score, $(if ($T.expect) { if ($r.matches_expected) { '  [matches expected]' } else { '  [MISMATCH: ' + ($r.mismatches -join '; ') + ']' } } else { '' }))
  foreach ($s in $Scenarios) { foreach ($c in $r.scenarios[$s].checks) { if ($c.ok -is [bool] -and -not $c.ok) { Write-Host "    FAIL $($c.check) :: $($c.detail)" } } }
}
$negs = @($results | Where-Object { $_.role -eq 'negative' })
$negOk = ($negs.Count -gt 0 -and -not @($negs | Where-Object { $_.scenarios['S1'].result -ne 'FAIL' }).Count)
$summary = [ordered]@{ env = $envInfo; scenarios = $Scenarios; targets = $results
  negative_fixtures_fail_S1 = $(if ($negs.Count) { $negOk } else { 'n/a' }); all_targets_match_expected = $(if ($PSCmdlet.ParameterSetName -eq 'suite') { $allMatch } else { 'n/a' }) }
if ($OutJson) { [IO.File]::WriteAllText($OutJson, ($summary | ConvertTo-Json -Depth 14), [Text.UTF8Encoding]::new($false)) }
if ($PSCmdlet.ParameterSetName -eq 'suite') {
  Write-Host "negative fixtures fail S1 (locked log) as required: $($summary.negative_fixtures_fail_S1)"
  Write-Host "all targets match targets.json expectations: $allMatch"
  exit $(if ($allMatch -and $negOk) { 0 } else { 1 })
}
$single = $results[0]
Write-Host "single target $($single.label): $($single.score)"
exit $(if ($single.score -eq ('{0}/{0}' -f $Scenarios.Count)) { 0 } else { 1 })
