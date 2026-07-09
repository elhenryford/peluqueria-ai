import cv2
import mediapipe as mp
from tkinter import Tk, filedialog

mp_face_mesh = mp.solutions.face_mesh

# ============================
# CAMBIA ESTA RUTA POR TU FOTO
# ============================

Tk().withdraw()

RUTA = filedialog.askopenfilename(
    title="Seleccione una fotografía",
    filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp")]
)
img = cv2.imread(RUTA)

if img is None:
    print("No se pudo abrir la imagen.")
    exit()

rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

with mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.2,
    min_tracking_confidence=0.2
) as face_mesh:
    print("Forma:", rgb.shape)
    print("Tipo:", rgb.dtype)
    cv2.imwrite("debug_rgb.jpg", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))

    resultado = face_mesh.process(rgb)
    print("multi_face_landmarks:", resultado.multi_face_landmarks)
if not resultado.multi_face_landmarks:
    print("\nNo se detectó rostro.")
    print("Orientación: ESPALDA")
    exit()

print("\nRostro detectado\n")

landmarks = resultado.multi_face_landmarks[0].landmark

nariz = landmarks[1]

ojo_izq = landmarks[33]
ojo_der = landmarks[263]

sien_izq = landmarks[234]
sien_der = landmarks[454]

oreja_izq = landmarks[127]
oreja_der = landmarks[356]

# ==========================
# DISTANCIAS
# ==========================

d_ojos = abs(ojo_der.x - ojo_izq.x)

d_nariz_izq = abs(nariz.x - ojo_izq.x)
d_nariz_der = abs(ojo_der.x - nariz.x)

d_sien_izq = abs(nariz.x - sien_izq.x)
d_sien_der = abs(sien_der.x - nariz.x)

d_oreja_izq = abs(nariz.x - oreja_izq.x)
d_oreja_der = abs(oreja_der.x - nariz.x)

# ==========================
# ÍNDICES
# ==========================

indice_ojos = d_nariz_izq / (d_nariz_der + 1e-6)
indice_sienes = d_sien_izq / (d_sien_der + 1e-6)
indice_orejas = d_oreja_izq / (d_oreja_der + 1e-6)

indice = (indice_ojos + indice_sienes + indice_orejas) / 3

# ==========================
# RESULTADOS
# ==========================

print("===== DISTANCIAS =====")
print(f"Ojos            : {d_ojos:.4f}")
print(f"Nariz-Ojo Izq   : {d_nariz_izq:.4f}")
print(f"Nariz-Ojo Der   : {d_nariz_der:.4f}")
print(f"Nariz-Sien Izq  : {d_sien_izq:.4f}")
print(f"Nariz-Sien Der  : {d_sien_der:.4f}")
print(f"Nariz-Oreja Izq : {d_oreja_izq:.4f}")
print(f"Nariz-Oreja Der : {d_oreja_der:.4f}")

print("\n===== ÍNDICES =====")
print(f"Ojos    : {indice_ojos:.2f}")
print(f"Sienes  : {indice_sienes:.2f}")
print(f"Orejas  : {indice_orejas:.2f}")
print(f"Promedio: {indice:.2f}")

if indice > 1.70:
    orientacion = "PERFIL DERECHO"
elif indice < 0.55:
    orientacion = "PERFIL IZQUIERDO"
else:
    orientacion = "FRENTE"

print("\n==============================")
print("ORIENTACIÓN:", orientacion)
print("==============================")

# Mostrar la imagen
cv2.imshow("Foto", img)
cv2.waitKey(0)
cv2.destroyAllWindows()