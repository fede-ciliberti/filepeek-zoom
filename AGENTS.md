# AGENTS.md — filepeek-zoom

> Fork de [filepeek](https://github.com/thrinz/filepeek) (MIT, remote `upstream`) que agrega **pan/zoom** (svg-pan-zoom) a los diagramas Mermaid. Herramienta de desarrollo, independiente de cualquier proyecto consumidor.

## Estructura

- `app.py` — backend FastAPI entero (sin build; `backup.py` es el único módulo aparte).
- `static/index.html` — frontend entero en un solo archivo (~3400 líneas, sin build ni bundler).
- `bin/filepeek` — lanzador bash global, puramente aditivo (no toca `app.py` ni `index.html`).
- `docs/PLAN.md` — documento maestro (visión, arquitectura, hitos, decisiones). Leelo antes de tocar Mermaid.
- No hay linter, formatter ni typecheck configurados. CI: Python 3.10 + 3.12.

## Comandos

```bash
./install.sh
FILEPEEK_ROOT=<carpeta> FILEPEEK_PORT=8766 .venv/bin/python app.py
```

- Puerto del fork: **8766** (el 8765 del upstream suele estar ocupado). Default upstream: 8765.
- Sin auth en local. `app.py` **se niega a bindear fuera de localhost** sin `FILEPEEK_PASSWORD_HASH` o `FILEPEEK_TOKEN` — no intentes `0.0.0.0` para probar.
- `bin/filepeek` también rechaza `host=0.0.0.0`; estado por proyecto en `~/.cache/filepeek/`.

## Tests

```bash
.venv/bin/python -m pytest -v        # unit + API (default, excluye e2e)
.venv/bin/python -m pytest -v -m e2e # browser (requiere: playwright install chromium)
```

- `pytest.ini` ya excluye `e2e` por defecto (`addopts = -m "not e2e"`).
- `tests/conftest.py`: la app lee `ROOT`/`STATE_DIR`/auth como **globals al importar** — los tests los cambian con `monkeypatch`, no con env vars. Seguí ese patrón. Solo `test_e2e.py` usa env vars (`FILEPEEK_ROOT`, `FILEPEEK_STATE_DIR`) + subprocess real con `--port`.
- Deps de test: `requirements-dev.txt` (httpx, moto[s3], playwright).

## Dónde vive el aporte del fork

Todo el pan/zoom está en `static/index.html`:

- `applyMermaidPanZoom(container)` — helper compartido (lo usan ambos renders).
- `renderMermaid()` → panel `#mermaid-view` (standalone `.mmd`).
- `renderMermaidFences()` + `open/closeMermaidLightbox()` → overlay `#mermaid-lightbox` (fences ` ```mermaid ` en Markdown, click-to-expand).
- `MERMAID_EXTS` (front) y `TEXT_EXTS` (back, `app.py`) — si agregás una extensión de diagrama, tocá **ambas**.
- Carga de la lib: `<script>` CDN de `svg-pan-zoom` junto al de Mermaid (línea ~26).

## Gotchas verificados

- **El SVG de Mermaid sale sin `viewBox`** (`width="100%"`, sin height). Sin setear `viewBox` desde `getBBox()` + `width/height: 100%`, `svg-pan-zoom` no calcula el `fit` y los controles quedan fuera de vista. Ya resuelto en el helper — no lo rompas.
- Pan/zoom es **best-effort** (try/catch con fallback a diagrama estático). Mantenelo así.
- **Diff chico y localizado**: no reescribas frontend ni backend; cambios aditivos y aislados para que `git merge upstream/main` sea trivial. Conflictos típicos: `static/index.html` (preservá el bloque pan/zoom) y `README.md` (el nuestro reemplaza al del upstream).
- **Verificación de frontend con Playwright** (abrir un `.mmd`, chequear la capa de svg-pan-zoom y los controles). `curl` solo confirma que sirve, no que el JS anda.
- Env vars que importan: `FILEPEEK_ROOT`, `FILEPEEK_PORT`/`HOST`, `FILEPEEK_STATE_DIR` (estado separado por proyecto), `FILEPEEK_PASSWORD_HASH`/`TOKEN`/`SECRET`. El estado (`permlinks/bookmarks/recents/auth.json`, `backup_config.json` con secreto S3) vive en `STATE_DIR` y está gitignoreado — nunca lo commitees, ni `.env` ni credenciales.
