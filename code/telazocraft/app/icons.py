from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPixmap, QIcon, QPainter, QPainterPath, QPen, QBrush, QColor, QPolygonF, QLinearGradient
import math
from . import style
def _arco_flecha(p, caja, inicio, barrido, escala):
    """Un arco con punta de flecha abierta en su extremo, en el sentido del barrido.

    Barrido negativo dibuja en sentido horario. La cabeza son dos segmentos cortos (no una
    cabeza rellena) porque a 14-15 px una cabeza sólida se convierte en una mancha; dos trazos
    siguen leyéndose como flecha con cualquier escalado de Windows.
    """
    path = QPainterPath()
    path.arcMoveTo(caja, inicio)
    path.arcTo(caja, inicio, barrido)
    p.drawPath(path)

    a, b = caja.width() / 2.0, caja.height() / 2.0
    cx, cy = caja.center().x(), caja.center().y()
    th = math.radians(inicio + barrido)
    punta = QPointF(cx + a * math.cos(th), cy - b * math.sin(th))
    # Tangente respecto al ángulo creciente; el sentido de avance sigue el signo del barrido.
    tx, ty = -a * math.sin(th), -b * math.cos(th)
    norma = math.hypot(tx, ty) or 1.0
    signo = 1.0 if barrido >= 0 else -1.0
    tx, ty = signo * tx / norma, signo * ty / norma
    largo = escala * 0.26
    medio_ancho = escala * 0.15
    base = QPointF(punta.x() - tx * largo, punta.y() - ty * largo)
    nx, ny = -ty, tx
    p.drawLine(punta, QPointF(base.x() + nx * medio_ancho, base.y() + ny * medio_ancho))
    p.drawLine(punta, QPointF(base.x() - nx * medio_ancho, base.y() - ny * medio_ancho))


def _glifo_recarga(p, r):
    """Dos flechas circulares horarias: el símbolo estándar de recargar/sincronizar.

    Sigue el diseño de assets/iconos_ref/recarga_ref.png: dos arcos semicirculares simétricos
    (giro de 180°), cada uno acabado en una punta, uno arriba-derecha y otro abajo-izquierda.
    """
    p.save()
    m = r.width() * 0.12
    caja = r.adjusted(m, m, -m, -m)
    escala = r.width()
    # Dos arcos de 135° con huecos amplios (~45°) a izquierda y derecha donde apuntan las puntas.
    # Bastante menos de 180° cada uno para que se lean como DOS flechas separadas, no como un
    # círculo casi cerrado ni dos arcos pegados.
    # Arco superior: sobre las 12, en sentido horario, con la punta cayendo hacia las 3-4.
    _arco_flecha(p, caja, 200.0, -135.0, escala)
    # Arco inferior: simétrico por rotación de 180°, bajo las 6, con la punta subiendo a las 9-10.
    _arco_flecha(p, caja, 20.0, -135.0, escala)
    p.restore()


def _glifo_mas(p, r):
    m = r.width() * 0.26
    p.drawLine(QPointF(r.center().x(), r.y() + m), QPointF(r.center().x(), r.bottom() - m))
    p.drawLine(QPointF(r.x() + m, r.center().y()), QPointF(r.right() - m, r.center().y()))


def _glifo_menos(p, r):
    m = r.width() * 0.26
    p.drawLine(QPointF(r.x() + m, r.center().y()), QPointF(r.right() - m, r.center().y()))


def _glifo_regla(p, r):
    """Una cota: dos topes y la linea entre ellos, que es lo que hace la regla del visor 3D.

    No es la regla de escolar con sus marcas: a 14 px las marcas se convierten en una mancha gris.
    Los dos topes verticales y el trazo se leen enteros a ese tamano y dicen lo mismo, "de aqui a
    aqui". Va en diagonal porque la medida del visor casi nunca cae en horizontal.
    """
    w = r.width()
    m = w * 0.22
    origen = QPointF(r.x() + m, r.bottom() - m)
    destino = QPointF(r.right() - m, r.y() + m)
    p.drawLine(origen, destino)
    # Los topes, perpendiculares al trazo: se calculan del propio vector para que sigan la diagonal
    # y no queden torcidos si algun dia cambia el margen.
    dx, dy = destino.x() - origen.x(), destino.y() - origen.y()
    largo = max(1e-6, (dx * dx + dy * dy) ** 0.5)
    nx, ny = -dy / largo * w * 0.16, dx / largo * w * 0.16
    for punto in (origen, destino):
        p.drawLine(QPointF(punto.x() - nx, punto.y() - ny),
                   QPointF(punto.x() + nx, punto.y() + ny))


