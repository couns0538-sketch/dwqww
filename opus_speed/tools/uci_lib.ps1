# uci_lib.ps1 - shared helpers for the speed-job tools (PowerShell 5.1; dot-source it: . "$PSScriptRoot\uci_lib.ps1").
# Placement (affinity + priority class, checked, fail closed), disk gates, hashing, LF files, and a small UCI driver
# that waits for real engine output (no sleeps). Engines inherit this process's affinity and class from their first
# instruction, so callers place themselves first (Set-OspdPlacement) and only then start engines.
# Lock facts used as defaults: pins of exe FD3A5190 (net on = defaults; net off = UseNNUE false).

[System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::InvariantCulture   # dot decimals in every number we write
$script:OspdLockExe = 'C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_v23.exe'
$script:OspdLockSha = 'FD3A51903E73DC1FA20263F1DCC7A4EEC506592E9F25E50B8F8739CA36873072'
$script:OspdLockSrc = 'F:\ospd\src\lock'
# string keys: an [ordered] dictionary indexed with an int reads by POSITION, not by key (bug found 09:10)
$script:OspdDepths = @(11, 13, 16, 20, 22)
$script:OspdPinsOn = @{ d11 = 312866; d13 = 862329; d16 = 3024920; d20 = 12389307; d22 = 34048354 }
$script:OspdPinsOff = @{ d11 = 375354; d13 = 907205; d16 = 2448617; d20 = 13573040; d22 = 24506465 }
$script:OspdPerftPins = [ordered]@{ startpos = 4865609; kiwipete = 193690690 }
$script:OspdKiwi = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'
$script:OspdScratch = 'F:\ospd'
$script:OspdAllowedMask = 0xF   # CPUs 0-3 only (job rule)

function Get-OspdNow { Get-Date -Format 'yyyy-MM-dd HH:mm:ss' }

function Set-OspdPlacement([long]$Mask, [string]$Priority) {
  # Pin THIS process (children inherit) to $Mask at $Priority; verify both; throw on any failure (fail closed).
  if ($Mask -le 0 -or ($Mask -band (-bnot $script:OspdAllowedMask)) -ne 0) { throw "mask 0x$('{0:X}' -f $Mask) is outside CPUs 0-3" }
  if ($Priority -notin @('Idle', 'BelowNormal')) { throw "priority $Priority not allowed (Idle or BelowNormal only)" }
  $me = [System.Diagnostics.Process]::GetCurrentProcess()
  $me.PriorityClass = $Priority
  $me.ProcessorAffinity = [IntPtr]$Mask
  $me.Refresh()
  if ([long]$me.ProcessorAffinity -ne $Mask) { throw "affinity not applied (got 0x$('{0:X}' -f [long]$me.ProcessorAffinity))" }
  if ("$($me.PriorityClass)" -ne $Priority) { throw "priority not applied (got $($me.PriorityClass))" }
}

function Get-OspdDirBytes([string]$Path) {
  if (-not (Test-Path $Path)) { return 0 }
  $s = (Get-ChildItem -Recurse -Force -File $Path -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
  if ($null -eq $s) { return 0 } else { return [long]$s }
}

function Assert-OspdDisk([double]$PlannedGB = 0.1) {
  # Job rule: C: >= 30 GB, F: >= 50 GB free (after the planned write), F:\ospd <= 8 GB; nothing is ever written to D:.
  $c = (Get-PSDrive C).Free / 1GB; $f = (Get-PSDrive F).Free / 1GB
  if ($c -lt 30) { throw ("C: has {0:N1} GB free (< 30)" -f $c) }
  if (($f - $PlannedGB) -lt 50) { throw ("F: would drop to {0:N1} GB free (< 50)" -f ($f - $PlannedGB)) }
  $used = (Get-OspdDirBytes $script:OspdScratch) / 1GB
  if (($used + $PlannedGB) -gt 8) { throw ("F:\ospd would hold {0:N2} GB (> 8)" -f ($used + $PlannedGB)) }
  return ("disk ok: C {0:N1} GB, F {1:N1} GB free, F:\ospd {2:N2} GB" -f $c, $f, $used)
}

function Get-OspdSha256([string]$Path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLower() }
function Get-OspdMd5([string]$Path) { (Get-FileHash -Algorithm MD5 -LiteralPath $Path).Hash.ToLower() }

function Write-OspdLf([string]$Path, [string[]]$Lines) {
  [System.IO.File]::WriteAllText($Path, (($Lines -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding($false)))
}
function Add-OspdLf([string]$Path, [string]$Line) {
  [System.IO.File]::AppendAllText($Path, ($Line + "`n"), (New-Object System.Text.UTF8Encoding($false)))
}

# ---------------- UCI driver ----------------
function Start-OspdEngine([string]$Exe, [string]$LogPath = '', [long]$Mask = 0) {
  # New engine process; inherits this process's placement. $Mask (optional) narrows the child further (subset only).
  if (-not (Test-Path -LiteralPath $Exe)) { throw "engine not found: $Exe" }
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $Exe
  $psi.WorkingDirectory = Split-Path -Parent $Exe
  $psi.UseShellExecute = $false
  $psi.RedirectStandardInput = $true
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $false
  $psi.CreateNoWindow = $true
  $p = [System.Diagnostics.Process]::Start($psi)
  if ($Mask -ne 0) {
    $parent = [long][System.Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity
    if (($Mask -band (-bnot $parent)) -ne 0) { $p.StandardInput.Close(); throw "child mask must be a subset of 0x$('{0:X}' -f $parent)" }
    $p.ProcessorAffinity = [IntPtr]$Mask
  }
  $p.StandardInput.AutoFlush = $true
  $p.StandardInput.NewLine = "`n"
  $eng = [pscustomobject]@{ Proc = $p; In = $p.StandardInput; Out = $p.StandardOutput; Log = $LogPath; Pending = $null }
  if ($LogPath) { Add-OspdLf $LogPath "# $(Get-OspdNow) start $Exe pid $($p.Id)" }
  return $eng
}

function Send-OspdUci($Eng, [string]$Line) {
  $Eng.In.WriteLine($Line)
  if ($Eng.Log) { Add-OspdLf $Eng.Log "> $Line" }
}

function Read-OspdLine($Eng, [int]$TimeoutSec) {
  # One output line or $null at EOF; throws on timeout (the task stays pending and is reused by the next read).
  if ($null -eq $Eng.Pending) { $Eng.Pending = $Eng.Out.ReadLineAsync() }
  if (-not $Eng.Pending.Wait([int]([Math]::Min([long]$TimeoutSec * 1000, [int]::MaxValue)))) { throw "engine timeout after $TimeoutSec s" }
  $line = $Eng.Pending.Result; $Eng.Pending = $null
  return $line
}

function Wait-OspdUci($Eng, [string]$Pattern, [int]$TimeoutSec = 600, [switch]$Collect) {
  # Read lines until one matches $Pattern; returns @{ Match = <System.Text.RegularExpressions.Match>; Lines = [..] }.
  $rx = New-Object System.Text.RegularExpressions.Regex($Pattern)
  $lines = New-Object System.Collections.Generic.List[string]
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while ($true) {
    $left = [int][Math]::Max(1, ($deadline - (Get-Date)).TotalSeconds)
    $line = Read-OspdLine $Eng $left
    if ($null -eq $line) { throw "engine exited before /$Pattern/" }
    if ($Eng.Log) { Add-OspdLf $Eng.Log $line }
    if ($Collect) { $lines.Add($line) }
    $m = $rx.Match($line)
    if ($m.Success) { return @{ Match = $m; Lines = $lines } }
  }
}

function Stop-OspdEngine($Eng) {
  # quit, then close stdin (EOF also ends the UCI loop); never kills (job rule). Returns $true if it exited.
  try { Send-OspdUci $Eng 'quit' } catch {}
  try { $Eng.In.Close() } catch {}
  $ok = $Eng.Proc.WaitForExit(30000)
  if ($Eng.Log) { Add-OspdLf $Eng.Log "# $(Get-OspdNow) exit ok=$ok" }
  return $ok
}

function Initialize-OspdEngine($Eng, [string[]]$Options) {
  # uci handshake; returns the uci lines; applies 'Name=Value' options; isready.
  Send-OspdUci $Eng 'uci'
  $r = Wait-OspdUci $Eng '^uciok' 60 -Collect
  foreach ($kv in $Options) {
    if (-not $kv) { continue }
    $i = $kv.IndexOf('='); if ($i -lt 1) { throw "bad option '$kv' (want Name=Value)" }
    Send-OspdUci $Eng ("setoption name {0} value {1}" -f $kv.Substring(0, $i), $kv.Substring($i + 1))
  }
  Send-OspdUci $Eng 'isready'
  $null = Wait-OspdUci $Eng '^readyok' 120
  return $r.Lines
}

function Invoke-OspdBench($Eng, [int]$Depth, [int]$TimeoutSec = 1800) {
  Send-OspdUci $Eng "bench $Depth"
  $m = (Wait-OspdUci $Eng ("bench depth {0} nodes (\d+) time (\d+) nps (\d+)" -f $Depth) $TimeoutSec).Match
  return [pscustomobject]@{ Depth = $Depth; Nodes = [long]$m.Groups[1].Value; Ms = [long]$m.Groups[2].Value; Nps = [long]$m.Groups[3].Value }
}

function Invoke-OspdPerft($Eng, [string]$Position, [int]$Depth = 5) {
  if ($Position -eq 'startpos') { Send-OspdUci $Eng 'position startpos' } else { Send-OspdUci $Eng ("position fen " + $Position) }
  Send-OspdUci $Eng "go perft $Depth"
  $m = (Wait-OspdUci $Eng '^nodes (\d+)' 1800).Match
  return [long]$m.Groups[1].Value
}

function Invoke-OspdSearch($Eng, [string]$Fen, [string]$GoArgs, [switch]$NewGame) {
  # One search; returns depth / score / nodes of the last 'info depth' line and the bestmove.
  if ($NewGame) { Send-OspdUci $Eng 'ucinewgame'; Send-OspdUci $Eng 'isready'; $null = Wait-OspdUci $Eng '^readyok' 120 }
  Send-OspdUci $Eng ("position fen " + $Fen)
  Send-OspdUci $Eng ("go " + $GoArgs)
  $r = Wait-OspdUci $Eng '^bestmove (\S+)' 3600 -Collect
  $last = $null
  foreach ($l in $r.Lines) { if ($l.StartsWith('info depth ')) { $last = $l } }
  $d = ''; $s = ''; $n = ''
  if ($last) {
    $mm = [regex]::Match($last, '^info depth (\d+) .*? score (cp -?\d+|mate -?\d+)(?: (?:lowerbound|upperbound))? nodes (\d+)')
    if ($mm.Success) { $d = $mm.Groups[1].Value; $s = $mm.Groups[2].Value; $n = $mm.Groups[3].Value }
  }
  return [pscustomobject]@{ Depth = $d; Score = $s; Nodes = $n; Best = $r.Match.Groups[1].Value }
}

function Get-OspdUciOptionLine([string[]]$UciLines, [string]$Name) {
  foreach ($l in $UciLines) { if ($l -match ('^option name ' + [regex]::Escape($Name) + ' type ')) { return $l } }
  return ''
}
