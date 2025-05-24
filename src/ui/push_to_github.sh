#!/usr/bin/env bash
# This script sets up git global config, clones the repository if not present, and pushes the current repository to GitHub

set -euo pipefail

# Change to the project root directory (2 levels up from this script)
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "$script_dir/../.." && pwd)"
cd "$project_root"

echo "Setting up git global username and email..."
# Set your global git username and email here (update as needed)
if [ -f "$script_dir/.env" ]; then
    # shellcheck disable=SC1090
    export $(grep -v '^#' "$script_dir/.env" | xargs)
    if [ -n "${GITHUB_USERNAME:-}" ] && [ -n "${GIT_USER_EMAIL:-}" ]; then
        git config --global user.name "$GITHUB_USERNAME"
        git config --global user.email "$GIT_USER_EMAIL"
    else
        echo "GIT_USERNAME and/or GIT_USER_EMAIL not set in .env file."
        exit 1
    fi
else
    echo ".env file not found in $script_dir. Please provide the .env file with GIT_USERNAME and GIT_USER_EMAIL."
    exit 1
fi

# Load GitHub repo URL, username, and PAT from .env file
if [ -f "$script_dir/.env" ]; then
    # shellcheck disable=SC1090
    export $(grep -v '^#' "$script_dir/.env" | xargs)
    REPO_URL="$GITHUB_REPO_URL"
    GITHUB_USERNAME="${GITHUB_USERNAME:-}"
    GITHUB_PAT="${GITHUB_PAT:-}"
else
    echo ".env file not found in $script_dir. Please provide the .env file with GITHUB_REPO_URL, GITHUB_USERNAME and GITHUB_PAT."
    exit 1
fi

# Remove trailing slash if present
REPO_URL="${REPO_URL%/}"
REPO_DIR_NAME="$(basename -s .git "$REPO_URL")"

# Create the clone URL with username and PAT authentication
if [ -n "${GITHUB_USERNAME:-}" ] && [ -n "${GITHUB_PAT:-}" ]; then
    CLONE_URL="https://${GITHUB_USERNAME}:${GITHUB_PAT}@github.com/$(echo "$REPO_URL" | sed -E 's|^https://github.com/||')"
else
    CLONE_URL="$REPO_URL"
fi

echo "Cloning repository from $CLONE_URL..."

# Clone the repository if the .git directory does not exist
if [ ! -d ".git" ]; then
    echo "No .git directory found. Cloning repository..."
    git clone "$CLONE_URL" "$REPO_DIR_NAME"
    cd "$REPO_DIR_NAME"
    
    # Copy the generated HTML file to the cloned repository
    echo "Adding generated HTML file to the repository..."    
    if [ -f "$script_dir/generated_app.html" ]; then
        cp "$script_dir/generated_app.html" .
        echo "Copied generated_app.html"
    else
        echo "No generated HTML file found."
        exit 1
    fi
else
    echo ".git directory found. Using existing repository."
    # Copy the generated HTML file to the repository
    if [ -f "$script_dir/generated_app.html" ]; then
        cp "$script_dir/generated_app.html" .
        echo "Copied generated_app.html to existing repository"
    else
        echo "No generated HTML file found."
        exit 1
    fi
fi

echo "Pushing code to GitHub..."

# Add all changes
git add .

# Commit with a generic message and timestamp
timestamp=$(date +"%Y-%m-%d %H:%M:%S")
commit_msg="Auto-commit from multi-agent system: $timestamp"
echo "Creating commit: $commit_msg"
git commit -m "$commit_msg" || echo "No changes to commit."

# When pushing, use the token-injected remote URL if available
if [ -n "${GIT_TOKEN:-}" ]; then
    git remote set-url origin "$CLONE_URL"
fi

# Push to the default remote (origin) and branch (main or master)
echo "Pushing to GitHub..."
if git push origin main; then
    echo "Successfully pushed to main branch"
else
    echo "Main branch not found, trying master branch..."
    if git push origin master; then
        echo "Successfully pushed to master branch"
    else
        echo "Error pushing to GitHub"
    fi
fi

echo "GitHub push operation completed."