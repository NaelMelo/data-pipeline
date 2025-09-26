from time import sleep
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from utils import medir_tempo, log
import os
from playwright.sync_api import sync_playwright, expect
from dotenv import load_dotenv
import re

load_dotenv(dotenv_path=".env.local")


def download_action(page, element):
    with page.expect_download(timeout=1000 * 1800) as download_info:
        page.locator(element).click()
    download = download_info.value
    brasilia_tz = ZoneInfo("America/Sao_Paulo")
    timestamp = datetime.now(brasilia_tz).strftime("%Y%m%d-%H%M%S")
    save_path = f"data/raw/RELATORIO_{timestamp}.csv"
    download.save_as(save_path)
    log(f"Salvo em: {save_path}", "\U0001f4e5")


@medir_tempo
def run():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(os.getenv("DinamicoFilaEspera_url"))
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

        # Seleciona: Parametros (SITUAÇÃO NA FILA)
        input_field = page.locator('input[id$="_PTIPO"]')
        input_field.click()
        input_field.fill("todas")
        option_text = "Todas as situações de ativos na fila de espera"
        page.get_by_text(option_text, exact=True).click()
        page.locator('span:has-text("Aplicar")').click()
        log("Parametros aplicados.", "\u2705")

        # Espera o CSV ser carregado
        log("Aguardando carregamento aparecer (1)...", "\u23f3")
        page.wait_for_selector("div.loadmask-msg", state="visible", timeout=1000 * 1500)
        log("Aguardando carregamento desaparecer (1)...", "\u23f3")
        page.wait_for_selector("div.loadmask-msg", state="hidden", timeout=1000 * 1500)
        log("Aguardando carregamento aparecer (2)...", "\u23f3")
        page.wait_for_selector("div.loadmask-msg", state="visible", timeout=1000 * 1500)
        log("Aguardando carregamento desaparecer (2)...", "\u23f3")
        page.wait_for_selector("div.loadmask-msg", state="hidden", timeout=1000 * 1500)

        # Verifica se apareceu o diálogo de alerta ou a grid com os dados primeiro
        timeout = 1800  # segundos para timeout máximo
        poll_interval = 2  # intervalo de verificação
        start_time = time.time()
        while True:

            # Verifica se apareceu a mensagem do diálogo bootstrap
            dialog = page.locator(
                "div.bootstrap-dialog-message", has_text="O número de linhas excedeu o máximo permitido"
            )
            if dialog.count() > 0 and dialog.is_visible():
                log("Alerta de linhas excedidas detectado primeiro...", "⚠️")  # ⚠️\u26a0
                # Faz o download do CSV
                page.locator(
                    "div.bootstrap-dialog-message", has_text="O número de linhas excedeu o máximo permitido"
                ).wait_for(state="visible")
                download_action(page, 'a.btn:has-text("Sim")')
                break

            # Verifica se apareceu a grid
            grid = page.locator('div[id^="Aba"] .dx-datagrid')
            if grid.count() > 0 and grid.is_visible():
                log("Grid com dados detectada primeiro...", "\U0001f4ca")
                log("Aguardando relatorio ser gerado...", "\u23f3")
                page.wait_for_selector(
                    'div[id^="Aba"] .dx-datagrid', state="visible"
                )  # espera a grid principal visível
                page.wait_for_selector("tr.dx-row.dx-data-row.dx-column-lines", state="visible")

                # Faz o download do CSV
                log("Iniciando download do CSV...", "\U0001f4e5")
                page.locator('div[role="button"][aria-label="fal fa-file-export"]').click()
                page.locator('.dx-item.dx-radiobutton:has-text("CSV")').click()
                download_action(page, 'span.dx-button-text:has-text("Exportar")')
                break

            if time.time() - start_time > timeout:
                log("Nenhum dos elementos apareceu dentro do tempo limite.", "\u23f1")
                break

            time.sleep(poll_interval)

        browser.close()


if __name__ == "__main__":
    run()
