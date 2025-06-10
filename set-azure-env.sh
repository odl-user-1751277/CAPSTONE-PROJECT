#!/bin/bash

# Azure Environment Variables Setup Script
# This script sets the required environment variables for the Azure Container App deployment

set -e  # Exit on any error

# Configuration - UPDATE THESE VALUES
AZURE_APP_NAME="dev-ui-wiqsod2wb3qek"  # Replace with your actual Azure Container App name
AZURE_RESOURCE_GROUP="CapstoneEnv"   # Replace with your actual resource group name

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo_info "Setting up Azure environment variables for Container App deployment..."

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo_error "Azure CLI is not installed. Please install it first:"
    echo "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if user is logged in to Azure
if ! az account show &> /dev/null; then
    echo_info "Please log in to Azure..."
    az login
fi

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo_info "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
    echo_success "Environment variables loaded from .env"
else
    echo_error ".env file not found! Please ensure the .env file exists with your configuration."
    exit 1
fi

# Check for required environment variables
REQUIRED_VARS=(
    "AZURE_OPENAI_API_KEY"
    "AZURE_OPENAI_ENDPOINT"
    "AZURE_OPENAI_DEPLOYMENT_NAME"
    "AZURE_OPENAI_API_VERSION"
    "GITHUB_REPO_URL"
    "GITHUB_PAT"
    "GIT_USER_EMAIL"
    "GITHUB_USERNAME"
    "SIMULATION_MODE"
)

echo_info "Checking required environment variables..."
MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
        echo_error "$var is not set"
    else
        if [[ "$var" == *"KEY"* || "$var" == *"PAT"* ]]; then
            echo_success "$var is set (masked)"
        else
            echo_success "$var is set: ${!var}"
        fi
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo_error "Missing required environment variables: ${MISSING_VARS[*]}"
    echo_info "Please update your .env file with all required values."
    exit 1
fi

echo_info "Setting Azure Container App environment variables..."

# Set the environment variables in Azure Container App
az containerapp update \
    --name "$AZURE_APP_NAME" \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --set-env-vars \
        AI_SERVICE="azure" \
        GLOBAL_LLM_SERVICE="AzureOpenAI" \
        AZURE_OPENAI_CHAT_DEPLOYMENT_NAME="$AZURE_OPENAI_DEPLOYMENT_NAME" \
        AZURE_OPENAI_DEPLOYMENT_NAME="$AZURE_OPENAI_DEPLOYMENT_NAME" \
        AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
        AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
        AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
        GITHUB_REPO_URL="$GITHUB_REPO_URL" \
        GITHUB_PAT="$GITHUB_PAT" \
        GIT_USER_EMAIL="$GIT_USER_EMAIL" \
        GITHUB_USERNAME="$GITHUB_USERNAME" \
        SIMULATION_MODE="$SIMULATION_MODE" \
    --output table

if [ $? -eq 0 ]; then
    echo_success "Environment variables successfully set in Azure Container App!"
    echo_info "The container app will restart automatically to pick up the new environment variables."
    echo_info "You can verify the deployment by checking the Azure portal or using:"
    echo "az containerapp show --name $AZURE_APP_NAME --resource-group $AZURE_RESOURCE_GROUP --query 'properties.template.containers[0].env'"
else
    echo_error "Failed to set environment variables in Azure Container App."
    exit 1
fi

echo_success "Azure environment setup completed!"
echo_info "Your app should now have access to all required environment variables."
echo_warning "Note: It may take a few minutes for the container to restart and pick up the new variables."
