# Bootstrap en Windows nativo. Requiere: gh auth login previo. NO imprime tokens.
$ErrorActionPreference = 'Stop'

$repoName = if ($env:REPO_NAME) { $env:REPO_NAME } else { 'amazon-us-affiliate-engine' }
$visibility = if ($env:REPO_VISIBILITY) { $env:REPO_VISIBILITY } else { 'private' }
$owner = if ($env:GITHUB_OWNER) { $env:GITHUB_OWNER } else { (gh api user --jq .login).Trim() }

if (-not (gh auth status 2>$null)) { throw 'gh sin autenticar. Ejecute: gh auth login' }
if ($visibility -notin @('private', 'public')) { throw 'REPO_VISIBILITY debe ser private o public' }

foreach ($required in @('SKILL.md', 'README.md', 'CHANGELOG.md', 'scripts/validate_contracts.py', 'docs/index.html')) {
    if (-not (Test-Path $required)) { throw "Falta archivo obligatorio: $required" }
}

git config core.hooksPath .githooks
python scripts/validate_contracts.py | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Validacion de contratos fallida' }

$pending = git status --porcelain
if ($pending) {
    git add -A
    git commit -m 'chore(skill): bootstrap v1.0.0'
}

$branch = (git branch --show-current).Trim()
if (-not $branch) { $branch = 'main' }

$exists = gh repo view "$owner/$repoName" 2>$null
if ($exists) {
    Write-Output "Repo $owner/$repoName ya existe; reutilizando."
    git remote get-url origin 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        git remote set-url origin "https://github.com/$owner/$repoName.git"
    } else {
        git remote add origin "https://github.com/$owner/$repoName.git"
    }
} else {
    gh repo create "$owner/$repoName" "--$visibility" --source=. --remote=origin
}

git push -u origin $branch

try {
    $payload = '{"source":{"branch":"' + $branch + '","path":"/docs"}}'
    $payload | gh api --method PUT "repos/$owner/$repoName/pages" --input - | Out-Null
    Write-Output "GitHub Pages configurado desde /docs en $branch"
} catch {
    Write-Output "No se pudo configurar Pages por API. Hacerlo en: Settings > Pages > Source: $branch /docs"
}

Write-Output "LISTO: https://github.com/$owner/$repoName"
