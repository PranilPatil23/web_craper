from flask import Flask, request, jsonify, send_file, render_template
from scraper import scrape_static, scrape_by_keyword
from utils import save_to_excel

app = Flask(__name__)

# ---------- HOME ROUTE (UI) ----------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- SCRAPE API ----------
@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()

    url = data.get("url")
    keyword = data.get("keyword")

    try:
        # 🔹 If URL provided
        if url:
            result = scrape_static(url)

        # 🔹 If keyword provided
        elif keyword:
            result = scrape_by_keyword(keyword)

        else:
            return jsonify({"error": "Provide URL or Keyword"}), 400

        # Handle error
        if isinstance(result, dict) and "error" in result:
            return jsonify(result), 500

        file_path = save_to_excel(result)

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)