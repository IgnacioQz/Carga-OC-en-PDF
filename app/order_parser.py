"""
Capa 2 — Parser y limpieza de líneas.

Aplica toda la lógica de negocio:
  1. Limpieza de código de fabricante (sufijos -66, L66, D66)
  2. Conversión de precio (formato $ 1.234,56 → float)
  3. Fallback de fecha: si una línea no tiene fecha, usa la máxima del pedido
"""
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_DATE_FMT = "%d/%m/%Y"


def parse_lines(raw_lines: list[dict]) -> list[dict]:
    """
    Recibe lista cruda del extractor y retorna lista de dicts limpios:
        {
            "cod_fabrica":  str,   # código limpio para buscar en Odoo
            "cantidad":     int,
            "precio_float": float,
            "fecha":        str,   # "DD/MM/YYYY" garantizada
        }
    """
    # Determinar fecha máxima entre todas las líneas (para el fallback)
    fecha_max = _calcular_fecha_max(raw_lines)
    logger.info(f"Fecha máxima del pedido (fallback): {fecha_max}")

    parsed = []
    for i, line in enumerate(raw_lines):
        try:
            cod_limpio  = _limpiar_codigo(line["cod_fabrica"])
            cantidad    = _parsear_cantidad(line["cantidad"])
            precio      = _parsear_precio(line["precio"])
            fecha       = line["fecha"] if line["fecha"] else fecha_max

            parsed.append({
                "cod_fabrica":  cod_limpio,
                "cantidad":     cantidad,
                "precio_float": precio,
                "fecha":        fecha,
            })
            logger.debug(f"Línea {i+1} parseada: {cod_limpio} | qty={cantidad} | precio={precio} | fecha={fecha}")

        except Exception as e:
            logger.warning(f"Línea {i+1} descartada ({line.get('cod_fabrica','?')}): {e}")

    return parsed


# ── Limpieza de código ─────────────────────────────────────────────────────────

def _limpiar_codigo(cod: str) -> str:
    """
    Replica la lógica del código heredado:
        if cod[-2:] == '66' and (cod[3:4] in ['-', 'L', 'D']):
            cod = cod[:-2]
    Se mantiene estandarizada tal cual sin excepciones por código puntual.
    """
    if len(cod) >= 4 and cod[-2:] == "66" and cod[3:4] in ("-", "L", "D"):
        cod_limpio = cod[:-2]
        logger.debug(f"Código recortado: {cod} → {cod_limpio}")
        return cod_limpio
    return cod


# ── Parseo de cantidad ─────────────────────────────────────────────────────────

def _parsear_cantidad(raw: str) -> int:
    """Extrae el entero de la cantidad. Lanza ValueError si no es válido."""
    limpio = re.sub(r"[^\d]", "", raw)
    if not limpio:
        raise ValueError(f"Cantidad inválida: '{raw}'")
    valor = int(limpio)
    if valor <= 0:
        raise ValueError(f"Cantidad debe ser positiva, got {valor}")
    return valor


# ── Parseo de precio ───────────────────────────────────────────────────────────

def _parsear_precio(raw: str) -> float:
    """
    Convierte precio con formato del proveedor a float.
    Ejemplos:
        "$ 829,41"    → 829.41
        "$ 1.658,82"  → 1658.82
        "na"          → 100.0   (fallback del código heredado)
        ""            → 100.0
    """
    # Limpiar símbolo $ y espacios
    limpio = re.sub(r"[^a-zA-Z0-9.,]", "", raw).strip()

    if not limpio or limpio.lower() == "na":
        logger.debug(f"Precio '{raw}' → fallback 100.0")
        return 100.0

    # Formato: punto como separador de miles, coma como decimal (ej: 1.658,82)
    # → quitar puntos, reemplazar coma por punto
    if "," in limpio:
        limpio = limpio.replace(".", "").replace(",", ".")
    # Si no tiene coma, solo tiene punto → ya es formato float estándar
    # (raro en este proveedor pero defensivo)

    try:
        return float(limpio)
    except ValueError:
        logger.warning(f"No se pudo parsear precio '{raw}', usando fallback 100.0")
        return 100.0


# ── Fecha máxima ───────────────────────────────────────────────────────────────

def _calcular_fecha_max(raw_lines: list[dict]) -> str:
    """
    Calcula la fecha máxima entre todas las líneas con fecha válida.
    Si no hay ninguna fecha, retorna la fecha de hoy como último fallback.
    """
    fechas_validas = []
    for line in raw_lines:
        fecha_str = line.get("fecha", "")
        if fecha_str:
            try:
                fechas_validas.append(datetime.strptime(fecha_str, _DATE_FMT))
            except ValueError:
                pass

    if fechas_validas:
        return max(fechas_validas).strftime(_DATE_FMT)

    fallback = datetime.today().strftime(_DATE_FMT)
    logger.warning(f"No se encontraron fechas en el PDF, usando hoy: {fallback}")
    return fallback
