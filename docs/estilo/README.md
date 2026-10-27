# Guía de estilo — índice

Solo en tareas de interfaz. Lee **este índice y únicamente el archivo del tema que toques**.

- Lo que el usuario pida en el chat manda sobre la guía. Cada decisión de diseño nueva o cambiada se
  escribe en su archivo en el mismo trabajo, sin esperar a que lo pida.
- Los valores salen de `code/vision_driver/app/style.py`; si no coinciden, manda el código.

## Dos capas (13/10/2026)

Decisión del usuario: el diseño tiene que servir para **cualquier programa**, no solo para este.

1. **Sistema de diseño** (genérico): tema, superficies, controles, composición, animaciones, iconos,
   textos y errores. Vale para cualquier aplicación de escritorio PySide6 que reutilice el tema y
   los controles propios; no nombra cámaras ni pantallas concretas.
2. **Anexo de Vision Driver** (`vision_driver.md`): lo que solo tiene sentido aquí (asistente de
   SDK, cámaras, Volumen, instalador, versiones…). Una decisión nueva va al sistema si se aplicaría
   igual en otro programa; si no, al anexo.

Cómo llevarse el diseño a otro programa: `reutilizar.md`.

| Si vas a tocar… | Lee |
|---|---|
| colores, tema, tipografía, títulos, medidas y radios | `tema.md` |
| paneles, pestañas, fondos, separadores, laterales, velos | `superficies.md` |
| botones, cajas, desplegables, casillas, sliders, tablas, estados, editar y aplicar | `controles.md` |
| logo, iconos, glifos | `iconos.md` |
| animaciones, fundidos, ventanas emergentes, carga | `animaciones.md` |
| cómo se reparte una pantalla: formularios, barras, rejillas, laterales, tamaños | `composicion.md` |
| textos, traducción, idioma | `textos.md` |
| algo que ya salió mal antes | `errores.md` |
| una pantalla o ventana concreta de Vision Driver | `vision_driver.md` |
| llevarse el diseño a otro proyecto | `reutilizar.md` |

## Principios

1. Fluent sobrio: superficies planas, esquinas redondeadas, un solo acento, sin sombras.
2. Todo sale del tema: ningún color, radio ni tamaño a mano.
3. Controles propios, nunca los de Qt pelados.
4. Nada se recorta: se reparte, se elide con tooltip, baja a un scroll o la pantalla se recoloca.
5. Todo va dentro de un panel redondeado con aire alrededor.
6. Jerarquía clara: el título de cada panel destaca (negrita y mayor); los subtítulos de grupo, por
   debajo; las filas, en texto normal.
7. Lo que no aporta no se pinta: agrupadores sin fondo, controles sin borde en reposo, lo largo al
   tooltip.
8. Toda ventana emergente aparece y se va con un fundido, y lo animado parte de lo que ya hay
   (`animaciones.md`), no de cero.
9. Nada cambia sin que el usuario lo vea: lo editado y sin aplicar se marca, lo que no puede
   trabajar se apaga con su motivo, lo que no recibe datos se oscurece y lo dice.

Pruebas que lo vigilan: `test_paneles`, `test_agrupadores`, `test_controles_numericos`,
`test_aspecto_paneles`, `test_sin_recortes`, `test_barra_estable`, `test_traduccion`.
