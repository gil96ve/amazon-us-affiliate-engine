# Motor de Auto-Evolución (Fase 5)

## 1. Telemetría adaptativa (solo `INTERACTIVE`)

El Director siempre cierra con:

```text
[TELEMETRÍA | Confianza: X% | Repo Sync: OK/Pendiente] — ¿Qué ajustarías? (Usa "FIX: [crítica]" para auto-actualizar la Skill en GitHub).
```

`Repo Sync: Pendiente` significa que los artefactos están en `data/staging/` y en `logs/offline_queue.jsonl`; **no** que se hayan perdido.

## 2. Diagnóstico de Causa Raíz (RCA)

Ante `FIX: <crítica>` o un fallo detectado por el linter:

1. Identificar el bloque `[01..09]` de la skill implicada que produjo el fallo.
2. Traducir la crítica a una regla concreta (afirmativa o negativa).
3. Comprobar si ya existe contramedida en el FMEA (`tests/ADVERSARIAL_EVAL.md`).
4. Decidir el bump: `patch` (texto/regla), `minor` (nuevo campo o comportamiento), `major` (cambio de contrato).
5. Añadir un caso de regresión a `tests/run_cold_tests.py` si el fallo es reproducible.

## 3. GIT_SELF_UPGRADE

```sh
bash scripts/self_upgrade.sh skills/02_SKILL_VIRAL_SCRIPTER.md patch "fix(skill): ajustar ganchos de retencion"
```

Efectos: bump semver en la skill y en `data/state_memory.json`, entrada nueva en `CHANGELOG.md`, commit con mensaje semántico en rama `skill/auto-*`, validación de contratos, push y PR a `main`. Si GitHub no responde, emite `HANDOFF` con los comandos exactos. **Nunca** commit directo a `main`, **nunca** `--force`.

## 4. Política de versionado

| Versión | Cuándo |
|---|---|
| `v1.0.0` | Bootstrap del ecosistema (actual). |
| `v1.0.x` | Ajustes de reglas, copy, thresholds y correcciones. |
| `v1.x.0` | Nuevos campos en contratos o nueva herramienta de validación. |
| `v2.0.0` | Cambio rompiente de `schema_version` (requiere migración de `data/`). |

## 5. Rollback

Si una PR degradó los KPIs: revertir el commit de la rama `skill/auto-*` y re-ejecutar `python tests/run_cold_tests.py`. El estado anterior queda en el historial de `CHANGELOG.md`.
