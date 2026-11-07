# scout_gate.ps1 - pre-flight gate for the OSS scout job (C:\opus_5h\oss_scout). Read-only on the PC.
# Run before every download, extract, build and heavy run:
#   pwsh -NoProfile -File C:\opus_5h\oss_scout\tools\scout_gate.ps1 -Step "<what>" [-PlannedGB 1.2] [-NoCpuSample]
# Checks (exit 3 when one fails, 0 when all pass):
#   - C:, D:, F: free >= MinFreeGB (30, the brief's floor). E: is a 3 GB volume and is only reported.
#   - C: free minus PlannedGB >= MinFreeGB.
#   - scout folder size + PlannedGB <= MaxScoutGB (10; the brief's hard cap is 15).
#   - free RAM >= MinRamGB (8).
# Snapshot (never a fail reason, written for the record): busy % of CPUs 0-3 over 2 s, GPU compute % per process,
# dedicated VRAM in use, number of gate engines / fastchess / self-play processes.
# Every call appends one JSON line to C:\opus_5h\oss_scout\logs\scout_gate.jsonl and prints a one-line summary.
param(
    [string]$Step = "check",
    [double]$PlannedGB = 0,
    [double]$MinFreeGB = 30,
    [double]$MaxScoutGB = 10,
    [double]$MinRamGB = 8,
    [double]$VramTotalGB = 20,
    [switch]$NoCpuSample
)
$ErrorActionPreference = 'Stop'
$inv = [Globalization.CultureInfo]::InvariantCulture
function F1([double]$x) { return [Math]::Round($x, 1).ToString($inv) }

$scout = 'C:\opus_5h\oss_scout'
$fails = @()
$disk = [ordered]@{}
foreach ($dl in 'C', 'D', 'E', 'F') {
    $d = Get-PSDrive -Name $dl -PSProvider FileSystem -ErrorAction SilentlyContinue
    if (-not $d) { continue }
    $free = $d.Free / 1GB
    $disk[$dl] = [Math]::Round($free, 1)
    if ($dl -ne 'E' -and $free -lt $MinFreeGB) { $fails += "${dl}: free $(F1 $free) GB < $MinFreeGB" }
}
if ($disk.Contains('C') -and ($disk['C'] - $PlannedGB) -lt $MinFreeGB) {
    $fails += "C: free after planned $(F1 $PlannedGB) GB would be $(F1 ($disk['C'] - $PlannedGB)) GB < $MinFreeGB"
}
$scoutBytes = (Get-ChildItem $scout -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
if (-not $scoutBytes) { $scoutBytes = 0 }
$scoutGB = $scoutBytes / 1GB
if (($scoutGB + $PlannedGB) -gt $MaxScoutGB) {
    $fails += "scout folder $(F1 $scoutGB) GB + planned $(F1 $PlannedGB) GB > $MaxScoutGB GB"
}
$os = Get-CimInstance Win32_OperatingSystem
$ramFree = $os.FreePhysicalMemory / 1MB
if ($ramFree -lt $MinRamGB) { $fails += "free RAM $(F1 $ramFree) GB < $MinRamGB" }

# Snapshot
$cpu = [ordered]@{}
if (-not $NoCpuSample) {
    try {
        $paths = 0..3 | ForEach-Object { "\Processor($_)\% Processor Time" }
        $s = Get-Counter -Counter $paths -SampleInterval 2 -MaxSamples 1
        foreach ($c in $s.CounterSamples) {
            if ($c.Path -match 'processor\((\d+)\)') { $cpu["cpu$($Matches[1])"] = [Math]::Round($c.CookedValue, 0) }
        }
    } catch { $cpu['error'] = "$_" }
}
$gpu = @()
try {
    $g = Get-Counter '\GPU Engine(*engtype_Compute*)\Utilization Percentage' -ErrorAction Stop
    $byPid = @{}
    foreach ($c in $g.CounterSamples) {
        if ($c.InstanceName -match 'pid_(\d+)_') {
            $p = [int]$Matches[1]
            if (-not $byPid.ContainsKey($p)) { $byPid[$p] = 0.0 }
            $byPid[$p] += $c.CookedValue
        }
    }
    foreach ($k in $byPid.Keys) {
        if ($byPid[$k] -ge 1) {
            $name = (Get-Process -Id $k -ErrorAction SilentlyContinue).ProcessName
            $gpu += "$name/$k=$([Math]::Round($byPid[$k], 0))%"
        }
    }
} catch { $gpu += "error: $_" }
$vramUsed = $null
try {
    $m = Get-Counter '\GPU Adapter Memory(*)\Dedicated Usage' -ErrorAction Stop
    $vramUsed = ($m.CounterSamples | Measure-Object CookedValue -Maximum).Maximum / 1GB
} catch { }
$procs = Get-Process -ErrorAction SilentlyContinue
$gateEngines = ($procs | Where-Object { $_.ProcessName -like 'forge_ltopgo*' }).Count
$fastchess = ($procs | Where-Object { $_.ProcessName -eq 'fastchess' }).Count
$selfplay = ($procs | Where-Object { $_.ProcessName -like 'forge_selfplay*' }).Count

$now = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$rec = [ordered]@{
    time = $now; step = $Step; ok = ($fails.Count -eq 0); fails = $fails
    disk_free_gb = $disk; scout_gb = [Math]::Round($scoutGB, 2); planned_gb = $PlannedGB
    ram_free_gb = [Math]::Round($ramFree, 1); cpu_busy = $cpu; gpu_compute = $gpu
    vram_used_gb = $(if ($null -ne $vramUsed) { [Math]::Round($vramUsed, 1) } else { $null })
    vram_free_gb = $(if ($null -ne $vramUsed) { [Math]::Round($VramTotalGB - $vramUsed, 1) } else { $null })
    gate_engines = $gateEngines; fastchess = $fastchess; selfplay = $selfplay
}
$json = $rec | ConvertTo-Json -Compress -Depth 4
$logDir = Join-Path $scout 'logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
Add-Content -Path (Join-Path $logDir 'scout_gate.jsonl') -Value $json -Encoding utf8
$cpuTxt = ($cpu.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ' '
$diskTxt = ($disk.GetEnumerator() | ForEach-Object { "$($_.Key):$($_.Value.ToString($inv))" }) -join ' '
$status = if ($fails.Count -eq 0) { 'OK' } else { 'FAIL' }
Write-Output ("[{0}] {1} step='{2}' disk {3} scout={4}GB ram={5}GB {6} gpu[{7}] vram_used={8}GB gates={9} fastchess={10} selfplay={11}" -f `
    $now, $status, $Step, $diskTxt, (F1 $scoutGB), (F1 $ramFree), $cpuTxt, ($gpu -join ','), `
    $(if ($null -ne $vramUsed) { F1 $vramUsed } else { '?' }), $gateEngines, $fastchess, $selfplay)
foreach ($f in $fails) { Write-Output "  FAIL: $f" }
if ($fails.Count -gt 0) { exit 3 }
exit 0
