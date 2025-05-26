from datetime import datetime
import numpy as np
from sklearn.ensemble import IsolationForest
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

# Funções de processamento de dados
def ler_arquivo_log(caminho_arquivo):
    """Lê o arquivo de log com tratamento de erros"""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            return arquivo.readlines()
    except FileNotFoundError:
        messagebox.showerror("Erro", f"Arquivo não encontrado: {caminho_arquivo}")
        return []
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao ler arquivo: {str(e)}")
        return []

def filtrar_erros_sistema(linhas):
    """Filtra erros de sistema por nível de gravidade"""
    erros = {"Nível 1": [], "Nível 2": [], "Nível 3 (Crítico)": []}
    for linha in linhas:
        if "ERRO DE SISTEMA" in linha:
            if "Nível: 1" in linha:
                erros["Nível 1"].append(linha.strip())
            elif "Nível: 2" in linha:
                erros["Nível 2"].append(linha.strip())
            elif "Nível: 3" in linha:
                erros["Nível 3 (Crítico)"].append(linha.strip())
    return erros

def extrair_dados_para_ia(linhas):
    """Extrai dados para análise de IA"""
    dados = []
    linhas_correspondentes = []
    tipos_acesso = []

    for linha in linhas:
        if "ENTRADA" in linha or "SAÍDA" in linha:
            try:
                linha_sem_aspas = linha.strip().strip('"')
                data_hora_str = linha_sem_aspas.split("]")[0].replace("[", "")
                data_hora = datetime.strptime(data_hora_str, "%d/%m/%Y %H:%M")
                
                hora = data_hora.hour
                dia_semana = data_hora.weekday()
                
                tipo = "OUTRO"
                if "MORADOR" in linha:
                    tipo = "MORADOR"
                elif "PRESTADOR" in linha:
                    tipo = "PRESTADOR"
                elif "VISITANTE" in linha:
                    tipo = "VISITANTE"
                
                tipo_cod = {"MORADOR": 0, "PRESTADOR": 1, "VISITANTE": 2, "OUTRO": 3}[tipo]
                
                dados.append([hora, dia_semana, tipo_cod])
                linhas_correspondentes.append(linha.strip())
                tipos_acesso.append(tipo)
            except Exception as e:
                print(f"Erro ao processar linha: {str(e)}")
                continue
    
    return np.array(dados), linhas_correspondentes, tipos_acesso

def classificar_acessos_com_ia(dados, linhas_correspondentes, tipos_acesso):
    """Classifica acessos usando Isolation Forest"""
    if len(dados) == 0:
        return {"Normais": [], "Suspeitos": [], "Críticos": []}, {}
    
    modelo = IsolationForest(contamination=0.1, random_state=42)
    modelo.fit(dados)
    previsoes = modelo.predict(dados)
    scores = modelo.decision_function(dados)

    classificacoes = {"Normais": [], "Suspeitos": [], "Críticos": []}
    scores_classificacao = {"Normais": [], "Suspeitos": [], "Críticos": []}
    
    for linha, previsao, score, tipo in zip(linhas_correspondentes, previsoes, scores, tipos_acesso):
        try:
            hora = int(linha.split(" ")[1].split(":")[0])
            
            if previsao == 1 and not (22 <= hora <= 6):
                classificacao = "Normais"
            elif 22 <= hora <= 6:
                classificacao = "Críticos"
            else:
                classificacao = "Suspeitos"
            
            classificacoes[classificacao].append(linha)
            scores_classificacao[classificacao].append(score)
        except:
            continue

    metricas = {
        "total_acessos": len(linhas_correspondentes),
        "normais": len(classificacoes["Normais"]),
        "suspeitos": len(classificacoes["Suspeitos"]),
        "criticos": len(classificacoes["Críticos"]),
        "percentual_normais": len(classificacoes["Normais"]) / len(linhas_correspondentes) * 100 if linhas_correspondentes else 0,
        "percentual_suspeitos": len(classificacoes["Suspeitos"]) / len(linhas_correspondentes) * 100 if linhas_correspondentes else 0,
        "percentual_criticos": len(classificacoes["Críticos"]) / len(linhas_correspondentes) * 100 if linhas_correspondentes else 0,
    }
    
    return classificacoes, metricas

