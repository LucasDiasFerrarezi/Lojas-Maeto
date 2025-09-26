# Web Scraping Loja Maeto - Extração de Produtos

Aplicação em Python para realizar web scraping de produtos no site da Loja Maeto, extraindo informações detalhadas e armazenando em banco de dados SQLite3.

## 📋 Descrição

Esta aplicação permite buscar produtos no site da Loja Maeto através de termos de pesquisa, extraindo automaticamente:

- **SKU** (Chave única do produto)
- **Título do Produto**
- **Preço**
- **Preço no PIX**
- **Valor da Parcela**
- **Número de Parcelas**
- **Informações Técnicas** (especificações detalhadas)

### 🚀 Funcionalidades

- ✅ Busca dinâmica de produtos por termo
- ✅ Extração automática de especificações técnicas
- ✅ Paginação automática para capturar todos os resultados
- ✅ Resolução de conflitos (atualização de produtos existentes)
- ✅ Otimização de performance (evita re-scraping de dados já coletados)
- ✅ Armazenamento em banco SQLite3 com unicidade por SKU

## 🛠️ Tecnologias Utilizadas

- **Python 3.7+**
- **requests** - Para requisições HTTP
- **beautifulsoup4** - Para parsing HTML
- **pandas** - Para manipulação de dados
- **lxml** - Parser XML/HTML
- **SQLite3** - Banco de dados (nativo do Python)

## 📦 Pré-requisitos

- Python 3.7 ou superior instalado
- Conexão com a internet
- Terminal/Prompt de comando

## 🔧 Instalação

### 1. Clone ou baixe o projeto

```bash
# Se usando Git
git clone <URL_DO_REPOSITORIO>
cd LojaMaeto

# Ou baixe e extraia o ZIP do projeto
```

### 2. Instale as dependências

```bash
# Instalar todas as bibliotecas necessárias
pip install requests beautifulsoup4 pandas lxml

# Ou se preferir, instale uma por vez:
pip install requests
pip install beautifulsoup4
pip install pandas
pip install lxml
```

### 3. Crie o banco de dados SQLite3

**⚠️ IMPORTANTE: Execute este passo ANTES de usar a aplicação principal!**

```bash
python create_database.py
```

Este comando irá:
- Criar o arquivo `produtos_maeto.db`
- Criar a tabela `produtos` com todos os campos necessários
- Configurar índices para otimização
- Exibir confirmação de criação

## 🚀 Como Usar

### Passo 1: Certifique-se que o banco foi criado

```bash
# Verifique se o arquivo produtos_maeto.db existe na pasta
dir produtos_maeto.db
# ou no Linux/Mac:
ls produtos_maeto.db
```

### Passo 2: Execute o programa principal

```bash
python test_pandas.py
```

### Passo 3: Interaja com o programa

1. **Digite o termo de busca** quando solicitado
   ```
   Digite o termo de busca: notebook
   ```

2. **Aguarde o processamento**
   - O programa irá buscar em todas as páginas disponíveis
   - Mostrará progresso em tempo real
   - Extrairá especificações técnicas automaticamente

3. **Visualize os resultados**
   - Produtos serão exibidos no terminal
   - Dados salvos automaticamente no banco
   - Produtos duplicados serão atualizados

### Exemplo de Uso

```bash
$ python test_pandas.py
Digite o termo de busca: mouse gamer

Buscando produtos para: mouse gamer
Processando página 1...
Processando página 2...

=== PRODUTOS ENCONTRADOS ===
SKU: MG001 | Título: Mouse Gamer RGB Pro
Preço: R$ 89,90 | PIX: R$ 80,91
Parcelas: 3x de R$ 29,97

[...mais produtos...]

Total de produtos processados: 25
Produtos novos: 20
Produtos atualizados: 5
```

## 📁 Estrutura do Projeto

```
DesafioMaeto/
├── test_pandas.py          # Programa principal
├── create_database.py      # Script para criar o banco
├── produtos_maeto.db       # Banco SQLite3 (criado após executar create_database.py)
└── README.md              # Este arquivo
```

