from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from opera_db import carrega_pedidos_nao_contatados, is_pedido_lido, insere_venda, set_pedido_chamado
from opera_wpp import envia_msg
import time, re, datetime as dt
import tkinter as tk
#import tkinter.messagebox as msgbox
import pyautogui, pymsgbox, winsound

def carregar_pagina_pedidos(driver):
    if driver.current_url.count('https://web.ideris.com.br/pedido/pesquisa') == 0:
        driver.switch_to.window(driver.window_handles[0])
    driver.get(f'https://web.ideris.com.br/pedido/pesquisa')
    time.sleep(3)
    
profile = 'Profile 2'#Irene
profile = 'Profile 7'#Mineiro
profile = 'Default'#Jaque

options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument("user-data-dir=C:/Users/Felipe/AppData/Local/Google/Chrome/User Data")
options.add_argument(f'profile-directory={profile}')

driver = webdriver.Chrome(options=options)
rodando = True

driver.get('https://taticalmilitaria.painel.magazord.com.br')
#time.sleep(2)
#if len(driver.find_elements(By.ID, 'email')) > 0:
time.sleep(30)

while rodando:
    try:
        #Atualizar pedidos
        driver.find_element(By.XPATH, "//*[text()='Atualizar']").click()

        list_vendas = list()
        for tr in driver.find_elements(By.CSS_SELECTOR, 'tr.x-grid-row'):
            num_pedido = tr.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            if is_pedido_lido(num_pedido):
                continue
            chechbox = tr.find_element(By.CSS_SELECTOR, 'td:nth-child(3)')
            chechbox.click()
            driver.find_element(By.XPATH, "//*[text()='Visualizar']").click()
            time.sleep(2)

            #Dentro da página do pedido
            nome = driver.find_elements(By.XPATH, "//*[text()='Cliente']//..//..//..")[-1].text

            text_pagina = driver.find_element(By.CSS_SELECTOR, 'body').text
            re_cpf_cnpj = re.search(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', text_pagina)
            if not re_cpf_cnpj:
                re_cpf_cnpj = re.search(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b', text_pagina)
            cpf_cnpj = re_cpf_cnpj.group()
            
            dict_venda = dict(nome=nome,documento=cpf_cnpj,num_pedido=num_pedido)
            print('Nome:', nome, 'CPF:', cpf_cnpj)
            ######


            list_venda_item = list()
            for produto_html in driver.find_elements(By.CSS_SELECTOR, '.swiper-slide-active'):
                nome_produto = produto_html.find_element(By.CSS_SELECTOR, '.nomeProduto').text
                qtd_produto  = produto_html.find_element(By.CSS_SELECTOR, '.itemValue').text

                list_venda_item.append((nome_produto, qtd_produto,''))

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
            while len(driver.find_elements(By.CSS_SELECTOR, 'div.phone')) == 0:
                time.sleep(0.1)
                contador_espera += 1
                if contador_espera > 100:
                    break
            
            if len(driver.find_elements(By.XPATH,  f'//a[text() = "Não localizamos nenhum telefone"]')) > 0:
                driver.find_element(By.XPATH,  f'//a[text() = "CONSULTAR TELEFONES RELACIONADOS"]').click()
                time.sleep()
            
            list_telefones = list()
            for telefone_html in driver.find_elements(By.CSS_SELECTOR, 'div.phone'):
                if len(telefone_html.text) > 1 and len(telefone_html.text) < 16:
                    print(telefone_html.text)
                    list_telefones.append(telefone_html.text)
            dict_venda['telefones'] = list_telefones

        #INSERIR TUDO NO BANCO DE DADOS
        for dict_venda in list_vendas:
            insere_venda(dict_venda['num_pedido'], dict_venda['nome'], dict_venda['documento'], dict_venda['itens'], dict_venda['telefones'])

        #LÊ TUDO DO BANCO DE DADOS E ENVIA AS MSGS - DE SEG A QUINTA DAS 8 AS 15. SEXTA DAS 8 AS 13
        list_vendas_x = carrega_pedidos_nao_contatados()

        if len(list_vendas_x) > 0:
            root = tk.Tk()
            root.withdraw()
            root.after(5000, root.destroy)

            xy = 250
            pyautogui.moveTo(xy,xy)
            pymsgbox.rootWindowPosition = f"+{xy}+{xy}"

            winsound.Beep(550, 700)
            winsound.Beep(450, 700)
            winsound.Beep(350, 700)
            
            pyautogui.FAILSAFE = False
            pyautogui.alert(title='ATENÇÂO', text='Nova(s) compra(s) identificadas. Não mexa na aba do whatsApp!', timeout=5000)

        for dict_venda in list_vendas_x:
            if len(dict_venda['telefones']) == 0:
                print(dict_venda['comprador'], 'Não tem telefone')
                set_pedido_chamado(dict_venda['id'], 2)
                continue
            
            msg_list = list()
            msg_list.append(('Hope!:salute', Keys.ENTER))
            msg_list.append('')
            msg_list.append(f'*{dict_venda["comprador"]}?*')
            msg_list.append(f'Aqui é da Tatical Militaria, tudo bem guerreiro(a)?')
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

        if len(list_vendas_x) > 0:
            root = tk.Tk()
            root.withdraw()
            root.after(5000, root.destroy)
            pyautogui.alert(title='PRONTO!!!', text='O programa já chamou todas as pessoas. Agora você pode continuar usando o navegador.!', timeout=3000)


        time.sleep(30)
    
    except Exception as ex:
        time.sleep(5)
        print('Excption:::', ex)

