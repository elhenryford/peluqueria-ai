import os
import json
import uuid
import threading
import webbrowser
import shutil
from datetime import datetime
import cv2
from flask import Flask, render_template, request, jsonify, send_from_directory, session
import numpy as np
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
from ia.modelo import cargar_modelo, segmentar
from procesar import generar_peinado, crear_peluca_desde_corte, procesar_foto
import uuid

model, device = cargar_modelo()

app = Flask(__name__)
app.secret_key = "ffd2fxs6.-"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tif', 'tiff'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER,)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------------------
# HISTORIAL
# ----------------------------
DEBUG_LOGS = []

def log(msg):
    print(msg)  # sigue saliendo en consola

    DEBUG_LOGS.append(msg)

    # opcional: limitar tamaño
    if len(DEBUG_LOGS) > 50:
        DEBUG_LOGS.pop(0)
        
@app.route("/debug")
def debug():
    return jsonify({
        "logs": DEBUG_LOGS
    })
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
    return "." in nombre and nombre.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def guardar_archivo(file_storage, ruta_destino):
    if file_storage is None:
        return False

    if not hasattr(file_storage, "stream"):
        return False

    try:
        file_storage.stream.seek(0)
        file_storage.save(ruta_destino)
        return os.path.exists(ruta_destino) and os.path.getsize(ruta_destino) > 0
    except Exception as e:
        log(f"No se pudo guardar el archivo en {ruta_destino}: {e}")
        return False


# ----------------------------
# ROUTES
# ----------------------------
@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def procesar(orientacion=None):
    try:
        # usuario persistente
        if "user_id" not in session:
            session["user_id"] = str(uuid.uuid4())

        user_id = session["user_id"]

        user_upload = os.path.join(UPLOAD_FOLDER, user_id)
        os.makedirs(user_upload, exist_ok=True)

        # validación
        cliente = request.files.get("cliente")
        corte = request.files.get("corte")
        cara = request.files.get("cara")
        peluca = request.files.get("peluca")

        
        id_peticion = uuid.uuid4().hex[:8]
        print(f"\n========== PETICIÓN {id_peticion} ==========")
        print(request.method, request.path)
        print("Remote:", request.remote_addr)
        print("Content-Length:", request.content_length)
        # tomar orientación desde el formulario (si viene) o usar 'frente' por defecto
        orientacion = request.form.get("orientacion", "frente")

        if cliente is None or corte is None:
            return jsonify({"ok": False, "error": "faltan imágenes"})

        if orientacion not in {"frente", "perfil", "espalda"}:
            return jsonify({"ok": False, "error": "orientación no válida"})

        tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")

        nombre_cliente = secure_filename(f"cliente_{tiempo}.png")
        nombre_cara = secure_filename(f"cara_{tiempo}.png")
        nombre_corte = secure_filename(f"corte_{tiempo}.png")
        nombre_peluca = secure_filename(f"peluca_{tiempo}.png")

        ruta_cliente = os.path.join(user_upload, nombre_cliente)
        ruta_corte = os.path.join(user_upload, nombre_corte)
        ruta_cara = os.path.join(user_upload, nombre_cara)
        ruta_peluca = os.path.join(user_upload, nombre_peluca)

        # Guardar archivos primero
        if not guardar_archivo(cliente, ruta_cliente):
            return jsonify({"ok": False, "error": "No se pudo guardar la foto del cliente"})

        if cara is not None:
            if not guardar_archivo(cara, ruta_cara):
                return jsonify({"ok": False, "error": "No se pudo guardar la foto de la cara"})
        else:
            # Si no llega la foto de la cara, se usa la del cliente como respaldo
            if not guardar_archivo(cliente, ruta_cara):
                return jsonify({"ok": False, "error": "No se pudo guardar la foto de la cara"})

        if not guardar_archivo(corte, ruta_corte):
            return jsonify({"ok": False, "error": "No se pudo guardar la foto del corte"})

        peluca_valida = peluca is not None and getattr(peluca, 'filename', '') != ''
        if peluca_valida:
            if not guardar_archivo(peluca, ruta_peluca):
                return jsonify({"ok": False, "error": "No se pudo guardar la foto de la peluca"})
        else:
            # `peluca` se comporta como el pelo de `corte`
            corte_img = cv2.imread(ruta_corte, cv2.IMREAD_UNCHANGED)
            if corte_img is None:
                return jsonify({"ok": False, "error": "No se pudo leer la imagen del corte para generar peluca"})
            if not crear_peluca_desde_corte(corte_img, ruta_peluca,model,device):
                return jsonify({"ok": False, "error": "No se pudo generar la peluca desde el corte"})
            log("peluca no enviado, creando peluca desde el corte")

        # Procesar la foto del cliente/cara y guardar la imagen procesada
        imagen_procesada, mensaje = procesar_foto(ruta_cara, orientacion)
        if imagen_procesada is None:
            return jsonify({"ok": False, "error": f"Error al procesar: {mensaje}"})
        cv2.imwrite(ruta_cara, imagen_procesada)

        # Generar el peinado final con la imagen de peluca si existe, si no con la imagen de corte
        ruta_resultado = generar_peinado(
            ruta_cara,
            ruta_peluca,
            user_upload,
            model,
            device,
            orientacion
        )
       
        resultado_nombre = os.path.basename(ruta_resultado)

        # historial (URLs web, no rutas físicas)
        guardar_historial(
            user_id,
            f"/historial/{user_id}/{nombre_cliente}",
            f"/historial/{user_id}/{nombre_corte}",
            f"/resultado/{user_id}/{resultado_nombre}"
        )
        print(f"========== FIN {id_peticion} ==========\n")
        return jsonify({
            "ok": True,
            "result": f"/resultado/{user_id}/{resultado_nombre}"
        })

    except Exception as e:
        log("ERROR EN /upload: " + str(e))
        import traceback
        log(traceback.format_exc())
        
        return jsonify({"ok": False, "error": "Error interno: " + str(e)})

