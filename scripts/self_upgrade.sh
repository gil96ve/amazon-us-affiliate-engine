#!/usr/bin/env bash
# GIT_SELF_UPGRADE: RCA -> bump semver -> CHANGELOG -> rama -> PR. Nunca commitea en main.
# Uso: bash scripts/self_upgrade.sh skills/02_SKILL_VIRAL_SCRIPTER.md patch "fix(skill): ajustar ganchos"
set -euo pipefail

SKILL_PATH="${1:-}"
BUMP="${2:-patch}"
MESSAGE="${3:-fix(skill): mejora automatica por FIX}"

if [[ -z "$SKILL_PATH" || ! -f "$SKILL_PATH" ]]; then
  echo "ERROR: debe indicar un archivo de skill existente." >&2
  echo "Uso: bash scripts/self_upgrade.sh <skill.md> <patch|minor|major> \"mensaje\"" >&2
  exit 2
fi

case "$BUMP" in
  patch|minor|major) ;;
  *) echo "ERROR: bump debe ser patch, minor o major" >&2; exit 2 ;;
esac

NEW_VERSION="$(python scripts/bump_version.py "$SKILL_PATH" --bump "$BUMP")"
python scripts/bump_version.py data/state_memory.json --bump "$BUMP" >/dev/null
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '\n## [v%s] - %s\n- %s\n' "$NEW_VERSION" "$TIMESTAMP" "$MESSAGE" >> CHANGELOG.md

BRANCH="skill/auto-$(basename "$SKILL_PATH" .md)-v${NEW_VERSION}-$(date -u +%Y%m%d%H%M%S)"
git checkout -b "$BRANCH"
git add "$SKILL_PATH" data/state_memory.json CHANGELOG.md
git commit -m "$MESSAGE"
python scripts/validate_contracts.py >/dev/null

if gh auth status >/dev/null 2>&1; then
  git push -u origin "$BRANCH"
  gh pr create --fill --base main --head "$BRANCH"
else
  printf 'HANDOFF | motivo: GITHUB_OFFLINE | rama: %s | comandos: git push -u origin %s && gh pr create --fill --base main --head %s\n' \
    "$BRANCH" "$BRANCH" "$BRANCH"
fi
