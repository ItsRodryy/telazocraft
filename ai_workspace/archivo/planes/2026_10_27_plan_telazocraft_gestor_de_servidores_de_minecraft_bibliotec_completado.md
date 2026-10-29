# Plan — Telazocraft: gestor de servidores de Minecraft + biblioteca ordenada

> **Estado:** COMPLETADO
> Creado: 2026-10-26. Marca cada `[ ]` al terminarlo.

## Objetivo

Crear **Telazocraft**, aplicación PySide6 pública (MIT) con el estilo de vision_driver, que sustituye
a la consola negra y gestiona varios servidores (Lepazo Vice, un Hardcore 26.3 y los que se creen):
arranque, consolita en directo, jugadores, rendimiento, diario, mods con Modrinth, zip de mods para
amigos, acceso TLauncher/premium, copias, bandeja y avisos de Windows, exe con actualizaciones.
Y ordenar la carpeta del servidor como «biblioteca» de datos.

Contexto obligatorio (parte del plan): `ai_workspace/contexto/reorganizacion.md` (bloques 0–1),
`telazocraft.md` (arquitectura, datos comprobados) y `telazocraft_pantallas.md` (bloques 3–6).

## Decisiones del dueño (no volver a preguntar)

- Nombre **Telazocraft**; el servidor sigue llamándose «Lepazo Vice» (MOTD incluido).
- Código en repo aparte y público; la biblioteca nunca va a GitHub. El dueño hará el Git.
- Exe e instalador con actualizaciones desde GitHub Releases, como vision_driver.
- Lepazo se queda en 1.21.1 / NeoForge 21.1.233 con sus 96 mods: ni quitar, ni añadir, ni
  actualizar NeoForge (hay 21.1.265: no tocar).
- Hardcore nuevo en **26.3** (NeoForge) con mods básicos: JEI, Jade, AppleSkin, Sophisticated
  Backpacks, Lithium, FerriteCore, Chunky, Terralith. Sin chat de voz. La lista es provisional:
  el dueño la ajustará desde la app. El hardcore 1.21.1 se archiva.
- Instalar Java 25 con `winget` (permiso dado). Permiso para el `.venv` del repo y PySide6.
- Cada servidor con sus mods, whitelist, ops, acceso y copias. Acceso `abierto` por defecto.
- Zip de mods: carpeta propia de la app con botón «Abrir carpeta»; incluye Xaero's Minimap y
  World Map como extras de cliente.
- Tema oscuro gris. X → bandeja. Avisos de Windows sí. Sin arranque con Windows, sin Discord,
  sin nube, sin horario. Reinicio cada 2 h se mantiene. Mods: solo avisar de actualizaciones.
- Extras: Jugadores, menú de bandeja, Rendimiento, Diario, Pregenerar con Chunky, consolita.
- Pruebas con servidores reales permitidas en este plan, siempre con `GESTOR_NO_PLAYIT=1`.

## Intocables

- Contenido de `world/` y `playerdata/` de Lepazo (se mueve entero, no se edita), los `.zip` de
  copias, `sync_guardia.local.ini` (su clave nunca a logs ni al repo), `archivo/migrate_players.ps1`.
- `D:/Proyectos/iovi/vision_driver/`: solo lectura. No renombrar la carpeta raíz (Syncthing).
- `online-mode`, whitelist (7 jugadores) y Playit de Lepazo quedan igual.

## Archivos y símbolos

`gestor_servidor.py` (1300 líneas; usa `graphify explain <símbolo>`): rutas L84–L96,
`preparar_modo` L513, `comando_servidor` L223, `identidad_a_hardcore` L462, `hacer_backup` L904,
`rotar` L864, `LectorConsola` L713, `VigilantePlayit` L599, `MonitorHW` L236,
`secuencia_parada` L1031, `main` L1275. Pruebas: `archivo/pruebas_plan/test_gestor.py`.

## Bloques

### 0 · Preparación [HECHO]
- [x] [HECHO] Servidor apagado, portátil pausado/desconectado, Syncthing al día, manifiesto de 1.552 archivos y respaldo de 1.541 verificados.

### 1 · Biblioteca ordenada [HECHO]
- [x] [HECHO] Traslados con hashes iguales, metadatos y emergencia; Done/list/stop y copias reales sobre copia; originales devueltos intactos. Syncthing idle y exclusiones verificadas por browse; se conservan /debug y *.bak para evitar entradas antiguas del portátil.

