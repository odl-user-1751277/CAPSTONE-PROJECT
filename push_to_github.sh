#!/bin/bash
# push_to_github.sh - Looks for index.html in root or src/ui/, stages, commits, pushes
# Uses GitHub PAT for authentication in Azure Container Apps

set -e  # Exit on any error

echo "🚀 Starting Git push process..."

# Load environment variables for Azure deployment
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Loaded environment variables from .env"
fi

# Configure Git with PAT for Azure Container Apps authentication
if [ ! -z "$GITHUB_PAT" ] && [ ! -z "$GITHUB_USERNAME" ] && [ ! -z "$GIT_USER_EMAIL" ]; then
    echo "🔐 Configuring Git authentication with PAT..."
    git config --global user.name "$GITHUB_USERNAME"
    git config --global user.email "$GIT_USER_EMAIL"
    
    # Set up remote URL with PAT authentication
    if [ ! -z "$GITHUB_REPO_URL" ]; then
        # Extract repo info from URL
        REPO_URL_WITH_PAT=$(echo "$GITHUB_REPO_URL" | sed "s|https://github.com|https://$GITHUB_PAT@github.com|")
        git remote set-url origin "$REPO_URL_WITH_PAT"
        echo "✅ Git remote configured with PAT authentication"
    fi
else
    echo "⚠️ GitHub PAT or credentials not found in .env - using existing Git config"
fi

# Set default and fallback paths
HTML_ROOT="index.html"
HTML_UI="src/ui/index.html"

if [ -f "$HTML_ROOT" ]; then
    HTML_FILE="$HTML_ROOT"
    echo "📄 Found index.html in root: $HTML_FILE"
elif [ -f "$HTML_UI" ]; then
    HTML_FILE="$HTML_UI"
    echo "📄 Found index.html in src/ui/: $HTML_FILE"
else
    echo "❌ Error: index.html not found in root or src/ui/"
    exit 1
fi

# Check for git repo
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a Git repository"
    exit 1
fi

echo "📝 Adding $HTML_FILE to staging..."
git add "$HTML_FILE"

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "ℹ️ No changes to commit"
    exit 0
fi

echo "📄 Staged changes:"
git diff --staged --name-only

# Create commit with timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
COMMIT_MESSAGE="Auto-deploy: Updated web app - $TIMESTAMP"

echo "💾 Committing changes..."
git commit -m "$COMMIT_MESSAGE"

CURRENT_BRANCH=$(git branch --show-current)
echo "⬆️  Pushing to branch: $CURRENT_BRANCH"
git push origin "$CURRENT_BRANCH"

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub!"
    echo "🌐 Changes are now live on your repository"
else
    echo "❌ Push failed. Please check your Git credentials and network connection"
    exit 1
fi