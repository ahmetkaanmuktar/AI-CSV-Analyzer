"""AI CSV Analyzer - Web Application Server.

A lightweight Flask server providing a modern web interface for uploading CSV datasets,
extracting descriptive statistics, and generating Google Gemini AI reports.
"""

import io
import os
from flask import Flask, jsonify, render_template, request
from main import parse_csv_stream, read_csv, run_full_analysis

app = Flask(__name__)

# Security: Enforce a strict 16 MB maximum file upload size
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


@app.route("/")
def index():
    """Render the primary dashboard application interface."""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_csv_endpoint():
    """Handle CSV file uploads, process in-memory, and return analytical payload."""
    lang = request.form.get("lang", "en").strip().lower()
    if lang not in ["tr", "en"]:
        lang = "en"

    if "file" not in request.files:
        err = "Lütfen analiz edilecek bir CSV dosyası seçin." if lang == "tr" else "Please select a CSV file to analyze."
        return jsonify({"success": False, "error": err}), 400

    uploaded_file = request.files["file"]

    if not uploaded_file or uploaded_file.filename == "":
        err = "Herhangi bir dosya seçilmedi." if lang == "tr" else "No file was selected."
        return jsonify({"success": False, "error": err}), 400

    filename = uploaded_file.filename
    if not filename.lower().endswith(".csv"):
        err = "Geçersiz dosya türü. Lütfen yalnızca .csv uzantılı dosya yükleyin." if lang == "tr" else "Invalid file format. Please upload a .csv file."
        return jsonify({"success": False, "error": err}), 400

    try:
        raw_bytes = uploaded_file.read()
        if not raw_bytes or len(raw_bytes.strip()) == 0:
            err = "Yüklenen CSV dosyası boş." if lang == "tr" else "The uploaded CSV file is empty."
            return jsonify({"success": False, "error": err}), 400

        text_content = raw_bytes.decode("utf-8-sig", errors="replace")
        stream = io.StringIO(text_content)

        columns, data_rows = parse_csv_stream(stream)
        results = run_full_analysis(columns, data_rows, lang=lang)
        results["filename"] = filename

        return jsonify({"success": True, "data": results})

    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Error: {str(e)}"}), 500


@app.route("/sample", methods=["GET"])
def analyze_sample_endpoint():
    """Quick-test endpoint to analyze the bundled sample_sales.csv dataset."""
    lang = request.args.get("lang", "en").strip().lower()
    if lang not in ["tr", "en"]:
        lang = "en"

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        sample_path = os.path.join(base_dir, "sample_sales.csv")
        columns, data_rows = read_csv(sample_path)
        results = run_full_analysis(columns, data_rows, lang=lang)
        results["filename"] = "sample_sales.csv (Demo Veri)" if lang == "tr" else "sample_sales.csv (Demo Dataset)"
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed: {str(e)}"}), 500


@app.errorhandler(413)
def handle_file_too_large(e):
    """Handle uploads exceeding maximum allowed size."""
    return jsonify({
        "success": False,
        "error": "Dosya boyutu 16 MB sınırını aşıyor." if request.form.get("lang") == "tr" else "File size exceeds 16 MB limit."
    }), 413


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\nAI CSV Analyzer Web Server Starting...")
    print(f"Access dashboard at: http://127.0.0.1:{port}/\n")
    app.run(host="127.0.0.1", port=port, debug=True)
