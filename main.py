from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from opera_db import carrega_pedidos_nao_contatados, is_pedido_lido, insere_venda, set_pedido_chamado
from opera_wpp import envia_msg
from navegador import fechar_tudo_zord, get_element_by_text, click
from opera_mercado_turbo import verifica_mercado_turbo
from dotenv import load_dotenv
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
load_dotenv()

import time, os, re, datetime as dt, traceback, requests
import tkinter as tk
#import tkinter.messagebox as msgbox
import pyautogui, pymsgbox, winsound
from selenium.common.exceptions import NoSuchWindowException 

def set_aba_zord(driver):
    for i in range(len(driver.window_handles)):
        driver.switch_to.window(driver.window_handles[i])
        if driver.current_url.count('https://taticalmilitaria.painel.magazord.com.br') > 0:
            break
    time.sleep(3)

somente_atualizar_estoque = True

options = EdgeOptions()

options.add_argument(r"--user-data-dir=C:\Users\vinic\AppData\Local\Microsoft\Edge\User Data")
options.add_argument("--profile-directory=Profile 1")

options.add_argument("--start-maximized")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Edge(options=options)

seletor_icon_maga = (By.CSS_SELECTOR, ".icon.icon-MAGAZORD")

driver.get("https://taticalmilitaria.painel.magazord.com.br")
time.sleep(2)
fechar_tudo_zord(driver, 2)

while len(driver.find_elements(By.ID, 'password')) > 0:
    try:
        driver.find_element(By.ID, 'email').clear()
        driver.find_element(By.ID, 'email').send_keys(os.getenv('EMAIL_MAGAZORD'))

        driver.find_element(By.ID, 'password').clear()
        driver.find_element(By.ID, 'password').send_keys(os.getenv('SENHA_MAGAZORD'))
        time.sleep(1) 
        
        driver.find_element(By.CSS_SELECTOR, 'button.submit').click()
    except StaleElementReferenceException:
        pass
    except NoSuchElementException:
        pass
time.sleep(2)
fechar_tudo_zord(driver, 2)
time.sleep(1)

#Abrir pelo menu a tela de pedidos
try:
    click(driver, driver.find_element(*seletor_icon_maga))
finally:
    driver.find_element(*seletor_icon_maga).click()


driver.find_element(By.XPATH, '//*[@id="area-superior"]/div/div[1]/ul/li[1]/ul/li[2]/div/span').click()
                               
time.sleep(3)

