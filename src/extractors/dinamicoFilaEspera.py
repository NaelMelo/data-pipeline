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
        start = time.time()
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(os.getenv("FASTMEDIC_URL_DinamicoFilaEspera"))
        print(f"\nPage title: {page.title()}")

        # Realiza login
        print("Realizando login...")
        page.locator("#inputUsuario").fill(os.getenv("FASTMEDIC_User"))
        page.locator("#inputSenha").fill(os.getenv("FASTMEDIC_Pass"))

        page.locator('a[onclick="validaLogin()"]').click(force=True)

        # Seleciona: Estabelecimento de Saúde
        print("Selecionando estabelecimento de saúde...")
        page.select_option("#comboEstabelecimento", label="SECRETARIA DA SAUDE DO ESTADO DO CEARA")
        sleep(1)
        page.keyboard.press("Enter")
        # page.locator(".dx-texteditor-input").press("Tab")  # sai do campo
        page.locator('a[onclick="desbloqueiaAcesso()"]').click(force=True)

        # Seleciona: Parametros (SITUAÇÃO NA FILA)
        # Escopa o SelectBox certo (PTIPO)

        texto_da_opcao = "Todas as situações de ativos na fila de espera"

        # 1. Encontre o container do seletor usando o atributo 'name' do input
        #    e clique nele para abrir as opções.
        seletor_container = page.locator('div.dx-selectbox:has(input[name="PTIPO"])')
        seletor_container.click()

        # 2. Com as opções visíveis, localize a opção desejada pelo texto e clique nela.
        #    O Playwright espera automaticamente o elemento aparecer.
        page.get_by_text(texto_da_opcao, exact=True).click()

        # 3. (Opcional, mas recomendado) Verifique se a seleção foi bem-sucedida.
        #    O próprio container do seletor agora deve conter o texto da opção selecionada.
        expect(seletor_container).to_contain_text(texto_da_opcao)
        """
        typeReport = "Todas as situações de ativos na fila de espera"

        # SelectBox do PTIPO
        selectbox = page.locator(".dx-selectbox-container").filter(
            has=page.locator('input[type="hidden"][name="PTIPO"]')
        )
        input_ptipo = selectbox.locator(".dx-texteditor-input")

        # Abre e imediatamente mira no overlay atual
        input_ptipo.click()

        selectbox.locator(".dx-dropdowneditor-button").click()

        overlay = page.locator(".dx-overlay-wrapper:has(.dx-list)").first
        item = overlay.locator(f'.dx-list-item:has(.custom-item:has-text("{typeReport}"))').first

        # Aguarda o item ficar clicável e clica logo
        expect(item).to_be_visible(timeout=5000)
        item.click()

        # Commit (Enter/Tab) e valida hidden
        page.keyboard.press("Enter")
        page.keyboard.press("Tab")
        ptipo = selectbox.locator('input[name="PTIPO"]')
        expect(ptipo).to_have_attribute("value", "12", timeout=30000)
        print("Opção selecionada corretamente.")
        """
        page.locator('span:has-text("Aplicar")').click()
        print("Parâmetros aplicados.")

        print("esperando load aparecer1...")
        page.wait_for_selector("div.loadmask-msg", state="visible", timeout=1000000)
        print("esperando load desaparecer1...")
        page.wait_for_selector("div.loadmask-msg", state="hidden", timeout=60000000)

        print("esperando load aparecer2...")
        page.wait_for_selector("div.loadmask-msg", state="visible", timeout=1000000)
        print("esperando load desaparecer2...")
        page.wait_for_selector("div.loadmask-msg", state="hidden", timeout=60000000)

        timeout = 1800  # segundos para timeout máximo
        poll_interval = 1  # intervalo de verificação

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

        # sleep(40)
        browser.close()

        """
        end = time.time()
        totalTime = end - start
        seconds = int(totalTime % 60)
        minutes = int(totalTime // 60)
        print(f"Tempo de execução: {minutes:02d}:{seconds:02d}\n")
        """


if __name__ == "__main__":
    run()
