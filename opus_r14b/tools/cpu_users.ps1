# cpu_users.ps1 - Opus R14-B: who uses the given CPUs right now (read-only). Samples TotalProcessorTime of every process
# whose affinity includes -Mask over -Seconds and prints those that used more than 0.1 CPU-seconds, busiest first, with
# affinity and priority class. Write its output next to every speed number measured on a shared PC.
# usage: powershell -NoProfile -File cpu_users.ps1 [-Mask 0xC] [-Seconds 5]
param([string]$Mask = '0xC', [int]$Seconds = 5)
$m = [Convert]::ToInt64($Mask.Replace('0x', ''), 16)
$t0 = @{}
foreach ($p in Get-Process) {
    try { if (([int64]$p.ProcessorAffinity -band $m) -ne 0) { $t0[$p.Id] = $p.TotalProcessorTime.TotalSeconds } } catch {}
}
Start-Sleep -Seconds $Seconds
$rows = foreach ($p in Get-Process) {
    try {
        if ($t0.ContainsKey($p.Id)) {
            $d = $p.TotalProcessorTime.TotalSeconds - $t0[$p.Id]
            if ($d -gt 0.1) {
                [pscustomobject]@{ Name = $p.ProcessName; Id = $p.Id; Cpu = $d / $Seconds;
                                   Affinity = ('0x{0:X}' -f [int64]$p.ProcessorAffinity); Priority = $p.PriorityClass }
            }
        }
    } catch {}
}
'{0} processes using CPUs in {1} over {2} s (CPU = cores busy on average):' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Mask, $Seconds
$rows | Sort-Object Cpu -Descending | ForEach-Object {
    '  {0,-26} pid {1,-6} {2,5:N2} cores  affinity {3,-7} {4}' -f $_.Name, $_.Id, $_.Cpu, $_.Affinity, $_.Priority
}
