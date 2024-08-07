from selenium import webdriver
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options # type: ignore
from selenium.webdriver.common.by import By
import datetime, time as t, requests, json, os
from datetime import timedelta
from navegador import fechar_tudo_zord, get_element_by_text, click
from requests.auth import HTTPBasicAuth

def consulta_movimento_estoque(driver: ChromiumDriver):
    url = 'https://taticalmilitaria.painel.magazord.com.br/api/v1/listEstoque'
    username = os.environ['token_api_zord'] 
    password = os.environ['senha_api_zord'] 

    limit = 100
    offset = 0
    list_produtos = []
    total = 999999
    dataHoraNow = datetime.datetime.now() - timedelta(hours=0, minutes=1)
    dataHoraNow = dataHoraNow.strftime('%Y-%m-%dT%H:%M:%S-03:00')
    with open('ultima_consulta_estoque.txt', 'r') as file:
        dataHoraAtualizacaoInicial = file.readline()

    while offset < total:
        response = requests.get(url, auth=HTTPBasicAuth(username, password), params={
            'dataHoraAtualizacaoInicial' : dataHoraAtualizacaoInicial,
            'offset' : offset,
            'limit' : limit
        })

        # Verifica se a resposta foi bem-sucedida
        if response.status_code == 200:
            # Converte a resposta JSON em um dicionário Python, se a resposta for JSON
            try:
                data = response.json()
                total = data['total']

                list_produtos = list_produtos + data['data']

            except ValueError:
                # Caso a resposta não seja um JSON, exibe o conteúdo da resposta
                print(response.text)
        else:
            print(f"Erro na requisição: {response.status_code}")
            print(response.text)
        
        offset = offset + limit

    for produto in list_produtos:
        nivelar_estoque(driver, produto['produto'], produto['quantidadeDisponivelVenda'])

    with open('ultima_consulta_estoque.txt', 'w') as file:
        file.write(dataHoraNow)

def nivelar_estoque(driver: ChromiumDriver, sku, quantidade):

    abre_aba_mt(driver)
    if driver.current_url.count('https://app.mercadoturbo.com.br/sistema/anuncio/anuncios') == 0:
        driver.get('https://app.mercadoturbo.com.br/sistema/anuncio/anuncios')
        t.sleep(5)
        driver.find_element(By.XPATH, "//*[text()='Nivelar Estoque']").click()
        t.sleep(2)

    driver.find_element(By.CSS_SELECTOR, '#form-nivelar-estoque input[type="integer"]').send_keys(quantidade)
    driver.find_element(By.CSS_SELECTOR, '#form-nivelar-estoque input[type="text"]').send_keys(sku)

    #Checkbox para aplicar em todas as contas
    driver.find_elements(By.CSS_SELECTOR, "#form-nivelar-estoque .ui-selectbooleancheckbox.ui-chkbox")[1].click()

    #Botão de confirmar
    driver.find_elements(By.CSS_SELECTOR, "#form-nivelar-estoque button")[1].click()
    t.sleep(1)
    driver.find_element(By.CSS_SELECTOR, '.ui-button.ui-confirmdialog-yes.mt-button-success').click()
    t.sleep(1)

    while driver.find_element(By.CSS_SELECTOR, '.dialog-aguarde').get_attribute('aria-modal') == 'true':
        t.sleep(1)


def get_descricao_by_sku(sku):
    url = f'https://taticalmilitaria.painel.magazord.com.br/api/v2/site/produtoDerivacoes'
    username = os.environ['token_api_zord'] 
    password = os.environ['senha_api_zord'] 

    response = requests.get(url, auth=HTTPBasicAuth(username, password), params={'codigo' : sku})

    if response.status_code in (200,201):
        return response.json()['data']['items'][0]['nomeCompleto']
    else:
        print(f"Erro na requisição em get_descricao_by_sku: {response.status_code}")
        print(response.text)



