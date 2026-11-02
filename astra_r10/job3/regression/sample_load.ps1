#requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$Log)
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]4
if($Log -notlike 'D:\a10\wt\astra_r10\job3\regression\*'){throw 'Owned log required'}
$samples=Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor
$row=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');cpu2=[int](($samples|Where-Object Name -eq '2').PercentProcessorTime);cpu3=[int](($samples|Where-Object Name -eq '3').PercentProcessorTime);host=[int](($samples|Where-Object Name -eq '_Total').PercentProcessorTime)}
$line=$row|ConvertTo-Json -Compress
Add-Content -LiteralPath $Log -Value $line -Encoding UTF8
$line
