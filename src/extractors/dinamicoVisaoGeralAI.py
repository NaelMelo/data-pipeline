import time
from captureSession import capture_session
from downloadCsv import download_csv
import json
import os
from extractors._df_to_bigquery import SendBigQuery
from utils import medir_tempo, gerar_periodos_formatados


@medir_tempo
def dinamicoVisaoGeralAI():
    print("🏁🏁🏁\n🏁 Iniciando extração do relatorio: Dinâmico Visão Geral CP - Agendas Integração\n◽")

    lista_de_periodos = gerar_periodos_formatados()

    for periodo in lista_de_periodos:
        inicio = time.time()
        print(f'📅 Extraindo: "{periodo["nome"]}" ({periodo["inicio"]} a {periodo["fim"]})')

        payload_raw = os.getenv("dinamicoVisaoGeralCP_IA_payload")
        payload_str = payload_raw.replace("startDate", periodo["inicio"]).replace("endDate", periodo["fim"])
        payload = json.loads(payload_str)
        jsonCompleto = capture_session(payload)
        print("🔗 Link do JSON Completo:", jsonCompleto)

        # nomeRelatorio = periodo["filename"]
        # download_csv(jsonCompleto, "DinamicoVisaoGeralAI_" + nomeRelatorio)
        SendBigQuery(jsonCompleto, os.getenv("DinamicoVisaoGeralCP_IA_table"), periodo["filename"])

        fim = time.time()
        tempo_total_minutos = (fim - inicio) / 60
        print(f'⏰ Tempo para extrair "{periodo["nome"]}": {tempo_total_minutos:.2f} minutos.')


if __name__ == "__main__":
    dinamicoVisaoGeralAI()
