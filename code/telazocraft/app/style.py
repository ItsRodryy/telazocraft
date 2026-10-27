# -*- coding: utf-8 -*-
"""Temas Fluent de vision_driver, aplicables en caliente."""

from dataclasses import dataclass, replace

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget

from ..common.infrastructure import ui_prefs


@dataclass(frozen=True)
class Tema:
    nombre: str
    fondo: str
    superficie_opaca: str
    superficie_alta: str
    borde: str
    borde_sutil: str
    texto: str
    texto_tenue: str
    texto_fuerte: str
    acento: str
    acento_hover: str
    acento_pressed: str
    acento_claro: str
    ok: str
    ok_claro: str
    aviso: str
    peligro: str
    peligro_claro: str
    overlay: str
    mica: bool = True
    opacidad_nav: float = 0.68
    # Color de texto/glifo que va ENCIMA del acento. Blanco por defecto (el verde de siempre lo
    # admite); con acentos claros (dorado, blanco) se recalcula a casi-negro por contraste.
    sobre_acento: str = "#ffffff"
    # Cámara desconectada a mano o sin su SDK (decisión del usuario, 07/10/2026): naranja, distinto
    # del ámbar de `aviso`, que ya dicen la simulación y el trabajo en curso. Semántico: no cambia
    # con el tema de color, solo con claro u oscuro.
    desconectada: str = "#ee7a3c"


OSCURO = Tema(
    "oscuro", "#0b1416", "#10191c", "#17242a", "#26363c", "#1b282d",
    "#d7e2e4", "#8fa3a8", "#f0f6f7", "#147d70", "#1a917f", "#0f6357",
    "#2bb3a1", "#1f9d5b", "#2fbf74", "#d99a3a", "#c8483c", "#e35c4d",
    "#29e0a0",
)

CLARO = Tema(
    "claro", "#eef3f4", "#ffffff", "#e7eef0", "#cdd9db", "#dde6e7",
    "#12262b", "#4d6469", "#07171b", "#147d70", "#0f6357", "#0b4d44",
    "#0f6357", "#1c8b50", "#1c8b50", "#b9791f", "#b53b30", "#b53b30",
    "#0f8f66", desconectada="#c9561c",
)


class _Bus(QObject):
    cambiado = Signal()


_bus = None
_actual = OSCURO
_animaciones = True

# Radios del sistema. Se INTERPOLAN en el QSS (%(r_control)d ...): antes existian como constantes
# pero el QSS repetia los numeros a mano, asi que cambiar la constante no cambiaba nada. Eran
# decorativas.
R_CONTROL = 8
R_PANEL = 12
R_DIALOGO = 16
# Piezas menudas: indicadores, barras y asas. Antes cada regla del QSS llevaba su numero a mano —3,
# 4, 5, 6, 7, 9, 10— y el resultado eran esquinas distintas por toda la aplicacion. Estos tres
# tokens cubren todo lo que no es un control ni un panel.
R_MENUDO = 4        # asas de scrollbar, ranuras de slider: casi recto, solo mata el pico
R_INDICADOR = 5     # casilla de verificacion, y el asa de scroll al pasar por encima
R_PILDORA = 9       # pastillas y capsulas: aviso, toggle, distintivos
# Las lineas de separacion: su grosor y la media cana que redondea los extremos. El radio es la
# mitad del grosor, que es lo que convierte la barra en una linea con los cabos suavizados.
ANCHO_LINEA = 2
R_LINEA = ANCHO_LINEA // 2
# Piezas en pildora: sliders y barras de desplazamiento. Cada radio se DERIVA de su lado, porque
# Qt tiene una trampa: si el radio pasa de la mitad del lado, no lo recorta, lo IGNORA y pinta la
# pieza cuadrada. Asi salian el asa blanca del slider (radio 8 en 14 px) y el asa del scroll (radio
# 4 en 4 px). Con el radio calculado aqui no puede volver a pasar.
ALTO_CARRIL = 4                 # carril del slider
R_CARRIL = ALTO_CARRIL // 2
LADO_ASA = 14                   # asa del slider: circulo de verdad
R_ASA = LADO_ASA // 2
ANCHO_SCROLL = 12               # lo que ocupa la barra de desplazamiento
GROSOR_SCROLL = 4               # su asa en reposo: una guia fina
GROSOR_SCROLL_ACTIVO = 8        # y al pasar por encima, mas gruesa para poder cogerla
# Nombres de objeto de los `QWidget` que solo existen para colocar cosas. Un `QWidget` sin nombre
# hereda el `QWidget { background: fondo }` general y, dentro de una tarjeta o de la barra, pinta un
# rectangulo oscuro: es el fallo que se vio en Pruebas, en la barra superior y en Carpetas. Todo
# contenedor de layout dentro de una superficie lleva uno de estos nombres (el general es
# `agrupador`) y el QSS los deja transparentes. `tests/comun/test_agrupadores.py` lo vigila.
AGRUPADORES = ("agrupador", "columnaFormulario", "bloqueCamara", "zonaBarra")

DURACION_HOVER_MS = 120
DURACION_FUNDIDO_MS = 150
# Sitio que se reserva a la derecha de un desplegable para su punta de flecha. Vive aqui porque lo
# necesitan a la vez el QSS (como `padding-right`) y quien pinta el chevron (`ComboSinRueda`,
# `CameraSelector`, `DomainSelector`): si cada uno llevara su numero, el texto acabaria pisando la
# flecha en cuanto uno de los dos cambiara.
ANCHO_CHEVRON = 22
LADO_CHEVRON = 14
# Alto de un control de la barra superior y su aire vertical interno (el `padding: 6px 10px` de
# `QToolButton`, mas abajo). La barra la fijan los botones de icono con `setFixedSize(30, 30)`, asi
# que lo que le quepa dentro a un `QToolButton` son 30 - 2*6 = 18 px: quien pinte un icono ahi
# —`DomainSelector`, `CameraSelector`— tiene que mirar este techo o hara crecer la barra ENTERA.
ALTO_CONTROL = 30
PADDING_CONTROL_V = 6


