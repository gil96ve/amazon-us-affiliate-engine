#!/usr/bin/env bash
# Bootstrap en un paso: commit inicial + repo GitHub + push + Pages desde /docs.
# Requiere: gh auth login previo. NO imprime tokens.
set -euo pipefail

REPO_NAME="${REPO_NAME:-amazon-us-affiliate-engine}"
VISIBILITY="${REPO_VISIBILITY:-private}"
OWNER="${GITHUB_OWNER:-}"

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: GitHub CLI (gh) no encontrado. Instale gh y ejecute: gh auth login" >&2
  exit 2
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: gh sin autenticar. Ejecute: gh auth login" >&2
  exit 2
fi
if [[ -z "$OWNER" ]]; then
  OWNER="$(gh api user --jq .login)"
fi

case "$VISIBILITY" in
  private|public) ;;
  *) echo "ERROR: REPO_VISIBILITY debe ser private o public" >&2; exit 2 ;;
esac

for required in SKILL.md README.md CHANGELOG.md scripts/validate_contracts.py docs/index.html; do
  [[ -f "$required" ]] || { echo "ERROR: falta archivo obligatorio $required" >&2; exit 2; }
done

git config core.hooksPath .githooks
if [[ -f .githooks/pre-commit ]]; then
  chmod +x .githooks/pre-commit
fi
python scripts/validate_contracts.py >/dev/null

if git diff --quiet && git diff --cached --quiet; then
  echo "Sin cambios nuevos para el commit inicial."
else
  git add -A
  git commit -m "chore(skill): bootstrap v1.0.0"
fi

BRANCH="$(git branch --show-current)"
BRANCH="${BRANCH:-main}"

if gh repo view "$OWNER/$REPO_NAME" >/dev/null 2>&1; then
  echo "Repo $OWNER/$REPO_NAME ya existe; reutilizando."
  if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "https://github.com/$OWNER/$REPO_NAME.git"
  else
    git remote add origin "https://github.com/$OWNER/$REPO_NAME.git"
  fi
else
  gh repo create "$OWNER/$REPO_NAME" "--$VISIBILITY" --source=. --remote=origin
fi

git push -u origin "$BRANCH"

if printf '{"source":{"branch":"%s","path":"/docs"}}' "$BRANCH" \
    | gh api --method PUT "repos/$OWNER/$REPO_NAME/pages" --input - >/dev/null 2>&1; then
  echo "GitHub Pages configurado desde /docs en $BRANCH"
else
  echo "No se pudo configurar Pages por API. Hacerlo en: Settings > Pages > Source: $BRANCH /docs"
fi

echo "LISTO: https://github.com/$OWNER/$REPO_NAME"
