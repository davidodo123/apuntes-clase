---
tags: [configuracion]
---
# Configuración

## Servicios
- **PC (Windows):** servidor OpenSSH activo (`sshd`, arranque automático). `servidor.py` escucha en `127.0.0.1:8765`.
- **Mac de clase:** solo navegador (Chrome o Safari) y Terminal para el túnel.
- **Claude Code** en el PC (`claude -p`), con la sesión de la suscripción iniciada.

## Variables de entorno (opcionales)
- `APUNTES_WHISPER`: ruta del modelo de Whisper (por defecto `modelos/faster-whisper-small`).
- `APUNTES_CLAUDE`: modelo de Claude para el resumen (por defecto `sonnet`).

## Datos
- `modelos/` guarda los modelos de Whisper descargados a mano con curl. **No se sube a git.**
- `clases/` guarda audio, transcripción y resumen de cada clase. **No se sube a git** (está en `.gitignore`).
