import cv2
import mediapipe as mp
import os
import uuid 
import numpy as np
from config import MASK_KERNEL_SIZE, MASK_BLUR_SIZE
from ia.modelo import segmentar
from datetime import datetime

mp_face = mp.solutions.face_detection.FaceDetection(
    model_selection=1,
    min_detection_confidence=0.5
)

def _asegurar_imagen(img, preserve_alpha=False):
    if img is None:
        return None

    if isinstance(img, tuple):
        return None

    if not isinstance(img, np.ndarray):
        img = np.asarray(img)

    if img.size == 0:
        return None

    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    if img.ndim == 3 and img.shape[2] == 1:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    if img.ndim == 3 and img.shape[2] == 4:
        if preserve_alpha:
            return img
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    return img


def detectar_cara(img):
    img = _asegurar_imagen(img, preserve_alpha=True)
    if img is None:
        return None

    h, w = img.shape[:2]
    if img.ndim == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    with mp.solutions.face_detection.FaceDetection(
        model_selection=1,
        min_detection_confidence=0.5
    ) as detector:
        result = detector.process(rgb)

    if not result.detections:
        return None

    box = result.detections[0].location_data.relative_bounding_box
    x = int(box.xmin * w)
    y = int(box.ymin * h)
    width = int(box.width * w)
    height = int(box.height * h)

    return x, y, width, height


def crear_mascara_corte(corte, orientacion=None):
    if corte is None:
        return None

    if corte.ndim == 3 and corte.shape[2] == 4:
        return corte[:, :, 3]

    if corte.ndim == 2:
        gris = corte
    else:
        if corte.shape[2] == 1:
            gris = corte[:, :, 0]
        else:
            gris = cv2.cvtColor(corte, cv2.COLOR_BGR2GRAY)

    # Intentar umbral automático (Otsu). Calculamos máscara directa e invertida
    try:
        _, m_bin = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        _, m_inv = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Elegir la máscara con menor área blanca (asumimos que el peinado ocupa menos área que fondo)
        if cv2.countNonZero(m_bin) <= cv2.countNonZero(m_inv):
            mascara = m_bin
        else:
            mascara = m_inv
    except Exception:
        # Fallback a un umbral alto como antes
        _, mascara = cv2.threshold(gris, 240, 255, cv2.THRESH_BINARY_INV)

    # Limpiar y suavizar la máscara usando parámetros configurables
    k = int(MASK_KERNEL_SIZE) if MASK_KERNEL_SIZE > 0 else 5
    if k % 2 == 0:
        k += 1
    kernel = np.ones((k, k), np.uint8)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel)

    b = int(MASK_BLUR_SIZE) if MASK_BLUR_SIZE > 0 else 7
    if b % 2 == 0:
        b += 1
    mascara = cv2.GaussianBlur(mascara, (b, b), 0)
    _, mascara = cv2.threshold(mascara, 127, 255, cv2.THRESH_BINARY)

    return mascara



import cv2
import mediapipe as mp
import numpy as np

mp_face = mp.solutions.face_detection.FaceDetection(
    model_selection=1,
    min_detection_confidence=0.5
)

def crear_peluca_desde_corte(corte, ruta_peluca, model, device):

    if corte is None:
        return False

    img = _asegurar_imagen(corte)
    
    print("Tipo:", type(img))
    print("Shape:", img.shape)
    print("Dimensiones:", img.ndim)

    if img is None:
        return False

    if img.shape[2] == 4:
        bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    else:
        bgr = img.copy()

    # Segmentación con BiSeNet
    parsing = segmentar(model, device, bgr)

    # Máscara del cabello
    mascara = np.zeros(parsing.shape, dtype=np.uint8)

    # Clase 17 = Hair
    mascara[parsing == 17] = 255

    # Suavizar un poco los bordes
    kernel = np.ones((3, 3), np.uint8)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel)
    mascara = cv2.GaussianBlur(mascara, (5, 5), 0)

    # Crear PNG con transparencia
    bgra = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = mascara

    return cv2.imwrite(ruta_peluca, bgra)

