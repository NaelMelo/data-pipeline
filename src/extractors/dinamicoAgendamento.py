import time
import json
import os
from .captureSession import capture_session
from .utils import medir_tempo, gerar_periodos_formatados
from .pipeline_bigquery import carregar_dados_bigquery

# from downloadCsv import download_csv
# from extractors._df_to_bigquery import SendBigQuery
# from . import config_loader
# config_loader.setup_environment()


@medir_tempo
def dinamicoAgendamento():
    print("🏁🏁🏁\n🏁 Iniciando extração do relatorio: Dinâmico Agendamentos - Regulação\n◽")

    lista_de_periodos = gerar_periodos_formatados()

    for periodo in lista_de_periodos:
        inicio = time.time()
        print(f'📅 Extraindo: "{periodo["nome"]}" ({periodo["inicio"]} a {periodo["fim"]})')

        payload_raw = os.getenv("DinamicoAgendamento_payload")
        payload_str = payload_raw.replace("startDate", periodo["inicio"]).replace("endDate", periodo["fim"])
        payload = json.loads(payload_str)
        json_completo = capture_session(payload)
        print("🔗 Link do JSON Completo:", json_completo)

        # nomeRelatorio = periodo["filename"]
        # download_csv(jsonCompleto, "DinamicoAgendamento_" + nomeRelatorio)

        tabela_bq = os.getenv("DinamicoAgendamento_table")
        mapping_str = os.getenv("DinamicoAgendamento_mapamento_bq")
        mapeamento_bq = json.loads(mapping_str)

        carregar_dados_bigquery(json_completo, tabela_bq, mapeamento_bq, periodo["filename"])

        fim = time.time()
        tempo_total_minutos = (fim - inicio) / 60
        print(f'⏰ Tempo para extrair "{periodo["nome"]}": {tempo_total_minutos:.2f} minutos.\n◽')


if __name__ == "__main__":
    dinamicoAgendamento()