def alto_contenido_control():
    """Pixeles utiles dentro de un control de la barra. El techo de cualquier icono que vaya ahi."""
    return ALTO_CONTROL - 2 * PADDING_CONTROL_V
# Aire interior de un panel. Con el margen que Qt trae de serie —9 px— los botones quedaban pegados
# al borde de su tarjeta, que es lo que hace que un panel se vea barato. Se declara aquí para que
# todos los paneles del programa respiren igual.
MARGEN_PANEL = (14, 12, 14, 12)


def margen_panel(layout):
    """Aplica el aire interior estándar de un panel. Devuelve el layout, para encadenar."""
    layout.setContentsMargins(*MARGEN_PANEL)
    return layout


# Aire entre paneles vecinos y entre un panel y el borde de su pantalla. Un panel redondeado nunca
# va pegado a otro borde: pegado a una caja recta se ve una esquina curva dentro de una recta.
SEPARACION_PANELES = 10
# Velo de «no se puede trabajar / sin imagen»: negro a esta opacidad (0–255) y el texto en blanco,
# igual en cualquier tema. Lo usan `CapaBloqueo` (pantallas) y `ImageViewer.velo` (visores).
ALFA_VELO = 176


def tarjeta(*widgets):
    """Un panel redondeado (`QFrame#panel`) con el aire estándar y, dentro, los widgets dados.

    Todo contenido de una pantalla va en un panel: suelto sobre el fondo parece a medio montar.
    Devuelve el marco; su layout vertical es `marco.layout()`.
    """
    marco = QFrame()
    marco.setObjectName("panel")
    capa = margen_panel(QVBoxLayout(marco))
    for widget in widgets:
        capa.addWidget(widget)
    return marco


def agrupador(widget=None):
    """Marca un `QWidget` de layout como transparente. Sin argumento, crea uno nuevo."""
    widget = QWidget() if widget is None else widget
    widget.setObjectName("agrupador")
    return widget


def bus():
    global _bus
    if _bus is None:
        _bus = _Bus()
    return _bus


def tema_actual():
    return _actual


def _luminancia(color):
    """Luminancia relativa WCAG 0..1 para calcular contraste de texto."""
    canales = (color.redF(), color.greenF(), color.blueF())
    lineales = tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                     for c in canales)
    return 0.2126 * lineales[0] + 0.7152 * lineales[1] + 0.0722 * lineales[2]


def contraste(col_a, col_b):
    """Relación de contraste WCAG entre dos colores."""
    la = _luminancia(QColor(col_a))
    lb = _luminancia(QColor(col_b))
    claro, oscuro = max(la, lb), min(la, lb)
    return (claro + 0.05) / (oscuro + 0.05)


def _paleta_acento(base_hex):
    """De un solo tono deriva (acento, hover, pressed, claro, sobre_acento).

    hover mas claro, pressed mas oscuro, claro mas luminoso; el texto encima es blanco o casi-negro
    segun la luminancia del acento, para que dorados/blancos sigan siendo legibles.
    """
    base = QColor(base_hex)
    hover = base.lighter(118)
    pressed = base.darker(125)
    claro = base.lighter(145)
    oscuro, blanco = "#0b1416", "#ffffff"
    sobre = oscuro if contraste(base_hex, oscuro) >= contraste(base_hex, blanco) else blanco
    return base.name(), hover.name(), pressed.name(), claro.name(), sobre


# --- temas de color -------------------------------------------------------------------------
#
# Ocho paletas completas, no solo un acento: TODO el software cambia (fondo, paneles, bordes,
# texto y acento). El truco para que sean serias y no un arcoiris es un "sistema tonal": se fija
# la SATURACION y la LUMINOSIDAD de cada rol (fondo, superficie, borde, texto...) y solo se mueve
# el TONO. Asi el morado y el azul se ven igual de sobrios, con el mismo contraste. Los colores
# semanticos (ok/aviso/peligro) NO cambian: verde=bien, ambar=ojo, rojo=mal, en todos los temas.
#
# El seed es el acento vivo; su TONO tine el resto. El orden es el que se ve en Interfaz.
TEMAS_COLOR = {
    "rojo": "#d47f74",
    "naranja": "#d98a4a",
    "ambar": "#cbab4c",
    "lima": "#9fb457",
    "verde": "#74b98d",
    "turquesa": "#3bb0a4",
    "cian": "#4fa8c4",
    "azul": "#6b93d6",
    "morado": "#9d84cf",
    "magenta": "#c778c0",
    "rosa": "#d98cae",
    "gris": "#8b95a4",
}
TEMA_COLOR_DEFECTO = "gris"         # gris y oscuro de serie (decisión del usuario, 06/10/2026)

# (saturacion, luminosidad) por rol. Curva OSCURA y curva CLARA. Fijas para todos los tonos.
_ROLES_OSCURO = {
    "fondo": (0.16, 0.070), "superficie_opaca": (0.15, 0.105), "superficie_alta": (0.14, 0.150),
    "borde": (0.16, 0.260), "borde_sutil": (0.15, 0.185),
    "texto": (0.10, 0.900), "texto_tenue": (0.10, 0.630), "texto_fuerte": (0.12, 0.970),
}
_ROLES_CLARO = {
    "fondo": (0.32, 0.950), "superficie_opaca": (0.20, 0.995), "superficie_alta": (0.24, 0.930),
    "borde": (0.24, 0.800), "borde_sutil": (0.22, 0.880),
    "texto": (0.30, 0.120), "texto_tenue": (0.16, 0.400), "texto_fuerte": (0.40, 0.060),
}


def _hsl(h, s, l):
    c = QColor()
    c.setHslF(h, max(0.0, min(1.0, s)), max(0.0, min(1.0, l)))
    return c.name()


