import time
import json
import os
from .captureSession import capture_session
from .utils import gerar_periodos_formatados_FULL, medir_tempo, gerar_periodos_formatados
from .pipeline_bigquery import carregar_dados_bigquery

# from .downloadCsv import download_csv
# from ._df_to_bigquery import SendBigQuery


def _executar_extracao_dinamica(nome_relatorio: str, payload_env_var: str, table_env_var: str):
    print(f"🏁🏁🏁\n🏁 Iniciando extração do relatorio: {nome_relatorio}")

    lista_de_periodos = gerar_periodos_formatados()
    # lista_de_periodos = gerar_periodos_formatados_FULL("2023-01")

    for periodo in lista_de_periodos:
        inicio = time.time()
        print(f'◽\n📅 Extraindo: "{periodo["nome"]}" ({periodo["inicio"]} a {periodo["fim"]})')

        payload_raw = os.getenv(payload_env_var)
        payload_str = payload_raw.replace("startDate", periodo["inicio"]).replace("endDate", periodo["fim"])
        payload = json.loads(payload_str)

        json_completo = capture_session(payload)
        print("🔗 Link do JSON Completo:", json_completo)

        tabela_bq = os.getenv(table_env_var)

        # download_csv(jsonCompleto, "DinamicoVisaoGeralCP_" + periodo["filename"])
        # SendBigQuery(jsonCompleto, tabela_bq, periodo["filename"])

        mapping_str = os.getenv("DinamicoVisaoGeral_mapamento_bq")
        mapeamento_bq = json.loads(mapping_str)

        carregar_dados_bigquery(json_completo, tabela_bq, mapeamento_bq, periodo["filename"])

        fim = time.time()
        tempo_total_minutos = (fim - inicio) / 60
        print(f'⏰ Tempo para extrair "{periodo["nome"]}": {tempo_total_minutos:.2f} minutos.')


@medir_tempo
def dinamicoVisaoGeralCP():
    """Extrai o relatório 'Dinâmico Visão Geral CP - Visão Geral C.P.'"""
    _executar_extracao_dinamica(
        nome_relatorio="Dinâmico Visão Geral CP - Visão Geral C.P.",
        payload_env_var="dinamicoVisaoGeralCP_payload",
        table_env_var="DinamicoVisaoGeralCP_table",
    )


@medir_tempo
def dinamicoVisaoGeralAI():
    """Extrai o relatório 'Dinâmico Visão Geral CP - Agendas Integração'"""
    _executar_extracao_dinamica(
        nome_relatorio="Dinâmico Visão Geral CP - Agendas Integração",
        payload_env_var="dinamicoVisaoGeralCP_IA_payload",
        table_env_var="DinamicoVisaoGeralCP_IA_table",
    )
