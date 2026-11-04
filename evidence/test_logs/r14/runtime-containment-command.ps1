param([Parameter(Mandatory=$true)][ValidateSet('red01','red02','green01')][string]$Phase,[ValidateSet(-1,2,3)][int]$Cpu=-1)
$ErrorActionPreference='Stop'
$samples=Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor
if ($Cpu -eq -1) {
    $sample=$samples | Where-Object Name -in @('2','3') | Sort-Object PercentProcessorTime | Select-Object -First 1
    $Cpu=[int]$sample.Name
} else {
    $sample=$samples | Where-Object Name -eq ([string]$Cpu)
}
if (-not $sample -or [int]$sample.PercentProcessorTime -gt 70) { throw "CPU $Cpu admission refused" }
if ((Get-PSDrive D).Free -lt (50GB+64MB) -or (Get-PSDrive C).Free -lt 30GB) { throw 'Disk floor' }
$used=(Get-ChildItem -LiteralPath D:\a14 -Recurse -File -Force | Measure-Object -Property Length -Sum).Sum
if ([long]$used+64MB -ge 5000000000L) { throw 'Owned storage cap' }
$current=[Diagnostics.Process]::GetCurrentProcess()
$current.PriorityClass='Idle'
$current.ProcessorAffinity=[IntPtr](1 -shl $Cpu)
Remove-Item Env:ASTRA_R14_CPU,Env:ASTRA_R13_CPU -ErrorAction SilentlyContinue
Write-Output "Admitted CPU $Cpu at $($sample.PercentProcessorTime)% busy; Idle and one CPU."
& D:\a14\tools\Run-R14QuickTests.ps1 -Name ('runtime-containment-'+$Phase) -Tests @('D:\a14\tests\test_r14_overlap.py','D:\a14\tests\test_r14_scan.py')
