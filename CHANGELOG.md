# Changelog

Todas las mejoras se registran aquí. Formato semántico: `feat(skill): ...` / `fix(skill): ...` / `chore(skill): ...`.

## [v1.0.0] - 2026-11-26

### Bootstrap (Fases 1–6)
- Inicialización de arquitectura base del monorepo y memoria de estado.
- `feat(skill)`: 4 skills con 9 bloques blindados (Directora INTERACTIVE + 3 workers HEADLESS).
- `feat(skill)`: contratos versionados con `run_id`, `input_sha256` y `producer` para evitar pérdida de contexto entre workers.
- `feat(skill)`: fail-closed ante datos no verificables (`BLOCKED: MISSING_FIELD`), sin invención de specs.
- `feat(skill)`: `scripts/validate_contracts.py` (linter de contratos + compliance Amazon Associates).
- `feat(skill)`: `.githooks/pre-commit` con escaneo de secretos (valores nunca impresos).
- `feat(skill)`: `scripts/init_repo.sh` y `scripts/init_repo.ps1` para bootstrap en un paso + Pages desde `/docs`.
- `feat(skill)`: `scripts/self_upgrade.sh` (`GIT_SELF_UPGRADE`) con bump semver, CHANGELOG y PR en rama `skill/auto-*`.
- `feat(skill)`: `tests/run_cold_tests.py` con 4 pruebas adversariales (happy, degradado/offline, estrés, inyección).
- `chore(skill)`: landing demo autocontenida en `docs/index.html` con disclosure y CTA dinámico.
- Configuración preservada: Associate Tag `vettedgearlab-20`, marketplace US, `allow_static_prices=false`.
