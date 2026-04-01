"""
Capa 4 — Constructor del CSV para Softland.

Header: se usa exactamente el string original que Softland acepta,
        incluyendo encoding con caracteres cortados (N mero, C digo, etc.)
        No modificar — cualquier cambio puede romper la importación.
"""
import logging
from datetime import datetime
from config import Config
from odoo_service import NOT_FOUND_CODE

logger = logging.getLogger(__name__)

_DATE_FMT = "%d/%m/%Y"

# Header original tal cual lo requiere Softland — NO modificar
SOFTLAND_HEADER = (
    "N mero de Orden,Proveedor,Condici n de pago,Moneda,Equivalencia,Centro de Costo,"
    "Fecha de Orden,Fecha Entrega Final,N mero Nota Vta/Cotiz, rea de Negocio,Contacto,"
    "C digo Producto,Partida o Talla,Pieza o Color,Fecha Vcto.,Cantidad,Precio Unitario,"
    "Porcentaje descuento 1,Valor Descuento 1,Porcentaje descuento 2,Valor Descuento 2,"
    "Porcentaje descuento 3,Valor Descuento 3,Porcentaje descuento 4,Valor Descuento 4,"
    "Porcentaje descuento 5,Valor Descuento 5,Total Descuento L nea,Total L nea,"
    "Fecha de Entrega,Centro de Costo Detalle,Detalle Producto,Subtotal Orden,"
    "Porcentaje descuento 1 Orden,Valor Descuento 1 Orden,Porcentaje descuento 2 Orden,"
    "Valor Descuento 2 Orden,Porcentaje descuento 3 Orden,Valor Descuento 3 Orden,"
    "Porcentaje descuento 4 Orden,Valor Descuento 4 Orden,Porcentaje descuento 5 Orden,"
    "Valor Descuento 5 Orden,Total Descuento Orden,Total Afecto I.V.A Orden,"
    "Total Exento I.V.A Orden,Porcentaje Flete Orden,Valor Flete Orden,"
    "Porcentaje Embalaje Orden,Valor Embalaje Orden,"
    "C digo impuesto 1vvalor Afecto impuesto 1,Valor Total Impuesto 1,"
    "C digo impuesto 2,Valor Afecto impuesto 2,Valor Total Impuesto 2,"
    "C digo impuesto 3,Valor Afecto impuesto 3,Valor Total Impuesto 3,"
    "C digo impuesto 4,Valor Afecto impuesto 4,Valor Total Impuesto 4,"
    "C digo impuesto 5,Valor Afecto impuesto 5,Valor Total Impuesto 5,"
    "C digo impuesto 6,Valor Afecto impuesto 6,Valor Total Impuesto 6,"
    "C digo impuesto 7,Valor Afecto impuesto 7,Valor Total Impuesto 7,"
    "C digo impuesto 8,Valor Afecto impuesto 8,Valor Total Impuesto 8,"
    "C digo impuesto 9,Valor Afecto impuesto 9,Valor Total Impuesto 9,"
    "C digo impuesto 10,Valor Afecto impuesto 10,Valor Total Impuesto 10,"
    "Total Final,Tipo Orden de Compra"
)


def build_csv(
    orden: str,
    equi: float,
    parsed_lines: list[dict],
    mapeo_odoo: dict[str, str],
) -> str:
    """
    Construye y retorna el contenido completo del CSV como string,
    con el header original de Softland en la primera línea.
    """
    fecha_hoy = datetime.now().strftime(_DATE_FMT)
    fecha_max = _fecha_maxima(parsed_lines)

    lineas_csv = [SOFTLAND_HEADER]

    for line in parsed_lines:
        cod_fabrica   = line["cod_fabrica"]
        default_code  = mapeo_odoo.get(cod_fabrica, NOT_FOUND_CODE)
        cantidad      = line["cantidad"]
        precio_usd    = line["precio_float"]
        fecha_entrega = line["fecha"]

        # Precio va directo desde el PDF (USD), sin dividir por equi.
        # equi se registra solo como dato informativo en el campo Equivalencia.
        precio_conv = precio_usd
        monto_desc  = round(precio_conv * cantidad * (Config.SOFTLAND_DESCUENTO_PCT / 100), 2)

        if default_code == NOT_FOUND_CODE:
            logger.warning(
                f"Línea OC {orden} | {cod_fabrica} → {NOT_FOUND_CODE} "
                f"(qty={cantidad}, precio={precio_usd})"
            )

        fila = _construir_fila(
            orden=orden,
            fecha_hoy=fecha_hoy,
            fecha_entrega=fecha_entrega,
            fecha_max=fecha_max,
            default_code=default_code,
            cantidad=cantidad,
            precio_conv=precio_conv,
            monto_desc=monto_desc,
            equi=equi,
        )
        lineas_csv.append(fila)

    if len(lineas_csv) <= 1:
        return "No existe Orden"

    logger.info(f"CSV generado: {len(lineas_csv) - 1} líneas de producto")
    return "\n".join(lineas_csv)


def _construir_fila(
    orden: str,
    fecha_hoy: str,
    fecha_entrega: str,
    fecha_max: str,
    default_code: str,
    cantidad: int,
    precio_conv: float,
    monto_desc: float,
    equi: float,
) -> str:
    c = ","

    fila = (
        f"{orden},"
        f"{Config.SOFTLAND_RUT_PROVEEDOR},"
        f"{Config.SOFTLAND_TIPO_DOC},"
        f"{Config.SOFTLAND_COD_BODEGA},"
        f"{equi},"
        f","
        f"{fecha_hoy},"
        f"{fecha_entrega},"
        f"{c*3}"
        f"{default_code.rstrip()},"
        f"{c*3}"
        f"{cantidad},"
        f"{precio_conv},"
        f"{Config.SOFTLAND_DESCUENTO_PCT},"
        f"{monto_desc}"
        f"{c*11}"
        f"{fecha_max}"
        f"{c*14}"
        f"0,0"
        f"{c*35}"
        f"1"
    )
    return fila


def _fecha_maxima(parsed_lines: list[dict]) -> str:
    """Retorna la fecha más tardía entre todas las líneas parseadas."""
    fechas = []
    for line in parsed_lines:
        fecha_str = line.get("fecha", "")
        if fecha_str:
            try:
                fechas.append(datetime.strptime(fecha_str, _DATE_FMT))
            except ValueError:
                pass

    if fechas:
        return max(fechas).strftime(_DATE_FMT)

    return datetime.today().strftime(_DATE_FMT)