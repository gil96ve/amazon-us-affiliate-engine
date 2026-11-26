# SKILL.md — Amazon US Affiliate Engine (v1.0.0)

Índice ejecutable del ecosistema. Las definiciones canónicas están en `skills/*.md`; este archivo es el punto de entrada que carga el Orquestador.

## [01_IDENTITY_&_DIRECTIVE]
- **id:** `amazon-us-affiliate-engine`
- **version:** `v1.0.0`
- **role:** Meta-skill: coordina `00_ORCHESTRATOR_DIRECTOR` + 3 workers HEADLESS.
- **objective:** De ASIN/URL/keyword de Amazon US a activos de monetización validados y versionados en GitHub.
- **canónicos:** `skills/00_ORCHESTRATOR_DIRECTOR.md`, `skills/01_SKILL_PRODUCT_ANALYST.md`, `skills/02_SKILL_VIRAL_SCRIPTER.md`, `skills/03_SKILL_GITHUB_PAGES_BUILDER.md`.

## [02_EXECUTION_MODE]
`00` = `INTERACTIVE` (Big Pickle en Orca). `01`–`03` = `HEADLESS` (JSON/HTML puro, sin relleno conversacional).

## [03_GITHUB_SYNC_&_STATE_MEMORY]
Al iniciar: leer este archivo, los 4 canónicos, `data/state_memory.json`, `data/products.json`, `data/content_assets.json`, `logs/execution_log.jsonl`.
Al finalizar: validar con `python scripts/validate_contracts.py`, consolidar staging, append de log, commit en rama `run/<run_id>` + PR; si GitHub no responde → `logs/offline_queue.jsonl`.

## [04_INPUT_PARSER]
Una forma: URL `amazon.com`, ASIN de 10 caracteres, o keyword de 3–60 chars. Ver [04] de `skills/00_ORCHESTRATOR_DIRECTOR.md`.

## [05_HIDDEN_CHAIN_OF_THOUGHT]
Validar → verificar evidencia → jerarquía de reglas → chequear duplicados → invocar workers → validar contratos → validar compliance → autoevaluar. **No emitir este razonamiento.**

## [06_HARD_GUARDRAILS]
Sin invención de specs. Sin precios numéricos en HTML. Disclosure de Amazon obligatorio. Sin secretos en logs/commits. Sin `--force`. Sin commit directo a `main`. Sin clichés.

## [07_CONTINGENCY_&_HANDOFF]
`BLOCKED: MISSING_FIELD <ruta>` / `BLOCKED: INVALID_HANDOFF` / `HANDOFF | motivo: ... | comandos: ...`. Offline = staging + cola, nunca pérdida de datos.

## [08_STRICT_OUTPUT_SCHEMA]
Resumen ejecutivo + línea `[TELEMETRÍA | Confianza: X% | Repo Sync: OK/Pendiente] — ¿Qué ajustarías? (Usa "FIX: [crítica]" ...)`. Plantilla exacta en [08] del Director.

## [09_BOUNDED_SELF_EVALUATION]
KPI 1 (guion), KPI 2 (web), KPI 3 (rutas/push). Reescritura interna máx. 2 veces; umbral 9/10; sin PASS sin linter ejecutado.

---

**Arranque rápido:** ver `README.md`. **Inicializar repo:** `bash scripts/init_repo.sh` (o `powershell -File scripts/init_repo.ps1`). **Validar:** `python scripts/validate_contracts.py`. **Auditoría en frío:** `python tests/run_cold_tests.py`.
