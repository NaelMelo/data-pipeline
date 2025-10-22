import os
import io
from dotenv import load_dotenv, dotenv_values
from google.cloud import secretmanager

SECRET_NAME = "Fast_Medic"


def setup_environment():
    """
    Carrega as variáveis de ambiente.

    - Se rodando no Google Cloud (ex: Colab Enterprise), busca do Secret Manager.
    - Se rodando localmente, busca de um arquivo .env.
    """

    # Verifica se está rodando no Google Cloud (Colab Ent. define esta variável)
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    if project_id:
        # --- ESTAMOS NO COLAB ENTERPRISE ---
        print("Ambiente Google Cloud detectado. Carregando secrets do Secret Manager...")
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{SECRET_NAME}/versions/latest"

            response = client.access_secret_version(request={"name": name})
            payload_str = response.payload.data.decode("UTF-8")

            # Usa dotenv_values para "ler" a string como se fosse um arquivo .env
            env_data = dotenv_values(stream=io.StringIO(payload_str))

            # Injeta CADA chave/valor lido do secret em os.environ
            for key, value in env_data.items():
                if key not in os.environ:  # Evita sobrescrever vars do sistema
                    os.environ[key] = value

            print(f"Sucesso: {len(env_data)} variáveis de ambiente carregadas do Secret Manager.")

        except Exception as e:
            print(f"ERRO ao carregar secrets do Google Secret Manager: {e}")
            print(
                "Verifique se o SECRET_NAME está correto e se a Conta de Serviço tem permissão 'Secret Manager Secret Accessor'."
            )
            raise e
    else:
        # --- ESTAMOS LOCALMENTE ---
        print("Ambiente local detectado. Carregando do arquivo .env...")
        from dotenv import load_dotenv, find_dotenv

        load_dotenv(find_dotenv())
        print("Variáveis locais carregadas.")
