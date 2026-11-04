# pc_gate.ps1 - R13 load/disk gate (read-only). Prints free disk C:/D:/F:, total + per-CPU load, free RAM.
# Exit 0 = OK to start a heavy step, 1 = wait (also when the CPU load cannot be read: the gate fails, never "0 %"),
# 2 = bad arguments. Thresholds (R14-B: C: >= 50 GB since Couns 14:40 on
# 2026-11-02; R13 had 30): C: >= 50 GB (+ NeedGB when writing there), D:/F: >= 50 GB + NeedGB only for the drive we
# write to (-Drive), total CPU <= MaxCpu, free RAM >= MinRamGB.
# usage: powershell -NoProfile -File pc_gate.ps1 [-Drive C] [-NeedGB 1] [-MaxCpu 85] [-MinRamGB 6] [-Quiet]
param([string]$Drive = 'C', [double]$NeedGB = 1, [double]$MaxCpu = 85, [double]$MinRamGB = 6, [string]$Cpus = '',
      [double]$MaxMyCpu = 100, [switch]$Quiet)
# -Cpus '2,3' -MaxMyCpu 60: also require the average load of the CPUs my work is pinned to to be <= MaxMyCpu
# (R13: the gate holds 4-15 and the Idle trainer 0-3; total CPU alone stops builds when only 0-1 are busy).
$floor = @{ 'C' = 50; 'D' = 50; 'F' = 50 }
# final bug hunt (04:15): an unknown drive or CPU list used to give exit 1 ("wait") forever, and a CPU number that
# does not exist gave no samples, an average of 0 and so "ok" whatever the load
if (-not $floor.ContainsKey($Drive.ToUpper())) { [Console]::Error.WriteLine("pc_gate: -Drive must be C, D or F, not '$Drive'"); exit 2 }
$Drive = $Drive.ToUpper()
$free = @{}
foreach ($d in 'C', 'D', 'F') { $free[$d] = [math]::Round((Get-PSDrive $d).Free / 1GB, 1) }
$ram = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1)
# CR fix 2026-11-03: CPU counters that cannot be read FAIL the gate (exit 1 with the reason on stderr, also with -Quiet).
# Before, a failed or empty Get-Counter gave no samples, a total of 0 % and ok=True.
$why = ''
try {
  $s = @((Get-Counter '\Processor(*)\% Processor Time' -SampleInterval 2 -MaxSamples 1 -ErrorAction Stop).CounterSamples | Where-Object { $_ })
} catch { $s = @(); $why = $_.Exception.Message }
$tot = @($s | Where-Object { $_.InstanceName -eq '_total' })
$cpu = @($s | Where-Object { $_.InstanceName -ne '_total' })
if (-not $why) {
  if ($tot.Count -ne 1) { $why = "$($tot.Count) _total samples among $($s.Count)" }
  elseif ($null -eq $tot[0].CookedValue) { $why = 'the _total sample has no value' }
  elseif ($cpu.Count -eq 0) { $why = 'no per-CPU samples' }
}
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
if ($why) {
  [Console]::Error.WriteLine("pc_gate: CPU load could not be read ($why): the gate FAILS (a missing load is never taken as 0 %)")
  if (-not $Quiet) { "$stamp free C:$($free['C']) D:$($free['D']) F:$($free['F']) GB | cpu unknown | ram $ram GB | ok=False" }
  exit 1
}
$total = [math]::Round($tot[0].CookedValue, 0)
$per = ($cpu | Sort-Object { [int]$_.InstanceName } | ForEach-Object { '{0}:{1:0}' -f $_.InstanceName, $_.CookedValue }) -join ' '
$need = $floor[$Drive] + $NeedGB
$my = 0
if ($Cpus) {
  $ids = @($Cpus.Split(',') | ForEach-Object { $_.Trim() })
  $have = @($cpu | ForEach-Object { $_.InstanceName })
  $bad = @($ids | Where-Object { $have -notcontains $_ })
  if ($bad.Count) { [Console]::Error.WriteLine("pc_gate: -Cpus names no CPU of this PC: $($bad -join ', ') (CPUs 0-$($have.Count - 1))"); exit 2 }
  $my = [math]::Round((($cpu | Where-Object { $ids -contains $_.InstanceName } | Measure-Object CookedValue -Average).Average), 0)
}
$ok = ($free[$Drive] -ge $need) -and ($free['C'] -ge $floor['C']) -and ($total -le $MaxCpu) -and ($ram -ge $MinRamGB) -and ($my -le $MaxMyCpu)
if (-not $Quiet) {
  "$stamp free C:$($free['C']) D:$($free['D']) F:$($free['F']) GB | write drive $Drive needs >= $need | cpu $total% (max $MaxCpu) | ram $ram GB (min $MinRamGB) | my cpus [$Cpus] $my% (max $MaxMyCpu) | ok=$ok"
  "per-cpu $per"
}
if ($ok) { exit 0 } else { exit 1 }
