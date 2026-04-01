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
  <title>Procesador OC → Softland</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    :root {
      --bg: #0f1117;
      --surface: #181c27;
      --border: #2a2f3e;
      --accent: #00d4aa;
      --accent2: #ff6b35;
      --text: #e2e8f0;
      --muted: #64748b;
      --mono: 'IBM Plex Mono', monospace;
      --sans: 'IBM Plex Sans', sans-serif;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--sans);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }

    .container {
      width: 100%;
      max-width: 560px;
    }

    .header {
      margin-bottom: 2.5rem;
    }

    .tag {
      font-family: var(--mono);
      font-size: 0.7rem;
      color: var(--accent);
      letter-spacing: 0.15em;
      text-transform: uppercase;
      margin-bottom: 0.75rem;
    }

    h1 {
      font-size: 1.75rem;
      font-weight: 600;
      line-height: 1.2;
      color: #fff;
    }

    h1 span { color: var(--accent); }

    .subtitle {
      margin-top: 0.5rem;
      font-size: 0.85rem;
      color: var(--muted);
    }

    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 2rem;
    }

    .field { margin-bottom: 1.5rem; }

    label {
      display: block;
      font-size: 0.75rem;
      font-family: var(--mono);
      color: var(--muted);
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-bottom: 0.5rem;
    }

    input[type="text"], input[type="number"] {
      width: 100%;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.65rem 0.9rem;
      color: var(--text);
      font-family: var(--mono);
      font-size: 0.9rem;
      transition: border-color 0.2s;
    }

    input:focus {
      outline: none;
      border-color: var(--accent);
    }

    .file-zone {
      border: 2px dashed var(--border);
      border-radius: 8px;
      padding: 2rem;
      text-align: center;
      cursor: pointer;
      transition: border-color 0.2s, background 0.2s;
      position: relative;
    }

    .file-zone:hover, .file-zone.active {
      border-color: var(--accent);
      background: rgba(0, 212, 170, 0.04);
    }

    .file-zone input[type="file"] {
      position: absolute;
      inset: 0;
      opacity: 0;
      cursor: pointer;
    }

    .file-icon { font-size: 2rem; margin-bottom: 0.5rem; }

    .file-label {
      font-size: 0.85rem;
      color: var(--muted);
    }

    .file-name {
      font-family: var(--mono);
      font-size: 0.8rem;
      color: var(--accent);
      margin-top: 0.5rem;
    }

    .btn {
      width: 100%;
      padding: 0.85rem;
      background: var(--accent);
      color: #0f1117;
      border: none;
      border-radius: 8px;
      font-family: var(--mono);
      font-size: 0.9rem;
      font-weight: 600;
      letter-spacing: 0.05em;
      cursor: pointer;
      transition: opacity 0.2s, transform 0.1s;
    }

    .btn:hover { opacity: 0.9; }
    .btn:active { transform: scale(0.99); }
    .btn:disabled { opacity: 0.4; cursor: not-allowed; }

    .status {
      margin-top: 1.5rem;
      padding: 1rem;
      border-radius: 8px;
      font-family: var(--mono);
      font-size: 0.8rem;
      display: none;
    }

    .status.error {
      background: rgba(255, 107, 53, 0.1);
      border: 1px solid rgba(255, 107, 53, 0.3);
      color: var(--accent2);
    }

    .status.success {
      background: rgba(0, 212, 170, 0.1);
      border: 1px solid rgba(0, 212, 170, 0.3);
      color: var(--accent);
    }

    .status.loading {
      background: rgba(100, 116, 139, 0.1);
      border: 1px solid var(--border);
      color: var(--muted);
    }

    .footer {
      margin-top: 2rem;
      font-size: 0.72rem;
      color: var(--muted);
      text-align: center;
      font-family: var(--mono);
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="tag">Antilhue · Softland Integration</div>
      <h1>Procesador <span>OC</span> → CSV</h1>
      <p class="subtitle">Sube el PDF de orden de compra para generar el archivo listo para Softland</p>
    </div>

    <div class="card">
      <div class="field">
        <label>N° Orden de Compra</label>
        <input type="text" id="orden" placeholder="ej: 6995" />
      </div>

      <div class="field">
        <label>Tasa de Cambio (USD → CLP)</label>
        <input type="number" id="tasa" placeholder="ej: 930.5" step="0.01" />
      </div>

      <div class="field">
        <label>Archivo PDF</label>
        <div class="file-zone" id="fileZone">
          <input type="file" id="pdfFile" accept=".pdf" onchange="updateFileName(this)" />
          <div class="file-icon">📄</div>
          <div class="file-label">Arrastra o haz clic para seleccionar el PDF</div>
          <div class="file-name" id="fileName"></div>
        </div>
      </div>

      <button class="btn" id="submitBtn" onclick="procesarOC()">
        Generar CSV para Softland
      </button>

      <div class="status" id="status"></div>
    </div>

    <div class="footer">PDF texto seleccionable · Conexión Odoo vía XML-RPC · v1.0</div>
  </div>

  <script>
    function updateFileName(input) {
      const name = input.files[0]?.name || '';
      document.getElementById('fileName').textContent = name;
      const zone = document.getElementById('fileZone');
      zone.classList.toggle('active', !!name);
    }

    function setStatus(msg, type) {
      const el = document.getElementById('status');
      el.textContent = msg;
      el.className = 'status ' + type;
      el.style.display = 'block';
    }

    async function procesarOC() {
      const orden = document.getElementById('orden').value.trim();
      const tasa  = document.getElementById('tasa').value.trim();
      const file  = document.getElementById('pdfFile').files[0];

      if (!orden || !tasa || !file) {
        setStatus('⚠ Completa todos los campos antes de continuar.', 'error');
        return;
      }

      const btn = document.getElementById('submitBtn');
      btn.disabled = true;
      setStatus('⏳ Procesando PDF y consultando Odoo...', 'loading');

      const formData = new FormData();
      formData.append('orden', orden);
      formData.append('tasa', tasa);
      formData.append('pdf', file);

      try {
        const resp = await fetch('/procesar-oc', { method: 'POST', body: formData });

        if (!resp.ok) {
          const err = await resp.json();
          setStatus('✗ ' + (err.error || 'Error desconocido'), 'error');
          return;
        }

        const blob = await resp.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `OC_${orden}_softland.csv`;
        a.click();
        URL.revokeObjectURL(url);
        setStatus(`✓ CSV generado correctamente para OC ${orden}`, 'success');
      } catch (e) {
        setStatus('✗ Error de red: ' + e.message, 'error');
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
    print("🔍 DEBUG request.content_type:", request.content_type)
    print("🔍 DEBUG files:", [f.filename for f in request.files.values() if f.filename])
    print("🔍 DEBUG form:", dict(request.form))
    orden = request.form.get("orden", "").strip()
    tasa_raw = request.form.get("tasa", "").strip()
    pdf_file = request.files.get("pdf")

    # — Validaciones de entrada —
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
        # 1. Extraer líneas crudas del PDF
        pdf_bytes = pdf_file.read()
        raw_lines = extract_order_lines(pdf_bytes)
        logger.info(f"[OC:{orden}] Líneas extraídas del PDF: {len(raw_lines)}")

        if not raw_lines:
            return jsonify({"error": "No se encontraron líneas de producto en el PDF"}), 422

        # 2. Parsear y limpiar líneas
        parsed_lines = parse_lines(raw_lines)
        logger.info(f"[OC:{orden}] Líneas parseadas válidas: {len(parsed_lines)}")

        if not parsed_lines:
            return jsonify({"error": "No se pudieron parsear líneas válidas del PDF"}), 422

        # 3. Consultar Odoo en batch
        codigos_fabrica = [l["cod_fabrica"] for l in parsed_lines]
        odoo = OdooService(
            url=Config.ODOO_URL,
            db=Config.ODOO_DB,
            username=Config.ODOO_USER,
            password=Config.ODOO_PASSWORD,
        )
        mapeo_odoo = odoo.buscar_codigos_batch(codigos_fabrica)
        logger.info(f"[OC:{orden}] Respuesta Odoo: {len(mapeo_odoo)} códigos encontrados de {len(codigos_fabrica)}")

        # 4. Generar CSV
        csv_content = build_csv(
            orden=orden,
            equi=equi,
            parsed_lines=parsed_lines,
            mapeo_odoo=mapeo_odoo,
        )

        # 5. Log resumen
        log_processing_summary(logger, orden, parsed_lines, mapeo_odoo)

        # 6. Devolver archivo
        csv_bytes = io.BytesIO(csv_content.encode("utf-8"))
        return send_file(
            csv_bytes,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"OC_{orden}_softland.csv",
        )

    except ConnectionError as e:
        logger.error(f"[OC:{orden}] Error de conexión Odoo: {e}")
        return jsonify({"error": f"No se pudo conectar a Odoo: {str(e)}"}), 503
    except Exception as e:
        logger.exception(f"[OC:{orden}] Error inesperado: {e}")
        return jsonify({"error": f"Error interno al procesar la OC: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=Config.DEBUG, host="0.0.0.0", port=Config.PORT)
