from .. import ajustes

VENTANA_ANCHO_MIN = 1080
VENTANA_ALTO_MIN = 720
VENTANA_ANCHO_PISO = 900
VENTANA_ALTO_PISO = 600


def tema_efectivo(preferencias):
    return "oscuro"


def cargar():
    return ajustes.cargar()


def guardar(datos):
    ajustes.guardar(datos)


def anchos_tabla(clave, longitud):
    valor = ajustes.cargar().get("tablas", {}).get(clave)
    return valor if isinstance(valor, list) and len(valor) == longitud else None


def guardar_anchos_tabla(clave, anchos):
    d = ajustes.cargar()
    d.setdefault("tablas", {})[clave] = anchos
    ajustes.guardar(d)
