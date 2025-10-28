import time
from functools import wraps
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta
from datetime import timedelta, datetime
import pandas as pd
import re
from unidecode import unidecode


def now_fortaleza(format_string: str | None = None) -> str | datetime:
    try:
        now_utc = datetime.now(ZoneInfo("UTC"))
        dt_fortaleza_aware = now_utc.astimezone(ZoneInfo("America/Fortaleza"))

        if format_string is None:
            return dt_fortaleza_aware.replace(tzinfo=None)

        return dt_fortaleza_aware.strftime(format_string)

    except ValueError as e:
        print(f"Erro: String de formatação inválida: '{format_string}'. Detalhe: {e}")
        return ""


def medir_tempo(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        inicio = time.time()
        resultado = func(*args, **kwargs)
        fim = time.time()

        tempo_total = fim - inicio
        minutos = int(tempo_total // 60)
        segundos = int(tempo_total % 60)

        print(f"◽\n🔚 Tempo de execucao de {func.__name__}: {minutos:02d}:{segundos:02d}\n🔚🔚🔚\n\n")
        return resultado

    return wrapper


def gerar_periodos_formatados():
    hoje = now_fortaleza().date()
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


if __name__ == "__main__":
    print(now_fortaleza())

    print(datetime.now())
