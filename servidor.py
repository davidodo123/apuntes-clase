"""Servidor local de la grabadora. Escucha solo en 127.0.0.1: desde el Mac se entra
por túnel SSH (ssh -L 8765:localhost:8765 ...), nunca expuesto a la red.

    .venv\\Scripts\\python servidor.py
"""
from __future__ import annotations

import json
import queue
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import procesar

RAIZ = Path(__file__).resolve().parent
CLASES = RAIZ / "clases"
WEB = RAIZ / "web"
PUERTO = 8765
EXTENSIONES = {"webm", "mp4", "ogg", "m4a", "wav"}
MAX_TROZO = 20 * 1024 * 1024

CLASES.mkdir(exist_ok=True)
cola: "queue.Queue[Path]" = queue.Queue()


def trabajador() -> None:
    while True:
        carpeta = cola.get()
        try:
            procesar.procesar(carpeta)
        except Exception as e:
            print(f"[error] {carpeta.name}: {e}")
        finally:
            cola.task_done()


def slug(texto: str) -> str:
    texto = texto.lower().strip()
    for a, b in zip("áéíóúüñ", "aeiouun"):
        texto = texto.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", texto).strip("-")[:40] or "clase"


def carpeta_de(id_: str) -> Path:
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{4}_[a-z0-9-]+", id_ or ""):
        raise ValueError("id no válido")
    carpeta = CLASES / id_
    if not carpeta.is_dir():
        raise FileNotFoundError("esa clase no existe")
    return carpeta


def unir_trozos(carpeta: Path, total: int) -> Path:
    trozos = carpeta / "trozos"
    ficheros = sorted(trozos.glob("*.*"))
    if total and len(ficheros) < total:
        faltan = total - len(ficheros)
        raise RuntimeError(f"faltan {faltan} trozos de audio por llegar")
    ext = ficheros[0].suffix if ficheros else ".webm"
    destino = carpeta / f"audio{ext}"
    with destino.open("wb") as salida:
        for f in ficheros:
            salida.write(f.read_bytes())
    return destino


class Manejador(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if "/api/trozo" not in (args[0] if args else ""):
            super().log_message(fmt, *args)

    def _json(self, datos, codigo=200):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _cuerpo(self) -> bytes:
        largo = int(self.headers.get("Content-Length", 0))
        if largo > MAX_TROZO:
            raise ValueError("trozo demasiado grande")
        return self.rfile.read(largo)

    def do_GET(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if url.path in ("/", "/index.html"):
                cuerpo = (WEB / "index.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(cuerpo)))
                self.end_headers()
                self.wfile.write(cuerpo)
            elif url.path == "/api/clases":
                lista = []
                for c in sorted(CLASES.iterdir(), reverse=True):
                    if c.is_dir():
                        lista.append({"id": c.name, **procesar.leer_estado(c)})
                self._json(lista)
            elif url.path == "/api/estado":
                self._json(procesar.leer_estado(carpeta_de(q.get("id"))))
            elif url.path == "/api/resumen":
                carpeta = carpeta_de(q.get("id"))
                archivo = "transcripcion.md" if q.get("tipo") == "transcripcion" else "resumen.md"
                ruta = carpeta / archivo
                self._json({"texto": ruta.read_text(encoding="utf-8") if ruta.exists() else ""})
            else:
                self._json({"error": "no existe"}, 404)
        except (ValueError, FileNotFoundError) as e:
            self._json({"error": str(e)}, 400)

    def do_POST(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if url.path == "/api/empezar":
                datos = json.loads(self._cuerpo() or b"{}")
                asignatura = (datos.get("asignatura") or "").strip()[:80]
                id_ = f"{time.strftime('%Y-%m-%d_%H%M')}_{slug(asignatura)}"
                carpeta = CLASES / id_
                n = 2
                while carpeta.exists():
                    carpeta = CLASES / f"{id_}-{n}"
                    n += 1
                (carpeta / "trozos").mkdir(parents=True)
                procesar.escribir_estado(carpeta, estado="grabando", asignatura=asignatura,
                                         empezado=time.strftime("%Y-%m-%d %H:%M"))
                self._json({"id": carpeta.name})
            elif url.path == "/api/trozo":
                carpeta = carpeta_de(q.get("id"))
                n = int(q.get("n", -1))
                ext = q.get("ext", "webm")
                if n < 0 or ext not in EXTENSIONES:
                    raise ValueError("trozo no válido")
                # Escribir por número hace que reintentar el mismo trozo sea seguro.
                (carpeta / "trozos" / f"{n:06d}.{ext}").write_bytes(self._cuerpo())
                self._json({"ok": True})
            elif url.path == "/api/terminar":
                carpeta = carpeta_de(q.get("id"))
                total = int(q.get("total", 0))
                unir_trozos(carpeta, total)
                procesar.escribir_estado(carpeta, estado="en cola", progreso=0)
                cola.put(carpeta)
                self._json({"ok": True})
            elif url.path == "/api/reprocesar":
                carpeta = carpeta_de(q.get("id"))
                procesar.buscar_audio(carpeta)
                procesar.escribir_estado(carpeta, estado="en cola", progreso=0, error=None)
                cola.put(carpeta)
                self._json({"ok": True})
            else:
                self._json({"error": "no existe"}, 404)
        except (ValueError, FileNotFoundError, RuntimeError) as e:
            self._json({"error": str(e)}, 400)


def main():
    # Clases que se quedaron a medias si el PC se apagó mientras procesaba.
    for c in CLASES.iterdir():
        if c.is_dir() and procesar.leer_estado(c).get("estado") in ("en cola", "transcribiendo", "resumiendo"):
            cola.put(c)
    threading.Thread(target=trabajador, daemon=True).start()
    threading.Thread(target=procesar.cargar_modelo, daemon=True).start()  # precarga Whisper
    servidor = ThreadingHTTPServer(("127.0.0.1", PUERTO), Manejador)
    print(f"Grabadora lista en http://localhost:{PUERTO}  (Ctrl+C para parar)")
    servidor.serve_forever()


if __name__ == "__main__":
    main()