def _glifo_segmentar(p, r):
    """Un polígono cerrado con sus vértices marcados: lo que se hace al marcar un bulto a clics.

    Irregular a propósito: un cuadrado se leería como «recortar» o «pantalla», y el gesto es ir
    pinchando esquinas. Los vértices van como puntos huecos, que a 14 px siguen separándose del trazo.
    """
    w, h = r.width(), r.height()
    relativos = ((0.24, 0.30), (0.62, 0.20), (0.80, 0.52), (0.58, 0.80), (0.22, 0.68))
    vertices = [QPointF(r.x() + w * a, r.y() + h * b) for a, b in relativos]
    camino = QPainterPath(vertices[0])
    for punto in vertices[1:]:
        camino.lineTo(punto)
    camino.closeSubpath()
    p.drawPath(camino)
    radio = w * 0.07
    for punto in vertices:
        p.drawEllipse(punto, radio, radio)


def pintar_tic(painter, rect, color=None, grosor=None):
    """Dibuja un tic vectorial con extremos y unión redondeados."""
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    ancho = float(rect.width())
    pen = QPen(QColor(color or style.tema_actual().sobre_acento),
               float(grosor or max(1.5, ancho * 0.13)))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    path = QPainterPath(QPointF(rect.left() + ancho * 0.22,
                                rect.top() + rect.height() * 0.52))
    path.lineTo(QPointF(rect.left() + ancho * 0.43,
                        rect.top() + rect.height() * 0.72))
    path.lineTo(QPointF(rect.left() + ancho * 0.79,
                        rect.top() + rect.height() * 0.29))
    painter.drawPath(path)
    painter.restore()


def _chevron(p, r, arriba):
    """Punta de flecha fina. Es lo que llevan los botones de los spinbox."""
    w, h = r.width(), r.height()
    ancho = w * 0.30
    alto = h * 0.15
    cx, cy = r.center().x(), r.center().y()
    y0 = cy + (alto if arriba else -alto)
    y1 = cy - (alto if arriba else -alto)
    path = QPainterPath(QPointF(cx - ancho, y0))
    path.lineTo(QPointF(cx, y1))
    path.lineTo(QPointF(cx + ancho, y0))
    p.drawPath(path)


def _glifo_pantalla_completa(p, r):
    """Cuatro esquinas abiertas: 'expandir'."""
    m = r.width() * 0.24
    largo = r.width() * 0.18
    caja = r.adjusted(m, m, -m, -m)
    for (x, y, dx, dy) in ((caja.left(), caja.top(), 1, 1),
                           (caja.right(), caja.top(), -1, 1),
                           (caja.left(), caja.bottom(), 1, -1),
                           (caja.right(), caja.bottom(), -1, -1)):
        p.drawLine(QPointF(x, y), QPointF(x + largo * dx, y))
        p.drawLine(QPointF(x, y), QPointF(x, y + largo * dy))


def _glifo_encuadrar(p, r):
    """Flecha diagonal con punta en los dos extremos: 'ajustar la vista'.

    Las cuatro esquinas hacia dentro que había antes se confundían con pantalla completa, que vive en
    la misma botonera. Una diagonal de doble punta se lee sola: estirar o recoger hasta que quepa.
    """
    m = r.width() * 0.22
    caja = r.adjusted(m, m, -m, -m)
    # De la esquina inferior izquierda a la superior derecha, como el gesto de redimensionar.
    a = QPointF(caja.left(), caja.bottom())
    b = QPointF(caja.right(), caja.top())
    p.drawLine(a, b)
    ala = r.width() * 0.20
    for punta, signo in ((a, 1.0), (b, -1.0)):
        # Las dos alas de cada punta salen del extremo hacia el centro: una en horizontal y otra en
        # vertical, que es como se dibujan las puntas del resto de glifos.
        p.drawLine(punta, QPointF(punta.x() + ala * signo, punta.y()))
        p.drawLine(punta, QPointF(punta.x(), punta.y() - ala * signo))


