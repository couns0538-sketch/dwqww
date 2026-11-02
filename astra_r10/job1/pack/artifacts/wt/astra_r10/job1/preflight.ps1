$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
[Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity=[IntPtr]12
$env:TEMP='D:\a10\tmp'; $env:TMP=$env:TEMP; $env:PYTHONDONTWRITEBYTECODE='1'
$env:PSModulePath='C:\Windows\System32\WindowsPowerShell\v1.0\Modules;C:\Program Files\WindowsPowerShell\Modules'
Import-Module Microsoft.PowerShell.Utility -ErrorAction Stop
Import-Module Microsoft.PowerShell.Archive -ErrorAction Stop
Get-Command Get-FileHash,Compress-Archive | Select-Object Name,Source
& D:\a10\python\python.exe -B D:\a10\wt\astra_r10\job1\run_build.py --help
if($LASTEXITCODE){throw 'Python/dependencies failed'}
