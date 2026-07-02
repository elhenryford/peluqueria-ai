import cv2
import mediapipe as mp
import os


mp_face = mp.solutions.face_detection


def detectar_cara(img):
    with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb)

        if not results.detections:
            return None

        h, w, _ = img.shape
        det = results.detections[0]
        box = det.location_data.relative_bounding_box

        x = int(box.xmin * w)
        y = int(box.ymin * h)
        bw = int(box.width * w)
        bh = int(box.height * h)

        return x, y, bw, bh


def generar_peinado(path_cliente, path_corte, output_folder):

    cliente = cv2.imread(path_cliente)
    corte = cv2.imread(path_corte)

    if cliente is None or corte is None:
        raise ValueError("No se pudieron cargar las imágenes")

    box = detectar_cara(cliente)

    if box is None:
        raise ValueError("No se detectó cara")

    x, y, w, h = box

    corte_resized = cv2.resize(corte, (w, h))

    h_img, w_img, _ = cliente.shape

    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(w_img, x + w)
    y2 = min(h_img, y + h)

    roi = cliente[y1:y2, x1:x2]
    corte_crop = corte_resized[0:(y2 - y1), 0:(x2 - x1)]

    if roi.shape[:2] == corte_crop.shape[:2]:
        blended = cv2.addWeighted(roi, 0.4, corte_crop, 0.6, 0)
        cliente[y1:y2, x1:x2] = blended

    nombre_salida = os.path.join(output_folder, "resultado.png")
    cv2.imwrite(nombre_salida, cliente)

    return nombre_salida