def _glifo_volver(p, r):
    """Flecha hacia atrás para salir del foco sin abandonar el multivisor."""
    m = r.width() * 0.24
    izquierda = r.left() + m
    centro_y = r.center().y()
    derecha = r.right() - m
    p.drawLine(QPointF(izquierda, centro_y), QPointF(derecha, centro_y))
    p.drawLine(QPointF(izquierda, centro_y),
               QPointF(izquierda + r.width() * 0.20, centro_y - r.height() * 0.20))
    p.drawLine(QPointF(izquierda, centro_y),
               QPointF(izquierda + r.width() * 0.20, centro_y + r.height() * 0.20))


def _glifo_rotar(p, r):
    """Rotar usa deliberadamente el mismo símbolo que Recargar, como pide la interfaz."""
    _glifo_recarga(p, r)


def _glifo_guardar(p, r):
    """Flecha hacia abajo sobre una bandeja: 'sacar esto a un fichero'."""
    cx = r.center().x()
    arriba = r.y() + r.height() * 0.20
    abajo = r.y() + r.height() * 0.58
    p.drawLine(QPointF(cx, arriba), QPointF(cx, abajo))
    ala = r.width() * 0.18
    path = QPainterPath(QPointF(cx - ala, abajo - ala))
    path.lineTo(QPointF(cx, abajo))
    path.lineTo(QPointF(cx + ala, abajo - ala))
    p.drawPath(path)
    bandeja = r.height() * 0.78
    m = r.width() * 0.20
    p.drawLine(QPointF(r.x() + m, bandeja), QPointF(r.right() - m, bandeja))


def _glifo_carpeta(p, r):
    """Carpeta de contorno, con su pestana: 'abrir la carpeta donde esto se guarda'.

    Solo trazo, como el resto: a 14 px un relleno es una mancha, y el contorno se recolorea solo
    al cambiar de tema.
    """
    w, h = r.width(), r.height()
    radio = w * 0.08
    izq = r.x() + w * 0.14
    der = r.right() - w * 0.14
    arriba = r.y() + h * 0.26          # tapa del cuerpo
    abajo = r.bottom() - h * 0.20
    # La pestana: sube desde la tapa sobre el tercio izquierdo, como una carpeta colgante.
    pestana_der = izq + (der - izq) * 0.42
    path = QPainterPath(QPointF(izq, abajo - radio))
    path.lineTo(QPointF(izq, r.y() + h * 0.16 + radio))
    path.quadTo(QPointF(izq, r.y() + h * 0.16), QPointF(izq + radio, r.y() + h * 0.16))
    path.lineTo(QPointF(pestana_der - radio, r.y() + h * 0.16))
    path.quadTo(QPointF(pestana_der, r.y() + h * 0.16),
                QPointF(pestana_der + w * 0.06, arriba))
    path.lineTo(QPointF(der - radio, arriba))
    path.quadTo(QPointF(der, arriba), QPointF(der, arriba + radio))
    path.lineTo(QPointF(der, abajo - radio))
    path.quadTo(QPointF(der, abajo), QPointF(der - radio, abajo))
    path.lineTo(QPointF(izq + radio, abajo))
    path.quadTo(QPointF(izq, abajo), QPointF(izq, abajo - radio))
    p.drawPath(path)


def _glifo_copiar(p, r):
    """Dos hojas superpuestas: el icono de 'copiar al portapapeles' de toda la vida.

    Solo contorno, como el resto de glifos: relleno a 14 px es una mancha, y ademas el trazo se
    recolorea solo con el tema (un PNG gris se ve mal en claro Y en oscuro).
    """
    w = r.width()
    radio = w * 0.10
    # La de atras, desplazada arriba-izquierda; la de delante, abajo-derecha.
    atras = QRectF(r.x() + w * 0.18, r.y() + w * 0.18, w * 0.50, w * 0.50)
    delante = QRectF(r.x() + w * 0.32, r.y() + w * 0.32, w * 0.50, w * 0.50)
    # De la hoja de atras solo se dibuja lo que ASOMA (una L con dos esquinas redondeadas): pintarla
    # entera cruzaria por dentro de la de delante y quedaria un garabato.
    path = QPainterPath(QPointF(delante.left(), atras.bottom()))
    path.lineTo(QPointF(atras.left() + radio, atras.bottom()))
    path.quadTo(QPointF(atras.left(), atras.bottom()), QPointF(atras.left(), atras.bottom() - radio))
    path.lineTo(QPointF(atras.left(), atras.top() + radio))
    path.quadTo(QPointF(atras.left(), atras.top()), QPointF(atras.left() + radio, atras.top()))
    path.lineTo(QPointF(atras.right() - radio, atras.top()))
    path.quadTo(QPointF(atras.right(), atras.top()), QPointF(atras.right(), atras.top() + radio))
    path.lineTo(QPointF(atras.right(), delante.top()))
    p.drawPath(path)
    p.drawRoundedRect(delante, radio, radio)


