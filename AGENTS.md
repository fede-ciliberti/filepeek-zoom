# AGENTS.md — filepeek-zoom

> Fork de `filepeek` que agrega **pan/zoom** (svg-pan-zoom) a los diagramas Mermaid. Es una **herramienta de desarrollo**, independiente de cualquier proyecto consumidor (no pertenece a ningún repo de producto).

## Qué es este repo

- Fork de [filepeek](https://github.com/thrinz/filepeek) (MIT). El upstream está configurado como remote `upstream`.
- Un `app.py` (backend FastAPI) + un `static/index.html` (frontend entero en un solo archivo).
- **Objetivo**: que los diagramas Mermaid —`.mmd` standalone y fences inline en Markdown— tengan **pan + zoom**, para recorrer los diagramas-modelo de un sistema.

## Reglas duras

- **Diff chico y localizado.** Es un fork: mantener los cambios acotados para que `git merge upstream/main` sea trivial. **No** reescribir el frontend ni el backend; los cambios son aditivos y aislados.
- **No tocar lo que no hace falta.** El upstream se mantiene tal cual; nuestro aporte vive en puntos concretos (ver "Dónde vive cada cosa").
- **Idioma**: español rioplatense en docs y comentarios nuevos.
- **No secretos** en el repo.
- **Verificación visual**: los cambios de frontend se validan abriendo el navegador (Playwright), no solo con curl.

## Dónde vive cada cosa

| Qué | Dónde |
|---|---|
| Backend: rutas, tipos de archivo | `app.py` |
| Frontend: UI, paneles, render Mermaid | `static/index.html` |
| Render Mermaid standalone | `renderMermaid()` en `static/index.html` |
| Render Mermaid inline (fences) | `renderMermaidFences()` en `static/index.html` |
| Panel del diagrama standalone | `#mermaid-view` en `static/index.html` |
| Extensiones Mermaid | `MERMAID_EXTS` (front) y `TEXT_EXTS` (back) |

## Cómo correr

```bash
./install.sh
FILEPEEK_ROOT=<carpeta-a-servir> FILEPEEK_PORT=8766 .venv/bin/python app.py
```

`127.0.0.1:8766` por defecto (el 8765 suele estar tomado por otros servicios locales). Sin auth en modo local.

## Cómo sincronizar con upstream

```bash
git fetch upstream
git merge upstream/main      # o git rebase upstream/main
```

Si hay conflicto, suele ser en `static/index.html` (nuestro punto de parche) o en `README.md` (lo reemplazamos por uno propio del fork). Resolver preservando el bloque de pan/zoom.

## Documento maestro

Ver **[`docs/PLAN.md`](docs/PLAN.md)** para visión, arquitectura de filepeek, plan por hitos, decisiones de diseño y roadmap.