def verifica_mercado_turbo(driver: ChromiumDriver):
    consulta_movimento_estoque(driver)

    contas = ['BAKESHOP23', 'INKALION']

    abre_aba_mt(driver)
    driver.get('https://app.mercadoturbo.com.br/sistema/venda/vendas_ml')
    t.sleep(2)

    conta_selecionada = driver.find_element(By.CSS_SELECTOR, 'li > form > div[role="combobox"] >  label').text
    contas.remove(conta_selecionada)
    contas.insert(0, conta_selecionada)

    list_vendas_chamar_wpp = []
    vendas_baixar_list = []
    for conta in contas:
        if conta_selecionada != conta:
            driver.find_element(By.CSS_SELECTOR, 'li form div.ui-selectonemenu-trigger > span').click()
            t.sleep(1)
            get_element_by_text(driver, conta, texto_exato=False, tipo_tag='li').click()
            t.sleep(12)

        for venda in driver.find_elements(By.CSS_SELECTOR, 'td.HeaderTextAlignLeft.CursorDefault.ColunaItemsVendas'):
            num_venda = venda.find_element(By.CSS_SELECTOR, 'div.p-d-flex.p-ai-center > a > span:nth-child(2)').text
            qtdd = venda.find_element(By.CSS_SELECTOR, 'div.Fs20').text.replace('x', '')
            sku = venda.find_element(By.CSS_SELECTOR, 'span.p-ml-1').text
            nome_produto = get_descricao_by_sku(sku) #venda.find_element(By.CSS_SELECTOR, '.p-ml-1 .p-text-bold.p-d-inline').text
            is_cancelamento = len(venda.find_elements(By.CSS_SELECTOR, 'div.Red')) > 0

            with open('controle_estoque.txt', 'r') as file:
                file_content = file.read()
                
                compare = '|'.join([num_venda, sku,qtdd,'1' if not is_cancelamento else '2'])
                                    
                if file_content.count(compare) == 0:
                    vendas_baixar_list.append({'num_venda' : num_venda ,'sku' : sku, 'qtdd' : qtdd, 'status' : '1' if not is_cancelamento else '2', "conta" : conta})
                    print('Baixar no zord: ', compare)
                else:
                    continue
            
            if not is_cancelamento:
                import re

                cpf_pattern = r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b'
                cnpj_pattern = r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b'
                combined_pattern = re.compile(f'({cpf_pattern})|({cnpj_pattern})')
                
                venda.find_element(By.CSS_SELECTOR, 'i.fa-info-circle').click()
                t.sleep(3)

                nome = driver.find_element(By.ID, 'dialog-nome-comprador').text
                info = driver.find_element(By.ID, 'dialog-perfil-comprador').text
                documento = combined_pattern.search(info).group().replace('.', '').replace('-', '').replace('/', '')

                driver.find_element(By.CSS_SELECTOR, '#dialog-perfil-comprador .ui-icon-closethick').click()

                item = [(nome_produto, qtdd, sku)]
                for venda_i in list_vendas_chamar_wpp:
                    if venda_i['documento'] == documento:
                        venda_i['itens'].extend(item)
                        break
                else:
                    list_vendas_chamar_wpp.append(dict(nome=nome, documento=documento, num_pedido=num_venda, itens=item))
            

    if len(vendas_baixar_list) > 0:
        import time
        for i, venda in enumerate(vendas_baixar_list):
            
            obs = ('' if venda['status'] == '1' else 'Cancelamento da ') + \
                "Venda ML Referência: " + venda['num_venda'] + ". Conta: " + venda['conta']

            url = 'https://taticalmilitaria.painel.magazord.com.br/api/v1/estoque'
            username, password = '0ca30e8f60766b2a7ba000c3eff3bd3304579218a8e18006379d446d7080b7e3', '&Bwg9MbM3'

            playload=\
                {
                    "produto": venda['sku'],
                    "deposito": 1,
                    "quantidade": int(venda['qtdd']),
                    "tipo": 1,#Físico
                    "tipoOperacao": 2 if venda['status'] == '1' else 1,
                    "origemMovimento": 8 if venda['status'] == '1' else 1,
                    "observacao": obs,
                }


            response = requests.post(url, auth=HTTPBasicAuth(username, password), json=playload)

            # Verifica se a resposta foi bem-sucedida
            if response.status_code == 200:
                # Converte a resposta JSON em um dicionário Python, se a resposta for JSON
                print('Sucesso ao movimentar estoque:' + json.dumps(playload))
                with open('controle_estoque.txt', 'a') as file:
                    file.write(';')
                    file.write('|'.join([venda['num_venda'], venda['sku'], venda['qtdd'], venda['status']]))
            else:
                print(f"Erro na requisição: {response.status_code}")
                print(response.text)
                print(json.dumps(playload))
                
    return list_vendas_chamar_wpp

def abre_aba_mt(driver : ChromiumDriver):
    if driver.current_url.count('https://app.mercadoturbo.com.br') == 0:
        abrir_nova = True
        for window_handle in driver.window_handles:
            driver.switch_to.window(window_handle)
            if driver.current_url.count('https://app.mercadoturbo.com.br') > 0:
                abrir_nova = False
                break

        if abrir_nova:
            driver.execute_script("window.open('https://app.mercadoturbo.com.br/sistema/venda/vendas_ml');")
            driver.switch_to.window(driver.window_handles[-1])