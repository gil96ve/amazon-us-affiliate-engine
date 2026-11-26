# Amazon US Affiliate Engine (Orca + GitHub)

Sistema autónomo multi-agente para validación de productos, guiones virales de 30s y micro-webs en GitHub Pages. **Costo initial: $0** (solo Git CLI, `gh` CLI, Python stdlib y archivos locales).

- **Amazon Store ID / Associate Tag:** `vettedgearlab-20`
- **Marketplace:** Amazon US (`amazon.com`)
- **Versión:** `v1.0.0`
- **Modelo orquestador:** Big Pickle (Orca)

## Arquitectura

```text
Input (URL | ASIN | keyword)
        │
        ▼
00_ORCHESTRATOR_DIRECTOR   [INTERACTIVE]  ← único escritor de estado/CHANGELOG
        │  data/staging/<run_id>/product_input.json
        ▼
01_SKILL_PRODUCT_ANALYST   [HEADLESS] → data/products.json
        │  product.specs_verified === true
        ▼
02_SKILL_VIRAL_SCRIPTER    [HEADLESS] → data/content_assets.json
        │  10 dolores + 10 hooks + 30s + prompts + 3 preguntas
        ▼
03_SKILL_GITHUB_PAGES_BUILDER [HEADLESS] → docs/index.html (GitHub Pages)
        │
        ▼
00 valida + consolida + logs + commit/PR + telemetría
```

## Estructura del monorepo

| Ruta | Contenido |
|---|---|
| `SKILL.md` | Punto de entrada / meta-skill |
| `skills/00_ORCHESTRATOR_DIRECTOR.md` | Director, modo interactivo, sync y `FIX:` |
| `skills/01_SKILL_PRODUCT_ANALYST.md` | Analista, salida JSON puro |
| `skills/02_SKILL_VIRAL_SCRIPTER.md` | Guion viral 30s, salida JSON puro |
| `skills/03_SKILL_GITHUB_PAGES_BUILDER.md` | Landing autocontenida, salida HTML |
| `data/products.json` | Productos validados |
| `data/content_assets.json` | Guiones y activos generados |
| `data/state_memory.json` | ASIN procesados, nichos, hooks ganadores |
| `data/staging/` | Artefactos temporales por `run_id` (no se commitean) |
| `logs/execution_log.jsonl` | Métricas por ejecución (sin secretos) |
| `logs/offline_queue.jsonl` | Cola de sync cuando GitHub falla |
| `docs/index.html` | Landing demo lista para GitHub Pages |
| `scripts/init_repo.sh` / `.ps1` | Bootstrap del repositorio en un paso |
| `scripts/self_upgrade.sh` | `GIT_SELF_UPGRADE` vía rama + PR |
| `scripts/validate_contracts.py` | Linter de contratos y compliance |
| `.githooks/pre-commit` | Escaneo de secretos + linter |
| `.github/workflows/validate.yml` | CI gratuita en push/PR |
| `tests/run_cold_tests.py` | 4 pruebas adversariales en frío |
| `tests/ADVERSARIAL_EVAL.md` | Evidencia de la auditoría y mapeo FMEA |
| `docs/SELF_EVOLUTION.md` | Telemetría, RCA, `GIT_SELF_UPGRADE` y rollback |
| `.gitignore` | Excluye `data/staging/`, `.env` y secretos locales |

## Uso

1. Entrega al Director: un enlace de `amazon.com`, un ASIN o un keyword (ej. `ergonomic posture corrector`).
2. Si es keyword, aporta al menos **3 datos verificables** (`user_facts`); si no, el sistema se detiene con `BLOCKED: MISSING_FIELD user_facts`. **Nunca inventa especificaciones.**
3. El Director_devuelve un único resumen ejecutivo con telemetría.
4. Para mejorar una skill: responde `FIX: <crítica>`. El Director hace RCA, bump de versión, actualiza `CHANGELOG.md` y abre un PR (nunca commitea en `main`).

## Inicializar el repositorio en GitHub (un paso)

```sh
bash scripts/init_repo.sh
```

Requiere `gh auth login` previo. Variables opcionales: `GITHUB_OWNER`, `REPO_NAME`, `REPO_VISIBILITY=private|public` (default `private`). En Windows nativo: `powershell -File scripts/init_repo.ps1`. Si `bash` no está en el PATH, usar `& 'C:\Program Files\Git\bin\bash.exe' scripts/init_repo.sh`.

El script: configura hooks, hace commit inicial `chore(skill): bootstrap v1.0.0`, crea/usa el repo, push a `main` y configura GitHub Pages desde `/docs`. **No imprime tokens.**

## Validación y compliance

```sh
python scripts/validate_contracts.py
python tests/run_cold_tests.py
```

Reglas duras: sin precios estáticos en HTML; CTA exacto *"Check Latest Price on Amazon"*; disclosure exacto *"As an Amazon Associate I earn from qualifying purchases."*; sin credenciales en logs/commits; sin `push --force`; sin commit directo a `main`.

## KPIs binarios

1. **KPI 1:** 10 problemas + 10 ganchos + combinación justificada + guion 6×5s con visuales del producto + prompts + 3 preguntas en inglés natural.
2. **KPI 2:** HTML 100% autocontenido, responsive, sin precios y con disclosure visible.
3. **KPI 3:** rutas exactas generadas y listas para `git push` sin edición manual.

## Nota legal

Participamos en el Programa de Afiliados de Amazon. Como Afiliado de Amazon, obtengo ingresos por las compras que cumplen los requisitos. Los precios se muestran de forma dinámica en Amazon; este proyecto nunca los fija en su HTML.
