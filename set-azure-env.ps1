# Azure Environment Variables Setup Script (PowerShell)
# This script sets the required environment variables for the Azure Container App deployment

param(
    [Parameter(Mandatory=$false)]
    [string]$AppName = "streamlit-multi-agent",  # Replace with your actual Azure Container App name
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "multi-agent-rg"   # Replace with your actual resource group name
)

# Function to write colored output
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    switch ($Color) {
        "Green" { Write-Host "✅ $Message" -ForegroundColor Green }
        "Yellow" { Write-Host "⚠️  $Message" -ForegroundColor Yellow }
        "Red" { Write-Host "❌ $Message" -ForegroundColor Red }
        "Blue" { Write-Host "ℹ️  $Message" -ForegroundColor Blue }
        default { Write-Host "$Message" -ForegroundColor White }
    }
}

Write-ColorOutput "Setting up Azure environment variables for Container App deployment..." "Blue"

# Check if Azure CLI is installed
try {
    $azVersion = az --version
    Write-ColorOutput "Azure CLI is installed" "Green"
} catch {
    Write-ColorOutput "Azure CLI is not installed. Please install it first:" "Red"
    Write-Host "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
}

# Check if user is logged in to Azure
try {
    $account = az account show --query "name" -o tsv 2>$null
    if ($account) {
        Write-ColorOutput "Logged in to Azure account: $account" "Green"
    } else {
        Write-ColorOutput "Please log in to Azure..." "Blue"
        az login
    }
} catch {
    Write-ColorOutput "Please log in to Azure..." "Blue"
    az login
}

# Load environment variables from .env file
if (Test-Path ".env") {
    Write-ColorOutput "Loading environment variables from .env file..." "Blue"
    
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            $name = $matches[1]
            $value = $matches[2]
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
    Write-ColorOutput "Environment variables loaded from .env" "Green"
} else {
    Write-ColorOutput ".env file not found! Please ensure the .env file exists with your configuration." "Red"
    exit 1
}

# Check for required environment variables
$RequiredVars = @(
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT", 
    "AZURE_OPENAI_DEPLOYMENT_NAME",
    "AZURE_OPENAI_API_VERSION",
    "GITHUB_REPO_URL",
    "GITHUB_PAT",
    "GIT_USER_EMAIL",
    "GITHUB_USERNAME",
    "SIMULATION_MODE"
)

Write-ColorOutput "Checking required environment variables..." "Blue"
$MissingVars = @()

foreach ($var in $RequiredVars) {
    $value = [Environment]::GetEnvironmentVariable($var)
    if ([string]::IsNullOrEmpty($value)) {
        $MissingVars += $var
        Write-ColorOutput "$var is not set" "Red"
    } else {
        if ($var -like "*KEY*" -or $var -like "*PAT*") {
            Write-ColorOutput "$var is set (masked)" "Green"
        } else {
            Write-ColorOutput "$var is set: $value" "Green"
        }
    }
}

if ($MissingVars.Count -gt 0) {
    Write-ColorOutput "Missing required environment variables: $($MissingVars -join ', ')" "Red"
    Write-ColorOutput "Please update your .env file with all required values." "Blue"
    exit 1
}

Write-ColorOutput "Setting Azure Container App environment variables..." "Blue"

# Build the environment variables string
$envVars = @(
    "AI_SERVICE=azure",
    "GLOBAL_LLM_SERVICE=AzureOpenAI",
    "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=$([Environment]::GetEnvironmentVariable('AZURE_OPENAI_DEPLOYMENT_NAME'))",
    "AZURE_OPENAI_DEPLOYMENT_NAME=$([Environment]::GetEnvironmentVariable('AZURE_OPENAI_DEPLOYMENT_NAME'))",
    "AZURE_OPENAI_ENDPOINT=$([Environment]::GetEnvironmentVariable('AZURE_OPENAI_ENDPOINT'))",
    "AZURE_OPENAI_API_KEY=$([Environment]::GetEnvironmentVariable('AZURE_OPENAI_API_KEY'))",
    "AZURE_OPENAI_API_VERSION=$([Environment]::GetEnvironmentVariable('AZURE_OPENAI_API_VERSION'))",
    "GITHUB_REPO_URL=$([Environment]::GetEnvironmentVariable('GITHUB_REPO_URL'))",
    "GITHUB_PAT=$([Environment]::GetEnvironmentVariable('GITHUB_PAT'))",
    "GIT_USER_EMAIL=$([Environment]::GetEnvironmentVariable('GIT_USER_EMAIL'))",
    "GITHUB_USERNAME=$([Environment]::GetEnvironmentVariable('GITHUB_USERNAME'))",
    "SIMULATION_MODE=$([Environment]::GetEnvironmentVariable('SIMULATION_MODE'))"
)

# Set the environment variables in Azure Container App
try {
    $result = az containerapp update `
        --name $AppName `
        --resource-group $ResourceGroup `
        --set-env-vars $envVars `
        --output table

    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "Environment variables successfully set in Azure Container App!" "Green"
        Write-ColorOutput "The container app will restart automatically to pick up the new environment variables." "Blue"
        Write-ColorOutput "You can verify the deployment by checking the Azure portal or using:" "Blue"
        Write-Host "az containerapp show --name $AppName --resource-group $ResourceGroup --query 'properties.template.containers[0].env'"
    } else {
        Write-ColorOutput "Failed to set environment variables in Azure Container App." "Red"
        exit 1
    }
} catch {
    Write-ColorOutput "Failed to set environment variables in Azure Container App: $($_.Exception.Message)" "Red"
    exit 1
}

Write-ColorOutput "Azure environment setup completed!" "Green"
Write-ColorOutput "Your app should now have access to all required environment variables." "Blue"
Write-ColorOutput "Note: It may take a few minutes for the container to restart and pick up the new variables." "Yellow"