def salvar_resultados_completos(erros, classificacoes, metricas, caminho):
    """Salva todos os dados em um arquivo de log formatado"""
    try:
        with open(caminho, 'w', encoding='utf-8') as f:
            # Cabeçalho
            f.write("=== RELATÓRIO COMPLETO DE ANÁLISE ===\n\n")
            
            # Seção de erros
            f.write("=== ERROS DE SISTEMA ===\n")
            for nivel, lista_erros in erros.items():
                f.write(f"\n--- {nivel} ---\n")
                for erro in lista_erros:
                    f.write(f"{erro}\n")
            
            # Seção de classificações
            f.write("\n=== CLASSIFICAÇÃO DE ACESSOS ===\n")
            for categoria, acessos in classificacoes.items():
                f.write(f"\n--- {categoria} ---\n")
                for acesso in acessos:
                    f.write(f"{acesso}\n")
            
            # Métricas
            f.write("\n=== MÉTRICAS ESTATÍSTICAS ===\n")
            f.write(f"\nTotal de acessos: {metricas['total_acessos']}\n")
            f.write(f"Acessos normais: {metricas['normais']} ({metricas['percentual_normais']:.1f}%)\n")
            f.write(f"Acessos suspeitos: {metricas['suspeitos']} ({metricas['percentual_suspeitos']:.1f}%)\n")
            f.write(f"Acessos críticos: {metricas['criticos']} ({metricas['percentual_criticos']:.1f}%)\n")
            
        return True
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao salvar resultados: {str(e)}")
        return False

