"""Verificación HTTPS con el almacén de certificados del sistema."""


def activar():
    import truststore
    truststore.inject_into_ssl()
