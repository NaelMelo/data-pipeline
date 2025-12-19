import pandas as pd
import numpy as np
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from tqdm import tqdm
from urllib.error import HTTPError
import re
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, BadRequest
from unidecode import unidecode

from .utils import now_fortaleza

# =========================================================================
# FUNÇÕES DE LIMPEZA E PREPARAÇÃO (Do seu script original, com melhorias)
# =========================================================================


def clean_headers_custom_rules(df: pd.DataFrame, max_length: int = 300) -> pd.DataFrame:
    """
    Limpa os nomes das colunas de um DataFrame aplicando um conjunto de regras customizadas.
    """
    df_clean = df.copy()

    new_cols = df_clean.columns.to_series().map(unidecode)

    new_cols = (
        new_cols.str.replace(r"[()]", "", regex=True)  # Regra: Remover parênteses
        .str.replace("/", " ", regex=False)  # Regra: Substituir '/' por espaço
        .str.replace(r"\s+", " ", regex=True)  # Regra: Compactar espaços
        .str.strip()  # Regra: Remover espaços nas bordas
        .str.replace(r"^(\d)", r"col_\1", regex=True)  # Regra: Prefixo para dígitos
        .str.replace(r"_{2,}", "_", regex=True)  # Regra: Compactar underscores
        .str.strip("_")  # Regra: Remover underscores nas bordas
        .str.slice(0, max_length)  # Regra: Limitar comprimento
    )

    # Tratamento de colunas duplicadas
    if new_cols.duplicated().any():
        counts = {}
        final_cols = []
        for col in new_cols:
            if col in counts:
                counts[col] += 1
                final_cols.append(f"{col}_{counts[col]}")
            else:
                counts[col] = 0
                final_cols.append(col)
        df_clean.columns = final_cols
    else:
        df_clean.columns = new_cols

    return df_clean


def converter_tipos_bigquery(df: pd.DataFrame, mapeamento_bq: dict) -> pd.DataFrame:
    """
    Converte os tipos de todas as colunas de um DataFrame.
    - Usa o mapeamento para tipos específicos.
    - Converte para STRING qualquer coluna não mapeada.
    """
    print("🔄 Iniciando conversão de tipos...")
    df_copy = df.copy()

    # Itera sobre TODAS as colunas do DataFrame, não apenas as do mapeamento.
    for coluna in df_copy.columns:
        # Pega o tipo do mapeamento. Se não existir, o padrão é 'STRING'.
        tipo_bq = mapeamento_bq.get(coluna, "STRING").upper()

        try:
            if tipo_bq == "DATETIME":
                df_copy[coluna] = pd.to_datetime(df_copy[coluna], errors="coerce", format="mixed", dayfirst=True)
            elif tipo_bq == "DATE":
                df_copy[coluna] = pd.to_datetime(
                    df_copy[coluna], errors="coerce", format="mixed", dayfirst=True
                ).dt.date
            elif tipo_bq == "TIME":
                df_copy[coluna] = pd.to_datetime(df_copy[coluna], errors="coerce", format="mixed").dt.time
            elif tipo_bq == "BOOLEAN":
                mapa_bool = {"true": True, "false": False, "1": True, "0": False, "falso": False, "verdadeiro": True}
                df_copy[coluna] = df_copy[coluna].astype(str).str.lower().str.strip().map(mapa_bool).astype("boolean")
            elif tipo_bq in ["INT64", "INTEGER"]:
                df_copy[coluna] = pd.to_numeric(df_copy[coluna], errors="coerce").astype("Int64")
            elif tipo_bq in ["FLOAT64", "NUMERIC", "FLOAT"]:
                df_copy[coluna] = pd.to_numeric(df_copy[coluna], errors="coerce").astype("Float64")
            else:
                df_copy[coluna] = (
                    df_copy[coluna]
                    .astype(str)
                    .replace({"<NA>": np.nan, "nan": np.nan})
                    .infer_objects(copy=False)
                    .astype("string")
                )

        except Exception as e:
            print(f"   - ❌ Erro ao converter '{coluna}' para {tipo_bq}: {e}")

    print("✅ Conversão de tipos finalizada.")
    return df_copy


def gerar_schema_bigquery(df: pd.DataFrame, mapeamento_bq_limpo: dict):
    """
    Gera o schema BigQuery (SchemaField) com base no DataFrame final e no mapeamento.
    """
    print("🧱 Gerando schema do BigQuery...")
    schema = []
    for coluna in df.columns:
        # Define STRING como padrão se a coluna não estiver no mapeamento
        tipo_bq = mapeamento_bq_limpo.get(coluna, "STRING").upper()
        schema.append(bigquery.SchemaField(coluna, tipo_bq, mode="NULLABLE"))

    print("✅ Schema do BigQuery gerado.")
    return schema


def filtrar_colunas_existentes_bq(df: pd.DataFrame, table_id: str, client: bigquery.Client) -> pd.DataFrame:
    """
    Remove do DataFrame todas as colunas que não existem na tabela do BigQuery.
    """
    try:
        table = client.get_table(table_id)
        colunas_bq = {field.name for field in table.schema}

        colunas_df = set(df.columns)
        colunas_ignoradas = colunas_df - colunas_bq

        if colunas_ignoradas:
            print(f"⚠️ Colunas ignoradas (não existem no BigQuery): {sorted(colunas_ignoradas)}")

        return df[[c for c in df.columns if c in colunas_bq]]

    except NotFound:
        print("⚠️ Tabela ainda não existe. Nenhuma coluna será filtrada.")
        return df