@app.route("/resultado/<user_id>/<archivo>")
def resultado(user_id, archivo):
    return send_from_directory(
        os.path.join(UPLOAD_FOLDER, user_id),
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





@app.route('/api/subir-corte', methods=['POST'])
def subir_corte():
    try:
        # Si se envía un archivo de corte, se guarda como uploads/corte.png
        if 'file' in request.files:
            file = request.files['file']

            if file.filename == '':
                return jsonify({'error': 'Nombre de archivo vacío'}), 400

            if not allowed_file(file.filename):
                return jsonify({'error': 'Tipo de archivo no permitido'}), 400

            corte_filename = 'corte.png'
            corte_filepath = os.path.join(app.config['UPLOAD_FOLDER'], corte_filename)
            file.save(corte_filepath)

            return jsonify({
                'exito': True,
                'mensaje': f'Corte subido correctamente: {corte_filename}',
                'archivo': corte_filename
            })

        # Si no hay archivo, se puede procesar una solicitud JSON de orientaciones.
        data = request.get_json(silent=True)

        if not data or 'orientaciones' not in data:
            return jsonify({'error': 'No se especificaron orientaciones'}), 400

        orientaciones = data['orientaciones']
        if not isinstance(orientaciones, list) or not orientaciones:
            return jsonify({'error': 'Lista de orientaciones inválida'}), 400

        valid_orientaciones = [o for o in orientaciones if o in {'frente', 'perfil', 'espalda'}]
        archivos_subidos = []
        source = os.path.join(app.config['UPLOAD_FOLDER'], 'corte.png')
        if os.path.exists(source):
            archivos_subidos = valid_orientaciones

        if not archivos_subidos:
            return jsonify({'error': 'No se encontraron fotos procesadas para subir'}), 400

        return jsonify({
            'exito': True,
            'mensaje': f'Corte(s) subido(s) correctamente: {" ,".join(archivos_subidos)}',
            'archivos': archivos_subidos
        })
    except Exception as e:
        return jsonify({'error': f'Error al subir corte: {str(e)}'}), 500

# ----------------------------
# AUTO OPEN
# ----------------------------

def open_browser():
    webbrowser.open('http://localhost:5000')
if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        threading.Timer(1.5, open_browser).start()
    app.run(debug=True, port=5000)
