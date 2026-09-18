# filepeek-zoom

> Fork de [filepeek](https://github.com/thrinz/filepeek) que agrega **pan + zoom** a los diagramas Mermaid, para navegar los **diagramas-modelo de un sistema** con la comodidad de Mermaid Live — local, sin pegar nada.

## El problema

`filepeek` sirve una carpeta como web navegable y renderiza Markdown + Mermaid (y Excel, HTML, código…). Es ideal para leer lo que escribe un agente. **Pero sus diagramas son estáticos**: no se pueden arrastrar ni hacer zoom.

Y hay una necesidad distinta a "leer docs": tener una carpeta de **diagramas canónicos del sistema** — el modelo entidad-relación, la máquina de estados, la arquitectura — como artefactos propios (`.mmd` puros, sin prosa), y poder **recorrerlos** cómodamente.

## La solución

Agregar a los diagramas Mermaid la misma capa de navegación que usa [Mermaid Live Editor](https://mermaid.live): la librería [`svg-pan-zoom`](https://github.com/bumbu/svg-pan-zoom) (+ `hammerjs` para touch). No hay que "mergear" nada: Mermaid Live solo la usa; es pública y standalone.

## Estado

| Hito | Qué | Estado |
|---|---|---|
| M1 | Pan/zoom en `.mmd` standalone (panel a pantalla completa) | ✅ |
| M2 | Diagramas inline en Markdown → click-to-expand con pan/zoom | ✅ |
| M3 | Controles extra / fullscreen / temas | ⏳ |

Detalle completo en **[`docs/PLAN.md`](docs/PLAN.md)**.

## Quickstart

```bash
./install.sh
FILEPEEK_ROOT=/ruta/a/los/diagramas FILEPEEK_PORT=8766 .venv/bin/python app.py
```

Abrí `http://localhost:8766`, navegá a un `.mmd` → se despliega a pantalla completa con controles de zoom y arrastre.

## Base

- Fork de `filepeek` (MIT). Upstream: `thrinz/filepeek` (remote `upstream`).
- Commit base: `839a156`.

## Documentación

- **[`docs/PLAN.md`](docs/PLAN.md)** — documento maestro (visión, arquitectura de filepeek, plan, roadmap, sync upstream).
- **[`AGENTS.md`](AGENTS.md)** — reglas para retomar el desarrollo con un agente.

## Licencia

MIT, heredada de filepeek.
