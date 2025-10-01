import time
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta, datetime
from captureSession import capture_session
from downloadCsv import download_csv
from dotenv import load_dotenv
import json
import os
from utils import medir_tempo
from zoneinfo import ZoneInfo

load_dotenv(dotenv_path=".env.local")


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


@medir_tempo
def dinamicoAgendamento():
    print("🏁🏁🏁\n🏁 Iniciando extração do relatorio: DinamicoAgendamento")

    lista_de_periodos = gerar_periodos_formatados()

    for periodo in lista_de_periodos:
        inicio = time.time()
        print(f'\n📅 Extraindo: "{periodo["nome"]}" ({periodo["inicio"]} a {periodo["fim"]})')

        payload_raw = os.getenv("DinamicoAgendamento_payload")
        payload_str = payload_raw.replace("startDate", periodo["inicio"]).replace("endDate", periodo["fim"])
        payload = json.loads(payload_str)
        jsonCompleto = capture_session(payload)
        print("🔗 Link do JSON Completo:", jsonCompleto)

        nomeRelatorio = periodo["filename"]
        download_csv(jsonCompleto, nomeRelatorio)

        fim = time.time()
        tempo_total_minutos = (fim - inicio) / 60
        print(f'⏰ Tempo para extrair "{periodo["nome"]}": {tempo_total_minutos:.2f} minutos.')


if __name__ == "__main__":
    dinamicoAgendamento()
