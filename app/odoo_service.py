"""
Capa 3 — Servicio Odoo.

Mejora crítica respecto al código heredado:
  - UNA sola autenticación por request
  - UNA sola llamada search_read para TODOS los códigos del pedido
  - El código heredado hacía 1 autenticación + 1 búsqueda POR producto
    (con 26 productos = 52 llamadas HTTP → ahora son 2)
"""
import xmlrpc.client
import logging

logger = logging.getLogger(__name__)

_NOT_FOUND = "No_Existe_en_ODOO"


class OdooService:
    def __init__(self, url: str, db: str, username: str, password: str):
        self.url      = url
        self.db       = db
        self.username = username
        self.password = password
        self._uid     = None
        self._models  = None

    def _connect(self):
        """Autentica contra Odoo y almacena uid + proxy de modelos."""
        if self._uid is not None:
            return  # Ya conectado

        try:
            common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            self._uid = common.authenticate(self.db, self.username, self.password, {})

            if not self._uid:
                raise ConnectionError(
                    f"Autenticación fallida en Odoo ({self.url}) "
                    f"con usuario '{self.username}'"
                )

            self._models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
            logger.info(f"Conexión Odoo establecida | uid={self._uid}")

        except xmlrpc.client.Fault as e:
            raise ConnectionError(f"Error XML-RPC al conectar con Odoo: {e.faultString}") from e
        except Exception as e:
            raise ConnectionError(f"No se pudo conectar a Odoo ({self.url}): {e}") from e

    def buscar_codigos_batch(self, codigos_fabrica: list[str]) -> dict[str, str]:
        """
        Busca TODOS los códigos de fabricante en una sola llamada a Odoo.

        Retorna dict:
            { manufacturer_code: default_code, ... }

        Los códigos no encontrados NO aparecen en el dict
        (el csv_builder usará _NOT_FOUND como fallback).
        """
        self._connect()

        # Deduplicar para no enviar duplicados a Odoo
        codigos_unicos = list(set(codigos_fabrica))
        logger.info(f"Consultando Odoo por {len(codigos_unicos)} códigos únicos (batch)")

        try:
            resultados = self._models.execute_kw(
                self.db, self._uid, self.password,
                "product.template", "search_read",
                [[["manufacturer_code", "in", codigos_unicos]]],
                {
                    "context": {"lang": "es_CL"},
                    "fields": ["default_code", "manufacturer_code", "name"],
                    "limit": len(codigos_unicos) + 10,  # margen de seguridad
                },
            )
        except xmlrpc.client.Fault as e:
            raise ConnectionError(f"Error en búsqueda batch Odoo: {e.faultString}") from e

        # Construir mapeo manufacturer_code → default_code
        mapeo = {}
        for producto in resultados:
            mfr_code = producto.get("manufacturer_code", "")
            def_code = producto.get("default_code", "")
            if mfr_code and def_code:
                mapeo[mfr_code] = def_code

        # Log de los que no se encontraron
        no_encontrados = [c for c in codigos_unicos if c not in mapeo]
        if no_encontrados:
            logger.warning(f"Códigos NO encontrados en Odoo ({len(no_encontrados)}): {no_encontrados}")

        logger.info(f"Odoo respondió: {len(mapeo)} encontrados, {len(no_encontrados)} faltantes")
        return mapeo


NOT_FOUND_CODE = _NOT_FOUND
