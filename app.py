import os
import json
import uuid
import threading
import webbrowser

from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, session
from werkzeug.utils import secure_filename

from procesar import generar_peinado


app = Flask(__name__)
app.secret_key = "ffd2fxs6.-"


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "salida")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED = {"png", "jpg", "jpeg", "webp"}


# ----------------------------
# HISTORIAL
# ----------------------------
def guardar_historial(user_id, original, corte, resultado):
    carpeta = os.path.join("historial", user_id)
    os.makedirs(carpeta, exist_ok=True)

    archivo = os.path.join(carpeta, "registros.json")

    data = []

    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            data = json.load(f)

    data.append({
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "original": original,
        "corte": corte,
        "resultado": resultado
    })

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ----------------------------
# UTIL
# ----------------------------
def permitido(nombre):
    return "." in nombre and nombre.rsplit(".", 1)[1].lower() in ALLOWED


# ----------------------------
# ROUTES
# ----------------------------
@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    # usuario persistente
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())

    user_id = session["user_id"]

    user_upload = os.path.join(UPLOAD_FOLDER, user_id)
    user_output = os.path.join(OUTPUT_FOLDER, user_id)

    os.makedirs(user_upload, exist_ok=True)
    os.makedirs(user_output, exist_ok=True)

    # validación
    if "cliente" not in request.files or "corte" not in request.files:
        return jsonify({"ok": False, "error": "faltan imágenes"})

    cliente = request.files["cliente"]
    corte = request.files["corte"]

    tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")

    nombre_cliente = secure_filename(f"cliente_{tiempo}.png")
    nombre_corte = secure_filename(f"corte_{tiempo}.png")

    ruta_cliente = os.path.join(user_upload, nombre_cliente)
    ruta_corte = os.path.join(user_upload, nombre_corte)

    cliente.save(ruta_cliente)
    corte.save(ruta_corte)

    # procesamiento
    salida = generar_peinado(
        ruta_cliente,
        ruta_corte,
        user_output
    )

    # historial (URLs web, no rutas físicas)
    guardar_historial(
        user_id,
        f"/uploads/{user_id}/{nombre_cliente}",
        f"/uploads/{user_id}/{nombre_corte}",
        f"/resultado/{user_id}/{os.path.basename(salida)}"
    )

    return jsonify({
        "ok": True,
        "result": f"/resultado/{user_id}/{os.path.basename(salida)}"
    })


@app.route("/resultado/<user_id>/<archivo>")
def resultado(user_id, archivo):
    return send_from_directory(
        os.path.join(OUTPUT_FOLDER, user_id),
        archivo
    )


@app.route("/historial")
def historial():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"ok": False, "error": "sin usuario"})

    archivo = os.path.join("historial", user_id, "registros.json")

    if not os.path.exists(archivo):
        return jsonify({"ok": True, "data": []})

    with open(archivo, "r", encoding="utf-8") as f:
        data = json.load(f)

    return jsonify({"ok": True, "data": data})


@app.route("/uploads/<path:filename>")
def uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/dashboard")
def dashboard():

    user_id = session.get("user_id")

    if not user_id:
        return "Sin usuario"

    archivo = os.path.join("historial", user_id, "registros.json")

    data = []

    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            data = json.load(f)

    return render_template("dashboard.html", data=data)


# ----------------------------
# AUTO OPEN
# ----------------------------
def abrir():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    if os.environ.get("RENDER"):
        app.run(host="0.0.0.0", port=10000)
    else:
        threading.Timer(1.5, abrir).start()
        app.run(debug=True)