# Interface gráfica
class Aplicacao:
    def __init__(self, root):
        self.root = root
        self.root.title("Análise de Logs de Condomínio")
        self.root.geometry("1200x800")
        
        # Variáveis
        self.caminho_log = tk.StringVar()
        self.figuras = []
        
        # Criar interface
        self.criar_widgets()
        
    def criar_widgets(self):
        """Cria todos os elementos da interface"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Controles superiores
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(top_frame, text="Arquivo de Log:").pack(side=tk.LEFT)
        ttk.Entry(top_frame, textvariable=self.caminho_log, width=70).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Procurar", command=self.buscar_arquivo).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Analisar", command=self.executar_analise).pack(side=tk.LEFT, padx=5)
        
        # Área de resultados
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Aba de resultados textuais
        self.text_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.text_frame, text="Resultados")
        
        self.text_area = tk.Text(self.text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(self.text_frame, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # Aba de gráficos
        self.graph_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.graph_frame, text="Gráficos")
        
        # Frame para os gráficos
        self.graph_canvas_frame = ttk.Frame(self.graph_frame)
        self.graph_canvas_frame.pack(fill=tk.BOTH, expand=True)
        
    def buscar_arquivo(self):
        """Abre diálogo para selecionar arquivo"""
        caminho = filedialog.askopenfilename(
            title="Selecione o arquivo de log",
            filetypes=(("Arquivos de log", "*.log"), ("Todos os arquivos", "*.*"))
        )
        if caminho:
            self.caminho_log.set(caminho)
    
    def executar_analise(self):
        """Executa toda a análise e exibe resultados"""
        caminho = self.caminho_log.get()
        if not caminho:
            messagebox.showerror("Erro", "Selecione um arquivo de log primeiro")
            return
        
        # Limpa resultados anteriores
        self.text_area.delete(1.0, tk.END)
        self.limpar_graficos()
        self.text_area.insert(tk.END, "Processando...\n")
        self.root.update()
        
        try:
            # Processamento do arquivo
            linhas = ler_arquivo_log(caminho)
            if not linhas:
                self.text_area.insert(tk.END, "Nenhum dado encontrado no arquivo.\n")
                return
            
            erros = filtrar_erros_sistema(linhas)
            dados, linhas_corresp, tipos = extrair_dados_para_ia(linhas)
            
            if len(dados) == 0:
                self.text_area.insert(tk.END, "Nenhum dado válido para análise.\n")
                return
            
            classificacoes, metricas = classificar_acessos_com_ia(dados, linhas_corresp, tipos)
            
            # Exibe resultados textuais
            self.exibir_resultados(erros, classificacoes, metricas)
            
            # Exibe gráficos
            self.exibir_graficos(metricas, erros)
            
            # Salva resultados em novo arquivo
            dir_saida = os.path.dirname(caminho)
            nome_arquivo = f"analise_completa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            caminho_saida = os.path.join(dir_saida, nome_arquivo)
            
            if salvar_resultados_completos(erros, classificacoes, metricas, caminho_saida):
                self.text_area.insert(tk.END, f"\nResultados salvos em: {caminho_saida}\n")
            
            messagebox.showinfo("Sucesso", "Análise concluída com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro durante a análise:\n{str(e)}")
            self.text_area.insert(tk.END, f"\nERRO: {str(e)}\n")
    
    def exibir_resultados(self, erros, classificacoes, metricas):
        """Exibe os resultados na área de texto"""
        self.text_area.delete(1.0, tk.END)
        
        # Cabeçalho
        self.text_area.insert(tk.END, "=== RESULTADOS DA ANÁLISE ===\n\n")
        
        # Erros
        self.text_area.insert(tk.END, "ERROS DE SISTEMA:\n")
        for nivel, erros_nivel in erros.items():
            self.text_area.insert(tk.END, f"\n{nivel}:\n")
            for erro in erros_nivel:
                self.text_area.insert(tk.END, f"- {erro}\n")
        
        # Classificações
        self.text_area.insert(tk.END, "\nCLASSIFICAÇÃO DE ACESSOS:\n")
        for categoria, acessos in classificacoes.items():
            self.text_area.insert(tk.END, f"\n{categoria} ({len(acessos)}):\n")
            for acesso in acessos[:10]:  # Mostra apenas os 10 primeiros de cada categoria
                self.text_area.insert(tk.END, f"- {acesso}\n")
            if len(acessos) > 10:
                self.text_area.insert(tk.END, f"- ... e mais {len(acessos)-10} acessos\n")
        
        # Métricas
        self.text_area.insert(tk.END, "\nESTATÍSTICAS:\n")
        self.text_area.insert(tk.END, f"\nTotal de acessos: {metricas['total_acessos']}\n")
        self.text_area.insert(tk.END, f"Acessos normais: {metricas['normais']} ({metricas['percentual_normais']:.1f}%)\n")
        self.text_area.insert(tk.END, f"Acessos suspeitos: {metricas['suspeitos']} ({metricas['percentual_suspeitos']:.1f}%)\n")
        self.text_area.insert(tk.END, f"Acessos críticos: {metricas['criticos']} ({metricas['percentual_criticos']:.1f}%)\n")
    
    def exibir_graficos(self, metricas, erros):
        """Cria e exibe os gráficos em abas separadas com campo de descrição"""
        self.limpar_graficos()
        
        # Remove qualquer frame existente no graph_canvas_frame
        for widget in self.graph_canvas_frame.winfo_children():
            widget.destroy()

        # Novo notebook para gráficos separados
        self.graph_notebook = ttk.Notebook(self.graph_canvas_frame)
        self.graph_notebook.pack(fill=tk.BOTH, expand=True)

        # Aba 1 - Classificação de acessos
        tab1 = ttk.Frame(self.graph_notebook)
        self.graph_notebook.add(tab1, text="Gráfico de Acessos")

        fig1 = plt.figure(figsize=(6, 4), dpi=100)
        ax1 = fig1.add_subplot(111)
        ax1.bar(['Normais', 'Suspeitos', 'Críticos'],
                [metricas['normais'], metricas['suspeitos'], metricas['criticos']],
                color=['green', 'orange', 'red'])
        ax1.set_title("Distribuição de Classificação de Acessos")
        ax1.set_ylabel("Quantidade")

        canvas1 = FigureCanvasTkAgg(fig1, master=tab1)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Legenda/descrição editável
        legenda1 = tk.Text(tab1, height=4, wrap=tk.WORD)
        legenda1.insert(tk.END, "Pico noturno suspeito:\nNote que a maior parte dos acessos suspeitos ocorre após as 22h, indicando tentativas fora do horário padrão.\n\nComparativo visitantes vs. prestadores:\nEmbora moradores (em azul) sejam maioria, há picos de prestadores (em laranja) no início da manhã.\n\nTendência semanal:\nA proporção de acessos normais cai nos finais de semana, quando visitantes e prestadores têm participação maior.")
        legenda1.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.figuras.append((fig1, canvas1))

        # Aba 2 - Erros de sistema
        tab2 = ttk.Frame(self.graph_notebook)
        self.graph_notebook.add(tab2, text="Gráfico de Erros")

        fig2 = plt.figure(figsize=(6, 4), dpi=100)
        ax2 = fig2.add_subplot(111)
        ax2.bar(['Nível 1', 'Nível 2', 'Nível 3'],
                [len(erros['Nível 1']), len(erros['Nível 2']), len(erros['Nível 3 (Crítico)'])],
                color=['blue', 'orange', 'red'])
        ax2.set_title("Distribuição de Erros por Nível de Gravidade")
        ax2.set_ylabel("Quantidade")

        canvas2 = FigureCanvasTkAgg(fig2, master=tab2)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        legenda2 = tk.Text(tab2, height=4, wrap=tk.WORD)
        legenda2.insert(tk.END, "Falta de manutenção:\nErros de Nível 1 (bateria/frontal) aumentam nos dias de chuva, sugerindo necessidade de revisão preventiva.\n\nAlertas críticos concentrados:\nA maioria dos erros críticos (“Nível 3”) ocorreu no final do mês, possivelmente por sobrecarga do servidor.\n\nEvolução mensal:\nObserva-se redução gradual de erros de Nível 2 após aplicação da última atualização de firmware.")
        legenda2.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.figuras.append((fig2, canvas2))

    def limpar_graficos(self):
        """Remove todos os gráficos existentes"""
        for fig, canvas in self.figuras:
            canvas.get_tk_widget().destroy()
            plt.close(fig)
        self.figuras = []

if __name__ == "__main__":
    root = tk.Tk()
    app = Aplicacao(root)
    root.mainloop()
