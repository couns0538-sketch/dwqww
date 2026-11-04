# Reviewer probe: does [Environment]::SetEnvironmentVariable($name,$null,'Process') (the R14-finish replacement for
# Remove-Item Env:) delete a process variable under pwsh, or leave it as an empty string?
$ErrorActionPreference = 'Stop'
$env:R14REVIEW_A = 'set'
[Environment]::SetEnvironmentVariable('R14REVIEW_A', $null, 'Process')
"after SetEnvironmentVariable(null): env:A=[{0}] isnull={1} Test-Path={2} dotnet=[{3}] dotnet_isnull={4}" -f $env:R14REVIEW_A, ($null -eq $env:R14REVIEW_A), (Test-Path Env:R14REVIEW_A), [Environment]::GetEnvironmentVariable('R14REVIEW_A','Process'), ($null -eq [Environment]::GetEnvironmentVariable('R14REVIEW_A','Process'))
$env:R14REVIEW_B = 'set'
Remove-Item -LiteralPath 'Env:R14REVIEW_B'
"after Remove-Item Env: env:B=[{0}] isnull={1} Test-Path={2}" -f $env:R14REVIEW_B, ($null -eq $env:R14REVIEW_B), (Test-Path Env:R14REVIEW_B)
$env:R14REVIEW_C = 'set'
[Environment]::SetEnvironmentVariable('R14REVIEW_C', [NullString]::Value, 'Process')
"after SetEnvironmentVariable(NullString): env:C=[{0}] isnull={1} Test-Path={2}" -f $env:R14REVIEW_C, ($null -eq $env:R14REVIEW_C), (Test-Path Env:R14REVIEW_C)
"pwsh version: $($PSVersionTable.PSVersion)"
