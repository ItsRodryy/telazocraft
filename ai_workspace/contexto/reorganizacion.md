# Reorganización de la biblioteca (raíz del servidor)

Mapa de la reorganización completada el 2026-10-27 (decidida el 2026-10-26). Mover = `Move-Item` en el mismo
volumen (renombrado instantáneo, sin copiar datos). Nada se borra salvo `__pycache__`. El código de
Telazocraft **no** vive aquí (ver `telazocraft.md`).

## Raíz final

```
telazocraft.json    marca de biblioteca
servidores/lepazo/  NeoForge 1.21.1 + 96 mods (lo que hoy es la raíz del servidor)
copias/<servidor>/{locales,compartidas,partidas}
exportaciones/      zips de mods para amigos (no se sincroniza)
compartido/         playit.exe, _ultimo_jugador.txt, EN_USO.lock, sync_guardia.local.ini,
                    logs_hardware/
archivo/            retirado (nunca se borra)
LEEME.md · stignore_comun.txt · AGENTS.md · CLAUDE.md · ai_workspace/
PLAN_ACTUAL.md solo mientras haya un plan activo
.claude/ .agents/ .codex/ .graphifyignore graphify-out/ .stfolder .stignore .stversions
```

El servidor hardcore nuevo (26.3) se crea en el bloque 6 con el asistente, en `servidores/hardcore/`.

## Origen → destino

| Hoy | Pasa a |
|---|---|
| `world/` `mods/` `config/` `defaultconfigs/` `libraries/` | `servidores/lepazo/` (mismo nombre) |
| `server.properties` `user_jvm_args.txt` `eula.txt` `server-icon.png` | `servidores/lepazo/` |
| `whitelist.json` `ops.json` `banned-*.json` `usercache.json` `usernamecache.json` | `servidores/lepazo/` |
| `logs/` `crash-reports/` | `servidores/lepazo/` |
| `modos/hardcore/` (1.21.1, nunca jugado) | `archivo/hardcore_1.21.1/` |
| `backups_mundo_auto/normal/` | `copias/lepazo/locales/` |
| `backups_mundo_auto/compartidos/normal/` | `copias/lepazo/compartidas/` |
| `backups_mundo_auto/hardcore/` y `compartidos/{hardcore,partidas}/` | `archivo/hardcore_1.21.1/copias/` |
| `playit.exe` `sync_guardia.local.ini` `_ultimo_jugador.txt` `logs_hardware/` | `compartido/` |
| `gestor_servidor.py` `esperar_sync.py` | originales a `archivo/pre_app/`; gestor adaptado y arrancar.bat retirados a `archivo/pre_app/emergencia/` |
| `arrancar_server.bat` `modo.ini` | `archivo/pre_app/` |
| `LEEME_MODOS.md` `PLAN_MODOS_Y_BACKUPS.md` `SYNCTHING_SETUP.md` | `archivo/docs_2026-09/`; lo vigente pasa a `LEEME.md` |
| `debug/` | `archivo/debug_2026-07-02/` |
| `__pycache__/` | se borra (regenerable) |

`servidores/lepazo/servidor.json` se crea con los valores actuales (ver `telazocraft.md`;
`java_mayor` 21, `ram_mb` 10240 = `user_jvm_args.txt`, `extras_cliente` Xaero's ×2).

## Rutas que dependen de la carpeta de trabajo

- NeoForge: `java @user_jvm_args.txt @libraries/net/neoforged/neoforge/<VER>/win_args.txt nogui`
  usa rutas relativas → el proceso arranca con cwd = `servidores/<id>`.
- Todos usan el puerto 25565 (un solo túnel de Playit): solo un servidor encendido a la vez.

## Syncthing (`stignore_comun.txt`, se sincroniza)

`.stignore` de cada PC contiene solo `#include stignore_comun.txt`. Contenido (si se añade una
negación `!`, va arriba: gana el primer patrón que casa):

```
/copias/*/locales
/exportaciones
/servidores/*/logs
/servidores/*/crash-reports
/compartido/logs_hardware
/compartido/EN_USO.lock
/compartido/sync_guardia.local.ini
**/session.lock
__pycache__
*.log
.stversions
// Compatibilidad con el indice anterior del portatil
/debug
*.bak
```

Portátil: el dueño cambia una vez su `.stignore` por `#include stignore_comun.txt` **antes** de
que el portátil vuelva a conectarse tras la reorganización (si no, bajaría las copias locales).
En el portátil Telazocraft se instala con el exe de Releases (o desde el repo).

La consulta REST tras reorganizar detectó 100 entradas antiguas (debug y .bak) en el índice del
portátil. Se conservan también las exclusiones /debug y *.bak para impedir que reaparezcan.
