from datetime import datetime
import os
import re
import sys
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import pandas as pd
import time
from urllib.error import HTTPError
from tqdm import tqdm


def download_csv(jsonCompleto, nomeRelatorio):
    maximo_minutos = 10
    intervalo_segundos = 10
    max_tentativas = (maximo_minutos * 60) // intervalo_segundos
    df = None
    for tentativa in tqdm(range(max_tentativas), desc="⏳ Carregando JSON"):
        try:
            # df = pd.read_json(jsonCompleto)
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

        # Salva o .CSV
        brasilia_tz = ZoneInfo("America/Sao_Paulo")
        timestamp = datetime.now(brasilia_tz).strftime("%Y%m%d-%H%M%S")
        if "google.colab" in sys.modules or "COLAB_RELEASE_TAG" in os.environ:
            save_path = os.getenv("save_path_google")
        else:
            save_path = os.getenv("save_path_local")
        save_path_full = f"{save_path}{nomeRelatorio}__{timestamp}.csv"
        df.to_csv(save_path_full, index=False, encoding="utf-8-sig", sep=";")
        print(f"✅ CSV salvo em: {save_path}")

    else:
        print(f"Falha ao carregar o JSON após {maximo_minutos} minutos tentando.")
