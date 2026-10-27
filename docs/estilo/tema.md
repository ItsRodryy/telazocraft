# Tema, tipografía y medidas

## Color

- 12 tonos (`TEMAS_COLOR`, por defecto `gris` y oscuro) × claro/oscuro. Cada rol tiene saturación
  y luminosidad fijas; solo cambia el tono. Las preferencias ya guardadas se respetan.
- Roles: `fondo` (página), `superficie_opaca` (tarjetas, menús, tablas), `superficie_alta` (controles,
  pestañas), `borde`, `borde_sutil`, `texto`, `texto_tenue`, `texto_fuerte`, `acento` (+ `_hover`,
  `_pressed`, `_claro`), `sobre_acento` (texto encima del acento).
- Semánticos fijos, iguales en todos los tonos: `ok` verde (bien), `aviso` ámbar (ojo: simulación,
  trabajo en curso, medida que vale pero con reservas), `peligro` rojo (mal) y `desconectada` naranja
  (`#ee7a3c` oscuro, `#c9561c` claro): un recurso desconectado a mano o al que le falta algo para
  funcionar. Distinto del ámbar.
- **Velo** (`ALFA_VELO`, 176/255): negro translúcido con el texto en blanco, igual en cualquier
  tema. Es lo único que usa blanco fijo: va sobre una imagen o sobre la pantalla apagada, no sobre
  la interfaz. Ver `superficies.md`.
- Transparencias con `_rgba(token, alfa)`. Nunca `#hex` ni `rgba()` literal en el QSS, salvo el velo.
- Lo que se pinta a mano lee `style.FONDO`, `style.ACENTO`… en cada pintado y escucha
  `style.bus().cambiado`.
- Mica opcional: superficies con alfa 0,76; la página siempre sólida.

## Tipografía y jerarquía

`Segoe UI`/`Arial` 13 px, color `texto`. **Cada panel tiene tres niveles y se distinguen a la vista**
(decisión del usuario, 13/10/2026: el título de un panel tiene que destacar sobre el resto):

| Nivel | objectName | Aspecto |
|---|---|---|
| título de pantalla | `titulo` | 15 px, 600, `texto_fuerte` |
| **título de panel** («Profundidad», «Ajustes», «Parámetros de la cámara») | `tituloPanel` | **15 px, 600, `texto_fuerte`** |
| subtítulo de grupo dentro de un panel («Filtros», «Color») | `grupoParametros` / título de `QGroupBox` | 13 px, 600; `texto_tenue` en listas y `texto_fuerte` en `QGroupBox`; en minúscula, nunca en mayúsculas |
| título de bloque | `featuretitle` | 13 px, 600 |
| filas, valores | — | 13 px, `texto` |
| secundario, notas, estados | `tenue` | 13 px, `texto_tenue` |
| rango pequeño | `rangelbl` | 11 px |
| cabecera de avanzadas | `avanzadas` | 11 px, 600, línea arriba |
| código, logs | — | `Cascadia Mono`/`Consolas` 11–12 px |

Los nombres de las cosas van en `texto`; `tenue` solo para lo secundario. Nada en MAYÚSCULAS para
destacar: se destaca con peso y tamaño.

## Medidas

| Token | Valor | Uso |
|---|---|---|
| `R_CONTROL` | 8 | botones, cajas, desplegables, pestañas |
| `R_PANEL` | 12 | paneles, tablas, menús |
| `R_DIALOGO` | 16 | diálogos |
| `R_PILDORA` / `R_INDICADOR` / `R_MENUDO` | 9 / 5 / 4 | distintivos / casillas / detalles |
| `MARGEN_PANEL` | 14, 12, 14, 12 | aire interior: `margen_panel(layout)` |
| `SEPARACION_PANELES` | 10 | entre paneles y hasta el borde de la pantalla |
| `ALTO_CONTROL` | 30 | controles de la barra superior |
| `ANCHO_CHEVRON` | 22 | hueco de la flecha de un desplegable |
| `ANCHO_LINEA` | 2 | separador vertical |
| `ALFA_VELO` | 176 | opacidad del velo |

**Regla del medio lado:** un radio nunca pasa de la mitad del lado; si pasa, Qt pinta la pieza
cuadrada. Las píldoras derivan el radio con `lado // 2`.

Espaciados: 18 px entre columnas de formulario, 10 entre paneles, 6–8 dentro de un grupo, 4 entre
piezas pegadas.