def _chevron_h(p, r, izquierda):
    """Punta de flecha horizontal. Para la navegación de imágenes (anterior/siguiente)."""
    w, h = r.width(), r.height()
    ancho = w * 0.16
    alto = h * 0.30
    cx, cy = r.center().x(), r.center().y()
    x0 = cx + (ancho if izquierda else -ancho)
    x1 = cx - (ancho if izquierda else -ancho)
    path = QPainterPath(QPointF(x0, cy - alto))
    path.lineTo(QPointF(x1, cy))
    path.lineTo(QPointF(x0, cy + alto))
    p.drawPath(path)


def _glifo_servidor(p, r):
    """Servidor: dos unidades apiladas con su piloto. Sustituye el punto de estado del servidor.

    Se pinta con el trazo (y el piloto relleno) del color de estado que reciba, así que sirve igual
    para parado (gris), activo (verde), iniciándose (ámbar) o error (rojo).
    """
    w = r.width()
    m = w * 0.14
    caja = r.adjusted(m, m, -m, -m)
    radio = w * 0.07
    h_unidad = caja.height() * 0.42
    sup = QRectF(caja.left(), caja.top(), caja.width(), h_unidad)
    inf = QRectF(caja.left(), caja.bottom() - h_unidad, caja.width(), h_unidad)
    p.drawRoundedRect(sup, radio, radio)
    p.drawRoundedRect(inf, radio, radio)
    pr = w * 0.055
    brocha = p.brush()
    p.setBrush(p.pen().color())
    for unidad in (sup, inf):
        cx = unidad.left() + unidad.width() * 0.20
        p.drawEllipse(QPointF(cx, unidad.center().y()), pr, pr)
    p.setBrush(brocha)


def _glifo_info(p, r):
    """'i' dentro de un círculo. Para avisos informativos que deben seguir el color del tema."""
    m = r.width() * 0.10
    caja = r.adjusted(m, m, -m, -m)
    p.drawEllipse(caja)
    cx = caja.center().x()
    pr = r.width() * 0.05
    brocha = p.brush()
    p.setBrush(p.pen().color())
    p.drawEllipse(QPointF(cx, caja.top() + caja.height() * 0.28), pr, pr)
    p.setBrush(brocha)
    p.drawLine(QPointF(cx, caja.top() + caja.height() * 0.46),
               QPointF(cx, caja.bottom() - caja.height() * 0.18))


def _tono_suave(p, factor=0.42):
    """Segundo tono derivado del pen que YA trae el painter, no de un color fijo.

    Los dos glifos de dominio son bicolor. Derivarlo del pen —y no leer el tema aqui— es lo que
    permite que el mismo glifo valga pintado con el acento (barra) y pintado en blanco (entrada de
    menu resaltada, donde el fondo ES el acento y un icono del color del acento desapareceria).
    """
    color = QColor(p.pen().color())
    color.setAlphaF(color.alphaF() * factor)
    return color


