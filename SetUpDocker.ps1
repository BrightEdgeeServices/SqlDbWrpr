param (
    [Parameter(Mandatory = $false, Position = 0)]
    [string]$Variant,

    [Parameter(Mandatory = $false)]
    [Switch]$Help,

# Used to indicate that the code is called by Pester to avoid unwanted code execution during Pester testing.
    [Parameter(Mandatory = $false)]
    [Switch]$Pester
)

function Show-Help {
    $separator = "-" * 80
    Write-Host $separator -ForegroundColor Cyan

    @"
    Usage:
    ------
    SetUpDocker.ps1 -Variant VariantName
    SetUpDocker.ps1 -Help

    Arguments:
    (0) Variant: Set the docker compose configuration file. If no variant name is
                 provided it will configure docker-compose.yaml else if the variant
                 name is "myvaraint" it will configure docker-compose-myvariant.yaml.
    e.g. SetUpDocker.ps1 MyVariant
"@ | Write-Host

    Write-Host $separator -ForegroundColor Cyan
}

if (-not $Pester) {
    Write-Host ''
    $dateTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "=[ START $dateTime ]=============================[ SetUpDocker.ps1 ]=" -ForegroundColor Blue
    Write-Host "Executing $PSCommandPath..." -ForegroundColor Yellow
    Write-Host "Create and start Docker containers." -ForegroundColor Yellow

    if ($ProjectName -eq "" -or $Help) {
        Show-Help
    }
    else {
        $DockerConfigFileName = "docker-compose.yaml"
        if ($Variant) {
            $DockerConfigFileName = "docker-compose-$Variant.yaml"
        }
        Write-Host "Docker config file: $DockerConfigFileName" -ForegroundColor Yellow
        if (Test-Path $DockerConfigFileName) {
            $DockerComposeProjectName = $env:COMPOSE_PROJECT_NAME
            if ([string]::IsNullOrWhiteSpace($DockerComposeProjectName)) {
                $DockerComposeProjectName = $env:PROJECT_NAME
            }
            if ([string]::IsNullOrWhiteSpace($DockerComposeProjectName)) {
                $DockerComposeProjectName = Split-Path -Path (Get-Location) -Leaf
            }

            $OriginalDockerComposeProjectName = $DockerComposeProjectName
            $DockerComposeProjectName = $DockerComposeProjectName.ToLowerInvariant()
            $DockerComposeProjectName = $DockerComposeProjectName -replace '[^a-z0-9_-]', '_'
            if ($DockerComposeProjectName -notmatch '^[a-z0-9]') {
                $DockerComposeProjectName = "rte_$DockerComposeProjectName"
            }
            if ($DockerComposeProjectName -ne $OriginalDockerComposeProjectName) {
                Write-Host "Using Docker Compose project name '$DockerComposeProjectName'." -ForegroundColor Yellow
            }
            if (Test-Path ./CreateDbSqlScript.ps1) {
                & ./CreateDbSqlScript.ps1
            }
            if (Test-Path ./SetupDotEnv.ps1) {
                & ./SetupDotEnv.ps1
            }
            docker compose -p $DockerComposeProjectName -f $DockerConfigFileName down -v --remove-orphans
            docker volume prune -a  --force
            docker builder prune --force
            docker compose -p $DockerComposeProjectName -f $DockerConfigFileName up -d
        }
        else {
            Write-Host "The $DockerConfigFileName does not exist!" -ForegroundColor Red
        }

        Write-Host '-[ END SetUpDocker ]------------------------------------------------------------' -ForegroundColor Cyan
        Write-Host ''
    }
}
