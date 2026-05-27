"""
Microservicio Flask - Procesador de Órdenes de Compra
Convierte PDF de OC → CSV compatible con Softland
"""
import io
import logging
from flask import Flask, request, jsonify, send_file, render_template
from pdf_extractor import extract_order_lines
from order_parser import parse_lines
from odoo_service import OdooService
from csv_builder import build_csv
from logger import setup_logger, log_processing_summary
from config import Config

app = Flask(__name__)
logger = setup_logger(__name__)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/procesar-oc", methods=["POST"])
def procesar_oc():
    orden    = request.form.get("orden", "").strip()
    tasa_raw = request.form.get("tasa", "").strip()
    pdf_file = request.files.get("pdf")

    if not orden:
        return jsonify({"error": "El campo 'orden' es requerido"}), 400
    if not tasa_raw:
        return jsonify({"error": "El campo 'tasa' es requerido"}), 400
    if not pdf_file or pdf_file.filename == "":
        return jsonify({"error": "Se requiere un archivo PDF"}), 400

    try:
        equi = float(tasa_raw)
        if equi <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({"error": "La tasa de cambio debe ser un número positivo"}), 400

    logger.info(f"[OC:{orden}] Inicio de procesamiento | tasa={equi}")

    try:
        pdf_bytes   = pdf_file.read()
        raw_lines   = extract_order_lines(pdf_bytes)
        logger.info(f"[OC:{orden}] Líneas extraídas del PDF: {len(raw_lines)}")

        if not raw_lines:
            return jsonify({"error": "No se encontraron líneas de producto en el PDF"}), 422

        parsed_lines = parse_lines(raw_lines)
        logger.info(f"[OC:{orden}] Líneas parseadas válidas: {len(parsed_lines)}")

        if not parsed_lines:
            return jsonify({"error": "No se pudieron parsear líneas válidas del PDF"}), 422

        codigos_fabrica = [l["cod_fabrica"] for l in parsed_lines]
        odoo = OdooService(
            url=Config.ODOO_URL,
            db=Config.ODOO_DB,
            username=Config.ODOO_USER,
            password=Config.ODOO_PASSWORD,
        )
        mapeo_odoo = odoo.buscar_codigos_batch(codigos_fabrica)
        logger.info(f"[OC:{orden}] Odoo: {len(mapeo_odoo)} encontrados de {len(codigos_fabrica)}")

        csv_content = build_csv(
            orden=orden,
            equi=equi,
            parsed_lines=parsed_lines,
            mapeo_odoo=mapeo_odoo,
        )

        log_processing_summary(logger, orden, parsed_lines, mapeo_odoo)

        csv_bytes = io.BytesIO(csv_content.encode("utf-8"))
        return send_file(
            csv_bytes,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"OC_{orden}_softland.csv",
        )

    except ConnectionError as e:
        logger.error(f"[OC:{orden}] Error conexión Odoo: {e}")
        return jsonify({"error": f"No se pudo conectar a Odoo: {str(e)}"}), 503
    except Exception as e:
        logger.exception(f"[OC:{orden}] Error inesperado: {e}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
