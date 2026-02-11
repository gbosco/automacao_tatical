
s = '''
Modelo: Pt809 838 Th380 Th9 Th40
Material: Kydex 0,80 (2mm)
Cor: Preto
Peso: 135G
Uso: Interno
'''

saida = '<ul>'
for x in s.splitlines():
    if x:
        saida += f'<li>{x}</li>'
saida += '</ul>'
print(saida)
print('Tamanho:', len(saida))