def limpiar_mascara_corte(corte, mascara):
    if corte is None or mascara is None:
        return mascara

    img = _asegurar_imagen(corte)
    if img is None:
        return mascara

    h, w = img.shape[:2]
    try:
        if img.ndim == 2:
            rgb = img
        else:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        with mp.solutions.face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.3
        ) as detector:
            result = detector.process(rgb)

        if not result.detections:
            return mascara

        box = result.detections[0].location_data.relative_bounding_box
        x = int(box.xmin * w)
        y = int(box.ymin * h)
        width = int(box.width * w)
        height = int(box.height * h)

        face_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.ellipse(
            face_mask,
            (x + width // 2, y + height // 2),
            (max(1, width // 2), max(1, height // 2)),
            0,
            0,
            360,
            255,
            -1
        )

        mascara[face_mask > 0] = 0
    except Exception:
        return mascara

    return mascara



def procesar_foto(ruta_foto, orientacion):
    """
    Procesa una foto según la orientación indicada.
    Retorna la imagen procesada o None si hay error.
    """
    
    if orientacion not in {"frente", "perfil", "espalda"}:
        return None, "Orientación no válida"
    
    img = _asegurar_imagen(cv2.imread(ruta_foto))
    
    if img is None:
        return None, "No se pudo abrir la imagen"
    
    h, w = img.shape[:2]
    
    if orientacion == "espalda":
        crop = img
        alpha_crop = None
    else:
        if img.ndim == 2:
            rgb = img
        else:
            if img.shape[2] == 1:
                rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            else:
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        mp_face = mp.solutions.face_detection
        mp_mesh = mp.solutions.face_mesh
        
        with mp_face.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.3
        ) as detector, mp_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.3
        ) as mesh:
            
            det_res = detector.process(rgb)
            mesh_res = mesh.process(rgb)
        
        if not det_res.detections:
            return None, "No se detectó rostro"
        
        if mesh_res.multi_face_landmarks:
            landmarks = mesh_res.multi_face_landmarks[0].landmark
            face_points = np.array(
                [[int(lm.x * w), int(lm.y * h)] for lm in landmarks],
                dtype=np.int32
            )
            face_hull = cv2.convexHull(face_points)
            face_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.fillConvexPoly(face_mask, face_hull, 255)
            x1, y1 = face_points.min(axis=0)
            x2, y2 = face_points.max(axis=0)
            bw = x2 - x1
            bh = y2 - y1
        else:
            box = det_res.detections[0].location_data.relative_bounding_box
            x = int(box.xmin * w)
            y = int(box.ymin * h)
            bw = int(box.width * w)
            bh = int(box.height * h)
            x1 = max(0, x - int(bw * 0.10))
            x2 = min(w, x + bw + int(bw * 0.10))
            y1 = max(0, y - int(bh * 0.10))
            y2 = min(h, y + bh + int(bh * 0.10))
            face_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.ellipse(
                face_mask,
                (x + bw // 2, y + bh // 2),
                (max(1, bw // 2), max(1, bh // 2)),
                0,
                0,
                360,
                255,
                -1
            )
        
        pad_x = int(bw * 0.10)
        if orientacion == "frente":
            pad_y_top = int(bh * 0.55)
            pad_y_bottom = int(bh * 0.35)
        else:
            pad_y_top = int(bh * 0.40)
            pad_y_bottom = int(bh * 0.20)
        
        x1 = max(0, x1 - pad_x)
        x2 = min(w, x2 + pad_x)
        
        y1 = max(0, y1 - pad_y_top)
        y2 = min(h, y2 + pad_y_bottom)
        
        crop = img[y1:y2, x1:x2]
        alpha_crop = face_mask[y1:y2, x1:x2]
    
    crop = _asegurar_imagen(crop)

    if crop is None or crop.size == 0:
        return None, "Recorte vacío"

    # Centrado de imagen
    size = max(crop.shape[:2])
    y_offset = (size - crop.shape[0]) // 2
    x_offset = (size - crop.shape[1]) // 2

    if orientacion == "espalda":
        square = np.ones((size, size, 3), dtype=np.uint8) * 255
        square[
            y_offset:y_offset+crop.shape[0],
            x_offset:x_offset+crop.shape[1]
        ] = crop
        final = cv2.resize(square, (512, 512), interpolation=cv2.INTER_AREA)
        return final, "Éxito"

    if alpha_crop is None:
        square = np.ones((size, size, 3), dtype=np.uint8) * 255
        square[
            y_offset:y_offset+crop.shape[0],
            x_offset:x_offset+crop.shape[1]
        ] = crop
        final = cv2.resize(square, (512, 512), interpolation=cv2.INTER_AREA)
        return final, "Éxito"

    square_rgba = np.zeros((size, size, 4), dtype=np.uint8)
    square_rgba[
        y_offset:y_offset+crop.shape[0],
        x_offset:x_offset+crop.shape[1],
        :3
    ] = crop
    square_rgba[
        y_offset:y_offset+crop.shape[0],
        x_offset:x_offset+crop.shape[1],
        3
    ] = alpha_crop

    final = cv2.resize(square_rgba, (512, 512), interpolation=cv2.INTER_AREA)
    return final, "Éxito"


def generar_peinado(ruta_cara, ruta_peluca, carpeta_salida, model, device,orientacion=None):

    print(">>> ENTRÓ A generar_peinado()")
    os.makedirs(carpeta_salida, exist_ok=True)

    # ----------------------------
    # Cargar cliente
    # ----------------------------
    cara = cv2.imread(ruta_cara, cv2.IMREAD_UNCHANGED)

    if cara is None:
        raise Exception("No se pudo abrir la imagen del cliente.")

    if len(cara.shape) == 2:
        cara = cv2.cvtColor(cara, cv2.COLOR_GRAY2BGRA)
    elif cara.shape[2] == 3:
        cara = cv2.cvtColor(cara, cv2.COLOR_BGR2BGRA)

    # ----------------------------
    # Cargar peluca ya creada
    # ----------------------------
    peluca = cv2.imread(ruta_peluca, cv2.IMREAD_UNCHANGED)

    if peluca is None:
        raise Exception("No se pudo cargar la imagen de la peluca.")

    if len(peluca.shape) == 2:
        peluca = cv2.cvtColor(peluca, cv2.COLOR_GRAY2BGRA)
    elif peluca.shape[2] == 3:
        peluca = cv2.cvtColor(peluca, cv2.COLOR_BGR2BGRA)

    # ----------------------------
    # Escalar peluca
    # ----------------------------
    alto_cara, ancho_cara = cara.shape[:2]

    escala = ancho_cara / peluca.shape[1]

    nuevo_ancho = int(peluca.shape[1] * escala)
    nuevo_alto = int(peluca.shape[0] * escala)

    peluca = cv2.resize(
        peluca,
        (nuevo_ancho, nuevo_alto),
        interpolation=cv2.INTER_AREA
    )

    # ----------------------------
    # Posición
    # ----------------------------
    resultado = cara.copy()

    x = max(0, (ancho_cara - nuevo_ancho) // 2)
    y = 0

    h = min(nuevo_alto, resultado.shape[0] - y)
    w = min(nuevo_ancho, resultado.shape[1] - x)

    roi = resultado[y:y+h, x:x+w]
    peluca = peluca[:h, :w]

    alpha = peluca[:, :, 3].astype(np.float32) / 255.0

    for c in range(3):
        roi[:, :, c] = (
            alpha * peluca[:, :, c]
            + (1.0 - alpha) * roi[:, :, c]
        ).astype(np.uint8)

    roi[:, :, 3] = np.maximum(
        roi[:, :, 3],
        peluca[:, :, 3]
    )

    resultado[y:y+h, x:x+w] = roi
# ----------------------------
# Guardar resultado
# ----------------------------
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    nombre_resultado = f"resultado_{timestamp}.png"

    ruta_resultado = os.path.join(
        carpeta_salida,
        nombre_resultado
    )

    cv2.imwrite(ruta_resultado, resultado)

    print(">>> GUARDANDO RESULTADO:", ruta_resultado)

    return ruta_resultado