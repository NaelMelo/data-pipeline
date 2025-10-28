import os
import json
from .captureSession import capture_session
from .utils import medir_tempo
from .pipeline_bigquery import carregar_dados_bigquery

# from extractors._df_to_bigquery import SendBigQuery
# from downloadCsv import download_csv


@medir_tempo
def dinamicoFilaEspera():
    print(f"🏁🏁🏁\n🏁 Iniciando extração do relatorio: Dinâmico Fila Espera\n◽")

    payload = json.loads(os.getenv("DinamicoFilaEspera_payload"))
    # payload = json.loads(os.getenv("DinamicoAgendamento_payload_test")) # uso para testagem rapida

    json_completo = capture_session(payload)
    print("🔗 Link do JSON Completo:", json_completo)

    # nomeRelatorio = "Fila Ambulatorial"
    # download_csv(json_completo, "DinamicoFilaEspera_" + nomeRelatorio)
    # SendBigQuery(json_completo, os.getenv("DinamicoFilaEspera_table"))

    tabela_bq = os.getenv("DinamicoFilaEspera_table")
    mapping_str = os.getenv("DinamicoFilaEspera_mapamento_bq")
    mapeamento_bq = json.loads(mapping_str)

    carregar_dados_bigquery(json_completo, tabela_bq, mapeamento_bq)
