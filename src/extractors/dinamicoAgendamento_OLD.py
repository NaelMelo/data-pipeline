from time import sleep
import time
from utils import medir_tempo, log, download_action
import os
from playwright.sync_api import sync_playwright, expect
from dotenv import load_dotenv
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta


load_dotenv(dotenv_path=".env.local")


def gerar_periodos_formatados():
    hoje = date.today()
    periodos = []
    nomes = {-1: "Mês Passado", 0: "Mês Atual", 1: "Próximo Mês"}

    for i in [-1, 0, 1]:
        data_referencia = hoje + relativedelta(months=i)
        inicio_mes_obj = data_referencia.replace(day=1)
        fim_mes_obj = (inicio_mes_obj + relativedelta(months=1)) - timedelta(days=1)

        periodos.append(
            {
                "nome": nomes[i],
                "inicio": inicio_mes_obj.strftime("%d/%m/%Y"),
                "fim": fim_mes_obj.strftime("%d/%m/%Y"),
                "filename": f"dinamicoAgendamento_{inicio_mes_obj.strftime('%Y-%m')}",
            }
        )

    return periodos


@medir_tempo
def run():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(os.getenv("DinamicoAgendamento_url"))
        log(f"Titulo da pagina: {page.title()}", "\U0001f4c4")

        # Realiza login
        log("Realizando login...", "\U0001f510")
        page.locator("#inputUsuario").fill(os.getenv("FASTMEDIC_User"))
        page.locator("#inputSenha").fill(os.getenv("FASTMEDIC_Pass"))

        page.locator('a[onclick="validaLogin()"]').click(force=True)

        # Seleciona: Estabelecimento de Saúde
        log("Selecionando estabelecimento de saude...", "\U0001f3e5")
        page.select_option("#comboEstabelecimento", label="SECRETARIA DA SAUDE DO ESTADO DO CEARA")
        sleep(1)
        page.keyboard.press("Enter")
        page.locator('a[onclick="desbloqueiaAcesso()"]').click(force=True)

        lista_de_periodos = gerar_periodos_formatados()
        for periodo in lista_de_periodos:
            inicio = time.time()
            # Seletor para o campo de data
            campo_data = page.locator('input[id$="_PDAT_INICIAL"]')
            campo_data.press_sequentially(periodo["inicio"])

            campo_data = page.locator('input[id$="_PDAT_FINAL"]')
            campo_data.press_sequentially(periodo["fim"])

            input_field = page.locator('input[id$="_PTIP_DATA"]')
            input_field.click()
            input_field.clear()
            input_field.fill("atendimento")
            option_text = "ATENDIMENTO/CONSULTA"
            page.get_by_text(option_text, exact=True).click()
            print(f'\n📅 Extraindo: "{periodo["nome"]}" ({periodo["inicio"]} a {periodo["fim"]})')
            sleep(5)
            page.locator('span:has-text("Aplicar")').click()
            log("Parametros aplicados.", "\u2705")

            # Espera o CSV ser carregado
            log("Aguardando load 1/4...", "\u23f3")
            page.wait_for_selector("div.loadmask-msg", state="visible", timeout=1000 * 1500)
            log("Aguardando load 2/4...", "\u23f3")
            page.wait_for_selector("div.loadmask-msg", state="hidden", timeout=1000 * 1500)
            log("Aguardando load 3/4...", "\u23f3")
            page.wait_for_selector("div.loadmask-msg", state="visible", timeout=1000 * 1500)
            log("Aguardando load 4/4...", "\u23f3")
            page.wait_for_selector("div.loadmask-msg", state="hidden", timeout=1000 * 1500)

            # Verifica se apareceu o diálogo de alerta ou a grid com os dados primeiro
            timeout = 1800  # segundos para timeout máximo
            poll_interval = 2  # intervalo de verificação
            start_time = time.time()
            name = periodo["filename"]
            while True:

                # Verifica se apareceu a mensagem do diálogo bootstrap
                dialog = page.locator(
                    "div.bootstrap-dialog-message", has_text="O número de linhas excedeu o máximo permitido"
                )
                if dialog.count() > 0 and dialog.is_visible():
                    log("Alerta de linhas excedidas detectado primeiro...", "\u26a0")
                    # Faz o download do CSV
                    page.locator(
                        "div.bootstrap-dialog-message", has_text="O número de linhas excedeu o máximo permitido"
                    ).wait_for(state="visible")
                    download_action(page, 'a.btn:has-text("Sim")', name)
                    break

                # Verifica se apareceu a grid
                grid = page.locator('div[id^="Aba"] .dx-datagrid')
                if grid.count() > 0 and grid.is_visible():
                    log("Grid com dados detectada primeiro...", "\U0001f4ca")
                    log("Aguardando relatorio ser gerado...", "\u23f3")
                    page.wait_for_selector(
                        'div[id^="Aba"] .dx-datagrid', state="visible"
                    )  # espera a grid principal visível
                    page.wait_for_selector(
                        "tr.dx-row.dx-data-row.dx-column-lines", state="visible", timeout=1000 * 1500
                    )

                    # Faz o download do CSV
                    log("Iniciando download do CSV...", "\U0001f4e5")
                    page.locator('div[role="button"][aria-label="fal fa-file-export"]').click()
                    page.locator('.dx-item.dx-radiobutton:has-text("CSV")').click()
                    download_action(page, 'span.dx-button-text:has-text("Exportar")', name)
                    break

                if time.time() - start_time > timeout:
                    log("Nenhum dos elementos apareceu dentro do tempo limite.", "\u23f1")
                    break

                time.sleep(poll_interval)

            fim = time.time()
            tempo_total_segundos = fim - inicio
            minutos = int(tempo_total_segundos // 60)
            segundos = int(tempo_total_segundos % 60)
            print(f"⏱️ Tempo de execução para {periodo['nome']}: {minutos:02d}:{segundos:02d}\n")

            page.get_by_title("Parâmetros").click()

        browser.close()


if __name__ == "__main__":
    run()
