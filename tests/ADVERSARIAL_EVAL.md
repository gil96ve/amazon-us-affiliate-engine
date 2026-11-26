# Auditoría Adversarial en Frío — v1.0.0

Fecha: 2026-11-26. Comandos ejecutados en el monorepo:

```sh
python scripts/validate_contracts.py
python tests/run_cold_tests.py
```

## Resultado final

| Prueba | Score | Evidencia |
|---|---|---|
| **T1 Happy Path** | **10/10** | `ok=True`, 0 errores, 1 producto y 1 asset validados; linter de compliance limpio. |
| **T2 Degradado / Offline Fallback** | **10/10** | 3 bloqueos deterministas (`MISSING_FILE`, `EMPTY_FIELD`, `MISSING_FIELD last_updated`); `logs/offline_queue.jsonl` preservado byte-a-byte; sin excepción. |
| **T3 Estrés de Contexto** | **10/10** | 20.941 caracteres en dolores + voiceovers largos; 10/10 dolores, 10/10 hooks, 6×5s = 30s; sin pérdida de restricciones. |
| **T4 Adversarial / Security** | **10/10** | `SECRET_EXPOSED`, `STATIC_PRICE` y `PROMPT_INJECTION` detectados en los tres vectores; ningún valor sensible impreso. |

`all_pass: true`

## Hallazgos corregidos durante la auditoría

1. **BOM UTF-8** en JSON/HTML escritos por el entorno → lectores migrados a `utf-8-sig` en `validate_contracts.py`, `bump_version.py` y `run_cold_tests.py`.
2. **Aserción de T4 demasiado estricta** (comparación de lista exacta en vez de substring) → corregida; el linter ya detectaba correctamente los 3 vectores.
3. **Regex de bump** con `\b` no reconocía `v1.0.0` → sustituido por `(?<![\d.])(\d+)\.(\d+)\.(\d+)(?![\d.])`; verificado: `v1.0.0 → v1.0.1`.
4. **Tipos de sintaxis** en `self_upgrade.sh` → corregido.

## Mapeo FMEA ↔ prueba

- F1 (conflictos de commit) → cubierto por diseño (escritor único + staging + rebase con abort) y por T2 (cola offline).
- F2 (pérdida de contexto) → T1/T3 validan `run_id`, `input_sha256` y contratos completos.
- F3 (invención de specs) → T2 confirma que un `evidence` vacío bloquea la cadena.
- F4 (secretos) → T4 vector 1 + hook `.githooks/pre-commit`.
- F5 (compliance Amazon) → T4 vector 2 + linter en CI.
