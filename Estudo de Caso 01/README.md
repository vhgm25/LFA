Sistema de Análise de Logs de Condomínio com IA

 Visão Geral
Script Python que processa logs de acesso de condomínios, utilizando machine learning para detectar acessos suspeitos e classificar erros do sistema por gravidade.

 Começando

Pré-requisitos
- Python 3.8+
- Bibliotecas listadas em `requirements.txt`

Instalação
1. Clone o repositório:
2. Instale as dependências:

 Como Usar
1. Coloque seu arquivo de log na raiz do projeto com o nome `portaria_condominio.log`
2. Execute o script:

3. Resultados serão gerados em:
- `resultados_classificados_ia.log` (relatório completo)
- `distribuicao_acessos.png` (gráfico)
- `distribuicao_erros.png` (gráfico)

 Funcionalidades Principais
- **Classificação Automática de Erros**
  - Nível 1: Baixa gravidade
  - Nível 2: Média gravidade
  - Nível 3: Crítico

- **Detecção de Anomalias com IA**
  - 🟢 Acessos normais
  - 🟡 Acessos suspeitos
  - 🔴 Acessos críticos

- **Geração de Relatórios**
  - Estatísticas detalhadas
  - Gráficos de distribuição

 Estrutura do Código
```python
# Principais funções:
def ler_arquivo_log(): ...
def filtrar_erros_sistema(): ...
def extrair_dados_para_ia(): ...
def classificar_acessos_com_ia(): ...  # Usa Isolation Forest
def gerar_relatorio_estatistico(): ...


 Exemplo de Saída

=== RELATÓRIO ESTATÍSTICO ===
Total de acessos: 150
✅ Normais: 120 (80.0%)
⚠️ Suspeitos: 20 (13.3%)
🚨 Críticos: 10 (6.7%)

Total de erros: 15
Nível 1: 5 (33.3%)
Nível 2: 7 (46.7%)
Nível 3: 3 (20.0%)


Formato do Log de Entrada
O arquivo de log deve conter linhas no formato:

[DD/MM/YYYY HH:MM] "TIPO_DE_ACESSO: [MORADOR/PRESTADOR/VISITANTE] (DETALHES)"
[DD/MM/YYYY HH:MM] "ERRO DE SISTEMA: Descrição (Nível: X)"
