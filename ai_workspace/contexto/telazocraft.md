# Telazocraft — arquitectura (0.3.1)

Autor: Adrián Rodríguez Rodríguez (ItsRodryy), MIT. Actualizado el 2026-10-27.
Pantallas: `telazocraft_pantallas.md`.

## Código y datos

- Repo público: `D:/Proyectos/personal/telazocraft/`, remoto `ItsRodryy/telazocraft`, rama main.
  Commits como ItsRodryy, sin Co-Authored-By ni atribuciones a IA; una etiqueta vX.Y.Z publica
  una Release, así que solo con permiso. Nunca la cuenta del instituto ni la del trabajo.
- Biblioteca: `biblioteca/` dentro de la app, excluida de Git y sincronizada por Syncthing;
  marca `telazocraft.json` schema 1.
  Servidores en `servidores/<id>/servidor.json`. El repo nunca contiene datos reales, mundos,
  JAR, nicks, UUID, túneles ni claves. Preferencias y cachés en LocalAppData/Telazocraft.
- Windows, Python 3.11+, PySide6 6.11, truststore (TLS nativo; nunca desactivar certificados).
  `.venv/Scripts/python.exe -B -m telazocraft` abre desarrollo. Modo `--consola ID` instalado
  con `python/python.exe`; stop guarda, detiene y crea copia de sesión.

## Organización

`code/telazocraft/`: motor sin Qt; app y widgets; common (ajustes, i18n, Releases);
tools (empaquetador, actualizador); tests (motor, HTTP simulado e interfaz offscreen).
`docs/estilo/` conserva la guía y `telazocraft.md` sus reglas propias. Recursos ligeros de marca
vectoriales; `app/logo_paths.py::VARIANTE_LOGO` elige entre cinco contornos incorporados.

Motor: un servidor a la vez, lock/testigo, Playit y Syncthing opcionales. Conserva copias por
niveles, reinicio y apagado si vacío, comandos y hardcore. La gracia usa Resistencia y resistencia
al fuego: no protege /kill ni el vacío. No modifica acceso, red ni identidades sin confirmación.
Java se localiza por versión mayor; el asistente ofrece winget si falta.

## Interfaz y rendimiento

Cinco vistas y engranaje emergente VentanaBase; consola inferior y bandeja. Abrir nunca inicia
un servidor. Posición centrada y sin pantalla completa, conservadas de 0.2.1.
Bus.resumen entrega lecturas pesadas desde trabajadores: inventario, diario y tamaño (caché
de cinco minutos). Solo se pinta la vista visible, inmediatamente con caché; los resultados
antiguos de otra biblioteca se descartan. Hashes de mods reutilizados por ruta/tamaño/mtime.
Watcher con antirrebote sobre metadatos, mods, diario y copias, sin logs/latest.log.
El motor recoge métricas cada cinco segundos desde el arranque; Inicio solo dibuja muestras.
Errores visibles y log rotado en LocalAppData/Telazocraft/telazocraft.log.

`motor/historial.py` importa sesiones y tiempos de encendido de logs de forma idempotente.
No cierra una sesión aún abierta en latest.log. `motor/tiempos.py` une intervalos solapados del
diario y logs, incluyendo sesiones vivas; no suma dos veces el mismo tiempo ni usa estadísticas
de personajes como sustituto. Eventos de jugadores actualizan Inicio al momento.

## Asistente y paquetes

Cinco pasos, versiones no editables, carga/errores/reintento visibles y NeoForge estable más
nuevo preseleccionado por versión MC. Acceso por itemData; extras vacíos en servidores nuevos.
Búsqueda Modrinth con 300 ms de antirrebote y descarte de respuestas antiguas; marca Instalado.
Paso final permite crear paquete. Una carpeta nueva vacía ofrece Servidor de prueba vanilla,
última release descargada al aceptar; nunca se ofrece en bibliotecas existentes.

Paquete en `exportaciones/<id>/Paquete_<Nombre>_<fecha>.zip`: mods de cliente/ambos y extras
con dependencias, instalador NeoForge con SHA-256 oficial, BAT/PowerShell e instrucciones.
Vanilla omite NeoForge. El cliente verifica hashes, aparta mods anteriores y busca Java en PATH
y runtimes de launchers. `--install-client RUTA` comprobado con --help del instalador real;
sin ventana en modo automático y con apertura normal si falla. Conserva tres ZIP, rotados a
archivo/exportaciones. Puede generarse con servidor activo, sin modificarlo.

## Distribución y verificación

Instalador por usuario Inno Setup 6.7.3; CPython 3.12.15 autocontenido con SHA-256 oficial,
dependencias dinámicas y código pyc con rutas relativas. `tools/launcher.cs` fabrica Telazocraft.exe
con icono propio usando .NET Framework de Windows. ICO 16–256, imágenes del instalador y
AppUserModelID ItsRodryy.Telazocraft coincidentes; ie4uinit -show después de instalar.
`tools/empaquetar.py --repositorio ItsRodryy/telazocraft --iscc RUTA` genera EXE y SHA256SUMS.
Workflow «Instalador y Release» fabrica y publica al subir vX.Y.Z; el actualizador exige digest
SHA-256 de la Release estable. Nunca publica ni inicia servidores al abrir la aplicación.

0.3.1: 57 pruebas, siete del legado, smoke de repo/paquete/instalada y capturas reales a
1400×900 y 1000×700. Con log simulado escribiendo: 0,024 % CPU del equipo (16 lógicos, 8 s).
Desplegables vacíos no reproducidos en 0.2.1 instalada; 103 releases visibles antes y después.
Paquete real Lepazo: 83 mods + dos extras; 13 exclusivos de servidor excluidos. BAT probado con
APPDATA falso y corrupción. 1.323 protegidos conservan tamaño y mtime; no se hizo hashing completo
de mundos para mantener las pruebas ligeras. Ningún servidor arrancado ni parado.

Release v0.3.1 publicada y digest comprobado (workflow 40568995133, commit 0a653ef). La 0.3.0
falló por PSModulePath heredado al abrir Windows PowerShell desde PowerShell 7: el BAT fija
sus módulos estándar con setlocal; la prueba reproduce esa herencia. 57 pruebas también en
Python 3.12. Estado final y evidencias: ESTADO.md.
