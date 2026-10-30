# R7 J4: where does the PC's CPU go? Samples every process's CPU time twice, $Seconds apart (read only).
# usage: powershell -NoProfile -File cpu_survey.ps1 [-Seconds 20]
# Groups: gate engines + fastchess (children of fastchess.exe), the NNUE trainer (python under the supervisor),
# self-play, Grok Bot, everything else. Prints cores' worth of CPU (1.00 = one logical CPU busy) per group.
param([int]$Seconds = 20)
$n = [Environment]::ProcessorCount
function Snap { $h = @{}; Get-Process | ForEach-Object { try { $h[$_.Id] = @{ Name = $_.ProcessName; Cpu = $_.TotalProcessorTime.TotalSeconds } } catch {} }; $h }
$procs = Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId, Name, CommandLine
$byId = @{}; foreach ($p in $procs) { $byId[[int]$p.ProcessId] = $p }
function Group-Of([int]$id) {
    $p = $byId[$id]; if (-not $p) { return "other" }
    $chain = @(); $cur = $p; $guard = 0
    while ($cur -and $guard -lt 12) { $chain += $cur; $cur = $byId[[int]$cur.ParentProcessId]; $guard++ }
    # Ancestry first (the trainer's own command line names forge_selfplay_*.pos data files, so a
    # self-play pattern must not be tried before the supervisor ancestry check).
    foreach ($c in $chain) {
        $cl = [string]$c.CommandLine
        if ($c.Name -eq "fastchess.exe") { return "gate (fastchess + engines)" }
        if ($cl -match "nnue_supervisor") { return "NNUE trainer" }
    }
    foreach ($c in $chain) {
        $cl = [string]$c.CommandLine
        if ($cl -match "forge_selfplay\.py|selfplay_guard\.py") { return "self-play" }
        if ($c.Name -match "Grok Bot") { return "Grok Bot" }
        if ($c.Name -match "claude") { return "Claude (this job)" }
    }
    return "other"
}
$a = Snap; $t0 = Get-Date
Start-Sleep -Seconds $Seconds
$b = Snap; $dt = ((Get-Date) - $t0).TotalSeconds
$groups = @{}; $fast = 0.0
foreach ($id in $b.Keys) {
    if (-not $a.ContainsKey($id)) { continue }
    $d = $b[$id].Cpu - $a[$id].Cpu
    if ($d -le 0) { continue }
    $g = Group-Of $id
    if ($b[$id].Name -eq "fastchess") { $fast += $d }
    if (-not $groups.ContainsKey($g)) { $groups[$g] = 0.0 }
    $groups[$g] += $d
}
$total = ($groups.Values | Measure-Object -Sum).Sum
"interval {0:N1} s, {1} logical CPUs, busy {2:N2} CPUs ({3:P0})" -f $dt, $n, ($total / $dt), ($total / $dt / $n)
foreach ($k in ($groups.Keys | Sort-Object { -$groups[$_] })) { "  {0,-28} {1,6:N2} CPUs" -f $k, ($groups[$k] / $dt) }
"  (fastchess.exe itself: {0:N3} CPUs)" -f ($fast / $dt)
