# Optional review-tool authentication

Current check, 2026-11-03: the user installed CodeRabbit CLI 0.9.2 and SonarQube
CLI 1.11.0. CodeRabbit's signed canonical Windows executable is authenticated;
its usage command reports ten included reviews and usage billing inactive.
Two scoped broad CodeRabbit attempts were rejected by the300-file cap (686/750
files counted despite intended code/test filters); neither returned findings or
a clean result. Authentication is working; this is a scope limit. Temporary local
configuration was restored to its original absent state. SonarQube
authentication remains unavailable. The earlier PATH/setup notes below are
retained for troubleshooting; installing again is unnecessary.

CodeRabbit executable: `C:/Users/Administrator/AppData/Local/Programs/coderabbit/coderabbit.exe`.
SonarQube executable: `C:/Users/Administrator/AppData/Local/sonarqube-cli/bin/sonar.exe`.
A separate PGN-only milestone review later completed at 08:57 UTC with zero
findings, one unidentified unreviewed file and warning exit1. Authentication
needs no repair; this is partial review coverage. Its receipts are in
evidence/extension5h/coderabbit_pgn_milestone. The independent reviewer and Forge
evidence checker remain in use. Attempt
receipts: evidence/extension5h/coderabbit_limits; analysis: DEV_TOOLS_RESEARCH.md.

Use PowerShell under the same Windows account as Codex. Official installers:

```powershell
irm https://cli.coderabbit.ai/install.ps1 | iex
irm https://raw.githubusercontent.com/SonarSource/sonarqube-cli/refs/heads/master/user-scripts/install.ps1 | iex
```

Close and reopen PowerShell, then authenticate interactively:

```powershell
coderabbit --version
coderabbit auth login
coderabbit auth status

sonar --version
sonar auth login --org YOUR_ORGANIZATION_KEY
sonar auth status
```

Complete each browser login. CodeRabbit EU accounts use
`coderabbit auth login --region eu`. SonarQube Cloud US uses
`sonar auth login --org YOUR_ORGANIZATION_KEY --server https://sonarqube.us`; a self-hosted SonarQube server
uses its own URL with `--server`. Select the organization that owns the project.
Keep tokens in the local login flow and OS credential storage, never in chat,
committed files or review logs. No installation or login was performed by this job.

Sources: [CodeRabbit Windows setup](https://docs.coderabbit.ai/cli/windows),
[CodeRabbit login/regions](https://docs.coderabbit.ai/cli),
[SonarQube CLI authentication](https://github.com/SonarSource/sonarqube-cli#step-2-authenticate).
The installed SonarQube integration skill also requires a running container
runtime and a restarted agent session for MCP tools; CLI login alone does not
configure that bridge. Verify CLI version/help before invoking a later review.

Fresh check at 06:30 UTC: the absolute Sonar path runs, but `auth status` returns
`No saved connection`. Its installed `auth login --help` confirms `--org` and
`--server`. If `sonar` is still not recognized in your terminal, this bypasses
PATH lookup (replace the placeholder with your Cloud organization key):

```powershell
& "$env:LOCALAPPDATA\sonarqube-cli\bin\sonar.exe" auth login --org YOUR_ORGANIZATION_KEY
& "$env:LOCALAPPDATA\sonarqube-cli\bin\sonar.exe" auth status
```

The default is Cloud EU. Add `--server https://sonarqube.us` to the login command
only for a Cloud US account. This job has not run login or accessed credentials.

At 03:26 UTC the user had installed SonarQube CLI 1.11.0, verified by executing
`%LOCALAPPDATA%/sonarqube-cli/bin/sonar.exe --version`. This agent's older PATH
still did not include the directory. In an existing PowerShell window use:

```powershell
$env:PATH = "$env:LOCALAPPDATA\sonarqube-cli\bin;$env:PATH"
sonar auth login --org YOUR_ORGANIZATION_KEY
sonar auth status
```

Replace the organization placeholder with the actual Cloud organization key.
Alternatively invoke `& "$env:LOCALAPPDATA\sonarqube-cli\bin\sonar.exe"` with
the same arguments. Login remains interactive and was not performed by this job.
The [official Windows installer](https://raw.githubusercontent.com/SonarSource/sonarqube-cli/refs/heads/master/user-scripts/install.ps1)
documents this PATH refresh for terminals opened before installation.
