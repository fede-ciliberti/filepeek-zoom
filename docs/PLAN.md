# PLAN — filepeek-zoom

> Documento maestro. Visión, arquitectura, plan por hitos, decisiones y roadmap para retomar el desarrollo.

## Índice

1. [Visión y motivación](#1-visión-y-motivación)
2. [Qué es filepeek y qué agrega este fork](#2-qué-es-filepeek-y-qué-agrega-este-fork)
3. [Arquitectura de filepeek (lo relevante)](#3-arquitectura-de-filepeek-lo-relevante)
4. [El plan: funcionalidades](#4-el-plan-funcionalidades)
5. [Decisiones de diseño](#5-decisiones-de-diseño)
6. [Roadmap](#6-roadmap)
7. [Desarrollo: setup, correr, verificar](#7-desarrollo-setup-correr-verificar)
8. [Sync con upstream](#8-sync-con-upstream)
9. [Anexo: snippets de implementación](#9-anexo-snippets-de-implementación)

---

## 1. Visión y motivación

Cuando el desarrollo de un sistema lo hace mayormente un agente, el humano pierde el modelo mental de la arquitectura. La forma más directa de recuperarlo es **ver los diagramas del sistema**: el modelo entidad-relación, la máquina de estados, la arquitectura de componentes.

Esos diagramas deben ser **artefactos de primera clase** del repo —archivos `.mmd` puros, generados desde la fuente (DB / código), no dibujados a mano— y hay que poder **recorrerlos cómodamente**: arrastrar y hacer zoom, como en [Mermaid Live Editor](https://mermaid.live).

`filepeek` ya sirve la carpeta y renderiza Mermaid, pero **estático**. Este fork agrega la capa de navegación que falta.

**Requisito de Fede (verbatim):** *"poder arrastrar un modelo o hacer zoom de manera sencilla, pero la idea es solo sobre modelos"* — sin notas, sin editar el diagrama, solo pan + zoom.

## 2. Qué es filepeek y qué agrega este fork

**filepeek** (MIT, `thrinz/filepeek`): un `app.py` (FastAPI) + un `static/index.html`. Sirve una carpeta como web navegable y renderiza Markdown, Mermaid, Excel/Word/PowerPoint, HTML, código, imágenes. Un solo operador, self-hosted, sin base de datos.

**Este fork agrega**: pan + zoom a los diagramas Mermaid, usando **`svg-pan-zoom`** — la misma librería que Mermaid Live Editor usa internamente (confirmado en su `src/lib/util/panZoom.ts`). No es "mergear" Mermaid Live (que es una app SvelteKit completa, no un componente); es reusar la pieza correcta.

## 3. Arquitectura de filepeek (lo relevante)

### Backend — `app.py`
- FastAPI. Rutas clave: `/` (shell HTML), `/view`, `/api/file` (contenido), `/api/tree` (árbol, lazy), `/api/raw`, `/api/search/*`.
- Extensiones: `MD_EXTS = {".md", ".markdown"}`; `TEXT_EXTS` **incluye `.mmd` y `.mermaid`** (se sirven como texto).
- El backend es agnóstico al render: manda el texto y el frontend decide cómo mostrarlo.

### Frontend — `static/index.html` (un solo archivo, ~3300 líneas)
- Carga Mermaid desde CDN: `mermaid@11/dist/mermaid.min.js`.
- `MERMAID_EXTS = [".mmd", ".mermaid"]`; `PREVIEW_EXTS` los incluye.
- Panel dedicado **`#mermaid-view`** (un `<div>` full-flex a pantalla completa) — es donde se despliega un `.mmd`.
- `showPanel(...)` dispatchea por tipo: `mermaid → "mermaid-view"`.
- **`renderMermaid(code)`** — renderiza un `.mmd` standalone dentro de `#mermaid-view`.
- **`renderMermaidFences(rootEl)`** — reemplaza los fences ```` ```mermaid ```` dentro de un Markdown renderizado por diagramas inline.

> **Clave**: filepeek **ya renderiza `.mmd` standalone a pantalla completa**. Lo único que falta es el pan/zoom.

## 4. El plan: funcionalidades

### M1 — Pan/zoom en `.mmd` standalone ✅
En `renderMermaid()`, después de `view.innerHTML = svg`, aplicar `svgPanZoom` al `<svg>` resultante, con `controlIconsEnabled: true` (botones de zoom), `fit`, `center`, `minZoom 0.2`, `maxZoom 12`. Cargar `svg-pan-zoom` desde CDN junto a Mermaid. Destruir la instancia previa antes de crear una nueva.

**Resultado**: abrís un `.mmd` → diagrama a pantalla completa con arrastre + zoom.

### M2 — Diagramas inline en Markdown ✅
Implementado como **click-to-expand** (opción b): cada fence ```` ```mermaid ```` en Markdown se renderiza inline y, al hacer click, abre un **lightbox a pantalla completa** con el diagrama + pan/zoom (reusa el helper `applyMermaidPanZoom`). Cierra con el botón ×, click en el fondo, o `Escape`. El inline queda legible; el full es para navegar.

> Nota de diseño: se implementó como **overlay/lightbox autocontenido** (no reusando `#mermaid-view`) para no acoplarse a la lógica de paneles del visor. Verificado: inline renderizado (cursor `zoom-in`), click abre el lightbox con 4 controles, wheel-zoom cambia la escala, `Escape` cierra.

### M3 — Mejoras opcionales ⏳
- Botón "reset view" / "fit".
- Fullscreen nativo (API Fullscreen).
- Persistir zoom/pan por archivo (como hace Mermaid Live con su `PanZoomState`).
- Respetar el tema claro/oscuro en los controles de svg-pan-zoom.

### Fuera de alcance (es del proyecto consumidor, no de la herramienta)
- El **set de diagramas canónicos** y sus **scripts de generación** (ER desde Postgres, máquina de estados desde el código). Viven en el repo del sistema que consume esta herramienta, no acá.

## 5. Decisiones de diseño

| Tema | Decisión | Estado |
|---|---|---|
| Librería de pan/zoom | `svg-pan-zoom` (la de Mermaid Live) | ✅ tomada |
| `.mmd` standalone | Panel full con pan/zoom | ✅ M1 |
| Inline en Markdown | (b) click-to-expand (lightbox overlay) | ✅ tomada |
| Dónde vive `svg-pan-zoom` | CDN (consistente con Mermaid) vs vendor en `static/vendor/` | ⏳ abierta — CDN por simplicidad |
| Botones de control | `controlIconsEnabled: true` (zoom in/out/reset) | ✅ M1 |
| Persistencia de vista | no en M1; evaluar en M3 | ⏳ |

## 6. Roadmap

1. **M1** — pan/zoom standalone. *(hecho)*
2. **M2** — click-to-expand para diagramas inline. *(hecho)*
3. **M3** — pulido: reset/fit, fullscreen, tema, persistencia.
4. **Opcional** — PR al upstream `thrinz/filepeek` (el patch es chico y genérico; podría interesarle).

## 7. Desarrollo: setup, correr, verificar

```bash
./install.sh                                   # crea .venv + deps (fastapi, uvicorn, openpyxl, boto3)
FILEPEEK_ROOT=/ruta/a/diagramas FILEPEEK_PORT=8766 .venv/bin/python app.py
```

- Local: `http://127.0.0.1:8766`, sin auth (binds 127.0.0.1).
- Verificación de frontend: **Playwright** (abrir un `.mmd`, verificar que el SVG tenga la capa de svg-pan-zoom y que los controles existan). `curl` solo confirma que sirve, no que el JS funciona.

## 8. Sync con upstream

```bash
git fetch upstream
git merge upstream/main
```

Nuestro diff se concentra en `static/index.html` (y el `<script>` de svg-pan-zoom). Los conflictos, si aparecen, se resuelven preservando el bloque de pan/zoom.

## 9. Anexo: snippets de implementación

### Carga de la librería (junto a Mermaid, `static/index.html`)
```html
<script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.2/dist/svg-pan-zoom.min.js"></script>
```

### M1 — `renderMermaid()` con pan/zoom
```js
let _mermaidPZ = null;
async function renderMermaid(code) {
  const view = $("mermaid-view");
  view.innerHTML = '<div class="text-slate-400 dark:text-ink-dim text-xs">Rendering diagram…</div>';
  if (!window.mermaid) { /* ... */ return; }
  try {
    const { svg } = await mermaid.render("mmd-" + (++_mermaidSeq), code || "");
    view.innerHTML = svg;
    try {
      if (_mermaidPZ) { _mermaidPZ.destroy(); _mermaidPZ = null; }
      const svgEl = view.querySelector("svg");
      if (svgEl && window.svgPanZoom) {
        // mermaid sale con width="100%" y sin viewBox; svg-pan-zoom necesita un viewBox.
        const bb = svgEl.getBBox();
        if (bb && bb.width && bb.height) {
          svgEl.setAttribute("viewBox", `${bb.x} ${bb.y} ${bb.width} ${bb.height}`);
        }
        // Llenar el panel para que el pan/zoom use toda el área disponible.
        svgEl.setAttribute("width", "100%");
        svgEl.setAttribute("height", "100%");
        svgEl.style.width = "100%";
        svgEl.style.height = "100%";
        svgEl.style.maxWidth = "none";
        _mermaidPZ = svgPanZoom(svgEl, {
          controlIconsEnabled: true, fit: true, center: true,
          minZoom: 0.2, maxZoom: 12,
        });
      }
    } catch (e) { /* pan/zoom es best-effort — si falla, queda el diagrama estático */ }
  } catch (e) { /* ... */ }
}
```

> **Gotchas descubiertos en M1**: (1) `mermaid.render()` devuelve un `<svg width="100%">` **sin `height` ni `viewBox`**. Sin `viewBox`, svg-pan-zoom no calcula el `fit` y los controles quedan fuera de la vista. Se setea `viewBox` desde `svgEl.getBBox()`. (2) El SVG debe **llenar el panel** (`width/height: 100%`); si no, queda del tamaño natural y el pan/zoom no usa toda el área (queda scale 1 y el diagrama recortado). (3) Se agregó un **damero suave** por CSS en `#mermaid-view` para visualizar el canvas. Verificado: canvas lleno, diagrama completo, controles visibles, wheel-zoom cambia la escala.

### Referencia — `PanZoomState` de Mermaid Live (para M2/M3)
Mermaid Live envuelve `svg-pan-zoom` + `hammerjs` en una clase `PanZoomState` (con `zoomIn/zoomOut/reset/restorePanZoom`). Es un buen modelo si en M3 queremos persistir la vista o agregar botones propios.
