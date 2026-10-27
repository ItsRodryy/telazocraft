import threading
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QScrollArea
from . import style
from .widgets.animated_button import AnimatedButton
from .widgets.fundido import ConFundido
from .widgets.dialogo_proceso import VentanaBase
from .widgets.fila_flexible import FilaFlexible
from ..common.i18n import tr


class Bus(QObject):
    evento = Signal(str, str, object)
    resultado = Signal(object, object, object)
    resumen = Signal(str, object, object)


def boton(texto, accion, principal=False, rol=None):
    b = AnimatedButton(tr(texto))
    if principal:
        b.setObjectName("aplicar")
    if rol or principal:
        b.setProperty("rol", rol or "principal")
    b.clicked.connect(accion)
    return b


def fila(*widgets):
    w = style.agrupador()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(8)
    for widget in widgets:
        h.addWidget(widget)
    h.addStretch()
    return w


def titulo(texto):
    w = QLabel(tr(texto))
    w.setObjectName("tituloPanel")
    return w


def acciones(*widgets):
    w = FilaFlexible(widgets)
    w.setObjectName("agrupador")
    return w


class Dialogo(VentanaBase):
    def __init__(self, padre, texto):
        super().__init__(padre)
        self.setWindowTitle(tr(texto))
        self.resize(560, 320)
        self.caja = QVBoxLayout(self)
        self.panel = style.tarjeta(titulo(texto))
        self.caja.addWidget(self.panel)
        self.formulario = self.panel.layout()

    def terminar_botones(self, texto="Aplicar"):
        cancelar = boton("Cancelar", self.reject)
        aceptar = boton(texto, self.accept, True)
        aceptar.setAutoDefault(False)
        cancelar.setDefault(True)
        cancelar.setFocus()
        self.caja.addWidget(fila(cancelar, aceptar))


def confirmar(padre, texto, accion="Continuar", cambios=(), destructivo=False):
    d = Dialogo(padre, accion)
    rotulo = QLabel(tr(texto))
    rotulo.setWordWrap(True)
    d.formulario.addWidget(rotulo)
    if cambios:
        contenido = style.agrupador()
        layout = QVBoxLayout(contenido)
        for nombre, antes, despues in cambios:
            cambio = QLabel(tr("%s: %s → %s") % (tr(nombre), str(antes), str(despues)))
            cambio.setWordWrap(True)
            layout.addWidget(cambio)
        scroll = QScrollArea()
        scroll.setObjectName("scrollEnPanel")
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(360)
        scroll.setWidget(contenido)
        d.formulario.addWidget(scroll)
    d.terminar_botones(accion)
    return d.exec() == QDialog.Accepted


class Comando(QLineEdit):
    def __init__(self):
        super().__init__()
        self.historial, self.indice = [], 0
        self.setPlaceholderText(tr("Escribe un comando de Minecraft"))

    def recordar(self):
        texto = self.text().strip()
        if texto:
            self.historial.append(texto)
        self.indice = len(self.historial)
        self.clear()
        return texto

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Up, Qt.Key_Down):
            self.indice = max(0, min(len(self.historial), self.indice + (-1 if e.key() == Qt.Key_Up else 1)))
            self.setText(self.historial[self.indice] if self.indice < len(self.historial) else "")
        else:
            super().keyPressEvent(e)


class Log(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setObjectName('log')
        self.setReadOnly(True)
        self.setMaximumBlockCount(5000)
        self.seguir = True

    def agregar(self, linea):
        color = style.tema_actual().texto
        if "ERROR" in linea:
            color = style.tema_actual().peligro
        elif "WARN" in linea:
            color = style.tema_actual().aviso
        c = QTextCursor(self.document())
        c.movePosition(QTextCursor.End)
        formato = QTextCharFormat()
        formato.setForeground(QColor(color))
        c.insertText(linea + "\n", formato)
        if self.seguir:
            self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


def opciones_boton(accion):
    from . import icons
    b=boton('',accion);b.setIcon(icons.glifo('opciones',18));b.setToolTip(tr('Más acciones'));b.setAccessibleName(tr('Más acciones'));return b


def vaciar_tabla(tabla):
    # Hide replaced cell widgets immediately; deleteLater otherwise paints them at (0,0).
    for r in range(tabla.rowCount()):
        for c in range(tabla.columnCount()):
            w=tabla.cellWidget(r,c)
            if w:w.hide()
    tabla.setRowCount(0)
