# OC Processor — PDF → CSV Softland

Microservicio Flask que recibe un PDF de orden de compra, extrae los productos,
consulta Odoo para obtener códigos internos y genera un CSV listo para Softland.

## Instalación

```bash
pip install -r requirements.txt
```

## Variables de entorno

Crea un archivo `.env` o expórtalas directamente:

```bash
# Odoo
ODOO_URL=https://antilhue.com
ODOO_DB=antilhue
ODOO_USER=tu_usuario@antilhue.com
ODOO_PASSWORD=tu_password

# Softland (campos fijos del CSV)
SOFTLAND_RUT_PROVEEDOR=78923930
SOFTLAND_TIPO_DOC=OC5
SOFTLAND_COD_BODEGA=02
SOFTLAND_DESCUENTO_PCT=2.5

# Flask
FLASK_DEBUG=false
PORT=5000
```

## Ejecución

```bash
cd app
python app.py
```

Luego abre `http://localhost:5000` en el navegador.

## Endpoint API

`POST /procesar-oc`

| Campo  | Tipo   | Descripción                        |
|--------|--------|------------------------------------|
| orden  | string | Número de orden de compra          |
| tasa   | float  | Tasa de cambio USD → CLP           |
| pdf    | file   | PDF de la orden del proveedor      |

Retorna: archivo CSV descargable.

## Estructura del proyecto

```
oc_processor/
├── app/
│   ├── app.py           # Flask app + endpoint + UI HTML
│   ├── config.py        # Variables de configuración
│   ├── pdf_extractor.py # Capa 1: extrae filas del PDF con pdfplumber
│   ├── order_parser.py  # Capa 2: limpia códigos, precios, fechas
│   ├── odoo_service.py  # Capa 3: búsqueda batch en Odoo (XML-RPC)
│   ├── csv_builder.py   # Capa 4: genera CSV formato Softland
│   └── logger.py        # Capa 5: logging estructurado
└── requirements.txt
```

## Notas técnicas

- **Batch Odoo**: a diferencia del código original que hacía 1 llamada por producto,
  este servicio hace **1 sola llamada** con todos los códigos del pedido.
- **Limpieza de código**: se aplica la regla heredada — si el código termina en `66`
  y la posición 3 es `-`, `L` o `D`, se recorta eliminando los últimos 2 caracteres.
- **Fallback de fecha**: las líneas sin fecha de envío usan la fecha máxima del pedido.
- **Fallback de precio**: precios `na` o vacíos se reemplazan por 100.0 (lógica heredada).
- Los campos fijos del CSV (`RUT`, `OC5`, `02`) se configuran vía variables de entorno.

## Log de trazabilidad

Cada OC procesada genera un resumen en `oc_processor.log` con:
- Total de líneas procesadas
- Códigos encontrados / no encontrados en Odoo
- Detalle de faltantes con cantidad y precio
