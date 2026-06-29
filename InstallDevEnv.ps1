Write-Host ''
$dateTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "=[ START $dateTime ]============================[ InstallDevEnv.ps1 ]=" -ForegroundColor Blue
Write-Host "Executing $PSCommandPath..." -ForegroundColor Yellow

try {
    $pythonVersion = [version](python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
} catch {
    Write-Error "Unable to determine the active Python version from PATH."
    exit 1
}

$minimumSupportedPythonVersion = [version]"3.10"
$maximumSupportedPythonVersion = [version]"3.15"

if (($pythonVersion -lt $minimumSupportedPythonVersion) -or ($pythonVersion -ge $maximumSupportedPythonVersion)) {
    Write-Error "Unsupported Python version $pythonVersion. This repo supports Python >= 3.10 and < 3.15, including all Python 3.14 releases."
    exit 1
}

(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
poetry init
& "$env:PROJECT_DIR\SetupDotEnv.ps1"
if (Test-Path -Path "$env:PROJECT_DIR\SetupGitHubAccess.ps1") {
    & "$env:PROJECT_DIR\SetupGitHubAccess"
} else {
    Write-Host "No $env:PROJECT_DIR\SetupGitHubAccess.ps1 file"
}
if (Test-Path -Path "$env:PROJECT_DIR\SetupPrivateRepoAccess.ps1") {
    & "$env:PROJECT_DIR\SetupPrivateRepoAccess.ps1"
}
if (Test-Path -Path "$env:PROJECT_DIR\pyproject.toml") {
    Write-Host 'Poetry Install...' -ForegroundColor Yellow
    poetry lock --no-cache --regenerate # Locks the project dependencies
    poetry install --with dev --no-cache # Installs the project dependencies
    poetry update --with dev --no-cache  # Update the dependencies as according to the pyproject.toml file
    poetry sync --with dev --no-cache # Update the project's environment according to the lockfile.
}
Write-Host 'Pre-Commit Install...' -ForegroundColor Yellow
pre-commit install
Write-Host 'Pre-Commit Auto Update...' -ForegroundColor Yellow
pre-commit autoupdate
if (Test-Path -Path "$env:PROJECT_DIR\SetUpDocker.ps1") {
    & "$env:PROJECT_DIR\SetUpDocker.ps1"
}
Write-Host '-[ END InstallDevEnv.ps1 ]------------------------------------------------------' -ForegroundColor Cyan
Write-Host ''
