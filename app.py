from flask import Flask, request, jsonify, send_file, render_template
from scraper import detect_input, fix_url, scrape_static, enhanced_scrape, ai_summary, deep_research, scrape_hdfc_categories, scrape_cards_from_category, scrape_dynamic  # ✅ ADDED scrape_dynamic
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
        # 🔥 HDFC Cards Special Case
        if query.lower() == "hdfc cards":
            result = scrape_hdfc_categories()
            return jsonify({
                "type": "category",
                "results": result,
                "summary": "Select a category to explore HDFC cards"
            })

        input_type = detect_input(query)

        if input_type == "url":
            result = scrape_static(query)
        else:
            engine = data.get("engine", "duckduckgo")

            if engine == "deep":
                result = deep_research(query)
            else:   
                result = enhanced_scrape(query, engine) 

        if isinstance(result, dict) and "error" in result:
            return jsonify(result), 500
       
        # 🔥 Description from results
        description = ""

        for item in result:
            if item.get("content"):
                description += item["content"] + " "

        description = description[:500]

        return jsonify({
            "summary": description,
            "results": result
        })

    except Exception as e:
        return jsonify({"error": f"Scrape Error: {str(e)}"}), 500


# ---------- CATEGORY → CARDS ----------
@app.route("/category-cards", methods=["POST"])
def category_cards():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        cards = scrape_cards_from_category(url)

        return jsonify({
            "type": "cards",
            "results": cards
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- CARD DETAILS ----------
@app.route("/card-details", methods=["POST"])
def card_details():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        try:
            result = scrape_static(url)

            # 🔥 fallback if blocked (slightly improved condition)
            if not result or "Status code" in result[0]["content"] or "Error" in result[0]["title"]:
                result = scrape_dynamic(url)

        except:
            result = scrape_dynamic(url)        

        return jsonify({
            "description": result[0]["content"],
            "link": url
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    app.run(debug=True, port=5000)
