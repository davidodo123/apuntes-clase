"""Transcribe el audio de una clase con faster-whisper y lo resume con `claude -p`.

Uso suelto (reprocesar una clase ya grabada):
    .venv\\Scripts\\python procesar.py clases\\2026-11-25_0900_historia
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PROMPT_RESUMEN = (RAIZ / "prompt_resumen.md").read_text(encoding="utf-8")

# Ruta a un modelo ya descargado (relativa a la carpeta del proyecto) o nombre de modelo del hub.
MODELO_WHISPER = os.environ.get("APUNTES_WHISPER", "modelos/faster-whisper-small")


def _ruta_modelo() -> str:
    local = RAIZ / MODELO_WHISPER
    if local.is_dir():
        return str(local)
    if "/" in MODELO_WHISPER or "\\" in MODELO_WHISPER:
        raise FileNotFoundError(f"No encuentro el modelo de Whisper en {local}")
    return MODELO_WHISPER  # nombre del hub (p. ej. "large-v3"): lo descarga faster-whisper
MODELO_CLAUDE = os.environ.get("APUNTES_CLAUDE", "sonnet")


def _preparar_dlls_cuda() -> None:
    """En Windows, las DLL de cuBLAS/cuDNN vienen en los paquetes pip nvidia-*."""
    if os.name != "nt":
        return
    import site

    for base in site.getsitepackages():
        nvidia = Path(base) / "nvidia"
        if not nvidia.is_dir():
            continue
        for bin_dir in nvidia.glob("*/bin"):
            os.add_dll_directory(str(bin_dir))
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ["PATH"]


_modelo = None
_modelo_lock = threading.Lock()


def cargar_modelo():
    global _modelo
    with _modelo_lock:
        if _modelo is None:
            _preparar_dlls_cuda()
            from faster_whisper import WhisperModel

            ruta = _ruta_modelo()
            try:
                _modelo = WhisperModel(ruta, device="cuda", compute_type="float16")
            except Exception as e:  # sin GPU usable: mismo modelo en CPU (más lento)
                print(f"[aviso] CUDA no disponible ({e}); uso CPU", file=sys.stderr)
                _modelo = WhisperModel(ruta, device="cpu", compute_type="int8")
        return _modelo


def escribir_estado(carpeta: Path, **datos) -> None:
    ruta = carpeta / "estado.json"
    actual = {}
    if ruta.exists():
        actual = json.loads(ruta.read_text(encoding="utf-8"))
    actual.update(datos)
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(actual, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ruta)


def leer_estado(carpeta: Path) -> dict:
    ruta = carpeta / "estado.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def _mmss(segundos: float) -> str:
    s = int(segundos)
    return f"{s // 3600:d}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60:02d}:{s % 60:02d}"


def transcribir(carpeta: Path, audio: Path) -> str:
    modelo = cargar_modelo()
    segmentos, info = modelo.transcribe(
        str(audio),
        language="es",
        vad_filter=True,
        beam_size=5,
        condition_on_previous_text=False,  # evita bucles de frases repetidas en audios largos
    )
    duracion = info.duration or 1
    lineas = []
    ultimo = 0.0
    for seg in segmentos:
        lineas.append(f"[{_mmss(seg.start)}] {seg.text.strip()}")
        if time.monotonic() - ultimo > 2:
            escribir_estado(carpeta, estado="transcribiendo", progreso=round(min(seg.end / duracion, 1) * 100))
            ultimo = time.monotonic()
    texto = "\n".join(lineas)
    (carpeta / "transcripcion.md").write_text(
        f"# Transcripción · {carpeta.name}\n\nDuración: {_mmss(duracion)}\n\n{texto}\n", encoding="utf-8"
    )
    return texto


def resumir(carpeta: Path, transcripcion: str, asignatura: str) -> str:
    claude = shutil.which("claude")
    if not claude:
        raise RuntimeError("No encuentro el comando 'claude' en el PATH")
    entrada = f"Asignatura: {asignatura or 'sin indicar'}\n\n<transcripcion>\n{transcripcion}\n</transcripcion>"
    r = subprocess.run(
        [
            claude, "-p",
            "--model", MODELO_CLAUDE,
            "--system-prompt", PROMPT_RESUMEN,
            "--tools", "",
            "--setting-sources", "project",
            "--no-session-persistence",
            "--output-format", "text",
        ],
        input=entrada,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=carpeta,
        timeout=900,
    )
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f"claude -p falló ({r.returncode}): {(r.stderr or r.stdout).strip()[:500]}")
    resumen = r.stdout.strip()
    (carpeta / "resumen.md").write_text(resumen + "\n", encoding="utf-8")
    return resumen


def buscar_audio(carpeta: Path) -> Path:
    candidatos = sorted(carpeta.glob("audio.*"))
    if not candidatos:
        raise FileNotFoundError(f"No hay audio en {carpeta}")
    return candidatos[0]


def procesar(carpeta: Path) -> None:
    carpeta = Path(carpeta)
    estado = leer_estado(carpeta)
    try:
        escribir_estado(carpeta, estado="transcribiendo", progreso=0, error=None)
        texto = transcribir(carpeta, buscar_audio(carpeta))
        if not texto.strip():
            raise RuntimeError("La transcripción ha salido vacía (¿el micro grababa silencio?)")
        escribir_estado(carpeta, estado="resumiendo", progreso=100)
        resumir(carpeta, texto, estado.get("asignatura", ""))
        escribir_estado(carpeta, estado="listo", terminado=time.strftime("%Y-%m-%d %H:%M"))
    except Exception as e:
        escribir_estado(carpeta, estado="error", error=str(e))
        raise


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    procesar(Path(sys.argv[1]).resolve())
    print((Path(sys.argv[1]) / "resumen.md").read_text(encoding="utf-8"))
