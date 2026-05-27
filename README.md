# 📄 OC Processor — PDF → CSV Softland

Microservicio Flask que automatiza el procesamiento de órdenes de compra: recibe un PDF del proveedor, extrae los productos, consulta Odoo para obtener códigos internos y genera un CSV listo para importar en Softland.

> Desarrollado durante práctica profesional para optimizar un proceso manual de ingreso de OC en una empresa con ERP Odoo + Softland.

---

## ¿Qué problema resuelve?

El proceso original requería revisar manualmente cada PDF de orden de compra, buscar códigos en Odoo producto por producto e ingresar los datos en Softland. Este microservicio automatiza ese flujo completo en segundos.

---

## Stack

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-black?logo=flask)
![Docker](https://img.shields.io/badge/Docker-containerizado-2496ED?logo=docker&logoColor=white)
![Odoo](https://img.shields.io/badge/Odoo-XML--RPC-875A7B)
![pdfplumber](https://img.shields.io/badge/pdfplumber-extracción_PDF-red)

---

## Endpoint

### `POST /procesar-oc`

| Campo   | Tipo   | Descripción                      |
|---------|--------|----------------------------------|
| `orden` | string | Número de orden de compra        |
| `tasa`  | float  | Tasa de cambio USD → CLP         |
| `pdf`   | file   | PDF de la orden del proveedor    |

**Retorna:** archivo CSV descargable, listo para importar en Softland.

---

## Arquitectura

El procesamiento está dividido en capas desacopladas:

```
oc_processor/
├── app/
│   ├── app.py              # Flask app + endpoints
│   ├── config.py           # Variables de configuración (env vars)
│   ├── pdf_extractor.py    # Capa 1: extrae filas del PDF con pdfplumber
│   ├── order_parser.py     # Capa 2: limpia códigos, precios, fechas
│   ├── odoo_service.py     # Capa 3: consulta batch a Odoo (XML-RPC)
│   ├── csv_builder.py      # Capa 4: genera CSV formato Softland
│   ├── logger.py           # Capa 5: logging estructurado
│   ├── templates/
│   │   └── index.html      # UI — interfaz web
│   └── static/
│       └── style.css       # Estilos (dark/light mode)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Decisiones técnicas destacadas

### 🚀 Batch query a Odoo
El código original realizaba una llamada XML-RPC por cada producto del pedido. Este servicio agrupa todos los códigos y realiza **una sola llamada**, reduciendo significativamente la latencia en órdenes con muchos ítems.

### 🧹 Limpieza de códigos
Se implementó la regla heredada del sistema: si un código termina en `66` y la posición 3 es `-`, `L` o `D`, se recortan los últimos 2 caracteres antes de consultar Odoo.

### 📅 Fallback de fecha
Las líneas del PDF que no incluyen fecha de envío toman automáticamente la fecha máxima del pedido.

### 💲 Fallback de precio
Los precios en blanco o con valor `na` se reemplazan por `100.0` (lógica heredada del sistema contable).

### 🌐 Tasa de cambio automática
La UI consume el endpoint `/dolar-observado` para precargar la tasa USD/CLP desde la API del Banco Central de Chile, evitando ingreso manual.

### 🎨 UI con dark/light mode
Interfaz estilo terminal con soporte dark/light mode, panel de log en tiempo real y descarga automática del CSV generado.

---

## Configuración

Copia el archivo de ejemplo y completa con tus valores:

```bash
cp app/.env.example app/.env
```

```env
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database_name
ODOO_USER=your_user@example.com
ODOO_PASSWORD=your_password

SOFTLAND_RUT_PROVEEDOR=00000000-0
SOFTLAND_TIPO_DOC=OC5
SOFTLAND_COD_BODEGA=01
SOFTLAND_DESCUENTO_PCT=0.0

FLASK_DEBUG=false
PORT=5000
```

---

## Log de trazabilidad

Cada OC procesada genera un resumen en `oc_processor.log`:

```
[2025-05-20 10:32:11] OC #4521 procesada
  - Líneas totales: 18
  - Encontrados en Odoo: 15
  - No encontrados: 3
    · COD-123A → qty: 2, precio: 45.00
    · COD-456B → qty: 1, precio: 120.00
    · COD-789C → qty: 5, precio: 30.00
```

---

## Cómo levantar el servicio

```bash
# Clonar el repo
git clone https://github.com/IgnacioQz/OC-processor
cd oc-processor

# Configurar variables de entorno
cp app/.env.example app/.env
# editar .env con tus datos

# Levantar con Docker Compose
docker compose up --build

# O build manual
docker build -t oc-processor .
docker run -p 5000:5000 --env-file app/.env oc-processor
```

La interfaz queda disponible en `http://localhost:5000`

---

## Autor

**Ignacio Quiero Zepeda**  
Analista Programador  
[LinkedIn](#) · [GitHub](https://github.com/IgnacioQz)