# =========================================================================
# FUNÇÃO PRINCIPAL DE ORQUESTRAÇÃO E ENVIO
# =========================================================================


def carregar_dados_bigquery(json_ou_df, table_id, mapeamento_bq, valor_periodo=None, delimitador_csv=","):
    """
    Orquestra o processo completo: carrega, limpa, converte e envia dados para o BigQuery.

    Args:
        json_ou_df (str or pd.DataFrame): Caminho para o arquivo JSON/CSV ou um DataFrame.
        table_id (str): ID completo da tabela no BigQuery (ex: 'projeto.dataset.tabela').
        mapeamento_bq (dict): Dicionário com {Nome Original da Coluna: Tipo BigQuery}.
        valor_periodo (str, optional): Valor para a coluna 'Periodo', usado para deletar dados antigos.
        delimitador_csv (str, optional): Delimitador para arquivos CSV. Padrão é ','.
    """
    print(f"🚀 Iniciando pipeline para a tabela: {table_id}")
    maximo_minutos = 10
    intervalo_segundos = 10
    max_tentativas = (maximo_minutos * 60) // intervalo_segundos
    df = None

    for tentativa in tqdm(range(max_tentativas), desc="⏳ Carregando JSON"):
        try:
            if not isinstance(json_ou_df, pd.DataFrame):
                df = pd.read_json(json_ou_df)
                tqdm.write(f"🎯 JSON carregado em {(tentativa * intervalo_segundos)//60} minutos!")
                break
            else:
                df = json_ou_df
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
        if df.empty or len(df) <= 10:
            print(f"🛑 Aviso: O DataFrame resultante está vazio (0 registros). Pulando o envio de '{table_id}'.")
            return

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

        # --- ETAPA 1: Limpeza dos Cabeçalhos ---
        print("✨ Iniciando limpeza dos cabeçalhos...")
        df_limpo = clean_headers_custom_rules(df)

        client = bigquery.Client()
        df_limpo = filtrar_colunas_existentes_bq(df_limpo, table_id, client)

        print("✅ Cabeçalhos limpos e padronizados.")

        # --- ETAPA 2: Ajuste do Mapeamento ---
        mapeamento_bq_limpo = {
            clean_headers_custom_rules(pd.DataFrame(columns=[k])).columns[0]: v for k, v in mapeamento_bq.items()
        }

        # --- ETAPA 3: Conversão de Tipos ---
        df_convertido = converter_tipos_bigquery(df_limpo, mapeamento_bq_limpo)

        # --- ETAPA 4: Geração do Schema ---
        schema_bq = gerar_schema_bigquery(df_convertido, mapeamento_bq_limpo)

        # --- ETAPA 5: Adicionar Colunas de Metadados ---
        df_convertido["extracao_timestamp"] = now_fortaleza()
        if "extracao_timestamp" not in mapeamento_bq_limpo:
            schema_bq.append(bigquery.SchemaField("extracao_timestamp", "DATETIME"))
        print("⏲️ Adicionada coluna de 'extracao_timestamp'")

        # --- ETAPA 6: Lógica de Envio para o BigQuery ---
        client = bigquery.Client()

        if valor_periodo:
            df_convertido["periodo"] = valor_periodo
            if "periodo" not in mapeamento_bq_limpo:
                schema_bq.append(bigquery.SchemaField("periodo", "STRING"))
            print(f"⚠️ Coluna 'periodo' adicionada com valor '{valor_periodo}'.")

            print(f"🔄 Modo de atualização: Deletando registros para o período '{valor_periodo}'...")
            query = f"DELETE FROM `{table_id}` WHERE periodo = '{valor_periodo}'"
            try:
                query_job = client.query(query)
                query_job.result()
                print(f"⚠️ Registros antigos removidos com sucesso.")
            except NotFound:
                print(f"⚠️ A tabela '{table_id}' não existe ainda. A etapa DELETE foi ignorada.")
            except BadRequest as e:
                if "Unrecognized name: periodo" in str(e):
                    print(
                        f"⚠️ A coluna 'periodo' não existe na tabela. A etapa DELETE foi ignorada (provavelmente é a primeira carga)."
                    )
                else:
                    raise e

            job_config = bigquery.LoadJobConfig(
                schema=schema_bq,
                write_disposition="WRITE_APPEND",
                create_disposition="CREATE_IF_NEEDED",
            )
        else:
            print("🔄 Modo de atualização: Substituindo a tabela inteira (WRITE_TRUNCATE)...")
            job_config = bigquery.LoadJobConfig(
                schema=schema_bq,
                write_disposition="WRITE_TRUNCATE",
                create_disposition="CREATE_IF_NEEDED",
            )

        print(f"📤 Enviando {len(df_convertido)} linhas para o BigQuery...")
        try:
            job = client.load_table_from_dataframe(df_convertido, table_id, job_config=job_config)
            job.result()
            print(f"✅ Sucesso! Tabela '{table_id}' foi atualizada.")
        except Exception as e:
            print(f"❌ Falha ao enviar dados para o BigQuery: {e}")
    else:
        print(f"Falha ao carregar o JSON/DF após {maximo_minutos} minutos tentando.")
