
import json
import random
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

URL_API = "http://127.0.0.1:8000/api/iot/medicion/"

DISPOSITIVO = "Sensor IoT de demostración"


def enviar_medicion():
    temperatura = round(random.uniform(20, 38), 1)
    humedad = round(random.uniform(30, 85), 1)

    datos = {
        "dispositivo": DISPOSITIVO,
        "temperatura": temperatura,
        "humedad": humedad,
    }

    cuerpo = json.dumps(datos).encode("utf-8")

    solicitud = Request(
        URL_API,
        data=cuerpo,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(solicitud, timeout=10) as respuesta:
            resultado = json.loads(
                respuesta.read().decode("utf-8")
            )

            print("Medición enviada correctamente")
            print(f"Temperatura: {temperatura} °C")
            print(f"Humedad: {humedad} %")
            print(f"Respuesta: {resultado}")
            print("-" * 40)

    except HTTPError as error:
        print(f"Error HTTP {error.code}:")
        print(error.read().decode("utf-8", errors="replace"))

    except URLError as error:
        print(f"No se pudo conectar con Django: {error.reason}")


if __name__ == "__main__":
    print("SIMULADOR IoT INICIADO")
    print("Frecuencia: cada 10 minutos")
    print("Presiona Ctrl+C para detenerlo.")
    print()

    try:
        while True:
            enviar_medicion()
            time.sleep(600)

    except KeyboardInterrupt:
        print("\nSimulador detenido.")
