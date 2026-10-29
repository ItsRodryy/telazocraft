# Plan — Telazocraft 0.2.0: rediseño de la interfaz

> **Estado:** COMPLETADO
> Creado: 2026-10-27. Marca cada `[ ]` al terminarlo.

## Objetivo

Rehacer la interfaz de Telazocraft para que sea intuitiva y se parezca de verdad a vision_driver:
5 pantallas, consola desplegable, botones con color, confirmaciones antes → después, listas que se
refrescan solas, logo «T», jugadores con historial importado. Publicar e instalar la 0.2.0.

Especificación obligatoria: `ai_workspace/contexto/telazocraft_pantallas.md` (v2). Arquitectura:
`telazocraft.md`. Guía de estilo de vision_driver (solo lectura) en
`D:/Proyectos/iovi/vision_driver/ai_workspace/contexto/estilo/`.

## Decisiones del dueño (no volver a preguntar)

- Problemas de la 0.1.0: no intuitiva, demasiados botones grises iguales; «Seleccionar» y la
  lista de tarjetas sobran (manda el desplegable); Mods y Jugadores salen vacíos; Rendimiento es
  un panel enorme para cuatro datos; logo de cubo no gusta.
- Pantallas: Inicio, Jugadores (Lista + Actividad), Mods, Copias, Ajustes; engranaje Telazocraft
  abajo en la barra lateral. Barra lateral con icono y texto. Sin pantalla de consola.
- Colores que peguen con el gris oscuro; Iniciar verde, Parar rojo, Reiniciar ámbar.
- Al abrir: queda elegido el último servidor; no se arranca nada.
- Confirmar Parar solo con jugadores conectados. Toda modificación de un servidor: ventana
  emergente antes → después.
- Importar los 6 jugadores de Lepazo con horas desde los logs.
- Pregenerar (Chunky) va a Ajustes → Mundo.
- El dueño no va a crear servidores ahora: el asistente se prueba con una biblioteca temporal.

## Intocables

- Biblioteca real (`C:\Users\adria\Desktop\minecraft_server_neoforge_1_21_1`): en este plan solo
  se **escribe** `servidores/*/sesiones.jsonl` (importación) y la caché de iconos/cabezas. Nada de
  mundos, mods, whitelist, ops, `server.properties` ni copias; las pruebas que cambien cosas van
  sobre copias en `%TEMP%`. Sin arrancar servidores reales.
- `D:/Proyectos/iovi/vision_driver/`: solo lectura. Sin Git. El motor no cambia de
  comportamiento salvo lo que pide este plan (importar historial, vigilancia de archivos).
- Portátil sigue pausado en Syncthing.

## Archivos y símbolos (repo `D:/Proyectos/personal/telazocraft/`)

- `code/telazocraft/app/principal.py` (`MainWindow`, `VISTAS`, barra superior, `QListWidget` nav,
  consolita), `gestion.py` (Jugadores, Rendimiento, Diario, Ajustes, Copias), `mods.py`,
  `asistente.py`, `icons.py` (`logo_pixmap`, `app_icon`), `style.py`, `app/widgets/`
  (`confirmacion`, `toggle`, `tabla_datos`, `estado_punto`, `status_badge`, `log_view`…).
- Referencia: vision_driver `code/vision_driver/app/main_window.py` (barra lateral icono+texto,
  compacto ≤1080 px), `icons.py::logo_pixmap/_dibujar_lambda`, `widgets/dialogo_proceso.py`,
  `widgets/fundido.py`, `widgets/anim.py`.
- Motor: `motor/jugadores.py::conocidos`, `motor/diario.py::Diario`.
- Pruebas: `tests/interfaz/test_diseno.py`, `tests/motor/*`. Versión: `code/telazocraft/__init__.py`.

## Bloques

### 1 · Base visual [HECHO]
- [x] [HECHO] T vectorial/ICO comparada con Λ, roles de botón QSS, glifos, VentanaBase/DialogoProceso y confirmación antes→después con Cancelar predeterminado.

