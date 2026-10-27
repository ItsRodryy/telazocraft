# Telazocraft

Gestor de bibliotecas de servidores Minecraft para Windows. Autor: Adrián Rodríguez Rodríguez.
Licencia MIT. La aplicación y sus datos se guardan por separado: este proyecto nunca contiene
mundos, servidores, mods, jugadores, copias ni claves.

Permite iniciar un solo servidor, enviar comandos, consultar jugadores, sesiones y rendimiento,
gestionar mods de Modrinth y generar un ZIP de cliente. Incluye copias por niveles, restauración,
partidas hardcore con gracia frente a daño normal, bandeja y avisos. `/kill` ignora la gracia.

## Desarrollo

Python 3.11 o posterior. Desde esta carpeta, en PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
$env:PYTHONPATH='code'
.venv/Scripts/python.exe -B -m telazocraft
```

En el primer arranque elige una biblioteca existente o una carpeta vacía para crearla. Las
preferencias de cada equipo viven en `%LOCALAPPDATA%/Telazocraft/ajustes.json`.
El modo de consola se abre con `python -m telazocraft --biblioteca RUTA --consola ID`.
`stop` guarda, detiene y crea copia de sesión; Ctrl+C solicita una parada segura.

## Uso

- El desplegable superior elige el servidor; el botón ＋ abre el asistente de cinco pasos. Al abrir nunca se inicia un servidor automáticamente.
- **Inicio**: datos del servidor, acceso, último uso, tamaño y conectados; tres gráficas pequeñas de CPU, RAM y TPS solo mientras está encendido y esta pantalla es visible.
- **Jugadores**: Lista y Actividad. El historial se importa de logs comprimidos o normales sin duplicar sesiones; identidades antiguas se unen por nick. Permisos y acciones en «⋯».
- **Mods**: carga automática, iconos en caché, búsqueda en Modrinth, JAR, dependencias y actualizaciones a petición. ZIP para amigos y carpeta de exportaciones. Cambios solo con el servidor parado.
- **Copias**: tarjetas por fecha y tipo; crear o restaurar con confirmación. El mundo sustituido y los ZIP rotados van a `archivo/`.
- **Ajustes**: General, Mundo (con Chunky), Acceso, Copias, Hardcore y Extras de cliente. Editar → cambios sin aplicar → confirmar antes/después. Cancelar conserva los datos.
- El engranaje **Telazocraft** reúne Playit, Syncthing, Java, biblioteca y actualizaciones.
- La **Consola** se despliega desde el borde inferior; recuerda apertura y altura. Admite búsqueda y comandos con historial. La barra lateral pasa a iconos por debajo de 1080 px.
- La X oculta en bandeja; «Salir» detiene y espera la copia. Iniciar no pide confirmación; Parar pregunta cuando hay jugadores conectados.

La gracia hardcore empieza con la primera entrada. Usa Resistencia y resistencia al fuego;
protege del daño normal, no de órdenes administrativas como `/kill` ni del vacío. Tras una muerte
fuera de la gracia se conserva la partida y se genera otra con una semilla diferente.

## Verificación

```powershell
$env:PYTHONPATH='code'
$env:QT_QPA_PLATFORM='offscreen'
.venv/Scripts/python.exe -B -m unittest discover -s tests
.venv/Scripts/python.exe -B -m telazocraft --biblioteca RUTA --smoke
```

Para pruebas reales locales usa `GESTOR_NO_PLAYIT=1`. Los datos de producción se conservan sin
editar; se prueba sobre una copia o sobre un servidor dedicado a pruebas. Las pruebas de interfaz
comprueban los controles reutilizados, contraste y dimensiones. Los tests de red usan HTTP simulado;
la aceptación de servidores, la migración y el ZIP se comprueban también con sus servicios reales.

## Instalador y Releases

`python tools/empaquetar.py --iscc RUTA_A_ISCC` fabrica `dist/Telazocraft-0.2.1-windows.exe` y
`SHA256SUMS`. Requiere Inno Setup 6.7 o posterior. Usa CPython 3.12.15 de python-build-standalone,
verificado con el SHA-256 de la publicación 20261001, dependencias dinámicas y código `.pyc`.
El instalador es por usuario, crea accesos «Telazocraft» y no incluye bibliotecas Minecraft.

Git y la publicación los gestiona el dueño. El flujo `.github/workflows/release.yml` compila y
publica al crear una etiqueta `vX.Y.Z`; `workflow_dispatch` solo genera el artefacto. Configura
`--repositorio propietario/telazocraft` al fabricar para que la instalación sepa de dónde actualizar;
GitHub Actions lo toma del repositorio actual. También puede indicarse en el engranaje Telazocraft.
No se presupone una URL ni se publica nada al ejecutar el programa. Las actualizaciones requieren
una Release estable con el instalador y un `digest` SHA-256 de GitHub; se verifican antes de ejecutar.

Las conexiones HTTPS usan el almacén de certificados del sistema mediante truststore. Las
licencias originales de Python, Qt y truststore acompañan al instalador.
