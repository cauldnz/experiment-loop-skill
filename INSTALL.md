# Install the Experiment Skills

The installers add both `experiment-loop` and its guided `experiment-setup`
companion for GitHub Copilot CLI and Claude Code.

## Windows

From this repository root:

```powershell
.\scripts\install.ps1
```

To overwrite an existing copy:

```powershell
.\scripts\install.ps1 -Force
```

Install for only one runtime:

```powershell
.\scripts\install.ps1 -Runtime Copilot
.\scripts\install.ps1 -Runtime Claude
```

## macOS/Linux

From this repository root:

```bash
bash scripts/install.sh
```

To overwrite an existing copy:

```bash
bash scripts/install.sh --force
```

Install for only one runtime:

```bash
bash scripts/install.sh --runtime copilot
bash scripts/install.sh --runtime claude
```

## Manual install

Copy the main skill and companion skill to the corresponding runtime folder:

```text
~/.copilot/skills/experiment-loop
~/.copilot/skills/experiment-setup
~/.claude/skills/experiment-loop
~/.claude/skills/experiment-setup
```

Install required dependencies without persisting an npm registry:

```text
python ~/.copilot/skills/experiment-loop/scripts/install_dependencies.py
```

On a managed device, inject the approved npm upstream at runtime or rely on the
machine-managed npm configuration:

```text
set EXPERIMENT_LOOP_NPM_REGISTRY=<approved-upstream>
python ~/.copilot/skills/experiment-loop/scripts/install_dependencies.py
```

PowerShell users can set `$env:EXPERIMENT_LOOP_NPM_REGISTRY` instead. The value
is passed to npm only for the child process; the script never writes `.npmrc`,
the lockfile, or repository configuration.

After install, start a new Copilot CLI or Claude Code session, or reload skills
if the runtime supports skill reload.
