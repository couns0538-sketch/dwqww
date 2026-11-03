# Optional review-tool authentication

Checked 2026-11-03: `coderabbit`, `sonar`, Docker, Podman and Nerdctl were absent
from this Windows session's PATH. No CodeRabbit or SonarQube review is claimed.
The existing independent reviewer and Forge evidence checker remain in use.

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
sonar auth login
sonar auth status
```

Complete each browser login. CodeRabbit EU accounts use
`coderabbit auth login --region eu`. SonarQube Cloud US uses
`sonar auth login --server https://sonarqube.us`; a self-hosted SonarQube server
uses its own URL with `--server`. Select the organization that owns the project.
Keep tokens in the local login flow and OS credential storage, never in chat,
committed files or review logs. No installation or login was performed by this job.

Sources: [CodeRabbit Windows setup](https://docs.coderabbit.ai/cli/windows),
[CodeRabbit login/regions](https://docs.coderabbit.ai/cli),
[SonarQube CLI authentication](https://github.com/SonarSource/sonarqube-cli#step-2-authenticate).
The installed SonarQube integration skill also requires a running container
runtime and a restarted agent session for MCP tools; CLI login alone does not
configure that bridge. Verify CLI version/help before invoking a later review.
