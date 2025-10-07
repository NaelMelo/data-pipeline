import os
import pandas as pd
import requests
import json
from downloadCsv import download_csv
from zoneinfo import ZoneInfo
from datetime import datetime
from utils import medir_tempo


def captureSession_agendamentosIntegrado(payload):
    url_login_page = os.getenv("Agendamentos_Integrados_url_login_page")
    url_login = os.getenv("Agendamentos_Integrados_url_login")
    url_api = os.getenv("Agendamentos_Integrados_url_api")
    url_form_data = json.loads(os.getenv("Agendamentos_Integrados_url_form_data"))
    url_headers = json.loads(os.getenv("Agendamentos_Integrados_url_headers"))

    try:
        session = requests.Session()
        session.get(url_login_page, headers=url_headers)
        session.post(url_login, data=url_form_data, headers=url_headers)

    except requests.exceptions.RequestException as e:
        print("\nErro na Requisição:", str(e))

    response = session.post(url_api, json=payload)

    if response.status_code == 200 and "application/json" in response.headers.get("Content-Type", ""):
        data = response.json()
        data = json.loads(data)
        print("🧾 JSON Recebido")
        return data
    else:
        print("Erro:", response.status_code, response.text[:500])

    session.close()


@medir_tempo
def agendamentos_integrado():
    print("🏁🏁🏁\n🏁 Iniciando extração do relatorio: Relatório de Agendamentos Integrados\n◽")
    brasilia_tz = ZoneInfo("America/Sao_Paulo")
    datetime_now = datetime.now(brasilia_tz).strftime("%Y-%m-%d")
    payload_raw = os.getenv("Agendamentos_Integrados_url_payload")
    payload_str = payload_raw.replace("endDate", datetime_now)
    payload = json.loads(payload_str)

    json_raw = captureSession_agendamentosIntegrado(payload)
    json_completo = pd.json_normalize(json_raw["GridAgendamento"])

    download_csv(json_completo, "dinamicoAgendamentosIntegrado_")


if __name__ == "__main__":
    agendamentos_integrado()
