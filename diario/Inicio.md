---
tags: [inicio]
---
# Apuntes-Clase

Grabadora de clases para mí (David). El micro del Mac de clase graba desde el navegador, el audio viaja por túnel SSH a mi PC con Windows, que lo transcribe con Whisper en la GPU y lo resume con Claude en apuntes de estudio.

- Repo: https://github.com/davidodo123/apuntes-clase
- Web: local, `http://localhost:8765` (solo por túnel SSH, no se publica)

## Cómo funciona
Mac (navegador, sin instalar nada) → túnel `ssh -L 8765:localhost:8765` → `servidor.py` en el PC → `clases/<id>/audio` → faster-whisper `small` local (RTX 5060 Ti) → `transcripcion.md` → `claude -p` → `resumen.md`.

## Fase actual
Fase 1 · Necesario: falta probar desde el Mac (túnel SSH + micro en el navegador) y grabar una clase real.

## Cómo usamos el diario
- [[Roadmap]]: fases y tareas; de aquí sale el progreso del panel.
- [[Ideas]]: bandeja de entrada.
- [[Decisiones]]: qué se decidió y por qué.
- [[Configuración]]: servicios y variables, nunca secretos.
- `Diario/`: una nota por día de trabajo.
