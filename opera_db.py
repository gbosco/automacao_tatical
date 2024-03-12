import sqlite3
from pathlib import Path
import datetime

ROOT_DIR = Path('C:/Users/Felipe/OneDrive/Área de Trabalho/Bosco/Projects/wpp_automacao/wpp_automacao_tatical/db.sqlite3').parent
DB_NAME = 'db.sqlite3'
DB_FILE = ROOT_DIR / DB_NAME

def is_pedido_lido(numero_pedido):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    cursor.execute(f'SELECT COUNT(*) AS CONTADOR FROM VENDAS WHERE NUMERO_IDR = {numero_pedido}')
    result = cursor.fetchone()
    
    cursor.close()
    connection.close()

    if result[0] > 0:
        return True
    return False

def insere_venda(numero_pedido, nome_comprador, documento, itens = [], telefones = []):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    cursor.execute('INSERT INTO VENDAS (NUMERO_IDR, COMPRADOR, DOCUMENTO, FOI_CHAMADO, DATAHORA) VALUES (?,?,?,?,?)',\
                   [numero_pedido, nome_comprador, documento,0,datetime.datetime.now()])
    id = cursor.execute('SELECT ID FROM VENDAS WHERE NUMERO_IDR = ?', [numero_pedido]).fetchone()[0]

    for item in itens:
        produto, qtd, variacao = item
        cursor.execute('INSERT INTO VENDAS_ITENS (DESCRICAO, QTD, VARIACAO, ID_VENDAS) VALUES (?,?,?,?)', [produto, qtd, variacao, id])
    
    for telefone in telefones:
        cursor.execute('INSERT INTO VENDAS_TELEFONES (TELEFONE, ID_VENDAS) VALUES (?,?)', [telefone, id])

    connection.commit()
    cursor.close()
    connection.close()

def carrega_pedidos_nao_contatados():
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    retorno_vendas = []
    cursor.execute(f'SELECT ID, COMPRADOR, DOCUMENTO FROM VENDAS WHERE FOI_CHAMADO = ?', [0])
    for result_venda in cursor.fetchall():
        id, comprador, documento = result_venda
        dict_venda = dict(id=id, comprador=comprador, documento=documento, itens=[], telefones=[])

        cursor.execute('SELECT DESCRICAO, QTD, VARIACAO FROM VENDAS_ITENS WHERE ID_VENDAS = ?', [id])
        for result_venda_item in cursor.fetchall():
            descricao, qtd, variacao = result_venda_item
            dict_venda['itens'].append((descricao, qtd, variacao))
        
        cursor.execute('SELECT TELEFONE FROM VENDAS_TELEFONES WHERE ID_VENDAS = ?', [id])
        for result_telefone in cursor.fetchall():
            dict_venda['telefones'].append(result_telefone[0])

        retorno_vendas.append(dict_venda)

    cursor.close()
    connection.close()

    return retorno_vendas

def set_pedido_chamado(id, status = 1):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    cursor.execute(f'UPDATE VENDAS SET FOI_CHAMADO = {status} WHERE ID = ?', [id])
    
    connection.commit()
    cursor.close()
    connection.close()