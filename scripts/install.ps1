param(
  [switch]$Force,
  [ValidateSet("Copilot", "Claude", "Both")]
  [string]$Runtime = "Both",
  [string]$Destination
)

$ErrorActionPreference = "Stop"
$source = Resolve-Path (Join-Path $PSScriptRoot "..")

if (-not (Test-Path (Join-Path $source "SKILL.md"))) {
  throw "Skill file not found: $source"
}

function Initialize-Destination([string]$Path) {
  if (Test-Path $Path) {
    if (-not $Force) {
      throw "Destination already exists: $Path. Re-run with -Force to overwrite."
    }
    Remove-Item $Path -Recurse -Force
  }
  New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Install-ExperimentLoop([string]$Path) {
  Initialize-Destination $Path
  foreach ($item in @(
    "SKILL.md", "CONTEXT.md", "references", "templates", "examples", "docs",
    "scripts", "README.md", "INSTALL.md", "PACKAGE_MANIFEST.json",
    "requirements.txt"
  )) {
    $itemPath = Join-Path $source $item
    if (Test-Path $itemPath) {
      Copy-Item $itemPath (Join-Path $Path $item) -Recurse -Force
    }
  }
  Write-Host "Installed experiment-loop skill to $Path"
  Write-Host "Install dependencies: python `"$Path\scripts\install_dependencies.py`""
}

function Install-ExperimentSetup([string]$Path) {
  Initialize-Destination $Path
  New-Item -ItemType Directory -Force -Path (Join-Path $Path "references") | Out-Null
  New-Item -ItemType Directory -Force -Path (Join-Path $Path "scripts") | Out-Null
  New-Item -ItemType Directory -Force -Path (Join-Path $Path "templates") | Out-Null
  Copy-Item (Join-Path $source "skills\experiment-setup\SKILL.md") (Join-Path $Path "SKILL.md")
  Copy-Item (Join-Path $source "references\experiment-brief-schema-v1.0.json") (Join-Path $Path "references")
  Copy-Item (Join-Path $source "references\experiment-approval-schema-v1.0.json") (Join-Path $Path "references")
  Copy-Item (Join-Path $source "scripts\validate_experiment_setup.py") (Join-Path $Path "scripts")
  Copy-Item (Join-Path $source "scripts\prepare_scratch.py") (Join-Path $Path "scripts")
  Copy-Item (Join-Path $source "templates\experiment-brief-template.json") (Join-Path $Path "templates")
  Copy-Item (Join-Path $source "templates\experiment-approval-template.json") (Join-Path $Path "templates")
  Write-Host "Installed experiment-setup skill to $Path"
}

$roots = @()
if ($Destination) {
  $roots += [pscustomobject]@{
    Loop = $Destination
    Setup = Join-Path (Split-Path $Destination -Parent) "experiment-setup"
  }
} else {
  if ($Runtime -in @("Copilot", "Both")) {
    $roots += [pscustomobject]@{
      Loop = "$HOME\.copilot\skills\experiment-loop"
      Setup = "$HOME\.copilot\skills\experiment-setup"
    }
  }
  if ($Runtime -in @("Claude", "Both")) {
    $roots += [pscustomobject]@{
      Loop = "$HOME\.claude\skills\experiment-loop"
      Setup = "$HOME\.claude\skills\experiment-setup"
    }
  }
}

foreach ($root in $roots) {
  Install-ExperimentLoop $root.Loop
  Install-ExperimentSetup $root.Setup
}
