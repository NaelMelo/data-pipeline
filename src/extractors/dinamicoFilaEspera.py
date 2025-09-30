from datetime import date
import time
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta
from extractors.captureSession import capture_session
from extractors.downloadCsv import download_csv
from dotenv import load_dotenv
import json
import os
from utils import medir_tempo

load_dotenv(dotenv_path=".env.local")


@medir_tempo
def _dinamicoFilaEspera():

    print("🏁 Iniciando extração do relatorio: DinamicoFilaEspera\n")

    payload = json.loads(os.getenv("DinamicoFilaEspera_payload"))
    # payload = json.loads(os.getenv("DinamicoAgendamento_payload_test"))# uso para testagem rapida
    jsonCompleto = capture_session(payload)
    print("🔗 Link do JSON Completo:", jsonCompleto)

    nomeRelatorio = "Fila Ambulatorial"
    download_csv(jsonCompleto, nomeRelatorio)


if __name__ == "__main__":
    _dinamicoFilaEspera()