### Descrição dos Arquivos

- **`test_pandas.py`**: Aplicação principal com todas as funcionalidades de scraping
- **`create_database.py`**: Script para inicializar o banco de dados SQLite3
- **`produtos_maeto.db`**: Arquivo do banco de dados (criado automaticamente)

## 🗄️ Estrutura do Banco de Dados

### Tabela: `produtos`

| Campo | Tipo | Descrição |
|-------|------|----------|
| `sku` | TEXT PRIMARY KEY | Código único do produto |
| `titulo` | TEXT | Nome/título do produto |
| `preco` | TEXT | Preço original |
| `preco_pix` | TEXT | Preço com desconto PIX |
| `valor_parcela` | TEXT | Valor de cada parcela |
| `numero_parcelas` | TEXT | Quantidade de parcelas |
| `informacoes_tecnicas` | TEXT | Especificações em formato JSON |
| `data_atualizacao` | TIMESTAMP | Data da última atualização |

### Consultar Dados no Banco

```bash
# Abrir o banco SQLite3
sqlite3 produtos_maeto.db

# Comandos úteis:
.tables                          # Listar tabelas
.schema produtos                 # Ver estrutura da tabela
SELECT COUNT(*) FROM produtos;   # Contar produtos
SELECT * FROM produtos LIMIT 5;  # Ver primeiros 5 produtos
.quit                           # Sair
```

## ⚡ Otimizações Implementadas

1. **Cache de Especificações**: Produtos que já possuem informações técnicas não são re-processados
2. **Delays Inteligentes**: Pausas entre requisições para evitar sobrecarga do servidor
3. **Tratamento de Erros**: Continua processamento mesmo com falhas pontuais
4. **Paginação Automática**: Coleta todos os produtos disponíveis automaticamente
5. **Atualização Incremental**: Apenas atualiza dados quando necessário

## 🔍 Troubleshooting

### Problema: "No such table: produtos"
**Solução**: Execute `python create_database.py` primeiro

### Problema: "ModuleNotFoundError"
**Solução**: Instale as dependências com `pip install requests beautifulsoup4 pandas lxml`

### Problema: Conexão lenta ou timeouts
**Solução**: Verifique sua conexão com a internet e tente novamente

### Problema: Nenhum produto encontrado
**Solução**: Tente termos de busca diferentes ou mais específicos

### Verificar se o banco foi criado corretamente

```bash
# Windows
dir produtos_maeto.db

# Linux/Mac
ls -la produtos_maeto.db

# Verificar conteúdo
sqlite3 produtos_maeto.db "SELECT COUNT(*) FROM produtos;"
```

## 📊 Exemplo de Dados Extraídos

```json
{
  "sku": "NB001",
  "titulo": "Notebook Gamer ASUS ROG",
  "preco": "R$ 3.499,00",
  "preco_pix": "R$ 3.149,10",
  "valor_parcela": "R$ 291,58",
  "numero_parcelas": "12x",
  "informacoes_tecnicas": {
    "Processador": "Intel Core i7",
    "Memória RAM": "16GB DDR4",
    "Armazenamento": "512GB SSD",
    "Placa de Vídeo": "NVIDIA GTX 1660"
  }
}
```

## 📝 Notas Importantes

- ⚠️ **Sempre execute `create_database.py` antes do primeiro uso**
- 🔄 **O programa atualiza produtos existentes automaticamente**
- 📊 **Especificações técnicas são salvas em formato JSON**
- 🚀 **Performance otimizada para evitar re-scraping desnecessário**
- 🛡️ **Tratamento robusto de erros e timeouts**

## 🤝 Suporte

Se encontrar problemas:
1. Verifique se todas as dependências estão instaladas
2. Confirme que o banco de dados foi criado
3. Teste com termos de busca simples primeiro
4. Verifique sua conexão com a internet