### 2 · Repo y motor [HECHO]
- [x] [HECHO] Proyecto separado sin Git, .venv PySide6 6.11.3, motor sin Qt por módulos y CLI --consola; pruebas ampliadas.

### 3 · App base [HECHO]
- [x] [HECHO] Tema gris, controles y guía reutilizados, logo propio, selección de biblioteca, Servidores, Consola/consolita, Sistema, bandeja, avisos y cierre seguro; pruebas offscreen en verde.

### 4 · Mods y zip [HECHO]
- [x] [HECHO] Modrinth, dependencias, JAR, retirada, actualizaciones a petición y Chunky; ZIP real abierto y verificado: 83+2 JAR y LEEME; 13 solo servidor excluidos.

### 5 · Gestión [HECHO]
- [x] [HECHO] Jugadores, Rendimiento, Diario, Ajustes y Copias; migración de prueba abierto→premium→abierto con API Mojang real, datos sintéticos y hashes conservados.

### 6 · Asistente y Hardcore 26.3 [HECHO]
- [x] [HECHO] Plantillas a–c, Java por versión e instalación con winget; Java 25 y NeoForge 26.3.0.99, ocho mods más tres dependencias, whitelist de siete y abierto. Cliente real aislado: salud 20→20 durante la gracia, muerte tras ella, partida archivada y otra semilla. Pruebas en archivo/pruebas_app/; cliente temporal fuera del proyecto.
### 7 · Exe, documentación y cierre [HECHO]
- [x] [HECHO] Empaquetador, Inno Setup 6.7.3, release.yml y actualizador; 0.1.0 instalado por usuario, accesos y aceptación instalada correctos. TLS nativo y regresión del cierre de diálogos comprobados.
- [x] [HECHO] Emergencia retirada a archivo/pre_app/emergencia/ con tres hashes idénticos; modo vigente --consola.
- [x] [HECHO] README, LEEME, AGENTS, contexto, configuración y estado actualizados; graphify update . ejecutado.
- [x] [HECHO] 26 pruebas de app y 7 de legado; smoke de desarrollo e instalado offscreen; 1.178 originales (11 ZIP) idénticos, 104 archivos públicos sin datos reales, instalador SHA-256 correcto; raíz, exclusiones y API verificadas. Medir sin excesos; cierre y archivo del plan.

## Pruebas y aceptación

- `python -B -m unittest discover -s tests` en el repo, en verde (motor + interfaz offscreen).
- Desde la app: iniciar Lepazo, ver log en consolita y Consola, jugadores, `list`, parar con copia
  de sesión; ídem Hardcore. X → bandeja; Salir con servidor encendido → parada con copia, sin
  `EN_USO.lock` ni `playit.exe` vivos.
- `world/level.dat` y `playerdata/66009901-d7ab-3218-9a18-0d0bd57632a4.dat` de Lepazo con el hash
  del manifiesto.
- Repo sin datos personales: buscar nicks, UUID, `joinmc.link`, Device ID y claves → 0 resultados.
- La raíz de la biblioteca contiene solo lo listado en «Raíz final».

## Riesgos y marcha atrás

- BSOD recurrentes (XMP): mover solo dentro del volumen; verificar hashes tras cada bloque que
  toque datos; si algo no cuadra, parar y restaurar desde el respaldo del bloque 0.
- Portátil con `.stignore` antiguo: no reconectar hasta cambiarlo (paso en `LEEME.md`).
- Marcha atrás total: servidor apagado; mover la biblioteca actual fuera de Syncthing; copiar el
  respaldo del bloque 0 y devolver las copias de `copias/` a `backups_mundo_auto/`.
- Dato no comprobable (API caída, versión inexistente, Java ausente): BLOQUEADO con motivo.

## Cierre (2026-10-27)

- Trabajo completado y verificado. Evidencia instalada: %TEMP%/telazocraft_aceptacion_qt_instalada_resultado.json (correcto=true); no fue necesario repetir la aceptación real ya superada.
- Instalador: D:/Proyectos/personal/telazocraft/dist/Telazocraft-0.1.0-windows.exe y SHA256SUMS.
- Respaldo: C:/Users/adria/Desktop/LepazoVice_respaldo_pre_app_2026-10-26_223850/; manifiesto %TEMP%/telazocraft_pre_app_eqjnrlkr/manifiesto_sha256.json.
- Sin Telazocraft, servidor, cliente, Playit ni lock al cerrar. Portatil pausado hasta actualizar su .stignore. Git/publicación y comprobación del túnel real corresponden al dueño; BIOS/MemTest86 quedan fuera de este plan.