def construir_tema(nombre, seed_hex, oscuro=True):
    """Paleta completa a partir de un tono: fondo/superficies/bordes/texto tenidos + acento vivo."""
    h, s_seed, _l, _a = QColor(seed_hex).getHslF()
    if h < 0:
        h = 0.0                                 # gris puro: tono neutro
    # Un seed poco saturado (gris) debe dar neutros DE VERDAD, no un azul-gris: se escala la tinta
    # de fondos/bordes/texto por la saturacion del propio color. Los vivos (azul, morado...) no se
    # tocan (su saturacion ya supera el umbral).
    f = min(1.0, s_seed / 0.55)
    ac, hov, pre, clr, sobre = _paleta_acento(seed_hex)
    roles = _ROLES_OSCURO if oscuro else _ROLES_CLARO
    n = {rol: _hsl(h, s * f, l) for rol, (s, l) in roles.items()}
    sem = OSCURO if oscuro else CLARO           # semanticos fijos por luminosidad base
    return Tema(
        nombre, n["fondo"], n["superficie_opaca"], n["superficie_alta"], n["borde"],
        n["borde_sutil"], n["texto"], n["texto_tenue"], n["texto_fuerte"],
        ac, hov, pre, clr, sem.ok, sem.ok_claro, sem.aviso, sem.peligro, sem.peligro_claro, clr,
        sobre_acento=sobre, desconectada=sem.desconectada)


def _color_marcado():
    """Morado fuerte para lo que se marca ENCIMA de una imagen de cámara (polígonos, máscaras).

    Es el tono del tema «morado» con la saturación al máximo, y es el mismo en todos los temas, como
    los semánticos: el fondo de estas marcas es la foto, no la interfaz, y con el acento del tema
    gris las marcas se perdían sobre la imagen (petición del usuario, 30/09/2026).
    """
    h, _s, _l, _a = QColor(TEMAS_COLOR["morado"]).getHslF()
    return _hsl(h, 0.95, 0.62)


COLOR_MARCADO = _color_marcado()


def desde_preferencias(preferencias, mica_forzada=None):
    oscuro = ui_prefs.tema_efectivo(preferencias) != "claro"
    nombre = str(preferencias.get("tema_color", TEMA_COLOR_DEFECTO))
    seed = TEMAS_COLOR.get(nombre, TEMAS_COLOR[TEMA_COLOR_DEFECTO])
    base = construir_tema(nombre, seed, oscuro=oscuro)
    mica = bool(preferencias.get("transparencia", True) and
                preferencias.get("backdrop", "mica") != "ninguno")
    if mica_forzada is not None:
        mica = bool(mica_forzada)
    return replace(base, mica=mica,
                   opacidad_nav=float(preferencias.get("opacidad_nav", 0.68)))


def _rgba(hex_color, alpha):
    c = hex_color.lstrip("#")
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return "rgba(%d,%d,%d,%.3f)" % (r, g, b, alpha)


