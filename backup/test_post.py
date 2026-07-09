import requests

url = 'http://localhost:5000/upload'
files = {
    'cliente': open('fotos_frente/foto1.jpg', 'rb'),
    'corte': open('fotos_perfil/foto3.jpg', 'rb')
}
print('Enviando POST a', url)
try:
    r = requests.post(url, files=files, timeout=30)
    print('Status:', r.status_code)
    try:
        print('JSON:', r.json())
    except Exception:
        print('Respuesta:', r.text[:1000])
except Exception as e:
    print('Error al enviar:', e)
finally:
    for f in files.values():
        try:
            f.close()
        except:
            pass
