import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()


def capture_session(payload):
    url_login_page = os.getenv("url_login_page")
    url_login = os.getenv("url_login")
    url_api = os.getenv("url_api")
    url_dinamico = os.getenv("url_dinamico")
    url_form_data = json.loads(os.getenv("url_form_data"))
    url_headers = json.loads(os.getenv("url_headers"))

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
        print("🧾 JSON Recebido:", data)
        resultado = data["Resultado"]
        return url_dinamico + resultado + "/completo/completo.json"
    else:
        print("Erro:", response.status_code, response.text[:500])

    session.close()


if __name__ == "__main__":
    payload = json.loads(os.getenv("DinamicoAgendamento_payload_test"))
    jsonCompleto = capture_session(payload)
    print("🔗 Link do JSON Completo:", jsonCompleto)
