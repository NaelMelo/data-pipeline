from captureSession import capture_session
from downloadCsv import download_csv
import json
import os
from utils import medir_tempo


@medir_tempo
def dinamicoFilaEspera():
    print(f"🏁🏁🏁\n🏁 Iniciando extração do relatorio: Dinâmico Fila Espera\n")

    payload = json.loads(os.getenv("DinamicoFilaEspera_payload"))
    # payload = json.loads(os.getenv("DinamicoAgendamento_payload_test"))# uso para testagem rapida
    jsonCompleto = capture_session(payload)
    print("🔗 Link do JSON Completo:", jsonCompleto)

    nomeRelatorio = "Fila Ambulatorial"
    download_csv(jsonCompleto, "DinamicoFilaEspera_" + nomeRelatorio)


if __name__ == "__main__":
    dinamicoFilaEspera()
