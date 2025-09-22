from time import sleep
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from utils import medir_tempo
import os
from playwright.sync_api import sync_playwright, expect
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")


def download_action(page, element):
    with page.expect_download(timeout=1000 * 1800) as download_info:
        page.locator(element).click()
    download = download_info.value
    brasilia_tz = ZoneInfo("America/Sao_Paulo")
    timestamp = datetime.now(brasilia_tz).strftime("%Y%m%d-%H%M%S")
    save_path = f"data/RELATORIO_{timestamp}.csv"
    download.save_as(save_path)
    print(f"File downloaded to: {save_path}\n")


@medir_tempo
def run():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(os.getenv("FASTMEDIC_URL_DinamicoFilaEspera"))
        print(f"\nPage title: {page.title()}")

        ## Realiza login
        print("Realizando login...")
        page.locator("#inputUsuario").fill(os.getenv("FASTMEDIC_User"))
        page.locator("#inputSenha").fill(os.getenv("FASTMEDIC_Pass"))

        page.locator('a[onclick="validaLogin()"]').click(force=True)

        ## Seleciona: Estabelecimento de Saúde
        print("Selecionando estabelecimento de saúde...")
        page.select_option("#comboEstabelecimento", label="SECRETARIA DA SAUDE DO ESTADO DO CEARA")
        sleep(1)
        page.keyboard.press("Enter")
        page.locator('a[onclick="desbloqueiaAcesso()"]').click(force=True)

        ## Seleciona: Parametros (SITUAÇÃO NA FILA)
        texto_da_opcao = "Todas as situações de ativos na fila de espera"
        seletor_container = page.locator('div.dx-selectbox:has(input[name="PTIPO"])')
        seletor_container.click()
        sleep(1)
        page.get_by_text(texto_da_opcao, exact=False).click()
        print(f'Opção "{texto_da_opcao}" selecionada.')
        expect(seletor_container).to_contain_text(texto_da_opcao)
        page.locator('span:has-text("Aplicar")').click()
        print("Parâmetros aplicados.")

        ## Espera o CSV ser carregado
        print("esperando load aparecer1...")
        page.wait_for_selector("div.loadmask-msg", state="visible", timeout=1000 * 1500)
        print("esperando load desaparecer1...")
        page.wait_for_selector("div.loadmask-msg", state="hidden", timeout=1000 * 1500)
        print("esperando load aparecer2...")
        page.wait_for_selector("div.loadmask-msg", state="visible", timeout=1000 * 1500)
        print("esperando load desaparecer2...")
        page.wait_for_selector("div.loadmask-msg", state="hidden", timeout=1000 * 1500)

        ## Verifica se apareceu o diálogo de alerta ou a grid com os dados primeiro
        timeout = 1800  # segundos para timeout máximo
        poll_interval = 2  # intervalo de verificação
        start_time = time.time()
        while True:
            # Verifica se apareceu a mensagem do diálogo bootstrap
            dialog = page.locator(
                "div.bootstrap-dialog-message", has_text="O número de linhas excedeu o máximo permitido"
            )
            if dialog.count() > 0 and dialog.is_visible():
                print("Alerta de linhas excedidas apareceu primeiro...")
                # Faz o download do CSV
                page.locator(
                    "div.bootstrap-dialog-message", has_text="O número de linhas excedeu o máximo permitido"
                ).wait_for(state="visible")
                download_action(page, 'a.btn:has-text("Sim")')
                break

            # Verifica se apareceu a grid
            grid = page.locator('div[id^="Aba"] .dx-datagrid')
            if grid.count() > 0 and grid.is_visible():
                print("Grid com dados apareceu primeiro...")
                print("Aguardando relatório ser gerado...")
                page.wait_for_selector(
                    'div[id^="Aba"] .dx-datagrid', state="visible"
                )  # espera a grid principal visível
                page.wait_for_selector("tr.dx-row.dx-data-row.dx-column-lines", state="visible")  # espera linha visível

                # Faz o download do CSV
                print("Iniciando download do CSV...")
                page.locator('div[role="button"][aria-label="fal fa-file-export"]').click()
                page.locator('.dx-item.dx-radiobutton:has-text("CSV")').click()
                download_action(page, 'span.dx-button-text:has-text("Exportar")')
                break

            if time.time() - start_time > timeout:
                print("Nenhum dos elementos apareceu dentro do timeout")
                break

            time.sleep(poll_interval)

        browser.close()


if __name__ == "__main__":
    run()
