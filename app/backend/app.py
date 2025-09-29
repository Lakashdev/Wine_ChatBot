from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Make sure Python can find the generator folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from generator.generator import answer_query_rag
from generator.generator import deepseek_quick, build_detailed_from_quick  # 👈 import helpers

app = Flask(__name__)
CORS(app)

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        query = data.get("query", "")
        if not query:
            return jsonify({"error": "Query not provided"}), 400

        result = answer_query_rag(query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 👇 New: quick mode
@app.route("/ask_quick", methods=["POST"])
def ask_quick():
    try:
        data = request.get_json()
        query = data.get("query", "")
        if not query:
            return jsonify({"error": "Query not provided"}), 400

        result = deepseek_quick(query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 👇 New: detailed mode (using quick answer to match dataset)
@app.route("/ask_detailed", methods=["POST"])
def ask_detailed():
    try:
        data = request.get_json()
        query = data.get("query", "")
        quick_answer = data.get("quick_answer", "")
        if not query:
            return jsonify({"error": "Query not provided"}), 400

        result = build_detailed_from_quick(query, quick_answer)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
