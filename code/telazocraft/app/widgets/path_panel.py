# -*- coding: utf-8 -*-
"""Panel de rutas: el usuario no deberia tener que recordar donde escribe el software."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout,
                               QApplication, QSizePolicy)

from ...common.infrastructure.apertura import abrir_carpeta  # reexportado por compatibilidad
from .. import style
from .animated_button import AnimatedButton
from .linea_guia import LineaGuia
from ...common.i18n import tr

__all__ = ["abrir_carpeta", "PathPanel"]


class _RutaEdit(QLineEdit):
    """Ruta de solo lectura cuyo doble clic selecciona el valor completo."""

    def mouseDoubleClickEvent(self, evento):
        super().mouseDoubleClickEvent(evento)
        self.selectAll()


class PathPanel(QFrame):
    """Lista de (etiqueta, ruta[, on_restablecer]) con boton de abrir y de copiar.

    Si una entrada trae un tercer elemento (un callable), se le anade ademas un boton
    «Restablecer» que lo invoca; sirve para vaciar la chascarrilla de logs desde aqui.
    """

    def __init__(self, entradas, descripcion=""):
        super().__init__()
        self.setObjectName("panel")
        # La explicación va dentro del panel, encima de las rutas: suelta sobre el fondo quedaba
        # fuera de cualquier panel.
        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(0, 0, 0, 0)
        exterior.setSpacing(0)
        if descripcion:
            aviso = QLabel(descripcion)
            aviso.setObjectName("tenue")
            aviso.setWordWrap(True)
            aviso.setContentsMargins(14, 12, 14, 0)
            exterior.addWidget(aviso)
        self._g = QGridLayout()
        exterior.addLayout(self._g)
        self._g.setContentsMargins(14, 12, 14, 12)
        self._g.setHorizontalSpacing(10)
        self._g.setVerticalSpacing(8)
        self.set_filas(entradas)

    def set_filas(self, entradas):
        """Reconstruye las filas conservando el panel y sus conexiones externas."""
        while self._g.count():
            item = self._g.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        for fila, entrada in enumerate(entradas):
            etiqueta, ruta = entrada[0], entrada[1]
            on_restablecer = entrada[2] if len(entrada) > 2 else None
            # Rótulo en texto normal, no tenue: es el nombre de la carpeta, lo primero que se lee.
            lbl = QLabel(etiqueta)
            val = _RutaEdit(str(ruta))
            val.setObjectName("rutaPanel")
            val.setReadOnly(True)
            val.setFrame(False)
            val.setCursor(Qt.IBeamCursor)
            # Una ruta larga no cabe en el panel y se queda cortada por la izquierda, que es la
            # parte que menos importa. El tooltip la da entera, y el cursor arranca al final para
            # que se vea la carpeta concreta y no el «C:\» de todas.
            val.setToolTip(str(ruta))
            val.home(False)
            val.setMinimumWidth(0)
            val.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            val.setStyleSheet("background: transparent; border: none; padding: 0;")

            b_abrir = AnimatedButton(tr("Abrir"))
            b_abrir.clicked.connect(lambda _=False, r=ruta: abrir_carpeta(r))
            b_copiar = AnimatedButton(tr("Copiar"))
            temporizador = QTimer(b_copiar)
            temporizador.setSingleShot(True)
            temporizador.setInterval(1200)
            temporizador.timeout.connect(lambda b=b_copiar: b.setText(tr("Copiar")))
            b_copiar.clicked.connect(
                lambda _=False, r=ruta, b=b_copiar, t=temporizador:
                self._copiar(r, b, t))

            # El rótulo va con su línea guía hasta el borde de la columna: los rótulos son de
            # largos muy distintos («Logs» y «Configuración de usuario»), y tras los cortos quedaba
            # un hueco en el que la vista se perdía antes de llegar a la ruta.
            # Solo coloca rótulo y línea: sin nombre de agrupador pintaba un rectángulo oscuro
            # dentro del panel, detrás de cada rótulo.
            guia = style.agrupador()
            fila_guia = QHBoxLayout(guia)
            fila_guia.setContentsMargins(0, 0, 0, 0)
            fila_guia.setSpacing(8)
            fila_guia.addWidget(lbl, 0)
            fila_guia.addWidget(LineaGuia(), 1)
            self._g.addWidget(guia, fila, 0)
            self._g.addWidget(val, fila, 1)
            self._g.addWidget(b_abrir, fila, 2)
            self._g.addWidget(b_copiar, fila, 3)
            if on_restablecer is not None:
                b_reset = AnimatedButton(tr("Restablecer"))
                b_reset.setToolTip(tr("Borra las sesiones antiguas, los informes y los diagnósticos."))
                b_reset.clicked.connect(lambda _=False, f=on_restablecer: f())
                self._g.addWidget(b_reset, fila, 4)
        self._g.setColumnStretch(1, 1)
        # Sin entradas se oculta. Con ellas, solo se ENSEÑA si ya está dentro de su pantalla: a un
        # widget sin padre, `show()` lo abre como ventana suelta durante un instante, y ese era el
        # parpadeo al arrancar el programa (30/09/2026). Sin padre basta con no ocultarlo: aparece
        # con la pantalla en la que se coloque.
        if not entradas:
            self.hide()
        elif self.parentWidget() is not None:
            self.show()

    @staticmethod
    def _copiar(ruta, boton, temporizador):
        QApplication.clipboard().setText(str(ruta))
        boton.setText(tr("Copiado ✓"))
        temporizador.start()
