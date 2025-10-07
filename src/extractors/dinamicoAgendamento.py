import time
from captureSession import capture_session
from downloadCsv import download_csv
import json
import os
from utils import medir_tempo, gerar_periodos_formatados


@medir_tempo
def dinamicoAgendamento():
    print("🏁🏁🏁\n🏁 Iniciando extração do relatorio: Dinâmico Agendamentos - Regulação")

    lista_de_periodos = gerar_periodos_formatados()

    for periodo in lista_de_periodos:
        inicio = time.time()
        print(f'\n📅 Extraindo: "{periodo["nome"]}" ({periodo["inicio"]} a {periodo["fim"]})')

        payload_raw = os.getenv("DinamicoAgendamento_payload")
        payload_str = payload_raw.replace("startDate", periodo["inicio"]).replace("endDate", periodo["fim"])
        payload = json.loads(payload_str)
        jsonCompleto = capture_session(payload)
        print("🔗 Link do JSON Completo:", jsonCompleto)

        nomeRelatorio = periodo["filename"]
        download_csv(jsonCompleto, "DinamicoAgendamento_" + nomeRelatorio)

        fim = time.time()
        tempo_total_minutos = (fim - inicio) / 60
        print(f'⏰ Tempo para extrair "{periodo["nome"]}": {tempo_total_minutos:.2f} minutos.')


if __name__ == "__main__":
    dinamicoAgendamento()
