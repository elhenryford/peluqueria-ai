from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
import threading
import webbrowser
import os

from procesar import generar_peinado

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "salida")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED = {"png", "jpg", "jpeg", "webp"}


def permitido(nombre):
    return "." in nombre and nombre.rsplit(".", 1)[1].lower() in ALLOWED


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    if "cliente" not in request.files:
        return jsonify({"ok": False, "error": "Falta la foto del cliente"})

    if "corte" not in request.files:
        return jsonify({"ok": False, "error": "Falta la foto del corte"})

    cliente = request.files["cliente"]
    corte = request.files["corte"]

    if cliente.filename == "" or corte.filename == "":
        return jsonify({"ok": False, "error": "Seleccione ambas imágenes"})

    if not permitido(cliente.filename):
        return jsonify({"ok": False, "error": "Formato del cliente incorrecto"})

    if not permitido(corte.filename):
        return jsonify({"ok": False, "error": "Formato del corte incorrecto"})

    tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")

    nombre_cliente = secure_filename(f"cliente_{tiempo}.png")
    nombre_corte = secure_filename(f"corte_{tiempo}.png")

    ruta_cliente = os.path.join(UPLOAD_FOLDER, nombre_cliente)
    ruta_corte = os.path.join(UPLOAD_FOLDER, nombre_corte)

    cliente.save(ruta_cliente)
    corte.save(ruta_corte)

    try:

        salida = generar_peinado(
            ruta_cliente,
            ruta_corte,
            OUTPUT_FOLDER
        )

        return jsonify({
            "ok": True,
            "result": "/resultado/" + os.path.basename(salida)
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        })


@app.route("/resultado/<archivo>")
def resultado(archivo):
    return send_from_directory(OUTPUT_FOLDER, archivo)


def abrir():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":

    threading.Timer(1.5, abrir).start()

    app.run(debug=True)