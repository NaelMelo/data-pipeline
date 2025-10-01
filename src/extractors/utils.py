import time
from functools import wraps
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta
from datetime import timedelta, datetime


def log(msg: str, emoji: str = "\u2139") -> None:
    """Imprime uma mensagem padronizada com emoji no inicio."""
    print(f"{emoji} {msg}")


def medir_tempo(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        inicio = time.time()
        resultado = func(*args, **kwargs)
        fim = time.time()

        tempo_total = fim - inicio
        minutos = int(tempo_total // 60)
        segundos = int(tempo_total % 60)

        print(f"\n🔚 Tempo de execucao de {func.__name__}: {minutos:02d}:{segundos:02d}\n🔚🔚🔚\n\n")
        return resultado

    return wrapper


def gerar_periodos_formatados():
    brasilia_tz = ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(brasilia_tz)
    hoje = agora.date()
    periodos = []
    nomes = {-1: "Mês Passado", 0: "Mês Atual", 1: "Próximo Mês"}

    for i in [-1, 0, 1]:
        data_referencia = hoje + relativedelta(months=i)
        inicio_mes_obj = data_referencia.replace(day=1)
        fim_mes_obj = (inicio_mes_obj + relativedelta(months=1)) - timedelta(days=1)

        periodos.append(
            {
                "nome": nomes[i],
                "inicio": inicio_mes_obj.strftime("%Y-%m-%d"),
                "fim": fim_mes_obj.strftime("%Y-%m-%d"),
                "filename": f"{inicio_mes_obj.strftime('%Y-%m')}",
            }
        )
    return periodos


def download_action(page, element, name):
    with page.expect_download(timeout=1000 * 1800) as download_info:
        page.locator(element).click()
    download = download_info.value
    brasilia_tz = ZoneInfo("America/Sao_Paulo")
    timestamp = datetime.now(brasilia_tz).strftime("%Y%m%d-%H%M%S")
    save_path = f"data/raw/{name}__{timestamp}.csv"
    download.save_as(save_path)
    log(f"Salvo em: {save_path}", "\U0001f4e5")
