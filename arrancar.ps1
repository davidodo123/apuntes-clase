# Arranca la grabadora en segundo plano, fuera de la sesión SSH (sigue viva al desconectar).
# Uso desde SSH:  powershell -File C:\Users\david\Desktop\Apuntes-Clase\arrancar.ps1
# Parar:          powershell -File C:\Users\david\Desktop\Apuntes-Clase\arrancar.ps1 -Parar
param([switch]$Parar)

$dir = $PSScriptRoot
$escuchando = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue

if ($Parar) {
    if (-not $escuchando) { "La grabadora no estaba en marcha."; exit 0 }
    $escuchando | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -like "*servidor.py*" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    "Grabadora parada."
    exit 0
}

if ($escuchando) { "La grabadora ya estaba en marcha: abre http://localhost:8765 en el Mac."; exit 0 }

# Win32_Process.Create lanza el proceso desde el servicio WMI, no como hijo de sshd,
# así que Windows no lo cierra cuando se corta la conexión SSH.
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine      = "cmd.exe /c `"$dir\iniciar.bat`""
    CurrentDirectory = $dir
}
if ($r.ReturnValue -ne 0) { "No se pudo arrancar (código $($r.ReturnValue))."; exit 1 }

for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Milliseconds 500
    if (Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue) {
        "Grabadora en marcha: abre http://localhost:8765 en el Mac."
        exit 0
    }
}
"Lanzada, pero aún no responde. Mira $dir\clases\servidor.err.log"
exit 1
