param([Parameter(Mandatory=$true)][ValidateSet('red01','green01','green02')][string]$Phase)
$ErrorActionPreference='Stop'
$sample=Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor | Where-Object Name -in @('0','1','3') | Sort-Object PercentProcessorTime | Select-Object -First 1
$cpu=[int]$sample.Name
if (-not $sample -or [int]$sample.PercentProcessorTime -gt 70) { throw 'Spare CPU admission refused' }
if ((Get-PSDrive D).Free -lt (50GB+64MB) -or (Get-PSDrive C).Free -lt 30GB) { throw 'Disk floor' }
$used=(Get-ChildItem -LiteralPath D:\a14 -Recurse -File -Force | Measure-Object -Property Length -Sum).Sum
if ([long]$used+64MB -ge 5000000000L) { throw 'Owned storage cap' }
$current=[Diagnostics.Process]::GetCurrentProcess()
$current.PriorityClass='Idle'
$current.ProcessorAffinity=[IntPtr](1 -shl $cpu)
Remove-Item Env:ASTRA_R14_CPU,Env:ASTRA_R13_CPU -ErrorAction SilentlyContinue
Write-Output "Admitted CPU $cpu at $($sample.PercentProcessorTime)% busy; Idle and one CPU."
$tests=@('D:\a14\tests\test_r14_qc_fixes.py','D:\a14\tests\test_p5_audit.py')
if ($Phase -eq 'green02') { $tests += 'D:\a14\tests\test_qc_core.py' }
& D:\a14\tools\Run-R14QuickTests.ps1 -Name ('qc-empty-runs-'+$Phase) -Tests $tests
