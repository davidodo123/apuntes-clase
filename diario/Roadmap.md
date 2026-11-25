---
tags: [roadmap]
---
# Roadmap

Regla: se trabaja **una fase cada vez** y no se pasa a la siguiente hasta que David la comprueba.

Leyenda: `[x]` hecho · `[ ]` pendiente · `[/]` empezado · `[-]` descartado

## Fase 1 · Necesario
- [x] Servidor local en el PC que recibe el audio por trozos y lo guarda → [[Decisiones#Grabar desde el navegador del Mac por túnel SSH]]
- [x] Página de grabación: asignatura, elegir micro, nivel, tiempo, reintentos si se corta la conexión
- [x] Transcripción con faster-whisper en la GPU, en español, con marcas de tiempo
- [x] Resumen con `claude -p` en apuntes estructurados → [[Decisiones#Resumir con claude -p y no con la API]]
- [x] Comprobar la GPU con el modelo `small` (audio de prueba): 34 s de audio en 1,8 s; flujo completo por el servidor OK
- [ ] Probar el túnel SSH desde el Mac y que el navegador pida el micro
- [ ] Grabar una clase real de prueba y revisar transcripción y resumen

## Fase 2 · Importante
- [/] Arrancar el servidor sin depender de la sesión SSH: hecho `arrancar.ps1`; falta que arranque solo al encender (tarea programada, pendiente de permiso)
- [ ] Guardar los trozos en el navegador si se cierra la pestaña sin querer
- [ ] Exportar los resúmenes a una bóveda de Obsidian de apuntes por asignatura
- [ ] Buscar entre todas las clases
- [ ] Pasar a un modelo más preciso (`large-v3-turbo` o `large-v3`) si `small` se queda corto

## Fase 3 · Mejoras
- [ ] Distinguir quién habla (profesor / alumnos)
- [ ] Generar tarjetas de repaso a partir de varias clases
