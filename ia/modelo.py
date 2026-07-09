from xml.parsers.expat import model
import torch
import numpy as np
import cv2
from ia.bisenet import BiSeNet

# =========================
# 1. CARGAR MODELO
# =========================

def cargar_modelo(peso_path="ia/pesos/bisenet.pth"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = BiSeNet(n_classes=19)
    model.load_state_dict(
        torch.load(peso_path, map_location=device)
    )

    model.to(device)
    model.eval()

    print("✔ Modelo BiSeNet cargado correctamente")
    return model, device
# =========================
# 2. SEGMENTACIÓN (AQUÍ VA TU FUNCIÓN)
# =========================
def segmentar(model, device, imagen):

    if imagen is None:
        raise ValueError("La imagen es None")

    h, w = imagen.shape[:2]

    img = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (512, 512))

    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    img = torch.tensor(img).unsqueeze(0).to(device)

    with torch.no_grad():
        out = model(img)[0]

    parsing = out.squeeze(0).cpu().numpy().argmax(0).astype(np.uint8)

    parsing = cv2.resize(
        parsing,
        (w, h),
        interpolation=cv2.INTER_NEAREST
    )

    return parsing

def mascara_cabello(parsing):

    mascara = np.zeros(parsing.shape, dtype=np.uint8)

    # Cabello
    mascara[parsing == 17] = 255

    return mascara