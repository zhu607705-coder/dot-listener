#!/usr/bin/env bash
# Creates only a NEW PRIVATE repository. Never modifies an existing remote.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OWNER="zhu607705-coder"
NAME="${1:-dot-listener}"
[[ "$NAME" =~ ^[a-zA-Z0-9._-]+$ ]] || { echo "Invalid repository name" >&2; exit 1; }
command -v gh >/dev/null || { echo "Install GitHub CLI first (brew install gh on macOS)." >&2; exit 1; }
command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "Run: gh auth login" >&2; exit 1; }
ACTUAL="$(gh api user --jq .login)"
[[ "$ACTUAL" == "$OWNER" ]] || { echo "Expected account $OWNER, got $ACTUAL; no changes made." >&2; exit 1; }
if gh repo view "$OWNER/$NAME" >/dev/null 2>&1; then
    echo "Repository exists; refusing to overwrite or push. Choose a new name." >&2; exit 1
fi
# This archive contains a source tree, not a remotely created repository.
if [[ ! -d .git ]]; then git init -b main; fi
[[ -z "$(git remote)" ]] || { echo "Existing Git remote detected; refusing to change it." >&2; exit 1; }
git config user.name >/dev/null || { echo "Set git user.name before publishing" >&2; exit 1; }
git config user.email >/dev/null || { echo "Set git user.email before publishing" >&2; exit 1; }
# Explicit allowlist: runtime, credentials, model weights and recordings are never added.
git add README.md AGENTS.md SECURITY.md CHANGELOG.md pyproject.toml .gitignore .env.example \
    .github android contracts docs evidence examples scripts src tests web
# Fail closed if a forbidden path has ever been force-added.
if git ls-files | grep -E '(^|/)(\.env$|runtime/|recordings/|models/)|\.(wav|pcm|enc|onnx|sqlite3|jks|keystore)$'; then
    echo "Sensitive paths are staged/tracked; refusing to publish." >&2; exit 1
fi
if ! git diff --cached --quiet; then git commit -m "feat: bootstrap local-first Dot Listener architecture and tested relay"; fi
gh repo create "$OWNER/$NAME" --private --source=. --remote=origin --push \
   --description "Local-first voice-to-dot input: Android capture scaffold, encrypted text relay, operational demo and evidence-backed architecture"
gh repo view "$OWNER/$NAME" --json url,isPrivate --jq '{url,isPrivate}'
