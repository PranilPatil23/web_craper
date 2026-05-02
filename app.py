from flask import Flask, request, jsonify, send_file, render_template
from scraper import detect_input, fix_url, scrape_static, enhanced_scrape
from utils import save_to_excel, save_to_json, save_to_word
import os
import uuid

app = Flask(__name__)

# Folder to store generated files
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- SCRAPE ----------
@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No input provided"}), 400

    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Provide a URL, keyword, or sentence"}), 400

    try:
        input_type = detect_input(query)

        if input_type == "url":
            url = fix_url(query)
            result = scrape_static(url)
        else:
            # 🔥 Multi-engine search
            result = enhanced_scrape(query)

        if isinstance(result, dict) and "error" in result:
            return jsonify(result), 500

        # 🔥 Clean Description
        descriptions = list(set([
            item.get("content", "") for item in result if item.get("content")
        ]))

        description = " ".join(descriptions[:3])[:500]

        if not description:
            description = "No description available."

        return jsonify({
            "summary": description,
            "results": result
        })

    except Exception as e:
        return jsonify({"error": f"Scrape Error: {str(e)}"}), 500


# ---------- DOWNLOAD ----------
@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data received"}), 400

    results = data.get("results", [])
    summary = data.get("summary", "")
    format_type = data.get("format", "excel")

    if not results:
        return jsonify({"error": "No results to download"}), 400

    try:
        file_id = str(uuid.uuid4())

        if format_type == "excel":
            file_path = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.xlsx")
            save_to_excel(results, file_path)

        elif format_type == "json":
            file_path = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.json")
            save_to_json(results, file_path)

        elif format_type == "word":
            file_path = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.docx")
            save_to_word(results, summary, file_path)

        else:
            return jsonify({"error": "Invalid format"}), 400

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": f"Download Error: {str(e)}"}), 500


# ---------- RUN ----------
if __name__ == "__main__":
    app.run()
