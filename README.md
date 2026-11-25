# Apuntes-Clase

Graba tus clases con el micrófono del Mac, transcríbelas en tu PC con Whisper (GPU) y recibe un resumen en forma de apuntes hecho por Claude.

En el Mac no se instala nada: se usa el navegador a través de un túnel SSH hacia el PC.

```
Mac (navegador + micro) ──ssh -L 8765──▶ PC: servidor.py ─▶ faster-whisper ─▶ claude -p ─▶ resumen.md
```

## Requisitos (PC con Windows)
- Python 3.12, GPU NVIDIA (va también en CPU, más lento)
- Servidor OpenSSH activo
- [Claude Code](https://claude.com/claude-code) con sesión iniciada (`claude` en el PATH)

## Instalación (una vez, en el PC)
```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```
Descarga el modelo de Whisper en `modelos/faster-whisper-small/` (carpeta fuera de git). Para usar otro, pon su ruta en `APUNTES_WHISPER`.

## Uso en clase
1. En el PC, arranca el servidor: `iniciar.bat` (o por SSH: `.venv\Scripts\python servidor.py`).
2. En la Terminal del Mac, abre el túnel y déjalo abierto:
   ```bash
   ssh -N -L 8765:localhost:8765 usuario@ip-del-pc
   ```
3. En el navegador del Mac, abre **http://localhost:8765**, escribe la asignatura y pulsa **Empezar a grabar**. Acepta el permiso del micro.
4. Al acabar, **Parar y resumir**. En unos minutos aparece la clase con su resumen y su transcripción.

Mientras grabas: pestaña abierta, Mac sin suspender (tapa abierta y enchufado). Si se corta el túnel, el audio pendiente se guarda en la pestaña y se reenvía al volver la conexión.

## Dónde queda todo
`clases/<fecha>_<hora>_<asignatura>/` con `audio.*`, `transcripcion.md` y `resumen.md`. Esta carpeta no se sube a git.

Reprocesar una clase: `.venv\Scripts\python procesar.py clases\<carpeta>`

## Ajustes
- `APUNTES_WHISPER`: ruta del modelo de Whisper (por defecto `modelos/faster-whisper-small`)
- `APUNTES_CLAUDE`: modelo del resumen (por defecto `sonnet`)
- El formato del resumen está en `prompt_resumen.md`.
