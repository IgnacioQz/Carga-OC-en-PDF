"""
Microservicio Flask - Procesador de Órdenes de Compra
Convierte PDF de OC → CSV compatible con Softland
"""
import io
import logging
from flask import Flask, request, jsonify, send_file, render_template_string
from pdf_extractor import extract_order_lines
from order_parser import parse_lines
from odoo_service import OdooService
from csv_builder import build_csv
from logger import setup_logger, log_processing_summary
from config import Config

app = Flask(__name__)
logger = setup_logger(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Procesador OC</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500&family=IBM+Plex+Mono&display=swap');

    :root {
      --bg:       #F5F4F0;
      --surface:  #FFFFFF;
      --border:   rgba(0,0,0,0.10);
      --border-hover: rgba(0,0,0,0.20);
      --accent:   #185FA5;
      --accent-hover: #0C447C;
      --accent-bg: #E6F1FB;
      --text:     #1a1a1a;
      --muted:    #6B6A66;
      --hint:     #9E9D99;
      --sans:     'IBM Plex Sans', sans-serif;
      --mono:     'IBM Plex Mono', monospace;
      --radius:   10px;
      --radius-lg: 14px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--sans);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }

    .wrap { width: 100%; max-width: 520px; }

    .brand { margin-bottom: 2rem; }

    .eyebrow {
      font-size: 11px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--hint);
      margin-bottom: 6px;
      font-family: var(--mono);
    }

    h1 { font-size: 24px; font-weight: 500; color: var(--text); }
    h1 em { font-style: normal; color: var(--accent); }

    .sub { font-size: 14px; color: var(--muted); margin-top: 4px; line-height: 1.5; }

    .card {
      background: var(--surface);
      border: 0.5px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 1.75rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

    .field { margin-bottom: 1.25rem; }

    label {
      display: block;
      font-size: 12px;
      font-weight: 500;
      color: var(--muted);
      margin-bottom: 6px;
      letter-spacing: 0.04em;
    }

    input[type="text"], input[type="number"] {
      width: 100%;
      background: var(--bg);
      border: 0.5px solid var(--border);
      border-radius: var(--radius);
      padding: 0.6rem 0.85rem;
      color: var(--text);
      font-family: var(--sans);
      font-size: 14px;
      transition: border-color 0.15s, box-shadow 0.15s;
      outline: none;
    }

    input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(24,95,165,0.12);
    }

    .drop {
      border: 1.5px dashed var(--border-hover);
      border-radius: var(--radius);
      padding: 1.5rem;
      text-align: center;
      cursor: pointer;
      transition: border-color 0.15s, background 0.15s;
      position: relative;
      background: var(--bg);
    }

    .drop:hover, .drop.active {
      border-color: var(--accent);
      background: var(--accent-bg);
    }

    .drop input[type="file"] {
      position: absolute;
      inset: 0;
      opacity: 0;
      cursor: pointer;
    }

    .drop-icon { font-size: 22px; margin-bottom: 6px; }

    .drop-text {
      font-size: 13px;
      color: var(--muted);
    }

    .drop-name {
      font-size: 12px;
      color: var(--accent);
      margin-top: 4px;
      font-weight: 500;
      font-family: var(--mono);
    }

    .btn {
      width: 100%;
      padding: 0.75rem;
      background: var(--accent);
      color: #fff;
      border: none;
      border-radius: var(--radius);
      font-family: var(--sans);
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: background 0.15s, transform 0.1s;
      margin-top: 0.25rem;
    }

    .btn:hover { background: var(--accent-hover); }
    .btn:active { transform: scale(0.99); }
    .btn:disabled { background: #B4B2A9; cursor: not-allowed; }

    .status {
      margin-top: 1rem;
      padding: 0.75rem 1rem;
      border-radius: var(--radius);
      font-size: 13px;
      display: none;
    }

    .status.error {
      background: #FCEBEB;
      color: #A32D2D;
      border: 0.5px solid #F09595;
    }

    .status.success {
      background: #EAF3DE;
      color: #3B6D11;
      border: 0.5px solid #97C459;
    }

    .status.loading {
      background: var(--accent-bg);
      color: var(--accent-hover);
      border: 0.5px solid #85B7EB;
    }

    .foot {
      margin-top: 1.25rem;
      font-size: 11px;
      color: var(--hint);
      text-align: center;
      font-family: var(--mono);
    }

    .logo {
      width: 150px;
      height: 33px;
      object-fit: contain;
      display: block;
      margin-bottom: 12px;
}
  </style>
</head>
<body>
  <div class="wrap">
    <img src="/static/logo.png" class="logo" alt="Antilhue">

    <div class="brand">
      <div class="eyebrow">Antilhue · Softland</div>
      <h1>Procesador <em>OC</em> → CSV</h1>
      <p class="sub">Sube la orden de compra en PDF para generar el archivo listo para Softland</p>
    </div>

    <div class="card">
      <div class="row">
        <div class="field">
          <label>N° Orden de compra</label>
          <input type="text" id="orden" placeholder="ej: 6995" />
        </div>
        <div class="field">
          <label>Tasa de cambio (USD)</label>
          <input type="number" id="tasa" placeholder="ej: 929.9" step="0.01" />
        </div>
      </div>

      <div class="field">
        <label>Archivo PDF</label>
        <div class="drop" id="zone">
          <input type="file" id="pdfFile" accept=".pdf" onchange="onFile(this)" />
          <div class="drop-icon">📄</div>
          <div class="drop-text">Arrastra o haz clic para seleccionar</div>
          <div class="drop-name" id="fname"></div>
        </div>
      </div>

      <button class="btn" id="btn" onclick="submit()">
        Generar CSV para Softland
      </button>
      <div class="status" id="status"></div>
    </div>

    <div class="foot">PDF texto seleccionable · Conexión Odoo XML-RPC · v1.0</div>
  </div>

  <script>
    function onFile(el) {
      const name = el.files[0]?.name || '';
      document.getElementById('fname').textContent = name;
      document.getElementById('zone').classList.toggle('active', !!name);
    }

    function setStatus(msg, type) {
      const el = document.getElementById('status');
      el.textContent = msg;
      el.className = 'status ' + type;
      el.style.display = 'block';
    }

    async function submit() {
      const orden = document.getElementById('orden').value.trim();
      const tasa  = document.getElementById('tasa').value.trim();
      const file  = document.getElementById('pdfFile').files[0];

      if (!orden || !tasa || !file) {
        setStatus('Completa todos los campos antes de continuar.', 'error');
        return;
      }

      const btn = document.getElementById('btn');
      btn.disabled = true;
      setStatus('Procesando PDF y consultando Odoo...', 'loading');

      const fd = new FormData();
      fd.append('orden', orden);
      fd.append('tasa', tasa);
      fd.append('pdf', file);

      try {
        const resp = await fetch('/procesar-oc', { method: 'POST', body: fd });

        if (!resp.ok) {
          const err = await resp.json();
          setStatus(err.error || 'Error desconocido', 'error');
          return;
        }

        const blob = await resp.blob();
        const a    = document.createElement('a');
        a.href     = URL.createObjectURL(blob);
        a.download = `OC_${orden}_softland.csv`;
        a.click();
        URL.revokeObjectURL(a.href);
        setStatus(`CSV generado correctamente — OC ${orden}`, 'success');

      } catch (e) {
        setStatus('Error de red: ' + e.message, 'error');
      } finally {
        btn.disabled = false;
      }
    }
  </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)


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
    app.run(debug=Config.DEBUG, host="0.0.0.0", port=Config.PORT)