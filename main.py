from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from opera_db import carrega_pedidos_nao_contatados, is_pedido_lido, insere_venda, set_pedido_chamado
from opera_wpp import envia_msg
import time, re, datetime as dt

profile = 'Profile 2'#Irene
profile = 'Profile 7'#Mineiro
profile = 'Default'#Jaque

options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument("user-data-dir=C:/Users/Felipe/AppData/Local/Google/Chrome/User Data")
options.add_argument(f'profile-directory={profile}')

driver = webdriver.Chrome(options=options)
continuar = True

while continuar:
    
    #LER PEDIDOS NO IDERIS E CARREGAR NAS VARIÁVEIS
    if driver.current_url.count('app3.ideris.com.br/Views/Pedido/Painel') == 0:
        driver.switch_to.window(driver.window_handles[0])
    driver.get(f'https://app3.ideris.com.br/Views/Pedido/Painel.aspx')
    
    lista_pedido_html = driver.find_elements(By.CSS_SELECTOR, 'table.table.table-master')
    lista_num_pedido = []
    for pedido_html in lista_pedido_html:
        n_pedido = pedido_html.find_element(By.CSS_SELECTOR, 'fieldset > div > span.itxt-info > span').text
        if len(pedido_html.find_elements(By.CSS_SELECTOR, 'span.label.label-warning')) > 0 and \
            pedido_html.find_element(By.CSS_SELECTOR, 'tr.tr-header').get_attribute('style').count('display: none') == 0:
            if not is_pedido_lido(n_pedido):
                lista_num_pedido.append(n_pedido)


    list_vendas = list()
    for num_pedido in lista_num_pedido:
        driver.get(f'https://app3.ideris.com.br/Views/Mensagem/DetalhesPedido.aspx?pedido={num_pedido}')
        nome = driver.find_element(By.ID, 'ContentPlaceHolder2_lblComprador').text
        
        html_contem_cpf = driver.find_element(By.CSS_SELECTOR, 'div.depd-container-infos-scroll > div:nth-child(3)').text
        procura_cpf_cnpj = re.search(r'[0-9]{14}', html_contem_cpf)
        if procura_cpf_cnpj is None:
            procura_cpf_cnpj = re.search(r'[0-9]{11}', html_contem_cpf)
        cpf_cnpj = html_contem_cpf[procura_cpf_cnpj.span()[0]:procura_cpf_cnpj.span()[1]]

        dict_venda = dict(nome=nome,documento=cpf_cnpj,num_pedido=num_pedido)
        print('Nome:', nome, 'CPF:', cpf_cnpj)

        list_venda_item = list()
        produtos_html = driver.find_elements(By.CSS_SELECTOR, 'div.depd-container-img-prod-text-in.depd-img-produto-texto')
        for produto_html in produtos_html:
            nome_produto = produto_html.find_element(By.TAG_NAME, 'a').text
            qtd_produto = produto_html.find_element(By.CSS_SELECTOR, 'span:nth-child(4)').text
            variacao_produto = produto_html.find_element(By.CSS_SELECTOR, 'span:nth-child(10)').text
            print(nome_produto, ' - ', variacao_produto)
            list_venda_item.append((nome_produto, qtd_produto,variacao_produto))

        dict_venda['itens'] = list_venda_item
        list_vendas.append(dict_venda)


    #LER OS TELEFONES (ASSERTIVA)
    if len(list_vendas) > 0:
        logou_assert = False

        while not logou_assert:
            driver.get('https://painel.assertivasolucoes.com.br/login')
            if len(driver.find_elements(By.ID, 'password')) > 0:
                if driver.find_element(By.ID, 'email').text != '':
                    driver.find_element(By.ID, 'email').send_keys('taticalmilitaria1@hotmail.com')
                    driver.find_element(By.ID, 'password').send_keys('Tatical0105.')
                    time.sleep(1)
                driver.find_element(By.ID, 'btn-entrar').click()
                time.sleep(5)
            else:
                logou_assert = True
        

    for dict_venda in list_vendas:
        
        if len(dict_venda['documento']) == 14:
            url = f'https://localize.assertivasolucoes.com.br/consulta/cnpj'
        else:
            url = f'https://localize.assertivasolucoes.com.br/consulta/cpf'
        
        driver.get(url)

        contador_recarregar = 0
        while len(driver.find_elements(By.ID, 'btn-consultar-doc')) == 0:
            time.sleep(0.1)
            contador_recarregar += 1
            if contador_recarregar > 100:
                print('recarregando', url)
                driver.get(url)
                contador_recarregar = 0
        
        if len(driver.find_elements(By.CSS_SELECTOR, '#btn-finalidade-de-uso')) > 0:
            if driver.find_element(By.CSS_SELECTOR, '#btn-finalidade-de-uso').text != 'Confirmação de identidade':
                driver.find_element(By.CSS_SELECTOR, '#btn-finalidade-de-uso').click()
                time.sleep(1)
                driver.find_element(By.CSS_SELECTOR, '#option-finalidade-de-uso-0').click()
        driver.find_element(By.CSS_SELECTOR, '#lc-drop-filter > div:nth-child(1) > div > div > div:nth-child(3) > form > div > div > input')\
        .send_keys(dict_venda['documento'])
        time.sleep(0.3)
        driver.find_element(By.ID, 'btn-consultar-doc').click()
        
        contador_espera = 0
        while len(driver.find_elements(By.ID, '#telefones')) == 0 and \
            len(driver.find_elements(By.CSS_SELECTOR, '#lc-drop-filter > div:nth-child(1) > div > div > div:nth-child(3) > form > div:nth-child(2) > span')) ==0:
            time.sleep(0.1)
            contador_espera += 1
            if contador_espera > 100:
                break
        
        if len(driver.find_elements(By.CSS_SELECTOR, 'div.MuiGrid-root.MuiGrid-container.MuiGrid-item.MuiGrid-direction-xs-column.MuiGrid-align-items-xs-center > h6')) > 0 and \
           driver.find_element(By.CSS_SELECTOR, 'div.MuiGrid-root.MuiGrid-container.MuiGrid-item.MuiGrid-direction-xs-column.MuiGrid-align-items-xs-center > h6').text.upper().count('NÃO LOCALIZAMOS NENHUM TELEFONE') > 0:
            driver.find_element(By.ID,'btn-mais-telefones').click()
            time.sleep(2)

        list_telefones = list()
        for telefone_html in driver.find_elements(By.CSS_SELECTOR,'h5'):
            if len(telefone_html.text) > 1 and len(telefone_html.text) < 16:
                print(telefone_html.text)
                list_telefones.append(telefone_html.text)
        dict_venda['telefones'] = list_telefones

    #INSERIR TUDO NO BANCO DE DADOS
    for dict_venda in list_vendas:
        insere_venda(dict_venda['num_pedido'], dict_venda['nome'], dict_venda['documento'], dict_venda['itens'], dict_venda['telefones'])

    #LÊ TUDO DO BANCO DE DADOS E ENVIA AS MSGS - DE SEG A QUINTA DAS 8 AS 15. SEXTA DAS 8 AS 13
    list_vendas_x = carrega_pedidos_nao_contatados()

    for dict_venda in list_vendas_x:
        if len(dict_venda['telefones']) == 0:
            print(dict_venda['comprador'], 'Não tem telefone')
            set_pedido_chamado(dict_venda['id'], 2)
            continue
        
        msg_list = list()
        msg_list.append(('Hope!:salute', Keys.ENTER))
        msg_list.append('')
        msg_list.append(f'*{dict_venda["comprador"]}?*')
        msg_list.append('Felipe da Tatical Militaria, tudo bem guerreiro(a)?')
        msgProdutos : str = 'Recebi seu pedido via mercado livre:'
        for i,item in enumerate(dict_venda['itens']):
            if i > 0:
                msgProdutos += ' e '
            if len(item[2]) > 0:
                msgProdutos += '*'+str(item[1])+'x '+item[0]+' '+str(item[2]).replace('Variação: ','')+'*'
            else:
                msgProdutos += '*'+str(item[1])+'x '+item[0]+'*'
        
        msg_list.append(msgProdutos)
        msg_list.append('Confere?')
        msg_list.append('')
        msg_list.append('Caso você não seja a pessoa indicada acima desculpe o incômodo e desconsidere essa mensagem')
        msg_list.append((':mãos juntas', Keys.ENTER))

        if int(time.strftime('%H')) < 8 or int(time.strftime('%H')) >= 15 or dt.date.today().weekday() in (5,6):
            msg_list.append('')
            msg_list.append((
                    'No momento estou passando somente para agradecer e confirmar a sua compra. Entrarei em contato por aqui novamente assim que possível para um melhor atendimento. Qualquer dúvida, estarei a disposição assim que retornar! (Nosso horário de atendimento é de segunda à sexta das 9:00 às 15:00). Tenha um ótimo e abençoado dia! :mãos juntas', Keys.ENTER
            ))

        sem_wpp = True
        for telefone in dict_venda['telefones']:
            try:
                envia_msg(driver, telefone, msg_list)
                set_pedido_chamado(dict_venda['id'])
                sem_wpp = False
            except Exception as err:
                print('Erro:', dict_venda["comprador"], '-',telefone,'-',err)
        if sem_wpp:
            set_pedido_chamado(dict_venda['id'], 3)
        
    time.sleep(300)
