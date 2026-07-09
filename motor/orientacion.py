import cv2
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh


def detectar_orientacion(img):

    if img is None:
        return None

    # Convertir la imagen a RGB
    if len(img.shape) == 2:
        rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    elif img.shape[2] == 4:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
    else:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Detectar rostro y landmarks
    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.2
    ) as face_mesh:

        resultado = face_mesh.process(rgb)

    # Si no detectó rostro asumimos que es una foto de espalda
    if not resultado.multi_face_landmarks:
        print("No se detectó rostro -> Espalda")
        return "espalda"

    print("Rostro detectado")

    landmarks = resultado.multi_face_landmarks[0].landmark

    nariz = landmarks[1]

    ojo_izq = landmarks[33]
    ojo_der = landmarks[263]

    sien_izq = landmarks[234]
    sien_der = landmarks[454]

    oreja_izq = landmarks[127]
    oreja_der = landmarks[356]

    # ← AQUÍ VA EL CÁLCULO DE DISTANCIAS

    d_ojos = abs(ojo_der.x - ojo_izq.x)

    d_nariz_izq = abs(nariz.x - ojo_izq.x)
    d_nariz_der = abs(ojo_der.x - nariz.x)

    d_sien_izq = abs(nariz.x - sien_izq.x)
    d_sien_der = abs(sien_der.x - nariz.x)

    d_oreja_izq = abs(nariz.x - oreja_izq.x)
    d_oreja_der = abs(oreja_der.x - nariz.x)

    indice_ojos = d_nariz_izq / (d_nariz_der + 1e-6)
    indice_sienes = d_sien_izq / (d_sien_der + 1e-6)
    indice_orejas = d_oreja_izq / (d_oreja_der + 1e-6)

    print(f"Índice ojos   : {indice_ojos:.2f}")
    print(f"Índice sienes : {indice_sienes:.2f}")
    print(f"Índice orejas : {indice_orejas:.2f}")

    # ← DESPUÉS VAN LOS print()

    print("----------")
    print("Nariz-Ojo Izq :", d_nariz_izq)
    print("Nariz-Ojo Der :", d_nariz_der)
    print("Nariz-Sien Izq:", d_sien_izq)
    print("Nariz-Sien Der:", d_sien_der)
    print("Nariz-Oreja Izq:", d_oreja_izq)
    print("Nariz-Oreja Der:", d_oreja_der)
    print("Distancia ojos:", d_ojos)

    # ← Y DESPUÉS EL ÍNDICE

    indice = (indice_ojos + indice_sienes + indice_orejas) / 3

    print(f"Índice promedio: {indice:.2f}")
    
    if indice > 1.70:
        orientacion = "perfil_derecho"
    elif indice < 0.55:
        orientacion = "perfil_izquierdo"
    else:
        orientacion = "frente"

    print("Orientación:", orientacion)

    return orientacion