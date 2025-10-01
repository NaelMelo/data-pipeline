import os
from dotenv import load_dotenv
import pandas as pd
import requests
import json
from downloadCsv import download_csv
from zoneinfo import ZoneInfo
from datetime import datetime
from utils import medir_tempo

load_dotenv(dotenv_path=".env.local")


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
def agendamentosIntegrado():
    # payload = json.loads(os.getenv("Agendamentos_Integrados_url_payload"))
    # jsonCompleto = captureSession_agendamentosIntegrado(payload)
    # df = pd.json_normalize(jsonCompleto["GridAgendamento"])
    # print(df)
    print("🏁🏁🏁\n🏁 Iniciando extração do relatorio: AgendamentosIntegrado\n")
    brasilia_tz = ZoneInfo("America/Sao_Paulo")
    datetimeNow = datetime.now(brasilia_tz).strftime("%Y-%m-%d")
    payload_raw = os.getenv("Agendamentos_Integrados_url_payload")
    payload_str = payload_raw.replace("endDate", datetimeNow)
    payload = json.loads(payload_str)

    jsonRaw = captureSession_agendamentosIntegrado(payload)
    jsonCompleto = pd.json_normalize(jsonRaw["GridAgendamento"])

    download_csv(jsonCompleto, "Relatório de Agendamentos Integrados")


if __name__ == "__main__":
    agendamentosIntegrado()
