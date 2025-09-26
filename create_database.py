import sqlite3
import os

def criar_banco():
    """Cria o banco de dados e a estrutura de tabelas"""
    
    # Nome do arquivo do banco
    db_name = 'produtos_maeto.db'
    
    # Remove o banco se já existir (para começar limpo)
    if os.path.exists(db_name):
        os.remove(db_name)
        print(f"Banco existente '{db_name}' removido.")
    
    # Conecta e cria o banco
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Cria a tabela produtos
    cursor.execute('''
        CREATE TABLE produtos (
            sku TEXT PRIMARY KEY,
            titulo_produto TEXT NOT NULL,
            preco TEXT,
            preco_pix TEXT,
            valor_parcelas TEXT,
            numero_parcelas TEXT,
            termo_busca TEXT NOT NULL,
            data_primeira_insercao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            informacoes_tecnicas TEXT
        )
    ''')
    
    # Cria índices para otimizar consultas
    cursor.execute('CREATE INDEX idx_termo_busca ON produtos(termo_busca)')
    cursor.execute('CREATE INDEX idx_data_insercao ON produtos(data_primeira_insercao)')
    cursor.execute('CREATE INDEX idx_data_atualizacao ON produtos(data_ultima_atualizacao)')
    
    conn.commit()
    conn.close()
    
    print(f"Banco de dados '{db_name}' criado com sucesso!")
    print("Estrutura da tabela 'produtos' criada.")
    print("Índices criados para otimização de consultas.")

if __name__ == "__main__":
    print("=== CRIAÇÃO DO BANCO DE DADOS ===")
    print("Criando banco de dados SQLite3...\n")
    
    try:
        criar_banco()
        print("\n✅ Banco criado com sucesso!")
        print("Agora você pode executar o script principal: python test_pandas.py")
    except Exception as e:
        print(f"\n❌ Erro ao criar o banco: {e}")