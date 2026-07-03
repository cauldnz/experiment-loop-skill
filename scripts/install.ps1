param(
  [switch]$Force,
  [string]$Destination = "$HOME\.copilot\skills\experiment-loop"
)

$ErrorActionPreference = "Stop"
$source = Resolve-Path (Join-Path $PSScriptRoot "..")

if (-not (Test-Path (Join-Path $source "SKILL.md"))) {
  throw "Skill file not found: $source"
}

if (Test-Path $Destination) {
  if (-not $Force) {
    throw "Destination already exists: $Destination. Re-run with -Force to overwrite."
  }
  Remove-Item $Destination -Recurse -Force
}

New-Item -ItemType Directory -Force -Path (Split-Path $Destination -Parent) | Out-Null
New-Item -ItemType Directory -Force -Path $Destination | Out-Null
foreach ($item in @("SKILL.md", "references", "templates", "examples", "README.md", "INSTALL.md", "PACKAGE_MANIFEST.json")) {
  $path = Join-Path $source $item
  if (Test-Path $path) {
    Copy-Item $path (Join-Path $Destination $item) -Recurse -Force
  }
}
Write-Host "Installed experiment-loop skill to $Destination"
