import time
from functools import wraps
from datetime import datetime
from zoneinfo import ZoneInfo


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


def download_action(page, element, name):
    with page.expect_download(timeout=1000 * 1800) as download_info:
        page.locator(element).click()
    download = download_info.value
    brasilia_tz = ZoneInfo("America/Sao_Paulo")
    timestamp = datetime.now(brasilia_tz).strftime("%Y%m%d-%H%M%S")
    save_path = f"data/raw/{name}__{timestamp}.csv"
    download.save_as(save_path)
    log(f"Salvo em: {save_path}", "\U0001f4e5")
