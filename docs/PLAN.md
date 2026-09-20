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
10. [Lanzador `bin/filepeek`](#10-lanzador-binfilepeek)

---

## 1. Visión y motivación

Cuando el desarrollo de un sistema lo hace mayormente un agente, el humano pierde el modelo mental de la arquitectura. La forma más directa de recuperarlo es **ver los diagramas del sistema**: el modelo entidad-relación, la máquina de estados, la arquitectura de componentes.

Esos diagramas deben ser **artefactos de primera clase** del repo —archivos `.mmd` puros, generados desde la fuente (DB / código), no dibujados a mano— y hay que poder **recorrerlos cómodamente**: arrastrar y hacer zoom, como en [Mermaid Live Editor](https://mermaid.live).

`filepeek` ya sirve la carpeta y renderiza Mermaid, pero **estático**. Este fork agrega la capa de navegación que falta para los diagramas.

La segunda motivación es más terrenal: al usar filepeek sobre una carpeta de docs con **links cruzados**, los links e imágenes relativos daban 404 y los índices con `#ancla` no tenían destino. El fork también arregla eso (ver M4).

**Requisito de Fede (verbatim):** *"poder arrastrar un modelo o hacer zoom de manera sencilla, pero la idea es solo sobre modelos"* — sin notas, sin editar el diagrama, solo pan + zoom.

## 2. Qué es filepeek y qué agrega este fork

**filepeek** (MIT, `thrinz/filepeek`): un `app.py` (FastAPI) + un `static/index.html`. Sirve una carpeta como web navegable y renderiza Markdown, Mermaid, Excel/Word/PowerPoint, HTML, código, imágenes. Un solo operador, self-hosted, sin base de datos.

**Este fork agrega** dos cosas, ambas en `static/index.html`:

1. **Pan + zoom a los diagramas Mermaid**, usando **`svg-pan-zoom`** — la misma librería que Mermaid Live Editor usa internamente (confirmado en su `src/lib/util/panZoom.ts`). No es "mergear" Mermaid Live (que es una app SvelteKit completa, no un componente); es reusar la pieza correcta.
2. **Navegación de documentos Markdown**: los links e imágenes relativos se reescriben a las rutas internas de filepeek y los headings llevan `id` estilo GitHub, así los links cruzados entre docs y los `#ancla` de sección funcionan (antes daban 404 o no tenían destino).

## 3. Arquitectura de filepeek (lo relevante)

### Backend — `app.py`
- FastAPI. Rutas clave: `/` (shell HTML), `/view`, `/api/file` (contenido), `/api/tree` (árbol, lazy), `/api/raw`, `/api/search/*`.
- Extensiones: `MD_EXTS = {".md", ".markdown"}`; `TEXT_EXTS` **incluye `.mmd` y `.mermaid`** (se sirven como texto).
- El backend es agnóstico al render: manda el texto y el frontend decide cómo mostrarlo.

### Frontend — `static/index.html` (un solo archivo, ~3400 líneas)
- Carga desde CDN: Mermaid (`mermaid@11`), `svg-pan-zoom`, `hammerjs` (touch) y `marked-gfm-heading-id`.
- `MERMAID_EXTS = [".mmd", ".mermaid"]`; `PREVIEW_EXTS` los incluye.
- Panel dedicado **`#mermaid-view`** (un `<div>` full-flex a pantalla completa) — es donde se despliega un `.mmd`.
- `showPanel(...)` dispatchea por tipo: `mermaid → "mermaid-view"`.
- **`renderMermaid(code)`** — renderiza un `.mmd` standalone dentro de `#mermaid-view`.
- **`renderMermaidFences(rootEl)`** — reemplaza los fences ```` ```mermaid ```` dentro de un Markdown renderizado por diagramas inline.
- **`rewriteRelativeLinks(container, basePath)`** — reescribe links/imágenes relativos del Markdown a las rutas internas de filepeek (navegación de docs, ver M4).
- **`marked-gfm-heading-id`** — extensión de marked que agrega `id` estilo GitHub a los headings, habilitando las anclas `#seccion`.

> **Clave**: filepeek **ya renderiza `.mmd` standalone a pantalla completa**. Lo único que falta para los diagramas es el pan/zoom.

## 4. El plan: funcionalidades

### M1 — Pan/zoom en `.mmd` standalone ✅
En `renderMermaid()`, después de `view.innerHTML = svg`, aplicar `svgPanZoom` al `<svg>` resultante, con `controlIconsEnabled: true` (botones de zoom), `fit`, `center`, `minZoom 0.2`, `maxZoom 12`. Cargar `svg-pan-zoom` desde CDN junto a Mermaid. Destruir la instancia previa antes de crear una nueva.

**Resultado**: abrís un `.mmd` → diagrama a pantalla completa con arrastre + zoom.

### M2 — Diagramas inline en Markdown ✅
Implementado como **click-to-expand** (opción b): cada fence ```` ```mermaid ```` en Markdown se renderiza inline y, al hacer click, abre un **lightbox a pantalla completa** con el diagrama + pan/zoom (reusa el helper `applyMermaidPanZoom`). Cierra con el botón ×, click en el fondo, o `Escape`. El inline queda legible; el full es para navegar.

> Nota de diseño: se implementó como **overlay/lightbox autocontenido** (no reusando `#mermaid-view`) para no acoplarse a la lógica de paneles del visor. Verificado: inline renderizado (cursor `zoom-in`), click abre el lightbox con 4 controles, wheel-zoom cambia la escala, `Escape` cierra.

> **Responsive y presentación**: el lightbox **re-encaja** el diagrama al redimensionar la ventana (debounced; respeta el zoom/pan manual del usuario vía el flag `_pzDirty`), **bloquea el scroll del body** mientras está abierto, y el overlay usa fondo `rgba(0,0,0,.8)` + `backdrop-blur`. El canvas del lightbox tiene **fondo claro** (`bg-slate-50 dark:bg-ink-bg`): sobre el damero oscuro los conectores del diagrama quedaban casi invisibles.

### M3 — Mejoras opcionales ⏳
- Botón "reset view" / "fit".
- Fullscreen nativo (API Fullscreen).
- Persistir zoom/pan por archivo (como hace Mermaid Live con su `PanZoomState`).
- Respetar el tema claro/oscuro en los controles de svg-pan-zoom.

### M4 — Navegación de documentos ✅
No estaba en el plan original: apareció al usar filepeek sobre una carpeta de docs con links cruzados. Dos problemas, dos fixes:

- **Links e imágenes relativos.** `marked.parse()` emitía el `href` crudo, así que un link como `docs/01-vision.md` resolvía contra `/` → 404. `rewriteRelativeLinks()` reescribe `a[href]` a `/?path=<resuelto>` e `img[src]` a `/api/raw?path=<resuelto>`, resolviendo `.`/`..` contra la carpeta del archivo actual. Deja intactos externos, protocol-relative, anclas puras (`#`), links ya en formato filepeek y `/api/`.
- **Anclas de sección.** marked no generaba `id` en los headings (los `#seccion` no tenían destino) y `syncUrl()` borraba el fragmento de la URL. Se agregó la extensión oficial **`marked-gfm-heading-id`** (ids estilo GitHub, así los links existentes funcionan sin tocarlos), click in-app sin recarga vía `openFromUrl()`, y `_pendingHash` + `scrollToHash()` para scrollear al heading tras renderizar.

**Resultado**: un Markdown con links relativos e índices con anclas se navega entero dentro del visor, sin recargas ni 404.

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
| Ids de headings | extensión oficial `marked-gfm-heading-id` (estilo GitHub) | ✅ M4 |
| `#fragmento` en links reescritos | fuera del `?path=` (si no, el backend busca un archivo con `#` en el nombre → 404) | ✅ M4 |

## 6. Roadmap

1. **M1** — pan/zoom standalone. *(hecho)*
2. **M2** — click-to-expand para diagramas inline. *(hecho)*
3. **M3** — pulido: reset/fit, fullscreen, tema, persistencia.
4. **M4** — navegación de documentos: links/imágenes relativos + anclas de sección. *(hecho, fuera del plan original)*
5. **Opcional** — PR al upstream `thrinz/filepeek` (los patches son chicos y genéricos; podrían interesarle).

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

Nuestro diff se concentra en `static/index.html` (los `<script>` de CDN y los bloques de pan/zoom y de navegación de docs). Los conflictos, si aparecen, se resuelven preservando esos bloques.

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

### M4 — Puntos no obvios de la navegación
El código completo vive en `static/index.html` (`rewriteRelativeLinks()`); acá solo lo que no se deduce leyéndolo:

- **Lista de skip** de `rewriteRelativeLinks()`: deja intactos los `href` que matchean `^(?:[a-z][a-z0-9+.-]*:|\/\/|#|\/\?path=|\/view\?path=|\/api\/)` — esquemas (`https:`), protocol-relative, anclas puras, links ya en formato filepeek y rutas de API. Para `img[src]` el skip es `^(?:[a-z][a-z0-9+.-]*:|\/\/|\/static\/|\/api\/)`.
- **El `#fragmento` se separa ANTES del encoding**: `encodeURIComponent(path + frag)` mete el `#` en el path y el backend busca un archivo con `#` en el nombre → 404. Se resuelve el path, se codifica, y el fragmento se concatena crudo.
- **`data-fp-path` / `data-fp-frag`**: el handler de click los lee para navegar in-app (`openFromUrl()`) sin recarga y conservar el fragmento.

---

## 10. Lanzador `bin/filepeek`

Script bash autocontenido (sin deps más allá de bash + coreutils + `xdg-open`) para usar filepeek como herramienta global: parado en cualquier proyecto, `filepeek` lo sirve y abre el navegador directo en sus diagramas.

**Comportamiento**:
- **Proyecto**: `$FILEPEEK_ROOT` si está seteado → raíz del repo git → `$PWD`. Un `.filepeek` opcional en la raíz acepta `root=`, `port=`, `host=`, `open=` (ignora claves desconocidas y `#` comentarios).
- **Landing**: primera carpeta que exista y contenga un `.mmd`/`.mermaid` (recursivo, sin `.git`/`.venv`/`node_modules`) entre `docs/diagrams`, `diagrams`, `docs/diagramas`. Si ninguna califica, abre `/`. Usa el deep-link `/?path=<rel>` que ya soporta el frontend.
- **Puerto**: `--port N` → `$FILEPEEK_PORT` → `.filepeek` `port=` → `8766`. Si está ocupado, sube hasta `8799` y avisa por stderr (el aviso va a stderr para no romper el `FILEPEEK_PORT` que lee `app.py`).
- **Idempotencia**: estado por proyecto en `~/.cache/filepeek/<slug>-<hash>/` (`pid`, `port`, `log`, `root`). Si el pid sigue vivo y su cmdline/environ coinciden con nuestro `app.py` + root, no arranca otro: reimprime la URL y reabre el navegador. El chequeo de idempotencia corre antes de escanear puertos, así la segunda corrida reusa el puerto guardado.
- **Arranque**: `setsid .venv/bin/python app.py` con el log al archivo de estado y `FILEPEEK_STATE_DIR` propio por proyecto (bookmarks/recents no se mezclan). Sin `.venv`, falla con mensaje claro (correr `./install.sh`).
- **`stop`**: mata solo el pid registrado y solo si pasa el chequeo de propiedad; después borra el pid. Nunca `pkill` por nombre, nunca toca otros proyectos.
- **Bind**: siempre `127.0.0.1` (un `host=0.0.0.0` en el config se rechaza con aviso).

**Decisiones**: no toca `app.py` ni `static/index.html` (puramente aditivo, diff chico per reglas del fork); el symlink global vive en `~/.local/bin/filepeek` (fuera del repo).
