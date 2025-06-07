#!/bin/bash
# push_to_github.sh - Looks for index.html in root or src/ui/, stages, commits, pushes

set -e  # Exit on any error

echo "🚀 Starting Git push process..."

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