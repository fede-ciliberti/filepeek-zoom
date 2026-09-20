# filepeek-zoom

> Fork de [filepeek](https://github.com/thrinz/filepeek) con dos aportes: **pan + zoom** en los diagramas Mermaid (como Mermaid Live) y **navegación de docs** (links e imágenes relativos + anclas de sección). Local, sin pegar nada.

## El problema

`filepeek` sirve una carpeta como web navegable y renderiza Markdown + Mermaid (y Excel, HTML, código…). Es ideal para leer lo que escribe un agente. **Pero sus diagramas son estáticos**: no se pueden arrastrar ni hacer zoom.

Y hay una necesidad distinta a "leer docs": tener una carpeta de **diagramas canónicos del sistema** — el modelo entidad-relación, la máquina de estados, la arquitectura — como artefactos propios (`.mmd` puros, sin prosa), y poder **recorrerlos** cómodamente.

Además, un Markdown con **links cruzados** entre documentos (índices, referencias a otras secciones) se rompe al servirlo: los links e imágenes relativos resuelven contra `/` y dan 404, y los `#ancla` de sección no tienen destino.

## La solución

**Diagramas.** Agregar a los diagramas Mermaid la misma capa de navegación que usa [Mermaid Live Editor](https://mermaid.live): la librería [`svg-pan-zoom`](https://github.com/bumbu/svg-pan-zoom) (+ `hammerjs` para touch). No hay que "mergear" nada: Mermaid Live solo la usa; es pública y standalone.

**Documentos.** Un Markdown servido por filepeek tiene links e imágenes relativos que, sin tratar, resuelven contra `/` y dan 404. El fork los reescribe a las rutas internas (`/?path=` para navegar, `/api/raw?path=` para imágenes) y genera `id` estilo GitHub en los headings, así los `#ancla` de sección funcionan y navegan in-app sin recargar.

## Estado

| Hito | Qué | Estado |
|---|---|---|
| M1 | Pan/zoom en `.mmd` standalone (panel a pantalla completa) | ✅ |
| M2 | Diagramas inline en Markdown → click-to-expand con pan/zoom | ✅ |
| M3 | Controles extra / fullscreen / temas | ⏳ |
| M4 | Navegación de docs: links/imágenes relativos + anclas de sección | ✅ |

Detalle completo en **[`docs/PLAN.md`](docs/PLAN.md)**.

## Quickstart

```bash
./install.sh
FILEPEEK_ROOT=/ruta/a/los/diagramas FILEPEEK_PORT=8766 .venv/bin/python app.py
```

Abrí `http://localhost:8766`, navegá a un `.mmd` → se despliega a pantalla completa con controles de zoom y arrastre.

### Lanzador `filepeek`

Desde cualquier carpeta de un proyecto, `filepeek` levanta el servidor en segundo plano sirviendo ese proyecto y abre el navegador directo en su carpeta de diagramas (`docs/diagrams`, `diagrams` o `docs/diagramas` — la primera que tenga `.mmd`). `filepeek stop` lo apaga.

```bash
ln -s /ruta/a/filepeek-zoom/bin/filepeek ~/.local/bin/filepeek  # una sola vez
cd ~/Trabajos/MiProyecto && filepeek          # arranca (o reabre si ya corría)
filepeek --port 8770 --no-open                # variantes
filepeek stop                                 # apaga la instancia de este proyecto
```

El estado vive en `~/.cache/filepeek/<proyecto>/` (`pid`, `port`, `log`). Un `.filepeek` opcional en la raíz del proyecto acepta `root=`, `port=`, `host=`, `open=`.

## Base

- Fork de `filepeek` (MIT). Upstream: `thrinz/filepeek` (remote `upstream`).
- Commit base: `839a156`.

## Documentación

- **[`docs/PLAN.md`](docs/PLAN.md)** — documento maestro (visión, arquitectura de filepeek, plan, roadmap, sync upstream).
- **[`AGENTS.md`](AGENTS.md)** — reglas para retomar el desarrollo con un agente.

## Licencia

MIT, heredada de filepeek.
