# SetupPrivateRepoAccess.ps1
Write-Host ''

function Restore-LocalTempDirectory {
    if ($null -ne $script:OriginalTemp) {
        $env:TEMP = $script:OriginalTemp
    }
    if ($null -ne $script:OriginalTmp) {
        $env:TMP = $script:OriginalTmp
    }
    if ($null -ne $script:OriginalTmpDir) {
        $env:TMPDIR = $script:OriginalTmpDir
    }
}

function Set-LocalTempDirectory {
    $script:OriginalTemp = $env:TEMP
    $script:OriginalTmp = $env:TMP
    $script:OriginalTmpDir = $env:TMPDIR

    $poetryEnvPath = (poetry env info --path).Trim()
    $projectRoot = (Resolve-Path $PSScriptRoot).Path
    $tempRoot = Join-Path $projectRoot ".tmp\poetry"

    if ($poetryEnvPath) {
        $poetryEnvDrive = [System.IO.Path]::GetPathRoot($poetryEnvPath)
        $projectDrive = [System.IO.Path]::GetPathRoot($projectRoot)
        if ($poetryEnvDrive -ne $projectDrive) {
            $tempRoot = Join-Path $poetryEnvDrive "poetry-temp"
        }
    }
    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

    $env:TEMP = $tempRoot
    $env:TMP = $tempRoot
    $env:TMPDIR = $tempRoot

    Write-Host "Using temp directory: $tempRoot" -ForegroundColor DarkYellow
}

function Remove-RepositoryConfiguration {
    param (
        [Object]$RepoDetails
    )
    Write-Host "Remove configuration" -ForegroundColor Magenta
    $command = "poetry source remove $( $RepoDetails.name )"
    Write-Host "Executing: $command" -ForegroundColor Cyan
    Invoke-Expression $command
    $command = "poetry remove $( $RepoDetails.name )"
    Write-Host "Executing: $command" -ForegroundColor Cyan
    Invoke-Expression $command
}

function Publish-RepositoryConfiguration {
    param (
        [Object]$RepoDetails
    )
    Write-Host "Add configuration" -ForegroundColor Magenta
    $command = "poetry source add --priority=explicit $( $RepoDetails.name ) https://github.com/$( $RepoDetails.org )/$( $RepoDetails.name ).git"
    Write-Host "Executing: $command" -ForegroundColor Cyan
    Invoke-Expression $command
    $command = "poetry add --source $( $RepoDetails.name ) git+https://github.com/$( $RepoDetails.org )/$( $RepoDetails.name ).git$( $RepoDetails.version_branch )"
    Write-Host "Executing: $command" -ForegroundColor Cyan
    Invoke-Expression $command
}

Write-Host ''
$dateTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "=[ START $dateTime ]===================[ SetupPrivateRepoAccess.ps1 ]=" -ForegroundColor Blue
Write-Host "Executing $PSCommandPath..." -ForegroundColor Yellow

# List of keys to configure in Poetry
#poetry config "http-basic.BEE" "__token__" $env:GH_REPO_ACCESS_BEE_LOCAL_USER
#poetry config "http-basic.RTE" "__token__" $env:GH_REPO_ACCESS_RTE_LOCAL_USER

$RepoDetailsList = @(
    [PSCustomObject]@{
        name           = "rtecommon"
        token          = "RTE"
        org            = "RealTimeEvents"
        version_branch = "#master"
        active         = $false
    }
    [PSCustomObject]@{
        name           = "rteapi"
        token          = "RTE"
        org            = "RealTimeEvents"
        version_branch = "#master"
        active         = $false
    }
    [PSCustomObject]@{
        name           = "fidewebtourparser"
        token          = "RTE"
        org            = "RealTimeEvents"
        version_branch = "#master"
        active         = $false
    }
    [PSCustomObject]@{
        name           = "fideratinglist"
        token          = "RTE"
        org            = "RealTimeEvents"
        version_branch = "#master"
        active         = $false
    }
    [PSCustomObject]@{
        name           = "sample_data_factory"
        token          = "RTE"
        org            = "RealTimeEvents"
        version_branch = "#master"
        active         = $false
    }
)

Set-LocalTempDirectory
try {
    foreach ($RepoDetails in $RepoDetailsList) {
        # Configure credentials for this source
        poetry config "http-basic.$( $RepoDetails.name )" "__token__" $env:GH_REPO_ACCESS_RTE_LOCAL_USER

        Remove-RepositoryConfiguration -RepoDetails $RepoDetails
        if($RepoDetails.active -eq $true) {
            Publish-RepositoryConfiguration -RepoDetails $RepoDetails
        }
    }
}
finally {
    Restore-LocalTempDirectory
}

Write-Host '-[ END SetupPrivateRepoAccess.ps1 ]---------------------------------------------' -ForegroundColor Cyan
Write-Host ''
