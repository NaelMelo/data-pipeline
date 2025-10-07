from datetime import datetime
import os
import re
import sys
from zoneinfo import ZoneInfo
import pandas as pd
import time
from urllib.error import HTTPError
from tqdm import tqdm
from google.cloud import bigquery


def SendBigQuery(jsonCompleto, table_id, valor_periodo=None):
    maximo_minutos = 10
    intervalo_segundos = 10
    max_tentativas = (maximo_minutos * 60) // intervalo_segundos
    df = None
    for tentativa in tqdm(range(max_tentativas), desc="⏳ Carregando JSON"):
        try:
            if not isinstance(jsonCompleto, pd.DataFrame):
                df = pd.read_json(jsonCompleto)
                tqdm.write(f"🎯 JSON carregado em {(tentativa * intervalo_segundos)//60} minutos!")
                break
            else:
                df = jsonCompleto
                tqdm.write(f"🎯 DataFrame carregados!")
                break
        except HTTPError as e:
            if e.code in (404, 500):
                time.sleep(intervalo_segundos)
            else:
                tqdm.write(f"Erro HTTP inesperado: {e}")
                break
        except Exception as e:
            tqdm.write(f"Ocorreu um erro inesperado: {e}")
            tqdm.write("Interrompendo as tentativas.")
            break

    if df is not None:
        # Encontra as colunas com data e ajusta
        padrao_timestamp = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
        colunas_transformadas = []
        for coluna in df.columns:
            if df[coluna].dtype == "object":
                primeiro_valor_valido = df[coluna].dropna().iloc[0] if not df[coluna].dropna().empty else None
                if (
                    primeiro_valor_valido
                    and isinstance(primeiro_valor_valido, str)
                    and padrao_timestamp.match(primeiro_valor_valido)
                ):
                    df[coluna] = df[coluna].str[:10]
                    colunas_transformadas.append(coluna)

        # Adiciona timestamp do relatório
        brasilia_tz = ZoneInfo("America/Sao_Paulo")
        timestamp_atual = datetime.now(brasilia_tz)
        df["Extracao_Timestamp"] = timestamp_atual.strftime("%Y-%m-%d %H:%M:%S")

        client = bigquery.Client()
        if valor_periodo is not None:
            df["Periodo"] = valor_periodo
            query = f"""
                DELETE FROM `{table_id}`
                WHERE periodo = '{valor_periodo}'
            """
            query_job = client.query(query)
            query_job.result()
            write_disposition = "WRITE_APPEND"
        else:
            write_disposition = "WRITE_TRUNCATE"

        job = client.load_table_from_dataframe(
            df, table_id, job_config=bigquery.LoadJobConfig(write_disposition=write_disposition)
        )
        job.result()
        print("Tabela atualizada com sucesso!")

    else:
        print(f"Falha ao carregar o JSON/DF após {maximo_minutos} minutos tentando.")
