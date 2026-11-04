# bullet_cpu0.ps1 [-Cpu 0] - checks of the GPU-trained v2 nets (2026-11-04): exit 1 while a process named
# forge-v2-bullet* runs on an affinity mask that includes the CPU (or whose mask cannot be read: fail closed), else 0.
# Also lists every process whose affinity mask includes the CPU but is not the full 16-CPU mask (who shares the CPU),
# so that the load next to a speed figure is on record. Read-only.
param([int]$Cpu = 0)
$bit = [int64]1 -shl $Cpu
$full = [int64]0xFFFF
$hits = 0
$procs = Get-CimInstance Win32_Process
foreach ($w in $procs) {
    $aff = -1; $cls = 'n/a'
    try { $p = Get-Process -Id $w.ProcessId -ErrorAction Stop; $aff = [int64]$p.ProcessorAffinity; $cls = "$($p.PriorityClass)" } catch {}
    $isBullet = $w.Name -like 'forge-v2-bullet*'
    $onCpu = ($aff -eq -1) -or (($aff -band $bit) -ne 0)
    if ($isBullet) {
        '{0} pid {1} aff 0x{2:X} class {3} on_cpu{4}={5}' -f $w.Name, $w.ProcessId, $aff, $cls, $Cpu, $onCpu
        if ($onCpu) { $hits += 1 }
    } elseif ($aff -ne -1 -and $aff -ne $full -and (($aff -band $bit) -ne 0)) {
        'sharer: {0} pid {1} aff 0x{2:X} class {3}' -f $w.Name, $w.ProcessId, $aff, $cls
    }
}
if ($hits -gt 0) { "forge-v2-bullet on CPU $Cpu : $hits process(es) - wait"; exit 1 }
"no forge-v2-bullet on CPU $Cpu"
exit 0
