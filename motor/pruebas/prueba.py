import cv2
from orientacion import detectar_orientacion

img = cv2.imread("foto.jpeg")

detectar_orientacion(img)