rodando = True
while rodando:
    try:
        set_aba_zord(driver)
        while len(driver.find_elements(By.CSS_SELECTOR, '.x-tab-close-btn')) > 1:
            driver.find_elements(By.CSS_SELECTOR, '.x-tab-close-btn')[-1].click()
        #Atualizar pedidos
        driver.find_element(By.XPATH, "//*[text()='Atualizar']").click()
        time.sleep(2)

        list_vendas = list()
        #Desselecionar qualquer linha que eventualmente esteja selecionada, para evitar erros
        for tr in driver.find_elements(By.CSS_SELECTOR, 'tr.x-grid-row-selected:has(div.x-grid-row-checker)'):
            tr.find_element(By.CSS_SELECTOR, 'div.x-grid-row-checker').click()

        for tr in driver.find_elements(By.CSS_SELECTOR, 'tr.x-grid-row'):

            num_pedido = tr.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            if is_pedido_lido(num_pedido):
                continue
            chechbox = tr.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > div > div')
            chechbox.click()
            driver.find_element(By.XPATH, "//*[text()='Visualizar']").click()
            time.sleep(2)

            #Dentro da página do pedido
            try:
                driver.find_element(By.CSS_SELECTOR, 'div[role="dialog"] button').click()#Add para pedidos em que abre um observação como cx de diálogo
            except:
                ...

            # nome = driver.find_elements(By.XPATH, "//span[text()='Cliente']//..//..//..")[2].text
            nome = driver.find_element(By.CSS_SELECTOR, "#cadastro-cliente > div > div div > div:nth-child(1) > strong > span").text
            time.sleep(3)

            text_pagina = driver.find_element(By.CSS_SELECTOR, 'body').text
            re_cpf_cnpj = re.search(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', text_pagina)
            if not re_cpf_cnpj:
                re_cpf_cnpj = re.search(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b', text_pagina)
            if bool(re_cpf_cnpj):
                cpf_cnpj = re_cpf_cnpj.group()
                cpf_cnpj = cpf_cnpj.replace('.','').replace('-', '').replace('/', '')
            else:
                cpf_cnpj = ''

            dict_venda = dict(nome=nome,documento=cpf_cnpj,num_pedido=num_pedido)
            print('Nome:', nome, 'CPF:', cpf_cnpj)
            
            list_venda_item = list()
            for produto_html in driver.find_elements(By.CSS_SELECTOR, '.swiper-slide'):
                nome_produto = produto_html.find_element(By.CSS_SELECTOR, '.nomeProduto').text
                qtd_produto  = produto_html.find_element(By.CSS_SELECTOR, '.itemValue').text
                sku          = produto_html.find_element(By.CSS_SELECTOR, '.codigoProduto').text.replace('\nCopiar', '')

                list_venda_item.append((nome_produto, qtd_produto, sku))

                #Tentar ir apertando o botão para o lado caso tenha muitos produto.
                try:
                    driver.find_element(By.CSS_SELECTOR, '.swiper-button-next').click()
                except:
                    ...
            
            if bool(cpf_cnpj):
                dict_venda['itens'] = list_venda_item
                list_vendas.append(dict_venda)

            #Fecha a última aba aberta (Do pedido que acabou de ler)
            driver.find_elements(By.CSS_SELECTOR, ".x-tab-close-btn")[-1].click()
            chechbox.click()
        ######################################## INICIO ########################################
        try:
            vendas_outras_contas = verifica_mercado_turbo(driver)
            list_vendas.extend(vendas_outras_contas)
        except Exception as e:
            import traceback
            print('Erro ao ler mercado turbo', e)
            traceback.print_exc()
        ######################################## FIM ########################################

        #LER OS TELEFONES (ASSERTIVA)
        if len(list_vendas) > 0:
            logou_assert = False
            #https://painel.assertivasolucoes.com.br
            
            abrir_nova = True
            for window_handle in driver.window_handles:
                driver.switch_to.window(window_handle)
                if driver.current_url.count('assertivasolucoes') > 0:
                    abrir_nova = False
                    break

            if abrir_nova:
                # driver.execute_script("window.open('https://painel.assertivasolucoes.com.br');")
                # driver.switch_to.window(driver.window_handles[-1])
                driver.switch_to.new_window('tab')
                driver.get('https://painel.assertivasolucoes.com.br')
                time.sleep(2)
            
            tentativas = 0
            while not logou_assert:
                driver.get('https://painel.assertivasolucoes.com.br/login')
                time.sleep(1.5)
                if len(driver.find_elements(By.ID, 'password')) > 0:
                    if driver.find_element(By.ID, 'email').text == '':
                        # driver.find_element(By.ID, 'email').send_keys(os.getenv('EMAIL_ASSERTIVA'))
                        # driver.find_element(By.ID, 'password').send_keys(os.getenv('SENHA_ASSERTIVA'))
                        driver.find_element(By.ID, 'email').send_keys('taticalmilitaria1@hotmail.com')
                        driver.find_element(By.ID, 'password').send_keys('10Facil0.')
                        time.sleep(1)
                    driver.find_element(By.ID, 'btn-entrar').click()
                    time.sleep(5)
                else:
                    logou_assert = True
                tentativas += 1
                if tentativas > 5 and not logou_assert:
                    from opera_wpp import enviar_mensagem_wpp_evolution_api
                    enviar_mensagem_wpp_evolution_api('47996526759', 'Erro ao logar no assertiva')
                    raise Exception("Erro assertiva. Não foi possível logar")
            

        for dict_venda in list_vendas:
            
            if len(dict_venda['documento']) == 14:
                url = f'https://localize.assertivasolucoes.com.br/consulta/cnpj'
            else:
                url = f'https://localize.assertivasolucoes.com.br/consulta/cpf'
            
            driver.get(url)

            contador_recarregar = 0
            while len(driver.find_elements(By.CSS_SELECTOR, '[type="submit"]')) == 0:
                time.sleep(0.1)
                contador_recarregar += 1
                if contador_recarregar > 100:
                    print('recarregando', url)
                    driver.get(url)
                    contador_recarregar = 0
            seletor_finalidade_uso = '#select-finalidade-uso'
            if len(driver.find_elements(By.CSS_SELECTOR, seletor_finalidade_uso)) > 0:
                if driver.find_element(By.CSS_SELECTOR, seletor_finalidade_uso).text != 'Confirmação de identidade':
                    driver.find_element(By.CSS_SELECTOR, seletor_finalidade_uso).click()
                    time.sleep(1)
                    driver.find_element(By.CSS_SELECTOR, '#option-finalidade-0').click()
            
            driver.find_element(By.CSS_SELECTOR, '#consultation-type-select').click()
            driver.find_element(By.CSS_SELECTOR, 'ul.MuiMenu-list > li:first-child').click()

            driver.find_elements(By.CSS_SELECTOR, '#root input')[1]\
            .send_keys(dict_venda['documento'])
            time.sleep(0.3)
            driver.find_element(By.CSS_SELECTOR, '[type="submit"]').click()
            
            contador_espera = 0
            while len(driver.find_elements(By.CSS_SELECTOR, 'div.phone')) == 0:
                time.sleep(0.1)
                contador_espera += 1
                if contador_espera > 100:
                    break
            
            if len(driver.find_elements(By.CSS_SELECTOR, 'div.phone')) == 0:
                try:
                    driver.find_element(By.XPATH,  f'//*[text() = "CONSULTAR TELEFONES RELACIONADOS"]').click()
                    time.sleep(2)
                except:
                    pass
            
            list_telefones = list()
            for telefone_html in driver.find_elements(By.CSS_SELECTOR, 'div.phone > div > span'):
                if len(telefone_html.text) > 1 and len(telefone_html.text) < 16:
                    print(telefone_html.text)
                    list_telefones.append(telefone_html.text)
            dict_venda['telefones'] = list_telefones

        #INSERIR TUDO NO BANCO DE DADOS
        for dict_venda in list_vendas:
            insere_venda(dict_venda['num_pedido'], dict_venda['nome'], dict_venda['documento'], dict_venda['itens'], dict_venda['telefones'])

        list_vendas_x = carrega_pedidos_nao_contatados()

        # if len(list_vendas_x) > 0:
        #     root = tk.Tk()
        #     root.withdraw()
        #     root.after(5000, root.destroy)

            # xy = 250
            # pyautogui.moveTo(xy,xy)
            # pymsgbox.rootWindowPosition = f"+{xy}+{xy}"

            # winsound.Beep(550, 700)
            # winsound.Beep(450, 700)
            # winsound.Beep(350, 700)
            
            # pyautogui.FAILSAFE = False
            # pyautogui.alert(title='ATENÇÃO', text='Nova(s) compra(s) identificadas. Não mexa na aba do whatsApp!', timeout=5000)

        for dict_venda in list_vendas_x:
            
            if len(['telefones']) == 0:
                print(dict_venda['comprador'], 'Não tem telefone')
                set_pedido_chamado(dict_venda['id'], 2)
                continue

            produtos_str = ''
            for i,item in enumerate(dict_venda['itens']):
                if not item[0]:
                    continue
                if i > 0:
                    produtos_str += ' e '
                produtos_str += '*'+str(item[1])+'x '+item[0]+'*'

            msg_fora_horario = ''
            if int(time.strftime('%H')) < 8 or int(time.strftime('%H')) >= 15 or dt.date.today().weekday() in (5,6):
                msg_fora_horario = '''No momento estou passando somente para agradecer e confirmar a sua compra. Entrarei em contato por aqui novamente assim que possível para um melhor atendimento. Qualquer dúvida, estarei a disposição assim que retornar! (Nosso horário de atendimento é de segunda à sexta das 9:00 às 15:00). Tenha um ótimo e abençoado dia! '''

            mensagem = f'''Hope!🫡

*{dict_venda["comprador"]}*?

Aqui é da Tatical Militaria, tudo bem guerreiro(a)?
Recebi seu pedido via mercado livre:{produtos_str}
Confere?

Caso você não seja a pessoa indicada acima, desculpe o incômodo e desconsidere essa mensagem. 🙏🏽
                '''

            if int(time.strftime('%H')) < 8 or int(time.strftime('%H')) >= 15 or dt.date.today().weekday() in (5,6):
                mensagem += '''
                
No momento estou passando somente para agradecer e confirmar a sua compra. Entrarei em contato por aqui novamente assim que possível para um melhor atendimento. Qualquer dúvida, estarei a disposição assim que retornar! (Nosso horário de atendimento é de segunda à sexta das 9:00 às 15:00). Tenha um ótimo e abençoado dia! ⭐ 
                        '''

            # msgProdutos = ''
            # msg_list = list()
            # msg_list.append(('Hope!:salute', Keys.ENTER))
            # msg_list.append('')
            # msg_list.append(f'*{dict_venda["comprador"]}?*')
            # msg_list.append(f'Aqui é da Tatical Militaria, tudo bem guerreiro(a)?')
            # msgProdutos : str = 'Recebi seu pedido via mercado livre:'
            # for i,item in enumerate(dict_venda['itens']):
            #     if not item[0]:
            #         continue
            #     if i > 0:
            #         msgProdutos += ' e '
            #     msgProdutos += '*'+str(item[1])+'x '+item[0]+'*'
            
            # msg_list.append(msgProdutos)
            # msg_list.append('Confere?')
            # msg_list.append('')
            # msg_list.append(('Caso você não seja a pessoa indicada acima desculpe o incômodo e desconsidere essa mensagem. :mãos juntas', Keys.ENTER))
            
            # if int(time.strftime('%H')) < 8 or int(time.strftime('%H')) >= 15 or dt.date.today().weekday() in (5,6):
            #     msg_list.append('')
            #     msg_list.append((
            #             'No momento estou passando somente para agradecer e confirmar a sua compra. Entrarei em contato por aqui novamente assim que possível para um melhor atendimento. Qualquer dúvida, estarei a disposição assim que retornar! (Nosso horário de atendimento é de segunda à sexta das 9:00 às 15:00). Tenha um ótimo e abençoado dia! :estrela ', Keys.ENTER
            #      ))

            sem_wpp = True
            for telefone in dict_venda['telefones']:
                try:
                    comprador = dict_venda["comprador"] if dict_venda['telefones'].index(telefone) == 0 else ''
                    
                    ###################### CHAMADA COM EVOLUTION ####################
                    from opera_wpp import enviar_mensagem_wpp_evolution_api
                    status_code = enviar_mensagem_wpp_evolution_api(telefone.replace(' ','').replace('(','').replace(')','').replace('-',''), mensagem)

                    ################## CHAMADA COM SELENIUM ##################
                    # envia_msg(driver, telefone, msg_list, comprador=comprador)

                    ############# CHAMADA KOMMO #################
                    # payload = {
                    #     "mensagem" : msgProdutos,
                    #     "cliente_nome" : comprador,
                    #     "telefone" : telefone.replace(' ','').replace('(','').replace(')','').replace('-',''),
                    #     "pipeline_name" : "Prospecção ativa",
                    #     "add_resposta_asst" : "false",
                    # }
                    # response = requests.post('https://tatical.atendimentosmart.com.br/lead/', data=payload)
                    ##############################
                    if status_code == 201:#
                        set_pedido_chamado(dict_venda['id'])
                        sem_wpp = False
                    elif status_code == 400:
                        print('Número sem whatsapp:', telefone)
                except TimeoutError as err:
                    print('Erro ao enviar mensagem. Servidor parece estar fora do ar')
                    raise err
                except Exception as err:
                    print('Erro:', dict_venda["comprador"], '-',telefone,'-',err)
            if sem_wpp:
                set_pedido_chamado(dict_venda['id'], 3)
            
        # if len(list_vendas_x) > 0:
        #     root = tk.Tk()
        #     root.withdraw()
        #     root.after(5000, root.destroy)
        #     pyautogui.alert(title='PRONTO!!!', text='O programa já chamou todas as pessoas. Agora você pode continuar usando o navegador.!', timeout=3000)
         
        time.sleep(45)

    except NoSuchWindowException as ex:
        pass
    except Exception as ex:
        try:
            click(driver, get_element_by_text(driver, 'OK'))            
        except:
            ...
        print(':::Excption Type:::', type(ex))
        print(':::Excption:::', ex)
        traceback.print_exc()

