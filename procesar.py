from dotenv import load_dotenv
import os
import base64
from openai import OpenAI
from datetime import datetime

# =========================
# CARGAR VARIABLES .env
# =========================
load_dotenv()

# =========================
# CLIENTE OPENAI
# =========================
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generar_peinado(cliente_path, corte_path, output_folder):
    """
    Envía las dos imágenes a GPT Image y genera resultado.
    """

    with open(cliente_path, "rb") as f1, open(corte_path, "rb") as f2:

        response = client.images.edit(
            model="gpt-image-1",
            image=[f1, f2],
            prompt=(
                "Usa la primera imagen como cliente. "
                "Usa la segunda imagen como referencia de peinado. "
                "Transfiere el peinado al cliente manteniendo: "
                "rostro, identidad, iluminación, ángulo y calidad fotográfica. "
                "Resultado realista estilo peluquería profesional."
            )
        )

    image_base64 = response.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    filename = f"resultado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    output_path = os.path.join(output_folder, filename)

    with open(output_path, "wb") as f:
        f.write(image_bytes)

    return output_path