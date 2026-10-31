# pc_gate.ps1 - R13 load/disk gate (read-only). Prints free disk C:/D:/F:, total + per-CPU load, free RAM.
# Exit 0 = OK to start a heavy step, 1 = wait. Thresholds per the R13 job rules:
#   C: >= 30 GB + NeedGB, D:/F: >= 50 GB only checked for the drive we write to (-Drive), total CPU <= MaxCpu, free RAM >= MinRamGB.
# usage: powershell -NoProfile -File pc_gate.ps1 [-Drive C] [-NeedGB 1] [-MaxCpu 85] [-MinRamGB 6] [-Quiet]
param([string]$Drive = 'C', [double]$NeedGB = 1, [double]$MaxCpu = 85, [double]$MinRamGB = 6, [switch]$Quiet)
$floor = @{ 'C' = 30; 'D' = 50; 'F' = 50 }
$free = @{}
foreach ($d in 'C', 'D', 'F') { $free[$d] = [math]::Round((Get-PSDrive $d).Free / 1GB, 1) }
$ram = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1)
$s = (Get-Counter '\Processor(*)\% Processor Time' -SampleInterval 2 -MaxSamples 1).CounterSamples
$total = [math]::Round(($s | Where-Object InstanceName -eq '_total').CookedValue, 0)
$per = ($s | Where-Object InstanceName -ne '_total' | Sort-Object { [int]$_.InstanceName } | ForEach-Object { '{0}:{1:0}' -f $_.InstanceName, $_.CookedValue }) -join ' '
$need = $floor[$Drive] + $NeedGB
$ok = ($free[$Drive] -ge $need) -and ($free['C'] -ge 30) -and ($total -le $MaxCpu) -and ($ram -ge $MinRamGB)
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
if (-not $Quiet) {
  "$stamp free C:$($free['C']) D:$($free['D']) F:$($free['F']) GB | write drive $Drive needs >= $need | cpu $total% (max $MaxCpu) | ram $ram GB (min $MinRamGB) | ok=$ok"
  "per-cpu $per"
}
if ($ok) { exit 0 } else { exit 1 }
