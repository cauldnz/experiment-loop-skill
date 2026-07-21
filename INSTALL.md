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

Both installed skills include `scripts/prepare_scratch.py`. Before an unattended
Windows run, create prompt-safe experiment-local scratch space with:

```powershell
python <installed-skill>\scripts\prepare_scratch.py `
  --generated-root .experiments\<experiment-id>\generated
```

If a tool requires an existing session scratch directory, use
`--session-scratch <path>` and pass agents only the printed long-form path.

The installed `experiment-loop` skill also includes the shared Viewer renderer
and standard adapter template. Generated adapters support both one-shot builds
and dependency-free local `--watch` mode without additional installation. Both
skills include the canonical human-feedback intake/disposition schemas and
templates; the loop skill includes `scripts/validate_human_feedback.py`.
The installed setup schema supports legacy v1.0 briefs and emits v1.1 briefs with
mandatory human-use applicability for physical and digital systems, prior-art
review, and explicit network-search policy. The shared Viewer adapter renders
selected qualitative use-friction evidence without presenting it as an objective
gate.
