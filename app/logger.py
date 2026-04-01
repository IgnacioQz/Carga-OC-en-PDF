"""
Capa 6 — Logger estructurado.

Configura logging con formato consistente para trazabilidad.
Cada OC procesada queda registrada con: códigos encontrados,
faltantes en Odoo, tiempos y errores.
"""
import logging
import sys
from odoo_service import NOT_FOUND_CODE


def setup_logger(name: str) -> logging.Logger:
    """
    Configura y retorna un logger con salida a stdout y archivo.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Ya configurado

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(formatter)

    # Handler archivo (rotativo simple)
    try:
        file_handler = logging.FileHandler("oc_processor.log", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        pass  # En entornos sin permisos de escritura, solo stdout

    logger.addHandler(stdout_handler)
    return logger


def log_processing_summary(
    logger: logging.Logger,
    orden: str,
    parsed_lines: list[dict],
    mapeo_odoo: dict[str, str],
) -> None:
    """
    Registra un resumen completo del procesamiento de una OC.
    Útil para auditoría y diagnóstico rápido.
    """
    total = len(parsed_lines)
    encontrados = [l for l in parsed_lines if mapeo_odoo.get(l["cod_fabrica"])]
    faltantes   = [l for l in parsed_lines if not mapeo_odoo.get(l["cod_fabrica"])]

    logger.info("=" * 60)
    logger.info(f"RESUMEN OC {orden}")
    logger.info(f"  Total líneas procesadas : {total}")
    logger.info(f"  Encontrados en Odoo     : {len(encontrados)}")
    logger.info(f"  No encontrados en Odoo  : {len(faltantes)}")

    if faltantes:
        logger.warning(f"  Códigos FALTANTES:")
        for line in faltantes:
            logger.warning(
                f"    → {line['cod_fabrica']} "
                f"(qty={line['cantidad']}, precio={line['precio_float']})"
            )

    logger.info("=" * 60)