### 2 · Armazón [HECHO]
- [x] [HECHO] Cinco vistas y engranaje, consola inferior con línea/altura/estado recordados, watcher con antirrebote y eventos, selección persistente y un solo servidor activo.

### 3 · Inicio y Jugadores [HECHO]
- [x] [HECHO] Inicio compacto y tres gráficas; importadas 205 sesiones idempotentes de logs: seis jugadores con horas e IRENEE sin sesiones; Lista/Actividad, cabezas, unión por nick y menús con confirmación.

### 4 · Mods y Copias [HECHO]
- [x] [HECHO] 96 mods automáticos, iconos/resultados Modrinth y caché, chips, añadir/JAR/ZIP y menús; copias en tarjetas, crear y restaurar con confirmación y servidor parado.

### 5 · Ajustes, Telazocraft y asistente [HECHO]
- [x] [HECHO] Secciones, controles propios, borradores y barra pendiente; Chunky en Mundo, engranaje Sistema y asistente de cinco pasos. Vanilla 26.3 verificado por SHA-1 y copia Lepazo de 96 JAR sin mundo creados en biblioteca temporal; whitelist de siete y sin arrancar servidores.

### 6 · Verificación, 0.2.0 y cierre [HECHO]
- [x] [HECHO] 41 pruebas de app y 7 de legado; sintaxis/JSON, smoke, capturas instaladas de seis vistas a 1400×900 y 1000×700 revisadas, acceso directo y cierre nativos comprobados. 0.2.0 fabricada e instalada; paquete instalado idéntico al build, SHA-256 correcto, 1.302 originales protegidos y 11 ZIP intactos; privacidad, documentación, Graphify y Medir correctos.

## Pruebas y aceptación

- Abrir la app: elegido el último servidor, nada arranca, ningún botón «Actualizar».
- Lepazo: Mods muestra 96 mods al entrar; Jugadores muestra 6 jugadores con horas; Inicio muestra
  versión, acceso, último uso legible y tamaño.
- Cualquier cambio (ajuste, whitelist, mod, restaurar) abre la confirmación antes → después;
  Cancelar no cambia nada (hash de los archivos igual).
- Consola: se pliega/despliega desde abajo y recuerda su estado tras reiniciar la app.
- A 1000 px de ancho la barra lateral pasa a iconos y nada se recorta.
- Hashes de `world/`, `mods/`, `server.properties`, `whitelist.json` y `ops.json` de los dos
  servidores reales iguales antes y después del plan.

## Riesgos y marcha atrás

- La 0.1.0 instalada sigue funcionando hasta instalar la 0.2.0; su instalador está en `dist/`
  (si no, copiarlo antes a `%TEMP%`). Marcha atrás: reinstalar la 0.1.0.
- Importación de historial: solo añade líneas con `origen: "logs"`; deshacer = quitar esas líneas
  (copiar `sesiones.jsonl` a `%TEMP%` antes).
- Modrinth o mc-heads sin red: la app sigue y muestra iconos/cabezas por defecto.

## Cierre (2026-10-27)

- Completado. Parada inicial de Lepazo autorizada expresamente por el dueño: guardado y copia de sesión antes de registrar el baseline. Después no se arrancaron servidores reales; solo importación de historial y cachés.
- Instalador: D:/Proyectos/personal/telazocraft/dist/Telazocraft-0.2.0-windows.exe; SHA256SUMS en la misma carpeta. 0.1.0 conservada para marcha atrás.
- Evidencia y respaldo del trabajo: ruta en %TEMP%/telazocraft_v020_ruta.txt; hashes_iniciales.json, aceptacion_asistente.json, verificacion_final.json y capturas/. No se copió la clave Syncthing al código público.
- Servidores, Playit y Telazocraft cerrados. Portatil pausado; no reanudar hasta cambiar su .stignore. Git y publicación remota corresponden al dueño; entrega de este plan: versión instalada e instalador local, sin usar Git.
