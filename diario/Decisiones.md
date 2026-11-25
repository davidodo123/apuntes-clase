---
tags: [decisiones]
---
# Decisiones

## Grabar desde el navegador del Mac por túnel SSH
**2026-11-25.** El micro está en el Mac de clase, pero ahí no se quiere instalar nada; todo vive en el PC.
- Alternativas: app o script en el Mac con ffmpeg (requiere instalar); grabar con Notas de voz y subir a mano (pasos manuales, se olvida).
- Elegido: el PC sirve una página en `127.0.0.1:8765`; desde el Mac se abre con `ssh -L 8765:localhost:8765` y el navegador graba con `MediaRecorder`. `localhost` cuenta como origen seguro, así que el navegador permite el micro sin HTTPS.
- El audio se manda cada 10 s, así que si se corta la conexión solo se pierde lo pendiente y se reintenta. El servidor no escucha en la red, solo por el túnel.

## Resumir con claude -p y no con la API
**2026-11-25.** `claude -p` usa la suscripción de Claude Code ya instalada en el PC: sin clave de API ni coste aparte.
- Se lanza con `--setting-sources project`, `--tools ""` y un system prompt propio para que no carguen los hooks ni el estilo de mis sesiones normales.
- `--bare` descartado: exige clave de API.

## Transcribir en local con faster-whisper large-v3
**2026-11-25.** La RTX 5060 Ti (16 GB) mueve `large-v3` en float16 de sobra; gratis, privado y mejor en español que modelos pequeños. Si falla CUDA, cae a CPU con `small`. *(Aparcada: ver [[#Empezar con el modelo small descargado a mano]].)*

## Empezar con el modelo small descargado a mano
**2026-11-25.** La descarga de `large-v3` con `huggingface_hub` se colgaba (hf_xet a 0 MB). David baja `faster-whisper-small` con curl a `modelos/faster-whisper-small/` y el código lo carga desde esa ruta (`WhisperModel(ruta, device="cuda", compute_type="float16")`).
- Si CUDA falla, el mismo modelo pasa a CPU (`int8`) en vez de descargar otro.
- `large-v3` queda pendiente: se probará si `small` se queda corto en clase.
