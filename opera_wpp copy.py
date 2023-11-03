from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
import time

def shift_enter(driver):
        ActionChains(driver)\
            .key_down(Keys.SHIFT)\
            .send_keys(Keys.ENTER)\
            .key_up(Keys.SHIFT)\
            .perform()
    

def envia_msg(driver : webdriver.Chrome, telefone: str, msg, enviar=True):
    abre_aba_wpp(driver)
    telefone = telefone.replace(' ', '').replace('(','').replace(')', '').replace('-', '')

    #driver.switch_to.window(window_handle)
    #driver.get(f'https://web.whatsapp.com/send?phone={telefone}')
    
    # Esperar para encontrar o input
    '''
    input_box_msg = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#main > footer > div._2lSWV._3cjY2.copyable-area > div > span:nth-child(2) > div > div._1VZX7 > div._3Uu1_ > div.g0rxnol2.ln8gz9je.lexical-rich-text-input > div.to2l77zo.gfz4du6o.ag5g9lrv.bze30y65.kao4egtt > p')
        )
    )
    '''
    carregando = True
    contador_anti_trava = 0
    while carregando:
        if len(driver.find_elements(By.CSS_SELECTOR, '#main > footer > div._2lSWV._3cjY2.copyable-area > div > span:nth-child(2) > div > div._1VZX7 > div._3Uu1_ > div.g0rxnol2.ln8gz9je.lexical-rich-text-input > div.to2l77zo.gfz4du6o.ag5g9lrv.bze30y65.kao4egtt > p')) > 0:
          carregando = False
        if len(driver.find_elements(By.CSS_SELECTOR, '#app > div > span:nth-child(2) > div > span > div > div > div > div > div > div.p357zi0d.ns59xd2u.kcgo1i74.gq7nj7y3.lnjlmjd6.przvwfww.mc6o24uu.e65innqk.le5p0ye3 > div > button')) > 0:
            if driver.find_element(By.CSS_SELECTOR, '#app > div > span:nth-child(2) > div > span > div > div > div > div > div > div.p357zi0d.ns59xd2u.kcgo1i74.gq7nj7y3.lnjlmjd6.przvwfww.mc6o24uu.e65innqk.le5p0ye3 > div > button').text.upper() == 'OK':
                raise Exception('sem_wpp')
        time.sleep(0.1)
        
        contador_anti_trava += 1
        if contador_anti_trava > 100:
            print('carregadando novamente -- ', telefone)
            driver.get(f'https://web.whatsapp.com/send?phone={telefone}')
            contador_anti_trava = 0


    input_box_msg = driver.find_element(By.CSS_SELECTOR, '#main > footer > div._2lSWV._3cjY2.copyable-area > div > span:nth-child(2) > div > div._1VZX7 > div._3Uu1_ > div.g0rxnol2.ln8gz9je.lexical-rich-text-input > div.to2l77zo.gfz4du6o.ag5g9lrv.bze30y65.kao4egtt > p')    
    if type(msg) == str:
        input_box_msg.send_keys(msg)
    if type(msg) == list:
        for m_i in msg:
            if type(m_i) == str:
                input_box_msg.send_keys(m_i)
            if type(m_i) == tuple:
                input_box_msg.send_keys(m_i[0])
                input_box_msg.send_keys(m_i[1])
            shift_enter(driver)
    if enviar:
        #Enter para enviar msg
        input_box_msg.send_keys(Keys.ENTER)

    time.sleep(1)

def abre_aba_wpp(driver : webdriver.Chrome):
    if driver.current_url.count('web.whatsapp.com') == 0:
        abrir_nova = True
        for window_handle in driver.window_handles:
            driver.switch_to.window(window_handle)
            if driver.current_url.count('whatsapp.com') > 0:
                abrir_nova = False

        if abrir_nova:
            #driver.execute_script("window.open('https://web.whatsapp.com');")
            #return driver.window_handles[-1]
            raise Exception('Abra a aba do WPP')
