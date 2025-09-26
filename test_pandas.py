import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import quote
import time
import threading
import sys
import sqlite3
import os
from datetime import datetime
import json

def buscar_produtos():
    # Solicita o termo de busca ao usuário
    termo_busca = input("Digite o nome do produto (ou 'sair' para encerrar): ")
    
    # Verifica se o usuário quer sair
    if termo_busca.lower() == 'sair':
        return None
    
    # Codifica o termo para URL
    termo_codificado = quote(termo_busca)
    
    # Monta a URL de busca
    url = f"https://www.lojamaeto.com/search/?q={termo_codificado}"
    
    print(f"Buscando por: {termo_busca}")
    
    # Inicia o spinner de carregamento
    spinner = Spinner()
    spinner.start()
    
    try:
        # Faz a requisição HTTP
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse do HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encontra todos os itens de produto da primeira página
        items = soup.select('.item')
        
        if not items:
            spinner.stop()
            print("Nenhum produto encontrado.")
            return pd.DataFrame()  # Retorna DataFrame vazio para continuar o programa
        
        # Lista para armazenar todos os produtos de todas as páginas
        todos_produtos = []
        
        # Processa primeira página
        todos_produtos.extend(extrair_produtos_pagina(items))
        
        # Tenta buscar mais páginas
        pagina = 2
        while True:
            # Testa diferentes padrões de paginação
            urls_pagina = [
                f"{url}&page={pagina}",
                f"{url}?q={termo_codificado}&page={pagina}",
                f"{url}&p={pagina}",
                f"{url}&start={(pagina-1)*30}",
                f"{url}&offset={(pagina-1)*30}"
            ]
            
            produtos_pagina = []
            for url_teste in urls_pagina:
                try:
                    time.sleep(0.5)  # Pausa para não sobrecarregar o servidor
                    response_pagina = requests.get(url_teste, headers=headers, timeout=10)
                    if response_pagina.status_code == 200:
                        soup_pagina = BeautifulSoup(response_pagina.content, 'html.parser')
                        items_pagina = soup_pagina.select('.item')
                        
                        if items_pagina and len(items_pagina) > 0:
                            # Verifica se não são os mesmos produtos da página anterior
                            skus_pagina = [extrair_sku(item) for item in items_pagina]
                            skus_anteriores = [p['SKU'] for p in todos_produtos]
                            
                            # Se encontrou produtos novos
                            if any(sku not in skus_anteriores for sku in skus_pagina if sku):
                                produtos_pagina = extrair_produtos_pagina(items_pagina)
                                break
                except:
                    continue
            
            if not produtos_pagina:
                break
            
            todos_produtos.extend(produtos_pagina)
            pagina += 1
            
            # Limite de segurança para não fazer muitas requisições
            if pagina > 20:
                break
        
        # Cria DataFrame com todos os produtos
        df = pd.DataFrame(todos_produtos)
        
        # Para o spinner
        spinner.stop()
        
        # Remove colunas completamente vazias
        df = df.dropna(axis=1, how='all')
        
        print(f"Encontrados {len(todos_produtos)} produtos no total:\n")
        
        # Exibe a tabela (excluindo a coluna de informações técnicas)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 50)
        
        # Cria uma cópia do DataFrame sem a coluna de informações técnicas para exibição
        df_display = df.drop(columns=['Informacoes_Tecnicas'], errors='ignore')
        print(df_display.to_string(index=False))
        
        # Salva os dados no banco SQLite3
        produtos_salvos = salvar_no_banco(todos_produtos, termo_busca)
        print(f"\n{produtos_salvos['novos']} produtos novos adicionados ao banco.")
        print(f"{produtos_salvos['atualizados']} produtos existentes foram atualizados.")
        
        return df
        
    except requests.RequestException as e:
        spinner.stop()
        print(f"Erro na requisição: {e}")
        return pd.DataFrame()  # Retorna DataFrame vazio para continuar o programa
    except Exception as e:
        spinner.stop()
        print(f"Erro inesperado: {e}")
        return pd.DataFrame()  # Retorna DataFrame vazio para continuar o programa

class Spinner:
    def __init__(self):
        self.spinning = False
        self.thread = None
        
    def spin(self):
        chars = "|/-\\"
        idx = 0
        while self.spinning:
            sys.stdout.write(f"\r Carregando {chars[idx % len(chars)]}")
            sys.stdout.flush()
            time.sleep(0.1)
            idx += 1
    
    def start(self):
        self.spinning = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        self.spinning = False
        if self.thread:
            self.thread.join()
        sys.stdout.write("\r" + " " * 20 + "\r")  # Limpa a linha
        sys.stdout.flush()