def _glifo_codigo(p, r):
    """Codigo QR: los tres ojos de posicion y un par de modulos de datos. Dominio de Lectoras.

    Era un codigo de BARRAS, y las lectoras leen sobre todo 2D. Se dibuja sobre una reticula de 7
    modulos, que es la que deja los ojos de 3x3 del QR real.

    A la altura a la que vive esto —la de una mayuscula, unos 9 px— la retecula fina de un QR de
    verdad se empasta en una mancha gris, asi que NO se reproduce: se conservan los tres ojos, que
    son lo que hace reconocible un QR de un vistazo. Por lo mismo se quedan fuera las cuatro
    esquinas de encuadre del original: a este tamano son cuatro puntos sucios.
    """
    lado = min(r.width(), r.height())
    margen = lado * 0.07
    caja = QRectF(r.center().x() - lado / 2.0 + margen, r.center().y() - lado / 2.0 + margen,
                  lado - margen * 2.0, lado - margen * 2.0)
    u = caja.width() / 7.0                      # modulo
    tinta = p.pen().brush()
    # Los tres ojos: cuadrado macizo de 3x3 al que se le VACIA el centro, para que quede el anillo
    # del patron de posicion. Se vacia de verdad (Clear) en vez de repintarlo con otro color porque
    # el icono es transparente y no sabemos que fondo tiene detras.
    for columna, fila in ((0, 0), (4, 0), (0, 4)):
        ojo = QRectF(caja.left() + columna * u, caja.top() + fila * u, u * 3.0, u * 3.0)
        p.fillRect(ojo, tinta)
        modo = p.compositionMode()
        p.setCompositionMode(QPainter.CompositionMode_Clear)
        p.fillRect(QRectF(ojo.left() + u, ojo.top() + u, u, u), Qt.black)
        p.setCompositionMode(modo)
    # Dos modulos de datos en el cuadrante libre, en el tono suave: dan el aire de QR sin ensuciar.
    suave = _tono_suave(p)
    for columna, fila in ((4, 4), (6, 6)):
        p.fillRect(QRectF(caja.left() + columna * u, caja.top() + fila * u, u * 1.6, u * 1.6), suave)


def _glifo_cubo(p, r):
    """Cubo isometrico: el dominio de Volumen. Silueta hexagonal, tapa y arista vertical.

    Isometrico de libro —las tres caras a 120 grados— en vez de la perspectiva floja de antes. Es
    geometria simple, asi que aguanta bien la altura de una mayuscula; la tapa lleva un velo del
    tono suave para que se lea el volumen y no un hexagono. Las esquinas de encuadre del original
    se quedan fuera por el mismo motivo que en el QR.
    """
    lado = min(r.width(), r.height()) * 0.86
    cx, cy = r.center().x(), r.center().y()
    mx = lado * 0.45                       # medio ancho
    alto = lado * 0.52                     # del centro al vertice de arriba
    cima = QPointF(cx, cy - alto)
    der_sup = QPointF(cx + mx, cy - alto / 2.0)
    der_inf = QPointF(cx + mx, cy + alto / 2.0)
    base = QPointF(cx, cy + alto)
    izq_inf = QPointF(cx - mx, cy + alto / 2.0)
    izq_sup = QPointF(cx - mx, cy - alto / 2.0)
    centro = QPointF(cx, cy)               # vertice donde concurren las tres caras visibles

    tapa = QPainterPath(cima)
    for punto in (der_sup, centro, izq_sup):
        tapa.lineTo(punto)
    tapa.closeSubpath()
    brocha = p.brush()
    p.setBrush(_tono_suave(p, 0.30))
    p.drawPath(tapa)
    p.setBrush(brocha)

    silueta = QPainterPath(cima)
    for punto in (der_sup, der_inf, base, izq_inf, izq_sup):
        silueta.lineTo(punto)
    silueta.closeSubpath()
    silueta.moveTo(centro)
    silueta.lineTo(base)                   # arista vertical del frente
    p.drawPath(silueta)


def _glifo_candado(p, r, abierto=False):
    """Candado simple; el arco abierto deja claro cuándo una fila admite cambios."""
    ancho = r.width()
    cuerpo = QRectF(r.x() + ancho * 0.18, r.y() + r.height() * 0.46,
                    ancho * 0.64, r.height() * 0.42)
    p.drawRoundedRect(cuerpo, ancho * 0.08, ancho * 0.08)
    arco = QPainterPath()
    if abierto:
        arco.moveTo(QPointF(r.x() + ancho * 0.62, r.y() + r.height() * 0.48))
        arco.cubicTo(QPointF(r.x() + ancho * 0.62, r.y() + r.height() * 0.14),
                     QPointF(r.x() + ancho * 0.25, r.y() + r.height() * 0.12),
                     QPointF(r.x() + ancho * 0.25, r.y() + r.height() * 0.34))
    else:
        arco.moveTo(QPointF(r.x() + ancho * 0.30, r.y() + r.height() * 0.47))
        arco.cubicTo(QPointF(r.x() + ancho * 0.30, r.y() + r.height() * 0.12),
                     QPointF(r.x() + ancho * 0.70, r.y() + r.height() * 0.12),
                     QPointF(r.x() + ancho * 0.70, r.y() + r.height() * 0.47))
    p.drawPath(arco)


