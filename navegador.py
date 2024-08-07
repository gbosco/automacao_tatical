import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

def get_element_by_text(driver, text, multiple = False, texto_exato = True, css_class = '', tipo_tag = '*'):
    if texto_exato:
        seletor = f'//{tipo_tag}[text()="{text}"]'
    else:
        seletor = f'//{tipo_tag}[text()[contains(., "{text}")]]'
    if not multiple:
        metodo = driver.find_element
    else:
        metodo = driver.find_elements
    if css_class:
        seletor = seletor + f'[@class[contains(.,"{css_class}")]]'
    
    return metodo(By.XPATH, seletor)

def click(driver, element, suprimir_TimeoutException = False, timeout = 5):
    
    if not type(element) == list:
        element = [element]
    for el in element:
        try:
            WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable(el)
            )
            driver.execute_script("arguments[0].click();", el)
        except TimeoutException as ex:
            if not suprimir_TimeoutException:
                raise ex
    
def get_driver_navegador():
    navegador = os.environ['navegador']

    if navegador.lower() == 'edge':
        os.system("taskkill /im msedge.exe /f")

        options = webdriver.EdgeOptions()
        usu = os.environ['usuario_edge']
        caminho = os.environ['caminho_usuario_edge']
        options.add_argument(f'user-data-dir={caminho}')
        options.add_argument(f'profile-directory={usu}')
        
        return webdriver.Edge(options=options)
    
    if navegador.lower() == 'chrome':
        os.system("taskkill /im chrome.exe /f")

        options = webdriver.ChromeOptions()
        usu = os.environ['usuario_chrome']
        caminho = os.environ['caminho_usuario_chrome']
        options.add_argument(f'user-data-dir={caminho}')
        options.add_argument(f'profile-directory={usu}')
        
        return webdriver.Chrome(options=options)
    
def fechar_tudo_zord(driver, qtdd = 10):
    for _ in range(qtdd):
        try:
            click(driver, get_element_by_text(driver, 'OK'))
        except:
            pass
        try:
            click(driver, get_element_by_text(driver, 'Fechar', css_class='prev'))
        except:
            pass
        try:
            driver.find_element(By.CSS_SELECTOR, 'div.close').click()
        except:
            pass