def verificar_banco():
    """Verifica se o banco de dados existe"""
    if not os.path.exists('produtos_maeto.db'):
        print("❌ Banco de dados não encontrado!")
        print("Execute primeiro: python create_database.py")
        return False
    return True

def verificar_produto_tem_info_tecnica(sku):
    """Verifica se um produto já possui informações técnicas no banco"""
    if not verificar_banco():
        return False
    
    try:
        conn = sqlite3.connect('produtos_maeto.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT informacoes_tecnicas 
            FROM produtos 
            WHERE sku = ? AND informacoes_tecnicas IS NOT NULL AND informacoes_tecnicas != '{}'
        ''', (sku,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        return resultado is not None
    except Exception as e:
        print(f"Erro ao verificar informações técnicas: {e}")
        return False

def salvar_no_banco(produtos, termo_busca):
    """Salva ou atualiza produtos no banco de dados"""
    if not verificar_banco():
        return {'novos': 0, 'atualizados': 0}
    
    conn = sqlite3.connect('produtos_maeto.db')
    cursor = conn.cursor()
    
    produtos_novos = 0
    produtos_atualizados = 0
    
    for produto in produtos:
        # Verifica se o produto já existe
        cursor.execute('SELECT sku FROM produtos WHERE sku = ?', (produto['SKU'],))
        existe = cursor.fetchone()
        
        if existe:
            # Produto existe - faz UPDATE
            cursor.execute('''
                UPDATE produtos 
                SET titulo_produto = ?, preco = ?, preco_pix = ?, 
                    valor_parcelas = ?, numero_parcelas = ?, termo_busca = ?,
                    informacoes_tecnicas = ?, data_ultima_atualizacao = CURRENT_TIMESTAMP
                WHERE sku = ?
            ''', (
                produto['Titulo_do_Produto'],
                produto['Preco'],
                produto['Preco_no_PIX'],
                produto['Valor_da_Parcelas'],
                produto['Numero_de_Parcelas'],
                termo_busca,
                produto.get('Informacoes_Tecnicas', '{}'),
                produto['SKU']
            ))
            produtos_atualizados += 1
        else:
            # Produto novo - faz INSERT
            cursor.execute('''
                INSERT INTO produtos 
                (sku, titulo_produto, preco, preco_pix, valor_parcelas, 
                 numero_parcelas, termo_busca, informacoes_tecnicas, data_primeira_insercao, data_ultima_atualizacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                produto['SKU'],
                produto['Titulo_do_Produto'],
                produto['Preco'],
                produto['Preco_no_PIX'],
                produto['Valor_da_Parcelas'],
                produto['Numero_de_Parcelas'],
                termo_busca,
                produto.get('Informacoes_Tecnicas', '{}')
            ))
            produtos_novos += 1
    
    conn.commit()
    conn.close()
    
    return {
        'novos': produtos_novos,
        'atualizados': produtos_atualizados
    }

def extrair_produtos_pagina(items):
    """Extrai dados de todos os produtos de uma página"""
    produtos = []
    produtos_pulados = 0
    produtos_processados = 0
    
    print(f"Processando {len(items)} produtos...")
    
    for i, item in enumerate(items, 1):
        print(f"Produto {i}/{len(items)}:")
        
        # Extrai dados usando os mesmos seletores do Power Query
        nome = extrair_texto(item, '.product-list-name *')
        preco_a_vista = extrair_texto(item, '.cash-payment-container .to-price')
        preco_normal = extrair_texto(item, '.to-price')
        valor_parcela = extrair_texto(item, '.installments-amount')
        promocao = extrair_texto(item, '.promotion')
        texto_pagamento = extrair_texto(item, '.cash-payment-text')
        num_parcelas = extrair_texto(item, '.installments-number')
        add_cart = extrair_texto(item, '.add2cart')
        botao = extrair_texto(item, '.botao')
        preco_de = extrair_texto(item, '.from-price')
        texto_preco = extrair_texto(item, '.to-price-text + *')
        
        # Extrai SKU do atributo data-sku
        sku = extrair_sku(item)
        
        # Extrai href do produto
        href = extrair_href(item)
        print(f"  SKU: {sku}")
        print(f"  Nome: {nome}")
        print(f"  Href: {href}")
        
        # Verifica se o produto já tem informações técnicas
        informacoes_tecnicas = '{}'
        if sku and verificar_produto_tem_info_tecnica(sku):
            print(f"  ⏭️ Produto já possui informações técnicas - pulando scraping")
            produtos_pulados += 1
            # Busca as informações técnicas existentes no banco
            try:
                conn = sqlite3.connect('produtos_maeto.db')
                cursor = conn.cursor()
                cursor.execute('SELECT informacoes_tecnicas FROM produtos WHERE sku = ?', (sku,))
                resultado = cursor.fetchone()
                if resultado:
                    informacoes_tecnicas = resultado[0]
                conn.close()
            except:
                informacoes_tecnicas = '{}'
        else:
            # Converte href para URL completa e faz scraping
            url_produto = converter_href_para_url(href)
            if url_produto:
                informacoes_tecnicas = scraping_especificacoes_tecnicas(url_produto)
                produtos_processados += 1
            else:
                print(f"  ⚠️ URL do produto não encontrada")
        
        produtos.append({
            'SKU': sku,
            'Titulo_do_Produto': nome,
            'Preco': preco_normal,
            'Preco_no_PIX': preco_a_vista,
            'Valor_da_Parcelas': valor_parcela,
            'Numero_de_Parcelas': num_parcelas,
            'Informacoes_Tecnicas': informacoes_tecnicas
        })
        
        print(f"  ✅ Produto processado\n")
    
    # Exibe estatísticas de otimização
    print(f"📊 Estatísticas de processamento:")
    print(f"   • Produtos com scraping: {produtos_processados}")
    print(f"   • Produtos pulados (já tinham info): {produtos_pulados}")
    print(f"   • Total processado: {len(produtos)}\n")
    
    return produtos

