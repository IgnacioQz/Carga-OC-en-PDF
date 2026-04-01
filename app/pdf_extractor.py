"""
Capa 1 — Extracción de líneas crudas del PDF.

Estrategia:
- Usamos pdfplumber con extracción de tablas (table_settings ajustados).
- Una fila válida es aquella cuya primera celda contiene el número de línea
  (múltiplo de 10: 10, 20, 30 ...) y la segunda el código de fabricante.
- Las filas de continuación (descripción multilínea) se ignoran ya que
  la descripción no se utiliza en el CSV de Softland.
"""
import re
import pdfplumber
import io
import logging

logger = logging.getLogger(__name__)

# Patrón: número de línea al inicio de fila (10, 20, 30 ...)
_RE_LINE_NUM = re.compile(r"^\d+$")

# Patrón básico para códigos de fabricante (alfanumérico con guiones/puntos/+)
_RE_CODIGO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-\+\.]{2,}$")

# Patrón precio: opcional "$", espacios, dígitos con puntos/comas
_RE_PRECIO = re.compile(r"^\$?\s*[\d.,]+$")


def extract_order_lines(pdf_bytes: bytes) -> list[dict]:
    """Extrae líneas usando REGEX en texto plano - funciona con tu PDF Danfoss"""
    raw_rows = []
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue
                
            # Split por líneas y busca patrón: "10 148B6230", "20 148B5603"...
            for line in text.split('\n'):
                line = line.strip()
                if len(line) < 10:
                    continue
                    
                # Patrón: NÚMERO_LÍNEA (10,20,30...) + space + CÓDIGO 
                match = re.match(r'^(\d{2,3})\s+([A-Z0-9][A-Z0-9\-+]{3,})', line)
                if not match:
                    continue

                num_linea, codigo = match.groups()
                resto = line[match.end():].strip()

                # ✅ Cantidad: número ANTES de "PCE"
                cantidad_match = re.search(r'(\d+)\s+PCE', resto)

                # ✅ Fecha: DD/MM/YYYY
                fecha_match = re.search(r'(\d{2}/\d{2}/\d{4})', resto)

                # ✅ Precio unitario: primer $ del resto
                precio_match = re.search(r'\$\s*([\d.,]+)', resto)

                row = {
                    "cod_fabrica": codigo,
                    "cantidad": cantidad_match.group(1) if cantidad_match else "",
                    "fecha": fecha_match.group(1) if fecha_match else "",
                    "precio": precio_match.group(1).strip() if precio_match else "",
                }
                raw_rows.append(row)
                logger.debug(
                    f"Pág {page_num} LÍNEA {num_linea}: {codigo} "
                    f"x{row['cantidad']} | {row['fecha']} | ${row['precio']}"
                )

    logger.info(f"Total filas extraídas: {len(raw_rows)}")
    return raw_rows

def _parse_row(row: list) -> dict | None:
    """
    Evalúa una fila cruda de la tabla y retorna dict si es una línea de producto.
    El PDF del proveedor (Danfoss) tiene esta estructura de columnas:
        [0] N° línea (10/20/30...)
        [1] Código fabricante
        [2] Descripción         ← ignorada
        [3] Cantidad
        [4] Unidad              ← ignorada
        [5] Fecha envío estimada
        [6] Precio neto unitario
        [7] Precio total        ← ignorado
    """
    if not row or len(row) < 6:
        return None

    # Limpiar celdas None → ""
    cells = [str(c).strip() if c else "" for c in row]

    col0 = cells[0]  # N° línea
    col1 = cells[1]  # Código fabricante
    col3 = cells[3]  # Cantidad
    col5 = cells[5]  # Fecha estimada
    col6 = cells[6] if len(cells) > 6 else ""  # Precio unitario

    # Filtro: la primera celda debe ser número de línea (10, 20, 30 ...)
    if not _RE_LINE_NUM.match(col0):
        return None

    # Filtro: segunda celda debe parecerse a un código de fabricante
    if not _RE_CODIGO.match(col1):
        return None

    # Extraer fecha (DD/MM/YYYY)
    fecha = _extract_fecha(col5)

    # El precio puede estar en col6 (normal) o col5 si hay corrimiento
    precio = col6 if _RE_PRECIO.match(col6) else (col5 if _RE_PRECIO.match(col5) else "")

    return {
        "cod_fabrica": col1,
        "cantidad":    col3,
        "fecha":       fecha,
        "precio":      precio,
    }


def _extract_fecha(valor: str) -> str:
    """Extrae fecha en formato DD/MM/YYYY. Retorna '' si no encuentra."""
    match = re.search(r"\d{2}/\d{2}/\d{4}", valor)
    return match.group(0) if match else ""
