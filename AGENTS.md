# Telazocraft

App de Windows (Python + PySide6) que gestiona la biblioteca de servidores de Minecraft: Lepazo Vice (NeoForge 1.21.1) y Hardcore 26.3. La biblioteca vive en biblioteca/, dentro de esta carpeta, excluida de Git y sincronizada con el portátil por Syncthing.

Autoría: Adrián Rodríguez Rodríguez (GitHub: ItsRodryy). Ninguna IA figura como autora ni firma nada.

## Forma de trabajar

- Responde en español, breve y directo. Durante el trabajo da un aviso breve cada 30–45 segundos, nunca más de 60 en silencio: qué has comprobado, qué haces y qué falta.
- Antes de una tarea mediana o grande, indica en una línea el modelo en uso y el esfuerzo que recomiendas.
- No expongas el enfoque salvo al planificar. Si una duda cambia el resultado, pregunta (cinco como
  máximo, juntas) y espera; después trabaja sin paradas salvo un bloqueo real. Sin dudas, actúa.
- El chat prevalece sobre estos documentos. Si el usuario decide algo nuevo o cambia algo escrito,
  actualiza el documento afectado en el mismo trabajo, sin esperar a que lo pida.
- Comprueba rutas y datos reales antes de usarlos; no inventes. Di lo que no hayas podido comprobar.
- Git: lee sin pedir permiso (`status`, `diff`, `log`, `show`, `blame`, `branch --list`, `remote -v`). Antes de cualquier operación que cambie algo (`add`, `commit`, `push`, `pull`, `fetch`, `checkout`, `switch`, `restore`, `reset`, `stash`, `merge`, `rebase`, `tag`, crear o borrar ramas, `config`, `init`, `clone`, `clean` o publicación), di exactamente qué vas a hacer, pide permiso y espera. El permiso vale solo para esa operación.
- Al terminar: qué se hizo, cómo se verificó y qué queda. Sin volcados de consola.

## Proyecto

- Plataformas: Windows (sobremesa y portátil).
- Tecnologías: Python 3.11/3.12; PySide6 6.11; NeoForge 1.21.1/JDK 21 y 26.3/JDK 25; Playit v1.0.10; Syncthing (SyncTrayzor); Inno Setup.
- biblioteca/ (datos de los servidores) no entra nunca en Git; los servidores nuevos se crean en biblioteca/servidores/.
- Antes de modificar datos de un servidor: apagado (sin Java del servidor ni compartido/EN_USO.lock). La app se puede trabajar con él activo, sin arrancarlo ni pararlo.
- Configs de Minecraft, .py, .ini y .json en UTF-8 sin BOM.
- En biblioteca/ lo que sobre se mueve a archivo/, nunca se borra.
- No cambiar online-mode, red, Playit ni whitelist sin avisar: rompe el acceso de los amigos. Sin OP ni creativo salvo petición.
- No quitar, añadir ni actualizar mods sin orden expresa.
- Una etiqueta vX.Y.Z publica una Release en GitHub: no crear etiquetas sin permiso.
- Comunica en castellano claro; explica los términos técnicos cuando haga falta.
- Distingue lo comprobado de lo supuesto, lo propuesto y lo pendiente.
- No digas que algo compila, funciona o está validado sin haberlo comprobado.
- Archivos y carpetas nuevos en minúsculas con guion bajo; respeta los nombres obligatorios y los existentes.
- Commits y push solo como ItsRodryy (nunca 2DAM-adrianrod493), mensaje «vX.Y.Z - Descripción» y sin firma de IA.
- Al acabar cada tarea, añade una fila en ai_workspace/registro_trabajo.md.
- Intocable sin orden expresa: biblioteca/servidores/lepazo/world/ y playerdata/; biblioteca/servidores/lepazo/{mods,config,defaultconfigs,libraries}/; ZIP de biblioteca/copias/ y biblioteca/archivo/hardcore_1.21.1/copias/; biblioteca/compartido/sync_guardia.local.ini (clave secreta: no imprimir ni copiar); biblioteca/archivo/migrate_players.ps1 (no ejecutar nunca).

## Verificación

Proporcional al riesgo: en cambios pequeños, solo lo afectado; todo en cambios grandes y al cerrar.

- `$env:PYTHONPATH='code'; $env:QT_QPA_PLATFORM='offscreen'; .venv/Scripts/python.exe -B -m unittest discover -s tests`
- `.venv/Scripts/python.exe -B -m telazocraft --biblioteca biblioteca --smoke (no arranca servidores)`
- `Pruebas reales solo con permiso, sobre copias y con GESTOR_NO_PLAYIT=1`

## Estado, planes y memoria

- Estado: `ai_workspace/ESTADO.md`. Si existe `PLAN_ACTUAL.md`, léelo antes de retomar.
- Skills: `crear-plan` planifica y para; `ejecutar-plan` ejecuta (la orden aprueba el plan);
  `cerrar` verifica, compacta y archiva, o deja el traspaso si solo se pausa; `error` diagnostica;
  `progreso` (= `estado`) retoma y da el avance (`ai_workspace/progreso.md`). Mensajes: según
  `ai_workspace/contexto/personas.md`; nada está enviado sin confirmarlo el usuario.
- `ai_workspace/` guarda solo documentos breves y vigentes: ni copias de código, ni binarios, ni
  informes viejos, ni traspasos duplicados. Los temporales van fuera del proyecto. Los límites de
  tamaño están en `ai_workspace/configuracion.json`.
- Graphify: antes de abrir archivos grandes, `graphify explain <símbolo>` o `graphify affected <símbolo>`. `cerrar` lo actualiza.

## Documentación bajo demanda

Rutas dentro de `ai_workspace/`.

| Si vas a… | Lee |
|---|---|
| tocar servidores, modos, copias, Playit o Syncthing | `contexto/servidor.md` |
| cambiar el código o la arquitectura de la app | `contexto/telazocraft.md` |
| crear o cambiar interfaz | `contexto/telazocraft_pantallas.md` |
| revisar cómo se migró la biblioteca | `contexto/reorganizacion.md` |

Uso diario: biblioteca/LEEME.md.