def _glifo_enchufe(p, r, conectado):
    """Clavija y toma en horizontal, con su cable a cada lado (petición del usuario, 07/10/2026).

    Conectado: la clavija metida en la toma, un solo bloque partido por una junta. Desconectado:
    separadas, con las dos patillas a la vista. Es el icono del botón de la barra, que dice cómo
    ESTÁ la cámara seleccionada; pulsarlo la pasa al otro estado.
    """
    # En diagonal, como los enchufes de Fluent: así ocupa la caja entera y a 15 px se lee igual que
    # Recargar. En horizontal se quedaba en un tercio del alto y era un borrón.
    w = r.width()
    alto = w * 0.42
    radio = w * 0.08
    p.save()
    p.translate(r.center())
    p.rotate(-45.0)

    def cuerpo(desde, hasta):
        p.drawRoundedRect(QRectF(w * desde, -alto / 2.0, w * (hasta - desde), alto), radio, radio)

    def linea(desde, hasta, dy=0.0):
        p.drawLine(QPointF(w * desde, dy), QPointF(w * hasta, dy))

    if conectado:
        linea(-0.64, -0.34)
        cuerpo(-0.34, 0.34)
        p.drawLine(QPointF(0.0, -alto / 2.0), QPointF(0.0, alto / 2.0))   # junta clavija-toma
        linea(0.34, 0.64)
    else:
        linea(-0.66, -0.44)
        cuerpo(-0.44, -0.16)
        linea(-0.16, -0.04, -alto * 0.24)     # patillas de la clavija, a la vista
        linea(-0.16, -0.04, alto * 0.24)
        cuerpo(0.16, 0.44)
        linea(0.44, 0.66)
    p.restore()


_GLIFOS = {
    "recarga": _glifo_recarga,
    "enchufe_conectado": lambda p, r: _glifo_enchufe(p, r, True),
    "enchufe_desconectado": lambda p, r: _glifo_enchufe(p, r, False),
    "codigo": _glifo_codigo,
    "cubo": _glifo_cubo,
    "copiar": _glifo_copiar,
    "mas": _glifo_mas,
    "menos": _glifo_menos,
    "regla": _glifo_regla,
    "segmentar": _glifo_segmentar,
    "arriba": lambda p, r: _chevron(p, r, True),
    "abajo": lambda p, r: _chevron(p, r, False),
    "izquierda": lambda p, r: _chevron_h(p, r, True),
    "derecha": lambda p, r: _chevron_h(p, r, False),
    "pantalla_completa": _glifo_pantalla_completa,
    "encuadrar": _glifo_encuadrar,
    "volver": _glifo_volver,
    "rotar": _glifo_rotar,
    "guardar": _glifo_guardar,
    "servidor": _glifo_servidor,
    "info": _glifo_info,
    "carpeta": _glifo_carpeta,
    "candado": lambda p, r: _glifo_candado(p, r, False),
    "candado_abierto": lambda p, r: _glifo_candado(p, r, True),
}


def dibujar_glifo(painter, nombre, caja, color=None, grosor=None):
    """Pinta un glifo DENTRO de un painter ajeno, en la caja indicada.

    `glifo_pixmap` sirve para iconos de botones, pero un control que se pinta a si mismo —un
    desplegable con su punta de flecha— no quiere un pixmap intermedio: quiere trazar sobre su
    propio painter, con el color que toque en ese momento. Devuelve si habia glifo con ese nombre.
    """
    dibujar = _GLIFOS.get(nombre)
    if dibujar is None:
        return False
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(QColor(color or style.TEXTO))
    lado = min(caja.width(), caja.height())
    pen.setWidthF(grosor if grosor is not None else max(1.2, lado * 0.10))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    dibujar(painter, QRectF(caja))
    painter.restore()
    return True


