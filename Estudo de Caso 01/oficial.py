from datetime import datetime
import numpy as np
from sklearn.ensemble import IsolationForest


def ler_arquivo_log(caminho_arquivo):
    """
    Lê o arquivo de log e retorna todas as linhas.
    """
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            return arquivo.readlines()
    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
        return []
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return []
        

def filtrar_erros_sistema(linhas):
    """
    Filtra as linhas que contêm "ERRO DE SISTEMA" e as organiza por nível de gravidade.
    """
    erros = {"Nível 1": [], "Nível 2": [], "Nível 3 (Crítico)": []}

    for linha in linhas:
        if "ERRO DE SISTEMA" in linha:
            # Extrai o nível do erro
            if "Nível: 1" in linha:
                erros["Nível 1"].append(linha.strip())
            elif "Nível: 2" in linha:
                erros["Nível 2"].append(linha.strip())
            elif "Nível: 3" in linha:
                erros["Nível 3 (Crítico)"].append(linha.strip())

    return erros

def extrair_dados_para_ia(linhas):
    """
    Extrai dados das linhas do log para serem usados na detecção de anomalias.
    Retorna uma lista de características (features) e as linhas correspondentes.
    """
    dados = []
    linhas_correspondentes = []

    for linha in linhas:
        if "ENTRADA" in linha or "SAÍDA" in linha:
            # Remover as aspas da linha
            linha_sem_aspas = linha.strip().strip('"')
            
            # Extrair a data e hora da linha
            data_hora = linha_sem_aspas.split("]")[0].replace("[", "")
            data_hora = datetime.strptime(data_hora, "%d/%m/%Y %H:%M")

            # Extrai características (features) para o modelo de IA
            hora = data_hora.hour
            dia_da_semana = data_hora.weekday()  # 0 = segunda, 6 = domingo
            dados.append([hora, dia_da_semana])
            linhas_correspondentes.append(linha.strip())

    return np.array(dados), linhas_correspondentes

def classificar_acessos_com_ia(dados, linhas_correspondentes):
    """
    Usa um modelo de Isolation Forest para classificar acessos como Normais, Suspeitos ou Críticos.
    """
    # Treina a IA = Isolation Forest
    modelo = IsolationForest(contamination=0.1, random_state=42)  # 10%  são considerados anômalos
    modelo.fit(dados)

    # Aqui ela faz a previsão 
    previsoes = modelo.predict(dados)

    # cassifca os acessos 
    classificacoes = {"Normais": [], "Suspeitos": [], "Críticos": []}

    for linha, previsao in zip(linhas_correspondentes, previsoes):
        if previsao == 1:
            classificacoes["Normais"].append(linha)
        elif "22:00" <= linha.split(" ")[1] <= "06:00":
            classificacoes["Críticos"].append(linha)  # 22H e 06Hrs são criticos
        else:
            classificacoes["Suspeitos"].append(linha)  # Os restantes são suspeito

    return classificacoes


def gerar_alertas(classificacoes, erros):
    """
    Gera alertas para acessos críticos e falhas críticas (nível 3).
    """
    # Criaçã de alerta para estados criticos
    if classificacoes["Críticos"]:
        print("\n=== ALERTA: ACESSOS CRÍTICOS DETECTADOS ===")
        for acesso in classificacoes["Críticos"]:
            print(f"ALERTA: {acesso}")

        # Envia alerta por e-mail 
        assunto = "ALERTA: Acessos Críticos Detectados"
        mensagem = "Os seguintes acessos críticos foram detectados:\n\n" + "\n".join(classificacoes["Críticos"])

        # Registra os alertas em um arquivo de log
        with open("alertas_criticos.log", "a", encoding="utf-8") as arquivo_alertas:
            arquivo_alertas.write("=== ALERTAS CRÍTICOS ===\n")
            for acesso in classificacoes["Críticos"]:
                arquivo_alertas.write(acesso + "\n")
    else:
        print("Nenhum acesso crítico detectado.")

    # Alertas para falhas críticas
    if erros["Nível 3 (Crítico)"]:
        print("\n=== ALERTA: FALHAS CRÍTICAS DETECTADAS ===")
        for erro in erros["Nível 3 (Crítico)"]:
            print(f"ALERTA: {erro}")

        # Envia alerta por e-mail
        assunto = "ALERTA: Falhas Críticas Detectadas"
        mensagem = "As seguintes falhas críticas foram detectadas:\n\n" + "\n".join(erros["Nível 3 (Crítico)"])

        # Registra os alertas em um arquivo de log
        with open("alertas_falhas_criticas.log", "a", encoding="utf-8") as arquivo_alertas:
            arquivo_alertas.write("=== ALERTAS DE FALHAS CRÍTICAS ===\n")
            for erro in erros["Nível 3 (Crítico)"]:
                arquivo_alertas.write(erro + "\n")
    else:
        print("Nenhuma falha crítica detectada.")

def salvar_resultados(erros, classificacoes, caminho_saida):
    """
    Salva os erros e classificações em um novo arquivo.
    """
    try:
        with open(caminho_saida, 'w', encoding='utf-8') as arquivo_saida:
            arquivo_saida.write("=== ERROS DE SISTEMA ===\n")
            for nivel, lista_erros in erros.items():
                arquivo_saida.write(f"\n=== {nivel} ===\n")
                for erro in lista_erros:
                    arquivo_saida.write(erro + "\n")

            arquivo_saida.write("\n=== CLASSIFICAÇÃO DOS ACESSOS ===\n")
            for categoria, lista_acessos in classificacoes.items():
                arquivo_saida.write(f"\n=== {categoria} ===\n")
                for acesso in lista_acessos:
                    arquivo_saida.write(acesso + "\n")

        print(f"Resultados salvos em '{caminho_saida}'.")
    except Exception as e:
        print(f"Erro ao salvar o arquivo de resultados: {e}")

def exibir_resultados(erros, classificacoes):
    """
    Exibe os erros e classificações no terminal.
    """
    print("\n=== ERROS DE SISTEMA ===")
    for nivel, lista_erros in erros.items():
        print(f"\n=== {nivel} ===")
        if lista_erros:
            for erro in lista_erros:
                print(erro)
        else:
            print("Nenhum erro encontrado.")

    print("\n=== CLASSIFICAÇÃO DOS ACESSOS ===")
    for categoria, lista_acessos in classificacoes.items():
        print(f"\n=== {categoria} ===")
        if lista_acessos:
            for acesso in lista_acessos:
                print(acesso)
        else:
            print(f"Nenhum acesso classificado como {categoria}.")

# Caminho do arquivo de log de entrada
caminho_log = 'portaria_condominio.log'

# Caminho do arquivo de saída para os resultados
caminho_saida = 'resultados_classificados_ia.log'

# Lê o arquivo de log
linhas = ler_arquivo_log(caminho_log)

# Filtra os erros de sistema
erros = filtrar_erros_sistema(linhas)

# Extrai dados para a IA
dados, linhas_correspondentes = extrair_dados_para_ia(linhas)

# Classifica os acessos com IA
classificacoes = classificar_acessos_com_ia(dados, linhas_correspondentes)

# Exibe os resultados no terminal
exibir_resultados(erros, classificacoes)

# Gera alertas para acessos críticos e falhas críticas
gerar_alertas(classificacoes, erros)

# Salva os resultados em um novo arquivo
salvar_resultados(erros, classificacoes, caminho_saida)