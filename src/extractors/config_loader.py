import os
import io
from dotenv import load_dotenv, dotenv_values
from google.cloud import secretmanager
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule

console = Console()

SECRET_NAME = "Fast_Medic"

stamp_load_loader = 1


def setup_environment():
    """
    Carrega as variáveis de ambiente com formatação Rich.
    - Se rodando no Google Cloud (ex: Colab Enterprise), busca do Secret Manager.
    - Se rodando localmente, busca de um arquivo .env.
    """

    # Evita rodar múltiplas vezes
    global stamp_load_loader
    if stamp_load_loader > 1:
        return
    stamp_load_loader += 1

    # Objeto de Texto para construir o conteúdo do painel
    setup_text = Text()

    # Verifica se está rodando no Google Cloud
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    if project_id:
        # --- ESTAMOS NO COLAB ENTERPRISE ---
        setup_text.append("☁️  ", style="dark_green")
        setup_text.append("Ambiente Google Cloud detectado.\n", style="dark_green")
        setup_text.append("🔑  ", style="dark_green")
        setup_text.append(f"Carregando secrets de [bold]{SECRET_NAME}[/bold]...", style="dark_green")

        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{SECRET_NAME}/versions/latest"

            response = client.access_secret_version(request={"name": name})
            payload_str = response.payload.data.decode("UTF-8")

            env_data = dotenv_values(stream=io.StringIO(payload_str))

            for key, value in env_data.items():
                if key not in os.environ:
                    os.environ[key] = value

            # --- Mensagem de Sucesso ---
            setup_text.append(f"\n✅  ", style="bold green")
            setup_text.append(f"Sucesso: {len(env_data)} variáveis carregadas do Secret Manager.", style="bold green")

            # --- Imprime o Painel de Sucesso ---
            console.print(
                Panel(
                    setup_text,
                    title="[bold]CONFIGURAÇÃO DE AMBIENTE[/bold]",
                    title_align="left",
                    border_style="dark_orange",
                )
            )

        except Exception as e:
            # --- Painel de Erro ---
            error_text = Text()
            error_text.append("Falha ao carregar secrets do Google Secret Manager.\n\n", style="red")
            error_text.append(f"Erro: [bold]{e}[/bold]\n\n", style="white")
            error_text.append("Verifique o SECRET_NAME e as permissões da Conta de Serviço.", style="yellow")

            console.print(Panel(error_text, title="[bold red]FALHA NA CONFIGURAÇÃO[/bold red]", border_style="red"))
            raise e
    else:
        # --- ESTAMOS LOCALMENTE ---
        from dotenv import find_dotenv  # Importa só se for usar

        setup_text.append("🏠  ", style="dark_green")
        setup_text.append("Ambiente local detectado.\n", style="dark_green")
        setup_text.append("📄  ", style="dark_green")
        setup_text.append("Carregando do arquivo .env...", style="dark_green")

        loaded = load_dotenv(find_dotenv())

        if loaded:
            setup_text.append(f"\n✅  ", style="bold green")
            setup_text.append("Variáveis locais carregadas do .env.", style="bold green")
        else:
            setup_text.append(f"\n⚠️  ", style="bold yellow")
            setup_text.append(
                "Nenhum arquivo .env encontrado. Usando vars de ambiente existentes.", style="bold yellow"
            )

        # --- Imprime o Painel de Sucesso Local ---
        console.print(
            Panel(
                setup_text,
                title="[bold]CONFIGURAÇÃO DE AMBIENTE[/bold]",
                title_align="left",
                border_style="dark_orange",
            )
        )

    console.print(Rule(style="dark_orange"))