def qss(t):
    superficie = _rgba(t.superficie_opaca, 0.76) if t.mica else t.superficie_opaca
    nav = _rgba(t.superficie_opaca, t.opacidad_nav) if t.mica else t.superficie_opaca
    # El fondo del area central es SOLIDO y del color del tema. Antes era "transparent" con mica, y
    # entonces se veia el backdrop gris de Windows en vez del tema: el fondo no cambiaba nunca.
    fondo_base = t.fondo
    # La línea que separa las dos columnas de un formulario. Sale del color de texto fuerte del
    # tema —blanco en los oscuros, casi negro en los claros— rebajado para que marque la división
    # sin competir con los rótulos. Derivada del token, nunca un color literal.
    linea_formulario = _rgba(t.texto_fuerte, 0.32)
    return """
* { color: %(texto)s; font-family: 'Segoe UI', 'Arial'; font-size: 13px; }
QMainWindow { background: transparent; }
QDialog, QWidget { background: %(fondo)s; }
QWidget#central, QWidget#body, QWidget#page, QWidget#paramswrap,
QStackedWidget#stack { background: %(fondo_base)s; }
QLabel { background: transparent; }

QFrame#topbar { background: %(superficie)s; border: none; border-bottom: 1px solid %(borde)s; }
QFrame#panel, QFrame#params {
    background: %(superficie)s; border: 1px solid %(borde)s; border-radius: %(r_panel)dpx;
}
/* La cámara con la que se está trabajando, dentro de la rejilla de visores: se distingue por el
   acento del tema, así que sigue al tema sin que nadie tenga que repintar nada a mano. */
QFrame#panel[activa="true"] {
    border: 2px solid %(acento)s;
}
/* Bloque agrupador DENTRO de un panel: sin borde, solo un fondo que lo separa de lo de al lado.
   Un `#panel` anidado dibujaría caja dentro de caja. */
QFrame#panelSuave {
    background: %(superficie_alta)s; border: none; border-radius: %(r_control)dpx;
}
/* Agrupadores que SOLO existen para el layout: columnas de un formulario y bloques de la barra
   superior. Sin esto heredan el `QWidget { background: fondo }` de arriba y dibujan un rectángulo
   oscuro dentro de la tarjeta o de la barra, que es lo que se veía detrás del selector de cámaras
   y detrás de las dos columnas de las pruebas. */
%(agrupadores)s { background: transparent; }
/* Separador vertical entre las dos columnas de un formulario: una barra fina del color de primer
   plano del tema, con los extremos suavizados. No usa `QFrame.VLine`, que se pinta con los colores
   nativos de la plataforma y salía como una franja negra. */
QFrame#separadorFormulario {
    background: %(linea_formulario)s; border: none; border-radius: %(r_linea)dpx;
    min-width: %(ancho_linea)dpx; max-width: %(ancho_linea)dpx; margin: 4px 0;
}
QLabel#titulo, QLabel#featuretitle { color: %(texto_fuerte)s; font-size: 15px; font-weight: 600; }
QLabel#featuretitle { font-size: 13px; }
QLabel#rangelbl { color: %(texto_tenue)s; font-size: 11px; }
QLabel#tenue, QLabel#estadoMotor { color: %(texto_tenue)s; }
/* Pantalla que ahora no puede trabajar (`widgets/capa_bloqueo.py`): velo oscuro y el motivo en
   blanco, igual en cualquier tema, como se diseñó para Fusión y medición. */
QFrame#capaBloqueo { background-color: rgba(0, 0, 0, %(alfa_velo)d); border: none; }
QLabel#motivoBloqueo { color: white; font-size: 18px; font-weight: 600; background: transparent; }
/* Parámetro de cámara cambiado y sin aplicar todavía: su rótulo en el acento. */
QLabel#rotuloParametro[pendiente="true"] { color: %(acento)s; font-weight: 600; }
/* Título de panel: destaca sobre el resto del panel (regla general, 13/10/2026). */
QLabel#tituloPanel { color: %(texto_fuerte)s; font-size: 15px; font-weight: 600; }
/* Subtítulo de un grupo dentro de un panel («Profundidad», «Filtros»…): tamaño normal, negrita y
   tenue, en minúscula. Por debajo del título del panel y por encima de las filas. */
QLabel#grupoParametros { color: %(texto_tenue)s; font-weight: 600; }
/* Distintivo: "hay una version nueva". Pastilla de acento, para que se vea sin gritar. */
QLabel#aviso {
    background: %(acento)s; color: %(sobre_acento)s; font-weight: 600;
    border-radius: %(r_pildora)dpx; padding: 3px 10px;
}
/* Estado de una cámara en la ventana de SDK: contorno del color semántico, sin relleno, para que
   se lea de un vistazo sin competir con el acento de la acción principal. */
QLabel#pastillaLista {
    background: transparent; color: %(ok)s; border: 1px solid %(ok)s;
    border-radius: %(r_pildora)dpx; font-weight: 600; padding: 3px 10px;
}
QLabel#pastillaFalta {
    background: transparent; color: %(aviso_estado)s; border: 1px solid %(aviso_estado)s;
    border-radius: %(r_pildora)dpx; font-weight: 600; padding: 3px 10px;
}
QLabel#pastillaFallo {
    background: transparent; color: %(peligro)s; border: 1px solid %(peligro)s;
    border-radius: %(r_pildora)dpx; font-weight: 600; padding: 3px 10px;
}
/* Lo que se va a perder si se sigue (desinstalar sin conservar los datos): texto en el color de
   peligro, sin relleno, debajo de la casilla que lo provoca. */
QLabel#avisoPeligro { background: transparent; color: %(peligro)s; font-weight: 600; }
/* Final de una ventana de progreso que salió bien: el mismo trato en verde, con qué hacer ahora. */
QLabel#mensajeOk { background: transparent; color: %(ok_claro)s; font-weight: 600; }
/* El código de GitHub que el usuario pega en el navegador: grande, espaciado y sobre su caja. */
QLabel#codigoSesion {
    background: %(superficie_alta)s; color: %(texto_fuerte)s; font-size: 28px; font-weight: 600;
    font-family: "Cascadia Mono", "Consolas", "DejaVu Sans Mono", monospace; letter-spacing: 4px;
    border-radius: %(r_control)dpx; padding: 10px 16px;
}

QPushButton {
    background: %(superficie_alta)s; border: 1px solid %(borde)s;
    border-radius: %(r_control)dpx; padding: 7px 16px;
}
QPushButton:hover { background: %(acento_hover)s; color: %(sobre_acento)s; }
QPushButton:pressed { background: %(acento_pressed)s; }
QPushButton:disabled { color: %(texto_tenue)s; background: %(borde_sutil)s; }
QListWidget { background: transparent; border: none; outline: none; }
QListWidget::item { border-radius: %(r_control)dpx; padding: 6px; }
QListWidget::item:selected { background: %(acento)s; color: %(sobre_acento)s; }
QListWidget::item:hover { background: %(superficie_alta)s; }
QLabel[nivel="error"] { color: %(peligro)s; }
QLabel[nivel="aviso"] { color: %(aviso_estado)s; }
QPushButton[rol="ok"] { background: %(ok)s; color: %(texto_fuerte)s; }
QPushButton[rol="peligro"] { background: %(peligro)s; color: %(texto_fuerte)s; }
QPushButton[rol="aviso"] { background: %(aviso_estado)s; color: %(fondo)s; }
QPushButton[rol="principal"] { background: %(acento)s; color: %(sobre_acento)s; }
QPushButton[rol="ok"]:hover { background: %(ok_claro)s; }
QPushButton[rol="peligro"]:hover { background: %(peligro_claro)s; }
QPushButton[rol="aviso"]:hover { background: %(aviso_estado)s; }
QPushButton[rol]:disabled { color: %(texto_tenue)s; background: %(borde_sutil)s; }
QPushButton[nav="true"] { text-align: left; padding: 12px; background: transparent; }
QPushButton[nav="true"]:checked { background: %(superficie_alta)s; color: %(acento_claro)s; }
/* Cifra grande de los resúmenes de Inicio. */
QLabel#cifra { color: %(texto_fuerte)s; font-size: 22px; font-weight: 600; }
/* Chip de estado: pastilla de contorno; el tono semántico solo cambia el color, nunca el tamaño. */
QLabel[chip="true"] { background: transparent; color: %(texto_tenue)s; border: 1px solid %(borde)s; border-radius: %(r_pildora)dpx; padding: 2px 10px; }
QLabel[chip="true"][tono="ok"] { color: %(ok_claro)s; border-color: %(ok)s; }
QLabel[chip="true"][tono="aviso"] { color: %(aviso_estado)s; border-color: %(aviso_estado)s; font-weight: 600; }
QLabel[chip="true"][tono="peligro"] { color: %(peligro_claro)s; border-color: %(peligro)s; font-weight: 600; }
QPushButton#modebtn { padding: 7px 20px; }
QPushButton#modebtn:checked { background: %(acento)s; border-color: %(acento)s; color: %(sobre_acento)s; }
/* Capturar es la acción principal de la pantalla y se le da más cuerpo a propósito, pero SOLO a lo
   ancho (`34px` de padding lateral) y en peso de letra. La altura es la misma que la del resto de
   la barra —mismo padding vertical y misma fuente—: un botón más alto que sus vecinos descuadra la
   fila entera y deja el campo «Nombre» y la carpeta flotando. */
QPushButton#capturar {
    background: %(acento)s; border: 1px solid %(acento)s; border-radius: %(r_control)dpx;
    padding: 7px 34px; font-weight: 600; color: %(sobre_acento)s;
}
/* `#pasada` (Iniciar pasada en Captura, Iniciar/Parar del servidor) es una acción de acento pero
   del MISMO tamaño que cualquier otro botón: mismo padding que el `QPushButton` general. Así el
   Iniciar del servidor mide igual que Reiniciar. */
QPushButton#pasada {
    background: %(acento)s; border: 1px solid %(acento)s; border-radius: %(r_control)dpx;
    padding: 7px 16px; font-weight: 600; color: %(sobre_acento)s;
}
/* Botones que son solo un glifo: cuadrados, sin padding lateral. */
QPushButton#iconbtn { padding: 4px; border-radius: %(r_control)dpx; }
/* Flechas de los spinbox: dos círculos independientes, sin bloque exterior ni separador. */
QPushButton#spinbtn {
    padding: 0; min-width: 18px; max-width: 18px; min-height: 18px; max-height: 18px;
    border: 1px solid %(borde_sutil)s; border-radius: %(r_pildora)dpx; background: transparent;
}
QPushButton#spinbtn:hover { background: %(acento_hover)s; border-color: %(acento_hover)s; }
QPushButton#spinbtn:pressed { background: %(acento_pressed)s; }
QPushButton#spinbtn:disabled { background: transparent; border-color: %(borde_sutil)s; }
QPushButton#capturar:hover, QPushButton#pasada:hover {
    background: %(acento_hover)s; border-color: %(acento_hover)s;
}
QPushButton#aplicar {
    background: %(acento)s; border-color: %(acento)s; color: %(sobre_acento)s;
    padding: 7px 16px; font-size: 13px; font-weight: 400;
}
QPushButton#aplicar:hover { background: %(acento_hover)s; border-color: %(acento_hover)s; }
/* Aplicar solo se enciende cuando hay algo que aplicar. Un boton de acento permanente pide que lo
   pulses siempre, y aqui casi nunca hay nada pendiente: se convierte en ruido. Sin la propiedad
   `pendiente` (el Aplicar de Interfaz) el boton sigue siendo de acento, como hasta ahora. */
QPushButton#aplicar[pendiente="false"] {
    background: %(superficie_alta)s; border-color: %(borde)s; color: %(texto_tenue)s;
}
QPushButton#aplicar[pendiente="false"]:hover {
    background: %(acento_hover)s; border-color: %(acento_hover)s; color: %(sobre_acento)s;
}
QPushButton#aplicar:disabled {
    background: %(borde_sutil)s; border-color: %(borde_sutil)s; color: %(texto_tenue)s;
}
/* El barrido de Pruebas: misma accion principal que Capturar, mismo tamano (incluida la altura). */
QPushButton#barrido {
    background: %(acento)s; border: 1px solid %(acento)s; border-radius: %(r_control)dpx;
    padding: 7px 34px; font-weight: 600; color: %(sobre_acento)s;
}
QPushButton#barrido:hover { background: %(acento_hover)s; border-color: %(acento_hover)s; }
QPushButton#capturar[auto="true"], QPushButton#pasada[grabando="true"],
QPushButton#barrido[barriendo="true"] {
    background: %(peligro)s; border-color: %(peligro)s;
}
QPushButton#capturar[auto="true"]:hover, QPushButton#pasada[grabando="true"]:hover,
QPushButton#barrido[barriendo="true"]:hover {
    background: %(peligro_claro)s; border-color: %(peligro_claro)s;
}

/* Progreso: la misma pastilla de acento que el resto, sin texto encima. */
QProgressBar {
    background: %(borde_sutil)s; border: 1px solid %(borde)s; border-radius: %(r_control)dpx;
    height: 12px; text-align: center;
}
QProgressBar::chunk { background: %(ok)s; border-radius: %(r_indicador)dpx; }

/* Controles de entrada: PLANOS en reposo. El borde permanente convertia cualquier formulario en una
   reja de cajas; aqui el contorno solo aparece cuando el raton pasa por encima o el control tiene el
   foco, que es cuando dice algo. El fondo tenue basta para saber que se puede escribir. */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: %(superficie_alta)s; border: 1px solid transparent;
    border-radius: %(r_control)dpx; padding: 6px 10px;
}
QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover { border-color: %(borde)s; }
QComboBox:on { border-color: %(borde)s; }
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: %(acento)s; }
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {
    color: %(texto_tenue)s; background: %(superficie)s;
}
QLineEdit[invalido="true"] { border-color: %(peligro_claro)s; }
QSpinBox, QDoubleSpinBox { min-width: 120px; }
/* Cajas de valor corto («30 ×»): el minimo general no las deja encoger y, en un panel estrecho,
   desbordan su fila hasta que las flechas se dibujan encima de la cifra. Ver `SpinBox.compactar`. */
QSpinBox[compacto="true"], QDoubleSpinBox[compacto="true"] { min-width: 0px; }
/* La flecha del desplegable se queda sin sitio a proposito: la pinta `ComboSinRueda` con el mismo
   chevron vectorial que los botones de incremento. La nativa solo se puede cambiar por un PNG. */
QComboBox::drop-down { border: none; width: 0px; }
QComboBox { padding-right: %(ancho_chevron)dpx; }
QComboBox QAbstractItemView {
    background: %(superficie_opaca)s; border: 1px solid %(borde)s;
    border-radius: %(r_control)dpx; padding: 4px;
    color: %(texto)s;
    selection-background-color: %(acento)s; selection-color: %(sobre_acento)s; outline: none;
}
QComboBox QAbstractItemView::item {
    min-height: 26px; padding: 2px 8px; border-radius: %(r_control)dpx; border: none;
    color: %(texto)s;
}
QComboBox QAbstractItemView::item:hover { background: %(superficie_alta)s; }
QComboBox QAbstractItemView::item:selected {
    background: %(acento)s; color: %(sobre_acento)s;
}

/* Los menus de la barra superior (camaras, dominio) eran los ultimos restos de Windows a la vista:
   fondo del sistema, esquinas cuadradas y seleccion azul. */
QMenu {
    background: %(superficie_opaca)s; border: 1px solid %(borde)s;
    border-radius: %(r_panel)dpx; padding: 6px;
}
QMenu::item {
    padding: 7px 28px 7px 12px; border-radius: %(r_control)dpx; color: %(texto)s;
}
QMenu::item:selected { background: %(acento)s; color: %(sobre_acento)s; }
QMenu::item:disabled { color: %(texto_tenue)s; }
QMenu::separator { height: 1px; background: %(borde_sutil)s; margin: 5px 8px; }
QMenu::indicator { width: 0px; }

/* Botones con menu propio (`CameraSelector`, `DomainSelector`): mismo reposo plano que los
   desplegables. Su flecha tambien se pinta a mano, asi que la nativa se anula. */
QToolButton {
    background: %(superficie_alta)s; border: 1px solid transparent;
    border-radius: %(r_control)dpx; padding: 6px 10px; color: %(texto)s;
}
QToolButton:hover { border-color: %(borde)s; }
QToolButton:pressed, QToolButton:checked { border-color: %(acento)s; }
QToolButton::menu-indicator { width: 0px; image: none; }
/* Los dos que llevan menú reservan a su derecha el hueco del chevron que pintan ellos mismos. */
QToolButton#camsel, QToolButton#domsel,
QToolButton#variantes { padding-right: %(ancho_chevron)dpx; }

QCheckBox, QRadioButton { color: %(texto)s; padding: 0 4px; background: transparent; }
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px; height: 16px; border: 1px solid %(texto_tenue)s; background: transparent;
}
QCheckBox::indicator { border-radius: %(r_indicador)dpx; }
/* Circulos DE VERDAD, no esquinas: el radio es la mitad del lado. No sustituir por un token. */
QRadioButton::indicator { border-radius: %(r_control)dpx; }
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background: %(acento)s; border-color: %(acento)s;
}
/* Las casillas de la aplicacion son `widgets/toggle.py` (interruptores pintados a mano: QSS no sabe
   animar la posicion de un pulgar). Las reglas de arriba quedan para las casillas que trae Qt por
   dentro en sus propios dialogos (QMessageBox, QFileDialog), que no son nuestras. */

/* Slider minimalista: sin fondo propio (como `QWidget` pintaba un rectangulo oscuro dentro del
   panel), carril en pildora y asa circular. El asa mide LADO_ASA en los dos sentidos: el margen
   negativo la saca del carril lo justo para que su alto sea igual a su ancho. */
QSlider { background: transparent; }
QSlider::groove:horizontal {
    height: %(alto_carril)dpx; background: %(borde)s; border: none;
    border-radius: %(r_carril)dpx;
}
QSlider::sub-page:horizontal { background: %(acento)s; border-radius: %(r_carril)dpx; }
QSlider::add-page:horizontal { background: %(borde)s; border-radius: %(r_carril)dpx; }
QSlider::handle:horizontal {
    background: %(texto_fuerte)s; border: none;
    width: %(lado_asa)dpx; height: %(lado_asa)dpx; margin: -%(sobra_asa)dpx 0;
    border-radius: %(r_asa)dpx;
}
QSlider::groove:vertical {
    width: %(alto_carril)dpx; background: %(borde)s; border: none;
    border-radius: %(r_carril)dpx;
}
QSlider::add-page:vertical { background: %(acento)s; border-radius: %(r_carril)dpx; }
QSlider::sub-page:vertical { background: %(borde)s; border-radius: %(r_carril)dpx; }
QSlider::handle:vertical {
    background: %(texto_fuerte)s; border: none;
    width: %(lado_asa)dpx; height: %(lado_asa)dpx; margin: 0 -%(sobra_asa)dpx;
    border-radius: %(r_asa)dpx;
}
QSlider::handle:disabled, QSlider::sub-page:disabled, QSlider::add-page:disabled {
    background: %(borde_sutil)s;
}

QListWidget#nav {
    background: %(nav)s; border: none; border-right: 1px solid %(borde)s;
    outline: none; padding: 8px 6px;
}
QListWidget#nav::item { padding: 10px 14px; border-radius: %(r_control)dpx; margin-bottom: 4px; }
QListWidget#nav::item:hover { background: %(superficie_alta)s; }
QListWidget#nav::item:selected { background: %(acento)s; color: %(sobre_acento)s; }

/* La caja redondea solo ABAJO. Redondeando las cuatro esquinas, la de arriba se curvaba por debajo
   de la pestana activa, que llega recta hasta el borde: quedaba un escalon y la pestana parecia
   pegada encima en vez de nacer de la caja. Es el aspecto "superpuesto" de Pruebas > Pasadas. */
/* Las pestanas no tienen caja: su contenido son paneles redondeados con aire alrededor. La caja
   recta de antes dejaba los paneles redondeados pegados dentro de una esquina recta. Las pestanas
   son pildoras sueltas, y el hueco bajo ellas es el mismo que separa dos paneles. */
QTabWidget::pane {
    border: none; background: transparent; border-radius: %(r_panel)dpx; top: %(separacion_paneles)dpx;
}
QTabWidget > QStackedWidget, QTabBar { background: transparent; border-radius: %(r_panel)dpx; }
QTabBar::tab {
    padding: 8px 16px; background: %(superficie_alta)s; margin-right: 6px;
    border: 1px solid %(borde_sutil)s; border-radius: %(r_control)dpx;
}
QTabBar::tab:hover { background: %(borde)s; }
QTabBar::tab:selected {
    background: %(acento)s; color: %(sobre_acento)s; border-color: %(acento)s;
}
QScrollArea { border: none; background: transparent; }
/* Scroll DENTRO de un panel: el viewport y su contenido no pintan fondo, se ve el del panel.
   Si no, el viewport pinta un bloque oscuro de esquinas rectas dentro de la tarjeta redondeada. */
QScrollArea#scrollEnPanel > QWidget#qt_scrollarea_viewport,
QScrollArea#scrollEnPanel > QWidget#qt_scrollarea_viewport > QWidget { background: transparent; }
/* Grupo con título dentro de un panel: sin caja propia. Con el fondo heredado pintaba un bloque
   oscuro dentro de la tarjeta; el título en negrita basta para separar los grupos. */
QGroupBox {
    background: transparent; border: none; margin-top: 22px; padding-top: 4px;
}
QGroupBox::title {
    subcontrol-origin: margin; subcontrol-position: top left; left: 0px; padding: 0px;
    color: %(texto_fuerte)s; font-weight: 600;
}
/* Separador fino dentro de los paneles. */
QFrame#sep { border: none; border-top: 1px solid %(borde_sutil)s; max-height: 1px; }
/* Cabecera de un bloque de opciones poco habituales. */
QLabel#avanzadas {
    color: %(texto_tenue)s; font-size: 11px; font-weight: 600;
    border-top: 1px solid %(borde_sutil)s; padding-top: 8px; margin-top: 6px;
}
QLabel#codigofiltro { font-family: 'Cascadia Mono', 'Consolas', monospace; font-size: 11px; }

QTableWidget, QTableView {
    background: %(superficie_opaca)s; border: 1px solid %(borde)s;
    border-radius: %(r_panel)dpx;
    selection-background-color: %(acento)s; outline: none;
}
/* El viewport pinta su fondo hasta el borde recto y tapaba por dentro las esquinas redondeadas de
   la tabla: se veia la curva del borde con un pico opaco debajo. Con el mismo radio, la esquina
   queda limpia. */
QTableWidget QWidget, QTableView QWidget,
QTableWidget::viewport, QTableView::viewport {
    background: %(superficie_opaca)s; border-radius: %(r_panel)dpx;
}
/* El propio QHeaderView es un QWidget hijo de la tabla: sin esta regla, más específica que la
   anterior, su fondo (el área NO cubierta por secciones, a la derecha del último dato) heredaba
   `superficie_opaca` y se veía una franja más oscura que las cabeceras. Debe igualar al tono de
   las secciones. */
QTableWidget QHeaderView, QTableView QHeaderView { background: %(superficie_alta)s; }
/* Sin rejilla y con aire: con la rejilla, cada dato de solo
   lectura quedaba dentro de su cajita y parecia un campo de escribir. Aqui no se edita nada. */
QTableWidget::item, QTableView::item { padding: 5px 8px; border: none; }
QTableWidget::item:selected, QTableView::item:selected { background: %(acento)s; color: %(sobre_acento)s; }
QHeaderView::section {
    background: %(superficie_alta)s; border: none; border-bottom: 1px solid %(borde)s;
    padding: 6px 10px; color: %(texto_tenue)s;
}
/* El separador de columnas: es lo que se arrastra para ensanchar una. */
QHeaderView::section:horizontal { border-right: 1px solid %(borde_sutil)s; }
QHeaderView::section:first { border-top-left-radius: %(r_panel)dpx; }
QHeaderView::section:last { border-top-right-radius: %(r_panel)dpx; }
QTableCornerButton::section { background: %(superficie_alta)s; border: none; border-top-left-radius: %(r_panel)dpx; }
QPlainTextEdit#log {
    background: %(superficie_opaca)s; border: 1px solid %(borde)s; border-radius: %(r_panel)dpx;
    font-family: 'Cascadia Mono', 'Consolas', monospace; font-size: 12px; padding: 8px;
}
/* Barras de desplazamiento: finas, sin flechas y sin pista visible. Ocupaban 15 px de ancho con un
   asa de 8 px de radio que se veía como un tubo gordo al lado del contenido; ahora son una guía de
   8 px que se ensancha y se aclara al pasar por encima, así que se ve dónde estás sin robar sitio.
   Los botones de flecha se quedan a 0: nadie los usa y descuadran las esquinas redondeadas. */
/* El asa es una pildora: su radio es la mitad de su grosor, en reposo y al pasar por encima. Antes
   el radio superaba ese medio grosor y Qt la pintaba con esquinas. */
QScrollBar:vertical { background: transparent; width: %(ancho_scroll)dpx; margin: 0; border: none; }
QScrollBar::handle:vertical {
    background: %(borde)s; border: none; min-height: 32px;
    margin: 2px %(margen_scroll)dpx; border-radius: %(r_scroll)dpx;
}
QScrollBar::handle:vertical:hover {
    background: %(texto_tenue)s; margin: 2px %(margen_scroll_activo)dpx;
    border-radius: %(r_scroll_activo)dpx;
}
QScrollBar::handle:vertical:pressed {
    background: %(acento)s; margin: 2px %(margen_scroll_activo)dpx;
    border-radius: %(r_scroll_activo)dpx;
}
QScrollBar:horizontal { background: transparent; height: %(ancho_scroll)dpx; margin: 0; border: none; }
QScrollBar::handle:horizontal {
    background: %(borde)s; border: none; min-width: 32px;
    margin: %(margen_scroll)dpx 2px; border-radius: %(r_scroll)dpx;
}
QScrollBar::handle:horizontal:hover {
    background: %(texto_tenue)s; margin: %(margen_scroll_activo)dpx 2px;
    border-radius: %(r_scroll_activo)dpx;
}
QScrollBar::handle:horizontal:pressed {
    background: %(acento)s; margin: %(margen_scroll_activo)dpx 2px;
    border-radius: %(r_scroll_activo)dpx;
}
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
/* Barra vertical de un scroll DENTRO de un panel: pista oscura con las esquinas redondeadas
   (decisión del usuario, 14/10/2026). La pintaba el contenedor de Qt, recto y con el fondo de la
   página; ahora el contenedor no pinta nada y la pista es la propia barra. */
QScrollArea#scrollEnPanel > QWidget#qt_scrollarea_vcontainer { background: transparent; }
QScrollArea#scrollEnPanel QScrollBar:vertical {
    background: %(fondo)s; border-radius: %(r_pista_scroll)dpx;
}

QStatusBar { background: %(superficie)s; color: %(texto_tenue)s; border-top: 1px solid %(borde)s; }
QStatusBar QLabel { color: %(texto_tenue)s; }
QStatusBar::item { border: none; }
QToolTip { background: %(superficie_opaca)s; color: %(texto)s; border: 1px solid %(borde)s; border-radius: %(r_control)dpx; padding: 4px 8px; }
""" % {
        "fondo": t.fondo, "fondo_base": fondo_base, "superficie": superficie,
        "linea_formulario": linea_formulario,
        "superficie_opaca": t.superficie_opaca,
        "superficie_alta": t.superficie_alta, "nav": nav, "borde": t.borde,
        "borde_sutil": t.borde_sutil, "texto": t.texto, "texto_tenue": t.texto_tenue,
        "texto_fuerte": t.texto_fuerte, "acento": t.acento, "acento_hover": t.acento_hover,
        "acento_pressed": t.acento_pressed, "acento_claro": t.acento_claro,
        "sobre_acento": t.sobre_acento,
        "ok": t.ok, "ok_claro": t.ok_claro, "aviso_estado": t.aviso, "peligro": t.peligro,
        "peligro_claro": t.peligro_claro,
        "r_control": R_CONTROL, "r_panel": R_PANEL, "r_dialogo": R_DIALOGO,
        "r_menudo": R_MENUDO, "r_indicador": R_INDICADOR, "r_pildora": R_PILDORA,
        "r_linea": R_LINEA, "ancho_linea": ANCHO_LINEA,
        "separacion_paneles": SEPARACION_PANELES, "alfa_velo": ALFA_VELO,
        "agrupadores": ", ".join("QWidget#%s" % nombre for nombre in AGRUPADORES),
        "alto_carril": ALTO_CARRIL, "r_carril": R_CARRIL,
        "lado_asa": LADO_ASA, "r_asa": R_ASA, "sobra_asa": (LADO_ASA - ALTO_CARRIL) // 2,
        "ancho_scroll": ANCHO_SCROLL, "r_pista_scroll": ANCHO_SCROLL // 2,
        "margen_scroll": (ANCHO_SCROLL - GROSOR_SCROLL) // 2, "r_scroll": GROSOR_SCROLL // 2,
        "margen_scroll_activo": (ANCHO_SCROLL - GROSOR_SCROLL_ACTIVO) // 2,
        "r_scroll_activo": GROSOR_SCROLL_ACTIVO // 2,
        "ancho_chevron": ANCHO_CHEVRON,
    }


