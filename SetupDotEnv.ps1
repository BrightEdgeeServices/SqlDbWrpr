Write-Host ''
$dateTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "=[ START $dateTime ]==============================[ SetupDotEnv.ps1 ]=" -ForegroundColor Blue
Write-Host "Executing $PSCommandPath..." -ForegroundColor Yellow

function Get-RequiredEnvValue {
    param (
        [Parameter(Mandatory = $true)]
        [string]$VariableName
    )
    $value = [Environment]::GetEnvironmentVariable($VariableName)
    if ([string]::IsNullOrWhiteSpace($value)) {
        throw "Required environment variable '$VariableName' is missing or empty."
    }
    return $value
}

function Get-EnvValueOrDefault {
    param (
        [Parameter(Mandatory = $true)]
        [string]$VariableName,
        [Parameter(Mandatory = $true)]
        [string]$DefaultValue
    )
    $value = [Environment]::GetEnvironmentVariable($VariableName)
    if ([string]::IsNullOrWhiteSpace($value)) {
        return $DefaultValue
    }
    return $value
}

$scriptDir = Split-Path -Parent $PSCommandPath
$filePath = Join-Path -Path $scriptDir -ChildPath ".env"

# Define the contents of the file
$fileContent = @"
DEV_AUTO_MYSQL_HOST=$(Get-RequiredEnvValue -VariableName "DEV_AUTO_MYSQL_HOST")
DEV_AUTO_MYSQL_TCP_PORT=$(Get-RequiredEnvValue -VariableName "DEV_AUTO_MYSQL_TCP_PORT")
DEV_AUTO_OVERRIDE=$(Get-RequiredEnvValue -VariableName "DEV_AUTO_OVERRIDE")
DEV_AUTO_RTEAPI_REDIS_PORT=$(Get-RequiredEnvValue -VariableName "DEV_AUTO_RTEAPI_REDIS_PORT")
DEV_DB_ROLLBACK_OVERRIDE=$(Get-RequiredEnvValue -VariableName "DEV_DB_ROLLBACK_OVERRIDE")
INSTALLER_USERID=$(Get-RequiredEnvValue -VariableName "INSTALLER_USERID")
INSTALLER_PWD=$(Get-RequiredEnvValue -VariableName "INSTALLER_PWD")
MYSQL_DATABASE=$(Get-RequiredEnvValue -VariableName "MYSQL_DATABASE")
MYSQL_HOST=$(Get-RequiredEnvValue -VariableName "MYSQL_HOST")
MYSQL_PASSWORD=$(Get-RequiredEnvValue -VariableName "MYSQL_PASSWORD" )
MYSQL_PWD=$(Get-RequiredEnvValue -VariableName "MYSQL_PWD")
MYSQL_ROOT_PASSWORD=$(Get-RequiredEnvValue -VariableName "MYSQL_ROOT_PASSWORD")
MYSQL_ROOT_USER=$(Get-RequiredEnvValue -VariableName "MYSQL_ROOT_USER")
MYSQL_TCP_PORT=$(Get-RequiredEnvValue -VariableName "MYSQL_TCP_PORT")
MYSQL_USER=$(Get-RequiredEnvValue -VariableName "MYSQL_USER")
PROJECT_DIR=$(Get-RequiredEnvValue -VariableName "PROJECT_DIR")
PROJECT_NAME=$(Get-RequiredEnvValue -VariableName "PROJECT_NAME")
VENV_ENVIRONMENT=$(Get-RequiredEnvValue -VariableName "VENV_ENVIRONMENT")

"@

# Write the contents to the file
Set-Content -Path $filePath -Value $fileContent

# Output a confirmation message
Write-Host "File '$filePath' has been created with the specified contents."
Write-Host '-[ END SetupDotEnv.ps1 ]--------------------------------------------------------' -ForegroundColor Cyan
Write-Host ''
