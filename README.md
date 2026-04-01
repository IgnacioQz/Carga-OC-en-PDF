# 📄 Proyecto: Conversor PDF → CSV (Odoo → Softland)

## 🎯 Objetivo

Desarrollar un microservicio que reciba un PDF de orden de pedido, extraiga su información, la procese y genere un archivo CSV compatible con Softland, utilizando datos de Odoo para mapear productos.

---

## 🔄 Flujo General

1. Subir PDF (orden de pedido)
2. Extraer datos del PDF
3. Limpiar y estructurar la información
4. Consultar Odoo para obtener códigos internos
5. Generar CSV en formato requerido por Softland
6. Entregar CSV listo para carga

---

## 🧩 Componentes

### 1. Entrada (Flask)

* Endpoint para subir PDF
* Recibe parámetros como tasa de conversión

### 2. Extracción

* Convertir PDF a texto/CSV (script o librería)
* Identificar:

  * Código producto
  * Cantidad
  * Precio
  * Fecha

### 3. Normalización

* Limpiar datos:

  * Quitar símbolos ($, espacios, etc.)
  * Corregir fechas
  * Ajustar códigos

### 4. Integración con Odoo

* Buscar productos por código de fabricante
* Obtener código interno (default_code)

### 5. Generación CSV

* Construir archivo con formato fijo requerido
* Incluir:

  * Orden
  * Productos
  * Cantidades
  * Precios
  * Fechas

---

## ⚠️ Consideraciones

* El PDF puede venir desordenado → parsing flexible
* Puede haber productos no encontrados en Odoo
* El formato del CSV debe ser exacto
* Evitar consultas repetidas a Odoo (optimizar)

---

## 🚀 Alcance inicial (MVP)

* Procesar 1 PDF a la vez
* Generar CSV correctamente formateado
* Resolver mapping básico con Odoo

---

## 🔧 Futuras mejoras

* Eliminar dependencia de scripts externos
* Manejo de errores y validaciones
* Procesamiento masivo (batch)
* Logs y monitoreo

---

## 🧠 Idea central

Transformar una orden en PDF en datos estructurados y compatibles entre sistemas (Odoo → Softland), automatizando un proceso manual.