def _publicar(t):
    global FONDO, SUPERFICIE, SUPERFICIE_ALTA, BORDE, TEXTO, TEXTO_TENUE, TEXTO_FUERTE
    global ACENTO, ACENTO_CLARO, SOBRE_ACENTO, OK, OK_CLARO, PELIGRO, PELIGRO_CLARO, DESCONECTADA
    DESCONECTADA = t.desconectada
    FONDO, SUPERFICIE, SUPERFICIE_ALTA, BORDE = t.fondo, t.superficie_opaca, t.superficie_alta, t.borde
    TEXTO, TEXTO_TENUE, TEXTO_FUERTE = t.texto, t.texto_tenue, t.texto_fuerte
    # El color del texto SOBRE el acento. Lo necesita cualquier glifo que vaya dentro de un botón
    # de acción: con el color de texto normal salía blanco sobre morado y cantaba.
    ACENTO, ACENTO_CLARO, SOBRE_ACENTO = t.acento, t.acento_claro, t.sobre_acento
    OK, OK_CLARO, PELIGRO, PELIGRO_CLARO = t.ok, t.ok_claro, t.peligro, t.peligro_claro


def aplicar_tema(app, tema):
    """Pone el tema en toda la aplicación, salvo que sea EXACTAMENTE el que ya tiene.

    `setStyleSheet` sobre la aplicación obliga a Qt a repasar el estilo de todos los controles. Al
    mostrarse, la ventana principal vuelve a pedir el tema (por la mica, que necesita la ventana
    nativa) y casi siempre es el mismo: con todas las pantallas construidas eso eran 4,5 s con la
    ventana en blanco y Windows diciendo «no responde» (medido el 30/09/2026).
    """
    global _actual, QSS
    if tema == _actual and app.styleSheet() == QSS:
        return
    _actual = tema
    _publicar(tema)
    QSS = qss(tema)
    app.setStyleSheet(QSS)
    bus().cambiado.emit()


def animaciones_activas():
    return _animaciones


def set_animaciones(activas):
    global _animaciones
    _animaciones = bool(activas)


_publicar(_actual)
QSS = qss(_actual)