def glifo_pixmap(nombre, size=16, color=None, grosor=None, angulo=0.0):
    """Glifo vectorial del tema actual, al tamano pedido."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    dibujar = _GLIFOS.get(nombre)
    if dibujar is None:
        return pm
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    if angulo:
        p.translate(size / 2.0, size / 2.0)
        p.rotate(float(angulo))
        p.translate(-size / 2.0, -size / 2.0)
    pen = QPen(QColor(color or style.TEXTO))
    pen.setWidthF(grosor if grosor is not None else max(1.2, size * 0.10))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    dibujar(p, QRectF(0, 0, size, size))
    p.end()
    return pm


def glifo(nombre, size=16, color=None, angulo=0.0):
    return QIcon(glifo_pixmap(nombre, size, color, angulo=angulo))




def logo_pixmap(size=128, con_fondo=True, estado=None):
    from .logo_paths import TRAZADOS, VARIANTE_LOGO
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(size, size)
    t = style.tema_actual()
    if con_fondo:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(t.superficie_opaca))
        p.drawRoundedRect(QRectF(.05, .05, .9, .9), .22, .22)
    grad = QLinearGradient(QPointF(.5, .19), QPointF(.5, .81))
    grad.setColorAt(0, QColor(t.acento_claro))
    grad.setColorAt(1, QColor(t.acento))
    path = QPainterPath()
    puntos = TRAZADOS[VARIANTE_LOGO]; i = 0
    while i < len(puntos):
        tipo, x, y = puntos[i]
        if tipo == 0: path.moveTo(x, y)
        elif tipo == 1: path.lineTo(x, y)
        elif tipo == 2:
            _, x2, y2 = puntos[i+1]; _, x3, y3 = puntos[i+2]
            path.cubicTo(x, y, x2, y2, x3, y3); i += 2
        i += 1
    p.setBrush(QBrush(grad))
    p.setPen(QPen(QBrush(grad), .035, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawPath(path)
    if estado:
        color = t.ok if estado == "encendido" else t.peligro if estado == "error" else t.texto_tenue if estado == "apagado" else t.aviso
        p.setBrush(QColor(color))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(.71, .71, .22, .22))
    p.end()
    return pm


def app_icon(estado=None):
    return QIcon(logo_pixmap(128, estado=estado))

def _glifo_inicio(p, r):
    w = r.width(); x = r.x(); y = r.y()
    path = QPainterPath(QPointF(x+w*.15,y+w*.48))
    for a,b in ((.5,.18),(.85,.48),(.78,.48),(.78,.84),(.58,.84),(.58,.61),(.42,.61),(.42,.84),(.22,.84),(.22,.48)):
        path.lineTo(x+w*a,y+w*b)
    p.drawPath(path)

def _glifo_jugadores(p, r):
    w=r.width(); x=r.x(); y=r.y()
    p.drawEllipse(QRectF(x+w*.36,y+w*.16,w*.28,w*.28))
    path=QPainterPath(QPointF(x+w*.2,y+w*.84))
    path.cubicTo(x+w*.2,y+w*.35,x+w*.8,y+w*.35,x+w*.8,y+w*.84)
    p.drawPath(path)

def _glifo_engranaje(p,r):
    w=r.width();c=r.center()
    p.drawEllipse(r.adjusted(w*.24,w*.24,-w*.24,-w*.24))
    p.drawEllipse(r.adjusted(w*.41,w*.41,-w*.41,-w*.41))
    for i in range(8):
        a=i*math.pi/4
        p.drawLine(QPointF(c.x()+math.cos(a)*w*.28,c.y()+math.sin(a)*w*.28),QPointF(c.x()+math.cos(a)*w*.4,c.y()+math.sin(a)*w*.4))

def _glifo_mas_opciones(p,r):
    w=r.width()
    for a in (.25,.5,.75):p.drawEllipse(QRectF(r.x()+w*a-w*.025,r.center().y()-w*.025,w*.05,w*.05))

_GLIFOS.update({"inicio":_glifo_inicio,"jugadores":_glifo_jugadores,"mods":_glifo_cubo,
                "copias":_glifo_guardar,"ajustes":_glifo_engranaje,"engranaje":_glifo_engranaje,
                "opciones":_glifo_mas_opciones})


def estado_icon(estado):
    from .widgets.estado_punto import pintar_punto
    pm=QPixmap(18,18);pm.fill(Qt.transparent);p=QPainter(pm)
    clave='operativa' if estado=='encendido' else 'fallo' if estado=='error' else 'inactiva' if estado=='apagado' else 'trabajando'
    pintar_punto(p,QRectF(0,0,18,18),clave,4);p.end();return QIcon(pm)
