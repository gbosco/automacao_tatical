from selenium.webdriver.chromium.webdriver import ChromiumDriver
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
    

def envia_msg(driver : ChromiumDriver, telefone: str, msg, enviar=True, comprador = ''):
    abre_aba_wpp(driver)
    telefone = telefone.replace(' ', '').replace('(','').replace(')', '').replace('-', '')
                                           
    seletor_div_conversas = (By.CSS_SELECTOR, '#pane-side > div > div > div > div')
    carregando = True
    while carregando:
        if len(driver.find_elements(*seletor_div_conversas)) > 0:
          carregando = False
        time.sleep(0.1)
    
    seletor_input_msg = (By.CSS_SELECTOR, 'div[aria-label="Digite uma mensagem"')
    
    element_grupo_abordagem = None
    for element in driver.find_elements(*seletor_div_conversas):
        if element.text.count('ABORDAGEM CLIENTES') > 0:
            element_grupo_abordagem = element
            element_grupo_abordagem.click()
            break
    
    time.sleep(5)
    if comprador:
        driver.find_element(*seletor_input_msg).send_keys('*'+comprador+'*')
        driver.find_element(*seletor_input_msg).send_keys(Keys.ENTER)
    
    driver.find_element(*seletor_input_msg).send_keys(telefone)
    driver.find_element(*seletor_input_msg).send_keys(Keys.ENTER)

    while True:    
        driver.find_element(By.XPATH,  f'//a[text() = "{telefone}"]').click()
        time.sleep(5)
        if len(driver.find_elements(By.CSS_SELECTOR,'div[aria-label="Conversar com "')) == 0:
            raise Exception('sem_wpp')
        
        driver.find_element(By.CSS_SELECTOR,'div[aria-label="Conversar com "').click()
        time.sleep(3)

        if not driver.find_element(By.CSS_SELECTOR, '#main header > div:nth-child(2) > div:nth-child(1)').text.count('ABORDAGEM CLIENTES'):
            break

    input_box_msg = driver.find_element(*seletor_input_msg)
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

    #NUNCA FICAR COM A CONVERSA ABERTA
    element_grupo_abordagem.click()

def abre_aba_wpp(driver : ChromiumDriver):
    if driver.current_url.count('web.whatsapp.com') == 0:
        abrir_nova = True
        for window_handle in driver.window_handles:
            driver.switch_to.window(window_handle)
            if driver.current_url.count('whatsapp.com') > 0:
                abrir_nova = False
                break

        if abrir_nova:
            driver.execute_script("window.open('https://web.whatsapp.com');")
            driver.switch_to.window(driver.window_handles[-1])
            
            