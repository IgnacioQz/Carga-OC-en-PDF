"""
Configuración centralizada — todos los valores hardcodeados van aquí.
En producción se sobreescriben con variables de entorno.
"""
import os
from dotenv import load_dotenv

# Carga .env DESDE app/ (mismo directorio)
load_dotenv()  # ¡Automático!

class Config:
    # ── Odoo ──────────────────────────────────────────────────────────────────
    ODOO_URL      = os.getenv("ODOO_URL")
    ODOO_DB       = os.getenv("ODOO_DB")
    ODOO_USER     = os.getenv("ODOO_USER")
    ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

    # ── Softland — campos fijos del CSV ───────────────────────────────────────
    SOFTLAND_RUT_PROVEEDOR = os.getenv("SOFTLAND_RUT_PROVEEDOR")
    SOFTLAND_TIPO_DOC      = os.getenv("SOFTLAND_TIPO_DOC")
    SOFTLAND_COD_BODEGA    = os.getenv("SOFTLAND_COD_BODEGA")
    SOFTLAND_DESCUENTO_PCT = float(os.getenv("SOFTLAND_DESCUENTO_PCT"))

    # ── Flask ─────────────────────────────────────────────────────────────────
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    PORT  = int(os.getenv("PORT", "5000"))
