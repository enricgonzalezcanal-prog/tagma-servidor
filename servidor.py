from flask import Flask, request, jsonify
import subprocess, json, os

app = Flask(__name__)

@app.route("/generar", methods=["POST"])
def generar():
    data = request.json
    result = subprocess.run(
        ["python3", "/Users/enric/TAGMA/agente/generar_documentos.py", json.dumps(data)],
        capture_output=True, text=True
    )
    return jsonify({"ok": True, "output": result.stdout, "error": result.stderr})

@app.route("/imprimir", methods=["POST"])
def imprimir():
    data = request.json
    semana = data.get("semana", "")
    result = subprocess.run(
        ["python3", "/Users/enric/TAGMA/agente/imprimir.py", str(semana)],
        capture_output=True, text=True
    )
    return jsonify({"ok": True, "output": result.stdout})

@app.route("/ping")
def ping():
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5680)