def extrair_texto(item, seletor):
    """Extrai texto de um elemento usando o seletor CSS"""
    try:
        elemento = item.select_one(seletor)
        return elemento.get_text(strip=True) if elemento else ''
    except:
        return ''

def extrair_sku(item):
    """Extrai o SKU do atributo data-sku da div product"""
    try:
        # Busca pela div com classe product que contém o data-sku
        div_product = item.select_one('.product[data-sku]')
        if div_product:
            return div_product.get('data-sku', '')
        # Se não encontrar dentro do item, talvez o próprio item seja a div product
        elif item.get('data-sku'):
            return item.get('data-sku', '')
        else:
            return ''
    except:
        return ''

def extrair_href(item):
    """Extrai o href do link do produto"""
    try:
        # Busca por links <a> dentro do item
        link = item.select_one('a[href]')
        if link:
            return link.get('href', '')
        return ''
    except:
        return ''

def converter_href_para_url(href):
    """Converte href relativo para URL completa"""
    if not href:
        return ''
    
    base_url = 'https://www.lojamaeto.com'
    
    # Se já for uma URL completa, retorna como está
    if href.startswith('http'):
        return href
    
    # Se começar com /, adiciona apenas o domínio
    if href.startswith('/'):
        return base_url + href
    
    # Caso contrário, adiciona domínio e /
    return base_url + '/' + href

def scraping_especificacoes_tecnicas(url_produto):
    """Faz scraping das especificações técnicas da página do produto"""
    try:
        print(f"  → Extraindo especificações de: {url_produto}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Delay para não sobrecarregar o servidor
        time.sleep(1)
        
        response = requests.get(url_produto, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Busca a tabela de especificações técnicas
        tabela = soup.select_one('#product-description-table-attributes')
        
        if not tabela:
            print(f"    ⚠️ Tabela de especificações não encontrada")
            return '{}'
        
        especificacoes = {}
        
        # Extrai as linhas da tabela
        linhas = tabela.select('tr')
        
        for linha in linhas:
            colunas = linha.select('td')
            if len(colunas) >= 2:
                atributo = colunas[0].get_text(strip=True)
                valor = colunas[1].get_text(strip=True)
                
                if atributo and valor:
                    especificacoes[atributo] = valor
        
        print(f"    ✅ {len(especificacoes)} especificações extraídas")
        return json.dumps(especificacoes, ensure_ascii=False)
        
    except requests.RequestException as e:
        print(f"    ❌ Erro na requisição: {e}")
        return '{}'
    except Exception as e:
        print(f"    ❌ Erro inesperado: {e}")
        return '{}'

if __name__ == "__main__":
    print("=== BUSCA DE PRODUTOS - LOJA MAETO ===")
    
    # Verifica se o banco existe antes de começar
    if not verificar_banco():
        exit(1)
    
    print("Digite 'sair' para encerrar o programa")
    print("Os dados serão salvos automaticamente no banco: produtos_maeto.db\n")
    
    while True:
        # Executa a busca
        resultado = buscar_produtos()
        
        # Se o usuário digitou 'sair', encerra o programa
        if resultado is None:
            print("Encerrando programa...")
            break
        
        # Separador visual entre buscas
        print("\n" + "="*60 + "\n")